# C# Class Naming Examples

## Naming Convention

C# uses `PascalCase` for class names, interfaces, and public members.

---

## Domain Noun Examples

### Good: Clear Domain Identity

```csharp
public class Account
{
    private readonly string _accountNumber;
    private decimal _balance;

    public Account(string accountNumber, decimal initialBalance)
    {
        _accountNumber = accountNumber;
        _balance = initialBalance;
    }

    public void Deposit(decimal amount)
    {
        _balance += amount;
    }

    public void Withdraw(decimal amount)
    {
        if (amount > _balance)
            throw new InsufficientFundsException(_accountNumber, amount, _balance);

        _balance -= amount;
    }
}
```

The name `Account` tells us what this object *is*—a financial account. It has state (account number, balance) and behavior that operates on that state.

### Good: Aggregate with Plural Noun

```csharp
public class Accounts
{
    private readonly Dictionary<string, Account> _accounts = new();

    public void Add(Account account)
    {
        _accounts[account.AccountNumber] = account;
    }

    public Account? Find(string accountNumber)
    {
        return _accounts.TryGetValue(accountNumber, out var account) ? account : null;
    }

    public decimal TotalBalance()
    {
        return _accounts.Values.Sum(a => a.Balance);
    }
}
```

`Accounts` aggregates `Account` objects. The plural noun clearly communicates this relationship.

---

## Interface and Implementation

```csharp
public interface IAccountRepository
{
    void Save(Account account);
    Account? FindByNumber(string accountNumber);
}

public class SqlServerAccountRepository : IAccountRepository
{
    private readonly IDbConnection _connection;

    public SqlServerAccountRepository(IDbConnection connection)
    {
        _connection = connection;
    }

    public void Save(Account account)
    {
        // Implementation details
    }

    public Account? FindByNumber(string accountNumber)
    {
        // Implementation details
    }
}
```

C# convention uses `I` prefix for interfaces. The interface (`IAccountRepository`) has the generic name. The implementation (`SqlServerAccountRepository`) specifies what kind it is.

---

## Problematic Patterns to Recognize

### Problem: Verb-Centric Name, No State

```csharp
// Problematic
public class PaymentProcessor
{
    public void ProcessPayment(decimal amount, Account account)
    {
        account.Withdraw(amount);
        // send to payment gateway...
    }
}
```

This "object" has no state—it's just a procedure holder. The name describes an action (`Process`), not an identity.

### Better: Find the Domain Noun

```csharp
// Better: What IS this in the domain?
public class Payment
{
    private readonly decimal _amount;
    private readonly Account _sourceAccount;
    private readonly IPaymentGateway _gateway;
    private PaymentStatus _status;

    public Payment(decimal amount, Account sourceAccount, IPaymentGateway gateway)
    {
        _amount = amount;
        _sourceAccount = sourceAccount;
        _gateway = gateway;
        _status = PaymentStatus.Pending;
    }

    public void Execute()
    {
        _sourceAccount.Withdraw(_amount);
        _gateway.Submit(this);
        _status = PaymentStatus.Completed;
    }
}
```

A `Payment` is a thing in the domain—a transaction with amount, source, and status. It has identity and state.

---

## Controller Exception

Controllers are acceptable as they are a universally understood pattern:

```csharp
[ApiController]
[Route("api/[controller]")]
public class AccountsController : ControllerBase
{
    private readonly IAccountRepository _repository;

    public AccountsController(IAccountRepository repository)
    {
        _repository = repository;
    }

    [HttpGet("{accountNumber}")]
    public ActionResult<Account> Get(string accountNumber)
    {
        var account = _repository.FindByNumber(accountNumber);
        return account is null ? NotFound() : Ok(account);
    }
}
```

The `Controller` suffix is acceptable because it's a universally understood pattern in web frameworks.

---

## Domain-Specific Abbreviations

Only use abbreviations that are part of the domain language:

```csharp
// Acceptable if "SKU" is ubiquitous in the domain
public class Sku
{
    // Stock Keeping Unit - a product identifier
}

// Acceptable if "VAT" is standard terminology
public class VatCalculation
{
    // Value Added Tax calculation for an order
}
```

Always confirm with the user before using abbreviations.
