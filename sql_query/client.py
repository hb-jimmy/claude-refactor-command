"""Read-only Azure SQL query execution via the Microsoft JDBC driver.

Authentication mirrors DataGrip's "ms-azure-active-directory-interactive":
the Microsoft JDBC driver (mssql-jdbc) is launched in a JVM with
authentication=ActiveDirectoryInteractive, which opens the system browser for
Azure AD sign-in. This is what the target server accepts; a manually-acquired
ODBC access token is rejected with "server is not configured to accept this
token".

The query is executed by a small Java helper (RunQuery.java) that writes the
result set straight to the output CSV. The Python process never holds the
result rows, so query output (which may contain PII) never enters this agent's
memory.

Read-only is enforced three ways:
  1. The query string is validated to be a single SELECT/WITH statement with
     no write keywords (see validate_read_only).
  2. The JDBC URL sets applicationIntent=ReadOnly.
  3. The connection calls setReadOnly(true).
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import List

from .config import SqlConfig

# Statements/keywords that indicate a write or otherwise non-read-only query.
# Matched as whole words, case-insensitively.
_FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "merge", "upsert",
    "drop", "create", "alter", "truncate", "rename",
    "grant", "revoke", "deny",
    "exec", "execute", "sp_", "xp_",
    "into",          # blocks SELECT ... INTO (which creates a table)
    "backup", "restore", "bulk", "shutdown", "kill",
    "commit", "rollback", "save", "begin",
]

_FORBIDDEN_RE = re.compile(
    r"(?<![\w@#])(" + "|".join(re.escape(k) for k in _FORBIDDEN_KEYWORDS) + r")(?![\w])",
    re.IGNORECASE,
)

# Java helper that does the actual JDBC work, shipped alongside this module.
_RUN_QUERY_JAVA = Path(__file__).resolve().parent / "RunQuery.java"


class QueryError(Exception):
    """Raised when a query is rejected or fails to execute."""
    pass


def _strip_sql_comments(sql: str) -> str:
    """Remove -- line comments and /* */ block comments for validation."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def validate_read_only(query: str) -> str:
    """Validate that the query is a single read-only SELECT/WITH statement.

    Args:
        query: The raw SQL query string.

    Returns:
        The trimmed query.

    Raises:
        QueryError: If the query is empty, contains multiple statements, does
            not begin with SELECT or WITH, or contains write keywords.
    """
    if not query or not query.strip():
        raise QueryError("Query is empty.")

    trimmed = query.strip()

    # Validate against a comment-stripped copy so comments can't smuggle in
    # forbidden keywords or hide the leading statement.
    stripped = _strip_sql_comments(trimmed).strip()
    if not stripped:
        raise QueryError("Query contains no executable SQL.")

    # Reject multiple statements. A single trailing semicolon is allowed.
    inner = stripped[:-1] if stripped.endswith(";") else stripped
    if ";" in inner:
        raise QueryError(
            "Only a single statement is allowed (found ';' separating statements)."
        )

    first_word = re.match(r"\s*([a-zA-Z]+)", stripped)
    if not first_word or first_word.group(1).lower() not in ("select", "with"):
        raise QueryError(
            "Read-only mode: query must begin with SELECT or WITH "
            f"(got '{(first_word.group(1) if first_word else '')}')."
        )

    match = _FORBIDDEN_RE.search(stripped)
    if match:
        raise QueryError(
            f"Read-only mode: query contains forbidden keyword '{match.group(1)}'."
        )

    return trimmed


