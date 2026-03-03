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

    async def get_schema_info(self) -> str:
        if not self._conn:
            return "Snowflake: not connected"

        tables = await self.execute_query("SHOW TABLES")
        if not tables:
            return "Snowflake: no tables found"

        lines = ["Snowflake tables:"]
        for t in tables[:50]:  # Cap at 50 tables
            table_name = t.get("name", t.get("TABLE_NAME", "unknown"))
            db = t.get("database_name", t.get("TABLE_CATALOG", ""))
            schema = t.get("schema_name", t.get("TABLE_SCHEMA", ""))
            lines.append(f"  - {db}.{schema}.{table_name}")

        return "\n".join(lines)
