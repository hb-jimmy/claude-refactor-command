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

1. **Code Structure Analyzer**
2. **Method Extraction and Control Normalization Agent**
3. **Cohesion and Class Extraction Agent**
4. **Encapsulation Enforcer Agent**
5. **Ownership and Boundary Enforcement Agent**
6. **Abstraction Enforcer Agent**
7. **Metrics and Convergence Monitor Agent**
9. **Code Implementation Agent**  

---

## 🎯 Objectives

1. **Sequential Execution** — Run all agents in defined dependency order.  
2. **Error and Violation Handling** — Detect, report, and respond to fail-fast conditions.  
3. **Iteration Management** — Repeat agent sequence until convergence thresholds are met.  
4. **Dependency Resolution** — Ensure each agent receives the data from its required predecessors.  
5. **Final Certification** — Produce the final report certifying refactoring stability, purity, and convergence.  

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
REPEAT
  # ANALYSIS PHASE
  1) Execute all analysis agents in defined order (Agents 1-7)
  2) Collect outputs and validate success criteria
  3) Aggregate metrics and detect convergence state
  4) Check for fail-fast violations

  # IMPLEMENTATION PHASE (if metrics below threshold)
  5) IF convergence NOT achieved:
       Execute Agent 9 (Code Implementation Agent)
       Apply all identified refactorings
       Validate compilation and semantic equivalence
     ENDIF

  # CONVERGENCE CHECK
  6) IF all metrics pass → STOP and certify
     ELSE IF implementation completed → Restart from Agent 1 with new code
     ELSE → STOP with error

UNTIL Convergence achieved or abort triggered (max 10 iterations)
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

## 🧱 Additional Responsibility — Recursive Class Refinement

### Overview
When a new class is extracted during the refactoring process, the Orchestrator **MUST** recursively re-run the relevant refinement agents to ensure that the new class itself is fully simplified and encapsulated.  
This recursive process creates a **hierarchical refinement cycle**, ensuring that each extracted class is as small, focused, and internally pure as possible.

---

### Required Behavior

1. When a new class is extracted (by the **Cohesion and Class Extraction Agent**), the Orchestrator **MUST** reapply the following sequence:  
   **Step 3 → Step 4 → Step 5 → Step 6**, corresponding to:  
   - **3. Cohesion and Class Extraction**  
   - **4. Encapsulation Enforcer**  
   - **5. Ownership and Boundary Enforcement**  
   - **6. Abstraction Enforcer**

2. This recursion **MUST** continue until no additional valid class extractions can be identified, or until all derived classes achieve stable metrics.

3. If a newly extracted class contains **three (3) or fewer methods**, the Orchestrator **SHOULD** skip Steps 3 (further class extraction) and begin directly at **Step 4 (Encapsulation Enforcement)**.  
   - Rationale: classes with ≤3 methods are typically already atomic in purpose and unlikely to yield meaningful sub-extractions.

4. The Orchestrator **MAY** decide *not* to create new classes ONLY if:
   - No method or field clusters meet the extraction thresholds.
   - The class demonstrably has a single responsibility.
   - Cohesion ≥ 0.9 AND coupling ≤ 0.3 AND SRP compliance = 100%.
   - Extraction would violate technical constraints (no fields, cyclic dependencies, semantic violations).

5. The Orchestrator **MUST NOT** skip extraction based on:
   - Subjective assessments of clarity or simplicity
   - Concern about creating "too many" classes
   - Preference for fewer, larger classes over many small classes

---

### Recursive Execution Flow

```
FOR EACH extracted_class IN new_classes:
    IF method_count > 3:
        RUN Agents [3, 4, 5, 6] on extracted_class
    ELSE:
        RUN Agents [4, 5, 6] on extracted_class
    ENDIF
    IF extracted_class spawns new sub-classes:
        RECURSE on each new class
    ENDIF
UNTIL no further extraction candidates exist
```

---

### Expected Outcome

- Deeply nested yet **coherent object hierarchies** emerge organically.  
- Each extracted class becomes a **minimal functional unit** — small, encapsulated, and self-contained.  
- System-level complexity **flattens**, yielding fewer dependencies and higher maintainability.  
- The Orchestrator maintains **refinement equilibrium**, stopping only when no further meaningful simplifications are possible.

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


## 🔁 Updated Recursive Refinement Flow

### **Naming Audit Pre-Flight**
Before each recursive refinement pass begins, the Orchestrator **MUST** invoke the **Encapsulation Enforcer Agent (Agent 4)** in naming-audit mode.  
This ensures that all existing and newly extracted classes conform to the **noun–verber rule** and naming discipline before any downstream agents execute.

### **Revised Recursive Execution Logic**
```
FOR EACH extracted_class IN new_classes:
    RUN Agent 4 (Encapsulation Enforcer) in Naming Reevaluation mode
    IF method_count > 3:
        RUN Agents [3, 4, 5, 6] on extracted_class
    ELSE:
        RUN Agents [4, 5, 6] on extracted_class
    ENDIF
    IF extracted_class spawns new sub-classes:
        RECURSE on each new class
    ENDIF
UNTIL no further extraction candidates exist
```

### **Additional Guarantees**
1. Claude **MUST** re-run Agent 4 immediately after any new class extraction, rename, or split operation.  
2. All extracted or renamed classes **MUST** pass the noun–verber test before Ownership (Agent 5) or Abstraction (Agent 6) run.  
3. If any naming violation is detected mid-recursion, the Orchestrator **MUST** halt the refinement of that class, perform automatic renaming, and restart the cycle from Agent 4.  
4. The **Metrics Monitor (Agent 7)** **MUST** include Naming Compliance as a convergence metric to ensure full alignment across passes.

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