def _find_java() -> str:
    """Locate the `java` executable.

    Raises:
        QueryError: If no JRE/JDK can be found.
    """
    java = shutil.which("java")
    if java:
        return java

    # Fall back to the macOS java_home shim.
    try:
        home = subprocess.run(
            ["/usr/libexec/java_home"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        candidate = Path(home) / "bin" / "java"
        if candidate.exists():
            return str(candidate)
    except (OSError, subprocess.CalledProcessError):
        pass

    raise QueryError(
        "No Java runtime found. Install one (e.g. `brew install openjdk`) "
        "or set JAVA_HOME."
    )


def _discover_jars(config: SqlConfig) -> List[Path]:
    """Find the mssql-jdbc + MSAL4J jars to put on the classpath.

    Uses config.jdbc_jars_dir if set, otherwise auto-discovers the driver jars
    DataGrip has already downloaded.

    Raises:
        QueryError: If no usable driver jars are found.
    """
    jars: List[Path] = []

    if config.jdbc_jars_dir:
        base = Path(config.jdbc_jars_dir).expanduser()
        if not base.is_dir():
            raise QueryError(f"jdbc_jars_dir does not exist: {base}")
        jars = list(base.rglob("*.jar"))
    else:
        # Auto-discover DataGrip's downloaded JDBC drivers (macOS path).
        jetbrains = Path.home() / "Library" / "Application Support" / "JetBrains"
        for dg in sorted(jetbrains.glob("DataGrip*"), reverse=True):
            drivers = dg / "jdbc-drivers"
            if drivers.is_dir():
                found = list(drivers.rglob("*.jar"))
                if any("mssql-jdbc" in j.name for j in found):
                    jars = found
                    break

    if not jars or not any("mssql-jdbc" in j.name for j in jars):
        raise QueryError(
            "Could not find the Microsoft JDBC driver (mssql-jdbc) and its "
            "MSAL4J dependencies.\n"
            "Either open the connection once in DataGrip (so it downloads the "
            "driver), or set 'jdbc_jars_dir' in ~/.azuresql.yaml to a directory "
            "containing mssql-jdbc*.jar plus the MSAL4J jars."
        )

    return jars


# Exit code the Java helper uses when silent auth fails and no browser is
# allowed (i.e. the user must run `run-query --login`).
_NOT_AUTHENTICATED = 3


def _run_java(
    config: SqlConfig,
    database: str,
    query: str,
    output_path: str,
    interactive: bool,
) -> int:
    """Invoke the Java helper. Returns the row count (or -1 if unknown).

    Raises:
        QueryError: On launch failure, auth failure, or query failure.
    """
    java = _find_java()
    jars = _discover_jars(config)
    classpath = ":".join(str(j) for j in jars)

    if not _RUN_QUERY_JAVA.exists():
        raise QueryError(f"Java helper not found at {_RUN_QUERY_JAVA}")

    cmd = [
        java,
        "-cp", classpath,
        str(_RUN_QUERY_JAVA),
        config.server,
        str(config.port),
        database,
        config.username,
        config.tenant_id or "",
        "interactive" if interactive else "silent",
        output_path,
        query,
    ]

    # stderr (sign-in prompts, progress) always streams straight to the
    # terminal. In file mode we capture stdout to read the row count. In stdout
    # mode the CSV *is* stdout, so we must NOT capture it (that would pull the
    # result rows into this process) -- let it stream straight to the terminal.
    to_stdout = not output_path
    try:
        if to_stdout:
            result = subprocess.run(cmd)
        else:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    except OSError as e:
        raise QueryError(f"Failed to launch Java: {e}") from e

    if result.returncode == _NOT_AUTHENTICATED:
        raise QueryError(
            "Not authenticated. Run `run-query --login` to sign in "
            "(opens a browser once; later runs reuse the cached credential)."
        )
    if result.returncode != 0:
        raise QueryError(
            f"Query failed (java exited {result.returncode}). See output above."
        )

    if to_stdout:
        return -1  # count unknown; CSV went straight to stdout

    out = (result.stdout or "").strip().splitlines()
    try:
        return int(out[-1]) if out else 0
    except ValueError:
        # Couldn't parse a count, but the command succeeded.
        return -1


def login(config: SqlConfig) -> None:
    """Force an interactive Azure AD sign-in and cache the credential.

    Raises:
        QueryError: If sign-in fails.
    """
    _run_java(config, database="master", query="", output_path="", interactive=True)


def run_query_to_csv(
    config: SqlConfig,
    database: str,
    query: str,
    output_path: str,
    force_login: bool = False,
) -> int:
    """Run a validated read-only query and write the results to output_path.

    By default this authenticates silently from the cached credential and never
    opens a browser; if there is no usable cached credential it raises (telling
    the user to run `run-query --login`). Pass force_login=True to sign in
    interactively first.

    The CSV is written by the Java helper. In file mode this process never sees
    the rows. If output_path is empty, the CSV streams to stdout instead.

    Args:
        config: Server connection config.
        database: Database name to connect to.
        query: The SQL query (re-validated here defensively).
        output_path: Destination CSV file path, or "" to stream to stdout.
        force_login: If True, open the browser for an interactive sign-in.

    Returns:
        The number of data rows written (or -1 if the count is unknown).

    Raises:
        QueryError: If the query is rejected, auth fails, or execution fails.
    """
    validate_read_only(query)
    return _run_java(config, database, query, output_path, interactive=force_login)
