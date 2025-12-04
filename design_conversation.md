# Refactoring Tool Redesign: Conversation Summary

## Initial Problem Statement

**User Goal:** Change how the refactoring tool works to focus on decomposing classes based on cohesion and functionality, rather than just extracting methods.

**Current Issue:** The tool does a great job decomposing code into small methods, but tends to create classes with a large number of methods and then stop. This improves code quality, but we can do significantly better.

**Desired Outcome:**
- Focus on decomposing classes based on cohesion and distinct responsibilities
- Decompose a method to call 2-5 methods on other classes that represent distinct responsibilities
- Recursively extract responsibilities to classes until all distinct responsibilities are extracted
- Continue using cohesion, coupling, and cyclomatic complexity metrics to understand when to stop

---

## Question 1: Refactoring Scope

**Question:** Should we always refactor at the class level wholistically, or should users be able to specify different scopes?

### User Response

**User-driven scope selection** - The user should decide the scope as part of the command invocation.

**Scope Options:**
- **Class-level:** Refactor the entire class (all responsibilities)
- **Method-level:** Refactor a specific method (extract its responsibilities)

**If scope is omitted, the tool MUST ask questions for clarity before proceeding.**

### Command Syntax

```bash
# Explicit class-level scope
/refactor_code src/OrderProcessor.java --scope=class

# Explicit method-level scope
/refactor_code src/OrderProcessor.java --scope=method --method=processOrder

# No scope specified - interactive prompts
/refactor_code src/OrderProcessor.java
> "What scope would you like to refactor?"
>   1. class - Refactor entire class
>   2. method - Refactor a specific method
>
> User: method
>
> "Which method would you like to refactor?"
>   Available methods: processOrder, validateInput, calculateTotal
```

### Scope Behaviors

**Class-Level Scope (`--scope=class`):**
- Analyze entire class wholistically
- Identify 2-5 distinct responsibilities across all methods and fields
- Extract each responsibility to its own class
- Apply breadth-first recursion to extracted classes until complete

**Method-Level Scope (`--scope=method --method=methodName`):**
- Analyze only the specified method
- Identify responsibilities within that method
- Extract those responsibilities to new classes
- **Apply full breadth-first recursion to extracted classes** (same as class-level)
- Leave rest of original class untouched
- Assume user will submit separate prompts for other methods if needed

### Field Handling for Method-Level Scope

**When method uses fields from the class:**

1. **Analyze field usage:**
   - Check if other methods in the class also access the same fields

2. **If no other methods use the field:**
   - **MOVE** field to extracted class
   - **REMOVE** field from original class

3. **If other methods also use the field:**
   - **COPY** field to extracted class
   - **KEEP** field in original class
   - **WARN** user about duplication

**Warning Example:**
```
⚠️  Field Duplication Detected:

    Field 'inventory' is now present in both:
    - OrderProcessor (original class)
    - InventoryChecker (extracted class)

    This may indicate that OrderProcessor has additional responsibilities
    that should be extracted. Consider running:

    /refactor_code OrderProcessor.java --scope=method --method=checkStock
    /refactor_code OrderProcessor.java --scope=method --method=updateInventory

    Or refactor the entire class:

    /refactor_code OrderProcessor.java --scope=class
```

### Error Handling

**Method not found - fuzzy matching:**
```bash
/refactor_code OrderProcessor.java --scope=method --method=processOrdre

❌ Error: Method 'processOrdre' does not exist in OrderProcessor

Did you mean 'processOrder'?

Available methods:
  - processOrder
  - validateInput
  - calculateTotal
```

### Scope Constraints

- **Single target per refactoring:** Specify one class OR one method per command invocation
- **Rationale:** Keeps scope reasonable and manageable

---

## Question 2: Responsibility Analysis

**Question:** What specifically defines a "distinct responsibility"?

### User Response - Interpretation B

**Distinct responsibilities** are separate concerns, each representing a different reason to change:

