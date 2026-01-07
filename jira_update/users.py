"""
Command-line interface for listing Jira users.

This module provides a CLI to list all active human users
with their account IDs for use in mentions and collaboration.
"""

import argparse
import json
import sys
from dataclasses import asdict
from typing import List

from .client import JiraApiError, JiraClient, JiraUser
from .config import ConfigError, load_credentials


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jira-users",
        description="List all active Jira users with their account IDs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Output as a human-readable table instead of JSON.",
    )

    return parser


def format_json(users: List[JiraUser]) -> str:
    """Format users as JSON for AI/script consumption."""
    user_dicts = [asdict(user) for user in users]
    return json.dumps(user_dicts, indent=2)


def format_table(users: List[JiraUser]) -> str:
    """Format users as a human-readable table."""
    if not users:
        return "No users found."

    # Calculate column widths
    name_width = max(len(u.display_name) for u in users)
    name_width = max(name_width, len("Display Name"))

    email_width = max(len(u.email) for u in users)
    email_width = max(email_width, len("Email"))

    # Build table
    lines = []
    header = f"| {'#':<4} | {'Display Name':<{name_width}} | {'Email':<{email_width}} | Account ID"
    separator = f"|{'-' * 6}|{'-' * (name_width + 2)}|{'-' * (email_width + 2)}|{'-' * 50}"

    lines.append(header)
    lines.append(separator)

    for i, user in enumerate(users, 1):
        line = f"| {i:<4} | {user.display_name:<{name_width}} | {user.email:<{email_width}} | {user.account_id}"
        lines.append(line)

    lines.append("")
    lines.append(f"Total: {len(users)} users")

    return "\n".join(lines)


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Load credentials
    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create client and fetch users
    client = JiraClient(credentials)

    try:
        users = client.get_all_users()
    except JiraApiError as e:
        print(f"Error: Failed to fetch users: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return 1

    # Output results
    if args.pretty:
        print(format_table(users))
    else:
        print(format_json(users))

    return 0


if __name__ == "__main__":
    sys.exit(main())
