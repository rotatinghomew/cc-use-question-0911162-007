from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from evidence_deliberation.claims.contract import DomainRecord, bounded, finite_number, normalized_text


SYNONYMS = {"stuck": "blocked", "jammed": "blocked", "卡住": "blocked", "atascado": "blocked",
            "slow": "latency", "延迟": "latency", "lambat": "latency", "overheat": "thermal", "过热": "thermal"}


def tokens(value: Any) -> tuple[str, ...]:
    raw = re.findall(r"[a-z0-9]+|[一-鿿]+", normalized_text(value))
    return tuple(SYNONYMS.get(item, item) for item in raw if item)


def signature(record: DomainRecord) -> tuple[str, ...]:
    values = [record.payload.get("claim_id", ""), record.payload.get("evidence_direction", ""),
              record.payload.get("scope_condition", ""), record.payload.get("source_kind", "")]
    merged = sorted({token for value in values for token in tokens(value)})
    return tuple(merged)


def similarity(left: DomainRecord, right: DomainRecord) -> float:
    a, b = set(signature(left)), set(signature(right))
    lexical = len(a & b) / max(1, len(a | b))
    same_model = left.payload.get("source_kind") == right.payload.get("source_kind")
    same_version = left.payload.get("source_version") == right.payload.get("source_version")
    regional = left.payload.get("working_group") == right.payload.get("working_group")
    return bounded(lexical * 0.55 + same_model * 0.20 + same_version * 0.15 + regional * 0.10)


def clusters(records: Iterable[DomainRecord], threshold: float = 0.45) -> list[list[DomainRecord]]:
    pending = list(records)
    result: list[list[DomainRecord]] = []
    while pending:
        seed = pending.pop(0)
        group = [seed]
        remaining = []
        for item in pending:
            if max(similarity(item, member) for member in group) >= threshold:
                group.append(item)
            else:
                remaining.append(item)
        pending = remaining
        result.append(group)
    return result


def deliberating_health(records: Iterable[DomainRecord]) -> dict[str, float]:
    rows = list(records)
    affected = sum(max(0.0, finite_number(row.payload.get("member_count", 0.0))) for row in rows)
    reproduced = sum(bounded(finite_number(row.payload.get("reproducibility", 0.0))) for row in rows)
    translation = sum(bounded(finite_number(row.payload.get("interpretation_confidence", 0.0))) for row in rows)
    claim_strength = sum(bounded(finite_number(row.payload.get("claim_strength", 0.0)) / 10.0) for row in rows)
    count = max(1, len(rows))
    return {"affected": affected, "reproduction": reproduced / count, "translation": translation / count,
            "claim_strength": claim_strength / count, "rollback_risk": bounded((claim_strength + reproduced) / (2.0 * count))}


def regional_distribution(records: Iterable[DomainRecord]) -> dict[str, float]:
    counts = Counter(str(row.payload.get("working_group", "unknown")) for row in records)
    total = sum(counts.values())
    concentration = sum((count / total) ** 2 for count in counts.values()) if total else 0.0
    return {"regions": float(len(counts)), "concentration": concentration, "diversity": bounded(1.0 - concentration)}


def derive_context(record: DomainRecord, repository: Any) -> dict[str, float]:
    rows = repository.list_records() or [record]
    groups = clusters(rows)
    health = deliberating_health(rows)
    regional = regional_distribution(rows)
    return {"duplicate_density_weight": 0.7 + (1.0 - len(groups) / max(1, len(rows))) * 0.7,
            "reproduction_confidence_weight": 0.6 + health["reproduction"] * 0.5,
            "regional_impact_weight": 0.6 + regional["diversity"] * 0.5,
            "rollback_risk_weight": 0.8 + health["rollback_risk"] * 0.6,
            "translation_gap_weight": 1.2 - health["translation"] * 0.4}
