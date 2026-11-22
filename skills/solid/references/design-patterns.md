# Design Patterns

## What Are Design Patterns?

Reusable solutions to common design problems. A shared vocabulary for discussing design.

## WARNING: Don't Force Patterns

> "Let patterns emerge from refactoring, don't force them upfront."

Patterns should solve problems you HAVE, not problems you MIGHT have.

Kotlin often provides the useful part through functions, default arguments, data classes, or delegation. Start with those when they express the problem clearly.

Examples are independent unless they explicitly refer to an earlier snippet. Partial examples name the application types, dependencies, or omitted work they require.

## When to Use Patterns

1. **You recognize the problem** - You've seen it before
2. **The pattern fits** - Not forcing it
3. **It simplifies** - Doesn't add unnecessary complexity
4. **Team understands it** - Shared knowledge

---

## Creational Patterns

### Singleton

**Purpose:** Ensure only one instance exists.

**When to use:** Global configuration, connection pools, logging.

**Warning:** Often overused. Consider dependency injection instead.

Standalone Kotlin demonstration; `println` stands in for a logging backend:

```kotlin
object Logger {
    fun log(message: String) {
        println(message)
    }
}

// Usage
fun logStartup() {
    Logger.log("Started")
}
```

Kotlin `object` supplies one instance without a manual `getInstance()`. It does not make mutable members thread-safe. In Android, prefer explicit DI scopes for stateful services and never retain an Activity, View, or other short-lived UI owner in an application-wide object.

### Factory

**Purpose:** Create objects without specifying exact class.

**When to use:** Object creation logic is complex, or varies by type.

Standalone Kotlin demonstration; printing represents each delivery mechanism:

```kotlin
interface Notification {
    fun send(message: String)
}

class EmailNotification : Notification {
    override fun send(message: String) = println("Email: $message")
}

class SmsNotification : Notification {
    override fun send(message: String) = println("SMS: $message")
}

class PushNotification : Notification {
    override fun send(message: String) = println("Push: $message")
}

enum class NotificationType { EMAIL, SMS, PUSH }

class NotificationFactory {
    fun create(type: NotificationType): Notification = when (type) {
        NotificationType.EMAIL -> EmailNotification()
        NotificationType.SMS -> SmsNotification()
        NotificationType.PUSH -> PushNotification()
    }
}
```

A factory can also be a function. Keep a class when it owns meaningful creation dependencies or policy. For ViewModels, reuse the project's existing factory or DI integration so creation respects the correct owner and saved-state contract.

### Builder

**Purpose:** Construct complex objects step by step.

**When to use:** Objects with many optional parameters, test data creation.

Standalone Kotlin demonstration:

```kotlin
data class User(
    val name: String,
    val email: String,
    val age: Int? = null,
)

class UserBuilder {
    private var name: String? = null
    private var email: String? = null
    private var age: Int? = null

    fun withName(name: String) = apply { this.name = name }
    fun withEmail(email: String) = apply { this.email = email }
    fun withAge(age: Int) = apply { this.age = age }

    fun build(): User = User(
        name = requireNotNull(name) { "Name is required" },
        email = requireNotNull(email) { "Email is required" },
        age = age,
    )
}

// Usage
val user = UserBuilder()
    .withName("Alice")
    .withEmail("alice@example.com")
    .build()
```

For this small value, named and default arguments are simpler:

```kotlin
// Uses User from the preceding example.
val alice = User(name = "Alice", email = "alice@example.com")
```

Use a builder when staged construction or a complex fixture makes it clearer, rather than requiring one for every data class. Validation should follow the actual domain contract.

### Prototype

**Purpose:** Create new objects by cloning existing ones.

**When to use:** Object creation is expensive, or you need copies with slight variations.

Standalone Kotlin demonstration:

```kotlin
interface Prototype<T> {
    fun clone(): T
}

data class Metadata(val tags: MutableList<String>)

data class Document(
    val title: String,
    val content: String,
    val metadata: Metadata,
) : Prototype<Document> {
    override fun clone(): Document = copy(
        metadata = metadata.copy(tags = metadata.tags.toMutableList()),
    )
}
```

