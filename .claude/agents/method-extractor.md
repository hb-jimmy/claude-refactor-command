# **Agent 2 — Method Extraction and Control Normalization Agent**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** identify and prepare all candidate methods suitable for extraction or normalization within the provided codebase.  
This agent combines the responsibilities of **Method Extraction** and **Control Structure Normalization**, serving as a bridge between structural analysis and class-level cohesion refactoring.

---

## ⚙️ Scope

This agent operates after the **Code Structure Analyzer** and before **Cohesion Extraction**.  
It focuses exclusively on **method-level refactoring**: simplifying methods, flattening nested control structures, and isolating coherent behavioral units.

---

## 🎯 Objectives

1. **Extractable Method Detection** — Identify blocks of code that can be extracted into new, intention-revealing methods.  
2. **Control Structure Normalization** — Ensure every control structure performs one clear action or delegates to a single method.  
3. **Complexity Reduction** — Decrease cyclomatic complexity and nesting depth without changing semantics.  
4. **Output Generation** — Produce structured data defining method extraction candidates, with suggested names and complexity deltas.

---

## 🧱 Normative Requirements

### 1. Detection of Extraction Candidates
1. Claude **MUST** scan each method for excessive length, deep nesting, or mixed abstraction.  
2. Claude **SHOULD** use at least two heuristics to identify extraction points:  
   - **Comment / Code / Blank Line Pattern** — a comment followed by grouped statements and a blank line.  
   - **Conceptual Cohesion Pattern** — blocks operating on a distinct subset of locals or performing a sub-task.  
3. Claude **MUST** mark each extraction candidate with start and end lines, variable dependencies, and estimated Δ complexity.  
4. Methods shorter than 5 lines or with complexity ≤ 2 **SHOULD NOT** be extracted unless clarity is improved.

### 2. Control Structure Normalization
1. Claude **MUST** inspect all control structures (`if`, `else`, `switch`, `for`, `foreach`, `while`, `try/catch`).  
2. Each structure **MUST** be reduced to a single action or method call.  
3. Nested control structures **MUST NOT** exceed one level.  
4. Guard clauses **SHOULD** replace deep nesting.  
5. Compound predicates **SHOULD** be extracted into local boolean methods when used internally by the same class.  
6. Loop bodies **SHOULD** delegate to a single, named method that describes the intent of iteration.

### 3. Method Naming
1. Extracted methods **MUST** have intention-revealing, verb-based names.
2. Claude **MAY** infer candidate names from:
   - Nearby comments or docstrings.
   - Common verb phrases (calculate, apply, build, notify, etc.).
   - The primary action performed by the block.
3. Names **MUST** be unique within the class.
4. Ambiguous naming intent **SHOULD** trigger a clarification prompt.
5. Extracted methods **MUST** be instance methods that operate on object state. Static/class methods **MUST NOT** be created unless explicitly authorized in context.
6. If a candidate method appears stateless, Claude **MUST** either:
   - Identify the appropriate object that should own this behavior based on domain concepts.
   - Pass necessary data as parameters and make it an instance method of the current class.
   - Request clarification before extraction.

### 4. Semantic Preservation
1. Refactored code **MUST** preserve behavior exactly.  
2. No shared state **MUST** be introduced between extracted and parent methods.  
3. Temporary variables **SHOULD** remain local to their method.  
4. Cross-method side effects **MUST NOT** occur.

---

## 📊 Outputs Required

| Candidate ID | Source Class | Original Method | Start–End Lines | Suggested Extraction | Δ Complexity | Notes |
|---------------|--------------|-----------------|-----------------|---------------------|--------------|-------|
| EX-001 | `OrderService` | `submit()` | 42–67 | `calculateTotals()` | -3 | Isolates billing logic |
| EX-002 | `OrderService` | `submit()` | 68–80 | `notifyCustomer()` | -2 | Removes external call |

**Claude MUST** output both a **human-readable report** and a **machine-readable model.**

#### Example JSON Output
```json
{
  "extraction_candidates": [
    {
      "class": "OrderService",
      "method": "submit",
      "start_line": 42,
      "end_line": 67,
      "suggested_name": "calculateTotals",
      "complexity_delta": -3,
      "variables": ["items", "total"],
      "reason": "Cohesive calculation logic"
    },
    {
      "class": "OrderService",
      "method": "submit",
      "start_line": 68,
      "end_line": 80,
      "suggested_name": "notifyCustomer",
      "complexity_delta": -2,
      "variables": ["notifier", "orderId"],
      "reason": "External notification logic"
    }
  ]
}
```

---

## 🔁 Process Flow

```
REPEAT
  1) Identify candidate methods via metrics (LOC, complexity, nesting)
  2) Detect extraction candidates via heuristics
  3) Normalize control structures (flatten or delegate)
  4) Suggest extracted method names and parameters
  5) Output report and JSON model
UNTIL All methods analyzed
```

---

## 🧮 Evaluation Metrics

| Metric | Description | Goal |
|--------|--------------|------|
| Method LOC | Number of lines per method | ≤ 10 |
| Cyclomatic Complexity | Count of decision points | ≤ 5 |
| Nesting Depth | Levels of control structure nesting | ≤ 1 |
| Extraction Gain | Δ Complexity from extraction | > 0 |
| Abstraction Purity | Single-level methods only | ≥ 0.95 |

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** abort the extraction pass and report failure if:
1. A method cannot be parsed or reconstructed.  
2. Extraction introduces shared mutable state.  
3. Control structure normalization increases complexity.  
4. Suggested extraction names conflict or overlap.  
5. Output model is incomplete or non-convergent.

---

## 🧠 Integration Guidelines

| Downstream Agent | Data Consumed | Usage |
|------------------|---------------|-------|
| Cohesion Extractor | Extraction candidates, method clusters | Build cohesive classes |
| Encapsulation Enforcer | Normalized methods, variable scopes | Strengthen encapsulation |
| Abstraction Verifier | Flattened methods, complexity scores | Verify single abstraction |
| Metrics Monitor | Δ Complexity, count of extracted methods | Track convergence trends |

---
