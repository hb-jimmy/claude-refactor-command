# C# Examples - Control Structure Skill

## If/Else Block

### Before

```csharp
public void ProcessOrder(Order order)
{
    if (order.IsValid)
    {
        var discount = CalculateDiscount(order);
        order.ApplyDiscount(discount);
        order.Status = OrderStatus.Processing;
        _orderRepository.Save(order);
        _notificationService.SendConfirmation(order);
    }
    else
    {
        order.Status = OrderStatus.Invalid;
        _orderRepository.Save(order);
        _notificationService.SendRejection(order);
    }
}
```

### After

```csharp
public void ProcessOrder(Order order)
{
    if (order.IsValid)
        ProcessValidOrder(order);
    else
        RejectInvalidOrder(order);
}

private void ProcessValidOrder(Order order)
{
    var discount = CalculateDiscount(order);
    order.ApplyDiscount(discount);
    order.Status = OrderStatus.Processing;
    _orderRepository.Save(order);
    _notificationService.SendConfirmation(order);
}

private void RejectInvalidOrder(Order order)
{
    order.Status = OrderStatus.Invalid;
    _orderRepository.Save(order);
    _notificationService.SendRejection(order);
}
```

The original method obscured the high-level decision: valid orders get processed, invalid orders get rejected. The refactored version makes this intent immediately clear. The implementation details are abstracted into descriptively named private methods.

---

## For Loop

### Before

```csharp
public void SendMonthlyReports(List<Customer> customers)
{
    for (int i = 0; i < customers.Count; i++)
    {
        var customer = customers[i];
        var report = GenerateReport(customer);
        var email = FormatEmailBody(report);
        _emailService.Send(customer.Email, email);
        _auditLog.RecordReportSent(customer.Id);
    }
}
```

### After

```csharp
public void SendMonthlyReports(List<Customer> customers)
{
    for (int i = 0; i < customers.Count; i++)
        SendReportToCustomer(customers[i]);
}

private void SendReportToCustomer(Customer customer)
{
    var report = GenerateReport(customer);
    var email = FormatEmailBody(report);
    _emailService.Send(customer.Email, email);
    _auditLog.RecordReportSent(customer.Id);
}
```

The loop's purpose is now clear: send a report to each customer. The details of what "sending a report" entails are encapsulated in a method whose name communicates this intent.

---

## Foreach Loop

### Before

```csharp
public decimal CalculateTotalRevenue(IEnumerable<Invoice> invoices)
{
    decimal total = 0;
    foreach (var invoice in invoices)
    {
        if (invoice.Status == InvoiceStatus.Paid)
        {
            var amount = invoice.Amount;
            var tax = amount * invoice.TaxRate;
            total += amount + tax;
        }
    }
    return total;
}
```

### After

```csharp
public decimal CalculateTotalRevenue(IEnumerable<Invoice> invoices)
{
    decimal total = 0;
    foreach (var invoice in invoices)
        total += CalculatePaidInvoiceContribution(invoice);
    return total;
}

private decimal CalculatePaidInvoiceContribution(Invoice invoice)
{
    if (invoice.Status != InvoiceStatus.Paid)
        return 0;

    return CalculateInvoiceTotalWithTax(invoice);
}

private decimal CalculateInvoiceTotalWithTax(Invoice invoice)
{
    var amount = invoice.Amount;
    var tax = amount * invoice.TaxRate;
    return amount + tax;
}
```

The nested control structure (if inside foreach) was processed from the inside out. The innermost calculation logic was extracted first, then the conditional check. The loop now clearly shows its purpose: accumulate contributions from each invoice.

---

## While Loop

### Before

```csharp
public void ProcessMessageQueue()
{
    while (_messageQueue.HasMessages())
    {
        var message = _messageQueue.Dequeue();
        var parsed = ParseMessage(message);
        ValidateMessage(parsed);
        RouteToHandler(parsed);
        _messageQueue.Acknowledge(message.Id);
    }
}
```

### After

```csharp
public void ProcessMessageQueue()
{
    while (_messageQueue.HasMessages())
        ProcessNextMessage();
}

private void ProcessNextMessage()
{
    var message = _messageQueue.Dequeue();
    var parsed = ParseMessage(message);
    ValidateMessage(parsed);
    RouteToHandler(parsed);
    _messageQueue.Acknowledge(message.Id);
}
```

The while loop now reads as a clear statement of intent: keep processing messages while there are messages to process. What "processing a message" means is detailed in the extracted method.

---

## Switch Statement

### Before

