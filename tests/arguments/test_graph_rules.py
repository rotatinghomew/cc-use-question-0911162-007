from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from evidence_deliberation.claims.contract import ContractError, DomainRecord, RuleResult, bounded, stable_hash
from evidence_deliberation.arguments.graph_rules import RULE_INDEX, evaluate, summarize
from evidence_deliberation.options.frontier import METRICS, compare, grouped_metrics, metric_vector, portfolio, record_score

FIELDS = ['working_group', 'topic', 'source_kind', 'source_version', 'claim_id', 'claim_strength', 'evidence_direction', 'scope_condition', 'source_quality', 'reproducibility', 'member_count', 'interpretation_confidence']

def make_record(seed: int = 1, state: str | None = None) -> DomainRecord:
    payload = {}
    for index, field in enumerate(FIELDS):
        selector = (seed + index) % 4
        if selector == 0:
            payload[field] = seed * 9.5 + index * 1.25
        elif selector == 1:
            payload[field] = f'{field}-{seed % 5}'
        elif selector == 2:
            payload[field] = (seed + index) / 10.0
        else:
            payload[field] = (seed + index) % 2 == 0
    return DomainRecord(f'governance_claim-{seed:03d}', payload, state or 'submitted')

class RuleGroup2Tests(unittest.TestCase):
    def test_evaluate_returns_complete_catalog(self):
        record = make_record()
        results = evaluate(record, {})
        self.assertEqual(len(results), len(RULE_INDEX))
        self.assertTrue(all(isinstance(item, RuleResult) for item in results))
        self.assertTrue(all(0.0 <= item.score <= 1.0 for item in results))

    def test_summary_is_conservative_and_counted(self):
        results = evaluate(make_record(2), {'risk_weight': 0.8})
        summary = summarize(results)
        self.assertEqual(summary['passed'] + summary['failed'], len(results))
        self.assertGreaterEqual(summary['critical'], 0)
        self.assertGreaterEqual(summary['score'], 0.0)
        self.assertLessEqual(summary['score'], 1.0)

    def test_check_source_version_presence_02_01(self):
        record = make_record(4)
        result = RULE_INDEX['check_source_version_presence'](record, {'check_source_version_presence_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_presence')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_range_02_02(self):
        record = make_record(5)
        result = RULE_INDEX['check_source_version_range'](record, {'check_source_version_range_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_range')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_stability_02_03(self):
        record = make_record(6)
        result = RULE_INDEX['check_source_version_stability'](record, {'check_source_version_stability_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_stability')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_freshness_02_04(self):
        record = make_record(7)
        result = RULE_INDEX['check_source_version_freshness'](record, {'check_source_version_freshness_threshold': 4.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_freshness')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_coverage_02_05(self):
        record = make_record(8)
        result = RULE_INDEX['check_source_version_coverage'](record, {'check_source_version_coverage_threshold': 5.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_coverage')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_consistency_02_06(self):
        record = make_record(9)
        result = RULE_INDEX['check_source_version_consistency'](record, {'check_source_version_consistency_threshold': 6.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_consistency')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_risk_02_07(self):
        record = make_record(10)
        result = RULE_INDEX['check_source_version_risk'](record, {'check_source_version_risk_threshold': 7.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_risk')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_confidence_02_08(self):
        record = make_record(11)
        result = RULE_INDEX['check_source_version_confidence'](record, {'check_source_version_confidence_threshold': 8.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_confidence')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_dependency_02_09(self):
        record = make_record(12)
        result = RULE_INDEX['check_source_version_dependency'](record, {'check_source_version_dependency_threshold': 9.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_dependency')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_source_version_readiness_02_10(self):
        record = make_record(13)
        result = RULE_INDEX['check_source_version_readiness'](record, {'check_source_version_readiness_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_source_version_readiness')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_presence_02_11(self):
        record = make_record(14)
        result = RULE_INDEX['check_claim_id_presence'](record, {'check_claim_id_presence_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_presence')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_range_02_12(self):
        record = make_record(15)
        result = RULE_INDEX['check_claim_id_range'](record, {'check_claim_id_range_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_range')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_stability_02_13(self):
        record = make_record(16)
        result = RULE_INDEX['check_claim_id_stability'](record, {'check_claim_id_stability_threshold': 4.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_stability')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_freshness_02_14(self):
        record = make_record(17)
        result = RULE_INDEX['check_claim_id_freshness'](record, {'check_claim_id_freshness_threshold': 5.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_freshness')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_coverage_02_15(self):
        record = make_record(18)
        result = RULE_INDEX['check_claim_id_coverage'](record, {'check_claim_id_coverage_threshold': 6.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_coverage')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_consistency_02_16(self):
        record = make_record(19)
        result = RULE_INDEX['check_claim_id_consistency'](record, {'check_claim_id_consistency_threshold': 7.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_consistency')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_risk_02_17(self):
        record = make_record(20)
        result = RULE_INDEX['check_claim_id_risk'](record, {'check_claim_id_risk_threshold': 8.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_risk')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_confidence_02_18(self):
        record = make_record(21)
        result = RULE_INDEX['check_claim_id_confidence'](record, {'check_claim_id_confidence_threshold': 9.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_confidence')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_dependency_02_19(self):
        record = make_record(22)
        result = RULE_INDEX['check_claim_id_dependency'](record, {'check_claim_id_dependency_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_dependency')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_id_readiness_02_20(self):
        record = make_record(23)
        result = RULE_INDEX['check_claim_id_readiness'](record, {'check_claim_id_readiness_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_id_readiness')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_presence_02_21(self):
        record = make_record(24)
        result = RULE_INDEX['check_claim_strength_presence'](record, {'check_claim_strength_presence_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_presence')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_range_02_22(self):
        record = make_record(25)
        result = RULE_INDEX['check_claim_strength_range'](record, {'check_claim_strength_range_threshold': 4.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_range')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_stability_02_23(self):
        record = make_record(26)
        result = RULE_INDEX['check_claim_strength_stability'](record, {'check_claim_strength_stability_threshold': 5.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_stability')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_freshness_02_24(self):
        record = make_record(27)
        result = RULE_INDEX['check_claim_strength_freshness'](record, {'check_claim_strength_freshness_threshold': 6.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_freshness')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_coverage_02_25(self):
        record = make_record(28)
        result = RULE_INDEX['check_claim_strength_coverage'](record, {'check_claim_strength_coverage_threshold': 7.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_coverage')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_consistency_02_26(self):
        record = make_record(29)
        result = RULE_INDEX['check_claim_strength_consistency'](record, {'check_claim_strength_consistency_threshold': 8.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_consistency')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_risk_02_27(self):
        record = make_record(30)
        result = RULE_INDEX['check_claim_strength_risk'](record, {'check_claim_strength_risk_threshold': 9.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_risk')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_confidence_02_28(self):
        record = make_record(31)
        result = RULE_INDEX['check_claim_strength_confidence'](record, {'check_claim_strength_confidence_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_confidence')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_dependency_02_29(self):
        record = make_record(32)
        result = RULE_INDEX['check_claim_strength_dependency'](record, {'check_claim_strength_dependency_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_dependency')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_claim_strength_readiness_02_30(self):
        record = make_record(33)
        result = RULE_INDEX['check_claim_strength_readiness'](record, {'check_claim_strength_readiness_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_claim_strength_readiness')
        self.assertIn(result.claim_strength, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

class MetricGroup2Tests(unittest.TestCase):
    def test_metric_vector_is_deterministic(self):
        record = make_record(11)
        first = metric_vector(record, {})
        second = metric_vector(record, {})
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(METRICS))
        self.assertTrue(all(0.0 <= value <= 1.0 for value in first.values()))

    def test_grouped_metrics_match_business_catalog(self):
        grouped = grouped_metrics(make_record(4), {})
        self.assertEqual(set(grouped), {'translation_gap', 'release_priority', 'reproduction_confidence', 'deliberating_health', 'regional_impact', 'duplicate_density', 'experiment_value', 'rollback_risk'})
        self.assertTrue(all(math.isfinite(value) for value in grouped.values()))

    def test_portfolio_orders_by_descending_score(self):
        result = portfolio([make_record(2), make_record(3), make_record(4)])
        scores = [row['score'] for row in result['rows']]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(result['count'], 3)
        self.assertGreaterEqual(result['maximum'], result['minimum'])

    def test_compare_has_all_metric_deltas(self):
        result = compare(make_record(5), make_record(6))
        self.assertEqual(set(result['delta']), {'translation_gap', 'release_priority', 'reproduction_confidence', 'deliberating_health', 'regional_impact', 'duplicate_density', 'experiment_value', 'rollback_risk'})
        self.assertIn(result['winner'], {make_record(5).record_id, make_record(6).record_id})

    def test_score_fingerprint_changes_with_payload(self):
        left = record_score(make_record(7))
        right = record_score(make_record(8))
        self.assertNotEqual(left['fingerprint'], right['fingerprint'])
        self.assertNotEqual(stable_hash(left['metrics']), stable_hash(right['metrics']))

if __name__ == '__main__':
    unittest.main()
