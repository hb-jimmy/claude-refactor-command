# /refactor Command Requirements

## Overview

The `/refactor` command extracts distinct responsibilities from a class or method into separate classes following object-oriented principles. It produces more classes with fewer methods, where each class has exactly one responsibility.

### Fundamental Principle

**A refactoring is a functionality-neutral change.** The code must do exactly the same thing before and after the refactoring.

---

## 1. Command Interface

### Invocation

```
/refactor <file> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--scope=class\|method` | Specify refactoring scope |
| `--method=<name>` | Method to refactor (required if scope=method) |
| `--resume=<file>` | Resume from a saved refactoring state file |
| `--help` | Display help text |

### Help Text

```
/refactor --help

Usage: /refactor <file> [options]

Extracts distinct responsibilities from a class or method into
separate classes following object-oriented principles.

Options:
  --scope=class|method    Specify refactoring scope
  --method=<name>         Method to refactor (required if scope=method)
  --resume=<file>         Resume from a saved refactoring state file

Scope Details:
  class   - Refactor the entire class. All public methods retain their
            signatures for backward compatibility, but their
            implementations may change to delegate to extracted classes.

  method  - Refactor a specific method only. Only the contents of that
            method will be changed. Other methods remain untouched.

Examples:
  /refactor src/order.py --scope=class
  /refactor src/order.py --scope=method --method=process
  /refactor --resume=refactoring_state.md
```

### No-Parameter Invocation

When `/refactor` is called without parameters, display available options and proceed to interactive questions:

```
/refactor

Available options:
  --scope=class|method    Specify refactoring scope
  --method=<name>         Method to refactor (required if scope=method)
  --resume=<file>         Resume from a saved refactoring state file

Let's proceed interactively.

What file would you like to refactor?
```

### Interactive Flow

If scope is omitted, prompt the user:

```
What scope would you like to refactor?
  1. class - Refactor entire class
  2. method - Refactor a specific method
```

If method scope is selected without `--method`, prompt:

```
Which method would you like to refactor?
Available methods:
  - process
  - validate
  - calculate_total
```

### Error Handling for Method Not Found

Use fuzzy matching when method name is not found:

```
❌ Error: Method 'processOrdre' does not exist in Order

   Did you mean 'process'?

   Available methods:
     - process
     - validate
     - calculate_total
```

---

## 2. Supported Languages

### Primary Languages

- **C#**
- **Python**

### Fallback

If implementations diverge too much between C# and Python, fall back to a **language-agnostic** approach.

### Language-Specific Conventions

Always follow language standards:
- **Python:** `snake_case` file names (e.g., `inventory.py`)
- **C#:** `PascalCase` file names (e.g., `Inventory.cs`)

---

## 3. Scope Options

### Class-Level Scope (`--scope=class`)

- Analyze entire class holistically
- Identify 2-5 distinct responsibilities across all methods and fields
- Extract each responsibility to its own class
- Apply breadth-first recursion to extracted classes until complete
- All public methods retain their signatures for backward compatibility
- Method implementations may change to delegate to extracted classes

### Method-Level Scope (`--scope=method --method=<name>`)

- Analyze only the specified method
- Identify responsibilities within that method
- Extract those responsibilities to new classes
- Apply full breadth-first recursion to extracted classes (same as class-level)
- Only the contents of that method will be changed
- Other methods remain untouched

### Scope Constraints

- **Single target per refactoring:** Specify one class OR one method per command invocation
- **Class is the largest scope:** No package or multi-file refactoring

---

## 4. Responsibility Identification

### What is a Distinct Responsibility?

A distinct responsibility is a separate concern representing a different reason to change. Each responsibility should be extractable to its own class.

**Example:** `process()` with 4 steps represents FOUR distinct responsibilities:
1. Order validation (different rules, different reasons to change)
2. Inventory management (different data, different business rules)
3. Payment processing (different external systems, different regulations)
4. Shipping coordination (different logistics, different providers)

### 2-5 Cognitive Constraint

- Humans can reason about 2-5 things at once
- Methods should delegate to 2-5 other classes (not more)
- If >5 responsibilities are identified, group into higher-level abstractions
- **Must ask user permission to exceed this constraint**

### Finding Higher-Level Abstractions

When 6+ responsibilities are identified, group them:

```python
# 8 responsibilities: validate, checkInventory, reserveInventory,
# chargePayment, handleRefunds, createShipment, notifyCustomer, logTransaction

# Group into 3 higher-level responsibilities:
def process(self, order):
    order.prepare()           # validate + inventory operations
    payment.process(order)    # charge + refund handling
    fulfillment.complete(order)  # shipment + notification + logging
```

