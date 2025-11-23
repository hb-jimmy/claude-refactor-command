# **Refactor Code Command Specification (Extended and Authoritative Edition)**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

The `/refactor_code` command is a **coordinated multi-agent refactoring system** designed to simplify, modularize, and stabilize codebases through structured, rule-driven refinement.  
All operations **MUST** be performed through the **Eight-Agent Architecture**, which collectively enforces cohesion, encapsulation, ownership, abstraction, and convergence across recursive refactoring cycles.

This document defines the complete process model, agent interactions, automation layer behavior, and fail-fast protocols required to guarantee deterministic, verifiable code refinement.

---

## ⚖️ Agent Utilization Requirement

1. Claude **MUST** execute all refactoring operations exclusively through the nine defined agents.
2. Each agent **MUST** be invoked according to the orchestration sequence (Analyzer → Implementation → Orchestrator).
3. Direct code manipulation, heuristic rewriting, or manual edits **MUST NOT** occur outside of agent execution.
4. If an agent fails or encounters invalid data, the **Refactoring Orchestrator (Agent 10)** **MUST** halt the pipeline, report the error, and either retry or terminate based on the fail-fast policy.
5. Claude **MUST NOT** bypass or substitute agents with ad hoc reasoning. All logic **MUST** route through the respective agent responsible for that domain of concern.
6. Violating this section **SHALL** constitute a **Protocol Failure**, which invalidates the refactoring result.

---

## 🎯 Single Responsibility Principle (Absolute Enforcement)

1. **Every class MUST have exactly ONE responsibility.**
2. When multiple responsibilities are detected in a class, extraction **MUST** occur, without exception.
3. The following are **NOT** valid reasons to avoid extraction:
   - "The resulting classes would be too small"
   - "This would create too many classes"
   - "The code would be harder to understand"
   - "The current structure is simpler"
4. Extraction **MUST** continue until each class answers to exactly one reason to change.
5. This requirement overrides subjective concerns about code organization, clarity, or simplicity.
6. Technical constraints (semantic preservation, no stateless classes, no cycles) remain the **ONLY** valid reasons to halt extraction.

**Rationale:** Small, focused classes with single responsibilities are easier to test, maintain, and reason about than large classes with multiple responsibilities, regardless of initial perception of simplicity.

---

## ⚙️ Overview of the Nine-Agent Architecture (RESPONSIBILITY-FIRST APPROACH)

| # | Agent | Primary Responsibility | When It Runs |
|--:|--------|------------------------| -------------|
| **1** | **Code Structure Analyzer** | **Identify 2-5 distinct responsibilities per class** using field cohesion, blank lines, section comments, and semantic analysis. | First step at each depth level |
| **3** | **Cohesion & Class Extraction Agent** | **Extract each identified responsibility** into its own class. Enforce 2-5 delegation constraint and anti-stovepipe validation. | After Agent 1 identifies 2+ responsibilities |
| **4** | **Encapsulation Enforcer Agent** | Enforce strict data hiding, remove getters/setters, and verify naming discipline (noun–verber rule). | After Agent 3 extracts classes |
| **5** | **Ownership & Boundary Enforcement Agent** | Ensure domain objects act on their own data and boundaries remain pure (no DTO or adapter leakage). | After Agent 4 |
| **6** | **Abstraction Enforcer Agent** | Guarantee single-level abstraction within all methods and delegation consistency. | After Agent 5 |
| **7** | **Metrics & Convergence Monitor Agent** | Check convergence: PRIMARY (cohesion=1.0 + one-sentence test) or FALLBACK (cohesion≥0.9 with human review). | After Agent 6 |
| **9** | **Code Implementation Agent** | Execute all identified refactorings, creating and modifying source files. | When Agent 7 reports changes needed |
| **2** | **Method Extraction Agent** | **FINAL POLISH ONLY**: Extract methods for readability after ALL responsibility extraction complete. | Only after all classes reach single responsibility |
| **10** | **Refactoring Orchestrator Agent** | Manage **breadth-first recursion**, depth tracking (prompt if >5), human review prompts, and convergence certification. | Coordinates entire flow |

**CRITICAL CHANGE:** Agent 1 now identifies responsibilities FIRST. Agent 3 extracts them to classes. Agent 2 runs LAST for readability only.

---

## 🔁 Main Execution Model (BREADTH-FIRST RESPONSIBILITY EXTRACTION)

