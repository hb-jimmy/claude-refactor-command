"""Configuration for run-query.

Server connection details are read from ~/.azuresql.yaml. The database name
is supplied per-invocation via --db, so the config only needs the server host
(and optional overrides).

Example ~/.azuresql.yaml:

    server: ha-prod1-azsqldb.database.windows.net
    username: you@thehelperbees.com
    # Optional:
    port: 1433
    tenant_id: 00000000-0000-0000-0000-000000000000  # AAD tenant (else "organizations")
    jdbc_jars_dir: ~/jdbc-drivers   # dir with mssql-jdbc + MSAL4J jars
                                    # (auto-discovers DataGrip's drivers if omitted)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


CONFIG_PATH = Path.home() / ".azuresql.yaml"

DEFAULT_PORT = 1433


class ConfigError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


@dataclass
class SqlConfig:
    """Azure SQL connection configuration."""
    server: str
    username: str
    port: int = DEFAULT_PORT
    jdbc_jars_dir: Optional[str] = None
    tenant_id: Optional[str] = None


def load_config() -> SqlConfig:
    """Load Azure SQL config from ~/.azuresql.yaml.

    Returns:
        SqlConfig with the server host, username, and optional overrides.

    Raises:
        ConfigError: If the file is missing or required fields are absent.
    """
    if not CONFIG_PATH.exists():
        raise ConfigError(
            f"Config not found at {CONFIG_PATH}.\n"
            "Create it with at least the server host and your username:\n\n"
            "server: ha-prod1-azsqldb.database.windows.net\n"
            "username: you@thehelperbees.com\n"
        )

    try:
        with open(CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read {CONFIG_PATH}: {e}")

    if not data or not isinstance(data, dict):
        raise ConfigError(f"Invalid config format in {CONFIG_PATH}")

    server = data.get("server")
    if not server:
        raise ConfigError(f"No 'server' configured in {CONFIG_PATH}")

    username = data.get("username")
    if not username:
        raise ConfigError(
            f"No 'username' configured in {CONFIG_PATH}.\n"
            "Add your Azure AD sign-in address, e.g.:\n"
            "username: you@thehelperbees.com"
        )

    return SqlConfig(
        server=str(server),
        username=str(username),
        port=int(data.get("port", DEFAULT_PORT)),
        jdbc_jars_dir=data.get("jdbc_jars_dir"),
        tenant_id=data.get("tenant_id"),
    )
