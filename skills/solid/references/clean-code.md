# Clean Code Practices

> Parts of this guide are based on concepts from the **"Clean Code" course summary** by [Academind GmbH / Maximilian Schwarzmuller](https://academind.com) (c) 2020. Examples and application notes are adapted for Kotlin and Android.

Examples below are **partial Kotlin teaching snippets**, not complete application implementations. BAD/GOOD alternatives belong in separate scopes. Domain types, repositories, validators, loggers, UI error presenters, and services are supplied by the surrounding application unless defined in the snippet; coroutine examples use the project's coroutine dependencies. Use the existing architecture and DI setup for those dependencies. Authentication, validation, pricing, IDs, and API fields must follow the real application contract; the examples do not define new policies.

## What is Clean Code?

Code that is:
- **Easy to understand** - reveals intent clearly
- **Easy to change** - modifications are localized
- **Easy to test** - dependencies can be controlled through the project's existing seams
- **Simple** - no unnecessary complexity

## The Human-Centered Approach

Code has THREE consumers:
1. **Users** - get their needs met
2. **Customers** - make or save money
3. **Developers** - must maintain it

Design for all three, but remember: **developers read code much more often than they write it.** The familiar "10x" saying is a readability heuristic, not a measured requirement.

## Naming Principles

### 1. Consistency & Uniqueness (HIGHEST PRIORITY)
Same concept = same name everywhere. One name per concept. Preserve distinct names when the domain distinguishes them: a customer is not automatically a user, and a cart-line ID is not a product ID.

```kotlin
// BAD: Inconsistent names for the same concept
getUserById(id)
fetchCustomerById(id)
retrieveClientById(id)

// GOOD: Consistent names when these are the same domain concept
getUser(id)
getOrder(id)
getProduct(id)
```

### 2. Understandability
Use domain language, not technical jargon.

```kotlin
// BAD: Technical
val arr = users.filter { u -> u.isActive }

// GOOD: Domain language
val activeCustomers = customers.filter { customer -> customer.isActive }
```

### 3. Specificity
Avoid vague names: `data`, `info`, `manager`, `handler`, `processor`, `utils`. Treat these as prompts to seek a more precise name, not a ban on established framework or domain terminology.

```kotlin
// BAD: Vague
class DataManager
fun processInfo(data: Payment) { /* ... */ }

// GOOD: Specific
class OrderRepository
fun validatePayment(payment: Payment) { /* ... */ }
```

### 4. Brevity (but not at cost of clarity)
Short names are good only if meaning is preserved.

```kotlin
// BAD: Too cryptic
val usrLst = getUsrs()

// BAD: Unnecessarily long
val listOfAllActiveUsersInTheSystem = getActiveUsers()

// GOOD: Brief but clear
val activeUsers = getActiveUsers()
```

### 5. Searchability
Names should be unique enough to grep/search.

```kotlin
// BAD: Common word, hard to search
val data = fetch()

// GOOD: Unique, searchable
val orderSummary = fetchOrderSummary()
```

### 6. Pronounceability
You should be able to say it in conversation.

```kotlin
// BAD
val genymdhms = generateYearMonthDayHourMinuteSecond()

// GOOD
val timestamp = generateTimestamp()
```

### 7. Austerity
Avoid unnecessary filler words.

```kotlin
// BAD: Redundant
val userData = currentUser // "Data" adds nothing here
class UserClass           // "Class" adds nothing

// GOOD
val user = currentUser
class User
```

---

## Functions & Methods

Functions are the building blocks of any codebase. Clean functions are **small, focused, and readable**.

### Minimize Parameters

The fewer independent concepts a caller must understand, the easier the function is to read and call. Parameter count is a review signal, not a quota. Kotlin named arguments and sensible defaults often make an explicit API clear; a stateless composable can reasonably expose several independent callbacks.

```kotlin
// Clear intent when no input is needed
createSession()
user.save()

// One parameter can be straightforward
isValid(email)
file.write(data)

// Two parameters can describe a natural operation
login(email = "test@example.com", password = suppliedPassword)
createProduct(name = "Carpet", price = price)

// Many positional arguments are hard to distinguish
createUser("Max", "Max", "test@example.com", suppliedPassword, 31, interests)

// Named arguments make the same API easier to review
createUser(
    firstName = "Max",
    lastName = "Max",
    email = "test@example.com",
    password = suppliedPassword,
    age = 31,
    interests = interests,
)
```

**Reduce parameters by grouping cohesive values into objects:**

Do this when the values form a meaningful concept. Do not introduce a generic parameter bag solely to reduce the count.

```kotlin
// BAD: Many indistinguishable positional parameters
createRectangle(10, 9, 30, 12)

// GOOD: Named arguments clarify a simple call
createRectangle(x = 10, y = 9, width = 30, height = 12)

// GOOD: A parameter object when these values form a reusable concept
data class RectangleBounds(
    val x: Int,
    val y: Int,
    val width: Int,
    val height: Int,
)

createRectangle(RectangleBounds(x = 10, y = 9, width = 30, height = 12))
```

### Keep Functions Small

Small functions are easier to read and encourage well-named helper functions. Prefer a coherent operation over an arbitrary line limit; excessive extraction can make the reader jump between trivial helpers.

```kotlin
// BAD: Long function with mixed concerns
suspend fun login(email: String, password: String) {
    if (!isValidEmail(email) || !isValidPasswordInput(password)) {
        throw InvalidLoginInput()
    }
    val existingUser = userRepository.findByEmail(email)
        ?: throw UserNotFound()
    if (credentialVerifier.matches(password, existingUser.passwordHash)) {
        sessionRepository.create(existingUser.id)
    } else {
        throw InvalidCredentials()
    }
}

// GOOD: Small, composed functions at the orchestration level
suspend fun login(email: String, password: String) {
    validateUserInput(email, password)
    val existingUser = findUserByEmail(email)
    verifyCredentials(existingUser, password)
    createSession(existingUser)
}
```

### Do One Thing (Levels of Abstraction)

Functions should do **one thing** at **one level of abstraction**.

Aim for operations on the **same level** of abstraction, usually **one level below** the function name. Use this as a readability test, not a requirement to hide every constructor or simple expression behind another function.

```kotlin
// BAD: Mixed levels of abstraction
suspend fun printDocument(documentPath: String) {
    val config = ReadConfig(mode = ReadMode.READ, onError = OnError.RETRY)
    val document = fileSystem.readFile(documentPath, config)
    val printer = Printer(format = PrintFormat.PDF)
    printer.print(document)
}

// GOOD: Consistent abstraction level
suspend fun printDocument(documentPath: String) {
    val document = readFromFile(documentPath)
    val printer = Printer(format = PrintFormat.PDF)
    printer.print(document)
}
```

### Split Functions Reasonably

Don't extract just for the sake of extraction. **Three warning signs** of bad splits:
1. You're just **renaming the operation** (e.g., `buildUser()` that just calls `User(...)`)
2. You need to **scroll more** to follow a simple function
3. You **can't find a good name** because the original name is already taken

```kotlin
// OVER-SPLIT: Too many trivial extractions
suspend fun createUser(email: String, password: String) {
    validateInput(email, password)
    saveUser(email, password)
}

suspend fun saveUser(email: String, password: String) {
    val user = buildUser(email, password)
    userRepository.save(user)
}

fun buildUser(email: String, password: String): User {
    return User(email = email, passwordHash = passwordHasher.hash(password))
}

// BETTER: Meaningful splits only
suspend fun createUser(email: String, password: String) {
    validateInput(email, password)
    val user = User(email = email, passwordHash = passwordHasher.hash(password))
    userRepository.save(user)
}
```

**Two rules of thumb for when to split:**
1. Extract code that works on the **same functionality** / is closely related
2. Extract code that requires **more interpretation** than the surrounding code

### Avoid Unexpected Side Effects

A side effect is unexpected when the function name doesn't imply it.

```kotlin
// BAD: Name says "validate", but also creates a session
suspend fun validateUserInput(email: String, password: String) {
    if (!isValidEmail(email) || !isValidPasswordInput(password)) {
        throw InvalidLoginInput()
    }
    createSession() // unexpected!
}

// GOOD: Move the side effect out, or make the name reveal it
suspend fun validateAndInitSession(email: String, password: String) {
    validateUserInput(email, password) // validation only in this alternative
    createSession()
}
```

---

## Control Structures

Control structures (`if`, `for`, `while`, `when`) can lead to suboptimal code. Three areas to focus on:

### Prefer Positive Checks

Use positive wording in conditions when possible.

```kotlin
// GOOD: Positive check
if (blogContent.isEmpty()) {
    // Report the missing content.
}

// LESS CLEAR: Negated positive requires extra interpretation
if (!hasContent(blogContent)) {
    // Report the missing content.
}
```

Exception: sometimes a negative check is cleaner when there are multiple valid states.

```kotlin
// GOOD: Negative check avoids enumerating all other states
if (!transaction.isOpen) {
    // Report that the transaction cannot proceed.
}
```

### Avoid Deep Nesting

Deeply nested code is hard to read and error-prone. Strategies to flatten:

#### 1. Use Guards & Fail Fast

```kotlin
// BAD: Deep nesting
suspend fun messageUser(user: User?, message: String?) {
    if (user != null) {
        if (!message.isNullOrBlank()) {
            if (user.acceptsMessages) {
                val success = user.sendMessage(message)
                if (success) {
                    logger.info("Message sent")
                }
            }
        }
    }
}

// GOOD: Guard clauses keep the main operation visible
suspend fun messageUser(user: User?, message: String?) {
    if (user == null || message.isNullOrBlank() || !user.acceptsMessages) {
        return
    }
    val success = user.sendMessage(message)
    if (success) {
        logger.info("Message sent")
    }
}
```

#### 2. Extract Control Structures into Functions

```kotlin
// BAD: Nested control structure
suspend fun connectDatabase(uri: String?): ConnectionDetails {
    require(!uri.isNullOrBlank()) { "A URI is required" }
    val database = Database(uri)
    val success = database.connect()
    if (!success) {
        if (database.hasFallbackConnection) {
            return database.fallbackConnectionDetails
        } else {
            throw ConnectionFailed()
        }
    }
    return database.connectionDetails
}

// GOOD: Extract nested logic
suspend fun connectDatabase(uri: String?): ConnectionDetails {
    validateUri(uri)
    val database = Database(requireNotNull(uri))
    return if (database.connect()) {
        database.connectionDetails
    } else {
        connectFallbackDatabase(database)
    }
}
```

#### 3. Use Polymorphism & Factory Functions

Replace duplicated conditional logic with polymorphic objects when behavior varies independently. A small exhaustive `when` over a sealed type or enum is also idiomatic Kotlin; do not add a hierarchy solely to remove a clear branch. The example assumes an exhaustive `PaymentMethod` enum and processors supplied by the existing DI setup.

```kotlin
// BAD: Repeated type checks
suspend fun processTransaction(transaction: Transaction) {
    if (transaction.isPayment) {
        if (transaction.method == PaymentMethod.CREDIT_CARD) {
            processCreditCardPayment(transaction)
        }
        if (transaction.method == PaymentMethod.PAYPAL) {
            processPayPalPayment(transaction)
        }
    } else {
        if (transaction.method == PaymentMethod.CREDIT_CARD) {
            processCreditCardRefund(transaction)
        }
        if (transaction.method == PaymentMethod.PAYPAL) {
            processPayPalRefund(transaction)
        }
    }
}

// GOOD: Polymorphic processors supplied by the existing DI setup
interface TransactionProcessor {
    suspend fun processPayment(transaction: Transaction)
    suspend fun processRefund(transaction: Transaction)
}

fun getProcessor(method: PaymentMethod): TransactionProcessor =
    when (method) {
        PaymentMethod.CREDIT_CARD -> creditCardProcessor
        PaymentMethod.PAYPAL -> payPalProcessor
    }

suspend fun processTransaction(transaction: Transaction) {
    val processor = getProcessor(transaction.method)
    if (transaction.isPayment) {
        processor.processPayment(transaction)
    } else {
        processor.processRefund(transaction)
    }
}
```

#### 4. Embrace Errors (throw instead of error codes)

Prefer meaningful failure contracts over undocumented numeric codes. The exception approach below is appropriate when that is the existing contract. Expected validation failures can instead use a sealed outcome or the project's typed result model; do not replace one consistently used contract merely to adopt exceptions. Use `require`/`check` for programmer preconditions/invariants, not as the sole presentation path for expected invalid UI input. Catch expected failures at an intentional boundary.

```kotlin
// BAD: Undocumented numeric codes couple validation and presentation
suspend fun createUser(email: String, password: String) {
    val validity = validateInput(email, password)
    if (validity.code == 1 || validity.code == 2) {
        showValidationError(validity.message)
        return
    }
    // ... continue
}

// GOOD: With an existing exception-based contract, catch expected failures
suspend fun handleSignupRequest(request: SignupRequest) {
    try {
        createUser(request.email, request.password)
    } catch (failure: SignupValidationException) {
        showValidationError(failure.reason)
    }
}

suspend fun createUser(email: String, password: String) {
    validateInput(email, password)
    // ... continue
}

suspend fun validateInput(email: String, password: String) {
    if (!isValidEmail(email) || !isValidPasswordInput(password)) {
        throw SignupValidationException(SignupError.InvalidInput)
    }
    if (findUserByEmail(email) != null) {
        throw SignupValidationException(SignupError.EmailTaken)
    }
}
```

---

## Classes & Objects

### Objects vs Data Containers

Distinguish between **objects** (hide data, expose behavior) and **data containers** (expose data, no behavior).

```kotlin
// Data container: exposes values
data class UserData(val name: String, val age: Int)

// Object: hides state, exposes behavior
class User(
    private val name: String,
    private val age: Int,
) {
    fun greet(): String = "Hi! I'm $name and I'm $age years old."
}
```

Both are valid - use the right kind for the right job. **Don't mix types** means keep ownership and invariants clear: do not reach into an object's hidden collaborators and update its internals from outside. Kotlin data classes can have validation, derived properties, or small value operations; they need not be behavior-free. DTOs and UI state naturally expose data without getter/setter wrappers.

### Class Cohesion

**Cohesion** = how closely a class's state and methods support one responsibility. Looking at which properties methods use can help, but not every method must use most properties.

- **High cohesion** → well-designed, focused class
- **Low cohesion** → review whether responsibilities should be separated; a data container may also be appropriate

When cohesion decreases, consider **smaller, more focused classes** if the split clarifies ownership and change boundaries. Do not create extra layers solely to improve a metric.

---

## Object Calisthenics (9 Rules)

Exercises to improve OO design. These nine rules are **optional practice constraints**, not production acceptance criteria. Their deliberately strict form helps reveal coupling; apply the underlying lesson with Kotlin and Android judgment. Do not reshape data classes, composables, ViewModels, or an existing architecture just to satisfy a count or syntax rule.

### 1. One Level of Indentation per Method

During practice, use extraction to see whether nesting conceals a meaningful operation. In production, guards, a direct loop, or an exhaustive `when` can be clearer. Collection chains may allocate intermediate lists or alter evaluation order; do not mechanically replace loops to meet this constraint.

```kotlin
// Multiple indentation levels to explore during the exercise
fun process(orders: List<Order>) {
    for (order in orders) {
        if (order.isValid()) {
            for (item in order.items) {
                if (item.inStock) {
                    processItem(item)
                }
            }
        }
    }
}

// One possible extraction when the helper has a useful meaning
fun process(orders: List<Order>) {
    orders.filter { it.isValid() }.forEach(::processOrder)
}

fun processOrder(order: Order) {
    order.items.filter { it.inStock }.forEach(::processItem)
}
```

### 2. Don't Use the ELSE Keyword

Use early returns, guard clauses, or polymorphism during the exercise. In production, `if`/`else` expressions and exhaustive `when` expressions are idiomatic Kotlin, especially when every branch produces a value. Prefer the form that makes the decision clearest.

```kotlin
// Starting point for the exercise
fun getDiscount(user: User): Int {
    if (user.isPremium) {
        return 20
    } else {
        return 0
    }
}

// Practice alternative: early return
fun getDiscount(user: User): Int {
    if (user.isPremium) return 20
    return 0
}

// Also idiomatic in production: an if expression
fun getDiscount(user: User): Int = if (user.isPremium) 20 else 0
```

### 3. Wrap All Primitives and Strings

For the exercise, wrap primitives to explore domain meaning. In production, introduce a value object when it prevents a realistic mix-up, owns validation, or gives behavior a useful home. Ordinary labels, counts, and simple parameters do not all need wrappers. Check serialization, Java interop, and persistence mappings before adopting `@JvmInline` value classes.

```kotlin
// Starting point: primitives can hide distinct domain concepts
fun createUser(email: String, age: Int) { /* ... */ }

// Value objects when validation or type safety earns the extra type
@JvmInline
value class Email private constructor(val value: String) {
    companion object {
        // Use the application's actual email validation policy.
        fun parse(value: String, isValid: (String) -> Boolean): Email? =
            if (isValid(value)) Email(value) else null
    }
}

@JvmInline
value class Age private constructor(val value: Int) {
    companion object {
        // The accepted range comes from the real domain contract.
        fun parse(value: Int, allowedRange: IntRange): Age? =
            if (value in allowedRange) Age(value) else null
    }
}

fun createUser(email: Email, age: Age) { /* ... */ }
```

### 4. First-Class Collections

The exercise asks any class with a collection to have no other instance variables. In production, an aggregate or UI state can correctly contain both collections and metadata. Extract a collection when it owns meaningful invariants or behavior, not because a list appears next to another property. The example assumes an existing `Money` type with addition and `ZERO`; it does not define a currency or rounding policy.

```kotlin
// Starting point: collection and aggregate metadata together
data class Order(
    val items: List<OrderItem>,
    val customerId: String,
    val total: Money,
)

// Exercise alternative: a collection with its own invariant or behavior
class OrderItems(items: List<OrderItem> = emptyList()) {
    private val items = items.toList()

    fun adding(item: OrderItem): OrderItems = OrderItems(items + item)
    fun total(): Money = items.fold(Money.ZERO) { sum, item -> sum + item.total }
    fun isEmpty(): Boolean = items.isEmpty()
}

class Order(
    private val items: OrderItems,
    private val customerId: CustomerId,
)
```

### 5. One Dot per Line (Law of Demeter)

Avoid coupling behavior to another object's internal collaborators. The one-dot rule is an exercise, not a Kotlin syntax limit: fluent collection/Flow chains, builders, and ordinary reads through immutable DTOs or UI state can be clear. Add a domain operation when it hides a real responsibility, not just to shorten a property path.

```kotlin
// Tight coupling when traversing another object's hidden collaborators
val city = order.customer.address.city

// A meaningful operation can hide that collaboration
val city = order.shippingCity()

// Fluent collection transformations are normal Kotlin
val activeNames = customers.filter { it.isActive }.map { it.name }
```

### 6. Don't Abbreviate

An awkwardly long name can indicate too many responsibilities, but length alone does not prove it. Prefer clear domain names; familiar project and platform abbreviations such as `UI`, `ID`, `URL`, and `ViewModel` do not need artificial expansion.

```kotlin
// BAD: Unclear abbreviations
val custRepo = CustRepo()
val ord = Ord()

// GOOD: Clear domain names
val customerRepository = CustomerRepository()
val order = Order()
```

### 7. Keep All Entities Small

Historical exercise targets:
- Classes: < 50 lines
- Methods: < 10 lines
- Files: < 100 lines

These are practice constraints, not production quotas. Review larger units for mixed responsibilities and difficult navigation; split when it improves comprehension. A cohesive composable, state model, test, or Android component can reasonably exceed these numbers. Follow existing repository tooling rather than introducing new size gates.

### 8. No Classes with More Than Two Instance Variables

For the exercise, this forces exploration of composition. In production, field count alone does not measure responsibility. A data class may describe several related values; a ViewModel may have several legitimate injected dependencies. Group them only when the new type has a real domain role, and avoid a dependency bag that hides coupling.

```kotlin
// Starting point for the exercise; these fields are not inherently wrong
data class Order(
    val id: String,
    val customerId: String,
    val items: List<Item>,
    val total: Money,
    val status: OrderStatus,
)

// Exercise alternative when the grouping reflects real responsibilities
class Order(
    private val id: OrderId,
    private val details: OrderDetails,
)

class OrderDetails(
    private val customer: Customer,
    private val lineItems: LineItems,
)
```

### 9. No Getters/Setters/Properties

For behavior-rich objects, prefer operations that own invariants: tell objects what to do. This is not a ban on Kotlin properties, immutable data classes, DTOs, UI state, or read-only state exposure. The example assumes an existing `Money` type and typed `WithdrawResult`; preserve actual account, concurrency, and persistence rules.

```kotlin
// BAD: Caller performs a balance invariant through public mutation
class Account(var balance: Money)

if (account.balance >= amount) {
    account.balance = account.balance - amount
}

// GOOD: Object owns the invariant
class Account(private var balance: Money) {
    fun withdraw(amount: Money): WithdrawResult {
        if (!canWithdraw(amount)) {
            return WithdrawResult.InsufficientFunds
        }
        balance -= amount
        return WithdrawResult.Success
    }

    private fun canWithdraw(amount: Money): Boolean =
        amount > Money.ZERO && balance >= amount
}

// Caller tells, object decides
val result = account.withdraw(amount)
```

---

## Comments

### When to Write Comments

**Prefer comments that explain WHY over comments that merely repeat WHAT the code does.**

Code should explain routine operations. Comments explain business reasons, non-obvious decisions, warnings, and concurrency assumptions. Public API KDoc, legal notices, protocol details, and a necessary explanation of a subtle algorithm are also useful; keep them accurate.

```kotlin
// BAD: Explains what (redundant)
// Add 1 to counter
counter++

// GOOD: Explains why
// Compensate for 0-based indexing in the legacy API.
counter++
```

### Prefer Self-Documenting Code

Instead of commenting, rename to make intent clear.

```kotlin
// BAD: Comment needed to name the policy
// Check if the user can access premium features.
if (user.subscriptionLevel >= 2 && !user.isBanned) {
    // ...
}

// GOOD: Self-documenting
if (user.canAccessPremiumFeatures()) {
    // ...
}
```

---

## Formatting

### Vertical Spacing
- Related code together
- Blank lines between concepts
- Most important/public at top

### Horizontal Spacing
- Consistent indentation
- Space around operators
- Use the repository's configured line length (often around 80-120 characters)

### Storytelling
Code should read top-to-bottom like a story. High-level at top, details below.

```kotlin
class OrderProcessor(
    private val orderRepository: OrderRepository,
) {
    // Public API first
    suspend fun process(order: Order): ProcessResult {
        validate(order)
        val pricedOrder = calculateTotals(order)
        return save(pricedOrder)
    }

    // Supporting methods below, in order of appearance
    private fun validate(order: Order) { /* domain validation */ }

    private fun calculateTotals(order: Order): Order {
        // Partial example: apply the existing pricing contract here.
        TODO("Use the application's pricing implementation")
    }

    private suspend fun save(order: Order): ProcessResult =
        orderRepository.save(order)
}
```

---

## Clean Code Checklist

### Naming
- [ ] Use **descriptive** and meaningful names
  - Variables & Properties: Nouns or short phrases with adjectives
  - Functions & Methods: Verbs or short phrases with adjectives
  - Classes: Nouns
- [ ] Be as **specific** as necessary and possible
- [ ] Use **yes/no "questions"** for booleans (e.g. `isValid`)
- [ ] Avoid **misleading** names
- [ ] Be **consistent** with names (e.g. stick to `get...` instead of `fetch...`)

### Comments & Formatting
- [ ] Remove redundant or stale comments; retain useful rationale and contract documentation
- [ ] Acceptable comments: legal info, warnings, regex explanations, todos
- [ ] Use **vertical formatting**: keep related concepts close, separate unrelated ones
- [ ] Write code **top to bottom**: called functions below calling functions
- [ ] Use **horizontal formatting**: avoid long lines, use indentation for scope

### Functions
- [ ] Review parameter complexity; use named arguments/defaults and group values when cohesive
- [ ] Functions should be **small and do one thing**
  - Aim for abstraction levels in the body **one level below** the function name
  - **Don't mix** levels of abstraction
  - But **avoid redundant splitting**!
- [ ] Stay **DRY** (Don't Repeat Yourself)
- [ ] **Avoid unexpected side effects**

### Control Structures & Errors
- [ ] Prefer **positive checks**
- [ ] Avoid **deep nesting**
  - Use **guard** statements and fail fast
  - Use **polymorphism** and factory functions
  - **Extract** control structures into separate functions
- [ ] Use a meaningful existing failure contract: typed outcomes or expected exceptions rather than undocumented numeric codes

### Objects & Classes
- [ ] Keep behavior ownership clear; use **objects** and **data containers** for their appropriate roles
- [ ] Build **small classes** focused on a **single responsibility** (not "single method"!)
- [ ] Build classes with **high cohesion**
- [ ] Review **Law of Demeter** coupling for behavior-rich objects; do not ban fluent APIs or immutable data access
- [ ] Follow the **SOLID principles** (especially SRP and OCP for clean code)


---

## Kotlin and Android Application Notes

### Nullability and Boundary Validation

Represent legitimate absence with nullable types. Avoid `!!`, unchecked casts, and empty defaults that conceal required missing data. Validate untrusted input at the boundary, then use a non-null local value or explicit outcome. Keep distinctions such as missing, empty, invalid, loading, and failed when the application contract distinguishes them.

Standalone Kotlin example; the positivity rule is illustrative and must match the real quantity contract:

```kotlin
sealed interface QuantityInput {
    data class Valid(val quantity: Int) : QuantityInput
    object Invalid : QuantityInput
}

fun parseQuantity(input: String): QuantityInput {
    val quantity = input.trim().toIntOrNull()
    return if (quantity != null && quantity > 0) {
        QuantityInput.Valid(quantity)
    } else {
        QuantityInput.Invalid
    }
}
```

Do not use defaults to silently substitute one identifier, price, status, or backend field for another. Preserve raw backend wording when the product contract requires it.

### State, Collections, and Immutability

Use `val` and value-oriented data classes for state. Keep mutation private and expose owned snapshots or read-only state through the existing architecture. Kotlin's `List` is read-only, not a guarantee that its backing collection or elements are immutable. `copy()` is shallow: mutating a nested collection can also change previously published state.

Replace changed collections rather than mutating published UI state in place. This helps Compose and other state observers see updates, but does not by itself make mutable elements safe. Model loading, data, and failures explicitly when needed; preserve whether the screen can display content and a recoverable error at the same time.

### Errors and Coroutine Cancellation

Use the existing error contract and map expected failures at an intentional boundary. Avoid catching every exception and presenting it as a network failure; programmer defects should remain diagnosable.

Catch specific expected exceptions when possible. If a broad catch around suspending work is necessary, rethrow `CancellationException` before mapping failures. `runCatching` also captures cancellation and needs the same care.

Standalone example; requires `kotlinx-coroutines-core` and JVM I/O:

```kotlin
import java.io.IOException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

class BlockingTextReader(
    private val ioDispatcher: CoroutineDispatcher,
    private val readBlocking: () -> String,
) {
    suspend fun readOrNull(): String? = withContext(ioDispatcher) {
        try {
            readBlocking()
        } catch (failure: IOException) {
            null
        }
    }
}
```

Here only an I/O failure maps to absence; cancellation and unexpected exceptions propagate. Use that mapping only if it matches the real contract. Dispatching blocking work to IO does not make it cooperatively cancellable; use the underlying API's cancellation support where available.

### Main-Safety and Structured Concurrency

A `suspend` function is not automatically off the main thread. Make APIs main-safe at the layer that performs blocking disk/network work or expensive CPU work, using an appropriate dispatcher supplied through the existing dependency seams. Already main-safe suspending APIs need no redundant dispatcher switch.

Let callers own completion through suspending functions and structured concurrency. Launch screen work in the existing ViewModel scope. Make longer-lived ownership explicit; persistent work across process loss needs a durable mechanism such as WorkManager when its scheduling semantics fit. Do not use `GlobalScope` to hide an ownership problem.

Use `Flow` for streams and `suspend` for one result. Expose read-only `StateFlow` where state is required, and make sharing, replay, and failure behavior deliberate. Choose debounce, `collectLatest`, retry, and buffering according to delivery semantics. Cancelling local work does not undo a server-side write. Long CPU loops may need explicit cancellation checks.

### Compose, Views, and Existing Architecture

For new UI work, follow the project's Compose conventions and existing state ownership. Keep composables focused on rendering state and reporting events; preserve meaningful defaults and explicit callbacks rather than changing the API to satisfy parameter quotas. Keep composition free of direct side effects and use effects with keys that reflect the actual operation's dependencies.

For an existing Views screen, fix the problem in place using its established lifecycle and binding patterns unless a UI migration is requested. Collect UI state with the project's lifecycle-aware mechanism; release view references with their owning lifecycle. Do not change navigation, DI frameworks, module boundaries, or architecture as incidental clean-code work.

Read [Architecture](architecture.md) for UI state collection and effects, and [Testing](testing.md) for cancellation and virtual-time checks.

### Resources, Accessibility, and Tooling

Use string resources for visible Android text and the existing locale-aware formatting utilities. Illustrative strings in this guide do not replace product resources. Preserve accessibility labels, content descriptions, RTL behavior, and backend/API contracts during refactors.

Follow the repository's formatter, lint, and static-analysis configuration. Keep targeted fixes scoped; avoid unrelated reformatting or adding new style gates. Review numeric quotas and object-calisthenics rules as learning tools, not reasons to change working architecture.

Further reading: [Android coroutine practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices), [Kotlin value classes](https://kotlinlang.org/docs/inline-classes.html).
