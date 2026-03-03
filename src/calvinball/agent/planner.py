"""Investigation planning (thin wrapper — the LLM does the real planning)."""

from __future__ import annotations


def format_question_prompt(question: str, depth: str = "normal") -> str:
    """Format the user's question for the first message."""
    return (
        f"Investigate the following question:\n\n"
        f"**{question}**\n\n"
        f"Start by orienting — think about what data and tools you'll need, "
        f"then dive in."
    )
