"""
Command-line interface for jira-update.

This module provides the CLI entry point and orchestrates the
update operations (comments, status changes, assignments).
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import List, Optional

from .client import JiraApiError, JiraClient
from .config import ConfigError, load_credentials


# Valid status values (case-insensitive matching)
VALID_STATUSES = [
    "To Do",
    "In Progress",
    "QA",
    "Code Review",
    "Accepted",
    "Done",
]

# Sentinel value to indicate --assign was used without a value (assign to self)
ASSIGN_SELF = "__SELF__"


@dataclass
class UpdateResult:
    """Result of an update operation."""
    issue_key: str
    issue_summary: str
    comment_added: bool
    comment_body: Optional[str]
    status_changed: bool
    old_status: Optional[str]
    new_status: Optional[str]
    available_statuses: Optional[List[str]]
    errors: List[str]


@dataclass
class AssignResult:
    """Result of an assignment operation."""
    issue_key: str
    issue_summary: str
    assigned: bool
    assignee_name: Optional[str]
    assignee_account_id: Optional[str]
    errors: List[str]


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    epilog = """
Examples:
  Add a comment to an issue:
    jira-update HB-123 --message "Fixed the null pointer exception in UserService"

    Expected outcome: Adds the comment to HB-123. The comment will appear in the
    issue's comment section with your user as the author.

  Change the status of an issue:
    jira-update HB-123 --status "In Progress"

    Expected outcome: Transitions HB-123 to "In Progress" status. If the transition
    is not available from the current status, shows available statuses.

  Add a comment and change status:
    jira-update HB-123 -m "Starting work on this" -s "In Progress"

    Expected outcome: Adds the comment AND transitions to "In Progress".
    Both operations are attempted; if one fails, the other may still succeed.

  Assign an issue to yourself:
    jira-update HB-123 --assign

    Expected outcome: Assigns HB-123 to the authenticated user (you).

  Assign an issue to a specific user:
    jira-update HB-123 --assign 712020:abc123-def456

    Expected outcome: Assigns HB-123 to the user with the given account ID.
    Use 'jira-users' command to look up account IDs.

  Use Jira wiki markup in comments:
    jira-update HB-123 -m "*Bold text* and _italic text_ and {code}some code{code}"

    Expected outcome: The comment is rendered with Jira formatting applied.

  Post a rich comment with @mentions using ADF format:
    jira-update HB-123 --adf -m '[{"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"Added authentication"}]},{"type":"paragraph","content":[{"type":"text","text":"Pairing: "},{"type":"mention","attrs":{"id":"712020:abc123","text":"@John Smith","accessLevel":""}}]},{"type":"paragraph","content":[{"type":"text","text":"Users can now log in with SSO credentials."}]}]'

    Expected outcome: Comment is posted with a heading, clickable @mention, and body text.

