# Code Smells & Anti-Patterns

## What Are Code Smells?

Indicators that something MAY be wrong. Not bugs, but design problems that make code hard to understand, change, or test.

A smell is a reason to investigate, not proof that a rewrite is needed. Start with the user's requested behavior and preserve unrelated code. Examples below are independent; before/after alternatives are not declarations to combine in one Kotlin file. Partial snippets identify their missing application context.

## The Five Categories

### 1. Bloaters

Code that has grown too large or accumulated unrelated work.

| Smell | Symptom | Refactoring |
|-------|---------|-------------|
| **Long Method** | Several responsibilities or hard-to-follow control flow | Extract meaningful operations |
| **Large Class** | Multiple unrelated responsibilities | Extract a cohesive responsibility |
| **Long Parameter List** | Arguments are hard to distinguish or repeatedly travel together | Named arguments; introduce a parameter object for a real concept |
| **Data Clumps** | Same meaningful group of variables appears together | Extract a coherent type when it clarifies the contract |
| **Primitive Obsession** | Primitives obscure domain distinctions or repeated validation | Consider a value type for the domain invariant |

Line counts, parameter counts, and property counts can prompt a review; they are not defect thresholds. A coherent screen-state data class or readable declarative composable may legitimately be large.

### 2. Object-Orientation Abusers

Misuse of OO principles.

| Smell | Symptom | Refactoring |
|-------|---------|-------------|
| **Switch Statements** | Repeated type-dependent branching causes scattered changes | Consider polymorphism or centralizing the policy |
| **Parallel Inheritance** | Adding a subclass requires adding another | Reconsider or merge coupled hierarchies |
| **Refused Bequest** | Subclass cannot honor the parent contract | Consider composition or delegation |
| **Alternative Classes** | Different interfaces obscure the same concept | Align names/contracts or extract shared behavior where useful |

An exhaustive Kotlin `when` over a sealed type is idiomatic. Prefer it when variants are finite and the operation reads clearly; adding a hierarchy is not automatically an improvement.

### 3. Change Preventers

Code that makes changes difficult.

| Smell | Symptom | Refactoring |
|-------|---------|-------------|
| **Divergent Change** | One class changed for many unrelated reasons | Extract Class (SRP) |
| **Shotgun Surgery** | One conceptual change touches many unrelated classes | Move related behavior/data together |
| **Parallel Inheritance** | (see above) | Reconsider coupled hierarchies |

Some changes legitimately cross UI, persistence, and API boundaries. Identify duplicated knowledge or misplaced responsibility before removing a boundary.

### 4. Dispensables

Code that may be removed or simplified when it serves no current purpose.

| Smell | Symptom | Refactoring |
|-------|---------|-------------|
| **Comments** | Comments compensate for avoidably unclear code | Improve names/structure; retain useful rationale |
| **Duplicate Code** | Duplicated knowledge must change together | Extract the shared concept when its contract is clear |
| **Dead Code** | Unreachable or unused code, confirmed in context | Remove within the authorized scope |
| **Speculative Generality** | Unused "just in case" machinery | Simplify when appropriate (YAGNI) |
| **Lazy Class** | A class adds no meaningful responsibility or boundary | Consider inlining it |

Useful KDoc, legal attribution, protocol details, and concurrency rationale should stay. Reflection, serialization, generated code, and framework entry points can make code look unused to a local text search.

### 5. Couplers

Excessive coupling between classes.

| Smell | Symptom | Refactoring |
|-------|---------|-------------|
| **Feature Envy** | Method uses another class's data extensively | Move behavior to its appropriate owner |
| **Inappropriate Intimacy** | Classes depend on each other's internals | Move behavior or introduce a focused operation |
| **Message Chains** | A caller must navigate several implementation details | Consider hiding the unstable traversal |
| **Middle Man** | A class only forwards without a useful boundary | Consider inlining it |

Kotlin collection chains and delegation are valid tools. A short chain is not inherently a coupling problem, and a forwarding adapter can protect a meaningful external contract.

---

## The Seven Most Common Code Smells

### 1. Long Method

**Symptom:** A method does several distinct things and is difficult to follow; length alone is not the problem.

Partial Kotlin comparison. The application supplies `Order`, `getTaxRate`, `db`, and `emailService`. Here `Order` has numeric item prices/quantities/discounts, a nullable customer, and `copy(total = ...)`; the extracted helper implementations are omitted. The arithmetic and operation order illustrate the existing workflow, not a production monetary specification.

