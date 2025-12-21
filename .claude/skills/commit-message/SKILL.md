---
name: commit-message
description: Generates git commit messages by analyzing staged changes. Uses imperative tone with title + body format by default. Follow any specific format instructions provided in the prompt.
---

# Commit Message Skill

## Purpose

This skill generates clear, descriptive git commit messages by analyzing staged changes. It produces messages that accurately describe what the commit does and why.

---

## Default Behavior

### 1. Analyze Staged Changes

Before generating a message, examine the staged changes:

```bash
git diff --cached
```

If no changes are staged, inform the user and suggest staging changes first.

### 2. Default Format: Title + Body

Generate messages with:
- **Title**: Short summary line (50 characters or less preferred, 72 max)
- **Blank line**: Separates title from body
- **Body**: Detailed explanation of what changed and why (wrap at 72 characters)

### 3. Imperative Tone

Write in imperative mood (commands):
- "Add user authentication" not "Added user authentication"
- "Fix null pointer exception" not "Fixes null pointer exception"
- "Refactor database connection handling" not "Refactoring..."

---

## Format Options

When the prompt specifies a different format, use it instead of the default:

### Conventional Commits

```
<type>[optional scope]: <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`

### Simple Summary

Single line describing the change. No body, no prefixes.

---

## Guidelines

### Title

- Start with a capital letter
- No period at the end
- Be specific: "Add password reset endpoint" not "Update auth"
- Focus on *what* the commit does

### Body

- Explain *why* the change was made, not just *what* changed
- Describe the problem being solved if relevant
- Note any side effects or important implementation details
- Use bullet points for multiple related changes

### What to Avoid

- Vague messages: "Fix bug", "Update code", "Changes"
- Implementation details in the title (save for body)
- Referencing line numbers or file paths unless critical
- Overly long titles

---

## Process

1. Run `git diff --cached` to see staged changes
2. Understand the scope and purpose of the changes
3. Draft a title that summarizes the change
4. Add body content explaining context and reasoning
5. Present the commit message to the user
6. If the user approves, create the commit

---

## Output

Present the generated commit message in a code block:

```
<title>

<body>
```

Ask if the user wants to proceed with the commit or make adjustments.
