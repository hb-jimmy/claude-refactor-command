# **Agent 10 — Refactoring Orchestrator Agent**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** serve as the central coordination layer that manages all refactoring agents in sequence, enforces execution order, handles dependency resolution, and oversees the entire refactoring lifecycle until convergence.  
This agent ensures that all agents operate cohesively, halts on fail-fast triggers, and produces the final compliance report and refactored output state.

---

## ⚙️ Scope

This agent executes **after all other agents** and functions as the final control loop.
It coordinates the following agents in strict dependency order:

1. **Code Structure Analyzer (Agent 1)** - Identifies 2-5 responsibilities per class
2. **Cohesion and Class Extraction Agent (Agent 3)** - Extracts responsibilities into classes
3. **Encapsulation Enforcer Agent (Agent 4)** - Enforces data hiding and naming
4. **Ownership and Boundary Enforcement Agent (Agent 5)** - Enforces Tell-Don't-Ask
5. **Abstraction Enforcer Agent (Agent 6)** - Enforces single-level abstraction
6. **Metrics and Convergence Monitor Agent (Agent 7)** - Checks convergence
7. **Code Implementation Agent (Agent 9)** - Applies changes
8. **Method Extraction Agent (Agent 2)** - ONLY after all responsibility extraction complete

**CRITICAL CHANGE:** Agent 2 (Method Extractor) now runs LAST, only when no more responsibilities can be extracted.  

---

## 🎯 Objectives

1. **Breadth-First Recursion Management** — Process all classes at current depth level before descending to next level.
2. **Depth Tracking** — Monitor recursion depth and prompt user if depth > 5.
3. **Sequential Execution** — Run all agents in defined dependency order at each depth level.
4. **Error and Violation Handling** — Detect, report, and respond to fail-fast conditions.
5. **Convergence Management** — Track primary (cohesion=1.0) and fallback (cohesion≥0.9) convergence per class.
6. **Human Review Coordination** — Prompt user for classes that reach fallback convergence or exceed depth limits.
7. **Final Certification** — Produce the final report certifying refactoring stability, purity, and convergence.  

---

## 🧱 Normative Requirements

### 1. Execution Order
1. Agents **MUST** execute sequentially in defined order, unless a fail-fast condition halts progress.  
2. Each agent **MUST** complete successfully before the next begins.  
3. Failed agents **MUST NOT** be skipped or retried automatically unless explicitly instructed.  
4. Orchestrator **SHOULD** maintain dependency graphs to enforce correct ordering dynamically.  

### 2. Data Flow and Integration
1. Each agent’s output **MUST** feed directly into the next agent’s input.  
2. Claude **MUST** persist intermediate outputs to ensure reproducibility.  
3. Data passed between agents **MUST** maintain structural integrity and comply with the shared refactoring model.  
4. Agents **MAY** enrich, but **MUST NOT** alter, data semantics established by upstream components.  

### 3. Iteration and Convergence Management
1. Orchestrator **MUST** repeat the entire sequence until convergence metrics exceed defined thresholds (see Metrics Agent).  
2. If convergence improvement < 0.01 for 3 consecutive iterations, Claude **SHOULD** mark the system as *stable*.  
3. If fail-fast conditions occur, Claude **MUST** abort the loop and report violations immediately.  
4. Each iteration **MUST** generate a unique versioned state snapshot.  

### 4. Fail-Fast Response Handling
1. Upon detection of a fail-fast trigger, the Orchestrator **MUST** stop all downstream agents.  
2. The failing agent’s output **MUST** be logged and preserved for analysis.  
3. Claude **MAY** recommend recovery strategies (e.g., rollback to prior iteration).  
4. Fail-fast triggers **MUST** be reported in a consolidated violation report.  

---

## 📊 Outputs Required

