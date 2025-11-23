# Installation Guide

This guide provides detailed instructions for installing the Claude Code Refactoring Plugin.

## Prerequisites

- Claude Code CLI installed and configured
- Access to your `.claude` directory (typically `~/.claude`)

## Installation Methods

### Method 1: Quick Install (Recommended)

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-refactor-plugin.git

# Navigate to the repository
cd claude-refactor-plugin

# Copy files to your Claude directory
cp -r .claude/* ~/.claude/

# Verify installation
ls ~/.claude/commands/refactor_code.md
ls ~/.claude/agents/refactor-orchestrator.md
```

### Method 2: Symlink Install (For Development)

If you plan to contribute or want automatic updates:

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-refactor-plugin.git
cd claude-refactor-plugin

# Create command symlink
ln -sf "$(pwd)/.claude/commands/refactor_code.md" ~/.claude/commands/refactor_code.md

# Create agent symlinks
for agent in .claude/agents/*.md; do
    ln -sf "$(pwd)/$agent" ~/.claude/agents/$(basename "$agent")
done

# Verify symlinks
ls -l ~/.claude/commands/refactor_code.md
ls -l ~/.claude/agents/
```

### Method 3: Manual Installation

If you prefer manual control:

1. Download or clone this repository
2. Manually copy each file:
   - Copy `.claude/commands/refactor_code.md` to `~/.claude/commands/`
   - Copy all files from `.claude/agents/` to `~/.claude/agents/`

## Verification

After installation, verify the plugin is available:

```bash
# In Claude Code, check for the command
/help

# You should see /refactor_code in the list of available commands
```

Or test directly:

```bash
# Try the command on a sample file
/refactor_code path/to/your/code.java
```

## Updating

### If Installed via Copy (Method 1)

```bash
cd claude-refactor-plugin
git pull
cp -r .claude/* ~/.claude/
```

### If Installed via Symlink (Method 2)

```bash
cd claude-refactor-plugin
git pull
# Symlinks automatically point to updated files
```

## Uninstallation

To remove the plugin:

```bash
# Remove command
rm ~/.claude/commands/refactor_code.md

# Remove agents
rm ~/.claude/agents/code-structure-analyzer.md
rm ~/.claude/agents/method-extractor.md
rm ~/.claude/agents/class-extractor.md
rm ~/.claude/agents/encapsulation-enforcer.md
rm ~/.claude/agents/ownership-boundary-enforcer.md
rm ~/.claude/agents/abstraction-enforcer.md
rm ~/.claude/agents/metrics-monitor.md
rm ~/.claude/agents/code-implementation.md
rm ~/.claude/agents/refactor-orchestrator.md
```

Or remove all at once:

```bash
cd ~/.claude/commands && rm -f refactor_code.md
cd ~/.claude/agents && rm -f code-structure-analyzer.md method-extractor.md class-extractor.md encapsulation-enforcer.md ownership-boundary-enforcer.md abstraction-enforcer.md metrics-monitor.md code-implementation.md refactor-orchestrator.md
```

## Troubleshooting

### Command Not Found

If `/refactor_code` is not recognized:

1. Verify the file exists: `ls ~/.claude/commands/refactor_code.md`
2. Check file permissions: `chmod 644 ~/.claude/commands/refactor_code.md`
3. Restart Claude Code

### Agents Not Loading

If agents fail to load:

1. Verify all agent files exist: `ls ~/.claude/agents/*.md`
2. Check file permissions: `chmod 644 ~/.claude/agents/*.md`
3. Ensure no duplicate agent files with different names

### Permission Errors

If you get permission errors during installation:

```bash
# Ensure .claude directory exists
mkdir -p ~/.claude/commands ~/.claude/agents

# Fix permissions
chmod 755 ~/.claude ~/.claude/commands ~/.claude/agents
```

## Directory Structure

After successful installation, your `.claude` directory should contain:

```
~/.claude/
├── commands/
│   └── refactor_code.md
└── agents/
    ├── abstraction-enforcer.md
    ├── class-extractor.md
    ├── code-implementation.md
    ├── code-structure-analyzer.md
    ├── encapsulation-enforcer.md
    ├── method-extractor.md
    ├── metrics-monitor.md
    ├── ownership-boundary-enforcer.md
    └── refactor-orchestrator.md
```

## Next Steps

After installation:

1. Read the [README.md](README.md) for usage instructions
2. Try the command on a sample codebase
3. Review the agent documentation in `.claude/agents/`
4. Configure any custom settings as needed

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review [open issues](https://github.com/yourusername/claude-refactor-plugin/issues)
3. Create a new issue with details about your problem
