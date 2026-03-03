"""calvinball investigate <question>"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console

console = Console()


def investigate(
    question: str = typer.Argument(..., help="The question to investigate"),
    resume: Optional[str] = typer.Option(None, help="Resume investigation by ID"),
    depth: str = typer.Option("normal", help="Investigation depth: shallow|normal|deep"),
    no_chat: bool = typer.Option(False, "--no-chat", help="Exit after investigation (no interactive follow-up)"),
) -> None:
    """Launch an autonomous investigation."""
    from calvinball.agent.loop import run_investigation

    asyncio.run(
        run_investigation(
            question, depth=depth, resume_id=resume, interactive=not no_chat
        )
    )
