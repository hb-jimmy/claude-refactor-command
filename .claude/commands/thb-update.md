# THB Update - Post Progress Update to Jira

This command helps you summarize changes on the current branch and publish an update to the associated Jira ticket. If Slack is configured, it can also post the same update to a Slack channel.

## User Input
$ARGUMENTS

**Supported flags:**
- `commits` - Include commit messages in analysis
- `--no-slack` - Skip Slack posting even if configured
- `--purge-cache` - Remove stale entries (older than 2 weeks) from the Jira issue cache

## Workflow

When invoked, follow this checklist workflow to post a progress update:

### 1. Detect Slack Configuration

Check if Slack is configured for posting updates. Slack is considered configured if a `user_token` is available.

**Check for user token:**
1. Check environment variable `SLACK_USER_TOKEN`
2. Check `~/.slack-config.yaml` for `user_token` field

**If user token is found AND `--no-slack` is NOT in $ARGUMENTS:**
- Set `slack_enabled = true`
- Proceed to check channel configuration (step 1b)

**If user token is NOT found OR `--no-slack` is in $ARGUMENTS:**
- Set `slack_enabled = false`
- Skip to step 2

#### 1b. Check Slack Channel Configuration

**Check for channel ID:**
1. Check environment variable `SLACK_UPDATE_CHANNEL_ID`
2. Check `~/.slack-config.yaml` for `update_channel_id` field

**If channel ID is found:**
- Store as `slack_channel_id`
- Proceed to step 2

**If channel ID is NOT found:**
- Ask the user: "Slack is configured but no update channel is set. What Slack channel should updates be posted to? (e.g., #team-updates)"
- Wait for user input (they should provide a channel name like `#test-channel` or `test-channel`)

**Look up channel ID from name:**
1. Strip leading `#` from the channel name if present
2. Check cached channels at `~/.slack-channels.json`:
   - Load the file and search the `channels` array for a matching `name`
   - If found, use the `id` field
3. If not found in cache or cache doesn't exist:
   - Run `slack-channels` to fetch and cache all channels
   - Search the updated `~/.slack-channels.json` for the channel name
4. If still not found:
   - Inform the user: "Could not find channel '{name}'. Please verify the channel name and ensure you have access."
   - Set `slack_enabled = false` and proceed without Slack

**Save channel ID to config:**
Once the channel ID is resolved, save it to `~/.slack-config.yaml` for future use:
1. Read existing `~/.slack-config.yaml` content
2. Add/update the `update_channel_id` field with the resolved ID
3. Write back to the file (preserve other fields like `client_id`, `client_secret`, `user_token`)

Store the `slack_channel_id` for step 10.

### 2. Handle Cache Purge (if requested)

**If `--purge-cache` is in $ARGUMENTS OR user verbally requested to purge:**

1. Load `~/.jira-issue-cache.json` if it exists
2. Calculate the cutoff timestamp (current time minus 2 weeks)
3. Remove all entries where `timestamp` is older than the cutoff
4. Save the updated cache file
5. Inform the user: "Purged {count} stale cache entries older than 2 weeks."

### 3. Identify Jira Issue

**Step 3a: Get current repo and branch:**
```bash
git rev-parse --show-toplevel  # Get repo root path
git branch --show-current       # Get branch name
```

Combine these to create a cache key: `{repo_path}:{branch_name}`

**Step 3b: Check the Jira issue cache:**

Load `~/.jira-issue-cache.json` if it exists. This file has the structure:
```json
{
  "entries": {
    "/path/to/repo:branch-name": {
      "issue_key": "HB-7162",
      "issue_summary": "Test for jira integration",
      "timestamp": "2026-02-04T10:30:00Z"
    }
  }
}
```

**If a cache entry exists for the current repo+branch:**
- Store the cached `issue_key`
- Inform the user: "Using cached Jira issue {issue_key} for branch '{branch_name}'"

**Step 3c: Check if user provided an issue in $ARGUMENTS:**

Look for a pattern matching `[A-Z]+-[0-9]+` (e.g., HB-7162, PROJ-123) in $ARGUMENTS.

