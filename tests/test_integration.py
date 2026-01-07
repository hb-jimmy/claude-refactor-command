"""
Integration tests for jira-update and jira-users CLI tools.

These tests make real HTTP calls to Jira and verify the commands work
as expected when run from the command line.

Test issue: HB-7162
Test user for assignment: Sarah Betack (557058:1b61afdf-a55d-43d9-8901-a15cb32a378f)
"""

import json
import subprocess
import pytest
from datetime import datetime


# Test configuration
TEST_ISSUE = "HB-7162"
SARAH_ACCOUNT_ID = "557058:1b61afdf-a55d-43d9-8901-a15cb32a378f"
SARAH_NAME = "Sarah Betack"


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run a CLI command and return the result."""
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
    )


class TestJiraUpdateComment:
    """Tests for adding comments with jira-update."""

    def test_add_comment_human_output(self):
        """Test adding a comment with human-readable output."""
        timestamp = datetime.now().isoformat()
        message = f"Integration test comment at {timestamp}"

        result = run_command([
            "jira-update", TEST_ISSUE,
            "--message", message,
        ])

        assert result.returncode == 0
        assert f"Added comment to {TEST_ISSUE}" in result.stdout

    def test_add_comment_json_output(self):
        """Test adding a comment with JSON output."""
        timestamp = datetime.now().isoformat()
        message = f"Integration test comment (JSON) at {timestamp}"

        result = run_command([
            "jira-update", TEST_ISSUE,
            "--message", message,
            "--json",
        ])

        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["success"] is True
        assert output["issue_key"] == TEST_ISSUE
        assert output["comment"]["added"] is True
        assert output["comment"]["body"] == message
        assert "issue_summary" in output
        assert output["errors"] == []


class TestJiraUpdateStatus:
    """Tests for changing status with jira-update."""

    def test_change_status_to_in_progress(self):
        """Test changing status to 'In Progress'."""
        result = run_command([
            "jira-update", TEST_ISSUE,
            "--status", "In Progress",
            "--json",
        ])

        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["success"] is True
        assert output["status"]["changed"] is True
        assert output["status"]["new"] == "In Progress"

    def test_restore_status_to_todo(self):
        """Test restoring status back to 'To Do'."""
        result = run_command([
            "jira-update", TEST_ISSUE,
            "--status", "To Do",
            "--json",
        ])

        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["success"] is True
        assert output["status"]["changed"] is True
        assert output["status"]["new"] == "To Do"


class TestJiraUpdateAssign:
    """Tests for assigning issues with jira-update."""

    def test_assign_to_other_user(self):
        """Test assigning issue to Sarah."""
        result = run_command([
            "jira-update", TEST_ISSUE,
            "--assign", SARAH_ACCOUNT_ID,
            "--json",
        ])

        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["success"] is True
        assert output["assignment"]["assigned"] is True
        assert output["assignment"]["assignee_account_id"] == SARAH_ACCOUNT_ID

    def test_assign_to_self(self):
        """Test assigning issue back to self (current user)."""
        result = run_command([
            "jira-update", TEST_ISSUE,
            "--assign",
            "--json",
        ])

        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["success"] is True
        assert output["assignment"]["assigned"] is True
        # Verify it was assigned to someone (the current user)
        assert output["assignment"]["assignee_account_id"] is not None
        assert output["assignment"]["assignee_name"] is not None

    def test_assign_human_output(self):
        """Test assign with human-readable output."""
        result = run_command([
            "jira-update", TEST_ISSUE,
            "--assign",
        ])

        assert result.returncode == 0
        assert f"Assigned {TEST_ISSUE} to" in result.stdout


class TestJiraUsers:
    """Tests for jira-users command."""

    def test_list_users_json(self):
        """Test listing users with default JSON output."""
        result = run_command(["jira-users"])

        assert result.returncode == 0

        users = json.loads(result.stdout)
        assert isinstance(users, list)
        assert len(users) > 0

        # Verify structure of first user
        first_user = users[0]
        assert "display_name" in first_user
        assert "email" in first_user
        assert "account_id" in first_user

        # Verify all users have required fields
        for user in users:
            assert user["display_name"]
            assert user["email"]
            assert user["account_id"]

    def test_list_users_pretty(self):
        """Test listing users with --pretty table output."""
        result = run_command(["jira-users", "--pretty"])

        assert result.returncode == 0

        # Verify table structure
        output = result.stdout
        assert "Display Name" in output
        assert "Email" in output
        assert "Account ID" in output
        assert "Total:" in output

        # Verify it contains separator lines (table formatting)
        assert "---" in output


class TestJiraUpdateCombinedOperations:
    """Tests for combined operations with jira-update."""

    def test_comment_and_status_change(self):
        """Test adding a comment and changing status in one command."""
        timestamp = datetime.now().isoformat()
        message = f"Combined operation test at {timestamp}"

        # First change to In Progress with a comment
        result = run_command([
            "jira-update", TEST_ISSUE,
            "--message", message,
            "--status", "In Progress",
            "--json",
        ])

        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["success"] is True
        assert output["comment"]["added"] is True
        assert output["status"]["changed"] is True
        assert output["status"]["new"] == "In Progress"

        # Restore to To Do
        restore_result = run_command([
            "jira-update", TEST_ISSUE,
            "--status", "To Do",
        ])
        assert restore_result.returncode == 0
