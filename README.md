# Claude Code Utilities

A collection of CLI tools and Claude Code commands for Jira, Slack, and code refactoring.

## Quick Start: CLI Tools

### Installation

```bash
git clone https://github.com/hb-jimmy/claude-refactor-command.git
cd claude-refactor-command
pip install -e .
```

### Jira Tools

Requires `~/.jira-config.yaml`:
```yaml
email: "your.email@example.com"
api_token: "your-jira-api-token"
```

| Command | Description |
|---------|-------------|
| `jira-read HB-123` | Get issue details as JSON |
| `jira-update HB-123 -m "comment"` | Add comment to issue |
| `jira-update HB-123 -s "In Progress"` | Change issue status |
| `jira-users` | List all Jira users |
| `jira-latest-comment HB-123` | Get SHA from latest THB Automated Summary |

### Slack Tools

First-time setup:
1. Create a Slack App at https://api.slack.com/apps
2. Add OAuth scopes: `chat:write`, `channels:read`, `groups:read`, `users:read`, `users:read.email`
3. Add redirect URL: `https://localhost:8765/oauth/callback`
4. Add to `~/.slack-config.yaml`:
   ```yaml
   client_id: "your-client-id"
   client_secret: "your-client-secret"
   ```
5. Run `slack-update --auth` to authenticate

| Command | Description |
|---------|-------------|
| `slack-update C01234567 "message"` | Post message to channel |
| `slack-users` | Fetch users to `~/.slack-users.json` |
| `slack-channels` | Fetch channels to `~/.slack-channels.json` |

### Claude Code Commands

#### /thb-flow

Start work on a Jira story:
```
/thb-flow HB-123
```

This command:
- Validates the issue exists and is workable
- Assigns the issue to you (if unassigned)
- Transitions to "In Progress"
- Creates or switches to a feature branch
- Displays story details

#### /thb-update

Post a progress update to Jira:
```
/thb-update
```

This command:
- Extracts Jira issue key from current branch name
- Finds changes since last THB Automated Summary (or merge-base)
- Generates a non-technical summary of what was achieved
- Optionally includes pairing partner mentions
- Posts formatted update to Jira with SHA tracking

---

## Refactoring Plugin

A multi-agent refactoring system for Claude Code that transforms complex codebases into clean, maintainable code.

### Overview

This plugin provides the `/refactor_code` command, which orchestrates nine specialized agents to analyze, refactor, and verify code through multiple iterative cycles until convergence is achieved.

### Key Features

- **Nine-Agent Architecture**: Specialized agents for structure analysis, method extraction, class extraction, encapsulation, ownership, abstraction, metrics monitoring, implementation, and orchestration
- **Recursive Refinement**: Automatically extracts classes and methods until single-responsibility is achieved
- **Metrics-Driven**: Tracks cohesion, coupling, complexity, encapsulation, ownership, and abstraction metrics
- **Convergence Detection**: Automatically stops when code reaches structural stability
- **Fail-Fast**: Built-in safeguards prevent regressions and violations
- **Semantic Preservation**: Maintains exact behavioral equivalence throughout refactoring

### Installation

Copy the `.claude` directory to your home directory:
```bash
cp -r .claude/* ~/.claude/
```

Or symlink to keep updated via git:
```bash
ln -s "$(pwd)/.claude/commands/"* ~/.claude/commands/
ln -s "$(pwd)/.claude/agents/"* ~/.claude/agents/
```

## Usage

### Basic Command

```bash
/refactor_code <source_path>
```

**Example:**
```bash
/refactor_code src/services/UserService.java
```

Or refactor an entire directory:
```bash
/refactor_code src/services/
```

### What Happens

1. **Analysis Phase** (Agents 1-7):
   - Analyzes code structure and complexity
   - Identifies method extraction opportunities
   - Finds cohesion-based class extraction candidates
   - Checks encapsulation and naming compliance
   - Verifies ownership boundaries
   - Ensures single-level abstraction
   - Aggregates metrics and checks convergence

2. **Implementation Phase** (Agent 9):
   - Executes all identified refactorings
   - Creates new class files
   - Extracts methods
   - Applies ownership fixes
   - Maintains semantic equivalence

3. **Orchestration** (Agent 10):
   - Manages agent sequencing
   - Triggers recursive refinement for extracted classes
   - Monitors convergence
   - Handles fail-fast conditions

4. **Iteration**:
   - Process repeats until all metrics meet thresholds for 3 consecutive iterations

### Expected Outputs

- Refactored source code files (created and modified)
- Convergence metrics report (Markdown + JSON)
- Implementation summary (files changed, methods extracted, classes created)
- Iteration history showing metric progression
- Final certification statement

## Architecture

### The Nine Agents

1. **Code Structure Analyzer** - Parses code, measures complexity, cohesion, and coupling
2. **Method Extraction & Control Normalization** - Extracts methods and flattens control flow
3. **Cohesion & Class Extraction** - Groups related methods into cohesive classes
4. **Encapsulation Enforcer** - Enforces data hiding and naming discipline (noun-verber rule)
5. **Ownership & Boundary Enforcement** - Ensures domain objects act on their own data
6. **Abstraction Enforcer** - Guarantees single-level abstraction in methods
7. **Metrics & Convergence Monitor** - Tracks stability and detects convergence
8. *(Reserved)*
9. **Code Implementation** - Executes all identified refactorings
10. **Refactoring Orchestrator** - Manages sequencing, recursion, and certification

### Convergence Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Cohesion | ≥ 0.9 | Relatedness of methods within each class |
| Coupling | ≤ 0.3 | Inter-class dependency ratio |
| Complexity | ≤ 3.5 | Average cyclomatic complexity per method |
| Encapsulation | ≥ 0.95 | Private-field compliance |
| Ownership | ≥ 0.9 | Domain objects act on internal data |
| Abstraction Purity | ≥ 0.95 | Single-level abstraction compliance |
| Naming Compliance | 100% | Classes conform to domain noun rule |
| Convergence Stability | < 0.01 | Δ improvement over 3 iterations |

## Design Principles

### Absolute Single Responsibility

This plugin **enforces** the Single Responsibility Principle without compromise:
- Every class must have exactly ONE responsibility
- Extraction occurs regardless of resulting class size
- Small, focused classes are prioritized over "simplicity"
- Only technical constraints (semantics, cycles) halt extraction

### Recursive Class Refinement

When classes are extracted, the system recursively refines them:
- Re-runs analysis on all extracted classes
- Continues extraction until stability
- Verifies naming compliance at each level
- Prevents regressions during recursion

### Fail-Fast Safeguards

The system immediately halts if it detects:
- Public/protected fields in domain classes
- Reintroduced getters/setters
- Cross-object predicates outside their owner
- Forbidden class names (Manager, Processor, Handler, Service, Controller)
- Methods longer than 5 executable lines
- Nesting depth > 1
- Metric regressions for 2+ iterations
- > 10 iterations without convergence

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development

To modify the agents or command:
1. Edit files in `.claude/agents/` or `.claude/commands/`
2. Test locally by running `/refactor_code` on sample code
3. Submit a PR with your improvements

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or discussions:
- Open an issue on GitHub
- Check the [Claude Code documentation](https://github.com/anthropics/claude-code)

## Credits

Created by Jimmy Balmert

Based on object-oriented design principles from:
- Clean Code (Robert C. Martin)
- Refactoring (Martin Fowler)
- Domain-Driven Design (Eric Evans)