**If user provided an issue AND it differs from cached issue:**
- Warn the user: "The cached issue for this branch is {cached_issue}, but you specified {provided_issue}. Do you want to update the cache to use {provided_issue}?"
- If yes: Use the provided issue and update cache (step 3f)
- If no: Use the cached issue

**If user provided an issue AND no cache exists (or matches):**
- Use the provided issue

**Step 3d: Check branch name for issue key:**

If no issue determined yet, look for a pattern matching `[A-Z]+-[0-9]+` in the branch name.

**Step 3e: Prompt user if no issue found:**

If still no issue determined:
- Ask the user: "I couldn't find a Jira issue key in the branch name '{branch_name}'. What Jira issue should this update be posted to?"
- Wait for user input before proceeding.

**Step 3f: Validate and cache the issue:**

```bash
jira-read {issue_key}
```

If the issue doesn't exist, inform the user and abort.

**Save to cache:**
1. Load existing `~/.jira-issue-cache.json` (or create empty structure)
2. Add/update entry for current cache key:
   ```json
   {
     "issue_key": "{issue_key}",
     "issue_summary": "{summary from jira-read}",
     "timestamp": "{current ISO timestamp}"
   }
   ```
3. Write back to `~/.jira-issue-cache.json`

### 4. Verify Issue Status

Check the issue status from the jira-read output.

**If status is "To Do", "Backlog", or "Open":**
- Prompt the user: "This issue is currently in '{status}' status. Would you like me to move it to 'In Progress' and assign it to you?"
- If yes:
  - Determine current user (see step 7)
  - Run: `jira-update {issue_key} --status "In Progress"`
  - Run: `jira-update {issue_key} --assign`
- If no, proceed without changing status.

**If status is "Done" or "Accepted":**
- Warn: "This issue is marked as '{status}'. Are you sure you want to post an update?"
- If no, abort.

### 5. Check for Uncommitted Changes

Before generating a summary, ensure all changes are committed:
```bash
git status --porcelain
```

**If there are uncommitted changes (output is not empty):**
- Inform the user: "You have uncommitted changes. All changes must be committed before posting an update so we can track the commit SHA."
- List the modified files
- Ask: "Would you like me to help you commit these changes?"
  - If yes: Help the user create a commit (gather commit message, stage files, commit)
  - If no: Abort the workflow with message "Please commit your changes and run /thb-update again."

**If working tree is clean:**
- Proceed to step 6

### 6. Find Last THB Update SHA

Get the SHA to use as the starting point for the summary:
```bash
jira-latest-comment {issue_key}
```

This returns JSON with a SHA:
- If a previous "THB Automated Summary" comment exists, returns that commit SHA
- If no previous comment exists, returns the merge-base SHA with main/master

Store this SHA for use in step 9.

### 7. Identify Current User

Determine the current user for assignment and display:

1. Read email from `~/.jira-config.yaml`
2. Check for cached users at `/tmp/jira-users-cache.json`
3. If cache doesn't exist or user not found:
   - Run `jira-users` and save output to `/tmp/jira-users-cache.json`
4. Look up the account ID by matching the email from the config

Store the user's `account_id` and `display_name` for later use.

### 8. Identify Pairing Partners

**Ask the user:**
"Are you pairing with anyone on this work?"

**If no:** Continue to step 9 (no pairing section will be included in the update).

**If yes:**

1. Check commit authors for potential pairing partners (commits since the SHA from step 6):
   ```bash
   git log {sha}..HEAD --format='%ae' | sort -u
   ```

2. If commits from other authors are found, suggest them: "I found commits from {emails}. Are any of these your pairing partners?"

3. Ask the user to enter pairing partner name(s), email(s), or username(s). They can enter multiple separated by commas.

4. For each partner entered:
   - Load the user cache from `/tmp/jira-users-cache.json`
   - Search for matches by display_name, email, or partial match
   - If multiple matches found, list them and ask the user to select
   - If no match found:
     - Run `jira-users` to refresh the cache
     - Search again
     - If still not found, abort with error: "Could not find Jira user matching '{input}'. Please verify the name/email."

5. Store each partner's `account_id`, `display_name`, and `email` for the comment (email is needed for Slack user matching).

### 9. Generate Change Summary

**Get the current HEAD SHA (short form):**
```bash
git rev-parse --short HEAD
```

Store this as `{current_sha}` for the comment header.

