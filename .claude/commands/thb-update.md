# THB Update - Post Progress Update to Jira

This command helps you summarize changes on the current branch and publish an update to the associated Jira ticket.

## User Input
$ARGUMENTS

## Workflow

When invoked, follow this checklist workflow to post a progress update:

### 1. Identify Jira Issue

Extract the Jira issue key from the current git branch name:
```bash
git branch --show-current
```

Look for a pattern matching `[A-Z]+-[0-9]+` (e.g., HB-7162, PROJ-123) anywhere in the branch name.

**If no issue key is found:**
- Ask the user: "I couldn't find a Jira issue key in the branch name '{branch_name}'. What Jira issue should this update be posted to?"
- Wait for user input before proceeding.

**Validate the issue exists:**
```bash
jira-read {issue_key}
```

If the issue doesn't exist, inform the user and abort.

### 2. Verify Issue Status

Check the issue status from the jira-read output.

**If status is "To Do", "Backlog", or "Open":**
- Prompt the user: "This issue is currently in '{status}' status. Would you like me to move it to 'In Progress' and assign it to you?"
- If yes:
  - Determine current user (see step 4)
  - Run: `jira-update {issue_key} --status "In Progress"`
  - Run: `jira-update {issue_key} --assign`
- If no, proceed without changing status.

**If status is "Done" or "Accepted":**
- Warn: "This issue is marked as '{status}'. Are you sure you want to post an update?"
- If no, abort.

### 3. Check for Uncommitted Changes

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
- Proceed to step 4

### 4. Find Last THB Update SHA

Get the SHA to use as the starting point for the summary:
```bash
jira-latest-comment {issue_key}
```

This returns JSON with a SHA:
- If a previous "THB Automated Summary" comment exists, returns that commit SHA
- If no previous comment exists, returns the merge-base SHA with main/master

Store this SHA for use in step 6.

### 5. Identify Current User

Determine the current user for assignment and display:

1. Read email from `~/.jira-config.yaml`
2. Check for cached users at `/tmp/jira-users-cache.json`
3. If cache doesn't exist or user not found:
   - Run `jira-users` and save output to `/tmp/jira-users-cache.json`
4. Look up the account ID by matching the email from the config

Store the user's `account_id` and `display_name` for later use.

### 6. Identify Pairing Partners

**Ask the user:**
"Are you pairing with anyone on this work?"

**If no:** Continue to step 7 (no pairing section will be included in the update).

**If yes:**

1. Check commit authors for potential pairing partners (commits since the SHA from step 4):
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

5. Store each partner's `account_id` and `display_name` for the comment.

### 7. Generate Change Summary

**Get the current HEAD SHA (short form):**
```bash
git rev-parse --short HEAD
```

Store this as `{current_sha}` for the comment header.

**Get the code diff since the last update:**
```bash
git diff {sha_from_step_4}..HEAD
```

**If user included "commits" in $ARGUMENTS:**
Also gather commit messages:
```bash
git log {sha_from_step_4}..HEAD --format='%s%n%b' --no-merges
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

### 8. Preview and Approve

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

### 9. Post Update to Jira

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

**On failure:**
- Display the error message
- Offer to retry or save the comment for manual posting

## Available Tools

- `jira-read {issue}` - Fetch issue details (JSON output)
- `jira-update {issue} --message "text"` - Add plain text comment
- `jira-update {issue} --message '{adf_json}' --adf` - Add rich comment with ADF format
- `jira-update {issue} --status "Status"` - Change issue status
- `jira-update {issue} --assign` - Assign to self
- `jira-users` - List all Jira users (JSON output)
- `jira-latest-comment {issue}` - Get SHA from latest THB Automated Summary (JSON output)
- `git diff {sha}..HEAD` - Get diff since a specific commit
- `git log {sha}..HEAD` - Get commit history since a specific commit
- `git rev-parse --short HEAD` - Get current HEAD short SHA

## Notes

- All changes must be committed before generating a summary (SHA tracking)
- The header format is "THB Automated Summary: {sha}" to identify and track updates
- The Pairing section is omitted entirely when working solo (not shown as empty)
- Summaries should be non-technical and focus on what was achieved
- Always get user approval before posting
- Use the cached user data at `/tmp/jira-users-cache.json` for efficiency
- Refresh the cache with `jira-users` only when a user cannot be found
- Subsequent updates only summarize changes since the last THB Automated Summary
