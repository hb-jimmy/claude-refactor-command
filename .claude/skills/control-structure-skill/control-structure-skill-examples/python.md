# Python Examples - Control Structure Skill

## If/Else Block

### Before

```python
def process_order(self, order):
    if order.is_valid:
        discount = self._calculate_discount(order)
        order.apply_discount(discount)
        order.status = OrderStatus.PROCESSING
        self._order_repository.save(order)
        self._notification_service.send_confirmation(order)
    else:
        order.status = OrderStatus.INVALID
        self._order_repository.save(order)
        self._notification_service.send_rejection(order)
```

### After

```python
def process_order(self, order):
    if order.is_valid:
        self._process_valid_order(order)
    else:
        self._reject_invalid_order(order)

def _process_valid_order(self, order):
    discount = self._calculate_discount(order)
    order.apply_discount(discount)
    order.status = OrderStatus.PROCESSING
    self._order_repository.save(order)
    self._notification_service.send_confirmation(order)

def _reject_invalid_order(self, order):
    order.status = OrderStatus.INVALID
    self._order_repository.save(order)
    self._notification_service.send_rejection(order)
```

The original method obscured the high-level decision: valid orders get processed, invalid orders get rejected. The refactored version makes this intent immediately clear. The implementation details are abstracted into descriptively named private methods.

---

## For Loop

### Before

```python
def send_monthly_reports(self, customers):
    for i in range(len(customers)):
        customer = customers[i]
        report = self._generate_report(customer)
        email = self._format_email_body(report)
        self._email_service.send(customer.email, email)
        self._audit_log.record_report_sent(customer.id)
```

### After

```python
def send_monthly_reports(self, customers):
    for i in range(len(customers)):
        self._send_report_to_customer(customers[i])

def _send_report_to_customer(self, customer):
    report = self._generate_report(customer)
    email = self._format_email_body(report)
    self._email_service.send(customer.email, email)
    self._audit_log.record_report_sent(customer.id)
```

The loop's purpose is now clear: send a report to each customer. The details of what "sending a report" entails are encapsulated in a method whose name communicates this intent.

---

## For-In Loop

### Before

```python
def calculate_total_revenue(self, invoices):
    total = 0
    for invoice in invoices:
        if invoice.status == InvoiceStatus.PAID:
            amount = invoice.amount
            tax = amount * invoice.tax_rate
            total += amount + tax
    return total
```

### After

```python
def calculate_total_revenue(self, invoices):
    total = 0
    for invoice in invoices:
        total += self._calculate_paid_invoice_contribution(invoice)
    return total

def _calculate_paid_invoice_contribution(self, invoice):
    if invoice.status != InvoiceStatus.PAID:
        return 0
    return self._calculate_invoice_total_with_tax(invoice)

def _calculate_invoice_total_with_tax(self, invoice):
    amount = invoice.amount
    tax = amount * invoice.tax_rate
    return amount + tax
```

The nested control structure (if inside for) was processed from the inside out. The innermost calculation logic was extracted first, then the conditional check. The loop now clearly shows its purpose: accumulate contributions from each invoice.

---

## While Loop

### Before

```python
def process_message_queue(self):
    while self._message_queue.has_messages():
        message = self._message_queue.dequeue()
        parsed = self._parse_message(message)
        self._validate_message(parsed)
        self._route_to_handler(parsed)
        self._message_queue.acknowledge(message.id)
```

### After

```python
def process_message_queue(self):
    while self._message_queue.has_messages():
        self._process_next_message()

def _process_next_message(self):
    message = self._message_queue.dequeue()
    parsed = self._parse_message(message)
    self._validate_message(parsed)
    self._route_to_handler(parsed)
    self._message_queue.acknowledge(message.id)
```

The while loop now reads as a clear statement of intent: keep processing messages while there are messages to process. What "processing a message" means is detailed in the extracted method.

---

## If/Elif/Else Chain

### Before

```python
def handle_payment(self, payment):
    if payment.method == PaymentMethod.CREDIT_CARD:
        self._validate_credit_card(payment.card_details)
        auth_code = self._card_processor.authorize(payment)
        payment.authorization_code = auth_code
        self._card_processor.capture(payment)
    elif payment.method == PaymentMethod.BANK_TRANSFER:
        bank_account = self._bank_service.validate_account(payment.bank_details)
        self._bank_service.initiate_transfer(bank_account, payment.amount)
        payment.transfer_reference = self._bank_service.get_reference()
    elif payment.method == PaymentMethod.CRYPTOCURRENCY:
        wallet = self._crypto_service.validate_wallet(payment.wallet_address)
        self._crypto_service.initiate_transaction(wallet, payment.amount)
        payment.transaction_hash = self._crypto_service.await_confirmation()
```

