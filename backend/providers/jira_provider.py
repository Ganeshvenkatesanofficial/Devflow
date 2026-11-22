"""Jira Cloud / Server ticket provider."""

from __future__ import annotations

import base64
from typing import Any

from .base import HTTPTicketProvider, Ticket
from ..utils.html_parser import html_to_text


_FIELDS = ",".join([
    "summary", "description", "status", "issuetype",
    "assignee", "labels",
    "customfield_10016",                                           # story points
    "customfield_10028", "customfield_10029", "customfield_10030", # acceptance criteria variants
])
_AC_FIELDS = ("customfield_10029", "customfield_10028", "customfield_10030")


class JiraProvider(HTTPTicketProvider):
    """Fetches tickets from Jira Cloud or Server."""

    def __init__(self, base_url: str, email: str, api_token: str):
        self._base_url = base_url.rstrip("/")
        self._auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()

    @property
    def name(self) -> str:
        return "jira"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Basic {self._auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def _validate_url(self) -> str:
        return f"{self._base_url}/rest/api/2/myself"

    async def fetch_ticket(self, ticket_id: str) -> Ticket:
        data = await self._get_json(
            f"{self._base_url}/rest/api/2/issue/{ticket_id}?fields={_FIELDS}"
        )
        return self._normalize(ticket_id, data)

    def _normalize(self, ticket_id: str, data: dict[str, Any]) -> Ticket:
        f = data.get("fields", {})
        ac_raw = next((f.get(k) for k in _AC_FIELDS if f.get(k)), None)
        assignee = f.get("assignee") or {}
        return Ticket(
            id=ticket_id,
            provider=self.name,
            title=f.get("summary", "Untitled"),
            description=html_to_text(f.get("description", "")),
            acceptance_criteria=html_to_text(ac_raw) if ac_raw else "",
            ticket_type=f.get("issuetype", {}).get("name", "Issue"),
            status=f.get("status", {}).get("name", "Unknown"),
            story_points=f.get("customfield_10016"),
            assigned_to=assignee.get("displayName"),
            labels=f.get("labels", []),
            url=f"{self._base_url}/browse/{ticket_id}",
        )
