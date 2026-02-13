"""
Configuration and credential discovery for fathom-tool.

Credentials and meeting configuration are stored in ~/.one-on-one/config.yaml.
Transcripts are stored in ~/.one-on-one/transcripts/<person>/.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


CONFIG_DIR = Path.home() / ".one-on-one"
CONFIG_FILE_PATH = CONFIG_DIR / "config.yaml"
TRANSCRIPTS_DIR = CONFIG_DIR / "transcripts"


@dataclass
class MeetingConfig:
    """A configured meeting to track, identified by Zoom meeting title."""
    title: str
    person: str
    repo: Optional[str] = None


@dataclass
class FathomConfig:
    """Full configuration."""
    api_key: str
    meetings: List[MeetingConfig] = field(default_factory=list)


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


def sanitize_person(person: str) -> str:
    """Convert a person name to a filesystem-safe directory name."""
    safe = re.sub(r'[^\w\s-]', '', person).strip()
    safe = re.sub(r'[\s]+', '_', safe)
    return safe.lower()


def transcript_dir_for_meeting(meeting: MeetingConfig) -> Path:
    """Get the transcript storage directory for a meeting."""
    return TRANSCRIPTS_DIR / sanitize_person(meeting.person)


def load_config() -> FathomConfig:
    """
    Load configuration from ~/.one-on-one/config.yaml.

    Expected format:
        fathom_api_key: "your-fathom-api-key"

        meetings:
          - title: "Alice / You 1:1"
            person: "Alice"
            repo: ~/one-on-ones/alice-shared
          - title: "Bob / You 1:1"
            person: "Bob"
            repo: ~/one-on-ones/bob-shared

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
            '  fathom_api_key: "your-fathom-api-key"\n'
            "\n"
            "  meetings:\n"
            '    - title: "Alice / You 1:1"\n'
            '      person: "Alice"\n'
            '      repo: ~/one-on-ones/alice-shared\n'
            '    - title: "Bob / You 1:1"\n'
            '      person: "Bob"\n'
            '      repo: ~/one-on-ones/bob-shared\n'
            "\n"
            "To create a Fathom API key, go to Fathom User Settings > API Access.\n"
        )

    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        raise ConfigError(f"Failed to read config file: {e}")

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid config file format: {CONFIG_FILE_PATH}")

    api_key = data.get("fathom_api_key")
    if not api_key:
        raise ConfigError(
            "Missing fathom_api_key in config file. Required field:\n"
            "  fathom_api_key"
        )

    meetings = []
    for m in data.get("meetings", []):
        if not isinstance(m, dict):
            continue
        title = m.get("title")
        person = m.get("person")
        repo = m.get("repo")
        if title and person:
            meetings.append(MeetingConfig(
                title=str(title),
                person=str(person),
                repo=str(repo) if repo else None,
            ))

    return FathomConfig(api_key=str(api_key), meetings=meetings)
