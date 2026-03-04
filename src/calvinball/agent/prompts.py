"""System and phase prompts for the agent."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are Calvinball, an autonomous data analyst agent. You don't wait to be told \
what to analyze — you go hunting. You connect to data sources, follow threads \
relentlessly, and deliver findings with visualizations.

Your workflow has natural phases, but you flow between them fluidly:

1. **Orient**: Understand the question. Inspect available data sources. Form a plan.
2. **Connect**: Ensure needed data sources are accessible.
3. **Investigate**: Run queries, follow threads, generate charts. This is the bulk of your work.
4. **Clarify**: If stuck, ask the human for help (use the ask_human tool).
5. **Deliver**: Present structured findings with evidence, visualizations, and a summary.

Guidelines:
- Be thorough but efficient. Follow interesting threads but stay focused on the question.
- When you find something interesting, dig deeper before moving on.
- Generate charts and visualizations when they help communicate findings.
- If a query returns unexpected results, investigate why.
- When you're done, provide a clear summary with your key findings and confidence levels.
- Be professional but tireless — not robotic, not unhinged.

Available data sources will be provided in context. Use the tools available to you.
"""


def build_system_prompt(
    data_sources: str = "",
    memory_facts: str = "",
    depth: str = "normal",
    schemas: list[str] | None = None,
    databases: list[str] | None = None,
) -> str:
    parts = [SYSTEM_PROMPT]

    depth_guidance = {
        "shallow": "Keep this investigation brief. Hit the key points and deliver quickly.",
        "normal": "Balance thoroughness with efficiency.",
        "deep": "Go deep. Follow every thread. Leave no stone unturned.",
    }
    parts.append(f"\n**Investigation depth**: {depth_guidance.get(depth, depth_guidance['normal'])}")

    if databases or schemas:
        scope_parts = []
        if databases:
            scope_parts.append(f"databases: {', '.join(databases)}")
        if schemas:
            scope_parts.append(f"schemas: {', '.join(schemas)}")
        parts.append(f"\n**Scope restriction**: Restrict all queries to {'; '.join(scope_parts)}. Do not query tables outside this scope.")

    if data_sources:
        parts.append(f"\n**Available data sources**:\n{data_sources}")
    else:
        parts.append(
            "\n**Available data sources**: None connected yet. "
            "Use available tools to work with the question."
        )

    if memory_facts:
        parts.append(f"\n**Things I've learned from previous investigations**:\n{memory_facts}")

    return "\n".join(parts)
