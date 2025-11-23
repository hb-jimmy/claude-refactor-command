# **Agent 6 — Abstraction Enforcer Agent**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** verify that every method in the codebase operates at a **single level of abstraction** and adheres to the principles of minimalism, clarity, and delegation.  
The purpose of this agent is to eliminate mixed abstraction logic, long methods, and inconsistent delegation patterns by enforcing uniform conceptual depth throughout the codebase.

---

## ⚙️ Scope

This agent operates after the **Ownership and Boundary Enforcement Agent** and before the **Metrics & Convergence Monitor Agent**.  
It focuses on evaluating **method purity**, **abstraction depth**, and **delegation consistency**, ensuring that each method maintains a coherent conceptual boundary.

---

## 🎯 Objectives

1. **Single-Level Abstraction Verification** — Ensure each method expresses a single, consistent conceptual layer.  
2. **Method Size Limitation** — Enforce a strict limit on method length (≤ 5 executable lines).  
3. **Delegation Consistency** — Verify that methods either perform direct logic or pure delegation, not both.  
4. **Flattened Control Flow** — Detect and eliminate unnecessary nesting beyond one level.  
5. **Abstraction Clarity Reporting** — Produce metrics and refactor suggestions for methods violating abstraction rules.

---

## 🧱 Normative Requirements

### 1. Method Length and Complexity
1. Every method **MUST** be ≤ 5 executable lines in length.  
2. Methods exceeding this threshold **MUST** be decomposed via Method Extraction (Agent 2).  
3. Cyclomatic complexity per method **MUST** be ≤ 3 unless explicitly justified.  
4. Deeply nested logic (depth > 1) **MUST NOT** exist.  
5. Loops and conditionals **MUST** delegate to named, intention-revealing methods when possible.

### 2. Abstraction Level Enforcement
1. Each method **MUST** maintain a single conceptual level (e.g., business logic, orchestration, or primitive operations).  
2. Mixing high-level orchestration with low-level operations **MUST NOT** occur.  
3. Method names **SHOULD** clearly reflect their abstraction level.  
4. Method calls within a class **MUST** flow top-down (higher → lower abstraction).  
5. Inline control structures within high-level orchestration methods **SHOULD** be replaced with delegation calls.

### 3. Delegation Consistency
1. A method **MUST** be either a **delegator** or a **doer**, not both.  
2. Methods combining data manipulation and orchestration logic **MUST** be split.  
3. All non-trivial logic inside orchestration layers **SHOULD** be delegated to specialized helper methods.  
4. Delegated methods **MAY** reside within the same class if cohesive, or in collaborator objects if cross-domain.

---

## 📊 Outputs Required

| Method | Lines (Before) | Lines (After) | Abstraction Mode | Mixed Level Found? | Suggested Resolution |
|---------|----------------|---------------|------------------|--------------------|----------------------|
| `OrderService.submit()` | 14 | 5 | Orchestration | ✅ Yes | Extract payment and notification logic |
| `Invoice.calculateTotal()` | 9 | 4 | Domain Logic | ⚠️ Partial | Inline redundant loop, delegate discounts |
| `Customer.notify()` | 3 | 3 | Delegation | ❌ No | Compliant |

#### Example JSON Output
```json
{
  "abstraction_violations": [
    {
      "method": "OrderService.submit",
      "lines_before": 14,
      "lines_after": 5,
      "abstraction_mode": "Orchestration",
      "mixed_level": true,
      "suggested_fix": "Extract payment and notification logic"
    },
    {
      "method": "Invoice.calculateTotal",
      "lines_before": 9,
      "lines_after": 4,
      "abstraction_mode": "Domain Logic",
      "mixed_level": false,
      "suggested_fix": "Delegate discount computation"
    }
  ]
}
```

---

## 🔁 Process Flow

```
REPEAT
  1) Scan all methods for size, nesting depth, and complexity
  2) Classify abstraction level: Orchestration / Domain Logic / Primitive Operation
  3) Detect mixed abstraction violations and recommend refactors
  4) Suggest extractions or delegations to restore purity
  5) Generate Markdown + JSON reports
UNTIL All methods conform to single-level abstraction
```

---

## 🧮 Evaluation Metrics

| Metric | Description | Target |
|--------|--------------|--------|
| Method Length | Executable lines per method | ≤ 5 |
| Cyclomatic Complexity | Decision points per method | ≤ 3 |
| Nesting Depth | Control flow nesting levels | ≤ 1 |
| Mixed Abstraction Count | Methods mixing conceptual layers | 0 |
| Abstraction Purity Score | Ratio of pure methods | ≥ 0.95 |

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** abort and report failure if:
1. Any method exceeds 5 executable lines without justification.  
2. Any method contains more than one abstraction level.  
3. Nesting depth exceeds one level in any function.  
4. Delegation direction (top-down) is violated.  
5. Output model omits required abstraction metrics.

---

## 🧠 Integration Guidelines

| Downstream Agent | Data Consumed | Usage |
|------------------|---------------|-------|
| Metrics & Convergence Monitor | Abstraction metrics, purity score | Track convergence and loop stability |
| Refactoring Orchestrator | Violation and fix reports | Trigger iteration or fail-fast restart |
| Encapsulation Enforcer | Method structure and naming | Validate internal purity alignment |
| Ownership Enforcer | Ownership-driven method flow | Ensure abstraction level matches object responsibility |

---