### After

```python
def handle_payment(self, payment):
    if payment.method == PaymentMethod.CREDIT_CARD:
        self._process_credit_card_payment(payment)
    elif payment.method == PaymentMethod.BANK_TRANSFER:
        self._process_bank_transfer_payment(payment)
    elif payment.method == PaymentMethod.CRYPTOCURRENCY:
        self._process_cryptocurrency_payment(payment)

def _process_credit_card_payment(self, payment):
    self._validate_credit_card(payment.card_details)
    auth_code = self._card_processor.authorize(payment)
    payment.authorization_code = auth_code
    self._card_processor.capture(payment)

def _process_bank_transfer_payment(self, payment):
    bank_account = self._bank_service.validate_account(payment.bank_details)
    self._bank_service.initiate_transfer(bank_account, payment.amount)
    payment.transfer_reference = self._bank_service.get_reference()

def _process_cryptocurrency_payment(self, payment):
    wallet = self._crypto_service.validate_wallet(payment.wallet_address)
    self._crypto_service.initiate_transaction(wallet, payment.amount)
    payment.transaction_hash = self._crypto_service.await_confirmation()
```

The if/elif chain now serves as a clear routing mechanism. Each branch directs to a single method call that describes the type of processing. The implementation details for each payment method are isolated in their own methods.

---

## Try/Except/Finally

### Before

```python
def import_data_file(self, file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        parsed = json.loads(content)
        self._validate_data(parsed)
        self._repository.bulk_insert(parsed['records'])
        self._audit_log.record_import(file_path, len(parsed['records']))
    except json.JSONDecodeError as ex:
        self._logger.error(f"Failed to parse file: {ex}")
        self._notification_service.alert_admin("Import parse failure", str(ex))
        raise ImportException("Parse error") from ex
    finally:
        self._temp_file_manager.cleanup(file_path)
        self._lock_manager.release(file_path)
```

### After

```python
def import_data_file(self, file_path):
    try:
        self._import_and_store_data(file_path)
    except json.JSONDecodeError as ex:
        self._handle_parse_failure(file_path, ex)
    finally:
        self._release_import_resources(file_path)

def _import_and_store_data(self, file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    parsed = json.loads(content)
    self._validate_data(parsed)
    self._repository.bulk_insert(parsed['records'])
    self._audit_log.record_import(file_path, len(parsed['records']))

def _handle_parse_failure(self, file_path, ex):
    self._logger.error(f"Failed to parse file: {ex}")
    self._notification_service.alert_admin("Import parse failure", str(ex))
    raise ImportException("Parse error") from ex

def _release_import_resources(self, file_path):
    self._temp_file_manager.cleanup(file_path)
    self._lock_manager.release(file_path)
```

The try/except/finally structure now clearly communicates the error handling strategy: attempt to import data, handle parse failures specifically, and always release resources. Each block delegates to a single descriptively named method.

---

## Match Statement (Python 3.10+)

### Before

```python
def describe_shape(self, shape):
    match shape:
        case Circle(radius=r):
            area = math.pi * r * r
            circumference = 2 * math.pi * r
            return f"Circle with radius {r}, area = {area:.2f}, circumference = {circumference:.2f}"
        case Rectangle(width=w, height=h):
            area = w * h
            perimeter = 2 * (w + h)
            return f"Rectangle {w}x{h}, area = {area:.2f}, perimeter = {perimeter:.2f}"
        case Triangle(a=a, b=b, c=c):
            area = self._calculate_triangle_area(a, b, c)
            perimeter = a + b + c
            return f"Triangle with sides {a}, {b}, {c}, area = {area:.2f}, perimeter = {perimeter:.2f}"
        case _:
            return "Unknown shape"
```

### After

```python
def describe_shape(self, shape):
    match shape:
        case Circle(radius=r):
            return self._describe_circle(r)
        case Rectangle(width=w, height=h):
            return self._describe_rectangle(w, h)
        case Triangle(a=a, b=b, c=c):
            return self._describe_triangle(a, b, c)
        case _:
            return "Unknown shape"

def _describe_circle(self, radius):
    area = math.pi * radius * radius
    circumference = 2 * math.pi * radius
    return f"Circle with radius {radius}, area = {area:.2f}, circumference = {circumference:.2f}"

def _describe_rectangle(self, width, height):
    area = width * height
    perimeter = 2 * (width + height)
    return f"Rectangle {width}x{height}, area = {area:.2f}, perimeter = {perimeter:.2f}"

def _describe_triangle(self, a, b, c):
    area = self._calculate_triangle_area(a, b, c)
    perimeter = a + b + c
    return f"Triangle with sides {a}, {b}, {c}, area = {area:.2f}, perimeter = {perimeter:.2f}"
```

