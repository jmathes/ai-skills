## C# TDD

### Preferred patterns

- Frameworks: **xUnit** + **Xunit.Combinatorial** + **FluentAssertions**
- `[PairwiseData]` instead of `[CombinatorialData]` when ≥3 parameters (>2s): O(k²) vs O(k^n)

### Structure

- Match surrounding structure when present. Otherwise:
  - One test class per SUT class. `[Fact]` for single cases, `[Theory]` for parameterized.
  - Test naming: `MethodName_Scenario_ExpectedResult` or descriptive sentence

### Anti-patterns

- `[SetUp]`/`[TearDown]` (NUnit-ism) — use constructor/`IDisposable` or `IAsyncLifetime`
- Start with mocks. Switch to fakes when mocks start needing behaviors instead of canned output.