A data class already supplies `copy(title = "New title")`. That copy is shallow: nested mutable objects remain shared unless explicitly copied, as the tags are above. Prefer immutable snapshots when possible; do not assume `copy()` makes mutable UI state independent.

---

## Structural Patterns

### Adapter

**Purpose:** Make incompatible interfaces work together.

**When to use:** Integrating third-party libraries, legacy code.

Partial Kotlin example. `OldPaymentApi` represents an existing SDK with `makePayment(cents: Long): Boolean`; the application's `Money.toCents()` and `ChargeResult.success()/failed()` supply the conversion and result contract.

```kotlin
// Our interface
interface PaymentGateway {
    fun charge(amount: Money): ChargeResult
}

// Adapter
class OldPaymentAdapter(
    private val oldApi: OldPaymentApi,
) : PaymentGateway {
    override fun charge(amount: Money): ChargeResult {
        val cents = amount.toCents()
        val success = oldApi.makePayment(cents)
        return if (success) ChargeResult.success() else ChargeResult.failed()
    }
}
```

A real adapter must preserve currency units, rounding, error semantics, and the SDK's threading contract. For Android callbacks, also handle cancellation and unregister listeners when their owner ends. Keep permission prompts and rendering outside a data adapter.

### Decorator

**Purpose:** Add behavior to objects dynamically.

**When to use:** Adding features without modifying existing code.

Standalone Kotlin demonstration; printing represents delivery:

```kotlin
interface Notifier {
    fun send(message: String)
}

class EmailNotifier : Notifier {
    override fun send(message: String) {
        println("Email: $message")
    }
}

// Decorators
class SmsDecorator(private val wrapped: Notifier) : Notifier {
    override fun send(message: String) {
        wrapped.send(message)
        println("SMS: $message")
    }
}

class SlackDecorator(private val wrapped: Notifier) : Notifier {
    override fun send(message: String) {
        wrapped.send(message)
        println("Slack: $message")
    }
}

// Usage - compose behaviors
fun sendAlert() {
    val notifier = SlackDecorator(
        SmsDecorator(
            EmailNotifier(),
        ),
    )
    notifier.send("Alert!") // Sends to all three
}
```

Kotlin interface delegation (`class Wrapper(private val wrapped: Notifier) : Notifier by wrapped`) can forward unchanged members while you override selected behavior. It helps when an interface has several operations; it adds little to this one-method example. Preserve error and delivery semantics when composing real notification channels.

### Proxy

**Purpose:** Control access to an object.

**When to use:** Lazy loading, access control, logging, caching.

Partial Kotlin example; the disk loading and rendering bodies are application-specific and omitted:

```kotlin
interface Image {
    fun display()
}

class RealImage(private val filename: String) : Image {
    init {
        loadFromDisk() // Expensive
    }

    private fun loadFromDisk() {
        // Load the image identified by filename.
    }

    override fun display() {
        // Render the loaded image.
    }
}

// Lazy loading proxy
class ImageProxy(private val filename: String) : Image {
    private val realImage: RealImage by lazy { RealImage(filename) }

    override fun display() {
        realImage.display()
    }
}
```

The lazy property initializes on first access, on the caller's thread. It does not move disk work off Android's main thread. Prefer the project's existing image loader for UI images. Caching proxies also need an explicit freshness and failure contract; adding a cache can change observable behavior.

### Composite

**Purpose:** Treat individual objects and compositions uniformly.

**When to use:** Tree structures, hierarchies (files/folders, UI components).

Standalone Kotlin demonstration; integer prices are illustrative units:

```kotlin
interface Component {
    fun getPrice(): Int
}

class Product(private val price: Int) : Component {
    override fun getPrice(): Int = price
}

class Box : Component {
    private val children = mutableListOf<Component>()

    fun add(component: Component) {
        children.add(component)
    }

    override fun getPrice(): Int = children.sumOf { it.getPrice() }
}

// Usage
fun printBoxPrice() {
    val smallBox = Box()
    smallBox.add(Product(10))
    smallBox.add(Product(20))

    val bigBox = Box()
    bigBox.add(smallBox)
    bigBox.add(Product(50))

    println(bigBox.getPrice()) // 80
}
```

