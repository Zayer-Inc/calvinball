"""Core autonomous loop — the heart of Calvinball."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from calvinball.agent.executor import execute_tool_call
from calvinball.agent.planner import format_question_prompt
from calvinball.agent.prompts import build_system_prompt
from calvinball.config.settings import Settings
from calvinball.llm.client import LLMClient
from calvinball.llm.messages import MessageHistory
from calvinball.tools.builtin.ask_human import AskHumanTool
from calvinball.tools.builtin.file_io import ReadFileTool, WriteFileTool
from calvinball.tools.builtin.python_exec import PythonExecTool
from calvinball.tools.builtin.remember import RememberTool
from calvinball.tools.registry import ToolRegistry

console = Console()


def _build_default_registry() -> ToolRegistry:
    """Register all built-in tools."""
    registry = ToolRegistry()
    registry.register(PythonExecTool())
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(AskHumanTool())
    registry.register(RememberTool())
    return registry


async def _run_autonomous_phase(
    client: LLMClient,
    history: MessageHistory,
    registry: ToolRegistry,
    max_iterations: int,
) -> None:
    """Run the autonomous phase: LLM calls tools until it stops or hits max iterations."""
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Show progress
        console.print(f"[dim]── iteration {iteration} ──[/dim]")

        # Call LLM
        try:
            response = await client.chat(
                messages=history.to_api_messages(),
                tools=registry.all_specs() or None,
            )
        except Exception as e:
            console.print(f"[red]LLM error: {e}[/red]")
            break

        choice = response.choices[0]
        message = choice.message

        # Save the assistant message
        assistant_msg: dict[str, Any] = {"role": "assistant"}
        if message.content:
            assistant_msg["content"] = message.content
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]
        history.add_assistant(assistant_msg)

        # If the LLM produced text, show it
        if message.content:
            console.print(Markdown(message.content))

        # If no tool calls, the agent is done with this phase
        if not message.tool_calls:
            break

        # Execute tool calls
        for tc in message.tool_calls:
            func_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            console.print(f"  [cyan]→ {func_name}[/cyan]", end="")
            if func_name == "python_exec":
                console.print(f" [dim](code)[/dim]")
            else:
                arg_summary = ", ".join(f"{k}={repr(v)[:40]}" for k, v in args.items())
                console.print(f" [dim]({arg_summary})[/dim]")

            result = await execute_tool_call(registry, func_name, args)

            if result.success:
                output_preview = result.output[:200]
                if len(result.output) > 200:
                    output_preview += "..."
                console.print(f"    [green]✓[/green] [dim]{output_preview}[/dim]")
            else:
                console.print(f"    [red]✗ {result.error}[/red]")

            history.add_tool_result(tc.id, result.to_content())

    else:
        console.print(
            f"[yellow]Reached max iterations ({max_iterations}). Stopping.[/yellow]"
        )


async def run_investigation(
    question: str,
    depth: str = "normal",
    resume_id: str | None = None,
    interactive: bool = True,
    schemas: list[str] | None = None,
    databases: list[str] | None = None,
) -> None:
    """Run the autonomous investigation loop, optionally followed by interactive chat."""
    settings = Settings.load()
    client = LLMClient(settings.llm)
    registry = _build_default_registry()

    # Load additional tools (sql_query, chart, etc.) if integrations exist
    _register_integration_tools(registry)

    # Build system prompt
    data_sources = await _get_data_sources_description(schemas=schemas, databases=databases)
    memory_facts = await _get_memory_facts()
    system_prompt = build_system_prompt(data_sources, memory_facts, depth, schemas=schemas, databases=databases)

    # Initialize or resume message history
    if resume_id:
        history = await _load_history(resume_id, system_prompt)
        investigation_id = resume_id
        console.print(f"[dim]Resuming investigation {investigation_id[:8]}...[/dim]")
    else:
        history = MessageHistory(system_prompt)
        history.add_user(format_question_prompt(question, depth))
        investigation_id = uuid.uuid4().hex[:12]

    console.print(
        Panel(
            f"[bold]{question}[/bold]\n[dim]ID: {investigation_id} | Depth: {depth}[/dim]",
            title="🔍 Investigation",
            border_style="blue",
        )
    )

    # Phase 1: Autonomous investigation
    await _run_autonomous_phase(client, history, registry, settings.llm.max_iterations)
    await _checkpoint(investigation_id, question, depth, history)

    if not interactive:
        console.print(
            Panel("[green]Investigation complete.[/green]", border_style="green")
        )
        await _checkpoint(investigation_id, question, depth, history, status="complete")
        return

    # Phase 2: Interactive conversation loop
    console.print(
        Panel(
            "[green]Investigation complete.[/green]\n"
            "[dim]Ask follow-up questions, or type [bold]done[/bold] to exit.[/dim]",
            border_style="green",
        )
    )

    while True:
        try:
            user_input = console.input("[bold blue]calvinball>[/bold blue] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "done"):
            break

        history.add_user(user_input)
        await _run_autonomous_phase(
            client, history, registry, settings.llm.max_iterations
        )
        await _checkpoint(investigation_id, question, depth, history)

    console.print("[dim]Goodbye.[/dim]")
    await _checkpoint(investigation_id, question, depth, history, status="complete")


def _register_integration_tools(registry: ToolRegistry) -> None:
    """Register tools from loaded integrations."""
    try:
        from calvinball.tools.builtin.sql_query import SQLQueryTool, DescribeSchemaTool
        registry.register(SQLQueryTool())
        registry.register(DescribeSchemaTool())
    except ImportError:
        pass

    try:
        from calvinball.tools.builtin.chart import ChartTool
        registry.register(ChartTool())
    except ImportError:
        pass

    try:
        from calvinball.tools.builtin.build_integration import BuildIntegrationTool
        registry.register(BuildIntegrationTool())
    except ImportError:
        pass

    # Load generated tools
    from calvinball.config.settings import GENERATED_TOOLS_DIR
    if GENERATED_TOOLS_DIR.exists():
        for py_file in GENERATED_TOOLS_DIR.glob("*.py"):
            try:
                registry.load_generated_tool(py_file)
            except Exception:
                pass


async def _get_data_sources_description(
    schemas: list[str] | None = None,
    databases: list[str] | None = None,
) -> str:
    """Get descriptions of connected data sources."""
    try:
        from calvinball.integrations.manager import IntegrationManager
        mgr = IntegrationManager()
        return await mgr.describe_all(schemas=schemas, databases=databases)
    except Exception:
        return ""


async def _get_memory_facts() -> str:
    """Load learned facts from memory."""
    try:
        from calvinball.persistence.memory import load_facts
        return await load_facts()
    except Exception:
        return ""


async def _load_history(investigation_id: str, system_prompt: str) -> MessageHistory:
    """Load message history from a previous investigation."""
    try:
        from calvinball.persistence.db import get_db
        db = await get_db()
        row = await db.execute_fetchone(
            "SELECT messages FROM investigations WHERE id = ?",
            (investigation_id,),
        )
        await db.close()
        if row:
            messages = json.loads(row["messages"])
            return MessageHistory.from_saved(system_prompt, messages)
    except Exception:
        pass
    return MessageHistory(system_prompt)


async def _checkpoint(
    investigation_id: str,
    question: str,
    depth: str,
    history: MessageHistory,
    status: str = "running",
) -> None:
    """Save investigation state to SQLite."""
    try:
        from calvinball.persistence.db import get_db
        from calvinball.config.settings import ensure_dirs

        ensure_dirs()
        db = await get_db()
        now = datetime.now(timezone.utc).isoformat()
        messages_json = json.dumps(history.serializable())

        await db.execute(
            """INSERT INTO investigations (id, question, status, depth, messages, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 status = excluded.status,
                 messages = excluded.messages,
                 updated_at = excluded.updated_at""",
            (investigation_id, question, status, depth, messages_json, now, now),
        )
        await db.commit()
        await db.close()
    except Exception:
        pass  # Don't let checkpoint failures kill the investigation
