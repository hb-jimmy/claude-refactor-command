"""
Jira HTTP adapter layer.

This module provides an abstraction over HTTP requests to the Jira API.
All HTTP interactions are encapsulated here to allow easy swapping of
the underlying HTTP library.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from .config import JIRA_BASE_URL, JiraCredentials


@dataclass
class JiraIssue:
    """Represents a Jira issue."""
    key: str
    summary: str
    status: str
    project: str


@dataclass
class JiraTransition:
    """Represents an available status transition."""
    id: str
    name: str
    to_status: str


@dataclass
class JiraComment:
    """Represents a Jira comment."""
    id: str
    body: str
    author: str
    created: str


@dataclass
class JiraUser:
    """Represents a Jira user."""
    display_name: str
    email: str
    account_id: str


class JiraApiError(Exception):
    """Raised when a Jira API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class JiraClient:
    """
    HTTP adapter for Jira REST API.

    This class encapsulates all HTTP interactions with Jira, providing
    a clean interface for the rest of the application. The underlying
    HTTP library (requests) can be swapped without affecting other code.
    """

    def __init__(self, credentials: JiraCredentials, base_url: str = JIRA_BASE_URL):
        """
        Initialize the Jira client.

        Args:
            credentials: Jira authentication credentials.
            base_url: Base URL for the Jira instance.
        """
        self._credentials = credentials
        self._base_url = base_url.rstrip("/")
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure an HTTP session."""
        session = requests.Session()
        session.auth = (self._credentials.email, self._credentials.api_token)
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        return session

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make an HTTP request to the Jira API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint (e.g., "/rest/api/3/issue/HB-123").
            json_data: JSON body for the request.
            params: Query parameters.

        Returns:
            Parsed JSON response, or None for 204 No Content.

        Raises:
            JiraApiError: If the request fails.
        """
        url = f"{self._base_url}{endpoint}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=30,
            )
        except requests.RequestException as e:
            raise JiraApiError(f"Network error: {e}")

        # Handle successful responses
        if response.status_code == 204:
            return None

        if response.ok:
            try:
                return response.json()
            except ValueError:
                return None

        # Handle errors
        error_message = self._parse_error_response(response)
        raise JiraApiError(
            message=error_message,
            status_code=response.status_code,
            response_body=response.text,
        )

    def _parse_error_response(self, response: requests.Response) -> str:
        """Parse error message from Jira API response."""
        try:
            data = response.json()
            if "errorMessages" in data and data["errorMessages"]:
                return "; ".join(data["errorMessages"])
            if "errors" in data and data["errors"]:
                return "; ".join(f"{k}: {v}" for k, v in data["errors"].items())
            return f"HTTP {response.status_code}: {response.reason}"
        except ValueError:
            return f"HTTP {response.status_code}: {response.reason}"

    def get_issue(self, issue_key: str) -> JiraIssue:
        """
        Fetch a Jira issue by key.

        Args:
            issue_key: The issue key (e.g., "HB-123").

        Returns:
            JiraIssue with issue details.

        Raises:
            JiraApiError: If the issue cannot be fetched.
        """
        endpoint = f"/rest/api/3/issue/{issue_key}"
        params = {"fields": "summary,status,project"}

        data = self._request("GET", endpoint, params=params)

        if not data:
            raise JiraApiError(f"No data returned for issue {issue_key}")

        fields = data.get("fields", {})

        return JiraIssue(
            key=data.get("key", issue_key),
            summary=fields.get("summary", ""),
            status=fields.get("status", {}).get("name", ""),
            project=fields.get("project", {}).get("key", ""),
        )

    def add_comment(self, issue_key: str, body: str) -> JiraComment:
        """
        Add a comment to a Jira issue.

        The comment body supports Jira wiki markup.

        Args:
            issue_key: The issue key (e.g., "HB-123").
            body: Comment body in Jira wiki markup format.

        Returns:
            JiraComment with the created comment details.

        Raises:
            JiraApiError: If the comment cannot be added.
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/comment"

        # Jira Cloud API v3 uses Atlassian Document Format (ADF)
        # We'll use a simple text node for wiki markup content
        json_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": body,
                            }
                        ]
                    }
                ]
            }
        }

        data = self._request("POST", endpoint, json_data=json_data)

        if not data:
            raise JiraApiError(f"No data returned when adding comment to {issue_key}")

        return JiraComment(
            id=data.get("id", ""),
            body=body,
            author=data.get("author", {}).get("displayName", ""),
            created=data.get("created", ""),
        )

    def get_transitions(self, issue_key: str) -> List[JiraTransition]:
        """
        Get available status transitions for an issue.

        Args:
            issue_key: The issue key (e.g., "HB-123").

        Returns:
            List of available JiraTransition objects.

        Raises:
            JiraApiError: If transitions cannot be fetched.
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/transitions"

        data = self._request("GET", endpoint)

        if not data:
            return []

        transitions = []
        for t in data.get("transitions", []):
            transitions.append(JiraTransition(
                id=t.get("id", ""),
                name=t.get("name", ""),
                to_status=t.get("to", {}).get("name", ""),
            ))

        return transitions

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        """
        Transition an issue to a new status.

        Args:
            issue_key: The issue key (e.g., "HB-123").
            transition_id: The ID of the transition to perform.

        Raises:
            JiraApiError: If the transition fails.
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/transitions"
        json_data = {
            "transition": {
                "id": transition_id
            }
        }

        self._request("POST", endpoint, json_data=json_data)

    def find_transition_to_status(self, issue_key: str, target_status: str) -> Optional[JiraTransition]:
        """
        Find a transition that leads to the target status.

        Args:
            issue_key: The issue key (e.g., "HB-123").
            target_status: The desired status name (case-insensitive).

        Returns:
            JiraTransition if found, None otherwise.
        """
        transitions = self.get_transitions(issue_key)
        target_lower = target_status.lower()

        for transition in transitions:
            if transition.to_status.lower() == target_lower:
                return transition

        return None

    def get_available_statuses(self, issue_key: str) -> List[str]:
        """
        Get list of statuses reachable from the current state.

        Args:
            issue_key: The issue key (e.g., "HB-123").

        Returns:
            List of status names that can be transitioned to.
        """
        transitions = self.get_transitions(issue_key)
        return [t.to_status for t in transitions]

    def get_all_users(self) -> List[JiraUser]:
        """
        Fetch all active human users from Jira.

        Returns only users with:
        - accountType == "atlassian" (real human users, not bots/apps)
        - active == True
        - Valid email address

        Returns:
            List of JiraUser objects.

        Raises:
            JiraApiError: If users cannot be fetched.
        """
        all_users: List[JiraUser] = []
        start_at = 0
        max_results = 100

        while True:
            endpoint = "/rest/api/3/users/search"
            params = {"startAt": start_at, "maxResults": max_results}

            data = self._request("GET", endpoint, params=params)

            if not data or not isinstance(data, list):
                break

            for user in data:
                # Filter to active human users with emails
                if not user.get("active", False):
                    continue
                if user.get("accountType") != "atlassian":
                    continue
                email = user.get("emailAddress", "")
                if not email:
                    continue

                all_users.append(JiraUser(
                    display_name=user.get("displayName", ""),
                    email=email,
                    account_id=user.get("accountId", ""),
                ))

            # Check if we've fetched all users
            if len(data) < max_results:
                break

            start_at += max_results

        return all_users

    def get_current_user(self) -> JiraUser:
        """
        Get the currently authenticated user.

        Returns:
            JiraUser with the current user's details.

        Raises:
            JiraApiError: If the user cannot be fetched.
        """
        endpoint = "/rest/api/3/myself"

        data = self._request("GET", endpoint)

        if not data:
            raise JiraApiError("No data returned for current user")

        return JiraUser(
            display_name=data.get("displayName", ""),
            email=data.get("emailAddress", ""),
            account_id=data.get("accountId", ""),
        )

    def assign_issue(self, issue_key: str, account_id: str) -> None:
        """
        Assign an issue to a user.

        Args:
            issue_key: The issue key (e.g., "HB-123").
            account_id: The account ID of the user to assign.

        Raises:
            JiraApiError: If the assignment fails.
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/assignee"
        json_data = {"accountId": account_id}

        self._request("PUT", endpoint, json_data=json_data)