```csharp
public void HandlePayment(Payment payment)
{
    switch (payment.Method)
    {
        case PaymentMethod.CreditCard:
            ValidateCreditCard(payment.CardDetails);
            var authCode = _cardProcessor.Authorize(payment);
            payment.AuthorizationCode = authCode;
            _cardProcessor.Capture(payment);
            break;
        case PaymentMethod.BankTransfer:
            var bankAccount = _bankService.ValidateAccount(payment.BankDetails);
            _bankService.InitiateTransfer(bankAccount, payment.Amount);
            payment.TransferReference = _bankService.GetReference();
            break;
        case PaymentMethod.Cryptocurrency:
            var wallet = _cryptoService.ValidateWallet(payment.WalletAddress);
            _cryptoService.InitiateTransaction(wallet, payment.Amount);
            payment.TransactionHash = _cryptoService.AwaitConfirmation();
            break;
    }
}
```

### After

```csharp
public void HandlePayment(Payment payment)
{
    switch (payment.Method)
    {
        case PaymentMethod.CreditCard:
            ProcessCreditCardPayment(payment);
            break;
        case PaymentMethod.BankTransfer:
            ProcessBankTransferPayment(payment);
            break;
        case PaymentMethod.Cryptocurrency:
            ProcessCryptocurrencyPayment(payment);
            break;
    }
}

private void ProcessCreditCardPayment(Payment payment)
{
    ValidateCreditCard(payment.CardDetails);
    var authCode = _cardProcessor.Authorize(payment);
    payment.AuthorizationCode = authCode;
    _cardProcessor.Capture(payment);
}

private void ProcessBankTransferPayment(Payment payment)
{
    var bankAccount = _bankService.ValidateAccount(payment.BankDetails);
    _bankService.InitiateTransfer(bankAccount, payment.Amount);
    payment.TransferReference = _bankService.GetReference();
}

private void ProcessCryptocurrencyPayment(Payment payment)
{
    var wallet = _cryptoService.ValidateWallet(payment.WalletAddress);
    _cryptoService.InitiateTransaction(wallet, payment.Amount);
    payment.TransactionHash = _cryptoService.AwaitConfirmation();
}
```

The switch statement now serves as a clear routing mechanism. Each case directs to a single method call that describes the type of processing. The implementation details for each payment method are isolated in their own methods.

---

## Try/Catch/Finally

### Before

```csharp
public void ImportDataFile(string filePath)
{
    try
    {
        var content = File.ReadAllText(filePath);
        var parsed = JsonSerializer.Deserialize<DataFile>(content);
        ValidateData(parsed);
        _repository.BulkInsert(parsed.Records);
        _auditLog.RecordImport(filePath, parsed.Records.Count);
    }
    catch (JsonException ex)
    {
        _logger.LogError(ex, "Failed to parse file");
        _notificationService.AlertAdmin("Import parse failure", ex.Message);
        throw new ImportException("Parse error", ex);
    }
    finally
    {
        _tempFileManager.Cleanup(filePath);
        _lockManager.Release(filePath);
    }
}
```

### After

```csharp
public void ImportDataFile(string filePath)
{
    try
        ImportAndStoreData(filePath);
    catch (JsonException ex)
        HandleParseFailure(filePath, ex);
    finally
        ReleaseImportResources(filePath);
}

private void ImportAndStoreData(string filePath)
{
    var content = File.ReadAllText(filePath);
    var parsed = JsonSerializer.Deserialize<DataFile>(content);
    ValidateData(parsed);
    _repository.BulkInsert(parsed.Records);
    _auditLog.RecordImport(filePath, parsed.Records.Count);
}

private void HandleParseFailure(string filePath, JsonException ex)
{
    _logger.LogError(ex, "Failed to parse file");
    _notificationService.AlertAdmin("Import parse failure", ex.Message);
    throw new ImportException("Parse error", ex);
}

private void ReleaseImportResources(string filePath)
{
    _tempFileManager.Cleanup(filePath);
    _lockManager.Release(filePath);
}
```

The try/catch/finally structure now clearly communicates the error handling strategy: attempt to import data, handle parse failures specifically, and always release resources. Each block delegates to a single descriptively named method.

---

## Pattern Matching

### Before

```csharp
public string DescribeShape(Shape shape)
{
    return shape switch
    {
        Circle c => $"Circle with radius {c.Radius}, area = {Math.PI * c.Radius * c.Radius:F2}, circumference = {2 * Math.PI * c.Radius:F2}",
        Rectangle r => $"Rectangle {r.Width}x{r.Height}, area = {r.Width * r.Height:F2}, perimeter = {2 * (r.Width + r.Height):F2}",
        Triangle t => $"Triangle with sides {t.A}, {t.B}, {t.C}, area = {CalculateTriangleArea(t):F2}, perimeter = {t.A + t.B + t.C:F2}",
        _ => "Unknown shape"
    };
}
```

