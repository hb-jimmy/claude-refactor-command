# **Agent 3 — Cohesion and Class Extraction Agent**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** identify and group related methods and data into cohesive classes that embody the **Single Responsibility Principle (SRP)** and communicate only through messages.  
This agent creates new or reorganized class structures that achieve high cohesion, low coupling, and strict encapsulation while maintaining semantic equivalence.

---

## ⚙️ Scope

This agent operates after the **Code Structure Analyzer (Agent 1)** and before the **Encapsulation Enforcer (Agent 4)**.
Its function is to extract pre-identified responsibilities into separate classes, ensuring each class has exactly ONE responsibility.

**CRITICAL:** This agent now receives 2-5 pre-identified responsibilities from Agent 1 and extracts each into its own class. It does NOT perform responsibility identification itself - that work is done by Agent 1.

---

## 🎯 Objectives

1. **Consume Pre-Identified Responsibilities** — Receive 2-5 distinct responsibilities identified by Agent 1, each with associated field clusters and code sections.
2. **Extract Responsibility-Based Classes** — Create one new class per identified responsibility, moving associated fields and code.
3. **Enforce 2-5 Delegation Constraint** — Ensure the original class/method delegates to 2-5 extracted classes (for human cognitive load management).
4. **Anti-Stovepipe Validation** — Ensure single-method classes have ≥2 downstream dependencies; prevent useless wrapper extraction.
5. **Target Cohesion = 1.0** — Each extracted class should have perfect cohesion (single responsibility), with fallback to ≥0.9.
6. **Preserve Semantics** — Maintain original behavior and external interfaces while restructuring internal organization.
7. **Define Clear Boundaries** — Remove cyclic dependencies and enforce one-way relationships between classes.

---

## 🧱 Normative Requirements

### 0. Single Responsibility Principle (Absolute Requirement)

1. Claude **MUST** extract pre-identified responsibilities from Agent 1 into separate classes.
2. A class **SHALL** be considered to have multiple responsibilities when Agent 1 has identified 2+ distinct responsibilities (based on field cohesion clustering, blank line separators, section comments, and semantic analysis).
3. When multiple responsibilities are provided by Agent 1, Claude **MUST** extract each responsibility into a separate class, regardless of:
   - Perceived impact on code complexity
   - Number of methods per responsibility
   - Current metric thresholds
   - Subjective clarity assessments
4. Extraction **MUST** continue recursively (breadth-first) until each class has exactly **ONE** responsibility (cohesion = 1.0).
5. The only valid reasons to stop extraction are:
   - The class demonstrably has a single, cohesive responsibility (Agent 1 identified only 1 responsibility)
   - Extraction would violate semantic equivalence
   - Extraction would create cyclic dependencies
   - Minimum 2 classes not achievable (anti-stovepipe - see requirement 3)
6. "Additional decomposition would reduce clarity" is **NOT** a valid reason to avoid extraction.

### 1. Responsibility Consumption (from Agent 1)
1. Claude **MUST** receive from Agent 1:
   - 2-5 distinct responsibilities (or 1 if single-responsibility already achieved)
   - For each responsibility: name (domain noun), associated field cluster, associated code sections, confidence level
2. If Agent 1 provides only 1 responsibility, Claude **MUST** skip extraction and mark the class as converged.
3. If Agent 1 provides 2-5 responsibilities, Claude **MUST** extract each into its own class.
4. If Agent 1 flags >5 responsibilities with ambiguous grouping, Claude **MUST** prompt the user for guidance before proceeding.

### 2. 2-5 Delegation Constraint (Cognitive Load Management)
1. After extraction, the original class/method **MUST** delegate to 2-5 extracted classes (not more, not less).
2. This constraint ensures human cognitive load remains manageable (humans can reason about 2-5 things at once).
3. If extraction would result in >5 delegations, Claude **MUST**:
   - Work with Agent 1 to find higher-level abstractions that group related responsibilities
   - If grouping is ambiguous, Claude **MUST** prompt the user for guidance
4. If extraction would result in <2 classes, this violates the anti-stovepipe rule (see requirement 3).
5. Exceeding the 2-5 constraint is **ONLY** permitted with explicit user approval.

