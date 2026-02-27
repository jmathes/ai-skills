---
name: test-driven-development
description: Execute test-driven development with red-green-refactor cycle. Use when writing new code, fixing bugs, or refactoring — write failing test first, minimal code to pass, then refactor. Supports language-specific TDD patterns via sidecar files.
metadata:
  readme: README.md
---

## Cycle

1. **Red** — Write the simplest possible failing test that defines desired behavior. This will often mean adding an input/expectation pair to a collection of test data. Run it. Confirm it fails for the expected reason.
2. **Green** —
   a. _Delegate to a stateless agent_ to write the minimal code to make the test pass. All SUT should be written by sub-agents. Sub-agents should be instructed to make the simplest possible change to make tests pass. Sub-agents should be reminded that "simplest possible change" implies no refactoring, no optimization, no extra code beyond what's needed to pass the test, no changes to the test.
   b. Run the test. Confirm it passes. If it doesn't, alert the user if possible, or debug.

3. **Refactor** —
   a. _Delegate to a stateless agent_ to DRY the SUT. Deduplication should involve the least possible planning for future deduplication, testing, or extension. As much as possible, these things should be discovered vs planned.
   b. Run tests. Confirm they all pass. If not, debug.

## Language-specific sidecars

Load relevant language-specific `lang-<language>.md` files (located in the same directory as this file - check config to find skill directories).

## Universal Patterns

- Test name is long and descriptive. Nobody ever has to call it, but people have to read it.
- test case layout:
  1. Setup: arrange test data, mocks/fakes, SUT instance
  2. Verify initial state (NOT optional, but not always possible. Prevents regression of the test itself, which is more dangerous than a regression of the SUT)
  3. Exercise SUT: invoke method/behavior under test
  4. Assert postconditions: state changes, output, interactions
- Mocks/stubs first, fakes later. Switch to fakes when mocks start needing behaviors instead of canned output.
- During a test, NOTHING should EVER access any kind of RNG or wall clock (including sleeping). Mock these out as universally as possible. Every wallclock check should return the exact time the test started executing. Every attempt to get a random value should raise an exception, forcing the test author to explicitly define the deterministic RNG output for that test case.

## Universal antipatterns

- Any kind of teardown. Last resort only. Test setup should always be enough.
- Don't DRY your tests.
- Don't optimize your tests. They should double as documentation.
- Mirror the SUT directory structure in the test tree. If an existing test structure exists, match it instead.
