# Test-Driven Development

Start with a concrete input and expected observable outcome. Use test-first development for new logic when it provides a useful feedback loop. For a bug, reproduce it and add a regression test where practical. For a behavior-preserving refactor, run existing coverage first and add characterization tests only where needed.

Documentation, formatting, and other low-impact edits do not need artificial tests. UI, lifecycle, and integration changes may need device or visual checks beyond JVM tests.

## The Core Loop

```
RED → GREEN → REFACTOR → RED → ...
```

### RED Phase
Write a failing test that describes the behavior you want. The test should:
- Use domain language, not technical jargon
- Describe WHAT, not HOW
- Be a concrete example, not an abstract statement

Run it and confirm the failure comes from the missing behavior, not broken setup. A compilation error may reveal a missing API, but a behavioral assertion failure is stronger evidence that a regression test catches a bug.

Partial JUnit 4 naming examples; import `org.junit.Test` in the containing test class. Replace the comments with setup and assertions.

```kotlin
// BAD: Abstract
@Test fun canAddNumbers() { /* ... */ }

// GOOD: Concrete example
@Test fun whenAdding2And3ThenReturns5() { /* ... */ }
```

### GREEN Phase
Write the **simplest possible code** to make the test pass. Two strategies:

1. **Fake It** - Return a hardcoded value
   ```kotlin
   fun add(a: Int, b: Int): Int = 5 // Temporary step for this one example
   ```

2. **Obvious Implementation** - If you know the solution
   ```kotlin
   fun add(a: Int, b: Int): Int = a + b
   ```

**Prefer Fake It** when learning or unsure. Let more tests drive the real implementation.

### REFACTOR Phase
This is where **design happens**. Look for:
- Duplication and whether the repeated knowledge has the same reason to change
- Long methods to extract
- Poor names to improve
- Complex conditions to simplify

## The Three Laws of TDD

These describe a strict TDD practice session. Use them to keep the feedback loop small when practicing TDD; choose proportionate checks for maintenance and non-behavioral work as described above.

1. **No production code** without a failing test
2. **No more test code** than sufficient to fail (compilation failures count)
3. **No more production code** than sufficient to pass the one failing test

## The Rule of Three

**The third occurrence is a useful signal to examine duplication, not a mandatory gate.**

Why? Wrong abstractions can be worse than duplication. Wait for the pattern to emerge when intent is uncertain; extract sooner when a clear responsibility or shared invariant justifies it.

```kotlin
// Duplication #1 - Keep the example clear.
// Duplication #2 - Ask whether the intent is really shared.
// Duplication #3 - Review the pattern; extract when the abstraction fits.
```

## Triangulation

Each new test "sculpts" the solution toward a general, robust implementation.

Think of **degrees of freedom** - like a car that needs forward/back, left/right, and rotation. Each test carves out one degree of freedom until the implementation handles the required cases.

For `add`, the example `2 + 3 = 5` permits a constant implementation. Adding `2 + 4 = 6` rules that out; a negative-input example checks another part of the contract. Choose examples that reveal a new requirement rather than repeating the same assertion.

## Transformation Priority Premise

When going from RED to GREEN, prefer simpler transformations:

| Priority | Transformation |
|----------|----------------|
| 1 | {} → null |
| 2 | null → constant |
| 3 | constant → variable |
| 4 | unconditional → conditional |
| 5 | scalar → collection |
| 6 | statement → recursion |
| 7 | value → mutated value |

Earlier rows represent simpler transformations in this heuristic. Avoid jumping to complex transformations too early. This is a design aid, not a required order or a reason to introduce nullability, recursion, or mutation into Kotlin code that does not need them.

## Arrange-Act-Assert

Use a clear setup, action, and assertion:

Partial JUnit 4 example. The feature's `Order` accepts prices in integer minor units and `PercentDiscount(10)` means 10%; adapt to the app's actual money and discount contract.

```kotlin
import org.junit.Assert.assertEquals
import org.junit.Test

class OrderDiscountTest {
    @Test
    fun calculatesTotalWith10PercentDiscount() {
        // ARRANGE - Set up the world
        val order = Order()
        order.addItem(priceMinor = 100)
        val discount = PercentDiscount(10)

        // ACT - Execute the behavior
        val total = order.calculateTotal(discount)

        // ASSERT - Verify the outcome
        assertEquals(90, total)
    }
}
```

## Writing Tests Backwards

Sometimes it helps to write AAA in reverse:
1. Write the ASSERT first - what do you want to verify?
2. Write the ACT - what action produces that result?
3. Write the ARRANGE - what setup is needed?

## Test Naming Principles

- Use **behavior-driven names** with domain language
- Provide **concrete examples**, not abstract statements
- **One example per test** for easy debugging
- Avoid leaking implementation details

Partial JUnit 4 naming examples; import `org.junit.Test` in the containing class.

```kotlin
// BAD: Technical, implementation-focused
@Test fun shouldSetTheDataPropertyTo1() { /* ... */ }

// GOOD: Behavior-focused, domain language
@Test fun recognizesMomAsAPalindrome() { /* ... */ }
```

## Classic vs Mockist TDD

**Classic (Detroit/Chicago) TDD:**
- Prefer real in-process collaborators and assert outcomes
- Avoid unnecessary interaction coupling; pure Kotlin tests can stay very fast
- Best for: Pure functions, domain models, cooperating objects

**Mockist (London) TDD:**
- Replace collaborators with doubles and specify important interactions
- Can isolate orchestration, but over-specification makes refactors brittle
- Best for: Boundaries where a collaborator interaction is the contract

Start with Classic TDD to learn the technique. Add fakes, stubs, spies, or mocks when a boundary needs control. Test actual Room queries and HTTP mapping separately with supported integration infrastructure; a mock does not verify those adapters.

## Common Mistakes

1. **Skipping the red check during TDD** - Run the test to establish that it catches the missing behavior
2. **Writing too much test** - Just enough to fail
3. **Writing too much code** - Just enough to pass
4. **Skipping refactor** - This is where design lives
5. **Testing implementation** - Test behavior, not how it's done
6. **Abstract test names** - Use concrete examples
7. **Extracting too early** - Check shared intent; use the Rule of Three as a heuristic


## Kotlin and Android Feedback Loops

For asynchronous logic, control completion, time, and cancellation explicitly. Use `runTest` and a shared test scheduler; use a Main dispatcher rule for local ViewModel tests and reset Main during cleanup. A test relying on a real delay or live backend cannot reliably distinguish a broken implementation from a slow environment. See [Testing Strategy](testing.md) for coroutine, Flow, and lifecycle guidance.

For a ViewModel action, choose a concrete public-state transition: for example, refresh starts, a controlled repository failure appears, and retry succeeds. Test duplicate submissions or superseded requests only when those behaviors belong to the feature's contract. Assert cancellation separately from a service failure.

For a behavior-preserving refactor:

- Capture the behavior that must stay unchanged, including failure and retry.
- Run existing focused tests first and distinguish baseline failures.
- Make small cohesive edits and rerun affected coverage.
- Build the relevant variant when platform integration changed.
- Use device or screenshot comparison before claiming unchanged visuals.

When test infrastructure is missing or blocked, report the exact limitation and use the strongest available check. Do not call an unrun test passing, or expand a small change into a test-framework migration.
