# Testing Strategy

## The Testing Pyramid

```
       /\
      /  \        E2E Tests (Few)
     /----\       - Full system
    /      \      - Slow, brittle
   /--------\
  /          \    Integration Tests (Some)
 /------------\   - Multiple components
/              \  - Medium speed
----------------
      Unit Tests (Many)
      - Single unit
      - Fast, isolated
```

Use the pyramid as a guide, not a fixed quota. Start with a concrete observable behavior and choose the smallest boundary that can prove it. Reuse the project's test runner and assertion libraries; add a dependency only for a concrete need.

## Test Types

### Unit Tests

Test ONE class or function in isolation.

**Characteristics:**
- Fast (milliseconds)
- No real external services (use real in-process collaborators or test doubles)
- Keep most business-rule feedback fast and local

Partial local JUnit 4 test. The app's `Order` accepts integer minor-unit prices through `addItem` and exposes `calculateTotal`; use its actual API and currency rules.

```kotlin
import org.junit.Assert.assertEquals
import org.junit.Test

class OrderTest {
    @Test
    fun calculatesTotalForTwoItems() {
        val order = Order()
        order.addItem(priceMinor = 100)
        order.addItem(priceMinor = 50)

        assertEquals(150, order.calculateTotal())
    }
}
```

### Integration Tests

Test multiple components together.

**Characteristics:**
- Slower (may use real DB)
- Test boundaries between components
- Fewer than unit tests

Partial Android integration test using JUnit 4, Room runtime, AndroidX Test core/ext, and kotlinx-coroutines-test. Assumes the app's `OrderDatabase`, `RoomOrderRepository`, and `OrderService` types and a suspend repository contract. Each test gets an isolated database.

```kotlin
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class OrderServiceIntegrationTest {
    private lateinit var database: OrderDatabase
    private lateinit var service: OrderService

    @Before
    fun setUp() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            OrderDatabase::class.java,
        ).build()
        service = OrderService(RoomOrderRepository(database.orderDao()))
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun savesAndRetrievesAnOrder() = runTest {
        val order = Order.create(customerId = "123")
        service.save(order)

        assertEquals(order, service.findById(order.id))
    }
}
```

### E2E / Acceptance Tests

Test the entire system from user perspective.

**Characteristics:**
- Slowest
- Most brittle (many moving parts)
- Test critical paths only

Partial instrumented Compose journey; requires Compose UI test JUnit 4 and AndroidX Test. The fixture launches the app with sandbox payments and controlled products; its definition and backend setup are project-specific. Text semantics shown must match the fixture's locale. Never use a real payment in an automated acceptance test.

```kotlin
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test

class CheckoutFlowTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<CheckoutTestActivity>()

    @Test
    fun userCanCompleteSandboxPurchase() {
        composeRule.onNodeWithText("Add to cart").performClick()
        composeRule.onNodeWithText("Checkout").performClick()
        composeRule.onNodeWithText("Pay with sandbox account").performClick()

        composeRule.onNodeWithText("Order confirmed").assertIsDisplayed()
    }
}
```

---

## Arrange-Act-Assert (AAA)

Use this structure to make each test's behavior clear:

Partial JUnit 4 example. The fixture's `Cart` contract gives a premium user a 20% discount; prices are integer minor units. This illustrates AAA, not an app-wide pricing rule.

```kotlin
import org.junit.Assert.assertEquals
import org.junit.Test

class CartTest {
    @Test
    fun applies20PercentDiscountToPremiumUsers() {
        // ARRANGE - Set up the test world
        val user = User(isPremium = true)
        val cart = Cart(user)
        cart.addItem(priceMinor = 100)

        // ACT - Execute the behavior under test
        val total = cart.calculateTotal()

        // ASSERT - Verify the expected outcome
        assertEquals(80, total)
    }
}
```

### Writing AAA Backwards

Sometimes easier to write in reverse:

1. **Assert first** - What do you want to verify?
2. **Act** - What action produces that result?
3. **Arrange** - What setup is needed?

---

## Test Naming

### Bad: Abstract, Technical

Partial naming examples: import `org.junit.Test`; each function would contain the scenario's setup and assertions inside a JUnit test class.

```kotlin
@Test fun shouldWorkCorrectly() { /* ... */ }
@Test fun handlesTheEdgeCase() { /* ... */ }
@Test fun setsTheDataProperty() { /* ... */ }
```

### Good: Concrete Examples, Domain Language

Partial naming examples; import `org.junit.Test` in the containing class.

```kotlin
@Test fun calculates20PercentDiscountForPremiumUsers() { /* ... */ }
@Test fun returnsErrorWhenCartIsEmpty() { /* ... */ }
@Test fun recognizesRacecarAsAPalindrome() { /* ... */ }
```

### Format

