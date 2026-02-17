"""
Configuration for summary-publish.

Shares configuration with fathom-tool from ~/.one-on-one/config.yaml.
"""

from pathlib import Path

from fathom_tool.config import load_config, ConfigError, MeetingConfig


def get_repo_path(person: str) -> Path:
    """Look up the repo path for a person from the shared config.

    Args:
        person: Name of the person (case-insensitive).

    Returns:
        Resolved Path to the person's repo.

    Raises:
        ConfigError: If person not found or repo not configured.
    """
    config = load_config()
    person_lower = person.lower()

    for meeting in config.meetings:
        if meeting.person.lower() == person_lower:
            if not meeting.repo:
                raise ConfigError(
                    f"No repo configured for '{meeting.person}' in "
                    "~/.one-on-one/config.yaml.\n"
                    "Add a 'repo' field to their meeting entry."
                )
            return Path(meeting.repo).expanduser()

    available = ", ".join(m.person for m in config.meetings)
    raise ConfigError(
        f"Unknown person: '{person}'\n"
        f"Available: {available}"
    )
