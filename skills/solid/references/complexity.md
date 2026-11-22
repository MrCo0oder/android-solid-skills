# Managing Complexity

## The Two Types of Complexity

### Essential Complexity

Inherent to the problem domain. Cannot be removed, only managed.

- Business rules
- Domain logic
- User requirements

### Accidental Complexity

Introduced by our solutions. CAN and SHOULD be minimized.

- Poor abstractions
- Unnecessary indirection
- Framework ceremony
- Technical debt

**Goal: Minimize accidental complexity while clearly expressing essential complexity.**

In Android, lifecycle changes, offline requirements, and cancellation can be essential parts of the problem. Duplicate state owners, hidden coroutine scopes, and identical models copied through unnecessary layers can add accidental complexity.

---

## Detecting Complexity

### 1. Change Amplification

Small changes require touching many files.

**Symptom:** "To add this field, I need to update 15 files."

**Cause:** Scattered responsibilities, poor abstraction boundaries.

A DTO, domain model, and UI model may legitimately differ. Investigate whether each boundary expresses a real difference rather than treating the number of files as proof of a problem.

### 2. Cognitive Load

Code is hard to understand, requires holding too much in memory.

**Symptom:** "I need to understand 10 other classes to understand this one."

**Cause:** Tight coupling, hidden dependencies, unclear naming.

A chain of trivial forwarding use cases, repositories, and wrappers can obscure a simple operation. Keep collaborators that own meaningful policy or isolate a real dependency.

### 3. Unknown Unknowns

Behavior is surprising, side effects are hidden.

**Symptom:** "I changed this, and something completely unrelated broke."

**Cause:** Global state, hidden dependencies, implicit contracts.

For asynchronous Android code, trace who starts the work, who owns its scope, when it is cancelled, and which state source is authoritative.

---

## The XP Values for Fighting Complexity

From Extreme Programming:

### 1. Communication

Code should communicate clearly. Names, structure, tests all contribute.

### 2. Simplicity

Do the simplest thing that could possibly work.

### 3. Feedback

Fast feedback loops catch complexity early. Focused tests, CI, code review, and device checks where behavior depends on the platform.

### 4. Courage

Refactor when evidence supports it. Use small, reversible steps and appropriate verification to keep complexity from accumulating.

### 5. Respect

Respect future readers (including yourself). Write for humans first.

---

## KISS - Keep It Simple, Silly

> "The simplest solution that works is usually the best."

### How to Apply:

1. Start with the obvious solution
2. Only add complexity when REQUIRED
3. Prefer boring, well-understood approaches
4. Question every abstraction

Partial Kotlin comparison; the factory creation bodies and application `User`/lookup implementation are omitted:

```kotlin
// Over-engineered when the extra creation layers solve no actual problem.
class UserServiceFactoryProvider private constructor() {
    companion object {
        val instance: UserServiceFactoryProvider by lazy {
            UserServiceFactoryProvider()
        }
    }

    fun createFactory(): UserServiceFactory = TODO("Factory creation")
}

// KISS
class UserService {
    fun getUser(id: String): User = TODO("Existing user lookup")
}
```

A factory or DI provider can be appropriate when construction or lifetime requires it. The problem above is redundant machinery, not the presence of dependency injection. For a small Kotlin utility, a local function may express the operation more clearly than another service class.

---

## YAGNI - You Aren't Gonna Need It

> "Don't build features until they're actually needed."

### Warning Signs:

- "We might need this later"
- "It would be nice to have"
- "Just in case"
- "For future extensibility"

### The Cost of YAGNI Violations:

1. **Development time** - Building unused features
2. **Maintenance burden** - Code that must be maintained
3. **Cognitive load** - More to understand
4. **Wrong abstraction** - Guessing future needs incorrectly

Partial Kotlin alternatives; `Email` is an application value type. These are separate versions of `User`, not declarations to combine in one file.

```kotlin
// YAGNI violation: Building for hypothetical needs
data class User(
    val name: String,
    val email: Email,
    // "We might need these someday"
    val middleName: String? = null,
    val secondaryEmail: Email? = null,
    val faxNumber: String? = null,
    val linkedinProfile: String? = null,
    val twitterHandle: String? = null,
)
```

```kotlin
// YAGNI: Only what's needed NOW
data class User(
    val name: String,
    val email: Email,
)
```

Apply this to speculative architecture too: do not add a generic navigation framework, extra Gradle modules, or offline persistence solely for possible future needs. Preserve fields and behavior required by an existing API or product contract.

---

## DRY - Don't Repeat Yourself (with The Rule of Three)

> "Every piece of knowledge should have a single, unambiguous representation."

### BUT: The Rule of Three

**Repeated examples can reveal a shared concept; three is a heuristic, not a required count.**

Why? The wrong abstraction is worse than duplication. Conversely, duplicating one authoritative business rule can be risky even before a third occurrence.

```text
Duplication #1 → Understand the requirement
Duplication #2 → Ask whether the same knowledge must change together
Duplication #3 → More evidence for extraction, not an automatic command
```

### Example:

Partial Kotlin example; `Order`, `validate`, `calculateTax`, `save`, `sendGuestEmail`, and `applyCorporateDiscount` are application collaborators. Their implementations are omitted. The example preserves the existing operation order and assumes these post-processing differences are intentional.