```kotlin
// SMELL
fun processOrder(order: Order) {
    // Validate
    require(order.items.isNotEmpty()) { "Empty" }
    val customer = requireNotNull(order.customer) { "No customer" }

    // Calculate
    var total = 0.0
    for (item in order.items) {
        total += item.price * item.quantity
        val discount = item.discount
        if (discount != null) {
            total -= discount
        }
    }

    // Apply tax
    val taxRate = getTaxRate(customer.state)
    total *= 1 + taxRate

    // Save
    db.orders.insert(order.copy(total = total))

    // Notify
    emailService.send(customer.email, "Order confirmed")
}
```

```kotlin
// REFACTORED
fun processOrder(order: Order) {
    validateOrder(order)
    val total = calculateTotal(order)
    saveOrder(order, total)
    notifyCustomer(order)
}
```

Each extracted name should explain a meaningful step. Preserve validation, rounding, error propagation, and side-effect order; creating four one-line wrappers is not itself proof of better design.

### 2. Large Class

**Symptom:** A class has many unrelated responsibilities and reasons to change, rather than merely many lines or properties.

Partial Kotlin alternatives; method bodies stand in for application behavior and are omitted.

```kotlin
// SMELL: God class
class User(val name: String, val email: String) {
    // Authentication
    fun login() { /* Existing behavior */ }
    fun logout() { /* Existing behavior */ }
    fun resetPassword() { /* Existing behavior */ }

    // Preferences
    fun setTheme() { /* Existing behavior */ }
    fun setLanguage() { /* Existing behavior */ }

    // Notifications
    fun sendEmail() { /* Existing behavior */ }
    fun sendSms() { /* Existing behavior */ }

    // Billing
    fun charge() { /* Existing behavior */ }
    fun refund() { /* Existing behavior */ }
}
```

```kotlin
// REFACTORED: Separate cohesive responsibilities
data class User(val name: String, val email: String)

class AuthService {
    fun login() { /* Existing behavior */ }
    fun logout() { /* Existing behavior */ }
    fun resetPassword() { /* Existing behavior */ }
}

class UserPreferences {
    fun setTheme() { /* Existing behavior */ }
    fun setLanguage() { /* Existing behavior */ }
}

class NotificationService {
    fun sendEmail() { /* Existing behavior */ }
    fun sendSms() { /* Existing behavior */ }
}

class BillingService {
    fun charge() { /* Existing behavior */ }
    fun refund() { /* Existing behavior */ }
}
```

Split where responsibilities actually vary independently. A data class with many fields can remain a coherent snapshot, and related ViewModel state/actions need not be scattered to meet a size quota.

### 3. Feature Envy

**Symptom:** A method uses another class's data more than its own.

Standalone Kotlin alternatives demonstrating the same illustrative shipping policy:

```kotlin
// SMELL: Order envies Customer
data class Customer(val country: String, val state: String)

class Order {
    fun calculateShipping(customer: Customer): Int {
        if (customer.country == "US") {
            if (customer.state == "CA") return 10
            return 15
        }
        return 25
    }
}
```

```kotlin
// REFACTORED: Move to Customer
class Customer(val country: String, val state: String) {
    fun shippingCost(): Int {
        if (country == "US") {
            if (state == "CA") return 10
            return 15
        }
        return 25
    }
}

class Order(private val customer: Customer) {
    fun calculateShipping(): Int = customer.shippingCost()
}
```

Moving behavior to Customer is appropriate only if Customer owns this rule. When shipping depends on carrier, order contents, or external configuration, a shipping policy may be the better owner. An external mapper or calculator legitimately reads another type's data.

### 4. Primitive Obsession

**Symptom:** Primitive types obscure important domain distinctions or allow repeated, inconsistent validation.

Partial Kotlin alternatives. User creation is omitted; `Address` is an application type. These validation rules are deliberately simplified examples, not a complete email specification or a prescribed age policy.

```kotlin
// SMELL
fun createUser(email: String, age: Int, zipCode: String) {
    // Validation is repeated at use sites; strings are easy to mix up.
    require('@' in email) { "Invalid email" }
    require(age in 0..150) { "Invalid age" }
    // Create the user using email, age, and zipCode.
}
```

```kotlin
// REFACTORED: Value objects
@JvmInline
value class Email(val value: String) {
    init {
        require('@' in value) { "Invalid email" }
    }
}

@JvmInline
value class Age(val value: Int) {
    init {
        require(value in 0..150) { "Invalid age" }
    }
}

fun createUser(email: Email, age: Age, address: Address) {
    // Construction has checked the example's Email/Age invariants.
    // Create the user using the supplied domain values.
}
```

Use the application's actual validation contract and check serialization/framework interoperability when adding value classes. A primitive remains appropriate when stronger type safety or centralized validation would add little. Wrapping every string, number, and parameter is not a goal.

