# **Agent 5 — Ownership and Boundary Enforcement Agent**

**BCP 14 Boilerplate**  
The key words **“MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “NOT RECOMMENDED”, “MAY”,** and **“OPTIONAL”** in this document are to be interpreted as described in **RFC 2119** and **RFC 8174**.

---

## 🧩 Mission

Claude **MUST** enforce full behavioral and structural ownership across the codebase.  
This includes eliminating cross-object predicates (e.g., `is*/has*`), removing outside-pull notifications, and preventing any external component (e.g., adapter or service) from controlling or exposing domain entities.  
Objects **MUST** act on their own data, communicate through **message-passing**, and respect strict **boundary isolation**.

---

## ⚙️ Scope

This agent operates after the **Encapsulation Enforcer Agent** and before the **Abstraction Verifier Agent**.  
It integrates the responsibilities of both **Ownership Enforcement** and **Boundary Checking**, ensuring that no ownership or encapsulation violations persist either internally or externally.

---

## 🎯 Objectives

1. **Internal Ownership Enforcement** — Ensure objects act on their own data rather than exposing it.  
2. **External Boundary Protection** — Prevent external systems (e.g., adapters, notifiers) from manipulating domain entities.  
3. **Eliminate Cross-Object Predicates** — Replace state-based external control with owner-driven command methods.  
4. **Replace Outside-Pull Notifications** — Convert `adapter.method(entity)` patterns into observer-port or mediator-based communication.  
5. **Preserve Semantic Equivalence** — Ensure that all behavioral transformations maintain original functionality.  

---

## 🧱 Normative Requirements

### 1. Predicate Ownership Rules
1. Claude **MUST** detect all public methods beginning with `is` or `has`.  
2. Claude **MUST** locate any external use of these predicates in conditional logic.  
3. Predicates used for external decisions **MUST** be replaced with owner-driven command methods.  
4. Internal predicates **MAY** remain private if used exclusively within the owning object.  
5. Boolean-returning methods exposing internal state **MUST NOT** remain public.  
6. Predicate-based logic **MUST** be refactored into message-passing behavior (e.g., `order.alertIfOverLimit()`).  

### 2. Boundary Ownership Rules
1. Claude **MUST NOT** allow external components to “pull” or act on entire domain entities.  
2. Any pattern of the form `adapter.method(entity)` or `notifier.entityUpdated(entity)` **MUST** trigger refactoring.  
3. Domain entities **MUST** own their outbound communication by invoking port interfaces directly (observer pattern).  
4. Data Transfer Objects (DTOs) **MUST NOT** exist between domain and infrastructure layers.  
5. Claude **MAY** use **Observer Ports** or **Mediators** as boundary interfaces, provided the domain retains behavioral ownership.  
6. All domain-to-adapter communication **MUST** pass only primitive or immutable values.  

### 3. Message-Passing Integrity
1. Domain objects **MUST** perform actions internally and notify external systems via message calls.  
2. Any external decision-making involving domain data **MUST** be replaced with internal logic or event dispatch.  
3. Polymorphism **SHOULD** replace external predicate-based branching.  
4. The resulting communication flow **MUST** maintain directionality: domain → port → adapter.  

---

## 📊 Outputs Required

| Violation ID | Type | Location | Suggested Refactor | Notes |
|---------------|------|-----------|--------------------|-------|
| OWN-001 | Cross-Object Predicate | `OrderService.submit()` | Replace `if (order.isOverLimit())` with `order.alertIfOverLimit(limit, notifier)` | Moves decision to owner |
| OWN-002 | Outside-Pull Notification | `NotifierService.send(order)` | Replace with `order.submit(orderEvents)` via observer port | Prevents domain leakage |
| OWN-003 | DTO Violation | `adapter.save(orderDTO)` | Replace DTO with domain event call `orderRepository.save(orderId, amount)` | DTOs forbidden |
| OWN-004 | Public Predicate | `User.hasOutstandingBalance()` | Refactor to `user.suspendIfOutstanding(policy)` | Moves control to data owner |

#### Example JSON Output
```json
{
  "ownership_boundary_violations": [
    {
      "id": "OWN-001",
      "type": "Cross-Object Predicate",
      "class": "OrderService",
      "method": "submit",
      "predicate": "order.isOverLimit",
      "suggested_fix": "Replace with order.alertIfOverLimit(limit, notifier)",
      "notes": "Moves decision to owner"
    },
    {
      "id": "OWN-002",
      "type": "Outside-Pull Notification",
      "location": "NotifierService.send",
      "suggested_fix": "Replace with order.submit(events) using observer port",
      "notes": "Eliminates domain leakage"
    },
    {
      "id": "OWN-003",
      "type": "DTO Violation",
      "class": "OrderRepository",
      "method": "save",
      "suggested_fix": "Replace DTO with explicit primitive arguments",
      "notes": "Domain must not emit DTOs"
    }
  ]
}
```

---

## 🔁 Process Flow

```
REPEAT
  1) Identify all cross-object predicates and external control patterns
  2) Detect and refactor outside-pull notifications and DTO usage
  3) Replace violations with owner-executed commands or observer ports
  4) Validate internal and external ownership boundaries
  5) Output Markdown + JSON reports
UNTIL All ownership and boundary violations eliminated
```

---

## 🧮 Evaluation Metrics

| Metric | Description | Target |
|--------|--------------|--------|
| Cross-Object Predicate Count | Predicate calls from outside the owning object | 0 |
| Outside-Pull Notifications | Calls where adapters act on domain entities | 0 |
| DTO Violations | Data objects crossing domain boundaries | 0 |
| Ownership Compliance Score | Combined internal/external ownership compliance | ≥ 0.95 |
| Behavioral Parity | Pre/post refactor tests passing | 100% |

---

## ⚠️ Fail-Fast Conditions

Claude **MUST** halt and report failure if:
1. Any cross-object predicate remains in the codebase.  
2. Any `adapter.method(entity)` pattern persists after enforcement.  
3. Any DTO is used between domain and infrastructure.  
4. Ownership transfer between layers (domain → adapter → domain) occurs.  
5. Behavioral equivalence cannot be maintained after refactor.  

---

## 🧠 Integration Guidelines

| Downstream Agent | Data Consumed | Usage |
|------------------|---------------|-------|
| Abstraction Verifier | Updated class methods and message flow | Verify abstraction purity |
| Metrics Monitor | Ownership, DTO, and boundary metrics | Track convergence |
| Refactoring Orchestrator | Ownership and boundary violation reports | Control iterative restarts |
| Encapsulation Enforcer | Confirmed private data maps | Validate encapsulation remains intact |

---
