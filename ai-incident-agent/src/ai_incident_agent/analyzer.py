from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory) if directory else self.default_directory()
        self.entries = self._load_entries()

    def default_directory(self) -> Path:
        return Path(__file__).resolve().parents[2] / "knowledgeBase"

    def _load_entries(self) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        if not self.directory.exists():
            return entries

        for file_path in sorted(self.directory.iterdir()):
            if file_path.is_file():
                entry = self._parse_entry(file_path)
                if entry:
                    entries.append(entry)

        return entries

    def _parse_entry(self, file_path: Path) -> dict[str, str] | None:
        current_key: str | None = None
        entry: dict[str, str] = {"file_name": file_path.name}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                for raw_line in file:
                    line = raw_line.strip()
                    if not line or line == "---":
                        continue

                    if line.startswith("##"):
                        current_key = line.lstrip("#").strip().lower().replace(" ", "_")
                        entry[current_key] = ""
                        continue

                    if current_key:
                        entry[current_key] = f"{entry[current_key]}{line}\n" if entry[current_key] else line

            for key, value in list(entry.items()):
                if isinstance(value, str):
                    entry[key] = value.strip()

            if "title" not in entry:
                entry["title"] = entry.get("error_title", file_path.stem)

            entry["full_text"] = "\n".join(
                str(value) for value in (
                    entry.get("title"),
                    entry.get("error_description"),
                    entry.get("root_cause"),
                    entry.get("resolution"),
                )
                if value
            )

            return entry
        except Exception as e:
            logger.warning(f"Failed to parse knowledge base file {file_path}: {e}")
            return None

    def find_match(self, message: str) -> dict[str, str] | None:
        normalized_message = message.lower()
        for entry in self.entries:
            search_fields = [
                entry.get("title", ""),
                entry.get("error_title", ""),
                entry.get("error_description", ""),
                entry.get("root_cause", ""),
                entry.get("resolution", ""),
                entry.get("full_text", ""),
            ]
            for field in search_fields:
                if not field:
                    continue
                normalized_field = field.lower()
                if normalized_field in normalized_message or normalized_message in normalized_field:
                    return entry

            keywords = [keyword.strip() for keyword in (entry.get("title", "") + " " + entry.get("error_title", "")).split() if keyword]
            if any(keyword in normalized_message for keyword in keywords):
                return entry

        return None

class Analyzer:
    def __init__(self, model_client: Any, knowledge_base_dir: Path | str | None = None) -> None:
        self.model_client = model_client
        self.knowledge_base = KnowledgeBase(knowledge_base_dir)

    def root_cause(self, anomaly: dict[str, Any]) -> dict[str, Any]:
        """Generate a root cause summary and remediation guidance using GPT-4 or the local knowledge base."""
        message = anomaly.get("message", "unknown issue")
        kb_entry = self.knowledge_base.find_match(message)
        if kb_entry:
            recommendation = kb_entry.get("resolution", "Review the knowledge base for remediation steps.")
            summary = kb_entry.get("root_cause") or kb_entry.get("error_description") or f"Known issue: {kb_entry.get('title', 'unknown')}."
            return {
                "summary": summary,
                "impact": "medium",
                "recommendation": recommendation,
                "source": "knowledge_base",
                "knowledge_base_entry": kb_entry.get("title", kb_entry.get("file_name")),
                "knowledge_base": {
                    "title": kb_entry.get("title", kb_entry.get("file_name")),
                    "error_id": kb_entry.get("error_id"),
                    "error_description": kb_entry.get("error_description"),
                    "root_cause": kb_entry.get("root_cause"),
                    "resolution": kb_entry.get("resolution"),
                    "owner": kb_entry.get("owner"),
                    "last_updated": kb_entry.get("last_updated"),
                },
            }

        prompt = f"""
Analyze this log anomaly and provide a brief root cause analysis:

Log Entry: {anomaly.get('message', 'unknown issue')}
Source: {anomaly.get('source', 'unknown')}
Level: {anomaly.get('level', 'unknown')}
Timestamp: {anomaly.get('timestamp', 'unknown')}

Provide a JSON response (no markdown, just JSON) with exactly this structure:
{{
  "summary": "brief explanation of what happened",
  "impact": "low or medium or high",
  "recommendation": "actionable recommendation"
}}
"""
        try:
            response = self.model_client.summarize(prompt)
            logger.info(f"GPT-4 response: {response}")
            print(f"[DEBUG] GPT-4 root_cause response: {response}")
            
            # Try to extract JSON from the response
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from GPT-4 response: {e}")
            print(f"[DEBUG] JSON parse error: {e}")
            print(f"[DEBUG] Raw response was: {response}")
            return {
                "summary": f"Detected {anomaly.get('message', 'unknown issue')}.",
                "impact": "medium",
                "recommendation": "Review the affected service logs and configuration.",
            }
        except Exception as e:
            logger.error(f"Error in root_cause analysis: {e}")
            print(f"[DEBUG] Unexpected error: {e}")
            return {
                "summary": f"Detected {anomaly.get('message', 'unknown issue')}.",
                "impact": "medium",
                "recommendation": "Review the affected service logs and configuration.",
            }

    def prioritize(self, incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(incidents, key=lambda item: item.get("severity", 0), reverse=True)
