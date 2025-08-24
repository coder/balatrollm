"""Data collection and run directory management for BalatroLLM."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from openai.types.chat import ChatCompletion


def generate_run_directory(
    deck: str,
    stake: int,
    seed: str,
    model: str,
    strategy: str,
    project_version: str,
    challenge: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> Path:
    """Generate structured directory path for the run."""
    base_dir = base_dir or Path.cwd() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Clean names for filesystem safety
    deck_clean = _clean_name(deck)
    model_clean = _clean_name(model, "/:", "-")
    challenge_clean = _clean_name(challenge) if challenge else None

    # Build run directory name
    parts = [timestamp, deck_clean, f"s{stake}"]
    if challenge_clean:
        parts.append(challenge_clean)
    parts.append(seed)

    run_dir_name = "_".join(parts)
    return base_dir / f"v{project_version}" / model_clean / strategy / run_dir_name


def _clean_name(name: str, chars_to_replace: str = " -", replacement: str = "") -> str:
    """Clean a name for filesystem safety."""
    for char in chars_to_replace:
        name = name.replace(char, replacement)
    return name


@dataclass
class RunDataCollector:
    """Collects run data in structured directory format."""

    run_dir: Path
    run_config: Dict[str, Any] = field(default_factory=dict)
    request_count: int = 0

    def __post_init__(self):
        """Create directory structure and write config."""
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Write config immediately if available
        if self.run_config:
            self._write_config()

    def _write_config(self) -> None:
        """Write the run configuration to config.json."""
        config_path = self.run_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(self.run_config, f, indent=2)

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update and write the run configuration."""
        self.run_config.update(config)
        self._write_config()

    def write_gamestate(self, entry: Dict[str, Any]) -> None:
        """Write a game state entry to gamestates.jsonl."""
        self._write_jsonl("gamestates.jsonl", entry)

    def write_request(self, request_data: Dict[str, Any]) -> str:
        """Write an LLM request to requests.jsonl in OpenAI batch format."""
        self.request_count += 1
        request_id = f"req_{self.request_count:03d}"

        batch_entry = {
            "custom_id": request_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": request_data,
        }

        self._write_jsonl("requests.jsonl", batch_entry)
        return request_id

    def write_response(
        self,
        request_id: str,
        response: Optional[ChatCompletion] = None,
        error: Optional[Exception] = None,
        status_code: int = 200,
    ) -> None:
        """Write an LLM response to responses.jsonl in OpenAI batch format."""
        if response:
            batch_response = self._create_success_response(request_id, response)
        elif error:
            batch_response = self._create_error_response(request_id, error, status_code)
        else:
            raise ValueError("Either response or error must be provided")

        self._write_jsonl("responses.jsonl", batch_response)

    def _create_success_response(
        self, request_id: str, response: ChatCompletion
    ) -> dict:
        """Create success response entry."""
        return {
            "id": request_id,
            "custom_id": request_id,
            "response": {
                "status_code": 200,
                "request_id": response.id,
                "body": response.model_dump(),
            },
            "error": None,
        }

    def _create_error_response(
        self, request_id: str, error: Exception, status_code: int
    ) -> dict:
        """Create error response entry."""
        return {
            "id": request_id,
            "custom_id": request_id,
            "response": {
                "status_code": status_code,
                "request_id": request_id,
                "body": {},
            },
            "error": {"code": type(error).__name__, "message": str(error)},
        }

    def _write_jsonl(self, filename: str, data: dict) -> None:
        """Write data to a JSONL file."""
        file_path = self.run_dir / filename
        with open(file_path, "a") as f:
            f.write(json.dumps(data) + "\n")
