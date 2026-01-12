"""OAuth authentication flow for Slack user tokens.

This module implements a manual OAuth 2.0 flow to obtain a Slack user token:
1. Display the authorization URL for the user to visit
2. User authorizes and copies the code from the redirect URL
3. Exchange the code for an access token
4. Save the token to the config file
"""

import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Optional

import requests

from .config import (
    OAUTH_REDIRECT_PORT,
    OAUTH_REDIRECT_PATH,
    OAUTH_SCOPES,
    OAuthConfig,
    save_token,
)


# Slack OAuth endpoints
SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"

# Use HTTPS for redirect URL (Slack requires it)
REDIRECT_URL = f"https://localhost:{OAUTH_REDIRECT_PORT}{OAUTH_REDIRECT_PATH}"


@dataclass
class AuthResult:
    """Result of an OAuth authentication attempt."""
    success: bool
    token: Optional[str] = None
    error: Optional[str] = None
    user_id: Optional[str] = None
    team_name: Optional[str] = None


def _build_authorize_url(oauth_config: OAuthConfig) -> str:
    """Build the Slack OAuth authorization URL.

    Args:
        oauth_config: OAuth client credentials.

    Returns:
        Full authorization URL.
    """
    params = {
        "client_id": oauth_config.client_id,
        "redirect_uri": REDIRECT_URL,
        "user_scope": ",".join(OAUTH_SCOPES),  # Only request user token scopes
    }

    return f"{SLACK_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def _exchange_code_for_token(
    oauth_config: OAuthConfig,
    code: str,
) -> AuthResult:
    """Exchange authorization code for access token.

    Args:
        oauth_config: OAuth client credentials.
        code: Authorization code from callback.

    Returns:
        AuthResult with token or error.
    """
    try:
        response = requests.post(
            SLACK_TOKEN_URL,
            data={
                "client_id": oauth_config.client_id,
                "client_secret": oauth_config.client_secret,
                "code": code,
                "redirect_uri": REDIRECT_URL,
            },
        )
        response.raise_for_status()
    except requests.RequestException as e:
        return AuthResult(success=False, error=f"Network error: {e}")

    data = response.json()

    if not data.get("ok"):
        error = data.get("error", "Unknown error")
        return AuthResult(success=False, error=f"Slack API error: {error}")

    # User token is in authed_user for user token flow
    authed_user = data.get("authed_user", {})
    user_token = authed_user.get("access_token")

    if not user_token:
        # Fallback to top-level access_token (bot token flow)
        user_token = data.get("access_token")

    if not user_token:
        return AuthResult(
            success=False,
            error="No access token in response. Check OAuth scopes.",
        )

    team_name = data.get("team", {}).get("name")
    user_id = authed_user.get("id")

    return AuthResult(
        success=True,
        token=user_token,
        user_id=user_id,
        team_name=team_name,
    )


def extract_code_from_url(url: str) -> Optional[str]:
    """Extract the authorization code from a redirect URL.

    Args:
        url: The full redirect URL or just the code parameter.

    Returns:
        The authorization code, or None if not found.
    """
    # If it looks like just a code (no URL structure), return it directly
    if not url.startswith("http") and "=" not in url and "&" not in url:
        return url.strip()

    # Parse as URL
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        codes = params.get("code", [])
        return codes[0] if codes else None
    except Exception:
        return None


def run_oauth_flow(oauth_config: OAuthConfig) -> AuthResult:
    """Run the manual OAuth flow to obtain a user token.

    This function:
    1. Displays the authorization URL
    2. Prompts user to authorize and copy the code
    3. Exchanges the code for a token
    4. Saves the token to config

    Args:
        oauth_config: OAuth client credentials.

    Returns:
        AuthResult indicating success or failure.
    """
    # Build authorization URL
    auth_url = _build_authorize_url(oauth_config)

    print("=" * 60)
    print("SLACK AUTHORIZATION")
    print("=" * 60)
    print()
    print("1. Open this URL in your browser:")
    print()
    print(f"   {auth_url}")
    print()
    print("2. Authorize the app when prompted")
    print()
    print("3. After authorizing, you'll be redirected to a page that")
    print("   won't load (this is expected). Copy the ENTIRE URL from")
    print("   your browser's address bar.")
    print()
    print("   It will look like:")
    print("   https://localhost:8765/oauth/callback?code=XXXXX...")
    print()
    print("=" * 60)
    print()

    # Open browser automatically
    try:
        webbrowser.open(auth_url)
        print("(Browser opened automatically)")
        print()
    except Exception:
        pass  # Browser open failed, user can copy URL manually

    # Prompt for the redirect URL
    try:
        user_input = input("Paste the redirect URL here: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return AuthResult(success=False, error="Authorization cancelled")

    if not user_input:
        return AuthResult(success=False, error="No URL provided")

    # Check for error in URL
    if "error=" in user_input:
        parsed = urllib.parse.urlparse(user_input)
        params = urllib.parse.parse_qs(parsed.query)
        error = params.get("error", ["unknown"])[0]
        error_desc = params.get("error_description", [""])[0]
        return AuthResult(
            success=False,
            error=f"Authorization denied: {error}. {error_desc}".strip(),
        )

    # Extract the code
    code = extract_code_from_url(user_input)
    if not code:
        return AuthResult(
            success=False,
            error="Could not extract authorization code from URL",
        )

    # Exchange code for token
    print()
    print("Exchanging authorization code for token...")
    result = _exchange_code_for_token(oauth_config, code)

    if result.success and result.token:
        save_token(result.token)
        print("Token saved to ~/.slack-config.yaml")

    return result
