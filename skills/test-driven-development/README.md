# Test-Driven Development

> **Note:** The `SKILL.md` in this directory is intentionally terse -- it's optimized for LLM consumption, not human reading. This file contains the full human-readable version.

---

## What is this?

A skill that orchestrates textbook test-driven development through a supervisor agent that delegates every step to specialized subprocess agents. The emphasis is on **following the process with pedantic correctness**, not on producing code efficiently. Correct process produces correct code as a side effect.

## Architecture

The skill defines a **supervisor** (loaded via SKILL.md) and **five subprocess agents** (in `agents/`). The supervisor never writes code itself. It delegates each TDD step to the appropriate agent, checks the agent's output, and either proceeds or sends the agent back with feedback.

```
Supervisor (SKILL.md)
  |
  +-- tdd-setup           One-time: test project boilerplate
  |
  +-- LOOP until done:
      +-- tdd-red-describe   Identify one untested behavior (sees SUT only, NOT tests)
      +-- tdd-red-implement  Write one failing test
      +-- tdd-green          Minimal code to pass
      +-- tdd-refactor       DRY the SUT (always runs, even if answer is "nothing to do")
      +-- Supervisor checks after EVERY step. Never skips.
```

### Why agent-per-step?

Each agent receives only what it needs. Red-describe never sees tests (so it reasons from requirements, not coverage gaps). Green never sees the spec (so it can't jump ahead). Refactor never sees the behavior description (so it can't add functionality). The information barriers enforce the discipline that makes TDD work.

### Why "process exercise" framing?

LLMs pattern-match. If you frame TDD as "build this feature," the model anchors on feature-building and treats the process as overhead to shortcut. If you frame it as "practice this discipline," the model anchors on textbook TDD pedagogy -- the part of its training data that is most careful about following every step. The framing is load-bearing.

## Key design decisions

### Never skip a step
The supervisor always runs all five agents per cycle. Even if it's "obvious" refactoring isn't needed, the refactor agent still runs and explicitly says "no refactoring needed." This prevents the supervisor from developing a habit of skipping steps "when they're not needed," which inevitably escalates.

### Red-describe sees no tests
The red-describe agent receives SUT source and a supervisor-maintained list of already-tested behaviors. It never sees test files. This forces it to reason about what the SUT SHOULD do based on its structure and purpose, not about what tests are missing. Subtle but important difference.

### One behavior per iteration
Each loop produces exactly one test. "I'll write a few related tests" is the most common TDD violation by LLMs. The one-test-at-a-time constraint is structural: each agent invocation handles exactly one test.

### Build gate
If the test project can't compile and run, the supervisor stops and tells the user. It does not fake the cycle by writing tests and code together. It does not assert "this would fail because..." without running it.

### Tested-behaviors list
The supervisor maintains a running list of behaviors that have been tested. This list is fed to red-describe so it doesn't repeat, and serves as documentation of what the TDD session accomplished.

## Agent installation

Agent files in `agents/` must be installed where your Copilot CLI discovers custom agents:

```
# Copy agent definitions to ~/.copilot/agents/
cp agents/*.agent.md ~/.copilot/agents/
```

The supervisor references them via `task` tool `agent_type` values: `tdd-setup`, `tdd-red-describe`, `tdd-red-implement`, `tdd-green`, `tdd-refactor`.

## Test-writing opinions (carried into red-implement agent)

These are enforced by the `tdd-red-implement` agent:

- **Long descriptive test names.** Nobody calls them; people read them.
- **Four-step layout:** Setup, verify initial state, exercise, assert. The "verify initial state" step is not optional -- it catches test regressions, which are more dangerous than SUT regressions.
- **Mocks first, fakes later.** Switch to fakes when mocks need behaviors instead of canned output.
- **No real RNG or wall clock in tests.** Mock universally. Clock returns test start time. Random raises unless explicitly seeded.
- **No teardown.** Setup must be sufficient.
- **No DRY-ing tests.** Tests are documentation. Duplicate freely.
- **No optimizing tests.** Clarity over performance.

## Language-specific extensions

Language-specific TDD patterns live in sidecar markdown files (e.g., `lang-python.md`, `lang-csharp.md`). The supervisor loads the relevant sidecar during pre-flight and passes its content to `tdd-setup` and `tdd-red-implement`.

| Sidecar | Human README | Language |
|---------|-------------|----------|
| `lang-python.md` | [lang-python-README.md](lang-python-README.md) | Python (pytest, pytest-describe) |
| `lang-csharp.md` | [lang-csharp-README.md](lang-csharp-README.md) | C# (xUnit, MSTest) |

## Failure modes this skill prevents

| Failure | Prevention |
|---------|-----------|
| Writing all tests at once | One agent invocation = one test. Structural constraint. |
| Faking the cycle when build is broken | Build gate with explicit stop |
| Giving green agent entire feature spec | Green receives ONLY: SUT + one test + failure output |
| Skipping refactor because "it's fine" | Supervisor always runs refactor agent. Always. |
| Claiming TDD without running tests | Every code-changing step ends with a test run |
| Red-describe just filling coverage gaps | Red-describe never sees test files |
| Supervisor writing code itself | Explicit rule: all code changes go through agents |

## Contributing

- Add a `lang-{language}.md` sidecar for new language support. Keep it terse (agent-facing).
- Add a `lang-{language}-README.md` for human-readable examples.
- Agent definitions in `agents/` follow the same terse-for-LLMs principle.
