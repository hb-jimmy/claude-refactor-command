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

## ⚙️ Overview of the Nine-Agent Architecture

| # | Agent | Primary Responsibility |
|--:|--------|------------------------|
| **1** | **Code Structure Analyzer** | Parse and evaluate code structure, measure complexity, cohesion, and coupling. |
| **2** | **Method Extraction & Control Normalization Agent** | Extract smaller, independent methods and flatten control flow. |
| **3** | **Cohesion & Class Extraction Agent** | Group related methods and fields into cohesive classes with single responsibility. |
| **4** | **Encapsulation Enforcer Agent** | Enforce strict data hiding, remove getters/setters, and verify naming discipline (noun–verber rule). |
| **5** | **Ownership & Boundary Enforcement Agent** | Ensure domain objects act on their own data and boundaries remain pure (no DTO or adapter leakage). |
| **6** | **Abstraction Enforcer Agent** | Guarantee single-level abstraction within all methods and delegation consistency. |
| **7** | **Metrics & Convergence Monitor Agent** | Aggregate metrics, track stability trends, and detect convergence or regressions. |
| **9** | **Code Implementation Agent** | Execute all identified refactorings, creating and modifying source files. |
| **10** | **Refactoring Orchestrator Agent** | Manage agent sequencing, recursion, implementation phase, fail-fast responses, and convergence certification. |

Each agent's output feeds directly into the next in a **closed operational loop** under Orchestrator supervision.

---

## 🔁 Main Execution Model

### **Primary Control Loop**
```
REPEAT
  # ANALYSIS PHASE
  0) Run Naming Audit Pre-Flight (Agent 4 in audit mode)
  1) Analyze code structure and metrics (Agent 1)
  2) Extract and normalize methods (Agent 2)
  3) Identify and extract cohesive classes (Agent 3)
  4) Enforce encapsulation and noun–verber naming rules (Agent 4)
  5) Enforce ownership and boundary control (Agent 5)
  6) Verify abstraction consistency (Agent 6)
  7) Aggregate and evaluate convergence metrics (Agent 7)

  # IMPLEMENTATION PHASE (if needed)
  9) IF convergence not achieved:
       Execute code implementation (Agent 9)
       Apply all identified refactorings
     ENDIF

  # ORCHESTRATION
  10) Coordinate recursion, restart analysis, or finalize (Agent 10)

UNTIL all convergence thresholds met OR fail-fast triggered
```

Each agent's actions **MUST** be executed in the above sequence without omission or substitution.
Intermediate outputs are immutable records that serve as formal checkpoints between agents.

---

## 🧱 Recursive Class Refinement

### **Purpose**
When new classes are extracted by **Agent 3 (Cohesion & Class Extraction)**, the system recursively applies further refinement to those classes until stability is achieved.

### **Rules**
1. The Orchestrator **MUST** re-run the following sequence for every extracted class: **Agents 3 → 4 → 5 → 6**.  
2. If the extracted class contains **three (3) or fewer methods**, the Orchestrator **SHOULD** begin at **Agent 4 (Encapsulation Enforcer)** instead.  
3. Each recursion **MUST** conclude only when no further extractions or renames are possible.  
4. All recursion cycles **MUST** verify naming compliance (noun–verber rule) before Agents 5 or 6 execute.  
5. Recursive refinement **MUST NOT** introduce naming regressions or encapsulation violations.

### **Execution Flow**
```
FOR EACH extracted_class IN new_classes:
    RUN Agent 4 (Encapsulation Enforcer) in Naming Reevaluation mode
    IF method_count > 3:
        RUN Agents [3, 4, 5, 6] on extracted_class
    ELSE:
        RUN Agents [4, 5, 6] on extracted_class
    ENDIF
    IF extracted_class spawns new sub-classes:
        RECURSE on each sub-class
    ENDIF
UNTIL no further extraction candidates exist
```

### **Outcome**
- Small, focused classes emerge naturally.  
- System-level complexity decreases monotonically.  
- All class names remain compliant with the **noun–verber rule**.  
- Recursive cycles terminate automatically when abstraction and encapsulation purity reach equilibrium.

---

## 🧮 Metrics and Convergence

The **Metrics & Convergence Monitor (Agent 7)** evaluates the state of the refactoring loop and ensures all quantitative thresholds are met.  
The following metrics **MUST** be collected every iteration:

| Metric | Description | Target | Source Agent |
|--------|--------------|---------|---------------|
| Cohesion | Relatedness of methods within each class | ≥ 0.9 | Class Extractor |
| Coupling | Inter-class dependency ratio | ≤ 0.3 | Class Extractor |
| Complexity | Average cyclomatic complexity per method | ≤ 3.5 | Analyzer / Method Extractor |
| Encapsulation | Private-field compliance | ≥ 0.95 | Encapsulation Enforcer |
| Ownership | Domain objects act on internal data | ≥ 0.9 | Ownership Enforcer |
| Abstraction Purity | Single-level abstraction compliance | ≥ 0.95 | Abstraction Enforcer |
| Naming Compliance | Classes conform to domain noun rule | 100% | Encapsulation Enforcer |
| Convergence Stability | Δ improvement over 3 iterations | < 0.01 | Metrics Monitor |

Convergence **MUST** be declared only when all metrics meet or exceed target thresholds **for three consecutive iterations**.

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** immediately halt processing and signal the Orchestrator when any of the following occur:

1. Public or protected fields appear in domain classes.  
2. Getters/setters are reintroduced.  
3. Cross-object predicates (`is*/has*`) appear outside their owning object.  
4. Class names match forbidden patterns (`Manager`, `Processor`, `Handler`, `Service`, `Controller`).  
5. Method length > 5 executable lines.  
6. Nesting depth > 1 in any function.  
7. Convergence metrics regress for two consecutive iterations.  
8. Any agent fails to produce valid output or terminates unexpectedly.  
9. Total iterations exceed 10 without convergence.  

All fail-fast events **MUST** include diagnostic metadata, including iteration number, offending class, and triggering metric.

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
