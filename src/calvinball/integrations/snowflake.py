"""Prebuilt Snowflake connector (browser SSO + key pair auth)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from calvinball.integrations.base import BaseIntegration


class SnowflakeIntegration(BaseIntegration):
    name = "snowflake"
    source_type = "snowflake"

    def __init__(self) -> None:
        self._conn: Any = None
        self._config: dict[str, Any] = {}

    @property
    def connected(self) -> bool:
        return self._conn is not None

    async def connect(self, config: dict[str, Any]) -> None:
        import snowflake.connector

        self._config = config

        conn_params: dict[str, Any] = {
            "account": config.get("account"),
            "user": config.get("user"),
            "warehouse": config.get("warehouse"),
            "database": config.get("database"),
            "schema": config.get("schema"),
            "role": config.get("role"),
        }

        # Auth routing
        auth_method = config.get("auth_method")
        private_key_path = config.get("private_key_path")

        if auth_method == "browser_sso":
            conn_params["authenticator"] = "externalbrowser"
        elif private_key_path:
            conn_params["authenticator"] = "SNOWFLAKE_JWT"
            conn_params["private_key_file"] = str(Path(private_key_path).expanduser())
            passphrase = config.get("private_key_passphrase")
            if passphrase:
                conn_params["private_key_file_pwd"] = passphrase
        elif config.get("private_key"):
            # Raw PEM key content passed directly
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend

            pem_bytes = config["private_key"].encode()
            passphrase = config.get("private_key_passphrase")
            pwd = passphrase.encode() if passphrase else None
            p_key = serialization.load_pem_private_key(
                pem_bytes, password=pwd, backend=default_backend()
            )
            pkb = p_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            conn_params["private_key"] = pkb

        # Run the blocking connect in a thread
        self._conn = await asyncio.to_thread(
            snowflake.connector.connect, **conn_params
        )

    async def disconnect(self) -> None:
        if self._conn:
            await asyncio.to_thread(self._conn.close)
            self._conn = None

    async def execute_query(self, query: str) -> list[dict[str, Any]]:
        if not self._conn:
            raise RuntimeError("Not connected to Snowflake")

        def _run() -> list[dict[str, Any]]:
            cur = self._conn.cursor()
            try:
                cur.execute(query)
                cols = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                return [dict(zip(cols, row)) for row in rows]
            finally:
                cur.close()

        return await asyncio.to_thread(_run)

    async def get_schema_info(
        self,
        schemas: list[str] | None = None,
        databases: list[str] | None = None,
    ) -> str:
        if not self._conn:
            return "Snowflake: not connected"

        # Normalize filters to uppercase (Snowflake identifiers are case-insensitive)
        allowed_databases = {d.upper() for d in databases} if databases else None
        allowed_schemas = {s.upper() for s in schemas} if schemas else None

        # Discover which databases to inspect
        try:
            db_rows = await self.execute_query("SHOW DATABASES")
            all_databases = [
                r.get("name", r.get("DATABASE_NAME", ""))
                for r in db_rows
                if r.get("name") or r.get("DATABASE_NAME")
            ]
        except Exception:
            # Fall back to the configured database if SHOW DATABASES fails
            configured = self._config.get("database")
            all_databases = [configured] if configured else []

        if allowed_databases:
            all_databases = [d for d in all_databases if d.upper() in allowed_databases]

        if not all_databases:
            return "Snowflake: no accessible databases found"

        lines = ["Snowflake tables:"]
        count = 0
        for db in all_databases:
            try:
                tables = await self.execute_query(f"SHOW TABLES IN DATABASE {db}")
            except Exception:
                continue  # Skip databases we can't access

            for t in tables:
                table_name = t.get("name", t.get("TABLE_NAME", "unknown"))
                schema = t.get("schema_name", t.get("TABLE_SCHEMA", ""))

                if allowed_schemas and schema.upper() not in allowed_schemas:
                    continue

                lines.append(f"  - {db}.{schema}.{table_name}")
                count += 1
                if count >= 500:
                    lines.append("  (truncated — more tables exist)")
                    return "\n".join(lines)

        if count == 0:
            filters = []
            if databases:
                filters.append(f"databases: {', '.join(databases)}")
            if schemas:
                filters.append(f"schemas: {', '.join(schemas)}")
            scope = "; ".join(filters) if filters else "any"
            return f"Snowflake: no tables found in scope ({scope})"

        return "\n".join(lines)
