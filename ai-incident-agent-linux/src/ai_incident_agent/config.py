from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class ConfigLoader:
    """Load and parse configuration from YAML files."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """
        Initialize config loader.

        Args:
            config_path: Path to config.yaml file. If not provided, looks for config.yaml
                        in the project root.
        """
        if config_path is None:
            config_path = Path(__file__).resolve().parents[2] / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}

        if self.config_path.exists():
            self._load_config()
        else:
            print(f"[CONFIG] No config.yaml found at {self.config_path}")
            print(f"[CONFIG] Using defaults. Copy config.example.yaml to config.yaml to customize.")

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as file:
                self.config = yaml.safe_load(file) or {}
            self._substitute_env_vars()
            print(f"[CONFIG] Loaded configuration from {self.config_path}")
        except Exception as e:
            print(f"[CONFIG] Error loading config: {e}")
            self.config = {}

    def _substitute_env_vars(self) -> None:
        """Recursively substitute ${VAR_NAME} with environment variables."""
        def substitute_value(value: Any) -> Any:
            if isinstance(value, str):
                # Replace ${VAR_NAME} patterns
                import re
                def replace_var(match: Any) -> str:
                    var_name = match.group(1)
                    return os.getenv(var_name, match.group(0))
                
                return re.sub(r"\$\{([^}]+)\}", replace_var, value)
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(v) for v in value]
            return value

        self.config = substitute_value(self.config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key (e.g., 'cloudwatch.log_group')."""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_local_logs_config(self) -> dict[str, Any]:
        """Get local logs configuration."""
        return self.get("local_logs", {"enabled": True, "paths": ["logs"]})

    def get_cloudwatch_config(self) -> dict[str, Any]:
        """Get CloudWatch configuration."""
        return self.get("cloudwatch", {"enabled": False})

    def get_openai_config(self) -> dict[str, Any]:
        """Get OpenAI configuration."""
        return self.get("openai", {})

    def get_ticketing_config(self) -> dict[str, Any]:
        """Get ticketing configuration."""
        return self.get("ticketing", {"provider": "file", "ticket_dir": "tickets"})

    def get_knowledge_base_config(self) -> dict[str, Any]:
        """Get knowledge base configuration."""
        return self.get("knowledge_base", {"directory": "knowledgeBase"})

    def get_agent_config(self) -> dict[str, Any]:
        """Get agent configuration."""
        return self.get("agent", {"monitor_interval": 5.0, "max_batch_size": 10})
