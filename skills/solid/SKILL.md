---
name: solid
description: Use when writing, refactoring, planning, reviewing, testing, or debugging Kotlin and Android code, including coroutines, Flow, ViewModels, Jetpack Compose, and existing XML or Views screens.
---

# Solid Skills: Professional Kotlin and Android Engineering

You are now operating as a senior software engineer. Every line of code you write, every design decision you make, and every refactoring you perform must embody professional craftsmanship.

## When This Skill Applies

**Use this skill for Kotlin and Android work when:**
- Writing code (features, fixes, utilities)
- Refactoring existing code
- Planning or designing architecture
- Reviewing code quality
- Debugging issues
- Creating tests
- Making design decisions

## Core Philosophy

> "Code is to create products for users & customers. Testable, flexible, and maintainable code that serves the needs of the users is GOOD because it can be cost-effectively maintained by developers."

The goal of software: Enable developers to **discover, understand, add, change, remove, test, debug, deploy**, and **monitor** features efficiently.

## The Engineering Process

### 1. Start with Behavior and Tests (TDD)

**Prefer Red-Green-Refactor for new logic and bug fixes:**

```
1. RED    - Write a failing test that describes the behavior
2. GREEN  - Write the SIMPLEST code to make it pass
3. REFACTOR - Clean up, remove duplication when a useful boundary emerges
```

**The Three Laws of TDD (when working test-first):**
1. Write a failing behavioral test before implementing the behavior
2. Write only enough test code to demonstrate the failure
3. Write only enough production code to satisfy the behavior

Use existing coverage for behavior-preserving refactors; add characterization tests where confidence is missing. Documentation and formatting edits need no artificial tests. For bugs, reproduce the failure and add a regression test where practical.

**Use REFACTORING to refine the design as behavior becomes clear.**

See: [references/tdd.md](references/tdd.md)

### 2. Apply SOLID Principles with Judgment

For the responsibilities and boundaries affected by the change:

| Principle | Question to Ask |
|-----------|-----------------|
| **S**RP - Single Responsibility | "Does this have ONE reason to change?" |
| **O**CP - Open/Closed | "Can I extend without modifying?" |
| **L**SP - Liskov Substitution | "Can subtypes replace base types safely?" |
| **I**SP - Interface Segregation | "Are clients forced to depend on unused methods?" |
| **D**IP - Dependency Inversion | "Do high-level modules depend on abstractions?" |

See: [references/solid-principles.md](references/solid-principles.md)

### 3. Write Clean, Human-Readable Code

**Naming (in order of priority):**
1. **Consistency** - Same concept = same name everywhere
2. **Understandability** - Domain language, not technical jargon
3. **Specificity** - Precise, not vague (avoid `data`, `info`, `manager`)
4. **Brevity** - Short but not cryptic
5. **Searchability** - Unique, greppable names

**Functions:**
- Make parameters clear; use named/default arguments and cohesive parameter objects where useful. Stateless composables may legitimately have several callbacks.
- Keep functions small and focused on one thing
- All operations at the same level of abstraction, one level below the function name
- Don't mix abstraction levels in a single function
- Split reasonably - avoid redundant extractions
- Avoid unexpected side effects (function name must imply all effects)

**Control Structures:**
- Prefer positive checks (`isEmpty(x)` over `!hasContent(x)`)
- Avoid deep nesting - use guards and fail fast
- Extract nested control structures into separate functions
- Use polymorphism or functions when behavior varies; keep readable exhaustive `when` expressions for sealed types
- Use the project's typed outcomes or exception contracts; preserve coroutine cancellation when handling failures