### 5. Switch Statements

**Symptom:** Repeated branching on type forces the same conceptual change into many locations.

Partial Kotlin alternatives. The first example uses a finite sealed set; the triangle perimeter body is omitted. The polymorphic version shows Circle only, with Rectangle and Triangle implementations omitted. Each alternative imports `kotlin.math.PI`.

```kotlin
import kotlin.math.PI

sealed interface Shape {
    data class Circle(val radius: Double) : Shape
    data class Rectangle(val width: Double, val height: Double) : Shape
    data class Triangle(val base: Double, val height: Double) : Shape
}

// POTENTIAL SMELL: Repeated type-dependent policy
fun getArea(shape: Shape): Double = when (shape) {
    is Shape.Circle -> PI * shape.radius * shape.radius
    is Shape.Rectangle -> shape.width * shape.height
    is Shape.Triangle -> 0.5 * shape.base * shape.height
}

fun getPerimeter(shape: Shape): Double = when (shape) {
    is Shape.Circle -> 2 * PI * shape.radius
    is Shape.Rectangle -> 2 * (shape.width + shape.height)
    is Shape.Triangle -> TODO("Existing triangle perimeter calculation")
}
```

```kotlin
import kotlin.math.PI

// REFACTORED: Polymorphism
interface Shape {
    fun getArea(): Double
    fun getPerimeter(): Double
}

class Circle(private val radius: Double) : Shape {
    override fun getArea(): Double = PI * radius * radius
    override fun getPerimeter(): Double = 2 * PI * radius
}
```

The first version may already be the clearer Kotlin design. Exhaustive `when` is useful for finite states/actions and makes new cases visible to the compiler. Consider polymorphism when variants own behavior and repeated branching creates a demonstrated maintenance problem; do not mechanically replace every `when`.

### 6. Inappropriate Intimacy

**Symptom:** Classes know too much about each other's internals.

Partial Kotlin alternatives. The application supplies `OrderItem` (SKU and quantity), inventory storage, `ReserveResult`, and `OutOfStockError`. In the refactored version, `canReserve` and `deductStock` are omitted inventory implementation details.

```kotlin
// SMELL
class Order(private val items: List<OrderItem>) {
    fun process() {
        val inventory = Inventory()

        // Reaching into inventory's internals
        for (item in items) {
            val stock = inventory.stockLevels.getValue(item.sku)
            check(stock.quantity >= item.quantity) { "Out of stock" }
            stock.quantity -= item.quantity
        }
    }
}
```

```kotlin
// REFACTORED: Tell, don't ask
class Inventory {
    fun reserve(items: List<OrderItem>): ReserveResult {
        // Inventory manages its own state.
        for (item in items) {
            if (!canReserve(item)) {
                return ReserveResult.outOfStock(item)
            }
        }
        deductStock(items)
        return ReserveResult.success()
    }

    private fun canReserve(item: OrderItem): Boolean =
        TODO("Check inventory under the application's reservation contract")

    private fun deductStock(items: List<OrderItem>) {
        // Existing stock update.
    }
}

class Order(private val items: List<OrderItem>) {
    fun process(inventory: Inventory) {
        val result = inventory.reserve(items)
        if (!result.isSuccess()) {
            throw OutOfStockError(result.failedItem)
        }
    }
}
```

This sketch demonstrates ownership, not an atomic reservation implementation. Real inventory logic must handle repeated SKUs, concurrent changes, partial failure, and any server transaction contract. Exposing a focused operation lets the inventory implementation own those rules.

### 7. Speculative Generality

**Symptom:** "Just in case" abstractions that aren't used.

Partial Kotlin alternatives; actual payment processing is omitted. The class name is illustrative and does not represent a provider SDK contract.

```kotlin
// SMELL: Over-engineered for hypothetical needs
interface PaymentProcessor {
    fun process()
    fun rollback()
    fun audit()
    fun generateReport()
    fun scheduleRecurring()
}

class StripeProcessor : PaymentProcessor {
    override fun process() { /* Actual payment code */ }
    override fun rollback(): Unit = error("Not implemented")
    override fun audit(): Unit = error("Not implemented")
    override fun generateReport(): Unit = error("Not implemented")
    override fun scheduleRecurring(): Unit = error("Not implemented")
}
```

```kotlin
// REFACTORED: YAGNI
interface PaymentProcessor {
    fun process()
}

class StripeProcessor : PaymentProcessor {
    override fun process() { /* Actual payment code */ }
}
// Add other capabilities when a real requirement establishes their contract.
```

