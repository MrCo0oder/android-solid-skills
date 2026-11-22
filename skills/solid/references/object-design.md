# Object-Oriented Design

Examples use Kotlin. Alternatives in separate sections are independent; partial snippets explicitly name the surrounding app context. Amounts and validation rules illustrate design and must follow the real application's contract when adapted.

## Responsibility-Driven Design (RDD)

The key insight: **Objects are defined by their responsibilities, not their data.**

### Finding Objects

Start with:
1. **Nouns** in requirements → candidate objects or values
2. **Verbs** → candidate methods/behaviors
3. **Domain concepts** → value objects

### Finding Responsibilities

Each object should answer:
- What does this object **know**?
- What does this object **do**?
- What does this object **decide**?

### Object Stereotypes

These stereotypes help discuss a class's responsibilities; they are not mandatory categories or reasons to add classes:

| Stereotype | Purpose | Example |
|------------|---------|---------|
| **Information Holder** | Knows things, holds data | `User`, `Product`, `Address` |
| **Structurer** | Maintains relationships | `OrderItems`, `UserGroup` |
| **Service Provider** | Performs work | `PaymentProcessor`, `EmailSender` |
| **Coordinator** | Orchestrates workflow | `OrderFulfillmentService` |
| **Controller** | Makes decisions, delegates | `CheckoutViewModel` |
| **Interfacer** | Transforms between systems | `UserApiAdapter`, `RoomUserMapper` |

### The Two Questions

For every class, ask:
1. **"What responsibility is this?"** - Which stereotype or boundary helps explain it?
2. **"Is it doing too much?"** - Look for unrelated reasons to change

If you can't answer clearly, investigate whether a focused change would improve cohesion. A pure function or data class can already be the simplest design.

---

## Tell, Don't Ask

**Ask the state owner to perform changes that must preserve its invariants.** Reading immutable state for rendering or mapping is appropriate.


```kotlin
// Partial alternatives; account and amount belong to the application's model.
// BAD: The caller can bypass account invariants.
if (account.balance >= amount) {
    account.balance -= amount
}

// GOOD: The owner decides whether a withdrawal is valid.
when (val result = account.withdraw(amount)) {
    is WithdrawResult.Success -> showBalance(result.balanceMinor)
    WithdrawResult.InvalidAmount -> showInvalidAmount()
    WithdrawResult.InsufficientFunds -> showInsufficientFunds()
}
```

Place invariant-preserving behavior with the owner of that state. Simple data snapshots may also contain useful derived properties or transformations.

---

## Design by Contract (DbC)

Every method has:
- **Preconditions** - What must be true BEFORE calling
- **Postconditions** - What will be true AFTER calling
- **Invariants** - What is ALWAYS true about the object


```kotlin
// Standalone Kotlin example; minor-unit amounts and rules are illustrative.
sealed interface WithdrawResult {
    data class Success(val balanceMinor: Long) : WithdrawResult
    object InvalidAmount : WithdrawResult
    object InsufficientFunds : WithdrawResult
}

class BankAccount(initialBalanceMinor: Long) {
    private var balanceMinor = initialBalanceMinor

    init {
        require(initialBalanceMinor >= 0)
    }

    // PRECONDITION for success: amount is positive and covered by the balance.
    // POSTCONDITION: decrease balance on success; otherwise leave it unchanged.
    fun withdraw(amountMinor: Long): WithdrawResult {
        if (amountMinor <= 0) return WithdrawResult.InvalidAmount
        if (amountMinor > balanceMinor) return WithdrawResult.InsufficientFunds

        balanceMinor -= amountMinor
        return WithdrawResult.Success(balanceMinor)
    }
}
```

---

## Composition Over Inheritance

**Prefer composing objects over extending classes.**

### Why Inheritance is Problematic:
- Tight coupling between parent and child
- Fragile base class problem
- Difficult to change parent without breaking children
- Forces "is-a" relationship that may not fit

### When to Use Inheritance:
- True "is-a" relationship (rare)
- Framework requirements
- Template Method pattern (intentional)

### Prefer Composition:

```kotlin
// BAD when each new policy requires another User subtype.
open class BaseUser {
    open fun discountPercent(): Int = 0
}

class PremiumUser : BaseUser() {
    override fun discountPercent(): Int = 20
}

// GOOD: A policy is a collaborator, not part of the User inheritance tree.
fun interface DiscountPolicy {
    fun discountPercent(): Int
}

class User(private val discountPolicy: DiscountPolicy) {
    fun discountPercent(): Int = discountPolicy.discountPercent()
}

fun premiumUser(): User = User(DiscountPolicy { 20 })
fun standardUser(): User = User(DiscountPolicy { 0 })

// If the policy never varies, a direct function/property may be enough.
```

---

## The Law of Demeter (Principle of Least Knowledge)

**Only talk to your immediate friends.**

A method should only call:
1. Methods on `this`
2. Methods on parameters
3. Methods on objects it creates
4. Methods on its direct components


```kotlin
// Partial app-model example.
// Potentially coupled to a collaborator's internal organization:
order.customer.account.shippingAddress.city

// Hide that organization when it is not part of the caller's contract:
order.shippingCity()

// Reading an immutable data snapshot is also legitimate:
val city = addressUiState.city
```

