from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

class Ticketing:
    def __init__(self, provider: str, config: dict[str, Any]) -> None:
        self.provider = provider
        self.config = config
        self.ticket_dir = Path(self.config.get("ticket_dir", "tickets"))
        self.ticket_dir.mkdir(parents=True, exist_ok=True)

    def create_ticket(self, incident: dict[str, Any]) -> dict[str, Any]:
        """Create or update an incident ticket in the configured system."""
        ticket_id = incident.get("id") or f"FILE-{uuid.uuid4().hex[:8]}"
        ticket = {
            "id": ticket_id,
            "status": incident.get("status", "open"),
            "title": incident.get("title", "AI-detected incident"),
            "description": incident.get("description", "Automated incident created."),
            "severity": incident.get("severity", "P2"),
            "root_cause": incident.get("root_cause", "Not available"),
            "analysis_source": incident.get("analysis_source", "ai"),
            "resolution": incident.get("resolution", "Review the affected service logs and configuration."),
            "owner": incident.get("owner", "Unknown"),
            "raw": incident.get("raw", {}),
            "analysis": incident.get("analysis", {}),
        }

        if self.provider == "file":
            self._write_ticket_file(ticket)

        return ticket

    def _write_ticket_file(self, ticket: dict[str, Any]) -> None:
        file_name = f"{ticket['id']}.json"
        ticket_path = self.ticket_dir / file_name
        ticket["file_path"] = str(ticket_path)
        with open(ticket_path, "w", encoding="utf-8") as file:
            json.dump(ticket, file, indent=2)
