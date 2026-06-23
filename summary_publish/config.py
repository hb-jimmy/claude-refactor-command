"""
Configuration for summary-publish.

Shares configuration with fathom-tool via a config.yaml file.
"""

from pathlib import Path
from typing import Optional

from fathom_tool.config import load_config, ConfigError, MeetingConfig


def get_repo_path(name: str, config_path: Optional[Path] = None) -> Path:
    """Look up the repo path for a name from the shared config.

    Args:
        name: Name of the meeting/person (case-insensitive).
        config_path: Optional path to config file.

    Returns:
        Resolved Path to the repo.

    Raises:
        ConfigError: If name not found or repo not configured.
    """
    config = load_config(config_path=config_path)
    name_lower = name.lower()

    for meeting in config.meetings:
        if meeting.name.lower() == name_lower:
            if not meeting.repo:
                raise ConfigError(
                    f"No repo configured for '{meeting.name}' in config.\n"
                    "Add a 'repo' field to their meeting entry."
                )
            return Path(meeting.repo).expanduser()

    available = ", ".join(m.name for m in config.meetings)
    raise ConfigError(
        f"Unknown name: '{name}'\n"
        f"Available: {available}"
    )


def get_meeting(name: str, config_path: Optional[Path] = None) -> MeetingConfig:
    """Look up the full meeting config for a name.

    Args:
        name: Name of the meeting/person (case-insensitive).
        config_path: Optional path to config file.

    Returns:
        The matching MeetingConfig.

    Raises:
        ConfigError: If name not found.
    """
    config = load_config(config_path=config_path)
    name_lower = name.lower()

    for meeting in config.meetings:
        if meeting.name.lower() == name_lower:
            return meeting

    available = ", ".join(m.name for m in config.meetings)
    raise ConfigError(
        f"Unknown name: '{name}'\n"
        f"Available: {available}"
    )