If difficult to find higher-level abstractions, prompt user for help.

### Anti-Stovepipe Rule

**Minimum extraction: 2 classes** (cannot extract just 1)

When only 1 responsibility is identified:
- Leave class as-is (don't extract)
- Extract 2+ responsibilities or don't extract at all

Single-method classes must have ≥2 downstream dependencies to avoid useless wrappers.

### Cohesion Analysis

**Primary approach (for non-decomposed code):**
- Analyze **variable cohesion** — which fields/variables are used together
- Look for clusters of fields accessed together
- Each cluster likely represents a distinct responsibility

**Additional context clues:**
- Blank lines between code sections indicate separate responsibilities
- Section comments signal distinct responsibilities

### Convergence Criteria

**Primary rule:** Extract until no more distinct responsibilities can be identified.

**At each recursive level:**
1. Analyze the class for distinct responsibilities
2. If responsibilities found → propose extraction, get approval, extract
3. If no more responsibilities found → prompt user to confirm analysis
4. Provide reasoning and useful context for your conclusion
5. User may suggest further extractions → follow their suggestions
6. User confirms no more extractions needed → class is complete

**This confirmation happens for EVERY recursive refactoring.**

---

## 5. Parallel Extraction and Agent Architecture

### Overview

The `/refactor` command orchestrates the refactoring process. When extracting classes, it spawns multiple extraction agents that run concurrently (one per class).

### Extraction Agent Input

Each extraction agent receives:
- Source file path
- Class being extracted from
- Name of the new class to create
- Responsibility description
- Fields to move
- Code sections to move

### Extraction Agent Output

Each extraction agent returns:
- Success/failure status
- Path to created file

### On Agent Failure

- Stop immediately
- Offer option to rollback current refactoring level before stopping
- If agents need to ask questions frequently, it indicates the orchestration needs enhancement

### Parallel Extraction Limits

The 2-5 responsibility constraint naturally limits parallelization. No explicit cap needed.

### Updating the Original Class

After all extraction agents complete successfully, the orchestrating command updates the original class atomically:
- Add imports for extracted classes
- Modify constructor to accept/create extracted classes
- Update method bodies to delegate to extracted classes
- Remove moved fields
- Remove moved code sections

---

## 6. Progress Display

### Hierarchical Tree View

Display progress as a hierarchical tree showing the refactoring structure:

```
Refactoring: Order (src/order.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key:
  ✅ Complete
  🔴 Needs Intervention
  🟡 Pending
  🔄 Currently Extracting
  🔵 Proposed, Awaiting Approval

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Order
├── ✅ Inventory
│   ├── ✅ Stock
│   └── ✅ Reservations
├── 🔄 PaymentChannel
│   ├── 🔴 Authorization
│   ├── ✅ Transactions
│   └── 🔄 Ledger
└── 🟡 Fulfillment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Authorization: Circular dependency detected with external
   class GatewayConfig. Please provide guidance.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Status Indicators

| Emoji | Status | Description |
|-------|--------|-------------|
| ✅ | Complete | Extraction finished successfully |
| 🔴 | Needs Intervention | User input required |
| 🟡 | Pending | Waiting to be analyzed |
| 🔄 | Currently Extracting | Extraction in progress |
| 🔵 | Proposed, Awaiting Approval | Proposed but not yet approved |

### Key Always Visible

The status key must always be displayed at the top of the progress view.

---

## 7. User Approval Workflow

### Proposal Display Template

Before extracting classes, present the proposal for user approval:

```
Analyzing: Order (src/order.py)
Scope: class

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Identified 3 distinct responsibilities to extract:

┌─────────────────────────────────────────────────────────────────┐
│ 1. Inventory                                                    │
├─────────────────────────────────────────────────────────────────┤
│ Responsibility: Manages stock levels and reservations          │
│                                                                 │
│ Fields to move:                                                 │
│   - stock: Dict[Product, int]                                  │
│   - reservations: List[Reservation]                            │
│                                                                 │
│ Code sections to move:                                          │
│   - Lines 45-67: Stock checking logic                          │
│   - Lines 89-112: Reservation creation and management          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 2. PaymentChannel                                               │
├─────────────────────────────────────────────────────────────────┤
│ Responsibility: Handles payment authorization and charging      │
│                                                                 │
│ Fields to move:                                                 │
│   - gateway: PaymentGateway                                    │
│   - transaction_log: List[Transaction]                         │
│                                                                 │
│ Code sections to move:                                          │
│   - Lines 134-156: Payment authorization                       │
│   - Lines 158-189: Charge processing and logging               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 3. Fulfillment                                                  │
├─────────────────────────────────────────────────────────────────┤
│ Responsibility: Coordinates shipping and delivery               │
│                                                                 │
│ Fields to move:                                                 │
│   - shipping_providers: List[ShippingProvider]                 │
│   - shipments: List[Shipment]                                  │
│                                                                 │
│ Code sections to move:                                          │
│   - Lines 201-245: Shipment creation                           │
│   - Lines 247-280: Provider selection and dispatch             │
└─────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Field 'customer' is used by multiple responsibilities.
    It will be copied to: Fulfillment
    It will remain in: Order
    This may indicate additional responsibilities to extract.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proceed with extraction? (approve/modify/abort)
```

### User Response Options

1. **Approve** — Proceed with extraction as proposed

2. **Suggest different responsibility distribution** — User disagrees with grouping. Agent re-evaluates and presents a complete new proposal.

3. **Suggest alternate names** — Agent updates the proposal display with new names (no full re-evaluation).

4. **Ask for justification** — Agent explains reasoning. User may provide new constraints, triggering a full re-evaluation.

5. **Abort** — Stop refactoring. Agent offers to document:
   - The current proposal
   - The up-to-date tracking/checklist information

### Shared Field Warning

When a field is used by multiple responsibilities:
- Copy the field to the extracted class
- Keep the field in the original class
- Display warning at the bottom of the proposal
- This scenario likely indicates a failure to identify distinct responsibilities correctly

---

## 8. Naming Conventions

### Domain-Oriented Naming

Use domain nouns, not services/managers/processors:

**Correct:**
- `order.validate()` not `orderValidator.validate(order)`
- `inventory.reserve(order)` not `inventoryChecker.reserve(order)`
- `payment.charge(order)` not `paymentProcessor.charge(order)`

**Principle:** Objects act on their own data.

### Noun-Verber Prohibition

**Do NOT propose noun-verber names.** Use judgment to avoid nouns that describe an action.

**Exception:** Controller classes are acceptable (universally accepted pattern).

**User override:** If the user requests a noun-verber name, accept but gently warn:

```
⚠️  Warning: 'PaymentProcessor' follows the noun-verber pattern.
    Consider using 'Payment' instead to better represent the domain object.
    Proceeding with your requested name.
```

### Existing Noun-Verbers

Leave existing noun-verber classes in place unless they prevent putting responsibilities in the correct class. If conflict occurs, ask the user what to do.

**Do NOT rename or change the purpose of an existing class without user consent.**

---

## 9. Encapsulation Rules

### For Newly Created Classes

1. **All fields must be private** — no exceptions
2. **Do not create properties** — properties expose internal state and break encapsulation
3. Objects are abstractions of data AND the operations on that data

### Data Flow Rules

**What an object MAY return:**
- Newly created objects (factory methods)
- Calculated values (results of operations)

**What an object must NEVER return:**
- Its dependencies
- Its internal state/data

**Pattern:** Instead of asking an object for its data and operating on it externally, tell the object to perform the operation itself:

```python
# WRONG - asking for data, operating externally
items = inventory.get_items()
total = calculate_price(items)

# RIGHT - telling object to operate on its own data
total = inventory.calculate_total()
```

### Dependency Injection

- **Prefer constructor injection** — dependencies should be injected when the object is created
- **Method parameters acceptable** — only when data cannot be known at construction time
- **Do not instantiate external dependencies directly** — if found, refactor to use injection
- If no reasonable alternative, prompt user for help

### External Dependencies and Adapters

When detecting external/third-party dependencies:
- Automatically create adapters
- Use proper noun naming conventions (no "Adapter" suffix)

```python
# WRONG
class HttpAdapter:
    ...

# RIGHT
class Http:
    def get(self, url):
        return requests.get(url)
```

---

## 10. Public Interface Preservation

### Public Method Signatures

- **ALL public methods** on the class being refactored must remain with the same signature
- Method contents may be refactored (delegate to extracted classes)
- Signature and intent must NOT change
- This preserves backward compatibility for all client code

### Constructor Exception

Unlike other public methods, **constructor signatures MAY be modified** to accept injected dependencies.

When modifying a constructor:
1. Find usages of the class (ask user for search scope)
2. Inform user what needs to be updated
3. Offer to make these changes for the user
4. Update in batches of 10 with user approval between batches

### Batch Update Display

Show for each batch:
- File path and line number
- Current code (before change)
- Proposed change (after)

### Scope Boundaries

- Refactoring scope does NOT expand upstream to client code (except constructor usages when offered)
- Only the target class and newly extracted classes are modified

### Functionality Change Requests

If user asks for functionality changes during refactoring:
- **REFUSE**
- Ask if they would like to proceed with just the refactoring part
- Functionality changes and refactoring are separate operations

---

## 11. Circular Reference Handling

### Rule

**Refuse to create circular imports/references.**

Extracted classes must NEVER reference each other directly. They don't know the others exist. The original class orchestrates all interaction between collaborators.

### Resolution Strategy

When circular reference is detected (e.g., `A → B → C → A`):

1. Introduce an interface (C#) or Protocol (Python)
2. Change `C` to depend on the interface instead of `A`
3. Have `A` implement the interface
4. Use a **method** (not constructor) to give `C` a reference to `A`

### Language-Specific Approach

**C# (and languages with interfaces):**
- Introduce an interface to break the cycle

**Python:**
- Use `Protocol` (from `typing` module)
- This provides static duck typing with type safety

```python
from typing import Protocol

class Orderable(Protocol):
    def get_items(self) -> list: ...
    def get_total(self) -> float: ...

class Fulfillment:
    def ship(self, order: Orderable) -> None:
        items = order.get_items()
        ...
```

### Temporal Coupling

Method injection (instead of constructor) creates temporal coupling. Accept this as a necessary tradeoff to break the cycle.

### If Resolution Not Possible

- Ask user for help
- Give user option to rollback or abort

---

## 12. Testing Requirements

### Before Refactoring Begins

1. Locate tests for the class being refactored
   - Search for common patterns (e.g., `test_order.py`, `OrderTests.cs`)
   - Look for test directory structures
   - If not found, ask user to locate them
2. Execute tests — all must pass
3. **If tests fail before refactoring, ABORT** — cannot refactor broken code

### During Refactoring

- Run tests after each depth level completes (all extractions at that level done)
- All tests must pass before proceeding to next depth
- Run the same top-level tests throughout — no need for tests specific to extracted classes

### After Refactoring Completes

- Offer to run the full test suite
- Let the user decide whether to run it

### On Test Failure After Refactoring

- Prompt user for guidance
- Be ready to rollback
- Do not proceed until all tests pass

---

## 13. Error Handling

### Severity Levels

| Indicator | Level | Description |
|-----------|-------|-------------|
| ❌ | Error | Cannot proceed |
| ⚠️ | Warning | Can proceed but user should be aware |
| ℹ️ | Info | Helpful context |

### Error Message Format

```
❌ Error: [Brief description]

   Reason: [Specific cause]

   [Explanation of why this blocks progress and what needs to change]
```

### Example Error

```
❌ Error: Cannot proceed with refactoring.

   Reason: Class 'Order' has public property 'total'.

   Public fields/properties prevent proper refactoring.
   The design must be changed before refactoring can succeed.
```

### Rollback Options

**On extraction failure:**
1. Prompt user for guidance to correct the issue
2. Keep prompting until:
   - User provides sufficient guidance, OR
   - User decides to rollback
3. Rollback deletes newly created files and updates resume state to reflect current actual state

**Multiple failures:** Prompt user once per failure.

---

## 14. Resume Functionality

### Invocation

```
/refactor --resume=refactoring_state.md
```

### Resume State File Format

```markdown
# Refactoring State: Order

## Target
- **File:** src/order.py
- **Class:** Order
- **Scope:** class
- **Started:** 2025-12-01 14:32:00

## Refactoring History

### Depth 0 (Complete)
| Original Class | Extracted Class | File Created | Status |
|----------------|-----------------|--------------|--------|
| Order | Inventory | src/inventory.py | Complete |
| Order | PaymentChannel | src/payment_channel.py | Complete |
| Order | Fulfillment | src/fulfillment.py | Complete |

### Depth 1 (In Progress)
| Original Class | Extracted Class | File Created | Status |
|----------------|-----------------|--------------|--------|
| Inventory | Stock | src/stock.py | Complete |
| Inventory | Reservations | src/reservations.py | Complete |
| PaymentChannel | - | - | Pending |
| Fulfillment | - | - | Pending |

## Current State
- **Current Depth:** 1
- **Classes Pending Analysis:** PaymentChannel, Fulfillment

## Pending Checklist
- [ ] Analyze PaymentChannel for responsibilities
- [ ] Analyze Fulfillment for responsibilities
- [x] Analyze Inventory for responsibilities
- [x] Extract Stock from Inventory
- [x] Extract Reservations from Inventory

## Files Modified
| File | Action | Original Hash |
|------|--------|---------------|
| src/order.py | Modified | a1b2c3d4 |
| src/inventory.py | Created | - |
| src/payment_channel.py | Created | - |
| src/fulfillment.py | Created | - |
| src/stock.py | Created | - |
| src/reservations.py | Created | - |

## Current Proposal (Aborted During Review)

Analyzing: PaymentChannel (src/payment_channel.py)

### Identified 2 distinct responsibilities to extract:

#### 1. Authorization
**Responsibility:** Validates payment methods and authorizes transactions

**Fields to move:**
- gateway: PaymentGateway
- auth_tokens: Dict[str, AuthToken]

**Code sections to move:**
- Lines 23-45: Gateway connection and auth token management
- Lines 47-62: Authorization request handling

#### 2. Transactions
**Responsibility:** Records and manages transaction history

**Fields to move:**
- transaction_log: List[Transaction]
- pending_charges: List[PendingCharge]

**Code sections to move:**
- Lines 78-95: Transaction recording
- Lines 97-134: Charge processing and reconciliation

### Warnings
- Field `merchant_id` is used by multiple responsibilities. Will be copied to both Authorization and Transactions.

## Abort Reason
User chose to abort during proposal review for PaymentChannel.
```

### Resume Validation

When resuming, if any file has changed (detected via hash), **abort** and inform the user that the state is invalid.

---

## 15. Updating Usages

### When Constructor Signatures Change

1. Ask user for search scope
2. Find all usages
3. Inform user what needs to be updated
4. Offer to make changes

### Batch Updates

- **Batch size:** 10 usages
- Show for each usage in batch:
  - File path and line number
  - Current code (before)
  - Proposed change (after)
- Get user approval before applying batch
- Repeat for remaining batches

---

## 16. Edge Cases and Constraints

### Pre-Refactoring Validation (Fail Fast)

**Check immediately and REFUSE refactoring if:**

1. **Public fields exist** (any language)
2. **Public properties exist** (any language)
3. **Protected fields/properties exist**
4. **Python `@property` decorators exist**
5. **Data-only classes** (`@dataclass`, `record`, classes with no behavior)
6. **Syntax errors** (file won't parse)

**Warn but proceed if:**
- Python fields missing `_` prefix convention

### Data-Only Classes

**Block refactoring for:**
- Classes using `@dataclass`, `record`, or similar markers
- Classes with no behavior methods (only expose data)

**Rationale:** If a class has no behavior other than exposing data, there is nothing to refactor without changing functionality.

**Using dataclasses as parameters/return types in extracted classes:**
- Do not allow
- Ask user how to proceed
- Offer abort option

### Empty or Trivial Classes

- **Empty class:** Nothing to do, stop
- **Constructor only:** May refactor, prompt user if questions arise
- **Single responsibility (nothing to extract):** Inform user with context, follow their suggestions

### Inheritance

- May refactor any code in the class
- Cannot change method signatures
- Must remain a valid child class of the parent when done

### Inherited Methods

If user requests to refactor a method that is only defined in a parent class (not overridden):
- **ABORT**
- Inform user the method is not defined in the target class

### Multiple Classes Per File

- If unclear which class to refactor, prompt user and list options
- If user specifies exact class, refactor only that class
- Leave other classes untouched
- Watch for inappropriate cross-class access (fields/properties that would force abort)

### File Organization

- **Location:** Extracted classes go in same directory as original class
- **One class per file:** Each extracted class gets its own file

### Static Methods

**For new code:**
- Always create instance methods
- If static seems natural, the design is likely wrong — rethink using OO principles
- If still stuck, prompt user for help

**For existing static methods:**
- **Private static:** May be refactored (converted to instance methods)
- **Public static:** Must remain static for backward compatibility, stay in original class

### External Dependencies

- Treat like any other field — may move to extracted classes
- Prefer constructor injection over internal instantiation
- Automatically create adapters for third-party dependencies
- Use proper noun names (no "Adapter" suffix)

---

## 17. Object-Oriented Design Principles

### Single Level of Abstraction

The top-level class defers ALL logic to collaborators. No partial delegation with local logic mixed in.

### Collaborators Don't Know About Each Other

Extracted classes:
- Receive only the data they need
- Return results
- Never reference other extracted classes
- The calling class passes data between collaborators

### Tell, Don't Ask

Instead of:
```python
data = object.get_data()
result = process(data)
```

Do:
```python
result = object.process()
```

### Objects Own Their Behavior

The object that owns the data should own the operations on that data.

**Example:**
```python
class Order:
    def process(self, inventory, payment_channel, fulfillment):
        reserved_items = inventory.reserve(self.items)
        payment_channel.charge(self.total)
        fulfillment.ship(reserved_items, self.address)
```

`Order` owns `process` because it owns the data (`items`, `total`, `address`). It passes what collaborators need, and they operate on their own internal state.
