"""
Configuration and credential discovery for fathom-tool.

Credentials and meeting configuration are stored in ~/.fathom-tool/config.yaml.
Transcripts are stored in ~/.fathom-tool/transcripts/<label>/.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


CONFIG_DIR = Path.home() / ".fathom-tool"
CONFIG_FILE_PATH = CONFIG_DIR / "config.yaml"
TRANSCRIPTS_DIR = CONFIG_DIR / "transcripts"


@dataclass
class MeetingConfig:
    """A configured meeting to track, identified by Zoom meeting title."""
    title: str
    label: str


@dataclass
class FathomConfig:
    """Full fathom-tool configuration."""
    api_key: str
    meetings: List[MeetingConfig] = field(default_factory=list)


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


def sanitize_label(label: str) -> str:
    """Convert a meeting label to a filesystem-safe directory name."""
    safe = re.sub(r'[^\w\s-]', '', label).strip()
    safe = re.sub(r'[\s]+', '_', safe)
    return safe.lower()


def transcript_dir_for_meeting(meeting: MeetingConfig) -> Path:
    """Get the transcript storage directory for a meeting."""
    return TRANSCRIPTS_DIR / sanitize_label(meeting.label)


def load_config() -> FathomConfig:
    """
    Load fathom-tool configuration from ~/.fathom-tool/config.yaml.

    Expected format:
        api_key: "your-fathom-api-key"

        meetings:
          - title: "Alice / You 1:1"
            label: "Alice - 1:1"
          - title: "Bob / You 1:1"
            label: "Bob - 1:1"

    Returns:
        FathomConfig with API key and meeting list.

    Raises:
        ConfigError: If config file is missing or invalid.
    """
    if not CONFIG_FILE_PATH.exists():
        raise ConfigError(
            f"Config file not found: {CONFIG_FILE_PATH}\n"
            "\n"
            "Create it with the following format:\n"
            "\n"
            '  api_key: "your-fathom-api-key"\n'
            "\n"
            "  meetings:\n"
            '    - title: "Alice / You 1:1"\n'
            '      label: "Alice - 1:1"\n'
            '    - title: "Bob / You 1:1"\n'
            '      label: "Bob - 1:1"\n'
            "\n"
            "To create an API key, go to Fathom User Settings > API Access.\n"
        )

    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        raise ConfigError(f"Failed to read config file: {e}")

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid config file format: {CONFIG_FILE_PATH}")

    api_key = data.get("api_key")
    if not api_key:
        raise ConfigError(
            "Missing api_key in config file. Required field:\n"
            "  api_key"
        )

    meetings = []
    for m in data.get("meetings", []):
        if not isinstance(m, dict):
            continue
        title = m.get("title")
        label = m.get("label")
        if title and label:
            meetings.append(MeetingConfig(title=str(title), label=str(label)))

    return FathomConfig(api_key=str(api_key), meetings=meetings)
