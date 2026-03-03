"""Typer app and command registration."""

from __future__ import annotations

import typer

from calvinball.cli.config_cmd import config_app
from calvinball.cli.connect import connect
from calvinball.cli.investigate import investigate
from calvinball.cli.status import status

app = typer.Typer(
    name="calvinball",
    help="Autonomous data analyst agent that goes hunting.",
    no_args_is_help=True,
)

app.command()(investigate)
app.command()(connect)
app.command()(status)
app.add_typer(config_app, name="config")

if __name__ == "__main__":
    app()
