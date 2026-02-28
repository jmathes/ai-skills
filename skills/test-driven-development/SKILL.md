---
name: test-driven-development
description: Execute test-driven development with red-green-refactor cycle. Use when writing new code, fixing bugs, or refactoring — write failing test first, minimal code to pass, then refactor. Supports language-specific TDD patterns via sidecar files.
metadata:
  readme: README.md
---

## Cycle

1. **Red** — Write the simplest possible failing test that defines desired behavior. This will often mean adding an input/expectation pair to a collection of test data. Run it. Confirm it fails for the expected reason.
2. **Green** —
   a. Delegate to the `tdd-green` agent (`task` tool, `agent_type: "tdd-green"`). It writes the minimal code to make the test pass. No refactoring, no optimization, no extra code, no test changes.
   b. Run the test. Confirm it passes. If it doesn't, alert the user if possible, or debug.

3. **Refactor** —
   a. Delegate to the `tdd-refactor` agent (`task` tool, `agent_type: "tdd-refactor"`). It DRYs the SUT minimally — no planning for future deduplication/extension. Discovery over planning.
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