**Example:** `processOrder()` with 4 steps:

**NOT a workflow** (reject this interpretation):
- "Process an order from start to finish" = ONE responsibility
- 4 steps are just procedural flow

**YES - Four distinct responsibilities** (use this interpretation):
1. Order validation (different rules, different reasons to change)
2. Inventory management (different data, different business rules)
3. Payment processing (different external systems, different regulations)
4. Shipping coordination (different logistics, different providers)

**It is rarely a mistake to decompose into tiny pieces.**

### Domain-Oriented Naming Principle

**Correct approach - Domain nouns:**
- `order.validate()` not `orderValidator.validate(order)`
- `inventory.reserve(order)` not `inventoryChecker.reserve(order)`
- `payment.charge(order)` not `paymentProcessor.charge(order)`
- `fulfillment.ship(order)` not `shippingCoordinator.ship(order)`

**Key Principle:** Use domain nouns (Order, Inventory, Payment, Fulfillment) not services/managers/processors. Objects act on their own data.

### Hidden Responsibility Example

**Scenario:** `Inventory` class appears to have one responsibility but actually has two:

```java
class Inventory {
    // Cluster 1: Stock Management
    private Map<Product, Integer> stock;
    void updateStock(Product product, int quantity);

    // Cluster 2: Reservation Management
    private List<Reservation> reservations;
    void reserve(Order order);

    // Uses both clusters
    boolean checkAvailability(Product product);
}
```

**Extract to two classes:**

```java
class Stock {
    private Map<Product, Integer> levels;
    void update(Product product, int quantity);
    boolean isAvailable(Product product, int quantity);
}

class Reservations {
    private List<Reservation> items;
    void reserve(Order order, Stock stock);
}
```

**Avoid noun-verber trap:** Use `Reservations` not `ReservationManager`.

---

## Question 3: Order of Operations

**Question:** What should the new sequence be?

### User Response

**Responsibility-first approach:**
1. Identify responsibilities FIRST
2. Extract responsibilities into new classes
3. Recursively apply same process to those classes
4. **Only when no more responsibilities exist → extract methods for readability**

**Key Insight:** Current tool creates "classes with many methods" because it extracts methods too early, before identifying and extracting underlying responsibilities.

### Principles

**Data and operations move together:**
- When extracting a responsibility to a new class, move relevant methods AND fields together
- This is the essence of OOP: combining data with operations on that data
- Cohesion analysis is critical to ensure we move the right data

**Wholistic class-level analysis:**
- Identify responsibilities at the class level (all methods/fields together)
- Don't focus on individual methods - may lead to improper decomposition
- Be very careful to detect hidden responsibilities

---

## Question 4: Method Decomposition Target (2-5 Constraint)

**Question:** Is "decompose a method to call 2-5 methods on other classes" a natural result or a constraint?

### User Response

**It is a constraint** - cognitive load management for humans.

**Rationale:**
- Humans can only understand up to 5 things at once
- Exceeding makes it harder to reason about code
- Can be exceeded, but **only if no alternatives exist and you MUST ask permission first**

### Higher Level Abstraction

**Scenario:** We identify 8 distinct responsibilities.

**Problem:** Extracting all 8 to separate classes → original method calls 8 methods → violates 2-5 constraint.

**Solution:** Find **higher level of abstraction** - group the 8 into 2-5 broader responsibilities:

```java
// 8 responsibilities: validate, checkInventory, reserveInventory,
// chargePayment, handleRefunds, createShipment, notifyCustomer, logTransaction

// Group into 3 higher-level responsibilities:
void processOrder(Order order) {
    order.prepare();        // validate + inventory operations
    payment.process(order); // charge + refund handling
    fulfillment.complete(order); // shipment + notification + logging
}
```

Then recursively decompose: `order.prepare()` internally calls 3 sub-responsibilities, etc.