Compose already supports composing UI from smaller functions. Do not introduce a parallel object tree solely to make composables fit this pattern.

---

## Behavioral Patterns

### Strategy

**Purpose:** Define a family of algorithms, make them interchangeable.

**When to use:** Multiple ways to do something, switchable at runtime.

Standalone Kotlin demonstration. Floating-point prices keep the example small; production money calculations must use the application's established precision and rounding rules.

```kotlin
interface PricingStrategy {
    fun calculate(basePrice: Double): Double
}

class RegularPricing : PricingStrategy {
    override fun calculate(basePrice: Double): Double = basePrice
}

class PremiumDiscount : PricingStrategy {
    override fun calculate(basePrice: Double): Double =
        basePrice * 0.8 // 20% off
}

class BlackFriday : PricingStrategy {
    override fun calculate(basePrice: Double): Double =
        basePrice * 0.5 // 50% off
}

data class Item(val price: Double)

class ShoppingCart(private val pricing: PricingStrategy) {
    fun calculateTotal(items: List<Item>): Double {
        val base = items.sumOf { it.price }
        return pricing.calculate(base)
    }
}
```

A Kotlin function parameter can express a single-operation strategy without a hierarchy:

```kotlin
// Uses Item from the preceding example.
fun calculateTotal(
    items: List<Item>,
    pricing: (Double) -> Double = { it },
): Double = pricing(items.sumOf { it.price })

fun discountedTotal(items: List<Item>): Double =
    calculateTotal(items) { base -> base * 0.8 }
```

Keep the interface when policies have meaningful state, configuration, or several related operations.

### Observer

**Purpose:** Notify multiple objects about state changes.

**When to use:** Event systems, pub/sub, reactive updates.

Partial Kotlin example; order processing is omitted and the caller provides the email delivery function. The emitter is confined to one owner/thread; it is not a concurrent event bus.

```kotlin
data class Order(val id: String)

sealed interface OrderEvent {
    data class OrderPlaced(val order: Order) : OrderEvent
}

fun interface Observer {
    fun update(event: OrderEvent)
}

open class EventEmitter {
    private val observers = mutableListOf<Observer>()

    fun subscribe(observer: Observer) {
        observers.add(observer)
    }

    fun unsubscribe(observer: Observer) {
        observers.removeAll { it === observer }
    }

    protected fun notify(event: OrderEvent) {
        // Snapshot permits subscription changes during notification.
        observers.toList().forEach { it.update(event) }
    }
}

// Usage
class OrderService : EventEmitter() {
    fun placeOrder(order: Order) {
        // Process order...
        notify(OrderEvent.OrderPlaced(order))
    }
}

class EmailService(
    private val sendConfirmation: (Order) -> Unit,
) : Observer {
    override fun update(event: OrderEvent) {
        when (event) {
            is OrderEvent.OrderPlaced -> sendConfirmation(event.order)
        }
    }
}
```

The owner that subscribes must unsubscribe when observation ends. A global emitter retaining a screen observer can leak that screen. Essential order side effects also need a real failure/retry contract; an in-memory notification alone does not guarantee delivery.

On Android, Flow is often the existing observation mechanism. This partial example depends on `kotlinx-coroutines`, AndroidX ViewModel with `viewModelScope`, `lifecycle-runtime-compose`, Compose, and `Order` above. The application supplies `OrderRepository.observeOrders(): Flow<List<Order>>` and `OrdersContent`.

```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn

sealed interface OrdersState {
    data object Loading : OrdersState
    data class Ready(val orders: List<Order>) : OrdersState
}

class OrdersViewModel(repository: OrderRepository) : ViewModel() {
    val state: StateFlow<OrdersState> = repository.observeOrders()
        .map<List<Order>, OrdersState> { OrdersState.Ready(it) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = OrdersState.Loading,
        )
}

@Composable
fun OrdersRoute(viewModel: OrdersViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    OrdersContent(state)
}
```

