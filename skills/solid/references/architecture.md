# Software Architecture

## The Goal of Architecture

Enable the development team to:
1. **Add** features with minimal friction
2. **Change** existing features safely
3. **Remove** features cleanly
4. **Test** features in isolation
5. **Deploy** independently when possible (Android feature modules still normally ship in one app)

Start with the existing app: trace one action through UI, state owner, repository/data source, and back to rendering. Inspect dependency injection, navigation scope, source sets, and tests before changing boundaries. These styles are options for reasoning about code, not a mandate to migrate an established app.

## Architectural Principles

### 1. Vertical Boundaries (Features/Slices)

Organize by **feature**, not by technical layer.

```
BAD: Layer-first
src/
  presentation/
    UserViewModel.kt
    OrderViewModel.kt
  services/
    UserService.kt
    OrderService.kt
  repositories/
    UserRepository.kt
    OrderRepository.kt

GOOD: Feature-first
src/
  users/
    UserViewModel.kt
    UserService.kt
    UserRepository.kt
  orders/
    OrderViewModel.kt
    OrderService.kt
    OrderRepository.kt
```

**Why:** Changes to "users" feature stay in `users/`. High cohesion within features.

### 2. Horizontal Boundaries (Layers)

Separate concerns into layers with clear dependencies.

```
┌──────────────────────────────────────┐
│           Presentation               │  Compose, Views, ViewModels
├──────────────────────────────────────┤
│           Application                │  Use Cases, Orchestration
├──────────────────────────────────────┤
│             Domain                   │  Business Logic, Entities
├──────────────────────────────────────┤
│          Infrastructure              │  Room, HTTP, Platform APIs
└──────────────────────────────────────┘
```

### 3. The Dependency Rule

**Dependencies point INWARD.**

```
Infrastructure → Application → Domain
      ↓               ↓            ↓
   (outer)        (middle)      (inner)
```

- Inner layers know NOTHING about outer layers
- Domain has zero dependencies on infrastructure
- Use interfaces to invert dependencies

Partial Kotlin example. `User`, `UserId`, and `UserDao` are app-defined types; the DAO exposes the same suspend operations shown here. Constructor injection can be manual or use the project's existing DI framework.

```kotlin
// The inner boundary defines the interface.
interface UserRepository {
    suspend fun save(user: User)
    suspend fun findById(id: UserId): User?
}

// The outer implementation adapts persistence to the contract.
class RoomUserRepository(private val dao: UserDao) : UserRepository {
    override suspend fun save(user: User) = dao.save(user)
    override suspend fun findById(id: UserId): User? = dao.findById(id)
}

// Business logic depends on the abstraction.
class UserService(private val repository: UserRepository)
```

Keep pure domain rules independent of Android framework types. In an Android app, UI depends on a data layer, with an optional domain/use-case layer for complex or reused operations. This dependency rule does not require creating every layer or an interface for every class. Preserve established DI and module boundaries; add Gradle modules only when ownership, reuse, or dependency control justifies them.

### 4. Contracts

Interfaces define boundaries between components.

Partial Kotlin contract; `Money`, `PaymentToken`, `ChargeResult`, and `RefundResult` come from the feature's actual payment contract. Do not invent provider endpoints or handle raw card details in an example integration.

```kotlin
interface PaymentGateway {
    suspend fun charge(amount: Money, token: PaymentToken): ChargeResult
    suspend fun refund(chargeId: String): RefundResult
}

// Production adapters and a test fake implement the same contract:
// ProviderPaymentGateway, SandboxPaymentGateway, FakePaymentGateway.
```

### 5. Cross-Cutting Concerns

Concerns that span multiple features: logging, auth, validation, error handling.

**Options:**
- HTTP interceptors or repository decorators
- Shared validation and error mapping at explicit boundaries
- Lifecycle-aware observers for platform concerns
- Base classes (use sparingly)

Partial decorator example; uses `UserRepository`, `User`, and `UserId` above. The injected logger must be safe for the calling context. Log no personal data, credentials, or payment tokens.

