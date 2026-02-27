# C# TDD Patterns

> **Note:** `lang-csharp.md` is the agent-facing sidecar — terse by design. This file explains the same patterns for humans.

## Xunit.Combinatorial

A single NuGet package (`Xunit.Combinatorial`) that provides two key attributes for `[Theory]` tests:

### `[CombinatorialData]`

Generates all possible combinations of parameter values. Use `[CombinatorialValues(...)]` on parameters to specify the value sets, or `[CombinatorialMemberData(nameof(Source))]` for dynamic sources.

```csharp
[Theory]
[CombinatorialData]
public async Task HappyPath(
    [CombinatorialValues(true, false)] bool real,
    [CombinatorialValues(true, false)] bool synchronous)
// Generates 4 test cases: (T,T), (T,F), (F,T), (F,F)
```

### `[PairwiseData]`

Drop-in replacement for `[CombinatorialData]` that generates a minimal set of test cases guaranteeing every *pair* of parameter values appears at least once. With 3+ parameters, this dramatically reduces test count — O(k²) instead of O(k^n) — while still catching the vast majority of interaction bugs (most defects are triggered by interactions between two parameters, not three or more).

```csharp
[Theory]
[PairwiseData]
public void Covers_all_pairs(
    [CombinatorialValues("a", "b", "c")] string x,
    [CombinatorialValues(1, 2, 3)] int y,
    [CombinatorialValues(true, false)] bool z)
// Full combinatorial: 18 cases. Pairwise: ~9 cases covering all pairs.
```

## FluentAssertions

Readable assertion library. `result.Should().Be(expected)` instead of `Assert.Equal(expected, result)`. Provides better failure messages and discoverable API via IntelliSense.

## Parameterization pattern

Whether using `[InlineData]`, `[CombinatorialData]`, `[PairwiseData]`, or `[MemberData]`, test parameters should include both **inputs and expected outputs**. The test body should be pure exercise-and-assert, not branching on inputs to determine expectations.

```csharp
[Theory]
[InlineData("hello", "HELLO")]
[InlineData("", "")]
[InlineData("already UPPER", "ALREADY UPPER")]
public void Upcase_returns_expected(string input, string expected)
{
    var result = Sut.Upcase(input);
    result.Should().Be(expected);
}
```

## Constructor / IDisposable over SetUp / TearDown

xUnit creates a new test class instance per test method, so the constructor acts as per-test setup. Implement `IDisposable` (or `IAsyncLifetime` for async) for cleanup. This is the xUnit-native pattern; `[SetUp]`/`[TearDown]` are NUnit concepts that don't exist in xUnit.
