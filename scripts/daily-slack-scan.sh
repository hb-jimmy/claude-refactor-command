#!/bin/bash
# Daily Slack Scan — runs /slack_scan via Claude Code in non-interactive mode
# Scheduled by launchd at 7am ET on weekdays

set -euo pipefail

LOG_DIR="$HOME/code/slack-notes/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"

{
    echo "=== Slack Scan started at $(date) ==="

    cd "$HOME/code/claude-utils"

    /opt/homebrew/bin/claude \
        -p \
        --dangerously-skip-permissions \
        --add-dir "$HOME/code/slack-notes" \
        -- "/slack_scan"

    echo "=== Slack Scan completed at $(date) ==="
} >> "$LOG_FILE" 2>&1
