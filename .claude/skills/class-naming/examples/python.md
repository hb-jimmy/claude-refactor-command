# Python Class Naming Examples

## Naming Convention

Python uses `PascalCase` for class names.

---

## Domain Noun Examples

### Good: Clear Domain Identity

```python
class Account:
    """Represents a financial account in the system."""
    def __init__(self, account_number: str, balance: Decimal):
        self._account_number = account_number
        self._balance = balance

    def deposit(self, amount: Decimal) -> None:
        self._balance += amount

    def withdraw(self, amount: Decimal) -> None:
        if amount > self._balance:
            raise InsufficientFunds(self._account_number, amount, self._balance)
        self._balance -= amount
```

The name `Account` tells us what this object *is*—a financial account. It has state (account number, balance) and behavior that operates on that state.

### Good: Aggregate with Plural Noun

```python
class Accounts:
    """Aggregates Account objects for a customer."""
    def __init__(self):
        self._accounts: dict[str, Account] = {}

    def add(self, account: Account) -> None:
        self._accounts[account.account_number] = account

    def find(self, account_number: str) -> Account | None:
        return self._accounts.get(account_number)

    def total_balance(self) -> Decimal:
        return sum(account.balance for account in self._accounts.values())
```

`Accounts` aggregates `Account` objects. The plural noun clearly communicates this relationship.

---

## Interface and Implementation

```python
from abc import ABC, abstractmethod

class AccountRepository(ABC):
    """Generic interface for account persistence."""

    @abstractmethod
    def save(self, account: Account) -> None:
        pass

    @abstractmethod
    def find_by_number(self, account_number: str) -> Account | None:
        pass


class PostgresAccountRepository(AccountRepository):
    """PostgreSQL implementation of account persistence."""

    def __init__(self, connection: Connection):
        self._connection = connection

    def save(self, account: Account) -> None:
        # Implementation details
        pass

    def find_by_number(self, account_number: str) -> Account | None:
        # Implementation details
        pass
```

The interface (`AccountRepository`) has the generic name. The implementation (`PostgresAccountRepository`) specifies what kind it is.

---

## Problematic Patterns to Recognize

### Problem: Verb-Centric Name, No State

```python
# Problematic
class PaymentProcessor:
    def process_payment(self, amount: Decimal, account: Account) -> None:
        account.withdraw(amount)
        # send to payment gateway...
```

This "object" has no state—it's just a procedure holder. The name describes an action (`process`), not an identity.

### Better: Find the Domain Noun

```python
# Better: What IS this in the domain?
class Payment:
    """Represents a payment transaction."""
    def __init__(self, amount: Decimal, source_account: Account, gateway: PaymentGateway):
        self._amount = amount
        self._source_account = source_account
        self._gateway = gateway
        self._status = PaymentStatus.PENDING

    def execute(self) -> None:
        self._source_account.withdraw(self._amount)
        self._gateway.submit(self)
        self._status = PaymentStatus.COMPLETED
```

A `Payment` is a thing in the domain—a transaction with amount, source, and status. It has identity and state.

---

## Domain-Specific Abbreviations

Only use abbreviations that are part of the domain language:

```python
# Acceptable if "SKU" is ubiquitous in the domain
class SKU:
    """Stock Keeping Unit - a product identifier."""
    pass

# Acceptable if "VAT" is standard terminology
class VATCalculation:
    """Value Added Tax calculation for an order."""
    pass
```

Always confirm with the user before using abbreviations.
