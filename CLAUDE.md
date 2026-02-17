# Claude Code Project Context

This project provides CLI tools for Jira and Slack integration, plus Claude Code commands for workflow automation.

## Directory Structure

```
claude-utils/
├── jira_update/          # Jira CLI tools
│   ├── cli.py            # jira-update command
│   ├── read.py           # jira-read command
│   ├── users.py          # jira-users command
│   ├── latest_comment.py # jira-latest-comment command
│   ├── client.py         # Jira API client
│   └── config.py         # Credential loading
├── slack_update/         # Slack CLI tools
│   ├── cli.py            # slack-update command
│   ├── channels.py       # slack-channels command
│   ├── users.py          # slack-users command
│   ├── client.py         # Slack API client
│   └── config.py         # Credential loading
├── slack_reminder/       # Slack reminder tool
│   ├── cli.py            # slack-remind command
│   ├── scanner.py        # Reminder API client
│   └── config.py         # Credential loading
├── slack_scan/           # Slack channel scanner
│   ├── cli.py            # slack-history command
│   ├── client.py         # History/thread API client
│   └── config.py         # Channel list + credential loading
├── .claude/
│   └── commands/         # Claude Code slash commands
│       ├── thb-flow.md   # /thb-flow command
│       └── thb-update.md # /thb-update command
└── pyproject.toml        # Package configuration
```

## Jira CLI Tools

### jira-read

Fetch Jira issue details as JSON.

```bash
jira-read HB-123
```

**Output fields:** key, summary, description, status, issuetype, assignee, reporter, parent, linked_issues, created, updated

**Use with jq:**
```bash
jira-read HB-123 | jq '.description'
jira-read HB-123 | jq '.status'
```

### jira-update

Update Jira issues with comments, status changes, and assignments.

**Add a comment:**
```bash
jira-update HB-123 --message "Fixed the bug"
jira-update HB-123 -m "Fixed the bug"
```

**Change status:**
```bash
jira-update HB-123 --status "In Progress"
jira-update HB-123 -s "Done"
```

**Valid statuses:** To Do, In Progress, QA, Code Review, Accepted, Done

**Assign to yourself:**
```bash
jira-update HB-123 --assign
```

**Assign to specific user:**
```bash
jira-update HB-123 --assign 712020:abc123-def456
```

**Add rich comment with @mentions (ADF format):**
```bash
jira-update HB-123 --adf --message '[{"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"Summary"}]},{"type":"paragraph","content":[{"type":"mention","attrs":{"id":"account_id","text":"@Name","accessLevel":""}},{"type":"text","text":" reviewed this."}]}]'
```

**Get JSON output:**
```bash
jira-update HB-123 -m "comment" --json
```

**Note:** `--assign` must be used alone (cannot combine with `--message` or `--status`).

### jira-users

List all active Jira users with account IDs.

```bash
jira-users          # JSON output
jira-users --pretty # Human-readable table
```

**Output fields:** display_name, email, account_id

Use this to look up account IDs for `jira-update --assign` or ADF mentions.

### jira-latest-comment

Find the SHA from the latest THB Automated Summary comment on an issue.

```bash
jira-latest-comment HB-123
```

**Output:** JSON with `sha` field (either from previous summary or git merge-base with main/master)

Used by `/thb-update` to determine what changes to summarize.

## Slack CLI Tools

### slack-update

Post messages to Slack channels.

```bash
slack-update C01234567 "Build completed successfully"
slack-update C01234567 "Hello team" --pretty
```

**Arguments:**
- First arg: Channel ID (find via Slack UI: right-click channel > View details > scroll to bottom)
- Second arg: Message text (supports Slack mrkdwn: `*bold*`, `_italic_`, `` `code` ``)

**Flags:**
- `--pretty` - Human-readable output instead of JSON
- `--auth` - Run OAuth flow for first-time setup

### slack-users

Fetch all Slack workspace users and save to `~/.slack-users.json`.

```bash
slack-users
```

### slack-channels

Fetch all accessible Slack channels and save to `~/.slack-channels.json`.

```bash
slack-channels
slack-channels --cursor "abc123"  # Resume from pagination cursor
```

### slack-remind

Create a Slack reminder directly via the API.

```bash
slack-remind "Order books for the team" --time 2026-02-16T08:00:00-05:00
slack-remind "Talk to Angela" --time 2026-02-17T09:00:00-05:00 --json
```

### slack-history

Fetch Slack channel history as JSON for analysis.

```bash
slack-history C01234567 --days 2              # Single channel, 2 days back
slack-history C01234567 --oldest 2026-02-14   # Single channel, from specific date
slack-history --all --days 1                  # All channels from ~/.slack-scan.yaml
slack-history --all --days 3 --no-threads     # Skip thread replies
```

**Config:** `~/.slack-scan.yaml` with channel list for `--all` mode:
```yaml
channels:
  - id: "C01234567"
    name: "engineering"
  - id: "C09876543"
    name: "general"
```

**Required Slack scopes:** `channels:history`, `groups:history`, `users:read`

## Claude Code Commands

### /thb-flow

Start work on a Jira story. Run this when beginning a new task.

```
/thb-flow HB-123
```

**What it does:**
1. Validates the issue exists and is workable (rejects Epics, completed issues)
2. Assigns the issue to you (if unassigned, or prompts if assigned to someone else)
3. Transitions to "In Progress" status
4. Creates or switches to a feature branch (`feature/HB-123` or `bug/HB-123`)
5. Displays story details and offers to help with implementation

**Requires:** Clean working tree (no uncommitted changes)

### /thb-update

Post a progress update to Jira summarizing recent work. Optionally posts to Slack if configured.

```
/thb-update
/thb-update commits    # Include commit messages in analysis
/thb-update --no-slack # Skip Slack posting even if configured
```

**What it does:**
1. Extracts Jira issue key from current branch name
2. Finds changes since last THB Automated Summary (or merge-base if first update)
3. Generates a non-technical summary focused on outcomes
4. Optionally includes pairing partner @mentions
5. Previews the update for approval before posting
6. Posts formatted comment with SHA tracking for incremental updates
7. If Slack is configured, asks to post the same update to Slack (with Slack @mentions)

**Slack Integration:**
- Automatically detects Slack configuration (`user_token` in `~/.slack-config.yaml` or `SLACK_USER_TOKEN` env var)
- Prompts for target channel on first use (saves to `update_channel_id` in config)
- Maps Jira @mentions to Slack @mentions by matching email addresses
- Use `--no-slack` to skip Slack posting
- Slack failures are non-fatal (Jira update is primary)

**Requires:** All changes committed (uses SHA tracking)

## User Caching

Both `/thb-flow` and `/thb-update` cache Jira users at `/tmp/jira-users-cache.json` for efficiency. The cache is refreshed automatically when a user lookup fails.

## Configuration

See README.md for setup instructions. Tools expect:
- Jira: `~/.jira-config.yaml` with email and api_token
- Slack: `~/.slack-config.yaml` with client_id and client_secret, then `slack-update --auth`

### Slack Configuration for /thb-update

To enable Slack posting in `/thb-update`, ensure your `~/.slack-config.yaml` has:

```yaml
user_token: xoxp-...        # Required - obtained via slack-update --auth
update_channel_id: C0ABC123 # Optional - will prompt on first use if missing
```

Or use environment variables:
- `SLACK_USER_TOKEN` - Slack API token
- `SLACK_UPDATE_CHANNEL_ID` - Target channel ID (overrides config file)
