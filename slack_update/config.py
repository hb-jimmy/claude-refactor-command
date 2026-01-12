"""Configuration and credential management for Slack CLI tools.

This module provides auto-discovery of Slack credentials from multiple sources:
1. Environment variables (highest priority)
2. Configuration file (~/.slack-config.yaml)

Credentials required:
- For OAuth flow: SLACK_CLIENT_ID, SLACK_CLIENT_SECRET
- For API calls: SLACK_USER_TOKEN

The OAuth flow is a one-time operation that obtains and stores the user token.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
import yaml


# Configuration constants
CONFIG_FILE_PATH = Path.home() / ".slack-config.yaml"
ENV_SLACK_USER_TOKEN = "SLACK_USER_TOKEN"
ENV_SLACK_CLIENT_ID = "SLACK_CLIENT_ID"
ENV_SLACK_CLIENT_SECRET = "SLACK_CLIENT_SECRET"

# OAuth settings
OAUTH_REDIRECT_PORT = 8765
OAUTH_REDIRECT_PATH = "/oauth/callback"
OAUTH_SCOPES = [
    "chat:write",       # Post messages
    "channels:read",    # List public channels
    "groups:read",      # List private channels
    "users:read",       # List users for mention resolution
    "users:read.email", # Access user emails
]


class ConfigError(Exception):
    """Raised when configuration or credentials cannot be loaded."""
    pass


@dataclass
class SlackCredentials:
    """Slack API credentials."""
    user_token: str


@dataclass
class OAuthConfig:
    """OAuth configuration for authentication flow."""
    client_id: str
    client_secret: str


def _load_token_from_env() -> Optional[SlackCredentials]:
    """Attempt to load user token from environment variables.

    Returns:
        SlackCredentials if token found, None otherwise.
    """
    token = os.environ.get(ENV_SLACK_USER_TOKEN)
    if token:
        return SlackCredentials(user_token=token)
    return None


def _load_token_from_config_file() -> Optional[SlackCredentials]:
    """Attempt to load user token from config file.

    Returns:
        SlackCredentials if token found in file, None otherwise.
    """
    if not CONFIG_FILE_PATH.exists():
        return None

    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            config = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read config file: {e}")

    if not config:
        return None

    token = config.get("user_token")
    if token:
        return SlackCredentials(user_token=token)

    return None


def _load_oauth_from_env() -> Optional[OAuthConfig]:
    """Attempt to load OAuth credentials from environment variables.

    Returns:
        OAuthConfig if both client_id and client_secret found, None otherwise.
    """
    client_id = os.environ.get(ENV_SLACK_CLIENT_ID)
    client_secret = os.environ.get(ENV_SLACK_CLIENT_SECRET)

    if client_id and client_secret:
        return OAuthConfig(client_id=client_id, client_secret=client_secret)
    return None


def _load_oauth_from_config_file() -> Optional[OAuthConfig]:
    """Attempt to load OAuth credentials from config file.

    Returns:
        OAuthConfig if both client_id and client_secret found, None otherwise.
    """
    if not CONFIG_FILE_PATH.exists():
        return None

    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            config = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read config file: {e}")

    if not config:
        return None

    client_id = config.get("client_id")
    client_secret = config.get("client_secret")

    if client_id and client_secret:
        return OAuthConfig(client_id=client_id, client_secret=client_secret)

    return None


def load_credentials() -> SlackCredentials:
    """Load Slack user token from environment or config file.

    Tries sources in order:
    1. Environment variable SLACK_USER_TOKEN
    2. Config file ~/.slack-config.yaml (user_token field)

    Returns:
        SlackCredentials with the user token.

    Raises:
        ConfigError: If no valid credentials found.
    """
    credentials = _load_token_from_env()
    if credentials:
        return credentials

    credentials = _load_token_from_config_file()
    if credentials:
        return credentials

    raise ConfigError(
        "Slack credentials not found. Either:\n"
        f"  1. Set environment variable {ENV_SLACK_USER_TOKEN}\n"
        f"  2. Create {CONFIG_FILE_PATH} with user_token field\n"
        f"  3. Run 'slack-update --auth' to authenticate via OAuth"
    )


def load_oauth_config() -> OAuthConfig:
    """Load OAuth configuration for authentication flow.

    Tries sources in order:
    1. Environment variables SLACK_CLIENT_ID and SLACK_CLIENT_SECRET
    2. Config file ~/.slack-config.yaml (client_id and client_secret fields)

    Returns:
        OAuthConfig with client credentials.

    Raises:
        ConfigError: If OAuth credentials not found.
    """
    config = _load_oauth_from_env()
    if config:
        return config

    config = _load_oauth_from_config_file()
    if config:
        return config

    raise ConfigError(
        "Slack OAuth credentials not found. Either:\n"
        f"  1. Set environment variables {ENV_SLACK_CLIENT_ID} and {ENV_SLACK_CLIENT_SECRET}\n"
        f"  2. Add client_id and client_secret to {CONFIG_FILE_PATH}\n\n"
        "To create a Slack App:\n"
        "  1. Go to https://api.slack.com/apps\n"
        "  2. Click 'Create New App' > 'From scratch'\n"
        "  3. Add OAuth scopes under 'OAuth & Permissions':\n"
        f"     {', '.join(OAUTH_SCOPES)}\n"
        "  4. Add redirect URL: http://localhost:8765/oauth/callback\n"
        "  5. Copy Client ID and Client Secret from 'Basic Information'"
    )


def save_token(token: str) -> None:
    """Save user token to config file.

    Preserves existing config values (like client_id/client_secret).

    Args:
        token: The Slack user token to save.

    Raises:
        ConfigError: If unable to write config file.
    """
    config = {}

    # Load existing config if present
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                existing = yaml.safe_load(f)
                if existing:
                    config = existing
        except (yaml.YAMLError, OSError):
            pass  # Start fresh if file is corrupted

    config["user_token"] = token

    try:
        with open(CONFIG_FILE_PATH, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    except OSError as e:
        raise ConfigError(f"Failed to save token to {CONFIG_FILE_PATH}: {e}")
