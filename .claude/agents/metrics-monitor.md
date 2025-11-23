# **Agent 7 — Metrics and Convergence Monitor Agent**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** continuously evaluate, track, and enforce structural and behavioral convergence across all refactoring agents.  
This agent ensures that the entire system of refactored code achieves measurable improvement across cohesion, complexity, abstraction purity, and encapsulation metrics.  
It also provides **fail-fast enforcement**, halting the loop when violations or regressions occur.

---

## ⚙️ Scope

This agent operates after the **Abstraction Enforcer Agent** and before the **Refactoring Orchestrator Agent**.  
It aggregates quantitative data from all prior agents, computes convergence metrics, detects regressions, and signals completion or restart conditions.

---

## 🎯 Objectives

1. **Metric Aggregation** — Collect and unify metrics from all preceding agents.  
2. **Convergence Detection** — Determine when refactoring has reached stable, compliant thresholds.  
3. **Violation Monitoring** — Detect when fail-fast conditions occur or when previous passes introduce regressions.  
4. **Trend Analysis** — Track complexity, cohesion, and abstraction trends across iterations.  
5. **Reporting and Certification** — Produce a consolidated convergence report with metric deltas and compliance state.

---

## 🧱 Normative Requirements

### 1. Metric Collection
1. Claude **MUST** gather all metric outputs from upstream agents, including:  
   - Cyclomatic Complexity (from Analyzer, Method Extractor).  
   - Cohesion and Coupling Scores (from Class Extractor).  
   - Encapsulation and Naming Compliance (from Enforcer).  
   - Ownership and Boundary Violations (from Ownership Agent).  
   - Abstraction Purity (from Abstraction Enforcer).  
2. Each metric **MUST** be normalized to a scale between 0.0 and 1.0 for comparative tracking.  
3. Historical iteration metrics **MUST** be retained to evaluate convergence trends.  

### 2. Convergence Evaluation

#### Primary Convergence Criteria (Ideal Goal)
1. Claude **MUST** determine convergence when ALL of the following are met:
   - **Cohesion = 1.0** (perfect single responsibility) for each class
   - **One-Sentence Test Passed**: Each class purpose can be described in one sentence without using "and"
   - Both metric (1.0) and semantic (one-sentence) criteria must be satisfied
   - No fail-fast violations remain active
   - Agent 1 identifies only 1 responsibility per class

#### Fallback Convergence Criteria (Pragmatic Goal)
2. If primary convergence cannot be achieved, Claude **MAY** accept fallback convergence when:
   - **Cohesion ≥ 0.9** (near-single responsibility)
   - **Complexity below threshold** (≤ 3.5 average per method)
   - **No more distinct responsibilities can be identified** by Agent 1
   - **Human review flag raised**: Class is flagged for user review and guidance
   - The rate of improvement per iteration < 0.01 for three consecutive passes

#### Convergence Actions
3. If primary convergence is achieved, Claude **MUST** mark the class as *converged* and move to next class in breadth-first order.
4. If fallback convergence is reached, Claude **MUST**:
   - Flag the class for human review
   - Prompt user for guidance on whether to continue or accept current state
   - Wait for user response before proceeding
5. If convergence fails or regressions occur, Claude **MUST** signal the Orchestrator to re-initiate upstream agents.  

### 3. Fail-Fast Monitoring
1. The agent **MUST** detect and report any fail-fast triggers inherited from prior stages, including:  
   - Public fields or accessors reintroduced.  
   - New cross-object predicates or DTOs.  
   - Increases in cyclomatic complexity or decreased cohesion.  
   - Methods exceeding abstraction or size limits.  
2. When fail-fast triggers occur, the monitor **MUST** immediately terminate the iteration and flag affected agents.  
3. Each fail-fast event **MUST** include the triggering metric, location, and responsible agent.  

---

## 📊 Outputs Required

### Example Markdown Summary
| Metric | Source Agent | Previous | Current | Δ Change | Target | Status |
|---------|---------------|----------|----------|----------|---------|--------|
| Cohesion | Class Extractor | 0.92 | 1.0 | +0.08 | 1.0 (ideal), ≥0.9 (fallback) | ✅ PRIMARY |
| One-Sentence Test | Metrics Monitor | N/A | Pass | N/A | Pass | ✅ PRIMARY |
| Coupling | Class Extractor | 0.36 | 0.25 | -0.11 | ≤ 0.3 | ✅ Pass |
| Complexity | Analyzer | 4.2 | 3.1 | -1.1 | ≤ 3.5 | ✅ Pass |
| Encapsulation | Enforcer | 0.91 | 0.96 | +0.05 | ≥ 0.95 | ✅ Pass |
| Ownership | Ownership Enforcer | 0.87 | 0.94 | +0.07 | ≥ 0.9 | ✅ Pass |
| Abstraction Purity | Abstraction Enforcer | 0.93 | 0.96 | +0.03 | ≥ 0.95 | ✅ Pass |
| Delegation Count | Class Extractor | N/A | 3 | N/A | 2-5 | ✅ Pass |
| Anti-Stovepipe | Class Extractor | N/A | Pass | N/A | 100% | ✅ Pass |