Partial naming alternatives using JUnit 4 (`org.junit.Test`); keep each concrete scenario's body in its test.

```kotlin
// Option 1: should + behavior
@Test fun shouldApplyTaxBasedOnShippingRegion() { /* ... */ }

// Option 2: when + then
@Test fun whenAdding2And3ThenReturns5() { /* ... */ }

// Option 3: Given-When-Then for a complex scenario
@Test fun givenPremiumUserWhenCheckingOutThenReceives20PercentDiscount() { /* ... */ }
```

---

## Test Doubles

### Dummy

Object passed but never used.

Partial Kotlin example. The existing `Logger` has one `log(String)` method and `UserService` accepts it as a constructor argument. No unchecked cast is needed for a dummy.

```kotlin
val dummyLogger = object : Logger {
    override fun log(message: String) = Unit
}
val service = UserService(realRepository, dummyLogger)
```

### Stub

Returns predefined values.

Partial Kotlin example. `UserRepository` declares the two suspend functions shown; `User` is an app model with `id` and `name`.

```kotlin
val stubRepository = object : UserRepository {
    override suspend fun findById(id: String): User? =
        User(id = id, name = "Test")
    override suspend fun save(user: User) = Unit
}
```

### Spy

Records how it was called.

Partial Kotlin spy. `ConfirmationSender` defines the suspend function shown. In a test running with one scheduler, assert the recorded recipients after the action completes.

```kotlin
class ConfirmationSpy : ConfirmationSender {
    val recipients = mutableListOf<String>()

    override suspend fun send(to: String, message: String) {
        recipients += to
    }
}

// Inside the test, after exercising the feature:
// assertTrue("user@example.com" in confirmationSpy.recipients)
// Import org.junit.Assert.assertTrue.
```

### Mock

Verifies expected interactions.

Partial MockK example inside `runTest`. Requires MockK and imports `io.mockk.mockk`, `io.mockk.coEvery`, and `io.mockk.coVerify`. The app's `CreateUserUseCase(repository).execute(expectedUser)` must persist the supplied user; `save` is suspend and `expectedUser` comes from the fixture. Verify this interaction when issuing exactly one persistence request is the contract.

```kotlin
val repository = mockk<UserRepository>()
coEvery { repository.save(any()) } returns Unit

val useCase = CreateUserUseCase(repository)
useCase.execute(expectedUser)

coVerify(exactly = 1) { repository.save(expectedUser) }
```

### Fake

Working implementation (simplified).

Partial Kotlin fake using the `UserRepository` and `User` contract above. This is suitable for single-scheduler tests; add synchronization only if the tested contract requires concurrent access.

```kotlin
class InMemoryUserRepository : UserRepository {
    private val users = mutableMapOf<String, User>()

    override suspend fun save(user: User) {
        users[user.id] = user
    }

    override suspend fun findById(id: String): User? = users[id]
}
```

---

## Testing Strategies by Layer

### Domain Layer (Most Business-Rule Tests)

- Unit tests with no mocks
- Test business rules, value objects, entities
- Fast, comprehensive

Partial local JUnit 4 tests. The feature's `Money` supports `plus`, value equality, `usd`/`eur` factories, and throws `CurrencyMismatch` for mixed currencies. The amounts below follow that fixture's factory contract.

```kotlin
import org.junit.Assert.assertEquals
import org.junit.Test

class MoneyTest {
    @Test
    fun addsAmountsWithSameCurrency() {
        val a = Money.usd(10)
        val b = Money.usd(20)
        assertEquals(Money.usd(30), a + b)
    }

    @Test(expected = CurrencyMismatch::class)
    fun rejectsAddingDifferentCurrencies() {
        Money.usd(10) + Money.eur(10)
    }
}
```

### Application Layer

- State and orchestration tests with controlled fakes or mocks
- Test use case orchestration

Partial test using JUnit 4 and kotlinx-coroutines-test. Assumes the feature's `CreateOrderUseCase`, in-memory order repository exposing `count`, and recording confirmation sender. The fixture `testItems()` supplies valid items from the app's contract.

```kotlin
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class CreateOrderUseCaseTest {
    @Test
    fun createsOrderAndSendsConfirmation() = runTest {
        val repository = InMemoryOrderRepository()
        val confirmation = ConfirmationSpy()
        val useCase = CreateOrderUseCase(repository, confirmation)

        useCase.execute(customerId = "123", items = testItems())

        assertEquals(1, repository.count())
        assertEquals(listOf("user@example.com"), confirmation.recipients)
    }
}
```

### Infrastructure Layer

- Integration tests with real dependencies
- Test Room queries, migrations, and HTTP client integration

Partial test method for the Room fixture shown under Integration Tests. Uses `kotlinx.coroutines.test.runTest`, `org.junit.Test`, and `org.junit.Assert.assertEquals`. The fixture creates/closes the database and constructs `repository` for each test.

