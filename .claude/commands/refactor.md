 /refactor Command

Extract distinct responsibilities from a class or method into separate classes following object-oriented principles.

## Arguments

- `$ARGUMENTS` - Command arguments (file path and options)

## Parsing Arguments

Parse the following from `$ARGUMENTS`:
- `file` - The file path to refactor
- `--scope=class|method` - Refactoring scope (default: prompt user)
- `--method=<name>` - Method name (required if scope=method)
- `--resume=<file>` - Resume from saved state file
- `--help` - Display help text

---

## Help Text

If `--help` is provided, display this and stop:

```
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

---

## No-Parameter Invocation

If no arguments are provided, display:

```
Available options:
  --scope=class|method    Specify refactoring scope
  --method=<name>         Method to refactor (required if scope=method)
  --resume=<file>         Resume from a saved refactoring state file

Let's proceed interactively.
```

Then ask: "What file would you like to refactor?"

---

## Resume Mode

If `--resume=<file>` is provided:

1. Read the resume state file
2. Validate all file hashes match current state
3. If any file changed, ABORT with error:
   ```
   ❌ Error: Cannot resume refactoring.

      Reason: File '<filename>' has been modified since refactoring started.

      The resume state is invalid. Please start a new refactoring session.
   ```
4. If valid, continue from the saved state:
   - Display the current progress tree
   - Resume analysis of pending classes
   - If there was a pending proposal, re-present it for approval

---

## Main Refactoring Flow

### Step 1: Validate Target File

1. Read the target file
2. Detect the programming language (Python or C#)
3. Parse the file to identify classes

**If file has syntax errors:**
```
❌ Error: Cannot proceed with refactoring.

   Reason: File has syntax errors and cannot be parsed.

   Please fix syntax errors before refactoring.
```

**If multiple classes exist and none specified:**
```
Multiple classes found in this file:
  1. Order
  2. OrderItem
  3. OrderStatus

Which class would you like to refactor?
```

### Step 2: Pre-Refactoring Validation (Fail Fast)

Check the target class for blocking issues. REFUSE refactoring if ANY of these exist:

**Public fields:**
```
❌ Error: Cannot proceed with refactoring.

   Reason: Class '<ClassName>' has public field '<fieldName>'.

   Public fields prevent proper refactoring.
   The design must be changed before refactoring can succeed.
```

**Public properties (C#) or @property decorators (Python):**
```
❌ Error: Cannot proceed with refactoring.

   Reason: Class '<ClassName>' has public property '<propertyName>'.

   Public properties expose internal state and prevent proper refactoring.
   Consider removing properties and using methods instead.
```

**Protected fields/properties:**
```
❌ Error: Cannot proceed with refactoring.

   Reason: Class '<ClassName>' has protected field '<fieldName>'.

   Protected fields prevent proper encapsulation during refactoring.
```

**Data-only classes (@dataclass, record, no behavior):**
```
❌ Error: Cannot proceed with refactoring.

   Reason: Class '<ClassName>' is a data-only class with no behavior methods.

   Data classes have nothing to refactor without changing functionality.
   Refactoring is a functionality-neutral change.
```

**Warn but proceed for Python fields missing `_` prefix:**
```
⚠️  Warning: Field '<fieldName>' is missing the private prefix convention.
    Consider renaming to '_<fieldName>' for proper encapsulation.
    Proceeding with refactoring.
```

### Step 3: Locate and Run Tests

1. Search for test files:
   - Python: `test_<filename>.py`, `<filename>_test.py`, `tests/test_<filename>.py`
   - C#: `<ClassName>Tests.cs`, `<ClassName>Test.cs`, `Tests/<ClassName>Tests.cs`

2. If no tests found, ask user:
   ```
   No tests found for '<ClassName>'.

   Please provide the test file path, or type 'skip' to proceed without tests.

   ⚠️  Warning: Refactoring without tests is risky. There's no way to verify
       the refactoring hasn't changed functionality.
   ```

3. Run the tests:
   - Python: `pytest <test_file>`
   - C#: `dotnet test --filter <ClassName>`

4. **If tests fail, ABORT:**
   ```
   ❌ Error: Cannot proceed with refactoring.

      Reason: Tests are failing before refactoring.

      All tests must pass before refactoring can begin.
      Fix the failing tests first, then run /refactor again.
   ```

### Step 4: Determine Scope

If `--scope` not provided, ask:
```
What scope would you like to refactor?
  1. class - Refactor entire class
  2. method - Refactor a specific method
```

If `--scope=method` but `--method` not provided:
1. List all methods in the class
2. Ask user to select:
   ```
   Which method would you like to refactor?
   Available methods:
     - process
     - validate
     - calculate_total
   ```

If method name not found, use fuzzy matching:
```
❌ Error: Method 'processOrdre' does not exist in <ClassName>

   Did you mean 'process'?

   Available methods:
     - process
     - validate
     - calculate_total
