"""Runbook and Step data models."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Step:
    """A single implementation step in a runbook."""

    id: str
    title: str
    description: str = ""
    commands: list[str] = field(default_factory=list)
    is_completed: bool = False
    time_spent_seconds: float = 0
    started_at: Optional[float] = None
    is_git_step: bool = False
    is_pr_step: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "commands": self.commands,
            "isCompleted": self.is_completed,
            "timeSpentSeconds": self.time_spent_seconds,
            "startedAt": self.started_at,
            "isGitStep": self.is_git_step,
            "isPRStep": self.is_pr_step,
        }


@dataclass
class Runbook:
    """A complete implementation runbook for a ticket."""

    ticket_id: str
    ticket_title: str
    steps: list[Step] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    ai_provider: str = "none"
    codebase_aware: bool = False

    @property
    def progress(self) -> float:
        """Completion percentage (0.0 to 100.0)."""
        if not self.steps:
            return 0.0
        done = sum(1 for s in self.steps if s.is_completed)
        return round((done / len(self.steps)) * 100, 1)

    @property
    def total_time_seconds(self) -> float:
        return sum(s.time_spent_seconds for s in self.steps)

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.is_completed)

    def to_dict(self) -> dict:
        return {
            "ticketId": self.ticket_id,
            "ticketTitle": self.ticket_title,
            "steps": [s.to_dict() for s in self.steps],
            "createdAt": self.created_at,
            "aiProvider": self.ai_provider,
            "codebaseAware": self.codebase_aware,
            "progress": self.progress,
            "totalTimeSeconds": self.total_time_seconds,
            "completedSteps": self.completed_steps,
            "totalSteps": len(self.steps),
        }
