"""
Configuration and credential discovery for jira-update.

Credentials are discovered in the following order:
1. Environment variables (JIRA_EMAIL, JIRA_API_TOKEN)
2. Config file (~/.jira-config.yaml)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


# Jira instance URL
JIRA_BASE_URL = "https://thehelperbees.atlassian.net"

# Config file location
CONFIG_FILE_PATH = Path.home() / ".jira-config.yaml"

# Environment variable names
ENV_JIRA_EMAIL = "JIRA_EMAIL"
ENV_JIRA_API_TOKEN = "JIRA_API_TOKEN"


@dataclass
class JiraCredentials:
    """Jira authentication credentials."""
    email: str
    api_token: str


class ConfigError(Exception):
    """Raised when configuration or credentials cannot be loaded."""
    pass


def _load_from_env() -> Optional[JiraCredentials]:
    """
    Attempt to load credentials from environment variables.

    Returns:
        JiraCredentials if both JIRA_EMAIL and JIRA_API_TOKEN are set,
        None otherwise.
    """
    email = os.environ.get(ENV_JIRA_EMAIL)
    api_token = os.environ.get(ENV_JIRA_API_TOKEN)

    if email and api_token:
        return JiraCredentials(email=email, api_token=api_token)

    return None


def _load_from_config_file() -> Optional[JiraCredentials]:
    """
    Attempt to load credentials from the YAML config file.

    Expected format:
        email: your.email@example.com
        api_token: your-api-token-here

    Returns:
        JiraCredentials if config file exists and contains valid credentials,
        None otherwise.
    """
    if not CONFIG_FILE_PATH.exists():
        return None

    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            return None

        email = config.get("email")
        api_token = config.get("api_token")

        if email and api_token:
            return JiraCredentials(email=str(email), api_token=str(api_token))

        return None
    except (yaml.YAMLError, IOError):
        return None


def load_credentials() -> JiraCredentials:
    """
    Load Jira credentials using auto-discovery.

    Discovery order:
    1. Environment variables (JIRA_EMAIL, JIRA_API_TOKEN)
    2. Config file (~/.jira-config.yaml)

    Returns:
        JiraCredentials with email and api_token.

    Raises:
        ConfigError: If credentials cannot be found in any location.
    """
    # Try environment variables first
    credentials = _load_from_env()
    if credentials:
        return credentials

    # Try config file
    credentials = _load_from_config_file()
    if credentials:
        return credentials

    # No credentials found
    raise ConfigError(
        "Jira credentials not found. Please configure credentials using one of:\n"
        f"  1. Environment variables: {ENV_JIRA_EMAIL} and {ENV_JIRA_API_TOKEN}\n"
        f"  2. Config file: {CONFIG_FILE_PATH}\n"
        "\n"
        "Config file format (YAML):\n"
        "  email: your.email@example.com\n"
        "  api_token: your-api-token-here\n"
        "\n"
        "To generate an API token, visit:\n"
        "  https://id.atlassian.com/manage-profile/security/api-tokens"
    )