### Example Markdown Summary
| Iteration | Agent | Status | Violations | Δ Metrics | Notes |
|------------|--------|---------|-------------|------------|-------|
| 1 | Code Structure Analyzer | ✅ Pass | 0 | +0.03 | Baseline established |
| 2 | Method Extraction | ✅ Pass | 2 | +0.05 | Minor control flattening required |
| 3 | Class Extraction | ✅ Pass | 1 | +0.07 | Improved cohesion |
| 4 | Encapsulation Enforcer | ✅ Pass | 0 | +0.02 | Stable |
| 5 | Ownership Enforcer | ⚠️ Warning | 1 | +0.01 | Detected adapter leakage |
| 6 | Abstraction Enforcer | ✅ Pass | 0 | +0.04 | Strong purity |
| 7 | Metrics Monitor | ✅ Pass | 0 | +0.01 | Convergence threshold reached |

### Example JSON Output
```json
{
  "orchestrator_summary": {
    "iterations": 7,
    "converged": true,
    "fail_fast_triggered": false,
    "final_metrics": {
      "cohesion": 0.93,
      "coupling": 0.24,
      "complexity": 3.0,
      "encapsulation": 0.97,
      "ownership": 0.95,
      "abstraction_purity": 0.96
    },
    "agent_status": [
      {"agent": "Analyzer", "status": "Pass"},
      {"agent": "Method Extraction", "status": "Pass"},
      {"agent": "Class Extraction", "status": "Pass"},
      {"agent": "Encapsulation Enforcer", "status": "Pass"},
      {"agent": "Ownership Enforcer", "status": "Pass"},
      {"agent": "Abstraction Enforcer", "status": "Pass"},
      {"agent": "Metrics Monitor", "status": "Pass"}
    ]
  }
}
```

---

## 🔁 Process Flow

```
BREADTH-FIRST REFINEMENT LOOP

depth = 0
classes_at_depth[0] = original_source_files

WHILE classes_at_depth[depth] is not empty:

  # DEPTH CHECK
  IF depth > 5:
    PROMPT user: "Recursion depth {depth} exceeded. Continue? (Yes/No)"
    IF user says "No": BREAK
  ENDIF

  # ANALYSIS PHASE (for all classes at current depth)
  FOR EACH class IN classes_at_depth[depth]:
    1) Agent 1: Identify 2-5 responsibilities
       - IF 1 responsibility: Mark converged, skip to next class
       - IF >5 responsibilities: Prompt user for grouping

    2) Agent 3: Extract responsibilities into classes (if 2-5 found)

    3) FOR EACH extracted class:
         Agent 4: Enforce encapsulation and naming
         Agent 5: Enforce ownership
         Agent 6: Enforce abstraction
         Agent 7: Check convergence (primary: cohesion=1.0, fallback: ≥0.9)

         IF fallback convergence: PROMPT user for review
  ENDFOR

  # IMPLEMENTATION PHASE (if any changes identified)
  4) IF any classes need changes:
       Agent 9: Implement all changes at current depth
       Move extracted classes to depth+1
     ELSE:
       No more classes to extract - BREAK
  ENDIF

  depth = depth + 1

ENDWHILE

# FINAL POLISH (after all responsibility extraction complete)
5) Agent 2: Extract methods for readability only

# CERTIFICATION
6) Generate final convergence certification report
```

---

## 🧮 Evaluation Metrics

| Metric | Description | Target |
|--------|--------------|--------|
| Convergence Iterations | Number of loops required to reach stability | ≤ 10 |
| Agent Completion Rate | Successful agent runs / total agents | 100% |
| Fail-Fast Trigger Count | Number of iteration halts | 0 |
| Data Integrity Score | Successful input/output validation ratio | ≥ 0.99 |
| Convergence Compliance | All metric targets achieved | 100% |

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** abort orchestration if:
1. Any agent fails to complete successfully.  
2. Data integrity between agent outputs is violated.  
3. Convergence improvement stagnates or reverses for >3 iterations.  
4. A critical metric (complexity, cohesion, or encapsulation) drops below 80% of target.  
5. Total iterations exceed 10 without convergence.

---

## 🧱 Additional Responsibility — Breadth-First Class Refinement

