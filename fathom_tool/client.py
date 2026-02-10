"""
Fathom HTTP adapter layer.

Uses the Fathom REST API to list meetings and retrieve transcripts.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


FATHOM_API_BASE = "https://api.fathom.ai/external/v1"


@dataclass
class Meeting:
    """Represents a Fathom meeting with transcript availability."""
    recording_id: int
    title: str
    created_at: str
    attendees: List[str]


class FathomApiError(Exception):
    """Raised when a Fathom API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class FathomClient:
    """
    HTTP adapter for the Fathom REST API.

    Authenticates via API key in the X-Api-Key header.
    """

    def __init__(self, api_key: str):
        self._session = requests.Session()
        self._session.headers.update({
            "X-Api-Key": api_key,
            "Accept": "application/json",
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Make an authenticated request to the Fathom API.

        Returns:
            Parsed JSON response.

        Raises:
            FathomApiError: If the request fails.
        """
        url = f"{FATHOM_API_BASE}{endpoint}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                timeout=30,
            )
        except requests.RequestException as e:
            raise FathomApiError(f"Network error: {e}")

        if response.status_code == 429:
            raise FathomApiError(
                "Rate limit exceeded (60 requests/minute). Try again shortly.",
                status_code=429,
            )

        if not response.ok:
            raise FathomApiError(
                f"Fathom API error: HTTP {response.status_code} {response.text}",
                status_code=response.status_code,
            )

        try:
            return response.json()
        except ValueError:
            return None

    def list_meetings(
        self,
        attendee_email: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
    ) -> List[Meeting]:
        """
        List meetings, optionally filtered by attendee email and date range.

        Args:
            attendee_email: Filter to meetings with this calendar invitee.
            created_after: ISO 8601 timestamp (e.g., "2026-01-01T00:00:00Z").
            created_before: ISO 8601 timestamp.

        Returns:
            List of Meeting objects across all pages.
        """
        params: Dict[str, Any] = {}
        if attendee_email:
            params["calendar_invitees[]"] = attendee_email
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before

        all_meetings: List[Meeting] = []
        cursor = None

        while True:
            if cursor:
                params["cursor"] = cursor

            data = self._request("GET", "/meetings", params=params)
            if not data:
                break

            for item in data.get("items", []):
                attendees = [
                    inv.get("email", "")
                    for inv in item.get("calendar_invitees", [])
                    if inv.get("email")
                ]
                all_meetings.append(Meeting(
                    recording_id=item.get("recording_id", 0),
                    title=item.get("title", ""),
                    created_at=item.get("created_at", ""),
                    attendees=attendees,
                ))

            cursor = data.get("next_cursor")
            if not cursor:
                break

        return all_meetings

    def get_transcript(self, recording_id: int) -> List[Dict[str, Any]]:
        """
        Get the transcript for a specific recording.

        Args:
            recording_id: The Fathom recording ID.

        Returns:
            List of transcript entry dicts, each with:
              - speaker: {display_name, matched_calendar_invitee_email}
              - text: spoken text
              - timestamp: "HH:MM:SS"
        """
        data = self._request("GET", f"/recordings/{recording_id}/transcript")

        if not data or not isinstance(data, list):
            return []

        return data
