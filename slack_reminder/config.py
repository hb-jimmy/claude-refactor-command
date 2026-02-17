"""Configuration for slack-remind.

State is stored in ~/.slack-reminder.yaml. Slack credentials are read
from ~/.slack-config.yaml (same file used by slack-update).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


REMINDER_CONFIG_PATH = Path.home() / ".slack-reminder.yaml"
SLACK_CONFIG_PATH = Path.home() / ".slack-config.yaml"


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


@dataclass
class ProcessedEntry:
    """A previously-processed file+date combination."""
    file: str
    date: str


@dataclass
class ReminderConfig:
    """Reminder configuration and state."""
    processed_files: List[ProcessedEntry] = field(default_factory=list)


def load_reminder_config() -> ReminderConfig:
    """Load reminder config from ~/.slack-reminder.yaml.

    Returns:
        ReminderConfig (with defaults if file is missing).
    """
    if not REMINDER_CONFIG_PATH.exists():
        return ReminderConfig()

    try:
        with open(REMINDER_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read {REMINDER_CONFIG_PATH}: {e}")

    if not data or not isinstance(data, dict):
        return ReminderConfig()

    processed = []
    for entry in data.get("processed_files", []):
        if isinstance(entry, dict) and "file" in entry and "date" in entry:
            processed.append(ProcessedEntry(file=entry["file"], date=entry["date"]))

    return ReminderConfig(processed_files=processed)


def save_reminder_config(config: ReminderConfig) -> None:
    """Write reminder config to ~/.slack-reminder.yaml."""
    data = {}
    if config.processed_files:
        data["processed_files"] = [
            {"file": e.file, "date": e.date} for e in config.processed_files
        ]

    try:
        with open(REMINDER_CONFIG_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    except OSError as e:
        raise ConfigError(f"Failed to write {REMINDER_CONFIG_PATH}: {e}")


def load_slack_token() -> str:
    """Load Slack user token from ~/.slack-config.yaml.

    Returns:
        The user_token string.

    Raises:
        ConfigError: If the token cannot be found.
    """
    if not SLACK_CONFIG_PATH.exists():
        raise ConfigError(
            f"Slack config not found at {SLACK_CONFIG_PATH}.\n"
            "Run 'slack-update --auth' to authenticate."
        )

    try:
        with open(SLACK_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read {SLACK_CONFIG_PATH}: {e}")

    if not data or not isinstance(data, dict):
        raise ConfigError(f"Invalid config format in {SLACK_CONFIG_PATH}")

    token = data.get("user_token")
    if not token:
        raise ConfigError(
            f"No user_token in {SLACK_CONFIG_PATH}.\n"
            "Run 'slack-update --auth' to authenticate."
        )

    return str(token)
