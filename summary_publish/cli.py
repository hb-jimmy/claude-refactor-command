"""
CLI for summary-publish.

Usage:
    summary-publish --config PATH <summary-file> <name>

Example:
    summary-publish --config ~/.one-on-one/config.yaml ~/.one-on-one/summaries/van/2026-02-03.md van
"""

import argparse
import sys
from pathlib import Path

from fathom_tool.config import ConfigError
from .config import get_meeting, get_repo_path
from .publisher import (
    extract_date_from_filename,
    insert_summary,
    git_commit_and_push,
)


def main():
    parser = argparse.ArgumentParser(
        description="Publish a meeting summary to a shared repo."
    )
    parser.add_argument(
        "--config", "-c",
        required=True,
        help="Path to the config.yaml file.",
    )
    parser.add_argument(
        "summary_file",
        help="Path to the summary markdown file (date is extracted from filename).",
    )
    parser.add_argument(
        "name",
        help="Name of the meeting/person (must match a name in config.yaml).",
    )
    args = parser.parse_args()

    summary_path = Path(args.summary_file).expanduser().resolve()
    if not summary_path.exists():
        print(f"Error: Summary file not found: {summary_path}", file=sys.stderr)
        sys.exit(1)

    config_path = Path(args.config).expanduser()

    # Look up meeting config
    try:
        meeting = get_meeting(args.name, config_path=config_path)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get repo path
    try:
        repo_path = get_repo_path(args.name, config_path=config_path)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    target_file = meeting.file or "one-on-one.md"
    md_path = repo_path / target_file
    if not md_path.exists():
        print(f"Error: {md_path} not found.", file=sys.stderr)
        sys.exit(1)

    # Extract date from filename
    try:
        date = extract_date_from_filename(summary_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Read the summary content
    summary_text = summary_path.read_text()

    # Insert the summary into the target file
    try:
        insert_summary(md_path, date, summary_text)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Inserted summary for {date} into {md_path}")

    # Commit and push
    try:
        git_commit_and_push(repo_path, date, filename=target_file)
        print(f"Committed and pushed to {repo_path}")
    except Exception as e:
        print(f"Error during git operations: {e}", file=sys.stderr)
        print("The summary was inserted but not committed.", file=sys.stderr)
        sys.exit(1)
