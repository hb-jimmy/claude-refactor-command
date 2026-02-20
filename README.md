# Claude Code Utilities

CLI tools and Claude Code commands for Jira and Slack integration, designed for use with `/thb-flow` and `/thb-update`.

## Installation

### Prerequisites

- Python 3.8+
- [Claude Code](https://github.com/anthropics/claude-code) installed
- Git

### Install

```bash
git clone https://github.com/hb-jimmy/claude-refactor-command.git
cd claude-refactor-command
./install.sh
```

### What `install.sh` Does

The script performs five steps:

1. **Installs pipx** if it isn't already available. It tries Homebrew first, then falls back to `pip3`/`pip`. pipx manages Python CLI tools in isolated virtual environments so they don't conflict with other Python packages on your system.

2. **Installs the `claude-utils` Python package** in editable mode via `pipx install -e .`. This creates an isolated virtualenv at `~/.local/pipx/venvs/claude-utils/` with all dependencies (requests, pyyaml, markdownify) and generates wrapper scripts in `~/.local/bin/` for each CLI tool. Editable mode means changes to the source `.py` files take effect immediately without reinstalling.

3. **Adds `~/.local/bin` to your PATH** if it isn't already there. The script checks your existing shell profiles (`.zshrc`, `.bashrc`, `.bash_profile`, `.profile`) and appends a `PATH` export to whichever ones exist, skipping any that already have the entry. If no profile exists, it creates `~/.zshrc`.

4. **Copies the `/thb-flow` and `/thb-update` command files** to `~/.claude/commands/` so they are available globally in Claude Code, not just within this repository. Existing files are only overwritten if the content has changed.

5. **Verifies the installation** by running `--help` on every CLI tool to confirm they are callable and working.

The script is idempotent and safe to run multiple times.

## Configuration

### Jira

Create `~/.jira-config.yaml`:
```yaml
email: "your.email@company.com"
api_token: "your-jira-api-token"
```

Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens

### Slack

1. Create a Slack App at https://api.slack.com/apps
2. Add OAuth scopes: `chat:write`, `channels:read`, `groups:read`, `users:read`, `users:read.email`, `channels:history`, `groups:history`
3. Add redirect URL: `https://localhost:8765/oauth/callback`
4. Add to `~/.slack-config.yaml`:
   ```yaml
   client_id: "your-client-id"
   client_secret: "your-client-secret"
   ```
5. Run `slack-update --auth` to complete the OAuth flow

For `/thb-update` Slack posting, add to `~/.slack-config.yaml`:
```yaml
user_token: xoxp-...
update_channel_id: C0ABC123  # optional, will prompt on first use
```

## Claude Code Commands

### /thb-flow

Start work on a Jira story:
```
/thb-flow HB-123
```

Validates the issue, assigns it to you, transitions to "In Progress", and creates or switches to a feature branch.

### /thb-update

Post a progress update to Jira (and optionally Slack):
```
/thb-update
```

Extracts the Jira key from your branch name, summarizes changes since the last update, and posts a formatted comment with SHA tracking for incremental updates.

## CLI Tools

| Command | Description |
|---------|-------------|
| `jira-read HB-123` | Get issue details as JSON |
| `jira-update HB-123 -m "comment"` | Add comment to issue |
| `jira-update HB-123 -s "In Progress"` | Change issue status |
| `jira-update HB-123 --assign` | Assign issue to yourself |
| `jira-users` | List all Jira users with account IDs |
| `jira-latest-comment HB-123` | Get SHA from latest THB Automated Summary |
| `jira-link HB-123 HB-456` | Link two Jira issues |
| `jira-migrate HB-123 HA` | Migrate/clone an issue to another project |
| `slack-update C01234567 "message"` | Post message to Slack channel |
| `slack-users` | Fetch users to `~/.slack-users.json` |
| `slack-channels` | Fetch channels to `~/.slack-channels.json` |
| `slack-remind "text" --time ISO8601` | Create a Slack reminder |
| `slack-history C01234567 --days 2` | Fetch channel history as JSON |

## License

MIT License - See LICENSE file for details.
