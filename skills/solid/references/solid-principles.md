# SOLID Principles

## Overview

Examples use Kotlin. Snippets are independent teaching examples; partial app types are identified. Amounts, validation, and notification behavior illustrate design rather than define product rules. Check real currency/rounding/range contracts before adapting money examples.

SOLID helps structure software to be flexible, maintainable, and testable. These principles reduce coupling and increase cohesion.

## S - Single Responsibility Principle (SRP)

> "A class should have one, and only one, reason to change."

### Problem It Solves
God objects that do everything - hard to test, hard to change, hard to understand.

### How to Apply
Each class handles a cohesive responsibility. If you find yourself saying "and" when describing it, investigate whether unrelated reasons to change are mixed. A ViewModel exposing state and handling actions for one screen can still be cohesive.


```kotlin
// Partial alternatives. OrderItem, persistence, and formatting are app types.
// BAD: Domain, persistence, and presentation share a change boundary.
interface MixedOrder {
    fun calculateTotal(): Long
    suspend fun saveToDatabase()
    fun generateInvoice(): String
}

// GOOD: Each contract has a cohesive responsibility.
data class OrderItem(val priceMinor: Long, val quantity: Int)

class Order(private val items: List<OrderItem>) {
    fun calculateTotal(): Long = items.sumOf { it.priceMinor * it.quantity }
}

interface OrderRepository {
    suspend fun save(order: Order)
}

fun interface InvoiceGenerator {
    fun generate(order: Order): String
}
```

### Detection Questions
- Does this class have multiple reasons to change?
- Can I describe it without using "and"?
- Would different stakeholders request changes to different parts?

---

## O - Open/Closed Principle (OCP)

> "Software entities should be open for extension but closed for modification."

### Problem It Solves
Having to modify existing, tested code every time requirements change. Risk of breaking working features.

### How to Apply
Design useful extension points where behavior varies. Kotlin functions can be sufficient; a new class is justified when it clarifies an actual policy boundary.


```kotlin
// Standalone Kotlin example; amounts and thresholds are illustrative minor units.
// BAD when new shipping policies repeatedly require editing this selector.
fun shippingCost(type: String, valueMinor: Long): Long = when (type) {
    "standard" -> if (valueMinor < 5_000) 500 else 0
    "express" -> 1_500
    else -> error("Unknown shipping method")
}

// GOOD when independently varying policies justify this boundary.
fun interface ShippingMethod {
    fun calculateCost(orderValueMinor: Long): Long
}

class StandardShipping : ShippingMethod {
    override fun calculateCost(orderValueMinor: Long): Long =
        if (orderValueMinor < 5_000) 500 else 0
}

class ExpressShipping : ShippingMethod {
    override fun calculateCost(orderValueMinor: Long): Long = 1_500
}

class SameDayShipping : ShippingMethod {
    override fun calculateCost(orderValueMinor: Long): Long = 2_500
}
```

### Architectural Insight
OCP at architecture level means: **isolate independently changing policies so adding a feature does not require unrelated changes.** A new feature does not automatically require a new module. Exhaustive `when` over sealed UI state is an idiomatic closed model.

---

## L - Liskov Substitution Principle (LSP)

> "Subtypes must be substitutable for their base types without altering program correctness."

### Problem It Solves
Subclasses that break expectations, requiring type-checking and special cases.

### How to Apply
Subclasses must honor the contract of the parent. If the parent returns positive numbers, subclasses cannot return negatives.


```kotlin
// BAD: An implementation violates the promised non-negative discount.
open class BaseDiscountPolicy {
    open fun discountMinor(valueMinor: Long): Long = 0
}

class WeirdDiscount : BaseDiscountPolicy() {
    override fun discountMinor(valueMinor: Long): Long = -500
}

// GOOD: Constructor validation preserves this example's invariant.
class DiscountPolicy(private val discountMinor: Long) {
    init {
        require(discountMinor >= 0) { "Discount must be non-negative" }
    }

    fun discountMinor(): Long = discountMinor
}
```

### Key Insight
This is why you can swap `InMemoryUserRepository` for `RoomUserRepository` when both honor the `UserRepository` contract. Match missing-item, ordering, persistence, error, Flow delivery, and cancellation semantics; an interface alone cannot guarantee equivalence.

---

## I - Interface Segregation Principle (ISP)

> "Clients should not be forced to depend on methods they do not use."