### **Breadth-First Control Loop**
```
depth = 0
classes_at_depth[0] = original_source_files

WHILE classes_at_depth[depth] is not empty:

  # DEPTH CHECK
  IF depth > 5:
    PROMPT user: "Recursion depth {depth} exceeded. Continue? (Yes/No)"
    IF user says "No": BREAK
  ENDIF

  # ANALYSIS PHASE (for ALL classes at current depth)
  FOR EACH class IN classes_at_depth[depth]:

    1) Agent 1: Identify 2-5 distinct responsibilities
       - Use field cohesion clustering
       - Detect blank line separators
       - Identify section comments
       - Perform semantic analysis
       - IF 1 responsibility found: Mark converged, SKIP to next class
       - IF >5 responsibilities found: PROMPT user for grouping guidance

    2) Agent 3: Extract each responsibility to its own class (if 2-5 found)
       - Create 2-5 new classes (2-5 delegation constraint)
       - Validate anti-stovepipe: single-method classes need ≥2 downstream deps
       - Move field clusters and code to new classes

    3) FOR EACH extracted class:
         Agent 4: Enforce encapsulation and naming (noun-verber rule)
         Agent 5: Enforce ownership (Tell-Don't-Ask)
         Agent 6: Enforce abstraction (single-level)
         Agent 7: Check convergence
                  - PRIMARY: cohesion=1.0 AND one-sentence test passed
                  - FALLBACK: cohesion≥0.9 AND complexity≤3.5 AND no more responsibilities
                  - IF fallback: PROMPT user for review

  ENDFOR

  # IMPLEMENTATION PHASE (after all classes at depth processed)
  4) IF any classes need implementation:
       Agent 9: Implement all changes at current depth
       Move extracted classes to classes_at_depth[depth+1]
       depth = depth + 1
     ELSE:
       No more classes to extract - BREAK
  ENDIF

ENDWHILE

# FINAL POLISH (only after ALL responsibility extraction complete)
5) Agent 2: Extract methods for readability (no new classes)

# CERTIFICATION
6) Generate final convergence certification report
```

Each agent's actions **MUST** be executed in the above sequence without omission or substitution.
Breadth-first processing ensures all classes at one level are complete before descending deeper.

---

## 🧱 Breadth-First Class Refinement

### **Purpose**
When new classes are extracted by **Agent 3 (Class Extraction)**, the system recursively applies further refinement using a **breadth-first** approach. All classes at depth N are fully processed before moving to depth N+1.

### **Rules**
1. The Orchestrator **MUST** process all classes at the current depth level before descending.
2. For each class, the Orchestrator **MUST** run: **Agent 1 → Agent 3 (if 2+ responsibilities) → Agents 4, 5, 6, 7**.
3. Depth tracking is enforced: if depth > 5, **MUST** prompt user for permission to continue.
4. Each class pursues **PRIMARY convergence** (cohesion=1.0 + one-sentence test) with **FALLBACK** (cohesion≥0.9 + human review) if primary unattainable.
5. Recursive refinement **MUST NOT** introduce naming regressions or encapsulation violations.
6. **Minimum extraction: 2 classes** - prevents useless stovepipe wrappers.
7. **2-5 delegation constraint** - ensures cognitive manageability for humans.

### **Key Changes from Previous Approach**
- **Was:** Depth-first recursion on each extracted class immediately
- **Now:** Breadth-first - complete all classes at depth N before depth N+1
- **Was:** Agent 2 (Method Extractor) ran early
- **Now:** Agent 2 runs LAST, only for readability polish after all responsibility extraction
- **Was:** Cohesion target ≥ 0.9
- **Now:** Cohesion target = 1.0 (ideal), ≥ 0.9 (fallback with human review)

### **Outcome**
- **More classes with fewer methods** - each class has exactly 1 responsibility
- **Systematic decomposition** - level-by-level ensures complete coverage
- **Cognitive manageability** - 2-5 delegation constraint maintained
- **Human oversight** - prompted when depth > 5 or fallback convergence reached
- All class names remain compliant with the **noun–verber rule**

---

## 🧮 Metrics and Convergence

The **Metrics & Convergence Monitor (Agent 7)** evaluates the state of each class and determines convergence level.
The following metrics **MUST** be collected for each class:

| Metric | Description | Target | Source Agent |
|--------|--------------|---------|---------------|
| **Cohesion (PRIMARY)** | **Relatedness of methods within each class** | **1.0 (ideal), ≥ 0.9 (fallback)** | **Class Extractor** |
| **One-Sentence Test (PRIMARY)** | **Class purpose describable without "and"** | **Pass (required for primary)** | **Metrics Monitor** |
| Coupling | Inter-class dependency ratio | ≤ 0.3 | Class Extractor |
| Complexity | Average cyclomatic complexity per method | ≤ 3.5 | Analyzer |
| Encapsulation | Private-field compliance | ≥ 0.95 | Encapsulation Enforcer |
| Ownership | Domain objects act on internal data | ≥ 0.9 | Ownership Enforcer |
| Abstraction Purity | Single-level abstraction compliance | ≥ 0.95 | Abstraction Enforcer |
| **Delegation Count** | **Number of classes delegated to** | **2-5 (cognitive constraint)** | **Class Extractor** |
| **Anti-Stovepipe** | **Single-method classes have ≥2 downstream deps** | **100%** | **Class Extractor** |
| Naming Compliance | Classes conform to domain noun rule | 100% | Encapsulation Enforcer |

