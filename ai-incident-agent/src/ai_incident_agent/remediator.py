from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class Remediator:
    def __init__(self, model_client: Any) -> None:
        self.model_client = model_client

    def generate_fix(self, incident: dict[str, Any]) -> dict[str, Any]:
        """Generate a code fix recommendation or remediation playbook using GPT-4."""
        prompt = f"""
Based on this incident, suggest remediation steps:

Title: {incident.get('title', 'unknown')}
Description: {incident.get('description', 'unknown')}
Analysis: {incident.get('analysis', {}).get('summary', 'no analysis')}
Raw Log: {incident.get('raw', {}).get('message', 'unknown')}

Provide a JSON response (no markdown, just JSON) with exactly this structure:
{{
  "fix_summary": "brief explanation of the fix",
  "playbook": ["step 1", "step 2", "step 3"],
  "priority": "immediate or urgent or normal"
}}
"""
        try:
            response = self.model_client.summarize(prompt)
            logger.info(f"GPT-4 response: {response}")
            print(f"[DEBUG] GPT-4 generate_fix response: {response}")
            
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from GPT-4 response: {e}")
            print(f"[DEBUG] JSON parse error: {e}")
            print(f"[DEBUG] Raw response was: {response}")
            return {
                "fix_summary": "Investigate recent deployment changes and patch the failing service.",
                "playbook": [
                    "Restart the affected service",
                    "Roll back the last deployment if the error persists",
                    "Update alert thresholds to track regression",
                ],
                "priority": "normal",
            }
        except Exception as e:
            logger.error(f"Error in generate_fix: {e}")
            print(f"[DEBUG] Unexpected error: {e}")
            return {
                "fix_summary": "Investigate recent deployment changes and patch the failing service.",
                "playbook": [
                    "Restart the affected service",
                    "Roll back the last deployment if the error persists",
                    "Update alert thresholds to track regression",
                ],
                "priority": "normal",
            }

    def execute_remediation(self, fix: dict[str, Any]) -> dict[str, Any]:
        """Execute or simulate a remediation workflow."""
        return {"status": "pending", "details": fix}