The match statement now acts as a clear dispatch mechanism. Each shape type routes to a method that knows how to describe that specific shape. The calculation logic is separated from the routing logic.

---

## Lambda Extraction

### Before

```python
def get_high_value_order_summaries(self, orders):
    return list(
        map(
            lambda o: OrderSummary(
                o.id,
                self._customer_service.get_name(o.customer_id),
                o.total,
                sum(i.quantity for i in o.items),
                any(o.discounts)
            ),
            filter(
                lambda o: o.total > 1000 and o.status == OrderStatus.COMPLETED,
                orders
            )
        )
    )
```

### After

```python
def get_high_value_order_summaries(self, orders):
    return list(
        map(
            self._create_order_summary,
            filter(self._is_high_value_completed_order, orders)
        )
    )

def _is_high_value_completed_order(self, order):
    return order.total > 1000 and order.status == OrderStatus.COMPLETED

def _create_order_summary(self, order):
    customer_name = self._customer_service.get_name(order.customer_id)
    item_count = sum(i.quantity for i in order.items)
    discount_applied = any(order.discounts)
    return OrderSummary(order.id, customer_name, order.total, item_count, discount_applied)
```

The functional pipeline now reads clearly: filter to high-value completed orders, then create summaries. The multi-line lambdas are replaced with method references, making the intent obvious at a glance.

---

## List Comprehension with Conditional

### Before

```python
def get_active_user_emails(self, users):
    return [
        user.email.lower().strip()
        for user in users
        if user.is_active and user.email_verified and not user.is_suspended
    ]
```

### After

```python
def get_active_user_emails(self, users):
    return [self._normalize_email(user) for user in users if self._is_eligible_user(user)]

def _is_eligible_user(self, user):
    return user.is_active and user.email_verified and not user.is_suspended

def _normalize_email(self, user):
    return user.email.lower().strip()
```

The list comprehension now clearly states its purpose: get normalized emails for eligible users. The criteria for eligibility and the normalization logic are extracted into descriptively named methods.

---

## Nested Control Structures

### Before

```python
def process_inventory_report(self, warehouses):
    for warehouse in warehouses:
        if warehouse.is_active:
            for item in warehouse.items:
                if item.quantity < item.reorder_threshold:
                    supplier = self._supplier_service.get_preferred(item.product_id)
                    order_qty = item.reorder_quantity
                    self._purchase_order_service.create(supplier, item.product_id, order_qty)
                    self._notification_service.alert_inventory_manager(warehouse.id, item.product_id)
```

### After

```python
def process_inventory_report(self, warehouses):
    for warehouse in warehouses:
        self._process_warehouse_inventory(warehouse)

def _process_warehouse_inventory(self, warehouse):
    if warehouse.is_active:
        self._check_and_reorder_low_stock_items(warehouse)

def _check_and_reorder_low_stock_items(self, warehouse):
    for item in warehouse.items:
        self._reorder_if_below_threshold(warehouse.id, item)

def _reorder_if_below_threshold(self, warehouse_id, item):
    if item.quantity < item.reorder_threshold:
        self._create_reorder_request(warehouse_id, item)

def _create_reorder_request(self, warehouse_id, item):
    supplier = self._supplier_service.get_preferred(item.product_id)
    order_qty = item.reorder_quantity
    self._purchase_order_service.create(supplier, item.product_id, order_qty)
    self._notification_service.alert_inventory_manager(warehouse_id, item.product_id)
```

The deeply nested structure was unwound from the inside out. Starting with the innermost reorder logic, each layer was extracted. The top-level method now clearly states: process inventory for each warehouse. Each subsequent method adds one layer of detail while maintaining the single-line body rule.

---

## Generator with Conditional Logic

### Before

```python
def stream_valid_records(self, file_path):
    with open(file_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            if self._validate_record(record):
                record['processed_at'] = datetime.now()
                record['source'] = file_path
                yield self._transform_record(record)
```

### After

```python
def stream_valid_records(self, file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield from self._process_line_if_valid(line, file_path)

def _process_line_if_valid(self, line, file_path):
    record = json.loads(line)
    if self._validate_record(record):
        yield self._prepare_and_transform_record(record, file_path)

def _prepare_and_transform_record(self, record, file_path):
    record['processed_at'] = datetime.now()
    record['source'] = file_path
    return self._transform_record(record)
```

The generator's nested logic was extracted from the inside out. The for loop now has a single yield statement. The validation and transformation logic are encapsulated in methods that clearly describe their purpose.