### 3. Anti-Stovepipe Validation
1. Claude **MUST NOT** extract fewer than 2 classes from a multi-responsibility class.
2. If an extracted class has only 1 method, Claude **MUST** verify it has ≥2 downstream dependencies (calls to other objects/classes).
3. A single-method class with <2 downstream dependencies is a "stovepipe" (useless wrapper) and **MUST NOT** be created.
4. Example of INVALID stovepipe:
   ```java
   // BAD - 1 method, 1 downstream dependency
   class OrderValidator {
       void validate(Order order) {
           order.validate(); // just wraps Order
       }
   }
   ```
5. Example of VALID single-method class:
   ```java
   // GOOD - 1 method, 3 downstream dependencies
   class OrderProcessor {
       void process(Order order) {
           order.validate();
           inventory.reserve(order);
           payment.charge(order);
       }
   }
   ```

### 4. Responsibility-Based Class Extraction
1. For each responsibility identified by Agent 1, Claude **MUST** create a new class with:
   - The responsibility name as the class name (domain noun)
   - All fields from the associated field cluster moved to the new class
   - All code from the associated code sections moved to appropriate methods in the new class
2. Each extracted class **MUST** be named using a **domain noun**.
3. Extracted classes **MUST** expose only message-based interactions, never raw data.
4. Methods **MUST** become instance methods acting on private fields of their new class.
5. Cross-class method calls **MUST** use clear message-passing (e.g., `order.validate()` instead of `orderValidator.validate(order)`).
6. Each extracted class **MUST** target cohesion = 1.0 (single responsibility) with fallback to ≥0.9.
7. Each extracted class **MUST** target coupling ≤ 0.3.
8. All methods within extracted classes **MUST** be instance methods. Static/class methods **MUST NOT** be created.
9. If Claude detects that a responsibility appears stateless (no fields), it **MUST** either identify missing state that should be fields, or request clarification before extraction.

### 5. Field Management
1. Fields from each responsibility's field cluster **MUST** be moved to the corresponding extracted class.
2. Shared fields **MUST NOT** remain global or public.
3. Transient external dependencies (e.g., `logger`, `db`, `client`) **SHOULD** remain as contextual parameters, not stored fields.
4. Fields **MUST** be private and accessed only via internal logic or message-based operations.

### 6. Naming Conventions
1. Each extracted class **MUST** use the responsibility name provided by Agent 1 (a domain noun).
2. Classes **MUST NOT** use action-based names (e.g., `Processor`, `Manager`, `Handler`, `Service`, `Controller`) unless these are legitimate domain roles.
3. If Agent 1's suggested name violates noun-verber rules, Claude **MUST** correct it before extraction.  

---

## 📊 Outputs Required

| Extracted Class | Responsibility Source | Core Fields | Delegation Count | Cohesion Score | Coupling Score | Downstream Deps | Notes |
|-----------------|----------------------|--------------|------------------|----------------|----------------|-----------------|-------|
| `Order` | Agent 1: "Order" responsibility | `items`, `status` | N/A | 1.0 | 0.22 | 0 (leaf class) | Perfect cohesion, single responsibility |
| `Inventory` | Agent 1: "Inventory" responsibility | `stock`, `reservations` | N/A | 1.0 | 0.28 | 0 (leaf class) | Perfect cohesion, single responsibility |
| `Payment` | Agent 1: "Payment" responsibility | `gateway`, `transactions` | N/A | 0.95 | 0.32 | 1 (gateway) | Near-perfect cohesion |
| `OrderProcessor` | Original class (now delegates) | None (all extracted) | 3 | N/A | 0.15 | 3 (Order, Inventory, Payment) | Meets 2-5 delegation constraint |

**Claude MUST** output both a **Markdown summary** and a **machine-readable JSON model.**

#### Example JSON Output
```json
{
  "extraction_summary": {
    "original_class": "OrderProcessor",
    "responsibilities_identified": 3,
    "classes_extracted": 3,
    "delegation_count": 3,
    "meets_2_5_constraint": true,
    "anti_stovepipe_violations": 0
  },
  "extracted_classes": [
    {
      "name": "Order",
      "responsibility_source": "Agent 1: Order responsibility",
      "core_fields": ["items", "status"],
      "methods": ["validate", "calculateTotal"],
      "cohesion_score": 1.0,
      "coupling_score": 0.22,
      "downstream_dependencies": 0,
      "notes": "Perfect cohesion, single responsibility"
    },
    {
      "name": "Inventory",
      "responsibility_source": "Agent 1: Inventory responsibility",
      "core_fields": ["stock", "reservations"],
      "methods": ["reserve", "checkAvailability"],
      "cohesion_score": 1.0,
      "coupling_score": 0.28,
      "downstream_dependencies": 0,
      "notes": "Perfect cohesion, single responsibility"
    },
    {
      "name": "Payment",
      "responsibility_source": "Agent 1: Payment responsibility",
      "core_fields": ["gateway", "transactions"],
      "methods": ["charge", "refund"],
      "cohesion_score": 0.95,
      "coupling_score": 0.32,
      "downstream_dependencies": 1,
      "notes": "Near-perfect cohesion, will be recursively analyzed"
    }
  ],
  "remaining_class": {
    "name": "OrderProcessor",
    "role": "Delegator",
    "methods": ["processOrder"],
    "delegation_count": 3,
    "delegates_to": ["Order", "Inventory", "Payment"]
  }
}
```

