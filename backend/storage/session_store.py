"""Simple JSON file-based storage for runbook sessions."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional


class SessionStore:
    """Stores runbook data, records, and config in a JSON file.

    In the VS Code extension, the extension shell handles VS Code's
    SecretStorage for credentials. This store handles runbook data
    and completion records that the Python backend manages.
    """

    def __init__(self, storage_path: str | Path):
        self._path = Path(storage_path)
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            try:
                self._path = Path.cwd() / ".devflow" / "store.json"
                self._path.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                import tempfile
                self._path = Path(tempfile.gettempdir()) / ".devflow" / "store.json"
                try:
                    self._path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if self._path.exists():
                return json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError, PermissionError):
            return {}
        return {}

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, indent=2))
        except (OSError, PermissionError):
            pass

    # --- Runbook storage ---

    def save_runbook(self, ticket_id: str, runbook_data: dict) -> None:
        key = f"runbook_{ticket_id}"
        self._data[key] = {**runbook_data, "saved_at": time.time()}
        self._save()

    def load_runbook(self, ticket_id: str) -> Optional[dict]:
        return self._data.get(f"runbook_{ticket_id}")

    # --- Completion records ---

    def get_records(self) -> dict:
        return self._data.get("records", {
            "completed_ticket_ids": [],
            "total_tickets_done": 0,
            "total_time_spent": 0,
            "fastest_ticket": None,
            "completed_tickets": [],
            "streak": {"current": 0, "best": 0, "last_date": None},
        })

    def record_completion(
        self, ticket_id: str, title: str, time_seconds: float, steps_count: int
    ) -> dict:
        records = self.get_records()
        ids = records["completed_ticket_ids"]

        entry = {
            "id": ticket_id,
            "title": title,
            "time_spent": max(0, time_seconds),
            "steps_count": steps_count,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # Remove old entry if re-completing
        old = next((t for t in records["completed_tickets"] if t["id"] == ticket_id), None)
        records["completed_tickets"] = [
            t for t in records["completed_tickets"] if t["id"] != ticket_id
        ]
        records["completed_tickets"].insert(0, entry)
        records["completed_tickets"] = records["completed_tickets"][:50]

        if ticket_id not in ids:
            ids.append(ticket_id)
        records["completed_ticket_ids"] = ids
        records["total_tickets_done"] = len(ids)

        old_time = old["time_spent"] if old else 0
        records["total_time_spent"] = max(0, records["total_time_spent"] - old_time + entry["time_spent"])

        if entry["time_spent"] > 0:
            fastest = records.get("fastest_ticket")
            if not fastest or entry["time_spent"] < fastest["time_spent"]:
                records["fastest_ticket"] = entry

        # Streak tracking
        today = time.strftime("%Y-%m-%d")
        yesterday = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400))
        streak = records.get("streak", {"current": 0, "best": 0, "last_date": None})
        if streak["last_date"] != today:
            streak["current"] = streak["current"] + 1 if streak["last_date"] == yesterday else 1
            streak["best"] = max(streak["best"], streak["current"])
            streak["last_date"] = today
        records["streak"] = streak

        self._data["records"] = records
        self._save()
        return records

    # --- Generic ---

    def clear_all(self) -> None:
        self._data = {}
        self._save()
