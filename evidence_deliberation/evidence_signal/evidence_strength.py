from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class DomainSignal:
    code: str
    score: float
    severity: str
    evidence: dict[str, Any]

def number(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
    return default if value != value or value in (float('inf'), float('-inf')) else value

def ratio(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = number(payload, key, default)
    if value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))

def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

def evidence_strength(payload:Mapping[str,Any])->DomainSignal:
    quality=ratio(payload,'source_quality'); reproducibility=ratio(payload,'reproducibility'); interpretation=ratio(payload,'interpretation_confidence'); members=max(1.0,number(payload,'member_count',1)); claim=ratio(payload,'claim_strength')
    direction=str(payload.get('evidence_direction','support')).lower(); polarity=-1.0 if direction in {'against','rebuttal','contradict'} else 1.0
    base=quality*.38+reproducibility*.34+interpretation*.18+min(1.0,members/38.0)*.10
    signed=clamp(.5+polarity*base*claim*.5); severity='critical' if interpretation<.3 else 'warning' if reproducibility<.5 else 'info'
    return DomainSignal('evidence_strength',signed,severity,{'polarity':polarity,'source_quality':quality,'reproducibility':reproducibility,'member_share':min(1.0,members/38.0)})

def peer_distribution(records:Iterable[Any],group_field:str='working_group')->dict[str,Any]:
    rows=[evidence_strength(getattr(r,'payload',r)) for r in records]
    return {'count':len(rows),'support':sum(s.evidence['polarity']>0 for s in rows),'rebuttal':sum(s.evidence['polarity']<0 for s in rows),'average':sum(s.score for s in rows)/len(rows) if rows else 0.0}

def augment_context(record:Any,repository:Any)->dict[str,Any]:
    signal=evidence_strength(record.payload); peers=peer_distribution(repository.list_records())
    return {'domain_signal':signal.score,'domain_severity':signal.severity,'rebuttal_count':peers['rebuttal'],'peer_average':peers['average']}
