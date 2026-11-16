from __future__ import annotations

import unittest
from evidence_deliberation.claims.contract import DomainRecord
from evidence_deliberation.arguments.evidence_merge import deliberating_health, clusters, similarity, tokens


class ClusterTests(unittest.TestCase):
    def record(self, key, symptom, working_group="th"):
        return DomainRecord(key, {"working_group": working_group, "topic": "durian", "source_kind": "r1", "source_version": "1",
            "claim_id": symptom, "claim_strength": 7, "evidence_direction": "wet", "scope_condition": "slope", "source_quality": 2,
            "reproducibility": .8, "member_count": 4, "interpretation_confidence": .9})

    def test_synonyms_cluster_across_languages(self):
        left, right = self.record("a", "stuck arm"), self.record("b", "卡住 arm")
        self.assertIn("blocked", tokens("卡住"))
        self.assertGreater(similarity(left, right), .5)
        self.assertEqual(len(clusters([left, right])), 1)

    def test_deliberating_health_tracks_risk(self):
        health = deliberating_health([self.record("a", "slow"), self.record("b", "lambat")])
        self.assertGreater(health["rollback_risk"], 0.0)