```kotlin
@Test
fun persistsAndRetrievesOrder() = runTest {
    val order = Order.create(customerId = "123")
    repository.save(order)

    val found = repository.findById(order.id)
    assertEquals(order, found)
}
```

---

## High-Value Integration Tests

Focus integration tests on:

1. **Boundaries** - Where systems meet
2. **Critical paths** - Money, security, core features
3. **Complex queries** - Database operations

### Contract Tests

Verify implementations match the same behavioral contract, not merely the Kotlin interface's method signatures.

Partial shared JUnit 4 contract suite using kotlinx-coroutines-test and the `UserRepository`/`User` types above. Concrete subclasses provide a fresh repository for each test; the Room subclass sets up and closes its database with `@Before`/`@After` in supported Android test infrastructure.

```kotlin
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

abstract class UserRepositoryContract {
    protected abstract fun createRepository(): UserRepository

    @Test
    fun savesAndRetrievesUser() = runTest {
        val repository = createRepository()
        val user = User(id = "user-1", name = "Test")

        repository.save(user)

        assertEquals(user, repository.findById(user.id))
    }

    @Test
    fun returnsNullForMissingUser() = runTest {
        val repository = createRepository()
        assertNull(repository.findById("nonexistent"))
    }
}

class InMemoryUserRepositoryTest : UserRepositoryContract() {
    override fun createRepository(): UserRepository = InMemoryUserRepository()
}

// Apply the same inherited tests in RoomUserRepositoryTest.
// Its factory returns RoomUserRepository(database.userDao()).
```

---

## Test Builders

Create test objects easily.

Standalone Kotlin fixture example. Adapt the fields to actual domain invariants; defaults should construct a valid order without unchecked casts. Prices here use integer minor units.

```kotlin
data class Item(val sku: String, val priceMinor: Int)
enum class OrderStatus { PENDING, PAID }
data class Order(
    val id: String,
    val customerId: String,
    val items: List<Item>,
    val status: OrderStatus,
)

class OrderBuilder {
    private var id = "order-1"
    private var customerId = "cust-1"
    private var items = emptyList<Item>()
    private var status = OrderStatus.PENDING

    fun withId(value: String) = apply { id = value }
    fun withItems(value: List<Item>) = apply { items = value.toList() }
    fun paid() = apply { status = OrderStatus.PAID }

    fun build() = Order(id, customerId, items, status)
}

// Usage
val order = OrderBuilder()
    .withItems(listOf(Item(sku = "ABC", priceMinor = 100)))
    .paid()
    .build()
```

---

## Common Testing Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Testing implementation | Brittle tests | Test behavior only |
| Too many mocks | Tests prove nothing | Use real objects when possible |
| Shared state | Flaky tests | Isolate each test |
| No assertions | False confidence | Always assert something meaningful |
| Testing trivial code | Wasted effort | Focus on logic and edge cases |
| Slow tests | Reduced feedback | Optimize, use unit tests |
| Real delays/live services | Flaky, slow feedback | Control schedulers and external boundaries |
| Missing cleanup | Tests affect each other | Reset Main, cancel collectors, close databases/servers |

---

## Selecting an Android Test Environment

| Behavior | Useful verification |
| --- | --- |
| Pure Kotlin rules and transformations | Local JVM tests |
| Suspend functions, Flow, ViewModel state | Local tests with controlled coroutine execution |
| Repository/cache/network interaction | Controlled integration tests |
| Room queries and migrations | Database tests in the project's supported environment |
| Compose or Views interaction | Android UI tests using existing infrastructure |
| Restoration, Back stack, platform callbacks | Lifecycle/navigation tests and targeted device checks |
| Pixel parity, RTL, fonts, accessibility | Visual comparison and appropriate UI/accessibility checks |
| Jank, startup, memory | Measurements on representative devices |

Do not assume every Room or UI test can run on a plain JVM, or that a local test proves platform behavior.

## Coroutine execution

Use `runTest` and test dispatchers sharing one `TestCoroutineScheduler`. Inject dispatchers when production code owns execution on a dispatcher. Virtual time only controls work using that scheduler; it does not accelerate real network calls or hardcoded IO/Main dispatchers.

Standalone local test; requires JUnit 4, kotlinx-coroutines-core, and kotlinx-coroutines-test. The function models a delayed operation for demonstration.

```kotlin
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

suspend fun delayedLabel(): String {
    delay(1_000)
    return "Ready"
}

@OptIn(ExperimentalCoroutinesApi::class)
class DelayedLabelTest {
    @Test
    fun completesAtTheExpectedVirtualTime() = runTest {
        val result = async { delayedLabel() }
        runCurrent()
        advanceTimeBy(999)
        assertFalse(result.isCompleted)
        advanceTimeBy(1)
        runCurrent()
        assertEquals("Ready", result.await())
    }
}
```

