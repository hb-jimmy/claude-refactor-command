"""
Configuration and credential discovery for fathom-tool.

Credentials and meeting configuration are stored in a config.yaml file.
Default location: ~/.one-on-one/config.yaml.
Transcripts are stored in <config_dir>/transcripts/<name>/.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


DEFAULT_CONFIG_DIR = Path.home() / ".one-on-one"
DEFAULT_CONFIG_FILE_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


@dataclass
class MeetingConfig:
    """A configured meeting to track, identified by Zoom meeting title."""
    title: str
    name: str
    repo: Optional[str] = None
    file: Optional[str] = None


@dataclass
class FathomConfig:
    """Full configuration."""
    api_key: str
    meetings: List[MeetingConfig] = field(default_factory=list)
    config_dir: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR)


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


def sanitize_name(name: str) -> str:
    """Convert a name to a filesystem-safe directory name."""
    safe = re.sub(r'[^\w\s-]', '', name).strip()
    safe = re.sub(r'[\s]+', '_', safe)
    return safe.lower()


# Backward-compatible alias
sanitize_person = sanitize_name


def transcript_dir_for_meeting(meeting: MeetingConfig, config_dir: Optional[Path] = None) -> Path:
    """Get the transcript storage directory for a meeting."""
    base = config_dir or DEFAULT_CONFIG_DIR
    return base / "transcripts" / sanitize_name(meeting.name)


def load_config(config_path: Optional[Path] = None) -> FathomConfig:
    """
    Load configuration from a YAML config file.

    Args:
        config_path: Path to config file. Defaults to ~/.one-on-one/config.yaml.

    Expected format:
        fathom_api_key: "your-fathom-api-key"

        meetings:
          - title: "Alice / You 1:1"
            name: "Alice"
            repo: ~/one-on-ones/alice-shared
          - title: "Bob / You 1:1"
            name: "Bob"
            repo: ~/one-on-ones/bob-shared
            file: bob.md

    Returns:
        FathomConfig with API key and meeting list.

    Raises:
        ConfigError: If config file is missing or invalid.
    """
    config_file = Path(config_path) if config_path else DEFAULT_CONFIG_FILE_PATH

    if not config_file.exists():
        raise ConfigError(
            f"Config file not found: {config_file}\n"
            "\n"
            "Create it with the following format:\n"
            "\n"
            '  fathom_api_key: "your-fathom-api-key"\n'
            "\n"
            "  meetings:\n"
            '    - title: "Alice / You 1:1"\n'
            '      name: "Alice"\n'
            '      repo: ~/one-on-ones/alice-shared\n'
            '    - title: "Bob / You 1:1"\n'
            '      name: "Bob"\n'
            '      repo: ~/one-on-ones/bob-shared\n'
            "\n"
            "To create a Fathom API key, go to Fathom User Settings > API Access.\n"
        )

    try:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        raise ConfigError(f"Failed to read config file: {e}")

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid config file format: {config_file}")

    api_key = data.get("fathom_api_key")
    if not api_key:
        raise ConfigError(
            "Missing fathom_api_key in config file. Required field:\n"
            "  fathom_api_key"
        )

    config_dir = config_file.parent

    meetings = []
    for m in data.get("meetings", []):
        if not isinstance(m, dict):
            continue
        title = m.get("title")
        # Accept both "name" and "person" keys (prefer "name")
        name = m.get("name") or m.get("person")
        repo = m.get("repo")
        file_val = m.get("file")
        if title and name:
            meetings.append(MeetingConfig(
                title=str(title),
                name=str(name),
                repo=str(repo) if repo else None,
                file=str(file_val) if file_val else None,
            ))

    return FathomConfig(
        api_key=str(api_key),
        meetings=meetings,
        config_dir=config_dir,
    )