### Problem It Solves
Fat interfaces that force partial implementations, empty methods, or throws.

### How to Apply
Split large interfaces into smaller, cohesive ones. Clients depend only on what they need.


```kotlin
// BAD: A device must pretend to support unrelated operations.
interface WarehouseDevice {
    fun printLabel(orderId: String)
    fun scanBarcode(): String
    fun packageItem(orderId: String)
}

class IncompatiblePrinter : WarehouseDevice {
    override fun printLabel(orderId: String) {
        println("Label: $orderId")
    }

    override fun scanBarcode(): String =
        throw UnsupportedOperationException("No scanner")

    override fun packageItem(orderId: String): Unit =
        throw UnsupportedOperationException("No packager")
}

// GOOD: Clients depend only on meaningful capabilities.
interface LabelPrinter {
    fun printLabel(orderId: String)
}

interface BarcodeScanner {
    fun scanBarcode(): String
}

interface ItemPackager {
    fun packageItem(orderId: String)
}

class BasicPrinter : LabelPrinter {
    override fun printLabel(orderId: String) {
        println("Label: $orderId")
    }
}
```

### Detection
If implementations repeatedly throw `UnsupportedOperationException` or provide meaningless empty methods, investigate whether the interface is too broad. A legitimate no-op is not automatically a defect.

---

## D - Dependency Inversion Principle (DIP)

> "High-level modules should not depend on low-level modules. Both should depend on abstractions."

### Problem It Solves
Tight coupling to specific implementations (databases, APIs, frameworks). Hard to test, hard to swap.

### How to Apply
Depend on abstractions at meaningful boundaries and inject implementations. Use the app's DI mechanism, including manual construction or factories; do not require a framework or an interface around every pure helper.


```kotlin
// Standalone wiring example. Printing is illustrative, not a real email SDK.
class ConsoleEmailClient {
    fun send(to: String, message: String) {
        println("$to: $message")
    }
}

// BAD: Business logic constructs its infrastructure.
class CoupledOrderService {
    private val emailClient = ConsoleEmailClient()

    fun confirmOrder(email: String) {
        emailClient.send(email, "Order confirmed")
    }
}

// GOOD: The composition root supplies the external capability.
fun interface EmailService {
    fun send(to: String, message: String)
}

class OrderService(private val emailService: EmailService) {
    fun confirmOrder(email: String) {
        emailService.send(email, "Order confirmed")
    }
}

fun consoleOrderService(): OrderService {
    val client = ConsoleEmailClient()
    return OrderService(EmailService(client::send))
}

// A test can supply a recording fake through the same contract.
```

### The Dependency Rule
Source code dependencies should point **inward** toward high-level policies (domain logic), never toward low-level details (infrastructure).

```
Infrastructure → Application → Domain
      ↑              ↑            ↑
    (outer)       (middle)     (inner)

Dependencies flow: outer → inner
Never: inner → outer
```

---

## Applying SOLID at Architecture Level

These principles scale beyond classes:

| Principle | Architecture Application |
|-----------|--------------------------|
| SRP | Each feature/state owner has cohesive responsibilities |
| OCP | Isolate extension points for independently varying behavior |
| LSP | Repository and provider implementations preserve the same observable contract |
| ISP | Focused interfaces between features and data capabilities |
| DIP | High-level business logic doesn't know about databases/frameworks |

---

## Quick Reference

| Principle | One-Liner | Red Flag |
|-----------|-----------|----------|
| SRP | One reason to change | "This class handles X and Y and Z" |
| OCP | Isolate genuine variability | Repeated unrelated edits for one policy |
| LSP | Subtypes are substitutable | Type-checking in calling code |
| ISP | Small, focused interfaces | Empty method implementations |
| DIP | Protect policy boundaries | Constructing transport/storage clients in business logic |

## Android Application

- Separate rendering from screen state and data access; use ViewModels and repositories according to the existing app's architecture.
- Keep Activities, Views, bindings, and navigation controllers outside long-lived business state owners.
- Use constructor injection with existing DI. Domain policy should not import transport or persistence details.
- Preserve coroutine cancellation and main-safety in every interchangeable suspend implementation.
- Add a domain layer or extra modules only when reuse, complexity, or ownership warrants them.

See [Architecture](architecture.md) for lifecycle boundaries and [Testing](testing.md) for contract checks.