```kotlin
// First time - keep the straightforward implementation.
fun processUserOrder(order: Order) {
    validate(order)
    calculateTax(order)
    save(order)
}

// Second time - note the similarity and compare the contracts.
fun processGuestOrder(order: Order) {
    validate(order)
    calculateTax(order)
    save(order)
    sendGuestEmail(order)
}

// Third time - another example helps identify the common parts.
fun processCorporateOrder(order: Order) {
    validate(order)
    calculateTax(order)
    save(order)
    applyCorporateDiscount(order)
}

// Once the common workflow is established, extract it.
fun processOrder(
    order: Order,
    postProcessing: (Order) -> Unit = {},
) {
    validate(order)
    calculateTax(order)
    save(order)
    postProcessing(order)
}

// Callers retain their specific post-processing.
fun processGuestOrderWithSharedProcessing(order: Order) {
    processOrder(order, ::sendGuestEmail)
}

fun processCorporateOrderWithSharedProcessing(order: Order) {
    processOrder(order, ::applyCorporateDiscount)
}
```

Share a critical pricing or validation rule as soon as it has a clear common contract. Similar-looking composables in different features may evolve independently; do not force them into one component with flags for every difference. Prefer a small function or component before a hierarchy.

---

## Separation of Concerns

> "Each module should address a single concern."

### Concerns to Separate:

- **Business logic** vs **Infrastructure**
- **What** (policy) vs **How** (mechanism)
- **Input** vs **Processing** vs **Output**
- **Data** vs **Behavior**, where separating them clarifies ownership

These are boundaries to consider, not a requirement for a class, interface, or Gradle module per concern. Keep cohesive behavior with its data when that makes the contract clearer.

### Example:

Partial Kotlin alternatives. The application supplies `Order` (with `items` and `customer.email`), database/email clients, and the collaborators named below. The first example assumes numeric price/quantity values for illustration. The separated version assumes `repository.save(order, total)` persists the calculated total and returns the saved order; adapt that signature to the actual repository contract.

```kotlin
// BAD: Mixed concerns
class OrderProcessor {
    fun process(order: Order) {
        // Validation
        require(order.items.isNotEmpty()) { "Empty" }

        // Business logic
        var total = 0.0
        for (item in order.items) {
            total += item.price * item.quantity
        }

        // Persistence
        val db = Database()
        db.saveOrder(order, total)

        // Notification
        val email = EmailClient()
        email.send(order.customer.email, "Order confirmed")
    }
}
```

```kotlin
// GOOD: Separated concerns
class OrderProcessor(
    private val validator: OrderValidator,
    private val calculator: OrderCalculator,
    private val repository: OrderRepository,
    private val notifier: OrderNotifier,
) {
    fun process(order: Order): ProcessResult {
        validator.validate(order)
        val total = calculator.calculateTotal(order)
        val savedOrder = repository.save(order, total)
        notifier.notifyConfirmation(savedOrder)
        return ProcessResult.success(savedOrder)
    }
}
```

The collaborators earn their place by isolating real rules and infrastructure. A short local calculation does not automatically need its own interface. In Android, keep rendering and UI interaction separate from data access; a use case is useful for a complex or reused business operation, rather than mandatory for every repository call. Blocking I/O and failure/cancellation handling are omitted from this synchronous sketch and must follow the real application's execution contract.

---

## Managing Technical Debt

### Types of Technical Debt:

1. **Deliberate** - Conscious trade-off for speed
2. **Accidental** - Mistakes, lack of knowledge
3. **Bit rot** - Code degrades over time

### The Boy Scout Rule:

> "Leave the code better than you found it."

When a small improvement directly supports the requested change, consider:

- Improving an unclear name in the affected path
- Extracting a method when it clarifies that change
- Adding focused coverage where the change needs confidence

This is not a cleanup quota. Keep unrelated cleanup out of scope, preserve other worktree edits, and report adjacent findings separately. A behavior-preserving refactor should preserve visible content, API payloads, navigation, analytics, and relevant error timing.

### When to Pay Down Debt:

- When it's in your path and materially helps the requested change
- When it's blocking new features
- When it's causing bugs
- During dedicated refactoring time

### When NOT to Refactor:

- Code that works and has no relevant maintenance problem
- Code being replaced soon
- When verification is inadequate for the risk; first establish focused coverage or another appropriate check

Measure before changing dispatchers, Flow sharing, caching, or Compose stability annotations for performance. A passing unit test does not demonstrate reduced jank or faster startup.

---

## The Four Elements of Simple Design

In priority order (from XP):

1. **Runs all the tests**
   - If it doesn't work, nothing else matters
   - Choose checks appropriate to the change; builds, unit tests, device behavior, and live API checks provide different evidence

2. **Expresses intent**
   - Clear names, obvious structure
   - Code tells the story

3. **No duplication**
   - Share knowledge that must change together; use the Rule of Three as a heuristic
   - Single source of truth

4. **Minimal**
   - Enough classes and methods to make responsibilities clear
   - Avoid machinery that does not solve a current problem

These are useful design checks, not a numerical score or proof that every behavior is correct.

See [Code smells](code-smells.md) for concrete symptoms and [Testing](testing.md) for choosing evidence.