### Example JSON Output
```json
{
  "convergence_type": "primary",
  "convergence_metrics": {
    "cohesion": 1.0,
    "one_sentence_test": true,
    "coupling": 0.25,
    "complexity": 3.1,
    "encapsulation": 0.96,
    "ownership": 0.94,
    "abstraction_purity": 0.96,
    "delegation_count": 3,
    "anti_stovepipe_pass": true
  },
  "converged": true,
  "convergence_level": "primary",
  "human_review_required": false,
  "fail_fast_triggered": false,
  "iteration_count": 7,
  "classes_pending_review": []
}
```

---

## 🔁 Process Flow

```
REPEAT
  1) Collect metrics from all prior agents
  2) Normalize and aggregate into unified structure
  3) Evaluate convergence thresholds
  4) Detect regressions or fail-fast violations
  5) Generate trend reports (Markdown + JSON)
UNTIL Convergence achieved or fail-fast condition triggered
```

---

## 🧮 Evaluation Metrics and Targets
### 🧩 Naming Compliance Metric

Claude **MUST** track **Naming Compliance** as a core convergence metric to ensure all class names adhere to the **domain noun rule** (no noun–verber forms).  
This metric guarantees that naming conventions remain consistent across all recursive refinements and agent passes.

1. **Definition:** Measures the percentage of classes that conform to the domain noun rule.  
2. **Detection:** Class names matching `/([A-Z][a-z0-9]+)+(Manager|Processor|Handler|Service|Controller)$/` **MUST** be flagged as violations.  
3. **Computation:**  
   - **Naming Compliance Score** = (Number of compliant class names ÷ Total classes) × 100  
4. **Target Threshold:** **100% compliance required** for convergence.  
5. **Agent Integration:**  
   - The **Encapsulation Enforcer (Agent 4)** reports naming violations.  
   - The **Orchestrator (Agent 8)** uses this score to determine re-run necessity.  
   - The **Metrics Monitor (Agent 7)** aggregates compliance results into each iteration summary.  
6. **Reporting:** Naming Compliance **MUST** be included in all Markdown and JSON convergence summaries.

---


| Metric | Description | Target | Source |
|--------|--------------|--------|---------|
| **Cohesion (Primary)** | **Degree of relatedness within each class** | **1.0 (ideal), ≥ 0.9 (fallback)** | **Class Extractor** |
| **One-Sentence Test (Primary)** | **Class purpose describable without "and"** | **Pass (required for primary convergence)** | **Metrics Monitor** |
| Coupling | Inter-class dependency ratio | ≤ 0.3 | Class Extractor |
| Complexity | Average cyclomatic complexity per method | ≤ 3.5 | Analyzer |
| Encapsulation | Private field integrity compliance | ≥ 0.95 | Enforcer |
| Ownership | Internal/external ownership compliance | ≥ 0.9 | Ownership Agent |
| Abstraction Purity | Methods maintaining single abstraction level | ≥ 0.95 | Abstraction Enforcer |
| SRP Compliance | One responsibility per class (ABSOLUTE) | 100% (REQUIRED) | Class Extractor |
| **Delegation Count** | **Number of classes delegated to** | **2-5 (cognitive load constraint)** | **Class Extractor** |
| **Anti-Stovepipe** | **Single-method classes have ≥2 downstream deps** | **100% (REQUIRED)** | **Class Extractor** |
| Convergence Stability | Δ improvement across 3 iterations | < 0.01 | Metrics Monitor |
| Naming Compliance | Classes conform to domain noun rule (no noun–verber) | 100% | Encapsulation Enforcer |
| Static Method Count | Methods declared as static/class methods | 0 | Encapsulation Enforcer |

---

## ⚠️ Fail-Fast Conditions

- **SRP Compliance:** If any class is detected with multiple responsibilities, Claude **MUST** trigger extraction regardless of other metrics. SRP violations take precedence over all other considerations except semantic preservation.
- **Naming Compliance:** If any class name matches the noun–verber pattern, Claude **MUST** trigger a fail-fast event and re-run Agents 3 → 4 on the affected class.
- **Static Methods:** If any static/class method is detected, Claude **MUST** trigger a fail-fast event and re-run Agent 4 on the affected class.


Claude **MUST** halt convergence monitoring and report a failure if:
1. Any metric falls below 80% of its target threshold.
2. Any fail-fast event is propagated from upstream agents.
3. Convergence improvement trends reverse (negative Δ for 2+ consecutive iterations).
4. The system exceeds 10 total iterations without stability.
5. Metric data is missing or corrupted from any required agent.

---

## 🧠 Integration Guidelines

| Downstream Agent | Data Consumed | Usage |
|------------------|---------------|-------|
| Refactoring Orchestrator | Convergence status, fail-fast flags | Determine loop continuation or completion |
| All Upstream Agents | Individual metric deltas | Adjust heuristics and thresholds for next iteration |
| Reporting/Visualization Layer | Trend data | Generate dashboards and compliance certification |

---
