"""Base ticket provider interfaces and normalized Ticket model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx


@dataclass
class Ticket:
    """Normalized ticket regardless of source (Jira, Azure, GitHub)."""

    id: str
    provider: str
    title: str
    description: str
    acceptance_criteria: str
    ticket_type: str = "Task"
    status: str = "Unknown"
    story_points: Optional[float] = None
    assigned_to: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    url: Optional[str] = None

    @property
    def full_text(self) -> str:
        """Combined text for AI analysis."""
        parts = [f"Title: {self.title}"]
        if self.description:
            parts.append(f"Description: {self.description}")
        if self.acceptance_criteria:
            parts.append(f"Acceptance Criteria: {self.acceptance_criteria}")
        return "\n\n".join(parts)


class TicketProvider(ABC):
    """Abstract base for all ticket providers."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def fetch_ticket(self, ticket_id: str) -> Ticket: ...

    @abstractmethod
    async def validate_connection(self) -> bool: ...


class HTTPTicketProvider(TicketProvider):
    """Shared HTTP boilerplate for REST-based ticket providers.

    Subclasses provide `_headers`, `_validate_url`, and implement
    `fetch_ticket` + `_normalize`. The shared client handles timeouts,
    error swallowing in validation, and JSON parsing.
    """

    DEFAULT_TIMEOUT = 15.0

    @property
    @abstractmethod
    def _headers(self) -> dict[str, str]: ...

    @property
    @abstractmethod
    def _validate_url(self) -> str: ...

    async def _get_json(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            resp = await client.get(url, headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def validate_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                resp = await client.get(self._validate_url, headers=self._headers)
                return resp.status_code == 200
        except Exception:
            return False
