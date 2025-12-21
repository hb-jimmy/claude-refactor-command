# Control Structure Skill

This skill enforces a single-line body rule for all control structures to improve code readability and clarify control flow intent through abstraction.

## Core Rule

Every control structure body must contain exactly **one executable line of code**. If more than one line is needed, the code must be extracted to a private method/function with a descriptive name that conveys intent and purpose.

## When This Skill Applies

- **Automatically** during all code generation when control structures are present
- **On request** when the user explicitly asks for refactoring
- **Universally** across all code contexts: production code, tests, scripts, etc.

## Applicable Control Structures

This rule applies to:

- `if` / `else if` / `else` blocks
- `for` loops
- `foreach` / `for...in` / `for...of` loops
- `while` loops
- `do...while` loops
- `switch` statements
- Pattern matching with multiple branches
- `try` / `catch` / `finally` blocks
- Lambdas and anonymous functions containing control structures (extract to named method)

## Excluded Constructs

This rule does **not** apply to:

- `using` blocks (C#)
- `with` statements (Python)
- `lock` blocks (C#)
- Ternary/inline conditionals (these are already single expressions)

## Extracted Method Guidelines

### Naming
- Use descriptive names that convey **intent and purpose**, not implementation details
- The name should explain **what** the code accomplishes, not **how** it works
- Let the context guide the most appropriate name

### Visibility
- Always use private/internal visibility
- These are implementation details and should not be exposed

### Placement
- Follow existing codebase conventions when possible
- If no clear convention exists, place near the calling code for readability

## Handling Nested Control Structures

When control structures are nested:

1. Start at the **innermost** control structure
2. Extract its body to a method if it contains more than one line
3. Work **outward** to each containing control structure
4. Each level must comply with the single-line rule

## Refactoring Scope

When refactoring existing code:

- Do **not** exceed the scope of the user's request
- If scope is unclear, **ask the user** before proceeding
- Only consider code outside the requested scope if it was generated as part of the refactoring

## Language Support

This skill applies to all programming languages that support control structures and methods/functions.

For language-specific examples, read the appropriate file from the examples directory:

- **C#**: Read `.claude/skills/control-structure-skill/control-structure-skill-examples/csharp.md`
- **Python**: Read `.claude/skills/control-structure-skill/control-structure-skill-examples/python.md`

Only read example files when generating code in that specific language or when examples would help clarify the pattern.
