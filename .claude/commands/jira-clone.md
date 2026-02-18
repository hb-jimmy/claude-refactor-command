# Jira Clone - Clone an Issue to Another Project

Clone a Jira issue (story, task, bug, or epic) to a target project, preserving all fields, links, and comments.

## User Input
$ARGUMENTS

## Arguments

Parse the arguments from "$ARGUMENTS":
- **First argument** (required): Source issue key (e.g., `HB-7162`)
- **Second argument** (required): Target project key (e.g., `HA`)
- **`--sprint "Sprint Name"`** (optional): Place the cloned issue in a specific sprint

If either required argument is missing, show usage:
```
Usage: /jira-clone <source-issue> <target-project> [--sprint "Sprint Name"]

Examples:
  /jira-clone HB-7162 HA
  /jira-clone HB-7162 HA --sprint "HA Sprint 0"
```

## Workflow

### 1. Fetch Source Issue

Use the Jira MCP tools to fetch the source issue with all fields:
- summary, description, status, issuetype, labels, reporter, assignee, issuelinks, comment, parent

Use the Atlassian cloud ID: `633ab2e7-1cc1-4ac4-821a-5a3016daa85c`

Display a summary of what will be cloned:
```
Cloning: HB-7162 (Bug) → HA
  Summary: <summary>
  Status: <status>
  Reporter: <name> | Assignee: <name or None>
  Labels: [label1, label2]
  Parent: <parent key and summary, or None>
  Links: <count> | Comments: <count>
```

### 2. Handle Parent Epic

**If the source issue has a parent epic:**

1. Fetch the parent epic's issue links to check for Cloners links from the target project
2. Look for a Cloners link where an issue in the target project clones the source parent epic
3. If found: use that target-project epic as the parent for the cloned issue
4. If NOT found: **stop** and tell the user:
   ```
   The parent epic <HB-XXX> (<summary>) has not been cloned to <target project> yet.
   Clone it first with:
     /jira-clone <parent-epic-key> <target-project>
   Then re-run this command.
   ```

**If the source issue has no parent:** proceed without a parent.

### 3. Create the Issue

Create the issue in the target project using the Jira MCP `createJiraIssue` tool:
- **projectKey**: target project
- **issueTypeName**: same as source (Task, Bug, Story, Epic)
- **summary**: same as source
- **description**: same as source (markdown format)
- **parent**: the target epic found in step 2 (omit if none)
- **additional_fields.labels**: same as source

If `--sprint` was specified:
- Find the sprint ID by querying an issue in that sprint: search with JQL `project = <target> AND sprint = "<sprint name>"` (maxResults=1)
- Read the `customfield_10008` field from that issue to get the sprint ID
- Add `customfield_10008: <sprint_id>` (as a number) to additional_fields

Report the created issue key: `Created: <new-key>`

### 4. Set Reporter

Use `editJiraIssue` to set the reporter's accountId to match the source issue.
If this fails (e.g., deactivated user), warn and continue.

### 5. Set Assignee

If the source issue has an assignee, use `editJiraIssue` to set the assignee's accountId.
If this fails, warn and continue.

### 6. Transition Status

Map the source status to the target status:

| Source Status | Target Status |
|---|---|
| To Do | To Do (no transition needed) |
| In Progress | In Progress |
| Blocked | Blocked |
| Done | Done |

**Any other status** (QA, Code Review, Accepted, "SMH not doing this", etc.) → **To Do** (no transition needed).

Use `getTransitionsForJiraIssue` on the new issue to find available transitions, then `transitionJiraIssue` to execute.

For **Blocked**: transition to In Progress first, then to Blocked (two-step).

### 7. Create Links

**Always create a Cloners link:** the new issue clones the source issue.
```bash
jira-link --type Cloners --outward <new-key> --inward <source-key>
```

**Recreate all other links** from the source issue, preserving direction:
- For each link on the source issue, create the same link type between the new issue and the linked issue
- Link types to recreate: Relates, Blocks, "Polaris work item link", and any others present
- Skip any "Parent-Child" links (parent is handled separately in step 2)
- Skip any Cloners links that point back to the source issue (already handled above)
- If a link creation fails, warn and continue

### 8. Copy Comments

Fetch all comments from the source issue. For each comment (oldest first):

Post to the new issue using `addCommentToJiraIssue` with attributed text:
```
**Originally posted by <author name> on <YYYY-MM-DD HH:MM>:**

<original comment body>
```

If a comment fails to copy (e.g., contains unsupported attachments), warn and continue.

### 9. Summary

Display the final result:
```
Done! Cloned <source-key> → <new-key>
  Parent: <target epic or "None">
  Sprint: <sprint name or "None">
  Status: <target status>
  Links: <count> created
  Comments: <count> copied
```

## Available Tools

Use the Jira MCP tools (Atlassian cloud ID: `633ab2e7-1cc1-4ac4-821a-5a3016daa85c`):
- `getJiraIssue` — fetch issue details
- `createJiraIssue` — create new issue
- `editJiraIssue` — update fields (reporter, assignee)
- `getTransitionsForJiraIssue` — get available status transitions
- `transitionJiraIssue` — change status
- `searchJiraIssuesUsingJql` — search for issues (sprint lookup, etc.)
- `addCommentToJiraIssue` — add comment

Use CLI tools:
- `jira-link --type <type> --outward <key> --inward <key>` — create issue links
- `jira-read <key>` — fetch issue as JSON (alternative to MCP)

## Notes

- Always warn but continue on non-critical failures (reporter, assignee, individual links, individual comments)
- Only stop on critical failures (issue creation failed, parent epic not found in target)
- The command works for all issue types including Epics (epics are cloned without their children)
