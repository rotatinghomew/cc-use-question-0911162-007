from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from evidence_deliberation.claims.contract import Decision, DomainRecord, canonical_json, stable_hash, utc_now
from evidence_deliberation.dissent.objections import (
    BLOCKING_STATUSES,
    OBJECTION_STATUSES,
    Objection,
    ObjectionAssessment,
    status_counts,
    unresolved,
    worst_status,
)


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(body + "\n", encoding="utf-8")
    return stable_hash(value)


def write_records(path: Path, records: Iterable[DomainRecord], decisions: Mapping[str, Decision],
                  dissent_by_record: Mapping[str, str] | None = None) -> int:
    dissent_by_record = dissent_by_record or {}
    rows = []
    for record in records:
        decision = decisions.get(record.record_id)
        rows.append({"record_id": record.record_id, "state": record.state, "version": record.version,
                     "source": record.source, "fingerprint": record.fingerprint,
                     "outcome": decision.outcome if decision else "", "score": decision.score if decision else "",
                     "dissent_status": dissent_by_record.get(record.record_id, "")})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "state", "version", "source",
                                                     "fingerprint", "outcome", "score", "dissent_status"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_rules(path: Path, decisions: Mapping[str, Decision]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "code", "passed", "score", "claim_strength", "message"])
        writer.writeheader()
        for record_id, decision in sorted(decisions.items()):
            for result in decision.rule_results:
                writer.writerow({"record_id": record_id, "code": result.code, "passed": result.passed,
                                 "score": result.score, "claim_strength": result.claim_strength, "message": result.message})
                count += 1
    return count