`runCurrent` executes currently queued tasks. `advanceTimeBy` moves virtual time; work scheduled exactly at the target may need `runCurrent`. `advanceUntilIdle` drains scheduled work where termination is expected. Avoid sleep-based synchronization.

## Cancellation and errors

Test cancellation separately from a service failure. Start a genuinely suspended operation, cancel its owner, and verify cancellation is propagated rather than converted to success or user-facing failure. A controllable fake can signal entry and wait for release; this is more reliable than guessing a delay.

A coroutine cancelled by its parent may still end in a cancelled state even if a catch swallowed the exception. Assert the externally visible consequence too: no failure toast/state, no fallback success, and no unintended follow-up side effect.

Exercise genuine failure, cleanup, and retry after failure. Include duplicate submission or superseded requests where the feature's contract requires them. Cancelling a client coroutine does not prove a server write was rolled back.

## Flow and StateFlow

- For a finite stream, use `first`, `take(n)`, or bounded collection. Do not call unbounded `toList()` on a StateFlow.
- For StateFlow, assert `value` at controlled checkpoints. Conflation means collectors may skip intermediate values.
- When using `stateIn` with lazy or while-subscribed sharing, start a collector before expecting upstream changes.
- Put long-running collectors in `backgroundScope`, or cancel them explicitly.
- Establish a SharedFlow collector before emitting when replay is absent. Use Turbine if already present or justified; do not require it for every Flow test.

Partial test-body pattern, inside `runTest`. Assumes a `viewModel.uiState` StateFlow and a fake `repository` whose suspending `emitProducts` controls upstream data. Required imports: `kotlinx.coroutines.flow.collect`, `kotlinx.coroutines.launch`, `kotlinx.coroutines.test.UnconfinedTestDispatcher`, `kotlinx.coroutines.test.runCurrent`; opt in to ExperimentalCoroutinesApi.

```kotlin
backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
    viewModel.uiState.collect {}
}
runCurrent()
repository.emitProducts(emptyList())
runCurrent()
// Assert the public state expected by this feature's actual contract.
```

## ViewModel tests

Use constructor-injected fakes for data boundaries and test public state/actions. Cover initial state, success, failure, retry, and overlapping work as applicable.

For local tests using `viewModelScope`, replace Main with a test dispatcher **before** creating the ViewModel. Use the project's Main-dispatcher rule or equivalent setup, and reset Main in cleanup. Ensure every test dispatcher uses the same scheduler. Cancel outstanding owned work during teardown; the test scope cannot automatically manage every externally created scope.

For restoration, seed supported inputs into SavedStateHandle, recreate the state owner, and verify reload behavior. A unit test with a supplied handle does not prove navigation actually supplies those inputs after Android process recreation.

## Repository and integration tests

Read the existing source-of-truth and fallback contract first. Test it; do not invent "return cached data on every exception."

Useful cases include:

- Fresh response maps and persists correctly.
- Network failure with and without cached data follows the agreed policy.
- Cancellation is propagated without being stored as an error.
- Persistence failure and retry preserve the required state.
- Repeated or concurrent operations preserve ordering or deduplication where promised.

Use a fake network boundary for isolated repository logic. Use a local controlled HTTP server, such as MockWebServer when compatible with the project, for actual client request/response mapping. Avoid live backends in ordinary deterministic tests.

Use isolated Room databases in supported Android/Robolectric infrastructure. Exercise actual queries, transactions, and migrations where those are the risk; an in-memory DAO fake does not verify SQL or schema compatibility. Close databases and servers and reset state between tests.

## Compose, Views, and journeys

Test stateless Compose content with explicit state and callbacks using semantics-based assertions. Test loading, content, error, retry, disabled actions, and meaningful accessibility semantics. Avoid adding test tags where existing semantics identify the behavior.

For XML screens, use existing View test infrastructure and check binding lifetime through navigation away and view recreation. For flows, test Back/results and rapid repeated actions at the navigation boundary.

Keep a few critical journeys for end-to-end integration. Control test accounts, fixtures, and backend assumptions. Screenshot checks require controlled rendering conditions; previews alone do not establish pixel parity.

## Running and Reporting

Discover the actual module and variant tasks from the project; do not paste a guessed Gradle task. Start with focused checks and run required affected builds/lint/device checks. Broaden only when failures or integration risks warrant it.

Report the command/task, result, relevant variant/device, and blockers. Separate local JVM tests, assembly, instrumented tests, visual comparison, and live service checks. Record unrelated baseline failures rather than silently treating them as passing.

Sources: [Coroutine testing](https://developer.android.com/kotlin/coroutines/test), [Flow testing](https://developer.android.com/kotlin/flow/test).
