"""Generate AI-powered PR descriptions from completed runbooks."""

from __future__ import annotations

from ..ai.base import AIEngine
from ..runbook.models import Runbook


PR_SYSTEM_PROMPT = """You are a senior developer writing a pull request description.
Write a concise, professional PR description with:
1. Brief summary (2-3 sentences)
2. Bullet list of what was implemented (completed items only)
3. Testing checklist

Do NOT mention time spent. Do NOT include git/branch/commit steps.
"""


class PRDescriptionGenerator:
    """Generates PR descriptions from runbook data."""

    def __init__(self, ai_engine: AIEngine | None = None):
        self._ai = ai_engine

    async def generate(self, runbook: Runbook, ticket_type: str = "Task") -> str:
        """Generate a PR description."""
        user_steps = [s for s in runbook.steps if not s.is_git_step]
        steps_summary = "\n".join(
            f"{i+1}. [{'DONE' if s.is_completed else 'PENDING'}] {s.title}"
            for i, s in enumerate(user_steps)
        )

        if self._ai:
            try:
                prompt = (
                    f"Ticket: #{runbook.ticket_id} - {runbook.ticket_title}\n"
                    f"Type: {ticket_type}\n\n"
                    f"Tasks:\n{steps_summary}\n\n"
                    f"Write a PR description."
                )
                return await self._ai.generate(prompt, PR_SYSTEM_PROMPT)
            except Exception:
                pass

        # Plain fallback
        return self._plain_pr(runbook, user_steps)

    @staticmethod
    def _plain_pr(runbook: Runbook, user_steps: list) -> str:
        done = [s for s in user_steps if s.is_completed]
        pending = [s for s in user_steps if not s.is_completed]

        lines = [
            f"## {runbook.ticket_title}",
            "",
            f"**Ticket:** #{runbook.ticket_id}",
            "",
            "## What was done",
        ]
        if done:
            lines.extend(f"- ✅ {s.title}" for s in done)
        else:
            lines.append("- No steps completed yet")

        if pending:
            lines.append("")
            lines.append("## Remaining")
            lines.extend(f"- ⬜ {s.title}" for s in pending)

        lines.extend([
            "",
            "## Checklist",
            "- [ ] Code reviewed",
            "- [ ] Tests passing",
            "- [ ] No console errors",
            "- [ ] Acceptance criteria verified",
        ])

        return "\n".join(lines)