### **Convergence Levels**

**PRIMARY Convergence (Ideal Goal):**
- Cohesion = 1.0 (perfect single responsibility)
- One-sentence test passed (class purpose describable without "and")
- Both metric AND semantic criteria met
- Agent 1 identifies only 1 responsibility
- **Action:** Mark class as converged, move to next class

**FALLBACK Convergence (Pragmatic Goal):**
- Cohesion ≥ 0.9 (near-single responsibility)
- Complexity ≤ 3.5
- No more distinct responsibilities identifiable by Agent 1
- **Action:** Flag class for human review, prompt user for guidance

Classes are evaluated individually. No "three consecutive iterations" requirement - each class converges when it reaches PRIMARY or FALLBACK criteria.

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** immediately halt processing and signal the Orchestrator when any of the following occur:

1. **Agent 1 provides no responsibility data** (integration failure between Agent 1 and 3).
2. **Delegation count would exceed 5** without explicit user approval (violates 2-5 cognitive constraint).
3. **Delegation count would be <2** (anti-stovepipe violation - cannot extract only 1 class).
4. **Single-method extracted class has <2 downstream dependencies** (anti-stovepipe violation).
5. **Any extracted class creates cyclic dependency**.
6. **Two extracted classes share mutable state**.
7. **Semantic equivalence cannot be maintained** during extraction.
8. **Agent 1 flags >5 responsibilities** but user does not respond to grouping prompt.
9. Public or protected fields appear in domain classes.
10. Getters/setters are reintroduced.
11. Cross-object predicates (`is*/has*`) appear outside their owning object.
12. Class names match forbidden patterns (`Manager`, `Processor`, `Handler`, `Service`, `Controller`).
13. Method length > 5 executable lines.
14. Nesting depth > 1 in any function.
15. Any agent fails to produce valid output or terminates unexpectedly.
16. **Extraction stopped due to subjective clarity concerns** rather than technical violations.

All fail-fast events **MUST** include diagnostic metadata, including depth level, offending class, and triggering condition.

---

#### **Optional (Automation Layer Improvement)**  
Claude **MAY** implement a **naming-audit pre-flight automation** step before each full agent cycle.  
This step ensures all class names comply with the **noun–verber rule** before the first agent (Analyzer) executes.

**Behavioral Requirements:**  
1. The Orchestrator (Agent 8) **MUST** call the **Encapsulation Enforcer (Agent 4)** in naming-audit mode before each top-level iteration.  
2. If any violations are detected, offending classes **MUST** be renamed before proceeding.  
3. Naming results **MUST** be reported as part of the Metrics & Convergence Monitor (Agent 7).  
4. This check **MAY** run automatically before each refactor loop or be manually triggered.  

**Goal:**  
To proactively eliminate naming drift and maintain domain purity across all agent cycles.

---

## 🧠 Integration and Invocation

### **Command Syntax**
```bash
/refactor_code <source_path>
```
- **Input:** Source file or directory path.  
- **Output:** Refactored codebase, convergence metrics, and reports in Markdown + JSON format.

### **Operational Behavior**
1. The command **MUST** instantiate all eight agents in sequence.  
2. Agents communicate through serialized JSON payloads between iterations.  
3. The Orchestrator manages dependency resolution, recursion depth, and termination.  
4. On success, the system produces final certification and structured reports.

---

## 🏁 Completion and Certification

Refactoring **SHALL** be considered complete when:

1. All convergence metrics meet thresholds for three consecutive iterations.
2. Agent 9 has successfully implemented all identified refactorings.
3. No class extraction or naming changes remain pending.
4. Encapsulation and ownership integrity are fully verified.
5. Abstraction Purity ≥ 0.95 across all methods.
6. Naming Compliance = 100%.
7. The refactored code compiles and maintains semantic equivalence.

### **Certification Output**
> "Refactor Converged: TRUE — Codebase structurally stable, encapsulated, and compliant with object hierarchy standards. All refactorings implemented and verified."

### **Deliverables**
1. Refactored source code files (created and modified)
2. Convergence metrics report (Markdown + JSON)
3. Implementation summary (files changed, methods extracted, classes created)
4. Iteration history (metrics across all iterations)
5. Final certification statement

---
