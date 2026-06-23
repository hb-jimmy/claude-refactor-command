# Summarize Standups

Process all unprocessed standup meeting transcripts and publish summaries.

## Arguments

No arguments. Processes all standup meetings (hA, CoPo, and combined Friday standups).

## Team Rosters

Use these rosters to identify which team members are speaking and to split combined transcripts:

- **homeAlign (hA):** Anthony, Matthew Adams, Van, Cory, Hilary, Deepi
- **Consumer Portal (CoPo):** Phil, Corey, Elias, Stephen

## Instructions

Follow these steps in order:

### Step 1: Fetch latest transcripts

Run the following command to download any new transcripts for all standup meetings:

```bash
fathom-transcripts --config ~/.standups/config.yaml fetch
```

### Step 2: Find unprocessed transcripts

For each meeting configured in `~/.standups/config.yaml` (ha, copo, combined):

1. List all files in `~/.standups/transcripts/<name>/` (where `<name>` is the meeting's name field). Each file must have a `YYYY-MM-DD` date in its filename.
2. Read the target markdown files to determine which dates already have summaries:
   - For **ha**: check `## YYYY-MM-DD` headings in the file at `<repo>/<file>` (from the ha meeting config — typically `~/standups/ha.md`)
   - For **copo**: check `## YYYY-MM-DD` headings in the file at `<repo>/<file>` (from the copo meeting config — typically `~/standups/copo.md`)
   - For **combined**: a transcript date is "processed" only when BOTH `ha.md` AND `copo.md` have a `## YYYY-MM-DD` heading for that date
3. Build a list of unprocessed transcripts across all three meetings.

If there are no unprocessed transcripts, tell the user everything is up to date and stop.

### Step 3: Process each unprocessed transcript (oldest first)

Merge all unprocessed transcripts from all meetings into a single list sorted by date ascending (oldest first). Process each one:

#### For ha or copo transcripts:

##### 3a: Read and understand the transcript

Read the transcript file. Transcripts may be in different formats (JSON, text, markdown, etc.) from different sources. Adapt to whatever format you find — the key information is who said what.

##### 3b: Generate the summary

Produce a meeting summary in markdown. Start with a `## YYYY-MM-DD` date header derived from the transcript filename.

##### 3c: Save the summary

Write the summary to `~/.standups/summaries/<name>/<date>.md`.

##### 3d: Human review

Display the full summary to the user and ask them to review it before publishing. Wait for explicit approval. If the user requests changes, edit the saved summary file accordingly and present the updated version for another round of review.

##### 3e: Publish

```bash
summary-publish --config ~/.standups/config.yaml ~/.standups/summaries/<name>/<date>.md <name>
```

Report the result to the user before moving on to the next transcript.

#### For combined transcripts:

##### 3a: Read and understand the transcript

Read the transcript file. This is a combined Friday standup with both teams present.

##### 3b: Generate TWO summaries

Split the transcript content by team. Content that is shared/relevant to both teams should appear in both summaries. Generate:

1. An **hA summary** — covering hA team members' updates plus any shared content
2. A **CoPo summary** — covering CoPo team members' updates plus any shared content

Each summary starts with a `## YYYY-MM-DD` date header.

##### 3c: Save the summaries

Write each summary separately:
- `~/.standups/summaries/ha/<date>.md`
- `~/.standups/summaries/copo/<date>.md`

##### 3d: Human review

Display each summary to the user one at a time. Wait for explicit approval of each before proceeding. If the user requests changes, edit the saved summary file and re-present.

##### 3e: Publish each

```bash
summary-publish --config ~/.standups/config.yaml ~/.standups/summaries/ha/<date>.md ha
summary-publish --config ~/.standups/config.yaml ~/.standups/summaries/copo/<date>.md copo
```

Report the result to the user before moving on to the next transcript.

## Summary Template

Include **only** the sections below that have content. Omit any section with nothing to report. Use `###` for section headings.

**Summary rules:**
- Start with a `## YYYY-MM-DD` date header
- Organize by topic/project, not by person or chronologically
- Be concise but capture all substantive information
- Attribute statements to the person who made them
- Paraphrase any obscene language to be professional
- Both the manager (Jimmy) and the team will read these summaries

**Sections (in this order, only if applicable):**

### Manager Notes
Things Jimmy said, was asked about, or committed to during the standup.

### Work in Progress
Organized by topic or project, not by person. What's being worked on, status, and any notable details shared.

### Blockers & Impediments
Anything blocking progress, who is blocked, and what they need.

### Decisions Made
Any decisions reached during the standup.

### Cross-Team Dependencies
Work that depends on or affects the other team, external teams, or other departments.

### Risks
Potential issues raised, timeline concerns, or things that might go wrong.

### Breakout Conversations
Side discussions that happened during standup — capture the topic and outcome.

### Action Items
Bulleted list with owner and deadline (if mentioned):
- **[Name]:** Description of action item (by [deadline] if mentioned)
