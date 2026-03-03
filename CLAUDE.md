# Calvinball — Development Guide

## What this is

Calvinball is an autonomous data analyst agent. It connects to data warehouses (currently Snowflake), takes a natural language question, and autonomously investigates it — writing SQL, running Python, generating charts, and presenting findings.

## Project structure

```
src/calvinball/
├── cli/              # Typer CLI commands
│   ├── app.py        # Main Typer app, registers all commands
│   ├── connect.py    # `calvinball connect` with interactive wizard
│   ├── investigate.py# `calvinball investigate` entry point
│   ├── status.py     # `calvinball status`
│   ├── config_cmd.py # `calvinball config init|show|set`
│   └── keygen.py     # RSA key pair generation for Snowflake
├── agent/            # Autonomous agent loop
│   ├── loop.py       # Core loop: LLM → tool calls → results → repeat
│   ├── executor.py   # Looks up and executes tools from registry
│   ├── planner.py    # Formats questions for the LLM
│   └── prompts.py    # System prompts
├── integrations/     # Data source connectors
│   ├── base.py       # BaseIntegration ABC
│   ├── manager.py    # IntegrationManager — create, persist, reload
│   └── snowflake.py  # SnowflakeIntegration (browser SSO + key pair)
├── tools/            # Tools the agent can call
│   ├── base.py       # BaseTool ABC + ToolResult dataclass
│   ├── registry.py   # ToolRegistry — register, lookup, list specs
│   ├── builtin/      # Built-in tools (sql_query, python_exec, chart, etc.)
│   └── generated/    # Hot-loaded tools created at runtime
├── llm/              # LLM client
│   ├── client.py     # Async litellm wrapper
│   └── messages.py   # Message history management
├── persistence/      # Storage
│   ├── db.py         # Async SQLite via aiosqlite
│   ├── schemas.sql   # DB schema (investigations, integrations, memory)
│   └── memory.py     # Long-term memory management
├── investigations/   # Investigation models
│   ├── manager.py
│   └── models.py
├── config/
│   └── settings.py   # Pydantic settings, paths, defaults
└── viz/
    └── charts.py     # Plotly chart generation
```

## Key conventions

- **Async everywhere.** All I/O (LLM calls, database, Snowflake queries, tool execution) is async. The CLI commands use `asyncio.run()` as the sync boundary.
- **litellm for LLM calls.** Supports any provider via `provider/model` strings (e.g. `openai/gpt-4o`, `anthropic/claude-sonnet-4-5-20250929`). API keys come from environment variables.
- **Typer for CLI, Rich for output.** All CLI commands are Typer functions. Use `rich.print` for styled output.
- **Abstract base classes for extensibility.** `BaseIntegration` and `BaseTool` define the interfaces. New data sources or tools implement these ABCs.
- **Config lives in `~/.calvinball/`.** SQLite database, config.toml, output directory, generated tools, and keys all live here.

## How the agent loop works

1. User asks a question via `calvinball investigate "..."`
2. `run_investigation()` in `agent/loop.py` sets up the LLM client, tool registry, and message history
3. The autonomous phase calls the LLM with available tool specs
4. LLM responds with tool calls (SQL queries, Python code, charts, etc.)
5. `executor.py` runs each tool and feeds results back to the LLM
6. Loop continues until the LLM stops calling tools or hits `max_iterations`
7. Investigation state is checkpointed to SQLite after each iteration (enables `--resume`)
8. After the autonomous phase, an interactive conversation loop lets the user ask follow-ups

## How integrations work

- `BaseIntegration` defines: `connect(config)`, `disconnect()`, `execute_query(query)`, `get_schema_info()`
- `IntegrationManager` creates instances, calls `connect()`, and persists config to SQLite
- On next run, `load_from_db()` reconnects saved integrations automatically
- The config dict is opaque JSON — each integration type defines its own keys

## How tools work

- `BaseTool` defines: `name`, `description`, `parameters` (JSON Schema), `execute(**kwargs)`
- `to_function_spec()` generates the OpenAI-style function spec for litellm
- `ToolResult` wraps output with optional error and artifacts (files, charts)
- `ToolRegistry` is a simple dict keyed by tool name
- Generated tools can be hot-loaded from Python files at runtime

## Adding a new data source

1. Create `src/calvinball/integrations/newtype.py` implementing `BaseIntegration`
2. Register it in `integrations/manager.py` `_INTEGRATION_TYPES` dict
3. Optionally add a wizard sub-flow in `cli/connect.py`

## Adding a new built-in tool

1. Create `src/calvinball/tools/builtin/newtool.py` with a `BaseTool` subclass
2. Register it in the tool loading section of `agent/loop.py`

## Dependencies

- `typer` — CLI framework
- `rich` — Terminal UI
- `litellm` — LLM abstraction (OpenAI, Anthropic, Google, etc.)
- `snowflake-connector-python` — Snowflake connectivity
- `cryptography` — RSA key generation (transitive dep of snowflake connector)
- `aiosqlite` — Async SQLite
- `pydantic-settings` — Configuration
- `plotly` + `kaleido` — Charts

## Running tests

```bash
pip install -e ".[dev]"
pytest
```