```

### Step 5: Initialize State

Create the initial refactoring state structure:

```markdown
# Refactoring State: <ClassName>

## Target
- **File:** <file_path>
- **Class:** <ClassName>
- **Scope:** <class|method>
- **Method:** <method_name> (if scope=method)
- **Started:** <timestamp>

## Refactoring History

### Depth 0 (In Progress)
| Original Class | Extracted Class | File Created | Status |
|----------------|-----------------|--------------|--------|

## Current State
- **Current Depth:** 0
- **Classes Pending Analysis:** <ClassName>

## Pending Checklist
- [ ] Analyze <ClassName> for responsibilities

## Files Modified
| File | Action | Original Hash |
|------|--------|---------------|
| <file_path> | Target | <hash> |
```

### Step 6: Display Progress Tree

Display the hierarchical progress view:

```
Refactoring: <ClassName> (<file_path>)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key:
  ✅ Complete
  🔴 Needs Intervention
  🟡 Pending
  🔄 Currently Extracting
  🔵 Proposed, Awaiting Approval

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<ClassName>
└── 🔄 Analyzing...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Responsibility Analysis

### Analyze for Responsibilities

For each class pending analysis:

1. **Read the class code carefully**

2. **Identify distinct responsibilities using:**
   - **Variable cohesion (primary):** Which fields/variables are used together? Each cluster likely represents a distinct responsibility.
   - **Code section patterns:** Blank lines between sections, section comments
   - **Reason to change:** Each responsibility should have a different reason to change

3. **Apply the 2-5 constraint:**
   - Must identify 2-5 distinct responsibilities
   - If >5 found, group into higher-level abstractions
   - If only 1 found, the class cannot be refactored further

4. **Apply the Anti-Stovepipe rule:**
   - Minimum extraction: 2 classes
   - Single-method classes must have ≥2 downstream dependencies
   - Cannot extract just 1 class

### When No Responsibilities Found

If only 1 responsibility is identified (or none to extract):

```
Analyzing: <ClassName> (<file_path>)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  Analysis complete: No further responsibilities to extract.

Reasoning:
  <Explain why no distinct responsibilities were found>
  <Provide useful context about the class structure>

The class appears to have a single, cohesive responsibility.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do you agree with this analysis, or would you like to suggest further extractions?
```

### When >5 Responsibilities Found

```
⚠️  Warning: Identified 8 distinct responsibilities.

This exceeds the recommended 2-5 cognitive limit. I suggest grouping
them into higher-level abstractions:

Current responsibilities:
  1. validate
  2. checkInventory
  3. reserveInventory
  4. chargePayment
  5. handleRefunds
  6. createShipment
  7. notifyCustomer
  8. logTransaction

Suggested grouping:
  1. Preparation (validate + inventory operations)
  2. Payment (charge + refund handling)
  3. Fulfillment (shipment + notification + logging)

Would you like to proceed with the suggested grouping, or provide your own?
```

If unable to find good groupings, ask the user for help.

---

## Proposal Display

### Present Extraction Proposal

```
Analyzing: <ClassName> (<file_path>)
Scope: <class|method>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Identified <N> distinct responsibilities to extract:

┌─────────────────────────────────────────────────────────────────┐
│ 1. <ExtractedClassName>                                         │
├─────────────────────────────────────────────────────────────────┤
│ Responsibility: <Description of what this class does>          │
│                                                                 │
│ Fields to move:                                                 │
│   - <field1>: <Type>                                           │
│   - <field2>: <Type>                                           │
│                                                                 │
│ Code sections to move:                                          │
│   - Lines <start>-<end>: <Description>                         │
│   - Lines <start>-<end>: <Description>                         │
└─────────────────────────────────────────────────────────────────┘

[Repeat for each extracted class]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[If shared fields exist:]
⚠️  Field '<fieldName>' is used by multiple responsibilities.
    It will be copied to: <ClassName1>, <ClassName2>
    It will remain in: <OriginalClass>
    This may indicate additional responsibilities to extract.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proceed with extraction? (approve/modify/abort)
```

### Naming Rules

**Use domain nouns, NOT services/managers/processors:**
- Correct: `Inventory`, `Payment`, `Fulfillment`
- Wrong: `InventoryManager`, `PaymentProcessor`, `FulfillmentService`

**If user requests a noun-verber name, accept but warn:**
```
⚠️  Warning: '<RequestedName>' follows the noun-verber pattern.
    Consider using '<SuggestedName>' instead to better represent the domain object.
    Proceeding with your requested name.
```

### User Response Handling

**On "approve":**
- Proceed to parallel extraction

**On "modify" or suggestions for different distribution:**
- Re-evaluate and present a complete new proposal

**On alternate name suggestions:**
- Update the proposal display with new names (no full re-evaluation)

**On "justify" or asking for reasoning:**
- Explain the reasoning for the proposal
- User may provide new constraints, triggering a full re-evaluation

**On "abort":**
- Stop refactoring
- Offer to save the current state:
  ```
  Would you like to save the refactoring state for later?
  This will create 'refactoring_state.md' in the project root.
  ```

