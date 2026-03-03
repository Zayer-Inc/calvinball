"""Tool: generate charts from data."""

from __future__ import annotations

import json
import uuid
from typing import Any

from calvinball.tools.base import BaseTool, ToolResult


class ChartTool(BaseTool):
    name = "chart"
    description = (
        "Generate a chart/visualization. You can provide data in two ways:\n"
        "1. Pass a SQL query via 'sql_query' — the tool runs it and charts the results.\n"
        "2. Pass data directly via 'data' as a JSON array of objects.\n"
        "Option 1 (sql_query) is preferred since it avoids copying large datasets.\n"
        "Returns file paths to generated HTML (interactive) and PNG (static) files."
    )
    parameters = {
        "type": "object",
        "properties": {
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "scatter", "pie", "histogram"],
                "description": "Type of chart to generate.",
            },
            "sql_query": {
                "type": "string",
                "description": "SQL query to fetch data for the chart. Preferred over passing data directly.",
            },
            "source": {
                "type": "string",
                "description": "Data source name for sql_query. If omitted, uses the first available.",
            },
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of data objects (rows) if not using sql_query.",
            },
            "x": {
                "type": "string",
                "description": "Column name for the x-axis (or labels for pie).",
            },
            "y": {
                "type": "string",
                "description": "Column name for the y-axis (or values for pie). Can be comma-separated for multiple series.",
            },
            "title": {
                "type": "string",
                "description": "Chart title.",
            },
        },
        "required": ["chart_type", "x", "y"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        from calvinball.viz.charts import create_chart

        try:
            chart_type = kwargs["chart_type"]
            x = kwargs["x"]
            y = kwargs["y"]
            title = kwargs.get("title", "")

            # Get data: either from sql_query or inline data
            data = kwargs.get("data")
            sql_query = kwargs.get("sql_query")

            if sql_query:
                from calvinball.integrations.manager import IntegrationManager

                mgr = IntegrationManager()
                await mgr.load_from_db()
                connected = mgr.all_connected()
                if not connected:
                    return ToolResult(output="", error="No data sources connected.")

                source_name = kwargs.get("source")
                if source_name:
                    integration = mgr.get(source_name)
                    if not integration:
                        return ToolResult(output="", error=f"Source '{source_name}' not found.")
                else:
                    integration = next(iter(connected.values()))

                data = await integration.execute_query(sql_query)
            elif data is None:
                return ToolResult(
                    output="",
                    error="Provide either 'sql_query' or 'data'. "
                          "sql_query is preferred — just pass the SQL and the tool will fetch the data.",
                )

            if not data:
                return ToolResult(output="", error="Query returned no data.")

            # Handle comma-separated y columns
            y_val: str | list[str] = y
            if "," in y:
                y_val = [c.strip() for c in y.split(",")]

            filename = f"chart_{uuid.uuid4().hex[:8]}"
            # Output charts to cwd so they're easy to find
            from pathlib import Path
            output_dir = Path.cwd() / "calvinball_charts"
            paths = create_chart(chart_type, data, x, y_val, title=title, filename=filename, output_dir=output_dir)

            # Auto-open the HTML chart in the browser
            html_path = paths.get("html")
            if html_path:
                import subprocess
                subprocess.Popen(["open", html_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            output_parts = [f"Chart generated ({len(data)} data points):"]
            for fmt, path in paths.items():
                output_parts.append(f"  {fmt.upper()}: {path}")

            return ToolResult(
                output="\n".join(output_parts),
                artifacts=paths,
            )
        except Exception as e:
            return ToolResult(output="", error=f"Chart generation failed: {e}")
