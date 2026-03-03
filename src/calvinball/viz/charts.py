"""Plotly chart generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import plotly.graph_objects as go


def create_chart(
    chart_type: str,
    data: list[dict[str, Any]],
    x: str,
    y: str | list[str],
    title: str = "",
    output_dir: Path | None = None,
    filename: str = "chart",
) -> dict[str, str]:
    """Create a chart and save as HTML + PNG.

    Returns dict with 'html' and 'png' file paths.
    """
    if output_dir is None:
        from calvinball.config.settings import CALVINBALL_DIR
        output_dir = CALVINBALL_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    y_cols = [y] if isinstance(y, str) else y

    fig = go.Figure()

    x_values = [row.get(x) for row in data]

    for y_col in y_cols:
        y_values = [row.get(y_col) for row in data]

        if chart_type == "bar":
            fig.add_trace(go.Bar(x=x_values, y=y_values, name=y_col))
        elif chart_type == "line":
            fig.add_trace(go.Scatter(x=x_values, y=y_values, mode="lines+markers", name=y_col))
        elif chart_type == "scatter":
            fig.add_trace(go.Scatter(x=x_values, y=y_values, mode="markers", name=y_col))
        elif chart_type == "pie":
            fig = go.Figure(go.Pie(labels=x_values, values=y_values))
            break  # Pie only uses first y column
        elif chart_type == "histogram":
            fig.add_trace(go.Histogram(x=y_values, name=y_col))
        else:
            fig.add_trace(go.Bar(x=x_values, y=y_values, name=y_col))

    fig.update_layout(title=title, template="plotly_white")

    html_path = output_dir / f"{filename}.html"
    png_path = output_dir / f"{filename}.png"

    fig.write_html(str(html_path))

    try:
        fig.write_image(str(png_path))
    except Exception:
        png_path = None  # Kaleido may not work on all systems

    result = {"html": str(html_path)}
    if png_path:
        result["png"] = str(png_path)
    return result
