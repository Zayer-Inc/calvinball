"""calvinball config init|show|set"""

from __future__ import annotations

import typer
from rich import print as rprint

from calvinball.config.settings import (
    CONFIG_PATH,
    DEFAULT_CONFIG_TOML,
    Settings,
    ensure_dirs,
)

config_app = typer.Typer(help="Manage Calvinball configuration.")


@config_app.command()
def init() -> None:
    """Initialize ~/.calvinball/ directory and default config."""
    ensure_dirs()
    if CONFIG_PATH.exists():
        rprint("[yellow]Config already exists at[/yellow]", str(CONFIG_PATH))
    else:
        CONFIG_PATH.write_text(DEFAULT_CONFIG_TOML)
        rprint("[green]Created config at[/green]", str(CONFIG_PATH))
    rprint("[green]Calvinball initialized.[/green]")


@config_app.command()
def show() -> None:
    """Display current configuration."""
    settings = Settings.load()
    rprint(settings.model_dump())


@config_app.command("set")
def set_value(key: str, value: str) -> None:
    """Set a config value (dot-notation, e.g. llm.model)."""
    # Simple: rewrite the TOML. For v0, just support top-level llm keys.
    import tomllib

    ensure_dirs()
    data: dict = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)

    parts = key.split(".")
    target = data
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value

    # Write back as simple TOML
    lines: list[str] = []
    for section, vals in data.items():
        if isinstance(vals, dict):
            lines.append(f"[{section}]")
            for k, v in vals.items():
                lines.append(f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}")
            lines.append("")
        else:
            lines.append(
                f'{section} = "{vals}"' if isinstance(vals, str) else f"{section} = {vals}"
            )

    CONFIG_PATH.write_text("\n".join(lines) + "\n")
    rprint(f"[green]Set {key} = {value}[/green]")
