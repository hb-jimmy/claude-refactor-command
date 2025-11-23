# Quick Start Guide

Get started with the Claude Code Refactoring Plugin in 5 minutes.

## 1. Install (30 seconds)

```bash
# Clone and install
git clone https://github.com/yourusername/claude-refactor-plugin.git
cd claude-refactor-plugin
cp -r .claude/* ~/.claude/
```

## 2. Verify (10 seconds)

Open Claude Code and check the command is available:

```bash
/help
```

You should see `/refactor_code` in the list.

## 3. Try It (5 minutes)

Run on a sample file:

```bash
/refactor_code src/MyClass.java
```

Or a directory:

```bash
/refactor_code src/services/
```

## What to Expect

The system will:

1. Analyze your code structure
2. Identify refactoring opportunities
3. Extract methods and classes
4. Enforce clean code principles
5. Iterate until convergence
6. Produce refactored code + metrics report

## Example Output

```
Iteration 1:
  Cohesion: 0.65 → 0.82
  Coupling: 0.55 → 0.38
  Complexity: 8.2 → 4.5
  Classes Created: 3

Iteration 2:
  Cohesion: 0.82 → 0.91
  Coupling: 0.38 → 0.29
  Complexity: 4.5 → 3.2
  Classes Created: 1

Convergence achieved after 3 iterations.

Files Created: 4
Files Modified: 2
Methods Extracted: 23
Classes Extracted: 4
```

## Common Use Cases

### Refactor a God Class

```bash
/refactor_code src/UserManager.java
```

Result: Multiple focused classes (User, UserValidator, UserRepository, etc.)

### Clean Up a Service Layer

```bash
/refactor_code src/services/
```

Result: Single-responsibility services with proper encapsulation

### Fix Spaghetti Code

```bash
/refactor_code src/legacy/OrderProcessor.java
```

Result: Clean, testable methods with single-level abstraction

## Understanding the Process

### The Nine Agents

1. **Analyzer** - Measures code quality metrics
2. **Method Extractor** - Identifies extraction opportunities
3. **Class Extractor** - Groups related functionality
4. **Encapsulation Enforcer** - Enforces data hiding
5. **Ownership Enforcer** - Ensures proper boundaries
6. **Abstraction Enforcer** - Maintains abstraction levels
7. **Metrics Monitor** - Tracks convergence
8. *(Reserved)*
9. **Implementation** - Executes refactorings
10. **Orchestrator** - Manages the process

### Convergence Criteria

The system stops when these targets are met for 3 consecutive iterations:

- Cohesion ≥ 0.9
- Coupling ≤ 0.3
- Complexity ≤ 3.5
- Encapsulation ≥ 0.95
- Ownership ≥ 0.9
- Abstraction Purity ≥ 0.95
- Naming Compliance = 100%

## Tips

1. **Start Small** - Try on a single problematic class first
2. **Review Changes** - Check the refactored code before committing
3. **Run Tests** - Verify semantic equivalence with your test suite
4. **Iterate** - Run multiple times if needed for complex code
5. **Trust the Process** - Small classes are better than "simple" large ones

## What Gets Changed

### Extracted:
- Long methods → Multiple focused methods
- God classes → Single-responsibility classes
- Nested logic → Flat, readable methods

### Enforced:
- Private fields (no public data)
- No getters/setters
- Single-level abstraction
- Proper ownership boundaries
- Domain-driven naming

### Preserved:
- Exact behavior
- Test compatibility
- Transaction boundaries
- Error handling
- Async/await patterns

## Troubleshooting

**Command not found?**
- Verify: `ls ~/.claude/commands/refactor_code.md`
- Fix: Re-run installation steps

**Agents failing?**
- Verify: `ls ~/.claude/agents/*.md` (should show 9 files)
- Fix: `cp -r .claude/agents/* ~/.claude/agents/`

**Code not compiling after refactoring?**
- This is a fail-fast condition
- Check the error report
- Report as an issue if it's a bug

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Check [INSTALL.md](INSTALL.md) for advanced installation options
- Review agent documentation in `.claude/agents/`
- Try on your own codebase
- Provide feedback via GitHub issues

## Need Help?

- GitHub Issues: https://github.com/yourusername/claude-refactor-plugin/issues
- Claude Code Docs: https://github.com/anthropics/claude-code

Happy refactoring!
