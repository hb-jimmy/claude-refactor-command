"""
Command-line interface for reading Jira issue details.

This module provides a CLI to fetch and display Jira issue information
in JSON format for use by other tools and scripts.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

from .client import JiraApiError, JiraClient
from .config import ConfigError, load_credentials


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jira-read",
        description="Read Jira issue details and output as JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Read an issue:
    jira-read HB-123

    Output includes: key, summary, description, status, issue type,
    assignee, reporter, project, and linked issues.

  Use with other tools:
    jira-read HB-123 | jq '.description'

Credential Configuration:
  Uses the same credentials as jira-update.
  See 'jira-update --help' for configuration details.
""",
    )

    parser.add_argument(
        "issue",
        metavar="ISSUE_KEY",
        help="Jira issue key (e.g., HB-123, PROJ-456). "
             "Must include the project prefix.",
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


def fetch_issue_details(client: JiraClient, issue_key: str) -> Dict[str, Any]:
    """
    Fetch comprehensive issue details from Jira.

    Args:
        client: Configured JiraClient instance.
        issue_key: The Jira issue key.

    Returns:
        Dictionary with issue details.
    """
    # Fetch issue with all relevant fields
    endpoint = f"/rest/api/3/issue/{issue_key}"
    params = {
        "fields": "summary,description,status,issuetype,assignee,reporter,project,parent,issuelinks,created,updated",
        "expand": "renderedFields",
    }

    data = client._request("GET", endpoint, params=params)

    if not data:
        raise JiraApiError(f"No data returned for issue {issue_key}")

    fields = data.get("fields", {})

    # Extract assignee info
    assignee = fields.get("assignee")
    assignee_info = None
    if assignee:
        assignee_info = {
            "display_name": assignee.get("displayName", ""),
            "email": assignee.get("emailAddress", ""),
            "account_id": assignee.get("accountId", ""),
        }

    # Extract reporter info
    reporter = fields.get("reporter")
    reporter_info = None
    if reporter:
        reporter_info = {
            "display_name": reporter.get("displayName", ""),
            "email": reporter.get("emailAddress", ""),
            "account_id": reporter.get("accountId", ""),
        }

    # Extract parent (for subtasks or issues in epics)
    parent = fields.get("parent")
    parent_info = None
    if parent:
        parent_info = {
            "key": parent.get("key", ""),
            "summary": parent.get("fields", {}).get("summary", ""),
        }

    # Extract linked issues
    issue_links = fields.get("issuelinks", [])
    linked_issues = []
    for link in issue_links:
        link_type = link.get("type", {}).get("name", "")
        if "inwardIssue" in link:
            linked = link["inwardIssue"]
            linked_issues.append({
                "type": link_type,
                "direction": "inward",
                "key": linked.get("key", ""),
                "summary": linked.get("fields", {}).get("summary", ""),
                "status": linked.get("fields", {}).get("status", {}).get("name", ""),
            })
        if "outwardIssue" in link:
            linked = link["outwardIssue"]
            linked_issues.append({
                "type": link_type,
                "direction": "outward",
                "key": linked.get("key", ""),
                "summary": linked.get("fields", {}).get("summary", ""),
                "status": linked.get("fields", {}).get("status", {}).get("name", ""),
            })

    # Extract description text from ADF format
    description = fields.get("description")
    description_text = extract_text_from_adf(description) if description else ""

    return {
        "key": data.get("key", issue_key),
        "summary": fields.get("summary", ""),
        "description": description_text,
        "status": fields.get("status", {}).get("name", ""),
        "issuetype": fields.get("issuetype", {}).get("name", ""),
        "project": {
            "key": fields.get("project", {}).get("key", ""),
            "name": fields.get("project", {}).get("name", ""),
        },
        "assignee": assignee_info,
        "reporter": reporter_info,
        "parent": parent_info,
        "linked_issues": linked_issues,
        "created": fields.get("created", ""),
        "updated": fields.get("updated", ""),
    }


def extract_text_from_adf(adf: Optional[Dict[str, Any]]) -> str:
    """
    Extract plain text from Atlassian Document Format (ADF).

    Args:
        adf: ADF document structure.

    Returns:
        Plain text representation of the document.
    """
    if not adf:
        return ""

    def extract_content(node: Dict[str, Any]) -> str:
        if not isinstance(node, dict):
            return ""

        node_type = node.get("type", "")
        text_parts = []

        # Handle text nodes
        if node_type == "text":
            return node.get("text", "")

        # Handle content arrays
        content = node.get("content", [])
        for child in content:
            text_parts.append(extract_content(child))

        result = "".join(text_parts)

        # Add newlines for block elements
        if node_type in ("paragraph", "heading", "bulletList", "orderedList", "listItem", "codeBlock"):
            result = result + "\n"

        return result

    return extract_content(adf).strip()


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate issue key format
    if not validate_issue_key(args.issue):
        print(
            f"Error: Invalid issue key format: \"{args.issue}\"\n"
            "Issue key must be in format PROJECT-NUMBER (e.g., HB-123)",
            file=sys.stderr
        )
        return 1

    # Load credentials
    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create client and fetch issue
    client = JiraClient(credentials)

    try:
        issue_data = fetch_issue_details(client, args.issue)
    except JiraApiError as e:
        print(f"Error: Failed to fetch issue: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return 1

    # Output as JSON
    print(json.dumps(issue_data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