def build_dissent_section(assessments: Sequence[ObjectionAssessment],
                          archives: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    latest: dict[str, ObjectionAssessment] = {}
    for assessment in assessments:
        previous = latest.get(assessment.objection_id)
        if previous is None or (assessment.objection_version, assessment.target_version) >= \
                (previous.objection_version, previous.target_version):
            latest[assessment.objection_id] = assessment
    current = sorted(latest.values(), key=lambda item: item.objection_id)
    open_items = unresolved(current)
    by_record: dict[str, list[str]] = {}
    for assessment in current:
        by_record.setdefault(assessment.target_record_id, []).append(assessment.status)
    archived = list(archives or [])
    return {
        "objection_count": len(latest),
        "status_counts": status_counts(current),
        "dissent_by_record": {record_id: worst_status(statuses)
                              for record_id, statuses in sorted(by_record.items())},
        "unresolved": [
            {"objection_id": item.objection_id, "target_record_id": item.target_record_id,
             "target_version": item.target_version, "chain_key": item.chain_key,
             "status": item.status, "evidence_ids": list(item.evidence_ids),
             "objection_weight": item.objection_weight, "rationale": item.rationale}
            for item in open_items
        ],
        "release_gate": {
            "releasable": not open_items,
            "blocking_count": len(open_items),
            "blocking_statuses": sorted({item.status for item in open_items}),
            "reasons": [f"{item.objection_id}->{item.target_record_id}@v{item.target_version}:{item.status}"
                        for item in open_items],
        },
        "archived_resolutions": [
            {"record_id": archive["record_id"], "record_version": archive["record_version"],
             "decision_id": archive["decision_id"], "record_fingerprint": archive["record_fingerprint"],
             "decision_fingerprint": archive["decision_fingerprint"],
             "evidence_refs": archive.get("evidence_refs", []),
             "objection_count": len(archive.get("objection_assessments", []))}
            for archive in archived
        ],
    }


def build_summary(records: list[DomainRecord], decisions: Mapping[str, Decision], snapshot: Mapping[str, Any],
                  assessments: Sequence[ObjectionAssessment] | None = None,
                  archives: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    outcomes: dict[str, int] = {}
    for decision in decisions.values():
        outcomes[decision.outcome] = outcomes.get(decision.outcome, 0) + 1
    scores = [decision.score for decision in decisions.values()]
    dissent = build_dissent_section(assessments or [], archives)
    gate = dissent["release_gate"]
    summary = {"product": '多边人工智能治理证据审议与异议保全台', "entity": 'governance_claim', "generated_at": utc_now(),
               "record_count": len(records), "decision_count": len(decisions), "outcomes": outcomes,
               "average_score": sum(scores) / len(scores) if scores else 0.0,
               "minimum_score": min(scores) if scores else 0.0, "maximum_score": max(scores) if scores else 0.0,
               "release_gate": gate, "dissent": dissent, "repository": snapshot}
    # 发布状态必须由异议状态决定：存在未解决反驳时整份决议不可发布。
    summary["release_status"] = "releasable" if gate["releasable"] else "withheld"
    return summary


def write_objections(path: Path, objections: Iterable[Objection],
                     assessments: Sequence[ObjectionAssessment]) -> int:
    latest: dict[str, ObjectionAssessment] = {}
    for assessment in assessments:
        previous = latest.get(assessment.objection_id)
        if previous is None or (assessment.objection_version, assessment.target_version) >= \
                (previous.objection_version, previous.target_version):
            latest[assessment.objection_id] = assessment
    rows = []
    for objection in sorted(objections, key=lambda item: item.objection_id):
        assessment = latest.get(objection.objection_id)
        rows.append({"objection_id": objection.objection_id, "target_record_id": objection.target_record_id,
                     "chain_key": objection.chain_key, "basis": objection.basis,
                     "version": objection.version, "weight": round(objection.weight, 6),
                     "evidence_ids": "|".join(objection.evidence_ids),
                     "response_id": objection.response.evidence_id if objection.response else "",
                     "status": assessment.status if assessment else "",
                     "target_version": assessment.target_version if assessment else "",
                     "target_fingerprint": assessment.target_fingerprint if assessment else ""})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["objection_id", "target_record_id", "chain_key",
                                                     "basis", "version", "weight", "evidence_ids",
                                                     "response_id", "status", "target_version",
                                                     "target_fingerprint"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def export_bundle(output: str | Path, records: list[DomainRecord], decisions: Mapping[str, Decision],
                  snapshot: Mapping[str, Any], events: list[dict[str, Any]],
                  objections: Sequence[Objection] | None = None,
                  assessments: Sequence[ObjectionAssessment] | None = None,
                  archives: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    root = ensure_output(output)
    objections = list(objections or [])
    assessments = list(assessments or [])
    archives = list(archives or [])
    dissent = build_dissent_section(assessments, archives)
    summary = build_summary(records, decisions, snapshot, assessments, archives)
    record_count = write_records(root / "records.csv", records, decisions, dissent["dissent_by_record"])
    rule_count = write_rules(root / "rules.csv", decisions)
    objection_count = write_objections(root / "objections.csv", objections, assessments)
    summary_hash = write_json(root / "summary.json", summary)
    decision_hash = write_json(root / "decisions.json", [value.as_dict() for _, value in sorted(decisions.items())])
    event_hash = write_json(root / "audit-events.json", events)
    assessment_hash = write_json(root / "objection-assessments.json",
                                 [item.as_dict() for item in assessments])
    archive_hash = write_json(root / "resolution-archives.json", archives)
    manifest = {"files": {"summary.json": summary_hash, "decisions.json": decision_hash,
                           "audit-events.json": event_hash,
                           "objection-assessments.json": assessment_hash,
                           "resolution-archives.json": archive_hash},
                "record_rows": record_count, "rule_rows": rule_count,
                "objection_rows": objection_count, "created_at": utc_now()}
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


def verify_bundle(output: str | Path) -> list[str]:
    root = Path(output)
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return ["manifest.json is missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_hash = manifest.pop("manifest_hash", "")
    if stable_hash(manifest) != expected_manifest_hash:
        errors.append("manifest hash mismatch")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if stable_hash(value) != expected:
            errors.append(f"{name} hash mismatch")
    return errors