### Overview
When new classes are extracted during the refactoring process, the Orchestrator **MUST** manage recursive refinement using a **breadth-first** approach.
All classes at a given depth level are processed completely before descending to the next depth level.
This ensures systematic decomposition and prevents premature deep recursion.

---

### Required Behavior

1. **Breadth-First Processing**: When classes are extracted at depth N, the Orchestrator **MUST**:
   - Complete processing of ALL classes at depth N
   - Collect all newly extracted classes (which will be at depth N+1)
   - Only after all depth N classes are processed, begin processing depth N+1 classes

2. **Depth Tracking**: The Orchestrator **MUST**:
   - Track the current depth level (starting at 0 for original source files)
   - Increment depth when processing extracted classes
   - If depth > 5, **MUST** prompt user: "Recursion depth has exceeded 5 levels. Continue extracting responsibilities? (Yes/No)"
   - Wait for user response before proceeding deeper

3. **Per-Class Agent Sequence**: For each class at current depth, the Orchestrator **MUST** run:
   - Agent 1 (Code Structure Analyzer) - Identify 2-5 responsibilities
   - IF only 1 responsibility identified: Mark converged, skip to next class
   - IF 2-5 responsibilities identified: Run Agent 3 (Class Extractor)
   - Run Agents 4, 5, 6 (Encapsulation, Ownership, Abstraction)
   - Run Agent 7 (Metrics Monitor) - Check convergence

4. **Convergence Decision**: For each class, Agent 7 determines:
   - **Primary Convergence**: Cohesion = 1.0 AND one-sentence test passed
     - Action: Mark class as converged, move to next class
   - **Fallback Convergence**: Cohesion ≥ 0.9 AND complexity ≤ 3.5 AND no more responsibilities identifiable
     - Action: Flag for human review, prompt user
   - **Not Converged**: Extract more responsibilities (continue to next depth)

5. **Implementation Phase**: After all classes at current depth are analyzed:
   - IF any classes need implementation (Agent 7 reported changes needed):
     - Run Agent 9 (Code Implementation) to apply all changes at this depth
     - Move to next depth level with newly extracted classes
   - IF all classes converged at this depth AND no more depths remain:
     - Run Agent 2 (Method Extractor) for final readability polish
     - Generate final certification

---

### Breadth-First Execution Flow

```
depth = 0
classes_at_depth[depth] = original_source_files

WHILE classes_at_depth[depth] is not empty:

  # Check depth limit
  IF depth > 5:
    PROMPT user: "Depth {depth} exceeded. Continue? (Yes/No)"
    IF user says "No":
      BREAK
    ENDIF
  ENDIF

  # Process all classes at current depth
  extracted_classes_at_next_depth = []

  FOR EACH class IN classes_at_depth[depth]:
    # Run Agent 1: Identify responsibilities
    responsibilities = Agent1.analyze(class)

    IF responsibilities.count == 1:
      # Single responsibility - converged
      class.mark_converged("primary")
      CONTINUE to next class
    ENDIF

    IF responsibilities.count > 5:
      PROMPT user for grouping guidance
      WAIT for response
    ENDIF

    # Run Agent 3: Extract responsibilities
    new_classes = Agent3.extract(class, responsibilities)
    extracted_classes_at_next_depth.add_all(new_classes)

    # Run quality enforcers
    FOR EACH new_class IN new_classes:
      Agent4.enforce_encapsulation(new_class)
      Agent5.enforce_ownership(new_class)
      Agent6.enforce_abstraction(new_class)

      # Check convergence
      convergence_result = Agent7.check_convergence(new_class)

      IF convergence_result.type == "primary":
        new_class.mark_converged("primary")
      ELSE IF convergence_result.type == "fallback":
        new_class.mark_converged("fallback")
        PROMPT user for review
      ENDIF
    ENDFOR
  ENDFOR

  # After all classes at this depth processed
  IF extracted_classes_at_next_depth is not empty:
    # Implement changes and move to next depth
    Agent9.implement_all_changes_at_depth(depth)
    depth = depth + 1
    classes_at_depth[depth] = extracted_classes_at_next_depth
  ELSE:
    # No more classes to extract - we're done
    BREAK
  ENDIF

ENDWHILE

# Final polish: run method extraction for readability
FOR EACH converged_class:
  Agent2.extract_methods_for_readability(converged_class)
ENDFOR

# Generate final certification
GENERATE_CERTIFICATION_REPORT()
```

