"""Investigation, Finding, Thread dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Finding:
    """A single finding from an investigation."""
    summary: str
    evidence: str = ""
    confidence: float = 0.5  # 0.0 - 1.0
    artifacts: list[str] = field(default_factory=list)  # file paths


@dataclass
class Thread:
    """A sub-line of inquiry within an investigation."""
    question: str
    status: str = "open"  # open, resolved, abandoned
    findings: list[Finding] = field(default_factory=list)


@dataclass
class Investigation:
    """An autonomous investigation session."""
    id: str
    question: str
    status: str = "running"  # running, complete, failed, paused
    depth: str = "normal"
    threads: list[Thread] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    report: str | None = None
    created_at: str = ""
    updated_at: str = ""
