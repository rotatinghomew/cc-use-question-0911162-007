from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from evidence_deliberation.claims.contract import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
        return float(min(100, len(text) + len(set(tokens)) * 5))

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    claim_strength = 'info' if passed else ('critical' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, claim_strength, message, evidence)

def check_working_group_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_working_group_presence_threshold', 10.333)
    return _result('check_working_group_presence', adjusted, threshold, True, 'validates working_group presence',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_working_group_range_threshold', 12.667)
    return _result('check_working_group_range', adjusted, threshold, True, 'validates working_group range',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_working_group_stability_threshold', 15.0)
    return _result('check_working_group_stability', adjusted, threshold, False, 'validates working_group stability',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_working_group_freshness_threshold', 17.333)
    return _result('check_working_group_freshness', adjusted, threshold, True, 'validates working_group freshness',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_working_group_coverage_threshold', 19.667)
    return _result('check_working_group_coverage', adjusted, threshold, True, 'validates working_group coverage',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_working_group_consistency_threshold', 22.0)
    return _result('check_working_group_consistency', adjusted, threshold, False, 'validates working_group consistency',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_working_group_risk_threshold', 24.333)
    return _result('check_working_group_risk', adjusted, threshold, True, 'validates working_group risk',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_working_group_confidence_threshold', 26.667)
    return _result('check_working_group_confidence', adjusted, threshold, True, 'validates working_group confidence',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_working_group_dependency_threshold', 29.0)
    return _result('check_working_group_dependency', adjusted, threshold, False, 'validates working_group dependency',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_working_group_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'working_group')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_working_group_readiness_threshold', 31.333)
    return _result('check_working_group_readiness', adjusted, threshold, True, 'validates working_group readiness',
                   {'field': 'working_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_topic_presence_threshold', 9.333)
    return _result('check_topic_presence', adjusted, threshold, True, 'validates topic presence',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_topic_range_threshold', 11.667)
    return _result('check_topic_range', adjusted, threshold, False, 'validates topic range',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_topic_stability_threshold', 14.0)
    return _result('check_topic_stability', adjusted, threshold, True, 'validates topic stability',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_topic_freshness_threshold', 16.333)
    return _result('check_topic_freshness', adjusted, threshold, True, 'validates topic freshness',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_topic_coverage_threshold', 18.667)
    return _result('check_topic_coverage', adjusted, threshold, False, 'validates topic coverage',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_topic_consistency_threshold', 21.0)
    return _result('check_topic_consistency', adjusted, threshold, True, 'validates topic consistency',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_topic_risk_threshold', 23.333)
    return _result('check_topic_risk', adjusted, threshold, True, 'validates topic risk',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_topic_confidence_threshold', 25.667)
    return _result('check_topic_confidence', adjusted, threshold, False, 'validates topic confidence',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_topic_dependency_threshold', 28.0)
    return _result('check_topic_dependency', adjusted, threshold, True, 'validates topic dependency',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_topic_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'topic')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_topic_readiness_threshold', 30.333)
    return _result('check_topic_readiness', adjusted, threshold, True, 'validates topic readiness',
                   {'field': 'topic', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_source_kind_presence_threshold', 8.333)
    return _result('check_source_kind_presence', adjusted, threshold, False, 'validates source_kind presence',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_source_kind_range_threshold', 10.667)
    return _result('check_source_kind_range', adjusted, threshold, True, 'validates source_kind range',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_source_kind_stability_threshold', 13.0)
    return _result('check_source_kind_stability', adjusted, threshold, True, 'validates source_kind stability',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_source_kind_freshness_threshold', 15.333)
    return _result('check_source_kind_freshness', adjusted, threshold, False, 'validates source_kind freshness',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_source_kind_coverage_threshold', 17.667)
    return _result('check_source_kind_coverage', adjusted, threshold, True, 'validates source_kind coverage',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_source_kind_consistency_threshold', 20.0)
    return _result('check_source_kind_consistency', adjusted, threshold, True, 'validates source_kind consistency',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_source_kind_risk_threshold', 22.333)
    return _result('check_source_kind_risk', adjusted, threshold, False, 'validates source_kind risk',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_source_kind_confidence_threshold', 24.667)
    return _result('check_source_kind_confidence', adjusted, threshold, True, 'validates source_kind confidence',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_source_kind_dependency_threshold', 27.0)
    return _result('check_source_kind_dependency', adjusted, threshold, True, 'validates source_kind dependency',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_kind_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_kind')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_source_kind_readiness_threshold', 29.333)
    return _result('check_source_kind_readiness', adjusted, threshold, False, 'validates source_kind readiness',
                   {'field': 'source_kind', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_source_version_presence_threshold', 31.667)
    return _result('check_source_version_presence', adjusted, threshold, True, 'validates source_version presence',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_source_version_range_threshold', 9.667)
    return _result('check_source_version_range', adjusted, threshold, True, 'validates source_version range',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_source_version_stability_threshold', 12.0)
    return _result('check_source_version_stability', adjusted, threshold, False, 'validates source_version stability',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_source_version_freshness_threshold', 14.333)
    return _result('check_source_version_freshness', adjusted, threshold, True, 'validates source_version freshness',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_source_version_coverage_threshold', 16.667)
    return _result('check_source_version_coverage', adjusted, threshold, True, 'validates source_version coverage',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_source_version_consistency_threshold', 19.0)
    return _result('check_source_version_consistency', adjusted, threshold, False, 'validates source_version consistency',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_source_version_risk_threshold', 21.333)
    return _result('check_source_version_risk', adjusted, threshold, True, 'validates source_version risk',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_source_version_confidence_threshold', 23.667)
    return _result('check_source_version_confidence', adjusted, threshold, True, 'validates source_version confidence',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_source_version_dependency_threshold', 26.0)
    return _result('check_source_version_dependency', adjusted, threshold, False, 'validates source_version dependency',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_version_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_version')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_source_version_readiness_threshold', 28.333)
    return _result('check_source_version_readiness', adjusted, threshold, True, 'validates source_version readiness',
                   {'field': 'source_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_claim_id_presence_threshold', 30.667)
    return _result('check_claim_id_presence', adjusted, threshold, True, 'validates claim_id presence',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_claim_id_range_threshold', 8.667)
    return _result('check_claim_id_range', adjusted, threshold, False, 'validates claim_id range',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_claim_id_stability_threshold', 11.0)
    return _result('check_claim_id_stability', adjusted, threshold, True, 'validates claim_id stability',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_claim_id_freshness_threshold', 13.333)
    return _result('check_claim_id_freshness', adjusted, threshold, True, 'validates claim_id freshness',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_claim_id_coverage_threshold', 15.667)
    return _result('check_claim_id_coverage', adjusted, threshold, False, 'validates claim_id coverage',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_claim_id_consistency_threshold', 18.0)
    return _result('check_claim_id_consistency', adjusted, threshold, True, 'validates claim_id consistency',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_claim_id_risk_threshold', 20.333)
    return _result('check_claim_id_risk', adjusted, threshold, True, 'validates claim_id risk',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_claim_id_confidence_threshold', 22.667)
    return _result('check_claim_id_confidence', adjusted, threshold, False, 'validates claim_id confidence',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_claim_id_dependency_threshold', 25.0)
    return _result('check_claim_id_dependency', adjusted, threshold, True, 'validates claim_id dependency',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_id_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_id')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_claim_id_readiness_threshold', 27.333)
    return _result('check_claim_id_readiness', adjusted, threshold, True, 'validates claim_id readiness',
                   {'field': 'claim_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_claim_strength_presence_threshold', 29.667)
    return _result('check_claim_strength_presence', adjusted, threshold, False, 'validates claim_strength presence',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_claim_strength_range_threshold', 32.0)
    return _result('check_claim_strength_range', adjusted, threshold, True, 'validates claim_strength range',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_claim_strength_stability_threshold', 10.0)
    return _result('check_claim_strength_stability', adjusted, threshold, True, 'validates claim_strength stability',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_claim_strength_freshness_threshold', 12.333)
    return _result('check_claim_strength_freshness', adjusted, threshold, False, 'validates claim_strength freshness',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_claim_strength_coverage_threshold', 14.667)
    return _result('check_claim_strength_coverage', adjusted, threshold, True, 'validates claim_strength coverage',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_claim_strength_consistency_threshold', 17.0)
    return _result('check_claim_strength_consistency', adjusted, threshold, True, 'validates claim_strength consistency',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_claim_strength_risk_threshold', 19.333)
    return _result('check_claim_strength_risk', adjusted, threshold, False, 'validates claim_strength risk',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_claim_strength_confidence_threshold', 21.667)
    return _result('check_claim_strength_confidence', adjusted, threshold, True, 'validates claim_strength confidence',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_claim_strength_dependency_threshold', 24.0)
    return _result('check_claim_strength_dependency', adjusted, threshold, True, 'validates claim_strength dependency',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_claim_strength_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'claim_strength')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_claim_strength_readiness_threshold', 26.333)
    return _result('check_claim_strength_readiness', adjusted, threshold, False, 'validates claim_strength readiness',
                   {'field': 'claim_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_evidence_direction_presence_threshold', 28.667)
    return _result('check_evidence_direction_presence', adjusted, threshold, True, 'validates evidence_direction presence',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_evidence_direction_range_threshold', 31.0)
    return _result('check_evidence_direction_range', adjusted, threshold, True, 'validates evidence_direction range',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_evidence_direction_stability_threshold', 9.0)
    return _result('check_evidence_direction_stability', adjusted, threshold, False, 'validates evidence_direction stability',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_evidence_direction_freshness_threshold', 11.333)
    return _result('check_evidence_direction_freshness', adjusted, threshold, True, 'validates evidence_direction freshness',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_evidence_direction_coverage_threshold', 13.667)
    return _result('check_evidence_direction_coverage', adjusted, threshold, True, 'validates evidence_direction coverage',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_evidence_direction_consistency_threshold', 16.0)
    return _result('check_evidence_direction_consistency', adjusted, threshold, False, 'validates evidence_direction consistency',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_evidence_direction_risk_threshold', 18.333)
    return _result('check_evidence_direction_risk', adjusted, threshold, True, 'validates evidence_direction risk',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_evidence_direction_confidence_threshold', 20.667)
    return _result('check_evidence_direction_confidence', adjusted, threshold, True, 'validates evidence_direction confidence',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_evidence_direction_dependency_threshold', 23.0)
    return _result('check_evidence_direction_dependency', adjusted, threshold, False, 'validates evidence_direction dependency',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_direction_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_direction')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_evidence_direction_readiness_threshold', 25.333)
    return _result('check_evidence_direction_readiness', adjusted, threshold, True, 'validates evidence_direction readiness',
                   {'field': 'evidence_direction', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_scope_condition_presence_threshold', 27.667)
    return _result('check_scope_condition_presence', adjusted, threshold, True, 'validates scope_condition presence',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_scope_condition_range_threshold', 30.0)
    return _result('check_scope_condition_range', adjusted, threshold, False, 'validates scope_condition range',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_scope_condition_stability_threshold', 8.0)
    return _result('check_scope_condition_stability', adjusted, threshold, True, 'validates scope_condition stability',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_scope_condition_freshness_threshold', 10.333)
    return _result('check_scope_condition_freshness', adjusted, threshold, True, 'validates scope_condition freshness',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_scope_condition_coverage_threshold', 12.667)
    return _result('check_scope_condition_coverage', adjusted, threshold, False, 'validates scope_condition coverage',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_scope_condition_consistency_threshold', 15.0)
    return _result('check_scope_condition_consistency', adjusted, threshold, True, 'validates scope_condition consistency',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_scope_condition_risk_threshold', 17.333)
    return _result('check_scope_condition_risk', adjusted, threshold, True, 'validates scope_condition risk',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_scope_condition_confidence_threshold', 19.667)
    return _result('check_scope_condition_confidence', adjusted, threshold, False, 'validates scope_condition confidence',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_scope_condition_dependency_threshold', 22.0)
    return _result('check_scope_condition_dependency', adjusted, threshold, True, 'validates scope_condition dependency',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_scope_condition_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'scope_condition')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_scope_condition_readiness_threshold', 24.333)
    return _result('check_scope_condition_readiness', adjusted, threshold, True, 'validates scope_condition readiness',
                   {'field': 'scope_condition', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_source_quality_presence_threshold', 26.667)
    return _result('check_source_quality_presence', adjusted, threshold, False, 'validates source_quality presence',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_source_quality_range_threshold', 29.0)
    return _result('check_source_quality_range', adjusted, threshold, True, 'validates source_quality range',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_source_quality_stability_threshold', 31.333)
    return _result('check_source_quality_stability', adjusted, threshold, True, 'validates source_quality stability',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_source_quality_freshness_threshold', 9.333)
    return _result('check_source_quality_freshness', adjusted, threshold, False, 'validates source_quality freshness',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_source_quality_coverage_threshold', 11.667)
    return _result('check_source_quality_coverage', adjusted, threshold, True, 'validates source_quality coverage',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_source_quality_consistency_threshold', 14.0)
    return _result('check_source_quality_consistency', adjusted, threshold, True, 'validates source_quality consistency',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_source_quality_risk_threshold', 16.333)
    return _result('check_source_quality_risk', adjusted, threshold, False, 'validates source_quality risk',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_source_quality_confidence_threshold', 18.667)
    return _result('check_source_quality_confidence', adjusted, threshold, True, 'validates source_quality confidence',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_source_quality_dependency_threshold', 21.0)
    return _result('check_source_quality_dependency', adjusted, threshold, True, 'validates source_quality dependency',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_quality_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_quality')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_source_quality_readiness_threshold', 23.333)
    return _result('check_source_quality_readiness', adjusted, threshold, False, 'validates source_quality readiness',
                   {'field': 'source_quality', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_reproducibility_presence_threshold', 25.667)
    return _result('check_reproducibility_presence', adjusted, threshold, True, 'validates reproducibility presence',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_reproducibility_range_threshold', 28.0)
    return _result('check_reproducibility_range', adjusted, threshold, True, 'validates reproducibility range',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_reproducibility_stability_threshold', 30.333)
    return _result('check_reproducibility_stability', adjusted, threshold, False, 'validates reproducibility stability',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_reproducibility_freshness_threshold', 8.333)
    return _result('check_reproducibility_freshness', adjusted, threshold, True, 'validates reproducibility freshness',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_reproducibility_coverage_threshold', 10.667)
    return _result('check_reproducibility_coverage', adjusted, threshold, True, 'validates reproducibility coverage',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_reproducibility_consistency_threshold', 13.0)
    return _result('check_reproducibility_consistency', adjusted, threshold, False, 'validates reproducibility consistency',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_reproducibility_risk_threshold', 15.333)
    return _result('check_reproducibility_risk', adjusted, threshold, True, 'validates reproducibility risk',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_reproducibility_confidence_threshold', 17.667)
    return _result('check_reproducibility_confidence', adjusted, threshold, True, 'validates reproducibility confidence',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_reproducibility_dependency_threshold', 20.0)
    return _result('check_reproducibility_dependency', adjusted, threshold, False, 'validates reproducibility dependency',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_reproducibility_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'reproducibility')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_reproducibility_readiness_threshold', 22.333)
    return _result('check_reproducibility_readiness', adjusted, threshold, True, 'validates reproducibility readiness',
                   {'field': 'reproducibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_member_count_presence_threshold', 24.667)
    return _result('check_member_count_presence', adjusted, threshold, True, 'validates member_count presence',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_member_count_range_threshold', 27.0)
    return _result('check_member_count_range', adjusted, threshold, False, 'validates member_count range',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_member_count_stability_threshold', 29.333)
    return _result('check_member_count_stability', adjusted, threshold, True, 'validates member_count stability',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_member_count_freshness_threshold', 31.667)
    return _result('check_member_count_freshness', adjusted, threshold, True, 'validates member_count freshness',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_member_count_coverage_threshold', 9.667)
    return _result('check_member_count_coverage', adjusted, threshold, False, 'validates member_count coverage',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_member_count_consistency_threshold', 12.0)
    return _result('check_member_count_consistency', adjusted, threshold, True, 'validates member_count consistency',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_member_count_risk_threshold', 14.333)
    return _result('check_member_count_risk', adjusted, threshold, True, 'validates member_count risk',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_member_count_confidence_threshold', 16.667)
    return _result('check_member_count_confidence', adjusted, threshold, False, 'validates member_count confidence',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_member_count_dependency_threshold', 19.0)
    return _result('check_member_count_dependency', adjusted, threshold, True, 'validates member_count dependency',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_member_count_readiness_threshold', 21.333)
    return _result('check_member_count_readiness', adjusted, threshold, True, 'validates member_count readiness',
                   {'field': 'member_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_interpretation_confidence_presence_threshold', 23.667)
    return _result('check_interpretation_confidence_presence', adjusted, threshold, False, 'validates interpretation_confidence presence',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_interpretation_confidence_range_threshold', 26.0)
    return _result('check_interpretation_confidence_range', adjusted, threshold, True, 'validates interpretation_confidence range',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_interpretation_confidence_stability_threshold', 28.333)
    return _result('check_interpretation_confidence_stability', adjusted, threshold, True, 'validates interpretation_confidence stability',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_interpretation_confidence_freshness_threshold', 30.667)
    return _result('check_interpretation_confidence_freshness', adjusted, threshold, False, 'validates interpretation_confidence freshness',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_interpretation_confidence_coverage_threshold', 8.667)
    return _result('check_interpretation_confidence_coverage', adjusted, threshold, True, 'validates interpretation_confidence coverage',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_interpretation_confidence_consistency_threshold', 11.0)
    return _result('check_interpretation_confidence_consistency', adjusted, threshold, True, 'validates interpretation_confidence consistency',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_interpretation_confidence_risk_threshold', 13.333)
    return _result('check_interpretation_confidence_risk', adjusted, threshold, False, 'validates interpretation_confidence risk',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_interpretation_confidence_confidence_threshold', 15.667)
    return _result('check_interpretation_confidence_confidence', adjusted, threshold, True, 'validates interpretation_confidence confidence',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_interpretation_confidence_dependency_threshold', 18.0)
    return _result('check_interpretation_confidence_dependency', adjusted, threshold, True, 'validates interpretation_confidence dependency',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_interpretation_confidence_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'interpretation_confidence')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_interpretation_confidence_readiness_threshold', 20.333)
    return _result('check_interpretation_confidence_readiness', adjusted, threshold, False, 'validates interpretation_confidence readiness',
                   {'field': 'interpretation_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_working_group_presence,
    check_working_group_range,
    check_working_group_stability,
    check_working_group_freshness,
    check_working_group_coverage,
    check_working_group_consistency,
    check_working_group_risk,
    check_working_group_confidence,
    check_working_group_dependency,
    check_working_group_readiness,
    check_topic_presence,
    check_topic_range,
    check_topic_stability,
    check_topic_freshness,
    check_topic_coverage,
    check_topic_consistency,
    check_topic_risk,
    check_topic_confidence,
    check_topic_dependency,
    check_topic_readiness,
    check_source_kind_presence,
    check_source_kind_range,
    check_source_kind_stability,
    check_source_kind_freshness,
    check_source_kind_coverage,
    check_source_kind_consistency,
    check_source_kind_risk,
    check_source_kind_confidence,
    check_source_kind_dependency,
    check_source_kind_readiness,
    check_source_version_presence,
    check_source_version_range,
    check_source_version_stability,
    check_source_version_freshness,
    check_source_version_coverage,
    check_source_version_consistency,
    check_source_version_risk,
    check_source_version_confidence,
    check_source_version_dependency,
    check_source_version_readiness,
    check_claim_id_presence,
    check_claim_id_range,
    check_claim_id_stability,
    check_claim_id_freshness,
    check_claim_id_coverage,
    check_claim_id_consistency,
    check_claim_id_risk,
    check_claim_id_confidence,
    check_claim_id_dependency,
    check_claim_id_readiness,
    check_claim_strength_presence,
    check_claim_strength_range,
    check_claim_strength_stability,
    check_claim_strength_freshness,
    check_claim_strength_coverage,
    check_claim_strength_consistency,
    check_claim_strength_risk,
    check_claim_strength_confidence,
    check_claim_strength_dependency,
    check_claim_strength_readiness,
    check_evidence_direction_presence,
    check_evidence_direction_range,
    check_evidence_direction_stability,
    check_evidence_direction_freshness,
    check_evidence_direction_coverage,
    check_evidence_direction_consistency,
    check_evidence_direction_risk,
    check_evidence_direction_confidence,
    check_evidence_direction_dependency,
    check_evidence_direction_readiness,
    check_scope_condition_presence,
    check_scope_condition_range,
    check_scope_condition_stability,
    check_scope_condition_freshness,
    check_scope_condition_coverage,
    check_scope_condition_consistency,
    check_scope_condition_risk,
    check_scope_condition_confidence,
    check_scope_condition_dependency,
    check_scope_condition_readiness,
    check_source_quality_presence,
    check_source_quality_range,
    check_source_quality_stability,
    check_source_quality_freshness,
    check_source_quality_coverage,
    check_source_quality_consistency,
    check_source_quality_risk,
    check_source_quality_confidence,
    check_source_quality_dependency,
    check_source_quality_readiness,
    check_reproducibility_presence,
    check_reproducibility_range,
    check_reproducibility_stability,
    check_reproducibility_freshness,
    check_reproducibility_coverage,
    check_reproducibility_consistency,
    check_reproducibility_risk,
    check_reproducibility_confidence,
    check_reproducibility_dependency,
    check_reproducibility_readiness,
    check_member_count_presence,
    check_member_count_range,
    check_member_count_stability,
    check_member_count_freshness,
    check_member_count_coverage,
    check_member_count_consistency,
    check_member_count_risk,
    check_member_count_confidence,
    check_member_count_dependency,
    check_member_count_readiness,
    check_interpretation_confidence_presence,
    check_interpretation_confidence_range,
    check_interpretation_confidence_stability,
    check_interpretation_confidence_freshness,
    check_interpretation_confidence_coverage,
    check_interpretation_confidence_consistency,
    check_interpretation_confidence_risk,
    check_interpretation_confidence_confidence,
    check_interpretation_confidence_dependency,
    check_interpretation_confidence_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'critical': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'critical': sum(item.claim_strength == 'critical' for item in results)}
