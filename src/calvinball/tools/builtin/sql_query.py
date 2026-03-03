"""Tools: sql_query and describe_schema for data source integrations."""

from __future__ import annotations

import json
from typing import Any

from calvinball.tools.base import BaseTool, ToolResult


class SQLQueryTool(BaseTool):
    name = "sql_query"
    description = (
        "Execute a SQL query against a connected data source. "
        "Returns results as a JSON array of objects. "
        "Use describe_schema first to understand available tables."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL query to execute.",
            },
            "source": {
                "type": "string",
                "description": "Name of the data source (integration name). If omitted, uses the first available.",
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        from calvinball.integrations.manager import IntegrationManager

        query = kwargs["query"]
        source_name = kwargs.get("source")

        mgr = IntegrationManager()
        await mgr.load_from_db()

        connected = mgr.all_connected()
        if not connected:
            return ToolResult(output="", error="No data sources connected. Use 'calvinball connect' first.")

        if source_name:
            integration = mgr.get(source_name)
            if not integration:
                return ToolResult(output="", error=f"Data source '{source_name}' not found. Available: {list(connected)}")
        else:
            integration = next(iter(connected.values()))

        try:
            rows = await integration.execute_query(query)
            # Truncate if too many rows
            truncated = False
            if len(rows) > 500:
                rows = rows[:500]
                truncated = True

            output = json.dumps(rows, indent=2, default=str)
            if truncated:
                output += f"\n\n(Truncated to 500 rows out of more results)"
            return ToolResult(output=output, artifacts={"row_count": len(rows)})
        except Exception as e:
            return ToolResult(output="", error=f"Query failed: {e}")


class DescribeSchemaTool(BaseTool):
    name = "describe_schema"
    description = (
        "Get the schema (tables and columns) of a connected data source. "
        "Use this to understand what data is available before writing queries."
    )
    parameters = {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "description": "Name of the data source. If omitted, describes all sources.",
            },
        },
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        from calvinball.integrations.manager import IntegrationManager

        mgr = IntegrationManager()
        await mgr.load_from_db()

        source_name = kwargs.get("source")

        if source_name:
            integration = mgr.get(source_name)
            if not integration:
                return ToolResult(output="", error=f"Data source '{source_name}' not found.")
            try:
                schema = await integration.get_schema_info()
                return ToolResult(output=schema)
            except Exception as e:
                return ToolResult(output="", error=str(e))
        else:
            desc = await mgr.describe_all()
            return ToolResult(output=desc or "No data sources connected.")