ADF Format (for --adf flag):
  When --adf is specified, --message must be a JSON array of ADF content nodes.
  Common node types:
    - Heading: {"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"Title"}]}
    - Paragraph: {"type":"paragraph","content":[...nodes...]}
    - Text: {"type":"text","text":"Your text here"}
    - Mention: {"type":"mention","attrs":{"id":"account_id","text":"@Display Name","accessLevel":""}}

  Get JSON output for scripting:
    jira-update HB-123 -m "Automated update" --json

    Expected outcome: Outputs structured JSON with full operation details,
    suitable for parsing by other tools or scripts.

  Mark an issue as done:
    jira-update HB-123 -s "Done" -m "Completed and deployed to production"

    Expected outcome: Transitions to "Done" and adds the completion comment.

Important Notes:
  --assign must be used alone and cannot be combined with --message or --status.

Credential Configuration:
  Credentials are auto-discovered in this order:

  1. Environment variables:
     export JIRA_EMAIL="your.email@example.com"
     export JIRA_API_TOKEN="your-api-token"

  2. Config file (~/.jira-config.yaml):
     email: your.email@example.com
     api_token: your-api-token

  To generate an API token, visit:
    https://id.atlassian.com/manage-profile/security/api-tokens

Valid Statuses:
  To Do, In Progress, QA, Code Review, Accepted, Done
  (Status matching is case-insensitive)
"""

    parser = argparse.ArgumentParser(
        prog="jira-update",
        description="Update Jira tickets with comments, status changes, and assignments.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "issue",
        metavar="ISSUE_KEY",
        help="Jira issue key (e.g., HB-123, PROJ-456). "
             "Must include the project prefix.",
    )

    parser.add_argument(
        "-m", "--message",
        metavar="TEXT",
        help="Comment to add to the issue. Supports Jira wiki markup for "
             "formatting (e.g., *bold*, _italic_, {code}code{code}). "
             "Cannot be used with --assign.",
    )

    parser.add_argument(
        "-s", "--status",
        metavar="STATUS",
        help=f"New status for the issue. Valid values: {', '.join(VALID_STATUSES)}. "
             "The tool will find and execute the appropriate transition. "
             "If the status is not reachable, available statuses will be shown. "
             "Cannot be used with --assign.",
    )

    parser.add_argument(
        "-a", "--assign",
        metavar="ACCOUNT_ID",
        nargs="?",
        const=ASSIGN_SELF,
        help="Assign the issue. Without a value, assigns to yourself. "
             "With an account ID, assigns to that user. "
             "Must be used alone (cannot combine with --message or --status). "
             "Use 'jira-users' to look up account IDs.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON for scripting/automation. "
             "Includes full operation details, issue info, and any errors.",
    )

    parser.add_argument(
        "--adf",
        action="store_true",
        help="Interpret --message as ADF (Atlassian Document Format) JSON. "
             "The message must be a JSON array of ADF content nodes. "
             "Use this for rich formatting with @mentions.",
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


def normalize_status(status: str) -> Optional[str]:
    """
    Normalize status input to match valid status names.

    Args:
        status: User-provided status string.

    Returns:
        Normalized status name if valid, None otherwise.
    """
    status_lower = status.lower()
    for valid_status in VALID_STATUSES:
        if valid_status.lower() == status_lower:
            return valid_status
    return None


def print_result(result: UpdateResult, use_json: bool) -> None:
    """Print the update result in the appropriate format."""
    if use_json:
        output = {
            "issue_key": result.issue_key,
            "issue_summary": result.issue_summary,
            "comment": {
                "added": result.comment_added,
                "body": result.comment_body,
            },
            "status": {
                "changed": result.status_changed,
                "old": result.old_status,
                "new": result.new_status,
                "available": result.available_statuses,
            },
            "errors": result.errors,
            "success": len(result.errors) == 0,
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    if result.comment_added:
        print(f"Added comment to {result.issue_key}")

    if result.status_changed:
        print(f"Status changed: \"{result.old_status}\" -> \"{result.new_status}\"")

    for error in result.errors:
        print(f"Error: {error}", file=sys.stderr)


def print_assign_result(result: AssignResult, use_json: bool) -> None:
    """Print the assignment result in the appropriate format."""
    if use_json:
        output = {
            "issue_key": result.issue_key,
            "issue_summary": result.issue_summary,
            "assignment": {
                "assigned": result.assigned,
                "assignee_name": result.assignee_name,
                "assignee_account_id": result.assignee_account_id,
            },
            "errors": result.errors,
            "success": len(result.errors) == 0,
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    if result.assigned:
        print(f"Assigned {result.issue_key} to {result.assignee_name}")

    for error in result.errors:
        print(f"Error: {error}", file=sys.stderr)


def run_update(issue_key: str, message: Optional[str], status: Optional[str], client: JiraClient, use_adf: bool = False) -> UpdateResult:
    """
    Execute the update operations on a Jira issue.

    Args:
        issue_key: The Jira issue key.
        message: Optional comment to add.
        status: Optional status to transition to.
        client: Configured JiraClient instance.

    Returns:
        UpdateResult with operation outcomes.
    """
    errors: List[str] = []
    comment_added = False
    comment_body = message
    status_changed = False
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    available_statuses: Optional[List[str]] = None
    issue_summary = ""

    # Fetch issue to validate it exists and get current status
    try:
        issue = client.get_issue(issue_key)
        old_status = issue.status
        issue_summary = issue.summary
    except JiraApiError as e:
        errors.append(f"Failed to fetch issue: {e}")
        return UpdateResult(
            issue_key=issue_key,
            issue_summary=issue_summary,
            comment_added=comment_added,
            comment_body=comment_body,
            status_changed=status_changed,
            old_status=old_status,
            new_status=new_status,
            available_statuses=available_statuses,
            errors=errors,
        )

    # Add comment if provided
    if message:
        try:
            if use_adf:
                # Parse message as ADF JSON content array
                adf_content = json.loads(message)
                client.add_rich_comment(issue_key, adf_content)
            else:
                client.add_comment(issue_key, message)
            comment_added = True
        except json.JSONDecodeError as e:
            errors.append(f"Failed to parse ADF JSON: {e}")
        except JiraApiError as e:
            errors.append(f"Failed to add comment: {e}")

    # Change status if provided
    if status:
        normalized_status = normalize_status(status)
        if not normalized_status:
            errors.append(f"Invalid status: \"{status}\". Valid statuses: {', '.join(VALID_STATUSES)}")
        else:
            try:
                transition = client.find_transition_to_status(issue_key, normalized_status)
                if transition:
                    client.transition_issue(issue_key, transition.id)
                    status_changed = True
                    new_status = normalized_status
                else:
                    available_statuses = client.get_available_statuses(issue_key)
                    if available_statuses:
                        errors.append(
                            f"Cannot transition to \"{normalized_status}\" from current status \"{old_status}\". "
                            f"Available statuses: {', '.join(available_statuses)}"
                        )
                    else:
                        errors.append(
                            f"Cannot transition to \"{normalized_status}\". No transitions available from \"{old_status}\"."
                        )
            except JiraApiError as e:
                errors.append(f"Failed to change status: {e}")

    return UpdateResult(
        issue_key=issue_key,
        issue_summary=issue_summary,
        comment_added=comment_added,
        comment_body=comment_body,
        status_changed=status_changed,
        old_status=old_status,
        new_status=new_status,
        available_statuses=available_statuses,
        errors=errors,
    )


def run_assign(issue_key: str, account_id: Optional[str], client: JiraClient) -> AssignResult:
    """
    Execute the assignment operation on a Jira issue.

    Args:
        issue_key: The Jira issue key.
        account_id: Account ID to assign to, or None to assign to self.
        client: Configured JiraClient instance.

    Returns:
        AssignResult with operation outcome.
    """
    errors: List[str] = []
    assigned = False
    assignee_name: Optional[str] = None
    assignee_account_id: Optional[str] = None
    issue_summary = ""

    # Fetch issue to validate it exists
    try:
        issue = client.get_issue(issue_key)
        issue_summary = issue.summary
    except JiraApiError as e:
        errors.append(f"Failed to fetch issue: {e}")
        return AssignResult(
            issue_key=issue_key,
            issue_summary=issue_summary,
            assigned=assigned,
            assignee_name=assignee_name,
            assignee_account_id=assignee_account_id,
            errors=errors,
        )

    # Determine who to assign to
    if account_id is None or account_id == ASSIGN_SELF:
        # Assign to self
        try:
            current_user = client.get_current_user()
            assignee_account_id = current_user.account_id
            assignee_name = current_user.display_name
        except JiraApiError as e:
            errors.append(f"Failed to get current user: {e}")
            return AssignResult(
                issue_key=issue_key,
                issue_summary=issue_summary,
                assigned=assigned,
                assignee_name=assignee_name,
                assignee_account_id=assignee_account_id,
                errors=errors,
            )
    else:
        # Assign to specified account ID
        assignee_account_id = account_id
        assignee_name = account_id  # We don't look up the name

    # Perform the assignment
    try:
        client.assign_issue(issue_key, assignee_account_id)
        assigned = True
    except JiraApiError as e:
        errors.append(f"Failed to assign issue: {e}")

    return AssignResult(
        issue_key=issue_key,
        issue_summary=issue_summary,
        assigned=assigned,
        assignee_name=assignee_name,
        assignee_account_id=assignee_account_id,
        errors=errors,
    )


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

    # Check if --assign is being used
    is_assign_mode = args.assign is not None

    # Validate: --assign cannot be combined with --message or --status
    if is_assign_mode and (args.message or args.status):
        print(
            "Error: --assign cannot be combined with --message or --status.\n"
            "Use --assign alone to assign an issue.",
            file=sys.stderr
        )
        return 1

    # Validate: --adf requires --message
    if args.adf and not args.message:
        print(
            "Error: --adf requires --message to be specified.\n"
            "Provide the ADF JSON content via --message.",
            file=sys.stderr
        )
        return 1

    # Require at least one action
    if not is_assign_mode and not args.message and not args.status:
        print(
            "Error: At least one of --message, --status, or --assign is required.\n"
            "Use --help for usage information.",
            file=sys.stderr
        )
        return 1

    # Load credentials
    try:
        credentials = load_credentials()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create client
    client = JiraClient(credentials)

    # Execute the appropriate operation
    if is_assign_mode:
        # Assignment mode
        try:
            # Pass the actual value (could be ASSIGN_SELF or an account ID)
            result = run_assign(args.issue, args.assign, client)
        except Exception as e:
            print(f"Error: Unexpected error: {e}", file=sys.stderr)
            return 1

        # Print results
        print_assign_result(result, args.json)
    else:
        # Update mode (comment/status)
        try:
            result = run_update(args.issue, args.message, args.status, client, use_adf=args.adf)
        except Exception as e:
            print(f"Error: Unexpected error: {e}", file=sys.stderr)
            return 1

        # Print results
        print_result(result, args.json)

    # Return non-zero if there were errors
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