**Get the code diff since the last update:**
```bash
git diff {sha_from_step_6}..HEAD
```

**If user included "commits" in $ARGUMENTS:**
Also gather commit messages:
```bash
git log {sha_from_step_6}..HEAD --format='%s%n%b' --no-merges
```

**Generate a user-facing summary:**

Analyze the diff and create a summary that:
- Focuses on WHAT was achieved, not HOW it was implemented
- Is readable by non-technical stakeholders
- Describes outcomes, capabilities added, problems solved, or behaviors changed
- May reference technical concepts but emphasizes results over implementation details
- Does NOT include file lists or progress indicators

**Format the summary with:**
1. A brief one-line header summarizing the changes
2. A detailed multi-paragraph description

### 10. Preview and Approve

Display the formatted comment to the user:

**With pairing:**
```
## THB Automated Summary: {current_sha}
### {brief_header}
Pairing: @{partner1_display_name}, @{partner2_display_name}

{detailed_description}
```

**Without pairing (solo work):**
```
## THB Automated Summary: {current_sha}
### {brief_header}

{detailed_description}
```

**Ask for approval:**
"Here's the update I'll post to {issue_key}. Would you like me to:
1. Post this update
2. Edit the update (tell me what to change)
3. Cancel"

If the user wants to edit, make the requested changes and preview again.

### 11. Post Update to Jira

Build the ADF JSON content array:

**With pairing partners:**
```json
[
  {"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"THB Automated Summary: {current_sha}"}]},
  {"type":"heading","attrs":{"level":3},"content":[{"type":"text","text":"{brief_header}"}]},
  {"type":"paragraph","content":[{"type":"text","text":"Pairing: "},{"type":"mention","attrs":{"id":"{partner1_account_id}","text":"@{partner1_display_name}","accessLevel":""}},{"type":"text","text":", "},{"type":"mention","attrs":{"id":"{partner2_account_id}","text":"@{partner2_display_name}","accessLevel":""}}]},
  {"type":"paragraph","content":[{"type":"text","text":"{paragraph1}"}]},
  {"type":"paragraph","content":[{"type":"text","text":"{paragraph2}"}]}
]
```

**Without pairing (solo):**
```json
[
  {"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"THB Automated Summary: {current_sha}"}]},
  {"type":"heading","attrs":{"level":3},"content":[{"type":"text","text":"{brief_header}"}]},
  {"type":"paragraph","content":[{"type":"text","text":"{paragraph1}"}]},
  {"type":"paragraph","content":[{"type":"text","text":"{paragraph2}"}]}
]
```

**Post the comment:**
```bash
jira-update {issue_key} --adf --message '{adf_json}'
```

**On success:**
- Inform the user: "Update posted to {issue_key}: {issue_summary}"
- Provide a link to the issue if possible
- Proceed to step 12 (Slack posting)

**On failure:**
- Display the error message
- Offer to retry or save the comment for manual posting
- If user cancels retry, skip Slack posting

### 12. Post Update to Slack (if enabled)

**If `slack_enabled` is false:**
- Skip this step entirely, workflow is complete

**If `slack_enabled` is true:**

#### 12a. Confirm Slack Posting

Ask the user: "Would you also like to post this update to Slack?"

**If no:** Skip Slack posting, workflow is complete.

**If yes:** Proceed to step 12b.

#### 12b. Resolve Slack User Mentions for Pairing Partners

**If there are pairing partners:**

For each partner, find their corresponding Slack user by email:

1. Load cached Slack users from `~/.slack-users.json`
2. Search for a user with matching `email` field (case-insensitive)
3. If found, store the Slack user's `id` for mention formatting

**If email match is not found:**
1. Run `slack-users` to refresh the cache
2. Search again
3. If still not found by exact email match, search for similar users:
   - Look for partial name matches in `display_name` or `real_name`
   - Present up to 3 closest matches to the user
   - Ask: "I couldn't find a Slack user with email '{email}'. Did you mean one of these?"
   - If user selects a match, use that Slack user ID
   - If user says none match or skips, omit that partner from Slack mentions

Store each resolved Slack user ID for formatting.

#### 12c. Format Slack Message

Build the Slack message using mrkdwn format:

