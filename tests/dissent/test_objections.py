from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evidence_deliberation.claims.contract import ContractError, DomainRecord
from evidence_deliberation.dissent.objections import (
    BLOCKING_STATUSES,
    DISPUTED,
    INSUFFICIENT,
    OBJECTION_STATUSES,
    RESPONDED,
    EvidenceRef,
    Objection,
    ObjectionAssessment,
    assess_objection,
    claim_chain_key,
    objections_from_fixture,
    status_counts,
    unresolved,
    worst_status,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "objections.json"
SUPPLEMENT = Path(__file__).resolve().parents[2] / "fixtures" / "supplement.json"


def make_record(record_id: str = "governance_claim-x", claim: str = "claim-chain-alpha",
                topic: str = "topic-1", scope: str = "scope-condition-2") -> DomainRecord:
    payload = {"working_group": "wg", "topic": topic, "source_kind": "kind",
               "source_version": "v1", "claim_id": claim, "claim_strength": 50.0,
               "evidence_direction": "support", "scope_condition": scope,
               "source_quality": 60.0, "reproducibility": 0.7, "member_count": 30.0,
               "interpretation_confidence": 0.8}
    return DomainRecord(record_id, payload, "submitted")


class EvidenceRefTests(unittest.TestCase):
    def test_weight_is_bounded_and_optional(self):
        ref = EvidenceRef("evidence-1", "note", 1.7)
        self.assertEqual(ref.weight, 1.0)
        self.assertIsNone(EvidenceRef("evidence-2").weight)
        with self.assertRaises(ContractError):
            EvidenceRef("   ")

    def test_round_trip_and_fingerprint(self):
        ref = EvidenceRef("evidence-3", "translation", 0.6, "detail")
        self.assertEqual(EvidenceRef.from_dict(ref.as_dict()), ref)
        self.assertTrue(ref.fingerprint)


class ObjectionAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.record = make_record()

    def test_objection_without_evidence_is_insufficient(self):
        objection = Objection("obj-1", self.record.record_id, "translation", "无材料异议", ())
        assessment = assess_objection(objection, self.record)
        self.assertEqual(assessment.status, INSUFFICIENT)
        self.assertEqual(assessment.objection_weight, 0.0)
        self.assertEqual(assessment.evidence_ids, ())

    def test_weak_evidence_is_insufficient(self):
        objection = Objection("obj-2", self.record.record_id, "scope", "弱材料",
                              (EvidenceRef("e", "note", 0.1),))
        self.assertEqual(assess_objection(objection, self.record).status, INSUFFICIENT)

    def test_supported_objection_without_response_is_disputed(self):
        objection = Objection("obj-3", self.record.record_id, "translation", "有依据",
                              (EvidenceRef("e1", "note", 0.8), EvidenceRef("e2", "note", 0.6)))
        assessment = assess_objection(objection, self.record)
        self.assertEqual(assessment.status, DISPUTED)
        self.assertAlmostEqual(assessment.objection_weight, 0.7)
        self.assertEqual(assessment.evidence_ids, ("e1", "e2"))

    def test_strong_response_resolves_disputed_objection(self):
        objection = Objection("obj-4", self.record.record_id, "scope", "有依据",
                              (EvidenceRef("e1", "note", 0.8),),
                              EvidenceRef("r1", "rebuttal", 0.9))
        self.assertEqual(assess_objection(objection, self.record).status, RESPONDED)

    def test_weak_response_keeps_objection_disputed(self):
        objection = Objection("obj-5", self.record.record_id, "scope", "有依据",
                              (EvidenceRef("e1", "note", 0.8),),
                              EvidenceRef("r1", "rebuttal", 0.4))
        self.assertEqual(assess_objection(objection, self.record).status, DISPUTED)

    def test_strong_response_also_resolves_insufficient_objection(self):
        objection = Objection("obj-6", self.record.record_id, "translation", "证据不足",
                              (EvidenceRef("e1", "note", 0.12),),
                              EvidenceRef("r1", "registry", 0.88))
        self.assertEqual(assess_objection(objection, self.record).status, RESPONDED)

    def test_assessment_pins_target_version_and_fingerprint(self):
        objection = Objection("obj-7", self.record.record_id, "scope", "有依据",
                              (EvidenceRef("e1", "note", 0.7),))
        assessment = assess_objection(objection, self.record)
        self.assertEqual(assessment.target_version, self.record.version)
        self.assertEqual(assessment.target_fingerprint, self.record.fingerprint)
        self.assertTrue(assessment.fingerprint)

    def test_evidence_changed_flag_tracks_record_evolution(self):
        objection = Objection("obj-8", self.record.record_id, "scope", "有依据",
                              (EvidenceRef("e1", "note", 0.7),))
        first = assess_objection(objection, self.record)
        changed_record = self.record.with_payload({"source_quality": 90.0})
        second = assess_objection(objection, changed_record, first)
        self.assertTrue(second.evidence_changed)
        self.assertNotEqual(second.target_fingerprint, first.target_fingerprint)

    def test_target_mismatch_is_rejected(self):
        objection = Objection("obj-9", "governance_claim-other", "scope", "x",
                              (EvidenceRef("e1", "note", 0.7),))
        with self.assertRaisesRegex(ContractError, "target does not match"):
            assess_objection(objection, self.record)

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(ContractError):
            ObjectionAssessment("obj", 1, self.record.record_id, 1, "fp", "chain",
                                "mystery", 0.5, None, (), "", "why", False)

    def test_chain_key_groups_same_claim_topic_scope(self):
        left = make_record("a", "claim-x", "topic-1", "scope-1")
        right = make_record("b", "claim-x", "topic-1", "scope-1")
        other = make_record("c", "claim-y", "topic-1", "scope-1")
        self.assertEqual(claim_chain_key(left), claim_chain_key(right))
        self.assertNotEqual(claim_chain_key(left), claim_chain_key(other))


class FixtureParsingTests(unittest.TestCase):
    def test_fixture_objections_resolve_chain_and_target(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        records = {r.record_id: r for r in
                   [DomainRecord.from_dict(item) for item in fixture["records"]]}
        objections = objections_from_fixture(fixture, records)
        self.assertEqual(len(objections), 4)
        self.assertTrue(all(obj.chain_key for obj in objections))
        self.assertTrue(all(obj.target_record_id in records for obj in objections))

    def test_unknown_target_is_rejected(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ContractError, "unknown record"):
            objections_from_fixture(fixture, {})

    def test_duplicate_identifiers_are_rejected(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        records = {r.record_id: r for r in
                   [DomainRecord.from_dict(item) for item in fixture["records"]]}
        fixture["objections"][1]["objection_id"] = fixture["objections"][0]["objection_id"]
        with self.assertRaisesRegex(ContractError, "duplicate objection"):
            objections_from_fixture(fixture, records)


class SummaryHelperTests(unittest.TestCase):
    def _assessment(self, objection_id: str, status: str) -> ObjectionAssessment:
        return ObjectionAssessment(objection_id, 1, "record-1", 1, "fp", "chain",
                                   status, 0.6, None, ("e1",), "", "why", False)

    def test_status_counts_and_worst_status(self):
        assessments = [self._assessment("a", RESPONDED), self._assessment("b", DISPUTED),
                       self._assessment("c", INSUFFICIENT)]
        self.assertEqual(status_counts(assessments),
                         {RESPONDED: 1, DISPUTED: 1, INSUFFICIENT: 1})
        self.assertEqual(worst_status([RESPONDED, INSUFFICIENT]), INSUFFICIENT)
        self.assertEqual(worst_status([RESPONDED, DISPUTED]), DISPUTED)
        self.assertEqual(worst_status([RESPONDED]), RESPONDED)

    def test_unresolved_keeps_latest_version_only(self):
        old = ObjectionAssessment("a", 1, "r", 1, "fp1", "c", DISPUTED, 0.6, None, (), "", "", False)
        new = ObjectionAssessment("a", 2, "r", 2, "fp2", "c", RESPONDED, 0.6, 0.9, (), "r1", "", False)
        self.assertEqual(unresolved([old, new]), [])
        open_items = unresolved([old])
        self.assertEqual(len(open_items), 1)
        self.assertEqual(open_items[0].status, DISPUTED)

    def test_blocking_statuses_are_stable_contract(self):
        self.assertEqual(set(OBJECTION_STATUSES), {RESPONDED, DISPUTED, INSUFFICIENT})
        self.assertEqual(set(BLOCKING_STATUSES), {DISPUTED, INSUFFICIENT})


if __name__ == "__main__":
    unittest.main()
