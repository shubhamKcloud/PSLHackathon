from __future__ import annotations

import os
from pathlib import Path
from typing import Any

class LogMonitor:
    def __init__(self, sources: list[str]) -> None:
        self.sources = [Path(source) for source in sources]
        self._positions: dict[str, int] = {}

    def collect(self) -> list[dict[str, Any]]:
        """Collect new log lines from configured files or folders."""
        events: list[dict[str, Any]] = []

        for source in self.sources:
            if source.is_dir():
                log_files = sorted(source.glob("*.log"))
                for path in log_files:
                    new_events = self._read_new_lines(path)
                    if new_events:
                        print(f"[LOG_MONITOR] Read {len(new_events)} new lines from {path.name}")
                    events.extend(new_events)
            elif source.is_file():
                new_events = self._read_new_lines(source)
                if new_events:
                    print(f"[LOG_MONITOR] Read {len(new_events)} new lines from {source.name}")
                events.extend(new_events)
            elif source.exists():
                continue

        return events

    def _read_new_lines(self, path: Path) -> list[dict[str, Any]]:
        path_key = str(path.resolve())
        events: list[dict[str, Any]] = []
        last_position = self._positions.get(path_key, 0)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                file.seek(last_position)
                for line in file:
                    if entry := self._parse_line(line.strip(), path):
                        events.append(entry)
                self._positions[path_key] = file.tell()
        except FileNotFoundError:
            return []

        return events

    def _parse_line(self, line: str, path: Path) -> dict[str, Any] | None:
        if not line:
            return None

        normalized = line.lower()
        if "error" in normalized:
            level = "error"
        elif "critical" in normalized:
            level = "critical"
        elif "warn" in normalized or "warning" in normalized:
            level = "warn"
        elif "info" in normalized:
            level = "info"
        else:
            level = "unknown"

        return {
            "raw_line": line,
            "level": level,
            "source": path.name,
            "message": line,
            "path": str(path),
        }

    def detect_anomalies(self, logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect anomalies or error conditions within ingested logs."""
        anomalies = [entry for entry in logs if entry.get("level") in {"error", "critical"}]
        return anomalies
