"""Configuration for slack-history.

Channel list is stored in ~/.slack-scan.yaml. Slack credentials are read
from ~/.slack-config.yaml (same file used by slack-update).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


SCAN_CONFIG_PATH = Path.home() / ".slack-scan.yaml"
SLACK_CONFIG_PATH = Path.home() / ".slack-config.yaml"


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


@dataclass
class ChannelEntry:
    """A channel to scan."""
    id: str
    name: str = ""


@dataclass
class ScanConfig:
    """Scan configuration."""
    channels: List[ChannelEntry] = field(default_factory=list)


def load_scan_config() -> ScanConfig:
    """Load scan config from ~/.slack-scan.yaml.

    Returns:
        ScanConfig with channel list.

    Raises:
        ConfigError: If the file is missing or invalid.
    """
    if not SCAN_CONFIG_PATH.exists():
        raise ConfigError(
            f"Scan config not found at {SCAN_CONFIG_PATH}.\n"
            "Create it with a list of channels to scan:\n\n"
            "channels:\n"
            '  - id: "C01234567"\n'
            '    name: "general"\n'
        )

    try:
        with open(SCAN_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read {SCAN_CONFIG_PATH}: {e}")

    if not data or not isinstance(data, dict):
        raise ConfigError(f"Invalid config format in {SCAN_CONFIG_PATH}")

    channels = []
    for entry in data.get("channels", []):
        if isinstance(entry, dict) and "id" in entry:
            channels.append(ChannelEntry(
                id=entry["id"],
                name=entry.get("name", ""),
            ))

    if not channels:
        raise ConfigError(f"No channels configured in {SCAN_CONFIG_PATH}")

    return ScanConfig(channels=channels)


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
