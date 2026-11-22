"""GitHub Issues ticket provider."""

from __future__ import annotations

from .base import HTTPTicketProvider, Ticket


_AC_MARKERS = (
    "## Acceptance Criteria",
    "### Acceptance Criteria",
    "**Acceptance Criteria**",
)


class GitHubProvider(HTTPTicketProvider):
    """Fetches issues from GitHub repositories."""

    def __init__(self, token: str, owner: str, repo: str):
        self._token = token
        self._owner = owner
        self._repo = repo

    @property
    def name(self) -> str:
        return "github"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DevFlow-VSCode",
        }

    @property
    def _validate_url(self) -> str:
        return "https://api.github.com/user"

    async def fetch_ticket(self, ticket_id: str) -> Ticket:
        data = await self._get_json(
            f"https://api.github.com/repos/{self._owner}/{self._repo}/issues/{ticket_id}"
        )
        return self._normalize(ticket_id, data)

    def _normalize(self, ticket_id: str, data: dict) -> Ticket:
        body = data.get("body") or ""
        description, acceptance = body, ""
        for marker in _AC_MARKERS:
            if marker in body:
                head, tail = body.split(marker, 1)
                description, acceptance = head.strip(), tail.strip()
                break

        assignee = data.get("assignee") or {}
        return Ticket(
            id=ticket_id,
            provider=self.name,
            title=data.get("title", "Untitled"),
            description=description,
            acceptance_criteria=acceptance,
            ticket_type="Pull Request" if data.get("pull_request") else "Issue",
            status=data.get("state", "open"),
            story_points=None,
            assigned_to=assignee.get("login"),
            labels=[l.get("name", "") for l in data.get("labels", [])],
            url=data.get("html_url", ""),
        )