**Structure:**
- Reduce unnecessary nesting without fragmenting a readable operation
- Use guard clauses or idiomatic `if`/`when` expressions according to readability
- Validate nullable and untrusted input at boundaries; use Kotlin map membership and typed parsing rather than unchecked casts
- Wrap domain values when type safety or shared invariants justify it, such as distinct product and cart-line IDs
- Encapsulate collections when they enforce rules; ordinary Kotlin collections are often sufficient
- Avoid reaching into collaborators' internals; readable Kotlin chains and immutable data access are valid
- Keep entities cohesive; use responsibility and readability rather than fixed line limits
- Give state a clear owner; data classes and ViewModels may need several properties
- Distinguish between **objects** that protect invariants and **data containers** that expose snapshots; data classes may also provide meaningful behavior

**Value Objects are useful when they protect a real distinction:**

```kotlin
// Distinct types prevent mixing identifiers at a boundary.
@JvmInline value class ProductId(val value: String)
@JvmInline value class CartLineId(val value: String)

// Partial signatures; bodies belong to the application.
interface CartActions {
    suspend fun addProduct(productId: ProductId)
    suspend fun changeQuantity(cartLineId: CartLineId, quantity: Int)
}

// A local loop counter or a simple display string needs no wrapper.
```

See: [references/clean-code.md](references/clean-code.md)

### 4. Design with Responsibility in Mind

**Ask these questions for every class:**
1. "What responsibility does this have?" (Entity, ViewModel, Repository, Factory, pure function, etc.)
2. "Is it doing too much?" (Look for unrelated reasons to change)

**Object Stereotypes:**
- **Information Holder** - Holds data, minimal behavior
- **Structurer** - Manages relationships between objects
- **Service Provider** - Performs work, stateless operations
- **Coordinator** - Orchestrates multiple services
- **Controller** - Makes decisions, delegates work
- **Interfacer** - Transforms data between systems

See: [references/object-design.md](references/object-design.md)

### 5. Manage Complexity Ruthlessly

**Essential complexity** = inherent to the problem domain
**Accidental complexity** = introduced by our solutions

**Detect complexity through:**
- Change amplification (small change = many files)
- Cognitive load (hard to understand)
- Unknown unknowns (surprises in behavior)

**Fight complexity with:**
- YAGNI - Don't build what you don't need NOW
- KISS - Simplest solution that works
- DRY - Share repeated knowledge when it changes together; Rule of Three is a heuristic, not a gate

See: [references/complexity.md](references/complexity.md)

### 6. Architect for Change

**Vertical Slicing:**
- Features as end-to-end slices
- Keep related UI, state, and data responsibilities discoverable within feature boundaries

**Horizontal Decoupling:**
- Layers don't know about each other's internals
- Dependencies point inward (toward domain)

**The Dependency Rule:**
- Source code dependencies point toward high-level policies
- Infrastructure depends on domain policy, never reverse; add a separate domain layer only when complexity or reuse warrants it

See: [references/architecture.md](references/architecture.md)

**Android application:**
- Read existing code, contracts, DI, navigation, and build variants before changing them; preserve unrelated behavior and edits.
- Keep UI rendering separate from screen business logic and data access. Use ViewModels for screen state and repositories for data boundaries.
- Keep published state read-only; preserve coroutine cancellation and make blocking work main-safe.
- Collect Compose state with `collectAsStateWithLifecycle`; use effects for composition-owned work. For existing Fragments, use the view lifecycle and clear ViewBinding on view destruction.
- Use Compose for new UI in a compatible project; preserve XML/Views when repairing existing screens. Keep the project's DI and navigation choices.
- Verify version-sensitive APIs against official documentation rather than forcing toolchain upgrades.

## The Four Elements of Simple Design (XP)

In priority order:
1. **Runs all the tests** - Must work correctly
2. **Expresses intent** - Readable, reveals purpose
3. **No duplication** - DRY where the same knowledge must change together
4. **Minimal** - Fewest classes, methods possible

## Code Smell Detection

**Investigate these signals and refactor when they cause a concrete problem:**

