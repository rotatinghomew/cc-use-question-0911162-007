from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from evidence_deliberation.claims.contract import (
    ContractError,
    DomainRecord,
    bounded,
    canonical_json,
    identifier,
    normalized_payload,
    normalized_text,
    stable_hash,
    utc_now,
)

# 异议评估的三种终态：
# responded     —— 已有回应证据且其权重不低于异议权重，证据权重未被改变
# disputed      —— 异议有依据，但仍存在未被充分回应的反驳
# insufficient  —— 异议缺乏支持材料或支持材料权重过低，证据不足
RESPONDED = "responded"
DISPUTED = "disputed"
INSUFFICIENT = "insufficient"
OBJECTION_STATUSES = (RESPONDED, DISPUTED, INSUFFICIENT)
BLOCKING_STATUSES = (DISPUTED, INSUFFICIENT)

# 异议支持材料平均权重低于该阈值时，判定为证据不足
INSUFFICIENT_FLOOR = 0.35
# 回应证据权重达到异议权重即视为已回应（保留极小容差避免浮点边界抖动）
RESPONSE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class EvidenceRef:
    """指向支持材料的可核验引用。"""

    evidence_id: str
    kind: str = ""
    weight: float | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", identifier(self.evidence_id))
        object.__setattr__(self, "kind", " ".join(str(self.kind or "").split()))
        if self.weight is not None:
            object.__setattr__(self, "weight", bounded(self.weight))
        object.__setattr__(self, "detail", " ".join(str(self.detail or "").split()))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EvidenceRef":
        if not isinstance(value, Mapping):
            raise ContractError("evidence reference must be an object")
        return cls(evidence_id=value.get("evidence_id", ""), kind=value.get("kind", ""),
                   weight=value.get("weight"), detail=value.get("detail", ""))

    def as_dict(self) -> dict[str, Any]:
        return {"evidence_id": self.evidence_id, "kind": self.kind,
                "weight": self.weight, "detail": self.detail}

    @property
    def fingerprint(self) -> str:
        return stable_hash(self.as_dict())


def evidence_weight(ref: EvidenceRef) -> float:
    """未量化的支持材料给予中性权重，显式权重以其为准。"""
    if ref.weight is None:
        return 0.5
    return bounded(ref.weight)


def claim_chain_key(record: DomainRecord) -> str:
    """同一主张链：claim_id / topic / scope_condition 一致的记录共享同一键。"""
    payload = record.payload
    basis = [normalized_text(payload.get("claim_id", "")),
             normalized_text(payload.get("topic", "")),
             normalized_text(payload.get("scope_condition", ""))]
    return "chain-" + stable_hash(basis)[:16]


@dataclass(frozen=True)
class Objection:
    """针对某条主张记录提出的、有依据的正式异议。"""

    objection_id: str
    target_record_id: str
    basis: str
    rationale: str
    evidence_refs: tuple[EvidenceRef, ...] = ()
    response: EvidenceRef | None = None
    chain_key: str = ""
    version: int = 1
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "objection_id", identifier(self.objection_id))
        object.__setattr__(self, "target_record_id", identifier(self.target_record_id))
        object.__setattr__(self, "basis", identifier(self.basis))
        if not " ".join(str(self.rationale or "").split()):
            raise ContractError("objection rationale is required")
        object.__setattr__(self, "rationale", " ".join(str(self.rationale).split()))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        if self.version < 1:
            raise ContractError("objection version must be positive")
        if not self.chain_key:
            object.__setattr__(self, "chain_key", "")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any], chain_key: str = "") -> "Objection":
        if not isinstance(value, Mapping):
            raise ContractError("objection must be an object")
        refs = tuple(EvidenceRef.from_dict(item) for item in value.get("evidence_refs", ()) or ())
        response = value.get("response")
        return cls(objection_id=value.get("objection_id", ""),
                   target_record_id=value.get("target_record_id", ""),
                   basis=value.get("basis", "unspecified"),
                   rationale=value.get("rationale", ""),
                   evidence_refs=refs,
                   response=EvidenceRef.from_dict(response) if response else None,
                   chain_key=str(value.get("chain_key") or chain_key),
                   version=int(value.get("version") or 1),
                   created_at=str(value.get("created_at") or utc_now()))

    def as_dict(self) -> dict[str, Any]:
        return {"objection_id": self.objection_id, "target_record_id": self.target_record_id,
                "basis": self.basis, "rationale": self.rationale,
                "evidence_refs": [ref.as_dict() for ref in self.evidence_refs],
                "response": self.response.as_dict() if self.response else None,
                "chain_key": self.chain_key, "version": self.version,
                "created_at": self.created_at}

    @property
    def fingerprint(self) -> str:
        return stable_hash(self.as_dict())

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(ref.evidence_id for ref in self.evidence_refs)

    @property
    def weight(self) -> float:
        if not self.evidence_refs:
            return 0.0
        return bounded(sum(evidence_weight(ref) for ref in self.evidence_refs) / len(self.evidence_refs))

    def with_response(self, response: EvidenceRef) -> "Objection":
        return Objection(self.objection_id, self.target_record_id, self.basis, self.rationale,
                         self.evidence_refs, response, self.chain_key, self.version + 1,
                         self.created_at)


