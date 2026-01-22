"""
Command-line interface for finding the latest THB Automated Summary SHA.

This module searches Jira comments for the most recent THB Automated Summary
marker and returns the associated commit SHA, or the merge-base with main/master
if no previous summary exists.
"""

import argparse
import json
import re
import subprocess
import sys
from typing import Optional

from .client import JiraApiError, JiraClient
from .config import ConfigError, load_credentials


# Pattern to match "THB Automated Summary: <sha>" in comments
THB_SUMMARY_PATTERN = re.compile(r"THB Automated Summary:\s*([a-f0-9]+)", re.IGNORECASE)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jira-latest-comment",
        description="Find the SHA from the latest THB Automated Summary comment on a Jira issue.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "issue",
        metavar="ISSUE_KEY",
        help="Jira issue key (e.g., HB-123).",
    )

    return parser


def get_merge_base() -> Optional[str]:
    """
    Get the merge-base SHA with main or master branch.

    Returns:
        The merge-base SHA, or None if it cannot be determined.
    """
    # Try main first, then master
    for branch in ["main", "master"]:
        try:
            result = subprocess.run(
                ["git", "merge-base", branch, "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            sha = result.stdout.strip()
            if sha:
                return sha[:7]  # Return short SHA
        except subprocess.CalledProcessError:
            continue

    return None


def find_latest_summary_sha(client: JiraClient, issue_key: str) -> Optional[str]:
    """
    Search comments for the latest THB Automated Summary and extract the SHA.

    Args:
        client: Configured JiraClient instance.
        issue_key: The Jira issue key.

    Returns:
        The SHA from the latest summary comment, or None if not found.
    """
    try:
        comments = client.get_comments(issue_key)
    except JiraApiError:
        return None

    # Search from newest to oldest (comments are returned oldest first)
    for comment in reversed(comments):
        match = THB_SUMMARY_PATTERN.search(comment.body)
        if match:
            return match.group(1)

    return None


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Load credentials
    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(json.dumps({"error": str(e)}))
        return 1

    # Create client
    client = JiraClient(credentials)

    # Search for latest THB Automated Summary
    sha = find_latest_summary_sha(client, args.issue)

    if sha:
        # Found a previous summary, return its SHA
        print(json.dumps({"sha": sha}))
        return 0

    # No previous summary found, return merge-base
    merge_base = get_merge_base()
    if merge_base:
        print(json.dumps({"sha": merge_base}))
        return 0

    # Could not determine merge-base
    print(json.dumps({"error": "Could not determine merge-base with main or master"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
