"""Configuration for slack-postmortem tool.

Loads Slack token from env or ~/.slack-config.yaml (reuses slack_update pattern)
and channel list from ~/.slack-postmortem.yaml.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import os
import yaml


CONFIG_FILE_PATH = Path.home() / ".slack-postmortem.yaml"
SLACK_CONFIG_FILE_PATH = Path.home() / ".slack-config.yaml"
ENV_SLACK_USER_TOKEN = "SLACK_USER_TOKEN"


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


@dataclass
class ChannelEntry:
    """A channel from the postmortem config."""
    name: str
    id: Optional[str] = None


@dataclass
class PostmortemConfig:
    """Postmortem tool configuration."""
    token: str
    channels: List[ChannelEntry]


def _load_token_from_env() -> Optional[str]:
    """Load token from environment variable."""
    return os.environ.get(ENV_SLACK_USER_TOKEN)


def _load_token_from_config_file() -> Optional[str]:
    """Load token from ~/.slack-config.yaml."""
    if not SLACK_CONFIG_FILE_PATH.exists():
        return None

    try:
        with open(SLACK_CONFIG_FILE_PATH, "r") as f:
            config = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read {SLACK_CONFIG_FILE_PATH}: {e}")

    if not config:
        return None

    return config.get("user_token")


def _load_token() -> str:
    """Load Slack user token from env or config file.

    Raises:
        ConfigError: If no token found.
    """
    token = _load_token_from_env()
    if token:
        return token

    token = _load_token_from_config_file()
    if token:
        return token

    raise ConfigError(
        "Slack credentials not found. Either:\n"
        f"  1. Set environment variable {ENV_SLACK_USER_TOKEN}\n"
        f"  2. Create {SLACK_CONFIG_FILE_PATH} with user_token field\n"
        f"  3. Run 'slack-update --auth' to authenticate via OAuth"
    )


def _load_channels() -> List[ChannelEntry]:
    """Load channel list from ~/.slack-postmortem.yaml.

    Raises:
        ConfigError: If config file missing or invalid.
    """
    if not CONFIG_FILE_PATH.exists():
        raise ConfigError(
            f"Config file not found: {CONFIG_FILE_PATH}\n"
            f"Create it with:\n\n"
            f"  channels:\n"
            f'    - name: "incident-2026-02-01"\n'
            f'    - name: "incident-2026-01-15"'
        )

    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            config = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read {CONFIG_FILE_PATH}: {e}")

    if not config or "channels" not in config:
        raise ConfigError(
            f"No 'channels' key found in {CONFIG_FILE_PATH}\n"
            f"Expected format:\n\n"
            f"  channels:\n"
            f'    - name: "incident-2026-02-01"'
        )

    channels = []
    for entry in config["channels"]:
        if isinstance(entry, str):
            channels.append(ChannelEntry(name=entry))
        elif isinstance(entry, dict):
            name = entry.get("name")
            channel_id = entry.get("id")
            if not name and not channel_id:
                raise ConfigError(
                    f"Channel entry must have 'name' or 'id': {entry}"
                )
            channels.append(ChannelEntry(name=name or channel_id, id=channel_id))
        else:
            raise ConfigError(f"Invalid channel entry: {entry}")

    if not channels:
        raise ConfigError(f"No channels configured in {CONFIG_FILE_PATH}")

    return channels


def load_config() -> PostmortemConfig:
    """Load full postmortem configuration.

    Returns:
        PostmortemConfig with token and channel list.

    Raises:
        ConfigError: If configuration is incomplete.
    """
    token = _load_token()
    channels = _load_channels()
    return PostmortemConfig(token=token, channels=channels)