**Finding higher-level abstractions is part of responsibility identification.** If difficult to find, prompt user for help.

---

## Question 5: Agent 2 (Method Extractor) Timing

**Question:** When should Agent 2 (Method Extractor) run?

### User Response

**Agent 2 runs LAST** - becomes a final polish step.

**New flow:**
1. Recursively extract responsibilities → classes
2. When a class has no more responsibilities to extract
3. **Then** run Agent 2 to extract methods for readability/complexity reduction

**Agent 2 moves from being step 2 in the pipeline to being one of the last steps.**

**For both class-level and method-level scope:**
- Extract responsibilities to new classes
- Apply full breadth-first recursion to extracted classes
- Continue until cohesion = 1.0 (or fallback criteria)
- Only then run Agent 2 for method extraction

---

## Question 6: Stopping Criteria

**Question:** When do we stop recursively extracting responsibilities?

### User Response

**Primary Goal:** Cohesion = 1.0 (exactly ONE responsibility per class)

**However, that could be very difficult to achieve.** Use fallback criteria if primary goal proves too difficult.

### Convergence Measurement

**Both must agree:**
1. **Metric:** Cohesion = 1.0
2. **Semantic:** Class purpose describable in one sentence without using "and"

### Fallback Convergence

**If primary goal unattainable:**
- Cohesion ≥ 0.9 (near-single responsibility)
- Complexity ≤ 3.5
- No more distinct responsibilities identifiable
- **Flag class for human review and ask for help**

---

## Question 7: "Large Number of Methods" Problem

**Question:** Why does the current tool create classes with many methods?

### User Response

**Root cause:** Tool achieves cohesion ≥ 0.9 and stops.

**Problem:**
- Leaves classes with 15+ methods that look cohesive (0.9)
- But actually contain 3-4 hidden responsibilities
- Not enough class extraction happening

**Desired outcome:** **More classes with fewer methods**

**New Goal:**
- Target cohesion = 1.0 (not 0.9)
- More aggressive responsibility identification
- Result: More classes, fewer methods per class
- Each class truly has ONE responsibility

---

## Question 8: Recursive Depth

**Question:** How deep should responsibility extraction go?

### User Response

**Breadth-first decomposition:**
- Process all classes at current depth BEFORE descending to next depth level
- Track recursion depth
- **If depth > 5, prompt user to see if we should continue**

**No safeguard against single-method classes:**
- Frequent in well-maintained OO code
- **However:** If a class has only 1 method AND <2 downstream dependencies → creating stovepipe (useless wrapper)

### Anti-Stovepipe Rule

**Minimum extraction: 2 classes** (cannot extract just 1)

**Bad Example - Stovepipe (1 method, 1 dependency):**
```java
class OrderValidator {
    void validate(Order order) {
        order.validate(); // just wraps Order
    }
}
```

**Good Example - Useful delegation (1 method, 3 dependencies):**
```java
class OrderProcessor {
    void process(Order order) {
        order.validate();
        inventory.reserve(order);
        payment.charge(order);
    }
}
```

