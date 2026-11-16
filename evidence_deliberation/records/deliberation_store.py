from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from evidence_deliberation.claims.contract import Decision, DomainRecord, ContractError, canonical_json, stable_hash, utc_now
from evidence_deliberation.dissent.objections import Objection, ObjectionAssessment


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS records(
    record_id TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS record_versions(
    record_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    stored_at TEXT NOT NULL,
    PRIMARY KEY(record_id, version)
);
CREATE TABLE IF NOT EXISTS decisions(
    decision_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    score REAL NOT NULL,
    decision_json TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    FOREIGN KEY(record_id) REFERENCES records(record_id)
);
CREATE TABLE IF NOT EXISTS events(
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    UNIQUE(aggregate_id, aggregate_version, event_type)
);
CREATE TABLE IF NOT EXISTS runs(
    run_id TEXT PRIMARY KEY,
    fixture_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS objections(
    objection_id TEXT PRIMARY KEY,
    target_record_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,
    chain_key TEXT NOT NULL,
    objection_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(target_record_id) REFERENCES records(record_id)
);
CREATE TABLE IF NOT EXISTS objection_versions(
    objection_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    objection_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    stored_at TEXT NOT NULL,
    PRIMARY KEY(objection_id, version)
);
CREATE TABLE IF NOT EXISTS objection_assessments(
    objection_id TEXT NOT NULL,
    objection_version INTEGER NOT NULL,
    target_record_id TEXT NOT NULL,
    target_version INTEGER NOT NULL,
    chain_key TEXT NOT NULL,
    status TEXT NOT NULL,
    assessment_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    assessed_at TEXT NOT NULL,
    PRIMARY KEY(objection_id, objection_version, target_version)
);
CREATE TABLE IF NOT EXISTS resolution_archives(
    record_id TEXT PRIMARY KEY,
    record_version INTEGER NOT NULL,
    decision_id TEXT NOT NULL,
    record_json TEXT NOT NULL,
    decision_json TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    objection_assessments_json TEXT NOT NULL,
    record_fingerprint TEXT NOT NULL,
    decision_fingerprint TEXT NOT NULL,
    archived_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_state ON records(state, updated_at);
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, event_id);
CREATE INDEX IF NOT EXISTS idx_decisions_record ON decisions(record_id, decided_at);
CREATE INDEX IF NOT EXISTS idx_objections_target ON objections(target_record_id, objection_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON objection_assessments(status, objection_id);
CREATE INDEX IF NOT EXISTS idx_assessments_chain ON objection_assessments(chain_key)
"""


class Repository:
    def __init__(self, database: str | Path):
        self.database = str(database)
        self._lock = threading.RLock()
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            connection = self.connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def _last_hash(self, connection: sqlite3.Connection) -> str:
        row = connection.execute("SELECT event_hash FROM events ORDER BY event_id DESC LIMIT 1").fetchone()
        return row[0] if row else "0" * 64

    def append_event(self, connection: sqlite3.Connection, event_type: str,
                     aggregate_id: str, aggregate_version: int, payload: Mapping[str, Any]) -> str:
        previous = self._last_hash(connection)
        created_at = utc_now()
        event_hash = stable_hash({"event_type": event_type, "aggregate_id": aggregate_id,
                                  "aggregate_version": aggregate_version, "payload": payload,
                                  "previous_hash": previous, "created_at": created_at})
        try:
            connection.execute("INSERT INTO events(event_type,aggregate_id,aggregate_version,payload_json,previous_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?)",
                               (event_type, aggregate_id, aggregate_version, canonical_json(payload),
                                previous, event_hash, created_at))
        except sqlite3.IntegrityError:
            row = connection.execute("SELECT event_hash,payload_json FROM events WHERE aggregate_id=? AND aggregate_version=? AND event_type=?",
                                     (aggregate_id, aggregate_version, event_type)).fetchone()
            if row and row[1] == canonical_json(payload):
                return row[0]
            raise ContractError("conflicting event replay") from None
        return event_hash

    def save_record(self, record: DomainRecord, expected_version: int | None = None) -> str:
        with self.transaction() as connection:
            current = connection.execute("SELECT version,fingerprint FROM records WHERE record_id=?", (record.record_id,)).fetchone()
            if current and expected_version is not None and current[0] != expected_version:
                raise ContractError("optimistic version conflict")
            if current and current[1] == record.fingerprint:
                return record.fingerprint
            if current and record.version <= current[0]:
                raise ContractError("record version must advance")
            payload = canonical_json(record.payload)
            connection.execute("INSERT INTO records(record_id,version,state,payload_json,fingerprint,occurred_at,source,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(record_id) DO UPDATE SET version=excluded.version,state=excluded.state,payload_json=excluded.payload_json,fingerprint=excluded.fingerprint,occurred_at=excluded.occurred_at,source=excluded.source,updated_at=excluded.updated_at",
                               (record.record_id, record.version, record.state, payload, record.fingerprint,
                                record.occurred_at, record.source, utc_now()))
            connection.execute("INSERT INTO record_versions(record_id,version,state,payload_json,fingerprint,stored_at) VALUES(?,?,?,?,?,?)",
                               (record.record_id, record.version, record.state, payload, record.fingerprint, utc_now()))
            self.append_event(connection, "record.saved", record.record_id, record.version,
                              {"state": record.state, "fingerprint": record.fingerprint})
            return record.fingerprint

    def get_record(self, record_id: str) -> DomainRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM records WHERE record_id=?", (record_id,)).fetchone()
        if not row:
            return None
        return DomainRecord(record_id=row["record_id"], payload=json.loads(row["payload_json"]),
                            state=row["state"], version=row["version"], occurred_at=row["occurred_at"],
                            source=row["source"])

    def list_records(self, state: str | None = None) -> list[DomainRecord]:
        query = "SELECT * FROM records"
        params: tuple[Any, ...] = ()
        if state:
            query += " WHERE state=?"
            params = (state,)
        query += " ORDER BY record_id"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [DomainRecord(record_id=row["record_id"], payload=json.loads(row["payload_json"]),
                             state=row["state"], version=row["version"], occurred_at=row["occurred_at"],
                             source=row["source"]) for row in rows]

    def save_decision(self, decision: Decision) -> str:
        decision_id = decision.fingerprint
        with self.transaction() as connection:
            if not connection.execute("SELECT 1 FROM records WHERE record_id=?", (decision.record_id,)).fetchone():
                raise ContractError("decision record does not exist")
            body = canonical_json(decision.as_dict())
            connection.execute("INSERT OR IGNORE INTO decisions(decision_id,record_id,outcome,score,decision_json,decided_at) VALUES(?,?,?,?,?,?)",
                               (decision_id, decision.record_id, decision.outcome, decision.score, body, decision.decided_at))
            self.append_event(connection, "decision.saved", decision.record_id,
                              self.event_count(decision.record_id, connection) + 1,
                              {"decision_id": decision_id, "outcome": decision.outcome, "score": decision.score})
        return decision_id

    def event_count(self, aggregate_id: str, connection: sqlite3.Connection | None = None) -> int:
        owns = connection is None
        connection = connection or self.connect()
        try:
            row = connection.execute("SELECT COUNT(*) FROM events WHERE aggregate_id=?", (aggregate_id,)).fetchone()
            return int(row[0])
        finally:
            if owns:
                connection.close()

    def save_objection(self, objection: Objection, status: str) -> str:
        with self.transaction() as connection:
            if not connection.execute("SELECT 1 FROM records WHERE record_id=?",
                                      (objection.target_record_id,)).fetchone():
                raise ContractError("objection target record does not exist")
            current = connection.execute("SELECT version FROM objections WHERE objection_id=?",
                                         (objection.objection_id,)).fetchone()
            if current and objection.version <= current[0]:
                raise ContractError("objection version must advance")
            body = canonical_json(objection.as_dict())
            connection.execute("INSERT INTO objections(objection_id,target_record_id,version,status,chain_key,objection_json,fingerprint,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(objection_id) DO UPDATE SET target_record_id=excluded.target_record_id,version=excluded.version,status=excluded.status,chain_key=excluded.chain_key,objection_json=excluded.objection_json,fingerprint=excluded.fingerprint,updated_at=excluded.updated_at",
                               (objection.objection_id, objection.target_record_id, objection.version,
                                status, objection.chain_key, body, objection.fingerprint, utc_now()))
            connection.execute("INSERT OR IGNORE INTO objection_versions(objection_id,version,objection_json,fingerprint,stored_at) VALUES(?,?,?,?,?)",
                               (objection.objection_id, objection.version, body, objection.fingerprint, utc_now()))
            self.append_event(connection, "objection.saved", objection.objection_id, objection.version,
                              {"target_record_id": objection.target_record_id, "version": objection.version,
                               "status": status, "fingerprint": objection.fingerprint})
            return objection.fingerprint

    def get_objection(self, objection_id: str) -> Objection | None:
        with self.connect() as connection:
            row = connection.execute("SELECT objection_json FROM objections WHERE objection_id=?",
                                     (objection_id,)).fetchone()
        return Objection.from_dict(json.loads(row[0])) if row else None

    def list_objections(self, target_record_id: str | None = None) -> list[Objection]:
        query = "SELECT objection_json FROM objections"
        params: tuple[Any, ...] = ()
        if target_record_id:
            query += " WHERE target_record_id=?"
            params = (target_record_id,)
        query += " ORDER BY objection_id"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [Objection.from_dict(json.loads(row[0])) for row in rows]

    def save_assessment(self, assessment: ObjectionAssessment) -> str:
        with self.transaction() as connection:
            if not connection.execute("SELECT 1 FROM records WHERE record_id=?",
                                      (assessment.target_record_id,)).fetchone():
                raise ContractError("assessment record does not exist")
            body = canonical_json(assessment.as_dict())
            connection.execute("INSERT OR IGNORE INTO objection_assessments(objection_id,objection_version,target_record_id,target_version,chain_key,status,assessment_json,fingerprint,assessed_at) VALUES(?,?,?,?,?,?,?,?,?)",
                               (assessment.objection_id, assessment.objection_version,
                                assessment.target_record_id, assessment.target_version,
                                assessment.chain_key, assessment.status,
                                body, assessment.fingerprint, assessment.assessed_at))
            connection.execute("UPDATE objections SET status=? WHERE objection_id=?",
                               (assessment.status, assessment.objection_id))
            self.append_event(connection, "objection.assessed", assessment.objection_id,
                              self.event_count(assessment.objection_id, connection) + 1,
                              {"target_record_id": assessment.target_record_id,
                               "target_version": assessment.target_version, "status": assessment.status,
                               "objection_version": assessment.objection_version,
                               "fingerprint": assessment.fingerprint})
        return assessment.fingerprint

    def list_assessments(self, target_record_id: str | None = None,
                         chain_key: str | None = None, status: str | None = None) -> list[ObjectionAssessment]:
        query = "SELECT assessment_json FROM objection_assessments WHERE 1=1"
        params: list[Any] = []
        if target_record_id:
            query += " AND target_record_id=?"
            params.append(target_record_id)
        if chain_key:
            query += " AND chain_key=?"
            params.append(chain_key)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY objection_id, objection_version, target_version"
        with self.connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [ObjectionAssessment.from_dict(json.loads(row[0])) for row in rows]

    def latest_assessments(self, target_record_id: str | None = None) -> list[ObjectionAssessment]:
        rows = self.list_assessments(target_record_id=target_record_id)
        latest: dict[str, ObjectionAssessment] = {}
        for assessment in rows:
            previous = latest.get(assessment.objection_id)
            if previous is None or (assessment.objection_version, assessment.target_version) >= \
                    (previous.objection_version, previous.target_version):
                latest[assessment.objection_id] = assessment
        return [latest[key] for key in sorted(latest)]

    def save_resolution_archive(self, record: DomainRecord, decision: Decision,
                                evidence_refs: Sequence[Mapping[str, Any]],
                                assessments: Sequence[ObjectionAssessment]) -> str:
        with self.transaction() as connection:
            existing = connection.execute("SELECT record_fingerprint FROM resolution_archives WHERE record_id=?",
                                          (record.record_id,)).fetchone()
            if existing:
                return existing[0]
            record_body = canonical_json(record.__dict__)
            decision_body = canonical_json(decision.as_dict())
            evidence_body = canonical_json(list(evidence_refs))
            assessment_body = canonical_json([item.as_dict() for item in assessments])
            connection.execute("INSERT INTO resolution_archives(record_id,record_version,decision_id,record_json,decision_json,evidence_refs_json,objection_assessments_json,record_fingerprint,decision_fingerprint,archived_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                               (record.record_id, record.version, decision.fingerprint, record_body,
                                decision_body, evidence_body, assessment_body,
                                record.fingerprint, decision.fingerprint, utc_now()))
            self.append_event(connection, "resolution.archived", record.record_id, record.version,
                              {"record_version": record.version, "decision_id": decision.fingerprint,
                               "record_fingerprint": record.fingerprint,
                               "decision_fingerprint": decision.fingerprint})
        return record.fingerprint

    def get_archive(self, record_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM resolution_archives WHERE record_id=?",
                                     (record_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["record"] = json.loads(result.pop("record_json"))
        result["decision"] = json.loads(result.pop("decision_json"))
        result["evidence_refs"] = json.loads(result.pop("evidence_refs_json"))
        result["objection_assessments"] = json.loads(result.pop("objection_assessments_json"))
        return result

    def list_archives(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT record_id FROM resolution_archives ORDER BY record_id").fetchall()
        return [archive for row in rows if (archive := self.get_archive(row[0]))]

    def begin_run(self, fixture_hash: str, record_count: int) -> str:
        run_id = stable_hash({"fixture_hash": fixture_hash, "record_count": record_count})[:24]
        with self.transaction() as connection:
            row = connection.execute("SELECT fixture_hash,record_count FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if row and (row[0] != fixture_hash or row[1] != record_count):
                raise ContractError("run identifier collision")
            connection.execute("INSERT OR IGNORE INTO runs(run_id,fixture_hash,status,record_count,result_json,started_at) VALUES(?,?,?,?,?,?)",
                               (run_id, fixture_hash, "running", record_count, "{}", utc_now()))
        return run_id

    def completed_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT status,result_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row or row["status"] != "finished":
            return None
        result = json.loads(row["result_json"])
        if not isinstance(result, dict):
            raise ContractError("stored run result is invalid")
        return result

    def finish_run(self, run_id: str, result: Mapping[str, Any]) -> None:
        with self.transaction() as connection:
            changed = connection.execute("UPDATE runs SET status='finished',result_json=?,finished_at=? WHERE run_id=?",
                                         (canonical_json(result), utc_now(), run_id)).rowcount
            if changed != 1:
                raise ContractError("unknown run")
            self.append_event(connection, "run.finished", run_id, 1, dict(result))

    def verify_chain(self) -> list[str]:
        errors: list[str] = []
        previous = "0" * 64
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
        for row in rows:
            payload = json.loads(row["payload_json"])
            expected = stable_hash({"event_type": row["event_type"], "aggregate_id": row["aggregate_id"],
                                    "aggregate_version": row["aggregate_version"], "payload": payload,
                                    "previous_hash": row["previous_hash"], "created_at": row["created_at"]})
            if row["previous_hash"] != previous:
                errors.append(f"event {row['event_id']} previous hash mismatch")
            if row["event_hash"] != expected:
                errors.append(f"event {row['event_id']} content hash mismatch")
            previous = row["event_hash"]
        return errors

    def snapshot(self) -> dict[str, Any]:
        with self.connect() as connection:
            counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                      for table in ("records", "record_versions", "decisions", "events", "runs",
                                    "objections", "objection_versions", "objection_assessments",
                                    "resolution_archives")}
            states = {row[0]: row[1] for row in connection.execute("SELECT state,COUNT(*) FROM records GROUP BY state")}
        return {"counts": counts, "states": states, "chain_errors": self.verify_chain()}

    def decision_rows(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT decision_json FROM decisions ORDER BY record_id,decided_at").fetchall()
        return [json.loads(row[0]) for row in rows]

    def event_rows(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
        return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in rows]