```kotlin
class LoggingUserRepository(
    private val delegate: UserRepository,
    private val log: (String) -> Unit,
) : UserRepository by delegate {
    override suspend fun save(user: User) {
        log("Saving user")
        delegate.save(user)
        log("User saved")
    }
}
```

### 6. Conway's Law

> "Organizations design systems that mirror their communication structure."

**Implication:** Team structure affects architecture. Align both intentionally.

---

## Common Architectural Styles

### Layered Architecture

Traditional layers: Presentation → Business → Persistence

**Pros:** Simple, well-understood
**Cons:** Can become a "big ball of mud" without discipline

### Hexagonal Architecture (Ports & Adapters)

Domain at center, adapters around the edges.

```
        ┌─────────────────────┐
        │      UI Adapter     │
        └─────────┬───────────┘
                  │
┌─────────────────▼─────────────────┐
│              DOMAIN                │
│   ┌─────────────────────────┐     │
│   │      Business Logic      │     │
│   │      Use Cases           │     │
│   └─────────────────────────┘     │
└─────────────────┬─────────────────┘
                  │
        ┌─────────▼───────────┐
        │   Database Adapter   │
        └─────────────────────┘
```

**Ports:** Interfaces defined by the domain
**Adapters:** Implementations that connect to the outside world

### Clean Architecture

Similar to Hexagonal, with explicit layers:

1. **Entities** - Enterprise business rules
2. **Use Cases** - Application business rules
3. **Interface Adapters** - ViewModels, Presenters, Gateways
4. **Frameworks & Drivers** - Android, Room, External interfaces

---

## Feature-Driven Structure (UI)

For multi-module Android projects, organize feature UI by flow. Replace the feature, flow, package, and class placeholders with the actual project names.

```text
feature/<feature-name>/src/main/kotlin/<package>/
  <flow-name>/                         # List, details, search, etc.
    ui/
      FeatureScreen.kt
      components/                      # UI used only by this flow
    state/
      FeatureViewModel.kt
      FeatureUiState.kt
      FeatureUiEvent.kt
      FeatureSideEffect.kt
    navigation/
      FeatureNavigation.kt

  shared/                              # Shared across flows in this module
    ui/
    state/
    util/
```

- A flow groups its rendering, screen state/actions, and navigation. Keep components used only by that flow under its own `ui/components`.
- `FeatureScreen` renders state and forwards user input. `FeatureViewModel` owns screen business logic; `FeatureUiState` describes the screen snapshot and `FeatureUiEvent` models its user actions.
- `FeatureSideEffect` represents transient UI effects when the flow needs them. Define lifecycle and delivery behavior deliberately; important outcomes should remain recoverable through state.
- `FeatureNavigation` owns the flow's navigation integration and inputs/results.
- Promote code to the module's `shared` package when multiple flows actually use it. Keep flow-specific details within their flow; `shared` is not a default destination for new code.

Compose suits new UI in a compatible app; a targeted Fragment/XML fix should retain the existing stack. Create the components and state types the flow needs rather than empty files to satisfy the diagram.

---

## Feature-Driven Structure (Data and Domain)

Keep the corresponding domain contracts, data implementations, and dependency wiring in the data module.

```text
data/<feature-name>/src/main/kotlin/<package>/
  domain/
    model/
      Feature.kt                       # Domain models
    repository/
      FeatureRepository.kt             # Repository contract
    useCase/
      GetFeatureUseCase.kt             # Business operations

  data/
    repository/
      FeatureRepositoryImpl.kt
    remote/
      FeatureService.kt                # API service
      dto/
        FeatureDto.kt
    local/
      FeatureDatabase.kt
      FeatureDao.kt
      entity/
        FeatureEntity.kt
    mapper/
      FeatureMapper.kt                 # DTO/entity/domain conversions

  di/
    FeatureModule.kt                   # Dependency injection wiring
```