@dataclass(frozen=True)
class ObjectionAssessment:
    """一次异议评估结果，钉住所引用的主张记录版本与证据指纹。"""

    objection_id: str
    objection_version: int
    target_record_id: str
    target_version: int
    target_fingerprint: str
    chain_key: str
    status: str
    objection_weight: float
    response_weight: float | None
    evidence_ids: tuple[str, ...]
    response_id: str
    rationale: str
    evidence_changed: bool
    assessed_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "objection_id", identifier(self.objection_id))
        object.__setattr__(self, "target_record_id", identifier(self.target_record_id))
        if self.status not in OBJECTION_STATUSES:
            raise ContractError(f"unsupported objection status: {self.status}")
        object.__setattr__(self, "objection_weight", bounded(self.objection_weight))
        if self.response_weight is not None:
            object.__setattr__(self, "response_weight", bounded(self.response_weight))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ObjectionAssessment":
        if not isinstance(value, Mapping):
            raise ContractError("assessment must be an object")
        return cls(objection_id=value.get("objection_id", ""),
                   objection_version=int(value.get("objection_version", 1)),
                   target_record_id=value.get("target_record_id", ""),
                   target_version=int(value.get("target_version", 1)),
                   target_fingerprint=value.get("target_fingerprint", ""),
                   chain_key=value.get("chain_key", ""),
                   status=value.get("status", ""),
                   objection_weight=float(value.get("objection_weight", 0.0)),
                   response_weight=value.get("response_weight"),
                   evidence_ids=tuple(value.get("evidence_ids", ()) or ()),
                   response_id=value.get("response_id", ""),
                   rationale=value.get("rationale", ""),
                   evidence_changed=bool(value.get("evidence_changed", False)),
                   assessed_at=str(value.get("assessed_at") or utc_now()))

    def as_dict(self) -> dict[str, Any]:
        return {"objection_id": self.objection_id, "objection_version": self.objection_version,
                "target_record_id": self.target_record_id, "target_version": self.target_version,
                "target_fingerprint": self.target_fingerprint, "chain_key": self.chain_key,
                "status": self.status, "objection_weight": self.objection_weight,
                "response_weight": self.response_weight, "evidence_ids": list(self.evidence_ids),
                "response_id": self.response_id, "rationale": self.rationale,
                "evidence_changed": self.evidence_changed, "assessed_at": self.assessed_at}

    @property
    def fingerprint(self) -> str:
        return stable_hash(self.as_dict())


def assess_objection(objection: Objection, target: DomainRecord,
                     previous: ObjectionAssessment | None = None) -> ObjectionAssessment:
    """基于异议材料权重与回应材料权重给出三态评估。"""
    if target.record_id != objection.target_record_id:
        raise ContractError("objection target does not match the record under review")
    weight = objection.weight
    response_weight = evidence_weight(objection.response) if objection.response is not None else None
    if objection.response is not None and response_weight is not None \
            and response_weight + RESPONSE_TOLERANCE >= max(weight, INSUFFICIENT_FLOOR):
        # 充分的回应证据可以同时覆盖“证据不足”与“仍有争议”两类异议。
        status = RESPONDED
    elif not objection.evidence_refs or weight < INSUFFICIENT_FLOOR:
        status = INSUFFICIENT
    elif objection.response is None:
        status = DISPUTED
    else:
        status = RESPONDED if response_weight + RESPONSE_TOLERANCE >= weight else DISPUTED
    evidence_changed = bool(previous and previous.target_fingerprint != target.fingerprint)
    return ObjectionAssessment(
        objection_id=objection.objection_id, objection_version=objection.version,
        target_record_id=target.record_id, target_version=target.version,
        target_fingerprint=target.fingerprint, chain_key=objection.chain_key,
        status=status, objection_weight=weight, response_weight=response_weight,
        evidence_ids=objection.evidence_ids,
        response_id=objection.response.evidence_id if objection.response else "",
        rationale=objection.rationale, evidence_changed=evidence_changed)


def objections_from_fixture(value: Mapping[str, Any],
                            records_by_id: Mapping[str, DomainRecord] | None = None) -> list[Objection]:
    raw = value.get("objections")
    if raw is None:
        return []
    if not isinstance(raw, list) or not raw:
        raise ContractError("fixture objections must be a non-empty list")
    records_by_id = records_by_id or {}
    objections: list[Objection] = []
    seen: set[str] = set()
    for item in raw:
        objection = Objection.from_dict(item)
        if objection.objection_id in seen:
            raise ContractError(f"duplicate objection identifier: {objection.objection_id}")
        seen.add(objection.objection_id)
        target = records_by_id.get(objection.target_record_id)
        if target is None:
            raise ContractError(f"objection {objection.objection_id} targets unknown record {objection.target_record_id}")
        if not objection.chain_key:
            object.__setattr__(objection, "chain_key", claim_chain_key(target))
        objections.append(objection)
    return objections


def worst_status(statuses: Iterable[str]) -> str:
    """发布摘要按最严重的异议状态概括一条主张记录。"""
    statuses = list(statuses)
    for candidate in (DISPUTED, INSUFFICIENT, RESPONDED):
        if candidate in statuses:
            return candidate
    return ""


def status_counts(assessments: Sequence[ObjectionAssessment]) -> dict[str, int]:
    return {status: sum(item.status == status for item in assessments)
            for status in OBJECTION_STATUSES}


def unresolved(assessments: Sequence[ObjectionAssessment]) -> list[ObjectionAssessment]:
    latest: dict[str, ObjectionAssessment] = {}
    for assessment in assessments:
        previous = latest.get(assessment.objection_id)
        if previous is None or assessment.objection_version >= previous.objection_version:
            latest[assessment.objection_id] = assessment
    return [item for item in latest.values() if item.status in BLOCKING_STATUSES]
