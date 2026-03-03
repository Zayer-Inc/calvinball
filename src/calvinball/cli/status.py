"""calvinball status"""

from __future__ import annotations

import asyncio

import typer
from rich import print as rprint
from rich.table import Table


def status(
    investigations: bool = typer.Option(False, "--investigations", help="Show investigations"),
    integrations: bool = typer.Option(False, "--integrations", help="Show integrations"),
) -> None:
    """Show status of investigations and integrations."""
    asyncio.run(_status(investigations, integrations))


async def _status(show_inv: bool, show_int: bool) -> None:
    from calvinball.persistence.db import get_db

    db = await get_db()

    if not show_inv and not show_int:
        show_inv = show_int = True

    if show_inv:
        rows = await db.execute_fetchall(
            "SELECT id, question, status, created_at FROM investigations ORDER BY created_at DESC LIMIT 20"
        )
        table = Table(title="Investigations")
        table.add_column("ID", style="dim", max_width=8)
        table.add_column("Question")
        table.add_column("Status")
        table.add_column("Created")
        for r in rows:
            table.add_row(r["id"][:8], r["question"][:60], r["status"], r["created_at"])
        rprint(table)

    if show_int:
        rows = await db.execute_fetchall(
            "SELECT name, source_type, created_at FROM integrations ORDER BY created_at DESC"
        )
        table = Table(title="Integrations")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Created")
        for r in rows:
            table.add_row(r["name"], r["source_type"], r["created_at"])
        rprint(table)

    await db.close()