- Feature UI consumes domain models, repository contracts, or use cases from the corresponding data module. Keep transport DTOs, Room entities, and storage details behind those contracts.
- The `domain` package owns business policy and does not import its `data` implementations. The `data` package implements repository contracts and coordinates remote/local sources according to the actual data contract.
- Use `mapper` for conversions where representations differ. Keep business operations in `domain/useCase`; add use cases when the operation warrants them rather than wrapping every repository getter.
- Keep dependency wiring in `di/FeatureModule.kt` using the project's existing DI mechanism. The file name does not require adopting a particular framework.
- Add remote or local infrastructure only when the feature uses it. The layout defines where responsibilities belong, not a requirement to add a database or API to every feature.

The feature module depends on its data module; the data module must not depend on feature UI. Expose a deliberate module API. Kotlin's `internal` visibility is module-wide, not package-private, so the `domain` and `data` package boundary within one module still requires dependency discipline.

This is the multi-module layout. For an existing project with a different structure or a single-module app, preserve its conventions unless restructuring is part of the requested work.

---

## The Walking Skeleton

Start with a minimal end-to-end slice:

1. **Thinnest possible feature** that touches all layers
2. **Installable and runnable** from day one
3. **Proves the architecture** works

Example walking skeleton for e-commerce:
- User can view ONE product (hardcoded)
- User can add it to cart
- User can "checkout" in a controlled demo (no real charge)

From there, flesh out each feature fully.

---

## Testing Architecture

```
┌────────────────────────────────────────────┐
│            E2E / Acceptance Tests          │  Few, slow, high confidence
├────────────────────────────────────────────┤
│            Integration Tests               │  Some, medium speed
├────────────────────────────────────────────┤
│              Unit Tests                    │  Many, fast, isolated
└────────────────────────────────────────────┘
```

**Test by layer:**
- **Domain:** Fast unit tests for business rules
- **Application/ViewModel:** State and orchestration tests with controlled fakes
- **Infrastructure:** Integration tests with actual Room queries or controlled HTTP
- **E2E:** Critical paths only

Use the testing pyramid as a guide, not a fixed quota. Test behavior at the smallest boundary that can prove it; see [Testing Strategy](testing.md).

---

## Architecture Decision Records (ADRs)

Document significant decisions:

```markdown
# ADR 001: Use Room for local persistence

## Status
Accepted

## Context
We need structured local persistence. Options: Room, direct SQLite, file storage

## Decision
Room for:
- Compile-time query checks
- Team familiarity
- Integration with Kotlin Flow

## Consequences
- Need Room and SQLite expertise
- Schema migrations required
- Queries and migrations need integration tests
```

---

## Red Flags in Architecture

- **Circular dependencies** between modules
- **Domain depending on infrastructure**
- **Framework code in business logic**
- **No clear boundaries** between features
- **Shared mutable state** across modules
- **"Util" or "Common" packages** that grow forever
- **Database schema driving domain model**

---

## Screen state and actions

Prefer unidirectional data flow: state goes down, actions go up. Composables and Views render state and report input; ViewModels own screen business state and actions. Keep Activity, View, binding, and NavController references out of ViewModels. A plain state holder can coordinate reusable UI behavior without owning screen business logic. Repositories coordinate sources of truth; data sources handle transport, persistence, and platform APIs without making UI or navigation decisions.

Expose immutable state through a read-only API. Keep transitions under one owner. A data class can represent content with loading/error flags if those states coexist; sealed types fit mutually exclusive alternatives.

Partial ViewModel example. Imports and declarations shown require AndroidX Lifecycle ViewModel KTX and kotlinx-coroutines-core. The repository's contract is main-safe; refresh either succeeds, throws IOException for an expected network failure, or propagates cancellation. The real app must define any other expected failures.

```kotlin
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import java.io.IOException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

interface RefreshRepository {
    suspend fun refresh()
}

data class RefreshUiState(
    val isRefreshing: Boolean = false,
    val hasRefreshError: Boolean = false,
)

class RefreshViewModel(
    private val repository: RefreshRepository,
) : ViewModel() {
    private val mutableState = MutableStateFlow(RefreshUiState())
    val uiState = mutableState.asStateFlow()

    // Called on Main by the UI; suppress duplicate in-flight refresh actions.
    fun refresh() {
        if (mutableState.value.isRefreshing) return
        mutableState.update { it.copy(isRefreshing = true, hasRefreshError = false) }
        viewModelScope.launch {
            try {
                repository.refresh()
            } catch (failure: IOException) {
                mutableState.update { it.copy(hasRefreshError = true) }
            } finally {
                mutableState.update { it.copy(isRefreshing = false) }
            }
        }
    }
}
```

