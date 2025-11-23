# **Agent 3 — Cohesion and Class Extraction Agent**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** identify and group related methods and data into cohesive classes that embody the **Single Responsibility Principle (SRP)** and communicate only through messages.  
This agent creates new or reorganized class structures that achieve high cohesion, low coupling, and strict encapsulation while maintaining semantic equivalence.

---

## ⚙️ Scope

This agent operates after the **Method Extraction and Control Normalization Agent** and before the **Encapsulation Enforcer**.  
Its function is to reorganize methods and data fields into coherent, message-oriented objects.

---

## 🎯 Objectives

1. **Detect Cohesive Clusters** — Group related methods and fields based on shared data access and behavioral intent.  
2. **Extract Classes** — Create new classes for each cluster, ensuring that each one embodies a single responsibility.  
3. **Preserve Semantics** — Maintain original behavior and external interfaces while restructuring internal organization.  
4. **Define Clear Boundaries** — Remove cyclic dependencies and enforce one-way relationships between classes.

---

## 🧱 Normative Requirements

### 0. Single Responsibility Principle (Absolute Requirement)

1. Claude **MUST** detect all distinct responsibilities within each class.
2. A class **SHALL** be considered to have multiple responsibilities when:
   - Methods operate on disjoint sets of fields with no shared data access
   - Methods serve different domain concepts or business capabilities
   - Methods could be described by different verbs representing different actions
   - The class name requires "and" to describe what it does
3. When multiple responsibilities are detected, Claude **MUST** extract each responsibility into separate classes, regardless of:
   - Perceived impact on code complexity
   - Number of methods per responsibility
   - Current metric thresholds
   - Subjective clarity assessments
4. Extraction **MUST** continue recursively until each class has exactly **ONE** responsibility.
5. The only valid reasons to stop extraction are:
   - The class demonstrably has a single, cohesive responsibility
   - Extraction would violate semantic equivalence
   - Extraction would create classes with no core data fields (stateless utilities)
   - Extraction would create cyclic dependencies
6. "Additional decomposition would reduce clarity" is **NOT** a valid reason to avoid extraction.

### 1. Cluster Detection
1. Claude **MUST** analyze method–field usage patterns to detect clusters of cohesion.  
2. Two methods **SHOULD** be grouped together when they share access to the same data fields or operate within a consistent domain concept.  
3. Methods that do not share fields with others **MAY** indicate a candidate for relocation or isolation.  
4. Each cluster **MUST** have at least one core data field that the majority of its methods manipulate.  
5. Cyclic dependencies between clusters **MUST NOT** exist.

### 2. Class Extraction
1. Each detected cluster **MUST** be extracted into a new class named after the domain noun that best represents its purpose.
2. Extracted classes **MUST** expose only message-based interactions, never raw data.
3. Methods **MUST** become instance methods acting on private fields of their new class.
4. Cross-class method calls **MUST** use clear message-passing (e.g., `order.applyDiscount()` instead of `discountCalculator.calculate(order)`).
5. Each extracted class **MUST** reduce overall system coupling and increase local cohesion.
6. All methods within extracted classes **MUST** be instance methods. Static/class methods **MUST NOT** be created.
7. If Claude detects that a method cluster appears stateless, it **MUST** either identify missing state that should be fields, or request clarification before extraction.

### 3. Field Management
1. Fields used by multiple method clusters **MUST** be relocated to the owning class that best represents their semantic responsibility.  
2. Shared fields **MUST NOT** remain global or public.  
3. Transient external dependencies (e.g., `logger`, `db`, `client`) **SHOULD** remain as contextual parameters, not stored fields.  
4. Fields **MUST** be private and accessed only via internal logic or message-based operations.

### 4. Naming Conventions
1. Each extracted class **MUST** be named using a **domain noun**.  
2. Classes **MUST NOT** use action-based names (e.g., `Processor`, `Manager`, `Handler`) unless these are domain roles.  
3. Claude **MAY** infer names from:  
   - The dominant field names (`order`, `invoice`, `item`)  
   - Frequent noun phrases in method names or comments  
   - File and variable naming patterns in the source code  

---

## 📊 Outputs Required

| Extracted Class | Source Methods | Core Fields | External Context | Cohesion Score | Coupling Score | Notes |
|-----------------|----------------|--------------|------------------|----------------|----------------|-------|
| `Order` | `calculateTotal`, `submit`, `alertIfOverLimit` | `items`, `status` | `OrderEvents` | 0.94 | 0.22 | High cohesion, single responsibility |
| `CustomerNotifier` | `notifyCustomer`, `composeMessage` | None | `EmailService` | 0.88 | 0.35 | Pure adapter logic |

**Claude MUST** output both a **Markdown summary** and a **machine-readable JSON model.**

#### Example JSON Output
```json
{
  "extracted_classes": [
    {
      "name": "Order",
      "source_methods": ["calculateTotal", "submit", "alertIfOverLimit"],
      "core_fields": ["items", "status"],
      "external_context": ["OrderEvents"],
      "cohesion_score": 0.94,
      "coupling_score": 0.22,
      "notes": "High cohesion, domain-driven class extracted"
    },
    {
      "name": "CustomerNotifier",
      "source_methods": ["notifyCustomer", "composeMessage"],
      "core_fields": [],
      "external_context": ["EmailService"],
      "cohesion_score": 0.88,
      "coupling_score": 0.35,
      "notes": "Adapter class isolated from domain logic"
    }
  ]
}
```

---

## 🔁 Process Flow

```
REPEAT
  1) Build method–field usage map from analysis data
  2) Compute cohesion and coupling scores
  3) Cluster methods by shared field access and domain concept
  4) Extract cohesive clusters into new classes
  5) Reassign fields and remove cyclic dependencies
  6) Generate Markdown + JSON reports
UNTIL All methods organized into cohesive classes
```

---

## 🧮 Evaluation Metrics

| Metric | Description | Target |
|--------|--------------|--------|
| Cohesion Score | Relatedness of methods sharing fields | ≥ 0.9 |
| Coupling Score | Degree of external dependency | ≤ 0.3 |
| Class Purity | Methods act only on internal data | 100% |
| SRP Compliance | One responsibility per class (ABSOLUTE) | 100% (REQUIRED) |
| Cyclic Dependencies | Detected cycles in dependency graph | 0 |

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** abort the extraction pass and report failure if:
1. Cohesion cannot be computed for more than 20% of methods.
2. Any extracted class creates a cyclic dependency.
3. A class has no core data fields.
4. Two extracted classes share mutable state.
5. Semantic equivalence cannot be maintained.
6. Multiple responsibilities detected in any class without extraction plan.
7. Extraction stopped due to subjective clarity concerns rather than technical violations.  

---

## 🧠 Integration Guidelines

| Downstream Agent | Data Consumed | Usage |
|------------------|---------------|-------|
| Encapsulation Enforcer | Extracted classes and private field definitions | Enforce strict data hiding |
| Naming Discipline | Extracted class names | Verify domain naming compliance |
| Predicate Eliminator | Message-passing structure | Eliminate cross-object predicates |
| Metrics Monitor | Cohesion, coupling, SRP metrics | Track convergence |
| Refactoring Orchestrator | Class extraction results | Loop control and iteration decisions |

---
