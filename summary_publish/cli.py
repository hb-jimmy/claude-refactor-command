"""
CLI for summary-publish.

Usage:
    summary-publish <summary-file> <person>

Example:
    summary-publish ~/.one-on-one/transcripts/van/2026-02-03.md van
"""

import argparse
import sys
from pathlib import Path

from fathom_tool.config import ConfigError
from .config import get_repo_path
from .publisher import (
    extract_date_from_filename,
    insert_summary,
    git_commit_and_push,
    ONE_ON_ONE_FILE,
)


def main():
    parser = argparse.ArgumentParser(
        description="Publish a meeting summary to a shared one-on-one repo."
    )
    parser.add_argument(
        "summary_file",
        help="Path to the summary markdown file (date is extracted from filename).",
    )
    parser.add_argument(
        "person",
        help="Name of the person (must match a person in ~/.one-on-one/config.yaml).",
    )
    args = parser.parse_args()

    summary_path = Path(args.summary_file).expanduser().resolve()
    if not summary_path.exists():
        print(f"Error: Summary file not found: {summary_path}", file=sys.stderr)
        sys.exit(1)

    # Look up repo path from shared config
    try:
        repo_path = get_repo_path(args.person)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    md_path = repo_path / ONE_ON_ONE_FILE
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

    # Insert the summary into one-on-one.md
    try:
        insert_summary(md_path, date, summary_text)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Inserted summary for {date} into {md_path}")

    # Commit and push
    try:
        git_commit_and_push(repo_path, date)
        print(f"Committed and pushed to {repo_path}")
    except Exception as e:
        print(f"Error during git operations: {e}", file=sys.stderr)
        print("The summary was inserted but not committed.", file=sys.stderr)
        sys.exit(1)
