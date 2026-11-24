"""
store.py — SQLite persistence for assessment history (Milestone 5 / SEC-12.1 re-review).

Keeps run metadata and approval decisions so a teammate's decision survives process restart.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import ROOT

DEFAULT_DB = ROOT / "data" / "assessor_history.sqlite3"

# Server-side identity → groups. Never trust client-supplied groups in production.
ROLE_GROUPS = {
    "employee": ["public", "employees"],
    "security": ["public", "employees", "security"],
    "procurement": ["public", "employees", "procurement"],
    "admin": ["public", "employees", "security", "procurement"],
}


def groups_for_role(role: str) -> list[str]:
    return list(ROLE_GROUPS.get(role.lower(), ROLE_GROUPS["employee"]))


class AssessmentStore:
    def __init__(self, path: Path | str = DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    run_id TEXT PRIMARY KEY,
                    question TEXT,
                    vendor TEXT,
                    tier TEXT,
                    users INTEGER,
                    overall TEXT,
                    status TEXT,
                    requested_by TEXT,
                    role TEXT,
                    report_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    status TEXT,
                    error TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

    def save_report(self, run_id: str, report: dict, *, question: str, vendor: str, tier: str,
                    users: int, requested_by: str, role: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute(
                """INSERT INTO assessments(run_id, question, vendor, tier, users, overall, status,
                   requested_by, role, report_json, created_at, updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(run_id) DO UPDATE SET
                     overall=excluded.overall, status=excluded.status, report_json=excluded.report_json,
                     updated_at=excluded.updated_at""",
                (run_id, question, vendor, tier, users, report.get("overall"),
                 (report.get("approval") or {}).get("status", "pending"),
                 requested_by, role, json.dumps(report), now, now),
            )

    def get(self, run_id: str) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM assessments WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def list_recent(self, limit: int = 20) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT run_id, question, vendor, tier, overall, status, created_at FROM assessments "
                "ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def update_approval(self, run_id: str, approval: dict) -> Optional[dict]:
        row = self.get(run_id)
        if not row:
            return None
        report = json.loads(row["report_json"])
        report["approval"] = approval
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute(
                "UPDATE assessments SET status=?, report_json=?, updated_at=? WHERE run_id=?",
                (approval.get("status"), json.dumps(report), now, run_id),
            )
        return approval

    def save_job(self, job_id: str, status: str, run_id: str = "", error: str = "") -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute(
                """INSERT INTO jobs(job_id, run_id, status, error, created_at, updated_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(job_id) DO UPDATE SET
                     run_id=excluded.run_id, status=excluded.status, error=excluded.error,
                     updated_at=excluded.updated_at""",
                (job_id, run_id, status, error, now, now),
            )

    def get_job(self, job_id: str) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row) if row else None
