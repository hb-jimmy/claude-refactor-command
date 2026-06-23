"""CLI entry point for run-query.

Runs a read-only query against an Azure SQL database using Azure Active
Directory authentication (via the Microsoft JDBC driver, the same way DataGrip
connects), and writes the results to a CSV file.

Authentication is cached on disk. Normal runs reuse the cached credential
silently and never open a browser. Use --login to (re)authenticate
interactively.

Usage:
    run-query --login
    run-query --db haCentene --query "SELECT TOP 10 * FROM dbo.Members"            # to stdout
    run-query --db haCentene --output results.csv --query "SELECT TOP 10 * ..."    # to file
    run-query --login --db haCentene -o out.csv -q "SELECT ..."   # re-auth, then run
"""

import argparse
import sys

from .config import ConfigError, load_config
from .client import QueryError, run_query_to_csv, login, validate_read_only


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="run-query",
        description=(
            "Run a read-only query against an Azure SQL database (AAD auth, "
            "cached) and write the results to a CSV file."
        ),
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Sign in interactively (opens a browser) and cache the credential. "
             "Without a query, just authenticates and exits.",
    )
    parser.add_argument(
        "--db",
        help="Database name to connect to.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to the CSV file to write results to. "
             "If omitted, the CSV is written to stdout.",
    )
    parser.add_argument(
        "--query", "-q",
        help='SQL query to run (must be read-only). Quote it on the command line.',
    )

    args = parser.parse_args()

    try:
        config = load_config()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Login-only: --login with no query just authenticates and caches.
    if args.login and not args.query:
        if args.db or args.output:
            parser.error("--db/--output require --query.")
        try:
            login(config)
        except QueryError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        return 0

    # Query mode: --db and --query are required; --output is optional (stdout).
    missing = [name for name, val in
               (("--db", args.db), ("--query/-q", args.query))
               if not val]
    if missing:
        parser.error("the following arguments are required: " + ", ".join(missing))

    # Validate the query is read-only before doing anything else (cheap and
    # avoids work for an invalid query).
    try:
        validate_read_only(args.query)
    except QueryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = args.output or ""
    try:
        rows = run_query_to_csv(
            config, args.db, args.query, output_path, force_login=args.login
        )
    except QueryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if output_path:
        if rows >= 0:
            print(f"Done. {rows} row(s) written to {output_path}.", file=sys.stderr)
        else:
            print(f"Done. Results written to {output_path}.", file=sys.stderr)
    # In stdout mode the CSV is the stdout payload; the Java helper already
    # reported the row count on stderr, so we add nothing here.
    return 0


if __name__ == "__main__":
    sys.exit(main())
