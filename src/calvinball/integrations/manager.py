"""Integration manager — discover, load, manage integrations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from calvinball.integrations.base import BaseIntegration
from calvinball.integrations.snowflake import SnowflakeIntegration

_INTEGRATION_TYPES: dict[str, type[BaseIntegration]] = {
    "snowflake": SnowflakeIntegration,
}


class IntegrationManager:
    """Manages data source integrations."""

    def __init__(self) -> None:
        self._integrations: dict[str, BaseIntegration] = {}

    async def add_integration(
        self,
        name: str,
        source_type: str,
        config: dict[str, Any],
    ) -> BaseIntegration:
        """Create, connect, and persist an integration."""
        cls = _INTEGRATION_TYPES.get(source_type)
        if cls is None:
            raise ValueError(f"Unknown source type: {source_type}. Available: {list(_INTEGRATION_TYPES)}")

        integration = cls()
        await integration.connect(config)
        self._integrations[name] = integration

        # Persist
        from calvinball.persistence.db import get_db
        from calvinball.config.settings import ensure_dirs

        ensure_dirs()
        db = await get_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """INSERT INTO integrations (name, source_type, config, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET config = excluded.config""",
            (name, source_type, json.dumps(config), now),
        )
        await db.commit()
        await db.close()
        return integration

    def get(self, name: str) -> BaseIntegration | None:
        return self._integrations.get(name)

    def all_connected(self) -> dict[str, BaseIntegration]:
        return dict(self._integrations)

    async def load_from_db(self) -> None:
        """Load persisted integrations and reconnect."""
        from calvinball.persistence.db import get_db
        from calvinball.config.settings import ensure_dirs

        ensure_dirs()
        db = await get_db()
        rows = await db.execute_fetchall("SELECT name, source_type, config FROM integrations WHERE is_generated = 0")
        await db.close()

        for row in rows:
            source_type = row["source_type"]
            cls = _INTEGRATION_TYPES.get(source_type)
            if cls is None:
                continue
            config = json.loads(row["config"]) if row["config"] else {}
            integration = cls()
            try:
                await integration.connect(config)
                self._integrations[row["name"]] = integration
            except Exception:
                pass  # Skip integrations that fail to reconnect

    async def describe_all(
        self,
        schemas: list[str] | None = None,
        databases: list[str] | None = None,
    ) -> str:
        """Get schema descriptions from all connected integrations."""
        if not self._integrations:
            await self.load_from_db()

        descriptions = []
        for name, integration in self._integrations.items():
            if integration.connected:
                try:
                    desc = await integration.get_schema_info(schemas=schemas, databases=databases)
                    descriptions.append(f"[{name}] {desc}")
                except Exception as e:
                    descriptions.append(f"[{name}] Error: {e}")
        return "\n".join(descriptions) if descriptions else ""
