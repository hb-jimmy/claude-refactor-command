---
name: class-naming
description: Guides naming of new classes using object-oriented principles. Centers on domain nouns, ubiquitous language, and avoiding verb-centric anti-patterns. Use when extracting or creating classes to validate that proposed names reflect domain identity rather than behavior.
---

# Class Naming Skill

## Purpose

This skill guides the naming of new objects when extracting or creating classes, validating that proposed names reflect domain identity rather than behavior. It may also be invoked when the user explicitly asks for analysis of an existing class name.

**Do not proactively critique or suggest changes to existing class names unless explicitly asked.**

---

## Core Principle

An object is defined by what it *is* in the domain, not by what it *does*. The name must reflect the object's identity—its place in the business model—using the language domain experts would recognize and use.

---

## The Naming Process

### 1. Understand the Domain Context

Before proposing a name, ensure you understand:

- What concept does this object represent in the business domain?
- What would a domain expert call this thing?
- How does this object relate to other objects in the domain?

**If context is insufficient or ambiguous, stop and ask clarifying questions.** Do not guess. Do not proceed until you have enough clarity to propose a confident name.

### 2. Find the Domain Noun

The name must be a **noun** that captures what the object *is*:

- Use the ubiquitous language of the business
- The name should make sense in conversation with domain experts
- Consider: "The `____` represents..." or "We have a `____` that..."

When the business language doesn't map cleanly to the technical model, this is acceptable—but prefer alignment with domain language whenever possible.

### 3. Consider Relationships

Ask whether the object's relationships make sense:

- Does it make sense for this object to know about its dependencies?
- Is there a missing abstraction? (e.g., should `Customer` have addresses directly, or is there an `Addresses` aggregate?)
- Relationships must make sense in domain terms—no arbitrary coupling

**Cyclical dependencies are never acceptable.**

### 4. Apply Naming Conventions

**Aggregates use plural nouns.** When an object aggregates others of a single type, use the plural form:
- `Accounts` aggregates `Account` objects
- `Orders` aggregates `Order` objects

**Interfaces get generic names; implementations get specific names:**
- Interface: `AccountList`
- Implementation: `CompanyAccountList` (describes the domain-specific variant)

**Favor interfaces over class inheritance.**

### 5. Handle Abbreviations and Length

- **Abbreviations**: Only use abbreviations that are part of the domain's ubiquitous language. Ask the user for permission before using any abbreviation.
- **Length**: Descriptive names are not a problem. If a name feels too long, prompt the user rather than sacrificing clarity.

---

## What to Avoid

Do not approach naming by memorizing lists of forbidden suffixes. Instead, recognize the underlying problem: **names that describe behavior rather than identity lead to stateless procedure containers that masquerade as objects.**

The warning signs:

- The name implies an action rather than a thing
- The object has methods but no meaningful state
- You're struggling to find a noun because the "object" is really just procedural logic

Suffixes like `Manager`, `Handler`, `Processor`, `Helper`, `Util`, and similar indicate the name is trying to describe *what the object does* rather than *what it is*. This leads to objects that hold verbs instead of state—procedural code pretending to be object-oriented.

If you find yourself reaching for these patterns, step back and ask: "What *is* this thing in the domain?" If no noun emerges, the design itself may need reconsideration.

---

## Exceptions

**Controllers** are acceptable. They are a universally understood pattern with established meaning across frameworks and ecosystems.

**Service** is the closest to acceptable among verb-centric suffixes because it isn't directly tied to a verb masquerading as a noun. However, treat it with skepticism—often a better domain noun exists.

Beyond these, any suffix that implies action over identity warrants scrutiny.

---

## Nested and Inner Classes

Do not create or suggest nested/inner classes. If they already exist in the codebase, leave them alone.

---

## Output Format

When proposing a name:

- If one name is clearly superior, present it alone with brief reasoning
- If multiple names are genuinely close, present them ranked with reasoning for each
- Always explain why the name fits the domain

Be prepared to iterate based on user feedback.

---

## Examples

Load language-specific examples as needed:
- Python: See `examples/python.md`
- C#: See `examples/csharp.md`
