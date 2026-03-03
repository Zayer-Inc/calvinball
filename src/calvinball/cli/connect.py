"""calvinball connect <source_type>"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import typer
from rich import print as rprint
from rich.prompt import Prompt


def connect(
    source_type: str = typer.Argument(..., help="Type of data source (e.g. snowflake)"),
    name: Optional[str] = typer.Option(None, help="Name for this connection"),
    credentials: Optional[str] = typer.Option(
        None,
        help='JSON credentials string. For Snowflake key pair auth: '
             '\'{"account":"...", "user":"...", "private_key_path":"~/.ssh/snowflake_key.p8", '
             '"warehouse":"...", "database":"..."}\'',
    ),
) -> None:
    """Connect a data source (Snowflake supports browser SSO and key pair auth)."""
    asyncio.run(_connect(source_type, name, credentials))


async def _connect(
    source_type: str,
    name: str | None,
    credentials: str | None,
) -> None:
    from calvinball.integrations.manager import IntegrationManager

    mgr = IntegrationManager()

    if credentials:
        # Non-interactive: existing JSON path
        config = json.loads(credentials)
    elif source_type == "snowflake":
        config = _snowflake_wizard()
    else:
        rprint(f"[red]No interactive wizard for '{source_type}'. Pass --credentials.[/red]")
        raise typer.Exit(code=1)

    conn_name = name or source_type

    rprint("\n  Testing connection...")
    try:
        integration = await mgr.add_integration(conn_name, source_type, config)
    except Exception as e:
        rprint(f"  [red]Connection failed: {e}[/red]")
        raise typer.Exit(code=1)

    # Show table count on success
    table_count = ""
    try:
        schema_info = await integration.get_schema_info()
        count = schema_info.count("\n")  # each table is a line after the header
        if count:
            table_count = f" Found {count} tables."
    except Exception:
        pass

    rprint(f"  [green]Connected!{table_count}[/green]")
    rprint(f"  Saved as [bold]'{conn_name}'[/bold].")


# ---------------------------------------------------------------------------
# Snowflake interactive wizard
# ---------------------------------------------------------------------------

AUTH_CHOICES = {
    "1": "key_pair_existing",
    "2": "key_pair_generate",
    "3": "browser_sso",
}


def _snowflake_wizard() -> dict[str, Any]:
    """Prompt the user step-by-step and return a config dict."""
    rprint("\n[bold]Connect to Snowflake[/bold]\n")

    account = Prompt.ask("  Account identifier (e.g. MYORG-ACCOUNT01)")
    user = Prompt.ask("  Username")

    rprint("\n  Auth method:")
    rprint("  [bold]1[/bold]) Key pair - use existing key [dim](recommended)[/dim]")
    rprint("  [bold]2[/bold]) Key pair - generate new key")
    rprint("  [bold]3[/bold]) Browser SSO [dim](requires SAML IdP configured in Snowflake)[/dim]")
    auth_choice = Prompt.ask("  Choice", choices=["1", "2", "3"], default="1")
    auth_method = AUTH_CHOICES[auth_choice]

    config: dict[str, Any] = {"account": account, "user": user}

    if auth_method == "browser_sso":
        config["auth_method"] = "browser_sso"

    elif auth_method == "key_pair_existing":
        config.update(_wizard_existing_key())

    elif auth_method == "key_pair_generate":
        config.update(_wizard_generate_key(user))

    rprint()
    warehouse = Prompt.ask("  Warehouse")
    database = Prompt.ask("  Database")
    role = Prompt.ask("  Role [dim](optional, press Enter to skip)[/dim]", default="")

    config["warehouse"] = warehouse
    config["database"] = database
    if role:
        config["role"] = role

    return config


def _wizard_existing_key() -> dict[str, Any]:
    """Sub-flow: use an existing private key file."""
    key_path = Prompt.ask("  Path to private key file")
    passphrase = Prompt.ask(
        "  Key passphrase [dim](leave empty if none)[/dim]",
        default="",
        password=True,
    )
    result: dict[str, Any] = {"private_key_path": key_path}
    if passphrase:
        result["private_key_passphrase"] = passphrase
    return result


def _wizard_generate_key(username: str) -> dict[str, Any]:
    """Sub-flow: generate a new RSA key pair."""
    from calvinball.cli.keygen import generate_snowflake_keypair
    from calvinball.config.settings import CALVINBALL_DIR

    keys_dir = CALVINBALL_DIR / "keys"
    rprint("\n  Generating RSA key pair...")
    private_key_path, public_key_b64 = generate_snowflake_keypair(keys_dir)
    rprint(f"  [green]Private key saved to {private_key_path}[/green]\n")

    alter_sql = f"ALTER USER {username} SET RSA_PUBLIC_KEY='{public_key_b64}';"
    rprint("  Run this in Snowflake to register the public key:")
    rprint(f"  [bold]{'─' * 60}[/bold]")
    rprint(f"  {alter_sql}")
    rprint(f"  [bold]{'─' * 60}[/bold]\n")

    Prompt.ask("  Press Enter once you've run that command")

    return {"private_key_path": str(private_key_path)}