---

## Parallel Extraction

### Spawn Extraction Agents

For each approved extraction, spawn an extraction agent using the **extract-class** file in the agents folde as an agent with these parameters:

**Agent input (provide in prompt):**
```
Source file: <file_path>
Source class: <ClassName>
New class name: <ExtractedClassName>
New file path: <new_file_path>
Responsibility: <Description>
Fields to move:
  - <field1>: <Type>
  - <field2>: <Type>
Code sections to move:
  - Lines <start>-<end>
Language: <Python|C#>
```

**Spawn all extraction agents in parallel** using a single message with multiple Task tool calls.

### After Agents Complete

1. **Check all agents succeeded**
   - If any failed, stop and report the error
   - Offer rollback option

2. **Update the original class atomically:**
   - Add imports for extracted classes
   - Modify constructor to accept/create extracted classes
   - Update method bodies to delegate to extracted classes
   - Remove moved fields
   - Remove moved code sections

3. **Update the state file**

4. **Run tests**
   - If tests fail, prompt user for guidance
   - Be ready to rollback

5. **Add extracted classes to pending analysis queue**

---

## Breadth-First Recursion

### Process All Classes at Current Depth

After completing extractions at one depth level:

1. Update progress tree with completed extractions
2. All newly extracted classes become "pending analysis"
3. Analyze each pending class for further responsibilities
4. Present proposals and get approvals
5. Extract approved classes (spawn agents in parallel)
6. Run tests after all extractions at this depth complete
7. Repeat until no more extractions possible

### Convergence

For each class, convergence happens when:
1. Analysis finds no more distinct responsibilities
2. User confirms the analysis (prompted each time)
3. User may suggest further extractions

---

## Updating Constructor Usages

### When Constructor Signature Changes

1. Ask user for search scope:
   ```
   The constructor for '<ClassName>' has changed to accept new dependencies.

   Where should I search for usages to update?
     1. Current directory only
     2. Entire project
     3. Specific path: ___
   ```

2. Find all usages of the class constructor

3. Display what needs updating:
   ```
   Found <N> usages of '<ClassName>' constructor.

   These need to be updated to provide the new dependencies:
     - <dependency1>: <Type>
     - <dependency2>: <Type>

   Would you like me to update them? I'll show you batches of 10 at a time.
   ```

4. For each batch of 10, show:
   ```
   Batch <M> of <Total>:

   ┌─────────────────────────────────────────────────────────────────┐
   │ <file_path>:<line_number>                                       │
   ├─────────────────────────────────────────────────────────────────┤
   │ Before:                                                         │
   │   order = Order(items)                                          │
   │                                                                 │
   │ After:                                                          │
   │   order = Order(items, Inventory(), PaymentChannel())           │
   └─────────────────────────────────────────────────────────────────┘

   [Repeat for each usage in batch]

   Apply these changes? (yes/no/skip)
   ```

---

## Circular Reference Handling

If the extraction agent reports a circular reference:

```
🔴 Circular dependency detected: <ClassA> → <ClassB> → <ClassC> → <ClassA>

Proposed resolution:
  1. Create interface/Protocol '<InterfaceName>'
  2. Have '<ClassA>' implement the interface
  3. Change '<ClassC>' to depend on the interface
  4. Use method injection (not constructor) to provide the reference

This introduces temporal coupling but breaks the circular dependency.

Proceed with this resolution? (yes/no/help)
```

**Language-specific approach:**
- **C#:** Create an interface
- **Python:** Create a Protocol (from `typing` module)

If resolution not possible, ask user for help or offer rollback.

---

## Error Handling During Extraction

### On Agent Failure

```
❌ Error: Extraction failed for '<ExtractedClassName>'

   Reason: <Error message from agent>

   <Explanation of what went wrong>

Options:
  1. Provide guidance to retry
  2. Rollback this extraction level
  3. Abort refactoring
```

### Rollback

If user chooses rollback:
1. Delete all newly created files from current depth
2. Restore original class to previous state
3. Update state file to reflect rollback
4. Continue from previous valid state

---

## Functionality Change Requests

If user asks for functionality changes during refactoring:

```
❌ Cannot add functionality changes during refactoring.

   A refactoring is a functionality-neutral change. The code must do
   exactly the same thing before and after.

   Would you like to:
     1. Proceed with just the refactoring
     2. Abort and make functionality changes first
```

---

## Completion

### When All Extractions Complete

1. Display final progress tree (all items ✅)
2. Offer to run full test suite
3. Provide summary:
   ```
   Refactoring Complete: <OriginalClass>

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   <FinalProgressTree>

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Summary:
     - Original class: <OriginalClass>
     - Classes extracted: <N>
     - New files created: <list>
     - Depths processed: <N>

   All public method signatures preserved for backward compatibility.

   Would you like to run the full test suite?
   ```

4. Clean up state file (or offer to keep for reference)
