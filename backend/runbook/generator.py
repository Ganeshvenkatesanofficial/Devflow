"""Runbook generation — combines ticket + codebase context + AI."""

from __future__ import annotations

import re
import time

from ..ai.base import AIEngine
from ..analyzer.codebase_scanner import CodebaseContext
from ..providers.base import Ticket
from ..utils.text_helpers import slugify
from .models import Runbook, Step


SYSTEM_PROMPT = """You are a senior developer assistant. Your job is to convert
a development ticket into a clear, actionable implementation plan.

Rules:
- Return ONLY a numbered list of steps
- Each step should be ONE clear action (under 15 words)
- Include 4 to 10 steps
- Do NOT include git steps (no checkout, commit, push, branch)
- Do NOT include test steps or PR steps (those are added automatically)
- If codebase context is provided, reference actual file paths and patterns
- Be specific: "Add login endpoint in src/api/auth.py" not "Create API endpoint"
"""


class RunbookGenerator:
    """Generates runbooks using AI with codebase context."""

    def __init__(self, ai_engine: AIEngine | None = None):
        self._ai = ai_engine

    async def generate(
        self,
        ticket: Ticket,
        codebase: CodebaseContext | None = None,
    ) -> Runbook:
        """Generate a full runbook for a ticket."""
        git_steps = self._make_git_steps(ticket.id, ticket.title)

        # Try AI generation
        if self._ai:
            try:
                ai_steps = await self._generate_with_ai(ticket, codebase)
                if ai_steps:
                    all_steps = [git_steps[0], *ai_steps, *git_steps[1:]]
                    model_name = getattr(self._ai, '_model', '')
                    provider_label = f"{self._ai.name} ({model_name})" if model_name else self._ai.name
                    return Runbook(
                        ticket_id=ticket.id,
                        ticket_title=ticket.title,
                        steps=all_steps,
                        ai_provider=provider_label,
                        codebase_aware=codebase is not None,
                    )
            except Exception as e:
                print(f"[DevFlow Generator] AI generation with {self._ai.name} failed: {e}")

        # Fallback: parse ticket text into steps
        fallback_steps = self._fallback_parse(ticket)
        all_steps = [git_steps[0], *fallback_steps, *git_steps[1:]]
        return Runbook(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            steps=all_steps,
            ai_provider="fallback",
            codebase_aware=False,
        )

    async def _generate_with_ai(
        self,
        ticket: Ticket,
        codebase: CodebaseContext | None,
    ) -> list[Step]:
        """Use AI to generate implementation steps."""
        prompt_parts = [ticket.full_text]

        if codebase:
            prompt_parts.append(
                "\n--- Codebase Context ---\n" + codebase.to_prompt_context()
            )

        prompt_parts.append(
            "\nGenerate a numbered implementation plan for this ticket."
        )

        response = await self._ai.generate(
            prompt="\n\n".join(prompt_parts),
            system_prompt=SYSTEM_PROMPT,
        )

        return self._parse_ai_response(response)

    def _parse_ai_response(self, text: str) -> list[Step]:
        """Parse numbered list from AI response into Step objects."""
        steps = []
        for line in text.strip().split("\n"):
            line = line.strip()
            # Remove numbering: "1. ", "1) ", "- ", "* "
            cleaned = re.sub(r"^(\d+[\.\)]\s*|[-•*]\s*)", "", line).strip()
            if len(cleaned) > 3:
                steps.append(Step(
                    id=f"step-{len(steps) + 1}-{int(time.time() * 1000)}",
                    title=cleaned,
                ))
        return steps

    def _fallback_parse(self, ticket: Ticket) -> list[Step]:
        """Parse ticket text directly when AI is unavailable."""
        source = ticket.acceptance_criteria or ticket.description
        if not source:
            return [Step(
                id=f"step-1-{int(time.time() * 1000)}",
                title="Review and implement the ticket requirements",
            )]

        steps = []
        for line in source.split("\n"):
            line = line.strip()
            cleaned = re.sub(r"^(\d+[\.\)]\s*|[-•*]\s*)", "", line).strip()
            if len(cleaned) > 3:
                steps.append(Step(
                    id=f"step-{len(steps) + 1}-{int(time.time() * 1000)}",
                    title=cleaned,
                ))

        return steps if steps else [Step(
            id=f"step-1-{int(time.time() * 1000)}",
            title="Review and implement the ticket requirements",
        )]

    def _make_git_steps(self, ticket_id: str, title: str) -> list[Step]:
        """Create the standard git workflow steps."""
        branch = f"feature/{ticket_id}-{slugify(title)[:40]}"
        ts = int(time.time() * 1000)

        return [
            Step(
                id=f"git-setup-{ts}",
                title="Setup: Fetch latest and create feature branch",
                description="Pull latest changes and create your feature branch.",
                commands=["git fetch origin", f"git checkout -b {branch}", "git status"],
                is_git_step=True,
            ),
            Step(
                id=f"git-test-{ts + 1}",
                title="Run tests to verify changes",
                description="Write tests for your changes and ensure they pass.",
                commands=["npm test", "npm run lint"],
                is_git_step=True,
            ),
            Step(
                id=f"git-commit-{ts + 2}",
                title="Commit and push changes",
                description="Stage all changes and push to remote.",
                commands=[
                    "git add -A",
                    f'git commit -m "feat(#{ticket_id}): {title[:60]}"',
                    "git push origin HEAD",
                ],
                is_git_step=True,
            ),
            Step(
                id=f"git-pr-{ts + 3}",
                title="Create pull request",
                description="Generate PR description and open a pull request.",
                is_git_step=True,
                is_pr_step=True,
            ),
        ]