Cancellation is not a refresh error. A screen leaving composition does not necessarily clear its ViewModel: inspect destination/graph scope and the actual job owner before changing cancellation policy.

## Compose state and effects

Collect screen state with `collectAsStateWithLifecycle`. Pass data and callbacks to stateless content; keep DI and navigation wiring at the screen boundary.

Partial UI example using the ViewModel above; requires Compose runtime, Material 3, and lifecycle-runtime-compose. The host obtains the correctly scoped ViewModel through the project's factory/DI. Add a localized error treatment in the real screen.

```kotlin
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun RefreshRoute(viewModel: RefreshViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    RefreshContent(state = state, onRefresh = viewModel::refresh)
}

@Composable
fun RefreshContent(state: RefreshUiState, onRefresh: () -> Unit) {
    Button(onClick = onRefresh, enabled = !state.isRefreshing) {
        Text(if (state.isRefreshing) "Refreshing" else "Refresh")
    }
}
```

The literals illustrate rendering only; use string resources in an app.

- Hoist state to the lowest owner that needs to coordinate it. Keep ephemeral UI state local; use a ViewModel for screen business state.
- `remember` survives recomposition, not recreation. Use `rememberSaveable` for small saveable UI values, and explicit persistence for durable data.
- Perform side effects through event callbacks or effect APIs, not the composable body.
- `LaunchedEffect` is composition-bound, not a guarantee of visible-screen lifetime. Choose keys from values that should restart the work. Use `rememberUpdatedState` for a changing value that should not restart an effect.
- Use `DisposableEffect` to register and clean up listeners tied to its keys. Use a remembered coroutine scope for UI actions whose work should end when that composition leaves.
- Do not add stability annotations or memoization without checking correctness and measuring the actual performance problem.

## Existing XML, Views, and Fragments

A Fragment's view can be destroyed while the Fragment still exists. Collect state using the **view** lifecycle.

Partial Fragment method; assumes an existing `viewModel` with `uiState` and `render` updating current ViewBinding. Required imports are shown; this belongs inside the existing Fragment.

```kotlin
import android.os.Bundle
import android.view.View
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
    super.onViewCreated(view, savedInstanceState)
    viewLifecycleOwner.lifecycleScope.launch {
        viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            viewModel.uiState.collect { state -> render(state) }
        }
    }
}
```

Clear the binding reference in `onDestroyView` using the project's binding pattern. Avoid capturing a destroyed binding in callbacks. Collect multiple never-ending flows in separate child coroutines inside the repeat block so the first collector does not block the others. Check collector registration across view recreation.

## Navigation, effects, and restoration

Keep navigation decisions at a deliberate screen/host boundary. Preserve the existing navigation library and back-stack semantics. Trace producers, destinations, argument types, result consumers, and duplicate-action timing together.

For new work, model important action outcomes as state that can survive collector absence. Do not assume a Channel or SharedFlow guarantees exactly-once delivery through recreation. For existing effects, preserve the agreed contract and test loss/replay behavior before redesigning it.

Scope each ViewModel intentionally: destination, graph, or activity. Use SavedStateHandle for small supported restoration values and IDs; reload authoritative data from repositories. Neither ViewModel nor in-memory Flow survives process death. Saved state is not durable storage for critical transactions.

Pass minimal navigation inputs. Avoid placing secrets or large object graphs in routes. Restore only data supported by the project's navigation and serialization contracts.

## Android Verification

Test state transitions and error/retry paths locally. Check view recreation, navigation Back/results, repeated taps, and restore behavior at the appropriate Android test level. A successful build does not establish visual parity, process-death recovery, or live API behavior.

Sources: [Architecture recommendations](https://developer.android.com/topic/architecture/recommendations), [Lifecycle-aware coroutines](https://developer.android.com/topic/libraries/architecture/coroutines), [Compose side effects](https://developer.android.com/develop/ui/compose/side-effects).