Before removing existing capabilities, trace callers and external contracts. Keep needed payment failure/retry semantics; a smaller interface does not make a real rollback or recurring-payment requirement disappear.

---

## Prevention Strategies

1. **Use Object Calisthenics selectively** - Exercises can expose design issues; their numeric constraints are not Kotlin production rules
2. **Use focused tests** - Tests provide feedback on behavior and design; TDD is one useful approach
3. **Review in pairs** - Fresh eyes catch smells
4. **Refactor when it supports the work** - Keep improvements scoped and verifiable
5. **Apply SOLID with judgment** - Clarify actual responsibilities and contracts
6. **Use static analysis** - Tools flag candidates for review, not automatic mandates for rewriting

---

## When You Find a Smell

1. **Confirm it's a problem** - Not all smells need fixing
2. **Establish appropriate verification** - Use existing coverage or add a focused behavioral regression
3. **Refactor in small steps** - Keep behavior and relevant checks stable
4. **Keep changes reviewable and reversible** - Commit only when requested and preserve unrelated work

A request to review code is not authorization for unrelated cleanup. For each finding, identify the trigger, observable impact, and root-cause location. Distinguish confirmed bugs from suggestions and unverified hypotheses.

---

## Android-Specific Symptoms

| Symptom | Investigate | Focused response |
| --- | --- | --- |
| Refresh shows an error after cancellation | Broad catch or runCatching around suspending work | Preserve CancellationException and test error mapping |
| Fragment updates a destroyed binding | Fragment scope used for view rendering | Use viewLifecycleOwner and clean up binding |
| A request repeats on recomposition | Side effect in composable body or incorrect effect keys | Move to an owned action/effect and check restart semantics |
| Stale UI after a state change | Mutable alias or in-place collection change | Publish a new snapshot |
| Main-thread stalls | Blocking IO or expensive computation | Make the operation main-safe and measure |
| An old search overwrites a newer result | Concurrent jobs, stale response ordering | Apply the feature's cancellation/order policy |
| Two screens unexpectedly share state | Wrong ViewModel/DI scope | Correct ownership and verify back-stack behavior |
| Retry creates duplicate writes | Hidden retry, repeated taps, missing request contract | Verify concurrency/idempotency at the proper boundary |
| One small change touches many wrappers | Redundant layers or duplicate models | Simplify the boundary in the affected slice |
| Tests hang collecting Flow | Unbounded collection or missing sharing subscriber | Bound collection and control its lifetime |

### Not Automatic Defects

- A data class with many properties can be a coherent screen snapshot.
- A long declarative composable may read clearly; extract meaningful sections rather than enforcing a line limit.
- A stateless content composable may have several callbacks. Group by a real concept, not a parameter quota.
- Exhaustive `when` over a sealed type is idiomatic.
- `else`, data-class properties, Kotlin collection chains, and concrete dependencies are valid tools.
- A primitive is appropriate until stronger type safety or validation earns a wrapper.
- Useful KDoc, legal attribution, and concurrency rationale should stay.

### Example: Cancellation Swallowed by a Broad Catch

Partial anti-pattern; `refresh` suspends and `showFailure` publishes an error:

```kotlin
try {
    refresh()
} catch (failure: Exception) {
    showFailure(failure)
}
```

Prefer catching the actual expected failure, such as IOException, when that matches the API. When an existing boundary genuinely needs a broad catch, preserve cancellation before mapping it.

Partial repair of that boundary; requires `kotlinx.coroutines.CancellationException`. The other functions belong to the existing app.

```kotlin
try {
    refresh()
} catch (cancelled: CancellationException) {
    throw cancelled
} catch (failure: Exception) {
    showFailure(failure)
}
```

Do not present a broad catch as a default error policy. Verify that cancellation produces no failure UI, while genuine service failures still do. See [Clean code](clean-code.md) and [Testing](testing.md).

### Cohesion and Coupling

Look for unrelated reasons to change: transport parsing mixed with rendering, navigation mixed with persistence, or shared state written by several owners.

Prefer composition over a broad BaseActivity, BaseFragment, or BaseViewModel that accumulates feature behavior. Keep useful framework integration and existing conventions; extract only the responsibility causing the problem.

A repository interface can protect a data contract. An interface for every pure utility and a use case for every getter can obscure it. See [Complexity](complexity.md).

### Repair Workflow

1. State the actual failure or change cost and locate its cause.
2. Trace callers, data contracts, and ownership before choosing a fix.
3. Use existing coverage or add a focused behavioral regression.
4. Make the smallest cohesive repair and verify affected consumers.
5. Report adjacent findings separately; do not treat a review as authorization to redesign the app.
