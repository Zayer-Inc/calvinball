# Calvinball

Autonomous data analyst agent that connects to your data warehouse and investigates questions on its own — querying, analyzing, and charting without hand-holding.

## Prerequisites

- Python 3.11+
- A Snowflake account
- An LLM API key (OpenAI, Anthropic, etc.)

## Installation

```bash
git clone https://github.com/Zayer-Inc/calvinball.git
cd calvinball
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Setup

### 1. Initialize config

```bash
calvinball config init
```

This creates `~/.calvinball/` with a default `config.toml`.

### 2. Set your LLM API key

Calvinball uses [litellm](https://docs.litellm.ai/) under the hood, so it works with any major LLM provider. Set the appropriate environment variable for your provider (add to `~/.zshrc` to persist across sessions):

```bash
# OpenAI (default)
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google
export GOOGLE_API_KEY="..."
```

To switch models, edit `~/.calvinball/config.toml`:

```toml
[llm]
model = "anthropic/claude-sonnet-4-5-20250929"
```

Or use the CLI:

```bash
calvinball config set llm.model "anthropic/claude-sonnet-4-5-20250929"
```

### 3. Connect to Snowflake

```bash
calvinball connect snowflake
```

This launches an interactive wizard that walks you through:

- Account identifier and username
- Auth method (key pair recommended, browser SSO if you have SAML configured)
- Warehouse, database, and optional role

For scripting/CI, you can pass credentials directly:

```bash
calvinball connect snowflake --credentials '{"account":"MYORG-ACCT01","user":"alice","private_key_path":"~/.ssh/snowflake_key.p8","warehouse":"COMPUTE_WH","database":"ANALYTICS"}'
```

## Usage

### Investigate a question

```bash
calvinball investigate "What are the top 10 routes by passenger volume?"
```

The agent will autonomously:
1. Explore your schema to understand available tables
2. Write and run SQL queries
3. Analyze results and run Python if needed
4. Generate charts
5. Present findings and enter an interactive follow-up conversation

Options:
- `--depth [shallow|normal|deep]` — controls how thorough the investigation is (default: `normal`)
- `--resume <id>` — pick up a previous investigation where it left off
- `--no-chat` — skip the interactive follow-up after the investigation

### Check status

```bash
calvinball status                # show everything
calvinball status --investigations  # recent investigations only
calvinball status --integrations    # connected data sources only
```

### Manage config

```bash
calvinball config show
calvinball config set llm.temperature 0.5
```

## Commands

| Command | Description |
|---------|-------------|
| `calvinball investigate "<question>"` | Run an autonomous data investigation |
| `calvinball connect <source>` | Connect a data source |
| `calvinball status` | Show investigations and connections |
| `calvinball config init\|show\|set` | Manage configuration |
