"""Org knowledge / learned facts cached across runs."""

from __future__ import annotations

from datetime import datetime, timezone

from calvinball.config.settings import ensure_dirs
from calvinball.persistence.db import get_db


async def save_fact(fact: str, source: str = "agent") -> None:
    """Store a learned fact."""
    ensure_dirs()
    db = await get_db()
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO memory (fact, source, created_at) VALUES (?, ?, ?)",
        (fact, source, now),
    )
    await db.commit()
    await db.close()


async def load_facts(limit: int = 50) -> str:
    """Load recent learned facts as a text block for the system prompt."""
    ensure_dirs()
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT fact FROM memory ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    await db.close()
    if not rows:
        return ""
    return "\n".join(f"- {r['fact']}" for r in rows)