The ViewModel owns sharing and its scope cancels when it is cleared; lifecycle-aware collection stops collecting while the UI is below its active lifecycle state. In this example, upstream work stops five seconds after the last subscriber disappears. Choose that policy from the real workload. The repository must cooperate with cancellation and implement the application's error contract; error rendering is omitted here.

StateFlow represents current state and conflates equal values. SharedFlow can distribute events, but replay and buffers do not provide durable exactly-once delivery. Model important outcomes according to the existing contract, especially when collectors can be absent.

### Template Method

**Purpose:** Define algorithm skeleton, let subclasses override steps.

**When to use:** Common algorithm with varying steps.

Partial Kotlin example. `Data.toCsv()` is an application-provided formatter; the JSON encoder and output functions are injected. Validation and completion reporting bodies are omitted.

```kotlin
abstract class DataExporter {
    // Template method - defines the algorithm; final by default.
    fun export(data: List<Data>) {
        validate(data)
        val formatted = format(data)
        write(formatted)
        notifyCompletion()
    }

    // Common steps
    private fun validate(data: List<Data>) {
        // Application validation.
    }

    private fun notifyCompletion() {
        // Application completion reporting.
    }

    // Steps to override
    protected abstract fun format(data: List<Data>): String
    protected abstract fun write(content: String)
}

class CsvExporter(
    private val writeContent: (String) -> Unit,
) : DataExporter() {
    override fun format(data: List<Data>): String =
        data.joinToString("\n") { it.toCsv() }

    override fun write(content: String) {
        writeContent(content)
    }
}

class JsonExporter(
    private val encodeJson: (List<Data>) -> String,
    private val writeContent: (String) -> Unit,
) : DataExporter() {
    override fun format(data: List<Data>): String = encodeJson(data)

    override fun write(content: String) {
        writeContent(content)
    }
}
```

Function parameters and composition can express varying steps without inheritance. Keep the template when the common algorithm and subclass contract are stable. In Android, output functions must respect threading and storage/URI permissions; this synchronous teaching example is not a main-thread export implementation.

### Command

**Purpose:** Encapsulate a request as an object.

**When to use:** Undo/redo, queuing, logging actions.

Partial Kotlin example; the application supplies `Cart.add(Item)`, `Cart.remove(Item)`, and `Item`. It assumes removal reverses this specific addition; production cart identities, duplicate items, and failures need their actual contract.

```kotlin
interface Command {
    fun execute()
    fun undo()
}

class AddItemCommand(
    private val cart: Cart,
    private val item: Item,
) : Command {
    override fun execute() {
        cart.add(item)
    }

    override fun undo() {
        cart.remove(item)
    }
}

class CommandHistory {
    private val history = mutableListOf<Command>()

    fun execute(command: Command) {
        command.execute()
        history.add(command)
    }

    fun undo() {
        val command = history.lastOrNull() ?: return
        command.undo()
        history.removeAt(history.lastIndex)
    }
}
```

A callback is sufficient for many Compose UI actions. A command object earns its place when identity, state, history, or queuing matters. An undo method does not itself reverse a completed server request, and a local queue does not establish server idempotency.

---

## Pattern Awareness

### The Four-Dimensional Lens

When analyzing new code/libraries, ask:

1. **What problem does it solve?** (Creational, Structural, Behavioral)
2. **What scope?** (Object-level, Class-level, System-level)
3. **When is it applied?** (Compile-time, Runtime)
4. **How coupled?** (Tight, Loose)

This helps recognize patterns even in unfamiliar code.

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **God Object** | Class does everything | Split by responsibility |
| **Spaghetti Code** | Tangled, no structure | Clarify boundaries and control flow |
| **Golden Hammer** | Using one pattern for everything | Match pattern to problem |
| **Premature Optimization** | Optimizing before needed | YAGNI, profile first |
| **Copy-Paste Programming** | Duplicated knowledge drifts | Extract a shared concept when evidence supports it; Rule of Three is a heuristic |