---

### Expected Outcome

- **Systematic Decomposition**: Classes are decomposed level-by-level, ensuring complete coverage at each depth.
- **Cognitive Manageability**: 2-5 delegation constraint maintained, ensuring humans can reason about code.
- **Depth Control**: User is prompted if recursion exceeds reasonable depth (>5 levels).
- **More Classes, Fewer Methods**: Each class has perfect (1.0) or near-perfect (≥0.9) cohesion with minimal methods.
- **Human-in-the-Loop**: User is consulted when fallback convergence is reached or depth limits exceeded.

---

## 🔧 Implementation Phase Management

### Overview
After the analysis phase (Agents 1-7) completes, the Orchestrator **MUST** evaluate whether implementation is required based on the Metrics Monitor output.

### Required Behavior

1. When **Agent 7 (Metrics Monitor)** reports `converged: false`, the Orchestrator **MUST** initiate the implementation phase.
2. The Orchestrator **MUST** invoke **Agent 9 (Code Implementation Agent)** with all analysis outputs from Agents 1-7.
3. Agent 9 **MUST** complete all code changes before the Orchestrator restarts the analysis loop.
4. After implementation completes, the Orchestrator **MUST** re-run the full analysis sequence (Agents 1-7) on the refactored code.
5. The Orchestrator **MUST** track which iteration produced which code changes for rollback capability.

### Implementation Phase Flow

```
AFTER Agent 7 reports convergence status:
  IF converged == false AND iteration < max_iterations:
    INVOKE Agent 9 (Code Implementation Agent)
    WAIT for implementation completion
    INCREMENT iteration counter
    RESTART from Agent 1 (Code Structure Analyzer)
  ELSE IF converged == true:
    GENERATE final certification
    EXIT with success
  ELSE:
    REPORT failure to converge
    EXIT with error
  ENDIF
```

### Implementation Tracking

The Orchestrator **MUST** maintain:
1. A log of which files were modified in each iteration
2. Metrics before and after each implementation phase
3. Any compilation or semantic errors encountered
4. Rollback capability to previous iteration if fail-fast triggered

---


## 🔁 Naming Compliance Integration

### **Naming Validation**
The **Encapsulation Enforcer Agent (Agent 4)** enforces the **noun–verber rule** as part of its normal execution within the breadth-first flow.
All extracted classes are automatically validated for naming compliance during Agent 4 execution.

### **Additional Guarantees**
1. Claude **MUST** run Agent 4 for every extracted class at every depth level.
2. All extracted or renamed classes **MUST** pass the noun–verber test before Ownership (Agent 5) or Abstraction (Agent 6) run.
3. If any naming violation is detected, Agent 4 **MUST** perform automatic renaming before proceeding.
4. The **Metrics Monitor (Agent 7)** **MUST** include Naming Compliance as a convergence metric to ensure full alignment across depth levels.

---

## 🧠 Integration Guidelines

| Connected Component | Data Shared | Purpose |
|---------------------|--------------|----------|
| Metrics & Convergence Monitor | Convergence state, metric deltas | Determine loop stability |
| All Refactoring Agents | Execution order and results | Enforce sequencing and restart logic |
| External Systems | Reports and certification outputs | Archive results for audit and analysis |

---

## 🏁 Final Output

When all agents complete successfully and convergence thresholds are met, the Orchestrator **MUST** produce a final certification report that includes:

- Timestamped summary of all iterations.  
- Final metrics and thresholds achieved.  
- Agent completion log.  
- Stability declaration (“Refactor Converged: TRUE”).  
- Optional export in JSON, Markdown, and CSV formats.  

---