**When we identify only 1 responsibility:**
- Leave class as-is (don't extract)
- **Rule:** Extract 2+ responsibilities or don't extract at all

---

## Question 9: Cohesion Analysis Approach

**Question:** What should cohesion analysis detect?

### User Response

**Primary approach (for non-decomposed code):**
- Analyze **variable cohesion** - which fields/variables are used together throughout the class
- Look for clusters of fields accessed together
- Each cluster likely represents a distinct responsibility
- Extract those field clusters (+ code that uses them) to new classes

**Secondary approach (for already decomposed code):**
- Semantic grouping by purpose
- Validate with field-sharing cohesion metrics

### Example - Field Clustering

```java
class OrderProcessor {
    // Cluster 1: validation fields
    private List<Rule> rules;
    private ErrorLog errors;

    // Cluster 2: inventory fields
    private Map<Product, Integer> stock;
    private List<Reservation> reservations;

    // Cluster 3: payment fields
    private PaymentGateway gateway;
    private TransactionLog transactions;

    // 200 lines of code using these fields...
}
```

Variable cohesion analysis reveals 3 field clusters → 3 responsibilities → extract to 3 classes.

### Additional Context Clues

**Blank lines between code sections:**
- Strong indicator of separate responsibility

**Section comments:**
- Signal that distinct responsibility follows

**Example:**
```java
void processOrder(Order order) {
    // Validate order
    for (Rule rule : rules) {
        if (!rule.check(order)) {
            errors.add(rule.getMessage());
        }
    }

    // Check inventory (blank line + comment signal)
    for (Item item : order.getItems()) {
        if (stock.get(item.product) < item.quantity) {
            throw new OutOfStockException();
        }
    }
}
```

**Three signals point to 2 responsibilities:**
1. Fields `rules/errors` vs `stock` (different clusters)
2. Blank line separator between sections
3. Comments "Validate order" vs "Check inventory"

---

## Summary of Key Design Decisions

### 1. **User-Driven Scope Selection**
- User specifies `--scope=class` or `--scope=method --method=methodName`
- If omitted, tool asks questions until scope is clear
- Single target per refactoring (one class OR one method)
- Both scopes apply full breadth-first recursion to extracted classes

### 2. **Responsibility-First Approach**
- Identify 2-5 distinct responsibilities BEFORE extracting anything
- Use field cohesion clustering, blank lines, section comments, and semantics
- Extract responsibilities to separate classes (not methods within same class)
- Each responsibility is a different reason to change (SRP)

### 3. **2-5 Cognitive Constraint**
- Humans can reason about 2-5 things at once
- Methods should delegate to 2-5 other classes (not more)
- If >5 responsibilities found, group into higher abstractions
- Must ask permission to exceed this constraint

### 4. **Anti-Stovepipe Rule**
- Minimum extraction: 2 classes (cannot extract just 1)
- Single-method classes must have ≥2 downstream dependencies
- Prevents useless wrapper classes

### 5. **Breadth-First Recursion**
- Process all classes at depth N before descending to depth N+1
- Track recursion depth, prompt user if depth > 5
- Ensures systematic decomposition level-by-level

### 6. **Convergence Criteria**
- **Primary Goal:** Cohesion = 1.0 + one-sentence test (both must pass)
- **Fallback Goal:** Cohesion ≥ 0.9 + complexity ≤ 3.5 + no more identifiable responsibilities + flag for human review

### 7. **Method Extraction Timing**
- Agent 2 (Method Extractor) runs LAST
- Only after all responsibility extraction is complete
- For readability improvement only, not to separate responsibilities

### 8. **Domain-Oriented Naming**
- Use domain nouns (Order, Inventory, Payment) not services (OrderValidator, InventoryManager)
- Objects act on their own data: `order.validate()` not `validator.validate(order)`
- Avoids noun-verber trap (Manager, Processor, Handler, Service, Controller)

### 9. **Field Handling for Method-Level Scope**
- Analyze if other methods use the same fields
- If no: MOVE field to extracted class
- If yes: COPY field to extracted class + warn about duplication

### 10. **Human-in-the-Loop**
- Prompt when >5 responsibilities need grouping
- Prompt when recursion depth > 5
- Prompt when fallback convergence reached
- Prompt to exceed 2-5 constraint
- Fuzzy match when method name not found

---

## Expected Outcomes

1. **User control over scope** - users decide class vs method level refactoring
2. **More classes with fewer methods** - each achieving true single responsibility
3. **Systematic decomposition** - level-by-level ensures complete coverage
4. **Cognitive manageability** - 2-5 delegation constraint maintained throughout
5. **Human oversight** - prompted when limits exceeded or decisions needed
6. **Better maintainability** - each class has exactly one reason to change
7. **Flexible workflow** - can refactor entire class or focus on specific methods
