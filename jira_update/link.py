"""
Command-line interface for creating Jira issue links.

This module provides a CLI to create links between Jira issues
(e.g., Duplicates, Blocks, Clones) and to list available link types.
"""

import argparse
import sys

from .client import JiraApiError, JiraClient
from .config import ConfigError, load_credentials


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jira-link",
        description="Create links between Jira issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create a "Duplicates" link:
    jira-link --type Duplicates --outward HA-1 --inward HB-4240
    Result: HA-1 duplicates HB-4240

  Create a "Blocks" link:
    jira-link --type Blocks --outward HB-100 --inward HB-200
    Result: HB-100 blocks HB-200

  List available link types:
    jira-link --list-types
""",
    )

    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List all available issue link types and exit.",
    )

    parser.add_argument(
        "--type",
        metavar="LINK_TYPE",
        help='Link type name (e.g., "Duplicates", "Blocks", "Clones").',
    )

    parser.add_argument(
        "--outward",
        metavar="ISSUE_KEY",
        help="The outward issue key (e.g., HA-1).",
    )

    parser.add_argument(
        "--inward",
        metavar="ISSUE_KEY",
        help="The inward issue key (e.g., HB-4240).",
    )

    return parser


def validate_issue_key(issue_key: str) -> bool:
    """Validate that the issue key has correct format (PROJECT-NUMBER)."""
    if "-" not in issue_key:
        return False
    parts = issue_key.split("-")
    if len(parts) != 2:
        return False
    project, number = parts
    if not project.isalpha() or not project.isupper():
        return False
    if not number.isdigit():
        return False
    return True


def list_link_types(client: JiraClient) -> int:
    """List all available issue link types."""
    link_types = client.get_link_types()

    if not link_types:
        print("No link types found.", file=sys.stderr)
        return 1

    # Calculate column widths
    name_width = max(len(lt.name) for lt in link_types)
    outward_width = max(len(lt.outward) for lt in link_types)
    inward_width = max(len(lt.inward) for lt in link_types)

    # Header
    print(f"{'Name':<{name_width}}  {'Outward':<{outward_width}}  {'Inward':<{inward_width}}")
    print(f"{'-' * name_width}  {'-' * outward_width}  {'-' * inward_width}")

    for lt in sorted(link_types, key=lambda x: x.name):
        print(f"{lt.name:<{name_width}}  {lt.outward:<{outward_width}}  {lt.inward:<{inward_width}}")

    return 0


def create_link(client: JiraClient, link_type: str, outward_key: str, inward_key: str) -> int:
    """Create a link between two issues."""
    # Validate issue key formats
    for key in (outward_key, inward_key):
        if not validate_issue_key(key):
            print(
                f'Error: Invalid issue key format: "{key}"\n'
                "Issue key must be in format PROJECT-NUMBER (e.g., HB-123)",
                file=sys.stderr,
            )
            return 1

    # Resolve link type name
    link_types = client.get_link_types()
    match = None
    for lt in link_types:
        if lt.name.lower() == link_type.lower():
            match = lt
            break

    if not match:
        available = ", ".join(sorted(lt.name for lt in link_types))
        print(
            f'Error: Unknown link type: "{link_type}"\n'
            f"Available types: {available}",
            file=sys.stderr,
        )
        return 1

    # Validate both issues exist
    for key in (outward_key, inward_key):
        try:
            client.get_issue(key)
        except JiraApiError as e:
            print(f"Error: Issue {key} not found: {e}", file=sys.stderr)
            return 1

    # Create the link
    try:
        client.create_issue_link(match.name, outward_key, inward_key)
    except JiraApiError as e:
        print(f"Error: Failed to create link: {e}", file=sys.stderr)
        return 1

    # Display result
    outward_width = max(len("Outward"), len(outward_key))
    inward_width = max(len("Inward"), len(inward_key))
    type_width = max(len("Link Type"), len(match.name))

    print(f"{'Outward':<{outward_width}}  {'Link Type':<{type_width}}  {'Inward':<{inward_width}}")
    print(f"{'-' * outward_width}  {'-' * type_width}  {'-' * inward_width}")
    print(f"{outward_key:<{outward_width}}  {match.name:<{type_width}}  {inward_key:<{inward_width}}")
    print()
    print(f"{outward_key} {match.outward} {inward_key}")

    return 0


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

    client = JiraClient(credentials)

    # Handle --list-types
    if args.list_types:
        return list_link_types(client)

    # Require --type, --outward, --inward for creating a link
    if not args.type or not args.outward or not args.inward:
        parser.error("--type, --outward, and --inward are required when creating a link")
        return 1

    return create_link(client, args.type, args.outward, args.inward)


if __name__ == "__main__":
    sys.exit(main())
