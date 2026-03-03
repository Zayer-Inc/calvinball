"""SQLite connection and migrations."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from calvinball.config.settings import DB_PATH

_SCHEMA_SQL = Path(__file__).parent / "schemas.sql"


async def get_db(db_path: Path = DB_PATH) -> aiosqlite.Connection:
    """Open a connection and ensure schema exists."""
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    schema = _SCHEMA_SQL.read_text()
    await db.executescript(schema)
    await db.commit()
    return db
