"""Azure DevOps ticket provider."""

from __future__ import annotations

import base64
from typing import Any

from .base import HTTPTicketProvider, Ticket
from ..utils.html_parser import html_to_text


_FIELDS = ",".join([
    "System.Title", "System.Description",
    "Microsoft.VSTS.Common.AcceptanceCriteria",
    "System.State", "System.WorkItemType",
    "Microsoft.VSTS.Scheduling.StoryPoints",
    "System.AssignedTo", "System.Tags",
])


class AzureDevOpsProvider(HTTPTicketProvider):
    """Fetches work items from Azure DevOps."""

    def __init__(self, org_url: str, project: str, pat: str):
        self._org_url = org_url.rstrip("/")
        self._project = project
        self._auth = base64.b64encode(f":{pat}".encode()).decode()

    @property
    def name(self) -> str:
        return "azure"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Basic {self._auth}",
            "Content-Type": "application/json",
        }

    @property
    def _validate_url(self) -> str:
        return f"{self._org_url}/_apis/projects?api-version=7.0&$top=1"

    async def fetch_ticket(self, ticket_id: str) -> Ticket:
        data = await self._get_json(
            f"{self._org_url}/{self._project}/_apis/wit/workitems/{ticket_id}"
            f"?fields={_FIELDS}&api-version=7.0"
        )
        return self._normalize(ticket_id, data)

    def _normalize(self, ticket_id: str, data: dict[str, Any]) -> Ticket:
        f = data.get("fields", {})
        tags_raw = f.get("System.Tags", "") or ""
        assigned = f.get("System.AssignedTo")
        assigned_name = (
            assigned.get("displayName") if isinstance(assigned, dict) else assigned
        )
        return Ticket(
            id=ticket_id,
            provider=self.name,
            title=f.get("System.Title", "Untitled"),
            description=html_to_text(f.get("System.Description", "")),
            acceptance_criteria=html_to_text(
                f.get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
            ),
            ticket_type=f.get("System.WorkItemType", "Work Item"),
            status=f.get("System.State", "Unknown"),
            story_points=f.get("Microsoft.VSTS.Scheduling.StoryPoints"),
            assigned_to=assigned_name,
            labels=[t.strip() for t in tags_raw.split(";") if t.strip()],
            url=f"{self._org_url}/{self._project}/_workitems/edit/{ticket_id}",
        )
