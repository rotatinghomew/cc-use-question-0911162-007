from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from evidence_deliberation.claims.contract import ContractError, Decision, DomainRecord, records_from_fixture, stable_hash
from evidence_deliberation.records.deliberation_store import Repository
from evidence_deliberation.resolutions.resolution_flow import STATES, advance_for_outcome, decide
from evidence_deliberation.dissent.conditions import export_bundle, verify_bundle
from evidence_deliberation.dissent.objections import (
    Objection,
    ObjectionAssessment,
    assess_objection,
    claim_chain_key,
    objections_from_fixture,
)
from evidence_deliberation.arguments.evidence_merge import derive_context
from evidence_deliberation.evidence_signal.evidence_strength import augment_context


class Application:
    def __init__(self, database: str | Path, context: Mapping[str, Any] | None = None):
        self.repository = Repository(database)
        self.context = dict(context or {})

    def ingest(self, record: DomainRecord) -> DomainRecord:
        current = self.repository.get_record(record.record_id)
        if current is None:
            self.repository.save_record(record)
            return record
        if current.fingerprint == record.fingerprint:
            return current
        replacement = DomainRecord(record.record_id, record.payload, current.state,
                                   current.version + 1, record.occurred_at, record.source)
        self.repository.save_record(replacement, expected_version=current.version)
        return replacement

    def _evaluate_record(self, record: DomainRecord) -> tuple[DomainRecord, Decision]:
        context = dict(self.context)
        context.update(derive_context(record, self.repository))
        context.update(augment_context(record, self.repository))
        statuses = [item.status for item in self.repository.latest_assessments(record.record_id)]
        decision = decide(record, context, objection_statuses=statuses)
        self.repository.save_decision(decision)
        advanced = advance_for_outcome(record, decision)
        if advanced.fingerprint != record.fingerprint:
            self.repository.save_record(advanced, expected_version=record.version)
        return advanced, decision

    def process(self, record: DomainRecord) -> tuple[DomainRecord, Decision]:
        stored = self.ingest(record)
        return self._evaluate_record(stored)

    # ------------------------------------------------------------------
    # 异议登记、评估与发布闸门
    # ------------------------------------------------------------------
    def register_objection(self, objection: Objection) -> Objection:
        target = self.repository.get_record(objection.target_record_id)
        if target is None:
            raise ContractError(f"objection target record does not exist: {objection.target_record_id}")
        if not objection.chain_key:
            objection = Objection(objection.objection_id, objection.target_record_id, objection.basis,
                                  objection.rationale, objection.evidence_refs, objection.response,
                                  claim_chain_key(target), objection.version, objection.created_at)
        current = self.repository.get_objection(objection.objection_id)
        if current is not None and current.version >= objection.version:
            # 重放同一批异议时保持幂等：已存在同版本或更新版本时不重复评估。
            return current
        assessment = assess_objection(objection, target)
        self.repository.save_objection(objection, assessment.status)
        self.repository.save_assessment(assessment)
        return objection

    def assess_target(self, record_id: str) -> list[ObjectionAssessment]:
        target = self.repository.get_record(record_id)
        if target is None:
            raise ContractError(f"unknown record: {record_id}")
        results: list[ObjectionAssessment] = []
        previous_rows = self.repository.list_assessments(target_record_id=record_id)
        for objection in self.repository.list_objections(record_id):
            previous = next((row for row in reversed(previous_rows)
                             if row.objection_id == objection.objection_id), None)
            assessment = assess_objection(objection, target, previous)
            self.repository.save_assessment(assessment)
            results.append(assessment)
        return results

    def _evidence_refs_for(self, record_id: str) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        for objection in self.repository.list_objections(record_id):
            refs.extend(ref.as_dict() for ref in objection.evidence_refs)
            if objection.response:
                refs.append(objection.response.as_dict())
        return refs

    def _maybe_archive(self, record: DomainRecord, decision: Decision,
                       assessments: Sequence[ObjectionAssessment]) -> None:
        # 归档是终态：固化当时引用的记录、决策与证据版本，后续补充证据不得改写。
        if record.state != STATES[-1] or self.repository.get_archive(record.record_id):
            return
        self.repository.save_resolution_archive(record, decision, self._evidence_refs_for(record.record_id),
                                                list(assessments))

    def _finish_run(self, run_id: str, fixture_hash: str, output: str | Path,
                    final_records: Sequence[DomainRecord], decisions: Mapping[str, Decision]) -> dict[str, Any]:
        snapshot = self.repository.snapshot()
        if snapshot["chain_errors"]:
            raise ContractError("audit chain verification failed")
        assessments = self.repository.list_assessments()
        archives = self.repository.list_archives()
        manifest = export_bundle(output, final_records, decisions, snapshot, self.repository.event_rows(),
                                 objections=self.repository.list_objections(),
                                 assessments=assessments, archives=archives)
        result = {"run_id": run_id, "fixture_hash": fixture_hash, "records": len(final_records),
                  "decisions": len(decisions), "manifest": manifest, "snapshot": snapshot,
                  "objections": len(self.repository.list_objections()),
                  "assessments": len(assessments), "archives": len(archives)}
        self.repository.finish_run(run_id, result)
        return result

    def run_fixture(self, fixture: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
        records = records_from_fixture(fixture)
        fixture_objections = objections_from_fixture(fixture, {item.record_id: item for item in records})
        fixture_hash = stable_hash({"fixture": fixture,
                                    "objections": [item.as_dict() for item in fixture_objections]})
        run_id = self.repository.begin_run(fixture_hash, len(records))
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            return completed
        records_by_id = {record.record_id: record for record in records}
        # 先完成所有主张记录的入库与首轮审议，确保每条异议都能指向真实主张及其支持材料。
        decisions: dict[str, Decision] = {}
        for record in records:
            final_record, decision = self.process(record)
            records_by_id[record.record_id] = final_record
            decisions[record.record_id] = decision
            self._maybe_archive(final_record, decision, self.repository.latest_assessments(record.record_id))
        for objection in fixture_objections:
            self.register_objection(objection)
        # 异议评估必须影响待发布决议：对所有被异议的主张链重新审议。
        affected_chains = {objection.chain_key for objection in fixture_objections}
        for record in records:
            current = records_by_id[record.record_id]
            if claim_chain_key(current) not in affected_chains:
                continue
            target = self.repository.get_record(record.record_id) or current
            advanced, decision = self._evaluate_record(target)
            records_by_id[record.record_id] = advanced
            decisions[record.record_id] = decision
            self._maybe_archive(advanced, decision, self.repository.latest_assessments(record.record_id))
        final_records = [records_by_id[record.record_id] for record in records]
        return self._finish_run(run_id, fixture_hash, output, final_records, decisions)

    def _load_responses(self, fixture: Mapping[str, Any]) -> list[Objection]:
        raw = fixture.get("objection_responses")
        if raw is None:
            return []
        if not isinstance(raw, list) or not raw:
            raise ContractError("objection_responses must be a non-empty list")
        return [Objection.from_dict(item) for item in raw]

    def supplement(self, fixture: Mapping[str, Any]) -> dict[str, Any]:
        """补充证据后只重评受影响的主张链，已归档决议保持其固化版本。"""
        responses = self._load_responses(fixture)
        raw_records = fixture.get("records", [])
        if not isinstance(raw_records, list):
            raise ContractError("supplement records must be a list")
        supplement_records = records_from_fixture({"records": raw_records}) if raw_records else []
        if not supplement_records and not responses:
            raise ContractError("supplement requires records or objection_responses")
        touched_chains: set[str] = set()
        updated_records: list[str] = []
        frozen: list[str] = []
        for incoming in supplement_records:
            current = self.repository.get_record(incoming.record_id)
            if current is None:
                raise ContractError(f"supplement targets unknown record: {incoming.record_id}")
            if current.payload == incoming.payload:
                # 幂等：相同证据重复提交不产生新版本，也不触发重评。
                continue
            merged = current.with_payload(incoming.payload)
            self.repository.save_record(merged, expected_version=current.version)
            updated_records.append(merged.record_id)
            if self.repository.get_archive(incoming.record_id) is not None:
                # 已归档决议不可重开：新证据可入库为新版本，但不改变归档时引用的证据版本。
                frozen.append(incoming.record_id)
                continue
            touched_chains.add(claim_chain_key(merged))
        for response in responses:
            objection = self.repository.get_objection(response.objection_id)
            if objection is None:
                raise ContractError(f"response targets unknown objection: {response.objection_id}")
            if response.evidence_refs:
                raise ContractError("objection response fixture must only carry the response evidence")
            if response.response is None:
                raise ContractError("objection response fixture requires response evidence")
            target = self.repository.get_record(objection.target_record_id)
            if objection.response is not None and objection.response == response.response:
                # 幂等：相同回应证据重复提交不产生异议新版本。
                touched_chains.add(objection.chain_key)
                continue
            updated = objection.with_response(response.response)
            assessment = assess_objection(updated, target)
            self.repository.save_objection(updated, assessment.status)
            self.repository.save_assessment(assessment)
            touched_chains.add(objection.chain_key)
        affected_record_ids = sorted(
            record.record_id for record in self.repository.list_records()
            if claim_chain_key(record) in touched_chains
            and self.repository.get_archive(record.record_id) is None)
        re_decided: list[str] = []
        for record_id in affected_record_ids:
            target = self.repository.get_record(record_id)
            if target is None:
                continue
            self.assess_target(record_id)
            advanced, decision = self._evaluate_record(target)
            re_decided.append(record_id)
            self._maybe_archive(advanced, decision, self.repository.latest_assessments(record_id))
        return {"updated_records": updated_records, "touched_chains": sorted(touched_chains),
                "re_evaluated_records": re_decided,
                "frozen_archives": sorted(set(frozen) | {row["record_id"] for row in self.repository.list_archives()})}

    def inspect(self) -> dict[str, Any]:
        return {"snapshot": self.repository.snapshot(), "records": [record.__dict__ for record in self.repository.list_records()],
                "decisions": self.repository.decision_rows(),
                "objections": [item.as_dict() for item in self.repository.list_objections()],
                "assessments": [item.as_dict() for item in self.repository.list_assessments()],
                "archives": self.repository.list_archives()}


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read fixture: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value


def run(fixture_path: str | Path, database: str | Path, output: str | Path,
        context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    application = Application(database, context)
    return application.run_fixture(load_fixture(fixture_path), output)


def verify(database: str | Path, output: str | Path) -> dict[str, Any]:
    repository = Repository(database)
    chain_errors = repository.verify_chain()
    bundle_errors = verify_bundle(output)
    return {"ok": not chain_errors and not bundle_errors, "chain_errors": chain_errors,
            "bundle_errors": bundle_errors, "snapshot": repository.snapshot()}