| Smell | Solution |
|-------|----------|
| Long Method | Extract methods, compose method pattern |
| Large Class | Extract class, single responsibility |
| Long Parameter List | Group cohesive values; retain clear composable callbacks |
| Divergent Change | Split into focused classes |
| Shotgun Surgery | Move related code together |
| Feature Envy | Move method to the envied class |
| Data Clumps | Extract class for grouped data |
| Primitive Obsession | Wrap in value objects |
| Repeated type branching | Consider polymorphism; retain exhaustive sealed `when` |
| Parallel Inheritance | Merge hierarchies |
| Speculative Generality | YAGNI - remove unused abstractions |

See: [references/code-smells.md](references/code-smells.md)

## Design Patterns Awareness

**Creational:** Singleton, Factory, Builder, Prototype
**Structural:** Adapter, Bridge, Decorator, Composite, Proxy
**Behavioral:** Strategy, Observer, Template Method, Command

**Warning:** Don't force patterns. Let them emerge from refactoring.

See: [references/design-patterns.md](references/design-patterns.md)

## Testing Strategy

**Test Types (from inner to outer):**
1. **Unit Tests** - Single class/function, fast, isolated
2. **Integration Tests** - Multiple components together
3. **E2E/Acceptance Tests** - Full system, user perspective

**Arrange-Act-Assert Pattern:**

```kotlin
// Partial JUnit test body; calculator is the subject under test.
// Required import: org.junit.Assert.assertEquals
// Arrange
val calculator = Calculator()

// Act
val result = calculator.add(2, 3)

// Assert
assertEquals(5, result)
```

**Test Naming:** Use concrete examples, not abstract statements

```kotlin
// BAD: canAddNumbers
// GOOD: adding2And3Returns5
```

See: [references/testing.md](references/testing.md)

Use deterministic coroutine tests, controlled repository boundaries, and appropriate Compose/Views tests. Report local tests, assembly, device behavior, visual comparisons, and live service checks separately.

## Behavioral Principles

- **Tell, Don't Ask** - Let the owner enforce invariants; reading immutable UI state is appropriate
- **Design by Contract** - Preconditions, postconditions, invariants
- **Hollywood Principle** - "Don't call us, we'll call you" (IoC)
- **Law of Demeter** - Only talk to immediate friends

## Pre-Code Checklist

Before changing code, answer:

1. [ ] Do I understand the requirement? (Write acceptance criteria first)
2. [ ] What existing or new behavioral check will verify this change?
3. [ ] What is the simplest solution?
4. [ ] What patterns might apply? (Don't force them)
5. [ ] Am I solving a real problem or a hypothetical one?

## During-Code Checklist

While coding, continuously ask:

1. [ ] Is this the simplest thing that could work?
2. [ ] Does this class have a single responsibility?
3. [ ] Do dependencies respect useful boundaries without unnecessary interfaces?
4. [ ] Can I name this more clearly?
5. [ ] Is repeated knowledge worth sharing, or would extraction add coupling?

## Post-Code Checklist

After the code works:

1. [ ] Do all tests pass?
2. [ ] Is there any dead code to remove?
3. [ ] Can I simplify any complex conditions?
4. [ ] Are names still accurate after changes?
5. [ ] Would a junior understand this in 6 months?

## Red Flags - Stop and Rethink

- Changing meaningful behavior without a way to verify it
- State with multiple uncoordinated owners
- A method or class mixing unrelated responsibilities
- Nesting or receiver chains that hide control flow
- Hardcoding values that should be configurable
- Creating abstractions without a demonstrated benefit
- Adding features "just in case"
- Coupling business policy to transport, persistence, or UI internals
- God classes that know everything

## Remember

> "A little bit of duplication is 10x better than the wrong abstraction."

> "Focus on WHAT needs to happen, not HOW it needs to happen."

> "Design principles become second nature through practice. Eventually, you won't think about SOLID - you'll just write SOLID code."

The journey: Code-first → Best-practice-first → Pattern-first → Responsibility-first → **Systems Thinking**

Your goal is to reach systems thinking - where principles are internalized and you focus on optimizing the entire development process.