**With pairing partners (where Slack IDs were resolved):**
```
*THB Automated Summary: {current_sha}*
*{brief_header}*
Pairing: <@{slack_user_id1}>, <@{slack_user_id2}>

{detailed_description}

<https://{jira_domain}.atlassian.net/browse/{issue_key}|{issue_key}: {issue_summary}>
```

**Without pairing or no Slack IDs resolved:**
```
*THB Automated Summary: {current_sha}*
*{brief_header}*

{detailed_description}

<https://{jira_domain}.atlassian.net/browse/{issue_key}|{issue_key}: {issue_summary}>
```

Note: Slack @mentions use the format `<@USER_ID>` (e.g., `<@U01234567>`).
Note: Slack links use the format `<URL|display text>`. The Jira domain can be extracted from `~/.jira-config.yaml` (e.g., `thehelperbees` from `thehelperbees.atlassian.net`).

#### 12d. Post to Slack

```bash
slack-update {slack_channel_id} "{slack_message}"
```

**On success:**
- Inform the user: "Update also posted to Slack"
- Workflow is complete

**On failure:**
- Display the error message but DO NOT fail the workflow
- Inform the user: "Slack posting failed, but the Jira update was successful: {error}"
- Workflow is complete (Jira update is the primary success criteria)

## Available Tools

### Jira Tools
- `jira-read {issue}` - Fetch issue details (JSON output)
- `jira-update {issue} --message "text"` - Add plain text comment
- `jira-update {issue} --message '{adf_json}' --adf` - Add rich comment with ADF format
- `jira-update {issue} --status "Status"` - Change issue status
- `jira-update {issue} --assign` - Assign to self
- `jira-users` - List all Jira users (JSON output)
- `jira-latest-comment {issue}` - Get SHA from latest THB Automated Summary (JSON output)

### Slack Tools
- `slack-update {channel_id} "message"` - Post message to Slack channel
- `slack-channels` - Fetch and cache Slack channels to `~/.slack-channels.json`
- `slack-users` - Fetch and cache Slack users to `~/.slack-users.json`

### Git Tools
- `git diff {sha}..HEAD` - Get diff since a specific commit
- `git log {sha}..HEAD` - Get commit history since a specific commit
- `git rev-parse --short HEAD` - Get current HEAD short SHA

## Configuration Files

### Jira
- `~/.jira-config.yaml` - Contains `email` and `api_token`
  - Jira domain for URLs is derived from the email domain (e.g., `user@thehelperbees.com` → `thehelperbees.atlassian.net`)
- `~/.jira-issue-cache.json` - Maps repo+branch to Jira issue (prevents updating wrong ticket)
  - Entries older than 2 weeks can be purged with `--purge-cache`
- `/tmp/jira-users-cache.json` - Cached Jira users

### Slack
- `~/.slack-config.yaml` - Contains:
  - `user_token` - Slack API token (required for Slack integration)
  - `update_channel_id` - Target channel for updates (saved after first prompt)
  - `client_id`, `client_secret` - OAuth credentials (for initial setup)
- `~/.slack-channels.json` - Cached Slack channels
- `~/.slack-users.json` - Cached Slack users

### Environment Variables (override config files)
- `SLACK_USER_TOKEN` - Slack API token
- `SLACK_UPDATE_CHANNEL_ID` - Target channel ID for updates

## Notes

- All changes must be committed before generating a summary (SHA tracking)
- The header format is "THB Automated Summary: {sha}" to identify and track updates
- The Pairing section is omitted entirely when working solo (not shown as empty)
- Summaries should be non-technical and focus on what was achieved
- Always get user approval before posting to Jira
- Slack posting requires separate confirmation after Jira is posted
- Use `--no-slack` flag to skip Slack posting entirely
- Slack failures are non-fatal - Jira update is the primary success criteria
- Use the cached user data at `/tmp/jira-users-cache.json` for efficiency
- Refresh the cache with `jira-users` only when a user cannot be found
- Subsequent updates only summarize changes since the last THB Automated Summary
- When matching Jira users to Slack users for mentions, match by email address
- If email match fails, suggest closest name matches and confirm with user
- Jira issue is cached per repo+branch to prevent accidentally updating the wrong ticket
- Use `--purge-cache` to remove stale cache entries older than 2 weeks
