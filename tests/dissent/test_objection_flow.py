from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from evidence_deliberation.claims.contract import ContractError, DomainRecord
from evidence_deliberation.records.deliberation_store import Repository
from evidence_deliberation.resolutions.resolution_flow import STATES, decide
from evidence_deliberation.dissent.conditions import verify_bundle
from evidence_deliberation.dissent.objections import (
    DISPUTED,
    INSUFFICIENT,
    RESPONDED,
    EvidenceRef,
    Objection,
    assess_objection,
    claim_chain_key,
)
from evidence_deliberation.secretariat import Application, run

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "objections.json"
SUPPLEMENT = Path(__file__).resolve().parents[2] / "fixtures" / "supplement.json"


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def make_record(record_id: str = "governance_claim-9", claim: str = "claim-chain-z",
                state: str = "submitted") -> DomainRecord:
    payload = {"working_group": "wg", "topic": "topic-9", "source_kind": "kind",
               "source_version": "v1", "claim_id": claim, "claim_strength": 50.0,
               "evidence_direction": "support", "scope_condition": "scope-9",
               "source_quality": 70.0, "reproducibility": 0.8, "member_count": 32.0,
               "interpretation_confidence": 0.85}
    return DomainRecord(record_id, payload, state)


class ObjectionPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repository = Repository(Path(self.temp.name) / "db.sqlite3")
        self.record = make_record()
        self.repository.save_record(self.record)

    def test_objection_requires_existing_target(self):
        objection = Objection("obj-x", "governance_claim-missing", "scope", "x",
                              (EvidenceRef("e", "note", 0.7),))
        with self.assertRaisesRegex(ContractError, "target record does not exist"):
            self.repository.save_objection(objection, DISPUTED)

    def test_save_and_reload_objection_round_trip(self):
        objection = Objection("obj-1", self.record.record_id, "translation", "有依据",
                              (EvidenceRef("e", "note", 0.7),), chain_key=claim_chain_key(self.record))
        self.repository.save_objection(objection, DISPUTED)
        loaded = self.repository.get_objection("obj-1")
        self.assertEqual(loaded, objection)
        self.assertEqual(len(self.repository.list_objections(self.record.record_id)), 1)

    def test_objection_version_must_advance(self):
        objection = Objection("obj-2", self.record.record_id, "scope", "x",
                              (EvidenceRef("e", "note", 0.7),), chain_key="c")
        self.repository.save_objection(objection, DISPUTED)
        with self.assertRaisesRegex(ContractError, "version must advance"):
            self.repository.save_objection(objection, DISPUTED)

    def test_assessment_history_is_append_only_and_filterable(self):
        objection = Objection("obj-3", self.record.record_id, "scope", "x",
                              (EvidenceRef("e", "note", 0.7),), chain_key=claim_chain_key(self.record))
        first = assess_objection(objection, self.record)
        self.repository.save_assessment(first)
        updated_record = self.record.with_payload({"source_quality": 91.0})
        self.repository.save_record(updated_record, expected_version=1)
        responded = objection.with_response(EvidenceRef("r", "rebuttal", 0.95))
        second = assess_objection(responded, updated_record, first)
        self.repository.save_objection(responded, second.status)
        self.repository.save_assessment(second)
        history = self.repository.list_assessments(target_record_id=self.record.record_id)
        self.assertEqual([item.status for item in history], [DISPUTED, RESPONDED])
        self.assertEqual(self.repository.latest_assessments(self.record.record_id)[0].status, RESPONDED)
        self.assertEqual(len(self.repository.list_assessments(status=DISPUTED)), 1)
        self.assertEqual(self.repository.verify_chain(), [])

    def test_snapshot_counts_new_tables(self):
        counts = self.repository.snapshot()["counts"]
        for table in ("objections", "objection_versions", "objection_assessments",
                      "resolution_archives"):
            self.assertIn(table, counts)


class DecisionGateTests(unittest.TestCase):
    def test_unresolved_objection_forces_hold(self):
        record = make_record()
        context = {"approve_threshold": 0.0, "review_threshold": 0.0,
                   "domain_signal": 0.99, "domain_severity": "info"}
        clean = decide(record, context)
        # 无论基线结论如何，存在阻断性异议时结论必须被压成 hold。
        for status in (DISPUTED, INSUFFICIENT):
            blocked = decide(record, context, objection_statuses=[status])
            self.assertEqual(blocked.outcome, "hold")
            self.assertTrue(any("blocking_objections" in reason for reason in blocked.reasons))
        # 同一记录在无异议时不会因异议闸门而被压成 hold。
        self.assertNotIn("blocking_objections=disputed", clean.reasons)
        self.assertNotIn("blocking_objections=insufficient", clean.reasons)

    def test_responded_objection_does_not_add_blocker(self):
        record = make_record()
        context = {"approve_threshold": 0.0, "review_threshold": 0.0,
                   "domain_signal": 0.99, "domain_severity": "info"}
        baseline = decide(record, context)
        with_response = decide(record, context, objection_statuses=[RESPONDED])
        self.assertEqual(with_response.outcome, baseline.outcome)
        self.assertIn("blocking_objections=none", with_response.reasons)

    def test_hold_does_not_advance_to_archive(self):
        record = make_record(state=STATES[3])
        held = decide(record, {"domain_severity": "critical"})
        advanced = self._advance(record, held)
        self.assertNotEqual(advanced.state, STATES[-1])
        self.assertLessEqual(STATES.index(advanced.state), STATES.index("deliberating"))

    @staticmethod
    def _advance(record, decision):
        from evidence_deliberation.resolutions.resolution_flow import advance_for_outcome
        return advance_for_outcome(record, decision)


class EndToEndDissentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "dissent.sqlite3"
        self.output = self.root / "output"

    def test_run_classifies_three_states_and_withholds_release(self):
        result = run(FIXTURE, self.database, self.output)
        self.assertEqual(result["objections"], 4)
        summary = json.loads((self.output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["release_status"], "withheld")
        self.assertFalse(summary["release_gate"]["releasable"])
        counts = summary["dissent"]["status_counts"]
        self.assertEqual(counts[RESPONDED], 1)
        self.assertEqual(counts[DISPUTED], 2)
        self.assertEqual(counts[INSUFFICIENT], 1)
        # 发布摘要可追溯到每条仍未解决的反驳及其证据。
        unresolved_ids = {item["objection_id"] for item in summary["dissent"]["unresolved"]}
        self.assertEqual(unresolved_ids, {"objection-001", "objection-002", "objection-003"})
        for item in summary["dissent"]["unresolved"]:
            self.assertTrue(item["evidence_ids"])
            self.assertEqual(item["target_version"], 1)
        # 被异议压住的记录保持待发布状态，未被自动归档。
        self.assertTrue(all(state != "archived"
                            for state in summary["repository"]["states"]))
        self.assertEqual(verify_bundle(self.output), [])

    def test_objections_csv_links_target_and_status(self):
        run(FIXTURE, self.database, self.output)
        import csv
        with (self.output / "objections.csv").open(encoding="utf-8") as handle:
            rows = {row["objection_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["objection-001"]["status"], DISPUTED)
        self.assertEqual(rows["objection-004"]["status"], RESPONDED)
        self.assertEqual(rows["objection-001"]["target_record_id"], "governance_claim-101")
        self.assertIn("transcript-77", rows["objection-001"]["evidence_ids"])
        with (self.output / "records.csv").open(encoding="utf-8") as handle:
            record_rows = list(csv.DictReader(handle))
        self.assertTrue(all("dissent_status" in row for row in record_rows))

    def test_assessment_bundle_pins_record_fingerprints(self):
        run(FIXTURE, self.database, self.output)
        assessments = json.loads((self.output / "objection-assessments.json").read_text(encoding="utf-8"))
        repository = Repository(self.database)
        for assessment in assessments:
            record = repository.get_record(assessment["target_record_id"])
            self.assertTrue(assessment["target_fingerprint"])
            self.assertTrue(assessment["chain_key"])
        self.assertEqual(assessments[0]["objection_weight"] >= 0.0, True)

    def test_repeated_run_is_idempotent(self):
        first = run(FIXTURE, self.database, self.output)
        second = run(FIXTURE, self.database, self.output)
        self.assertEqual(first["objections"], second["objections"])
        repository = Repository(self.database)
        self.assertEqual(repository.snapshot()["counts"]["objections"], 4)
        self.assertEqual(len(repository.list_assessments()), 4)
        self.assertEqual(repository.verify_chain(), [])
        self.assertEqual(verify_bundle(self.output), [])


class SupplementReEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "dissent.sqlite3"
        self.output = self.root / "output"
        self.application = Application(self.database)
        self.application.run_fixture(load_fixture(FIXTURE), self.output)

    def test_supplement_only_re_evaluates_affected_chains(self):
        before = {r.record_id: r.version
                  for r in self.application.repository.list_records()}
        result = self.application.supplement(load_fixture(SUPPLEMENT))
        # alpha(101,102) 与 beta(103) 受影响；gamma(104) 不在任何受影响主张链内。
        self.assertEqual(set(result["re_evaluated_records"]),
                         {"governance_claim-101", "governance_claim-102", "governance_claim-103"})
        self.assertNotIn("governance_claim-104", result["re_evaluated_records"])
        untouched = self.application.repository.get_record("governance_claim-104")
        self.assertEqual(untouched.version, before["governance_claim-104"])
        latest = {a.objection_id: a.status
                  for a in self.application.repository.latest_assessments()}
        self.assertEqual(latest["objection-001"], RESPONDED)
        self.assertEqual(latest["objection-003"], RESPONDED)
        self.assertEqual(latest["objection-002"], DISPUTED)
        self.assertEqual(latest["objection-004"], RESPONDED)

    def test_supplement_unknown_record_is_rejected(self):
        bad = {"records": [{
            "record_id": "governance_claim-ghost",
            "payload": load_fixture(FIXTURE)["records"][0]["payload"],
            "state": "submitted", "source": "x"}]}
        with self.assertRaisesRegex(ContractError, "unknown record"):
            self.application.supplement(bad)

    def test_response_to_unknown_objection_is_rejected(self):
        bad = {"records": [], "objection_responses": [{
            "objection_id": "objection-ghost", "target_record_id": "governance_claim-101",
            "basis": "translation", "rationale": "x",
            "response": {"evidence_id": "r", "weight": 0.9}}]}
        with self.assertRaisesRegex(ContractError, "unknown objection"):
            self.application.supplement(bad)

    def test_repeated_supplement_is_idempotent(self):
        fixture = load_fixture(SUPPLEMENT)
        first = self.application.supplement(fixture)
        versions_before = {r.record_id: r.version for r in self.application.repository.list_records()}
        objection_versions_before = {o.objection_id: o.version
                                    for o in self.application.repository.list_objections()}
        second = self.application.supplement(fixture)
        self.assertEqual(second["re_evaluated_records"], first["re_evaluated_records"])
        self.assertEqual({r.record_id: r.version for r in self.application.repository.list_records()},
                         versions_before)
        self.assertEqual({o.objection_id: o.version for o in self.application.repository.list_objections()},
                         objection_versions_before)
        self.assertEqual(self.application.repository.verify_chain(), [])


class ArchiveFreezeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "archive.sqlite3"
        # 低阈值 + 高信号，使无阻断异议的记录可以一路 approve 到归档。
        self.application = Application(self.database, {
            "approve_threshold": 0.0, "review_threshold": 0.0,
            "transition_threshold": 0.0, "domain_signal": 0.99,
            "domain_severity": "info"})
        self.record = make_record("governance_claim-archive", "claim-chain-final")
        self.application.repository.save_record(self.record)

    def _drive_to_archive(self):
        from evidence_deliberation.resolutions.resolution_flow import decide
        record = self.application.repository.get_record(self.record.record_id)
        decision = None
        # 无阻断异议的记录沿生命周期逐状态推进，直到归档终态。
        for target in STATES[STATES.index(record.state) + 1:]:
            record = record.with_state(target)
            self.application.repository.save_record(record, expected_version=record.version - 1)
            decision = decide(record, self.application.context)
            self.application.repository.save_decision(decision)
        record = self.application.repository.get_record(self.record.record_id)
        self.assertEqual(record.state, "archived")
        assessments = self.application.repository.latest_assessments(record.record_id)
        self.application._maybe_archive(record, decision, assessments)
        archive = self.application.repository.get_archive(record.record_id)
        self.assertIsNotNone(archive)
        return record, decision, archive

    def test_archive_pins_record_and_decision_fingerprints(self):
        record, decision, archive = self._drive_to_archive()
        self.assertEqual(archive["record_fingerprint"], record.fingerprint)
        self.assertEqual(archive["record_version"], record.version)
        self.assertEqual(archive["decision_id"], decision.fingerprint)
        self.assertEqual(archive["decision_fingerprint"], decision.fingerprint)

    def test_archive_is_immutable_after_supplement(self):
        record, _, archive = self._drive_to_archive()
        pinned_fingerprint = archive["record_fingerprint"]
        supplement = {"records": [{
            "record_id": record.record_id,
            "payload": dict(record.payload) | {"source_quality": 99.0},
            "state": record.state, "source": "supplement"}]}
        result = self.application.supplement(supplement)
        self.assertIn(record.record_id, result["frozen_archives"])
        frozen = self.application.repository.get_archive(record.record_id)
        self.assertEqual(frozen["record_fingerprint"], pinned_fingerprint)
        current = self.application.repository.get_record(record.record_id)
        self.assertNotEqual(current.fingerprint, pinned_fingerprint)
        # 归档内钉住的仍是当时引用的证据版本。
        self.assertEqual(frozen["record"]["payload"]["source_quality"],
                         record.payload["source_quality"])
        # 归档只写一次，重复触发不会产生第二条。
        self.assertEqual(len(self.application.repository.list_archives()), 1)
        self.assertEqual(self.application.repository.verify_chain(), [])

    def test_archive_captures_objection_assessment_snapshot(self):
        record = self.application.repository.get_record(self.record.record_id)
        objection = Objection("obj-arch", record.record_id, "scope", "有依据",
                              (EvidenceRef("e1", "note", 0.7),),
                              EvidenceRef("r1", "rebuttal", 0.95),
                              chain_key=claim_chain_key(record))
        self.application.register_objection(objection)
        self.assertEqual(
            self.application.repository.latest_assessments(record.record_id)[0].status,
            RESPONDED)
        archived, _, archive = self._drive_to_archive()
        self.assertEqual(len(archive["objection_assessments"]), 1)
        self.assertEqual(archive["objection_assessments"][0]["status"], RESPONDED)
        self.assertTrue(archive["evidence_refs"])


if __name__ == "__main__":
    unittest.main()