---

## 🔁 Process Flow

```
FOR EACH class at current depth level:
  1) Receive pre-identified responsibilities from Agent 1 (2-5 responsibilities, or 1 if single-responsibility)
  2) IF only 1 responsibility identified:
       - Skip extraction, mark class as converged
       - CONTINUE to next class
  3) IF 2-5 responsibilities identified:
       - Validate 2-5 delegation constraint will be met
       - FOR EACH responsibility:
           a) Create new class with responsibility name (domain noun)
           b) Move associated field cluster to new class
           c) Move associated code sections to new class
           d) Compute cohesion (target 1.0) and coupling (target ≤0.3)
           e) IF extracted class has 1 method:
                - Count downstream dependencies
                - FAIL if <2 dependencies (anti-stovepipe violation)
       - Update original class to delegate to 2-5 extracted classes
       - Verify no cyclic dependencies created
  4) IF >5 responsibilities flagged by Agent 1:
       - Prompt user for guidance on grouping
       - Wait for user response before proceeding
  5) Generate Markdown + JSON reports with:
       - Extraction summary
       - Each extracted class with metrics
       - Delegation count validation
       - Anti-stovepipe validation results
  6) Mark extracted classes for breadth-first recursive analysis
UNTIL All classes at current depth processed
```

---

## 🧮 Evaluation Metrics

| Metric | Description | Target |
|--------|--------------|--------|
| Cohesion Score | Relatedness of methods sharing fields | 1.0 (ideal), ≥ 0.9 (fallback) |
| Coupling Score | Degree of external dependency | ≤ 0.3 |
| Class Purity | Methods act only on internal data | 100% |
| SRP Compliance | One responsibility per class (ABSOLUTE) | 100% (REQUIRED) |
| Delegation Count | Number of classes delegated to | 2-5 (human cognitive load constraint) |
| Anti-Stovepipe | Single-method classes have ≥2 downstream deps | 100% (REQUIRED) |
| Cyclic Dependencies | Detected cycles in dependency graph | 0 |

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** abort the extraction pass and report failure if:
1. Agent 1 provides no responsibility data (integration failure).
2. Any extracted class creates a cyclic dependency.
3. Delegation count would exceed 5 without user approval.
4. Delegation count would be <2 (anti-stovepipe violation).
5. Single-method extracted class has <2 downstream dependencies (anti-stovepipe violation).
6. Two extracted classes share mutable state.
7. Semantic equivalence cannot be maintained.
8. Agent 1 flags >5 responsibilities but user does not respond to grouping prompt.
9. Extraction stopped due to subjective clarity concerns rather than technical violations.  

---

## 🧠 Integration Guidelines

| Upstream Agent | Data Provided | Usage |
|----------------|---------------|-------|
| **Code Structure Analyzer (Agent 1)** | **2-5 identified responsibilities per class, field clusters, code sections** | **Primary input: drives all extraction decisions** |

| Downstream Agent | Data Consumed | Usage |
|------------------|---------------|-------|
| Encapsulation Enforcer (Agent 4) | Extracted classes and private field definitions | Enforce strict data hiding |
| Ownership Enforcer (Agent 5) | Message-passing structure | Eliminate cross-object predicates |
| Abstraction Enforcer (Agent 6) | Extracted class methods | Enforce single-level abstraction |
| Metrics Monitor (Agent 7) | Cohesion=1.0, coupling≤0.3, delegation count, anti-stovepipe validation | Track convergence and flag issues |
| Refactoring Orchestrator (Agent 10) | Extracted classes list (for breadth-first recursion) | Track which classes need recursive analysis at next depth level |

---
