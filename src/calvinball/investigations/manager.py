"""CRUD for investigations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from calvinball.config.settings import ensure_dirs
from calvinball.investigations.models import Investigation
from calvinball.persistence.db import get_db


class InvestigationManager:
    """Manage investigation lifecycle and persistence."""

    async def save(self, inv: Investigation) -> None:
        ensure_dirs()
        db = await get_db()
        now = datetime.now(timezone.utc).isoformat()
        inv.updated_at = now
        if not inv.created_at:
            inv.created_at = now

        await db.execute(
            """INSERT INTO investigations (id, question, status, depth, threads, findings, messages, report, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 status = excluded.status,
                 threads = excluded.threads,
                 findings = excluded.findings,
                 messages = excluded.messages,
                 report = excluded.report,
                 updated_at = excluded.updated_at""",
            (
                inv.id, inv.question, inv.status, inv.depth,
                json.dumps([_thread_to_dict(t) for t in inv.threads]),
                json.dumps([_finding_to_dict(f) for f in inv.findings]),
                json.dumps(inv.messages),
                inv.report,
                inv.created_at, inv.updated_at,
            ),
        )
        await db.commit()
        await db.close()

    async def load(self, investigation_id: str) -> Investigation | None:
        ensure_dirs()
        db = await get_db()
        row = await db.execute_fetchone(
            "SELECT * FROM investigations WHERE id = ?", (investigation_id,)
        )
        await db.close()
        if not row:
            return None
        return _row_to_investigation(row)

    async def list_all(self, limit: int = 20) -> list[Investigation]:
        ensure_dirs()
        db = await get_db()
        rows = await db.execute_fetchall(
            "SELECT * FROM investigations ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        await db.close()
        return [_row_to_investigation(r) for r in rows]


def _finding_to_dict(f: Any) -> dict:
    return {"summary": f.summary, "evidence": f.evidence, "confidence": f.confidence, "artifacts": f.artifacts}


def _thread_to_dict(t: Any) -> dict:
    return {"question": t.question, "status": t.status, "findings": [_finding_to_dict(f) for f in t.findings]}


def _row_to_investigation(row: Any) -> Investigation:
    return Investigation(
        id=row["id"],
        question=row["question"],
        status=row["status"],
        depth=row["depth"],
        messages=json.loads(row["messages"]) if row["messages"] else [],
        report=row["report"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
