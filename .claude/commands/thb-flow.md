# THB Flow - Begin Work on Jira Story

This command helps you begin work on a Jira story by ensuring everything is in the correct state.

## User Input
$ARGUMENTS

## Workflow

When invoked, follow this workflow to prepare for working on a Jira story:

### 1. Parse Issue Key

Extract the Jira issue key (e.g., HB-7162) from the user's input: "$ARGUMENTS"

If no issue key is found, ask the user to provide one. Note: Creating new stories is not currently supported - the story must already exist in Jira.

### 2. Validate the Story

Fetch the issue from Jira using:
```bash
jira-read {issue_key}
```

This returns JSON with fields: key, summary, description, status, issuetype, assignee, etc.

**Validation rules:**
- If the issue type is **Epic**, reject with message: "Epics cannot be worked on directly. Please select a Story, Task, Bug, or Subtask within the Epic."
- If the status is **Done** or **Accepted**, reject with message: "This issue is already completed (status: {status}). Please select an active issue."

### 3. Handle Assignment

Determine the current user:
1. Read email from `~/.jira-config.yaml`
2. Check for cached users at `/tmp/jira-users-cache.json`
3. If cache doesn't exist or user not found, run `jira-users` and save output to `/tmp/jira-users-cache.json`
4. Look up the account ID by matching the email

**Assignment logic:**
- If issue is unassigned → assign to current user using `jira-update {issue} --assign`
- If assigned to current user → proceed (no action needed)
- If assigned to someone else → warn the user: "This issue is currently assigned to {assignee_name}. Would you like to reassign it to yourself?" Wait for confirmation before reassigning.

### 4. Update Jira Status

If the issue status is not "In Progress":
- Use `jira-update {issue} --status "In Progress"` to transition the issue
- Inform the user of the status change

### 5. Check for Uncommitted Changes

Before switching or creating branches, check for uncommitted changes:
```bash
git status --porcelain
```

**If there are uncommitted changes (output is not empty):**
- Abort the workflow
- Inform the user: "You have uncommitted changes on the current branch. Please commit or stash your changes before starting work on a new story."
- List the modified files so the user knows what needs attention
- Do NOT proceed with branch operations

**If working tree is clean:**
- Proceed to step 6

### 6. Handle Git Branch

**Branch naming convention:**
- Story, Task, Subtask → `feature/{issue_key}` (e.g., `feature/HB-7162`)
- Bug → `bug/{issue_key}` (e.g., `bug/HB-7162`)

**Branch logic:**
1. Check if a branch containing the issue key already exists:
   ```bash
   git branch -a | grep {issue_key}
   ```

2. If branch exists:
   - Switch to it: `git checkout {branch_name}`
   - Inform the user: "Switched to existing branch: {branch_name}"

3. If no branch exists:
   - Propose the branch name and base branch (default: main)
   - Ask for confirmation: "Create branch '{branch_name}' from 'main'?"
   - On confirmation: `git checkout -b {branch_name} main`
   - Inform the user: "Created and switched to branch: {branch_name}"

### 7. Present the Story

After setup is complete:

1. Display the issue details:
   - Issue key and summary
   - Description (formatted for readability)
   - Current status and assignee

2. Check for relevant linked issues (parent epic, related stories, blockers) and mention them if they provide useful context.

3. Offer to discuss the implementation:
   - "I've read the story details above. How would you like to approach this? I can help you:"
   - "- Explore the codebase to understand relevant areas"
   - "- Discuss implementation options"
   - "- Break down the work into smaller tasks"
   - "- Start implementing right away"

4. Gather information through discussion to fully understand the request and desired approach before beginning implementation.

## Available Tools

- `jira-read {issue}` - Fetch issue details (JSON output)
- `jira-update {issue} --message "text"` - Add comment to issue
- `jira-update {issue} --status "Status"` - Change issue status
- `jira-update {issue} --assign` - Assign to self
- `jira-update {issue} --assign {account_id}` - Assign to specific user
- `jira-users` - List all Jira users (JSON output)
- `jira-users --pretty` - List all Jira users (table format)

## Notes

- Always inform the user when making changes (branch creation, status changes, assignments)
- The code and CLAUDE.md files are the source of truth for understanding the current system state
- Ask clarifying questions to fully understand the approach before implementing