### After

```csharp
public string DescribeShape(Shape shape)
{
    return shape switch
    {
        Circle c => DescribeCircle(c),
        Rectangle r => DescribeRectangle(r),
        Triangle t => DescribeTriangle(t),
        _ => "Unknown shape"
    };
}

private string DescribeCircle(Circle c)
{
    var area = Math.PI * c.Radius * c.Radius;
    var circumference = 2 * Math.PI * c.Radius;
    return $"Circle with radius {c.Radius}, area = {area:F2}, circumference = {circumference:F2}";
}

private string DescribeRectangle(Rectangle r)
{
    var area = r.Width * r.Height;
    var perimeter = 2 * (r.Width + r.Height);
    return $"Rectangle {r.Width}x{r.Height}, area = {area:F2}, perimeter = {perimeter:F2}";
}

private string DescribeTriangle(Triangle t)
{
    var area = CalculateTriangleArea(t);
    var perimeter = t.A + t.B + t.C;
    return $"Triangle with sides {t.A}, {t.B}, {t.C}, area = {area:F2}, perimeter = {perimeter:F2}";
}
```

The pattern match now acts as a clear dispatch mechanism. Each shape type routes to a method that knows how to describe that specific shape. The calculation logic is separated from the routing logic.

---

## Lambda Extraction

### Before

```csharp
public List<OrderSummary> GetHighValueOrderSummaries(List<Order> orders)
{
    return orders
        .Where(o => o.Total > 1000 && o.Status == OrderStatus.Completed)
        .Select(o => {
            var customerName = _customerService.GetName(o.CustomerId);
            var itemCount = o.Items.Sum(i => i.Quantity);
            var discountApplied = o.Discounts.Any();
            return new OrderSummary(o.Id, customerName, o.Total, itemCount, discountApplied);
        })
        .ToList();
}
```

### After

```csharp
public List<OrderSummary> GetHighValueOrderSummaries(List<Order> orders)
{
    return orders
        .Where(IsHighValueCompletedOrder)
        .Select(CreateOrderSummary)
        .ToList();
}

private bool IsHighValueCompletedOrder(Order o)
{
    return o.Total > 1000 && o.Status == OrderStatus.Completed;
}

private OrderSummary CreateOrderSummary(Order o)
{
    var customerName = _customerService.GetName(o.CustomerId);
    var itemCount = o.Items.Sum(i => i.Quantity);
    var discountApplied = o.Discounts.Any();
    return new OrderSummary(o.Id, customerName, o.Total, itemCount, discountApplied);
}
```

The LINQ query now reads as a clear pipeline: filter to high-value completed orders, then create summaries. The multi-line lambda is replaced with a method reference, and the filtering predicate is also extracted for clarity.

---

## Nested Control Structures

### Before

```csharp
public void ProcessInventoryReport(List<Warehouse> warehouses)
{
    foreach (var warehouse in warehouses)
    {
        if (warehouse.IsActive)
        {
            foreach (var item in warehouse.Items)
            {
                if (item.Quantity < item.ReorderThreshold)
                {
                    var supplier = _supplierService.GetPreferred(item.ProductId);
                    var orderQty = item.ReorderQuantity;
                    _purchaseOrderService.Create(supplier, item.ProductId, orderQty);
                    _notificationService.AlertInventoryManager(warehouse.Id, item.ProductId);
                }
            }
        }
    }
}
```

### After

```csharp
public void ProcessInventoryReport(List<Warehouse> warehouses)
{
    foreach (var warehouse in warehouses)
        ProcessWarehouseInventory(warehouse);
}

private void ProcessWarehouseInventory(Warehouse warehouse)
{
    if (warehouse.IsActive)
        CheckAndReorderLowStockItems(warehouse);
}

private void CheckAndReorderLowStockItems(Warehouse warehouse)
{
    foreach (var item in warehouse.Items)
        ReorderIfBelowThreshold(warehouse.Id, item);
}

private void ReorderIfBelowThreshold(int warehouseId, InventoryItem item)
{
    if (item.Quantity < item.ReorderThreshold)
        CreateReorderRequest(warehouseId, item);
}

private void CreateReorderRequest(int warehouseId, InventoryItem item)
{
    var supplier = _supplierService.GetPreferred(item.ProductId);
    var orderQty = item.ReorderQuantity;
    _purchaseOrderService.Create(supplier, item.ProductId, orderQty);
    _notificationService.AlertInventoryManager(warehouseId, item.ProductId);
}
```

The deeply nested structure was unwound from the inside out. Starting with the innermost reorder logic, each layer was extracted. The top-level method now clearly states: process inventory for each warehouse. Each subsequent method adds one layer of detail while maintaining the single-line body rule.
