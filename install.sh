#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"
LOCAL_BIN="$HOME/.local/bin"

# CLI tools installed by this package that /thb-flow and /thb-update depend on
TOOLS=(
    jira-update
    jira-read
    jira-users
    jira-latest-comment
    slack-update
    slack-users
    slack-channels
    fathom-transcripts
    summary-publish
    run-query
)

info()  { printf "\033[1;34m==>\033[0m %s\n" "$1"; }
ok()    { printf "\033[1;32m  ✓\033[0m %s\n" "$1"; }
warn()  { printf "\033[1;33m  !\033[0m %s\n" "$1"; }
fail()  { printf "\033[1;31m  ✗\033[0m %s\n" "$1"; }

# ---------- 1. Ensure pipx is installed ----------

info "Checking for pipx..."
if command -v pipx &>/dev/null; then
    ok "pipx is already installed"
else
    warn "pipx not found, installing..."
    if command -v brew &>/dev/null; then
        brew install pipx
    elif command -v pip3 &>/dev/null; then
        pip3 install --user pipx
    elif command -v pip &>/dev/null; then
        pip install --user pipx
    else
        fail "Cannot install pipx: no brew, pip3, or pip found"
        exit 1
    fi
    pipx ensurepath
    ok "pipx installed"
fi

# ---------- 2. Install Python CLI tools via pipx ----------

info "Installing claude-utils Python package..."
if pipx list 2>/dev/null | grep -q "claude-utils"; then
    pipx install -e "$SCRIPT_DIR" --force
    ok "claude-utils reinstalled (editable mode)"
else
    pipx install -e "$SCRIPT_DIR"
    ok "claude-utils installed (editable mode)"
fi

# ---------- 3. Ensure ~/.local/bin is in PATH ----------

info "Checking PATH for $LOCAL_BIN..."
if echo "$PATH" | tr ':' '\n' | grep -qx "$LOCAL_BIN"; then
    ok "$LOCAL_BIN is already in PATH"
else
    warn "$LOCAL_BIN is not in PATH, adding to shell profile..."

    PATH_LINE="export PATH=\"\$HOME/.local/bin:\$PATH\""
    ADDED=false

    for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
        if [ -f "$rc" ]; then
            if ! grep -Fq '$HOME/.local/bin' "$rc" && ! grep -Fq '~/.local/bin' "$rc"; then
                printf '\n# Added by claude-utils install.sh\n%s\n' "$PATH_LINE" >> "$rc"
                ok "Added PATH entry to $(basename "$rc")"
                ADDED=true
            else
                ok "PATH entry already present in $(basename "$rc")"
                ADDED=true
            fi
        fi
    done

    if [ "$ADDED" = false ]; then
        # No existing rc file found; create .zshrc as default on macOS
        printf '# Added by claude-utils install.sh\n%s\n' "$PATH_LINE" >> "$HOME/.zshrc"
        ok "Created ~/.zshrc with PATH entry"
    fi

    # Update PATH for the remainder of this script
    export PATH="$LOCAL_BIN:$PATH"
fi

# ---------- 4. Copy Claude Code commands ----------

info "Installing Claude Code commands..."
mkdir -p "$COMMANDS_DIR"

for cmd in thb-flow.md thb-update.md summarize_standup.md; do
    src="$SCRIPT_DIR/.claude/commands/$cmd"
    dst="$COMMANDS_DIR/$cmd"
    if [ ! -f "$src" ]; then
        fail "Source command not found: $src"
        exit 1
    fi
    if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
        ok "$cmd is already up to date"
    else
        cp "$src" "$dst"
        ok "$cmd copied to $COMMANDS_DIR/"
    fi
done

# ---------- 5. Verify installation ----------

info "Verifying CLI tools..."
FAILURES=0
for tool in "${TOOLS[@]}"; do
    if "$tool" --help &>/dev/null; then
        ok "$tool --help succeeded"
    else
        fail "$tool --help failed"
        FAILURES=$((FAILURES + 1))
    fi
done

# ---------- Done ----------

echo ""
if [ "$FAILURES" -eq 0 ]; then
    info "Installation complete! All tools verified."
else
    warn "Installation finished with $FAILURES tool failure(s). Check output above."
fi

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$LOCAL_BIN"; then
    echo ""
    warn "Restart your shell or run: source ~/.zshrc"
fi