This reduces coupling when it hides a collaborator's internal structure. It is not a one-dot-per-line restriction: Kotlin collection chains and reading immutable data properties are valid.

---

## Encapsulation

**Hide internal details, expose behavior.**

### Levels of Encapsulation:
1. **Data** - private fields, no direct access
2. **Implementation** - how things work internally
3. **Type** - concrete class hidden behind interface
4. **Design** - architectural decisions hidden from clients


```kotlin
// Standalone alternatives. The example excludes tax/currency/overflow handling.
data class Item(val priceMinor: Long, val quantity: Int)

// BAD: Clients can mutate internals and create an inconsistent total.
class MutableOrder {
    val items = mutableListOf<Item>()
    var totalMinor: Long = 0
}

// GOOD: The owner controls updates and computes a consistent total.
class Order {
    private val items = mutableListOf<Item>()

    fun addItem(item: Item) {
        require(item.priceMinor >= 0 && item.quantity > 0)
        items += item
    }

    fun totalMinor(): Long = items.sumOf { it.priceMinor * it.quantity }

    fun itemsSnapshot(): List<Item> = items.toList()
}
```

---

## Polymorphism

**Use types or functions when independently varying behavior warrants them.** A closed enum/sealed model with exhaustive `when` can remain clearer than open polymorphism.


```kotlin
// Standalone Kotlin alternatives; prices are illustrative minor units.
fun shippingCost(method: String, valueMinor: Long): Long = when (method) {
    "standard" -> if (valueMinor < 5_000) 500 else 0
    "express" -> 1_500
    "overnight" -> 2_500
    else -> error("Unknown method")
}

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

fun shippingCost(method: ShippingMethod, valueMinor: Long): Long =
    method.calculateCost(valueMinor)
```

---

## Value Objects vs Entities

### Value Objects
- Defined by their attributes (no identity)
- Immutable
- Comparable by value
- Examples: `Money`, `Email`, `Address`, `DateRange`


```kotlin
// Standalone Kotlin value object. Currency scale/conversion remain app policy.
data class Money(val amountMinor: Long, val currency: String) {
    fun add(other: Money): Money {
        require(currency == other.currency) { "Currency mismatch" }
        return copy(amountMinor = Math.addExact(amountMinor, other.amountMinor))
    }
}

// Data-class equality compares amountMinor and currency.
```

### Entities
- Have identity (survives attribute changes)
- Can be mutable through controlled methods or represented by immutable snapshots
- Have domain identity; choose equality semantics deliberately
- Examples: `User`, `Order`, `Product`


```kotlin
// Standalone Kotlin identity example.
@JvmInline value class UserId(val value: String)

class User(
    val id: UserId,
    private var email: String,
    private var name: String,
) {
    fun hasSameIdentityAs(other: User): Boolean = id == other.id

    fun changeEmail(newEmail: String) {
        email = newEmail
    }
}

// Identity and validation rules belong to the domain contract.
// Do not assume default class equality or data-class equality means identity.
```

---

## Aggregates

A cluster of objects treated as a single unit for data changes.

- One object is the **aggregate root** (entry point)
- External code only references the root
- Root enforces invariants for the entire cluster


```kotlin
// Standalone aggregate example; the maximum is supplied by the caller.
data class Product(val id: String, val priceMinor: Long)
data class OrderItem(val id: String, val product: Product, val quantity: Int)

class Order(private val maximumTotalMinor: Long) {
    private var items: List<OrderItem> = emptyList()

    init {
        require(maximumTotalMinor >= 0)
    }

    fun addItem(itemId: String, product: Product, quantity: Int) {
        require(product.priceMinor >= 0 && quantity > 0)
        require(items.none { it.id == itemId }) { "Duplicate item ID" }
        val candidate = items + OrderItem(itemId, product, quantity)
        validateTotal(candidate) // Validate BEFORE committing the mutation.
        items = candidate
    }

    fun removeItem(itemId: String) {
        items = items.filterNot { it.id == itemId }
    }

    fun itemsSnapshot(): List<OrderItem> = items.toList()

    private fun validateTotal(candidate: List<OrderItem>) {
        val total = candidate.fold(0L) { sum, item ->
            Math.addExact(
                sum,
                Math.multiplyExact(item.product.priceMinor, item.quantity.toLong()),
            )
        }
        require(total <= maximumTotalMinor) { "Order total exceeded" }
    }
}

// Clients update through the root rather than mutating its collection.
```

## Android State Ownership

- A ViewModel owns screen business state and accepts actions; a composable or View renders snapshots. Keep reusable UI components independent of a specific ViewModel where practical.
- Do not retain Activity, Fragment, ViewBinding, View, or NavController references in long-lived state owners.
- Expose read-only StateFlow and replace published collections rather than mutating aliases. `List` is read-only, not deeply immutable, and data-class `copy()` is shallow.
- Hoist UI state only as far as coordination requires. Use saveable state or SavedStateHandle for small supported restoration inputs; neither an in-memory class nor ViewModel provides durable storage.
- Value classes can distinguish domain identifiers, but should earn their cost through actual type safety or invariants. Check serializer and Java interoperability.
- Domain aggregates enforce local invariants; database transactions and server contracts still govern cross-process or remote atomicity.

See [Architecture](architecture.md) for lifetime boundaries and [Testing](testing.md) for verification.
