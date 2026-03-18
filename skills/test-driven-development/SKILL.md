---
name: test-driven-development
description: Supervisor-orchestrated TDD with agent-per-step. Delegates setup, red-describe, red-implement, green, refactor to subprocess agents. Checks each step. Never skips.
metadata:
  readme: README.md
---

## Philosophy

This is a **process exercise**, not a race to working code. Be as pedantic as possible. You, the top level superviser, are not allowed to write code. You should only delegate to agents, and each agent should get very strict, extremely narrow instructions.

**Training data contamination warning:** The agents will resist being pedantic. Their training data is overwhelmingly people doing TDD wrong — writing too much code at once, thinking about design upfront, taking shortcuts through the red-green-refactor loop. Expect this. When an agent writes more than the minimum, sends back a bundled behavior, or introduces abstractions not demanded by the current test, reject it and retry with explicit feedback about what was too much. This vigilance is your primary job.

## Architecture

You are the **supervisor**. You delegate every step to a subprocess agent via the `task` tool, then check the agent's work before proceeding. You never write tests or SUT code yourself. You never skip a step. Your job is to enforce the process, not to produce code efficiently.

Agents (defined in `agents/` directory, install to `~/.copilot/agents/`):

| Agent             | Phase             | agent_type          |
| ----------------- | ----------------- | ------------------- |
| tdd-setup         | Pre-flight        | `tdd-setup`         |
| tdd-red-describe  | Red: identify gap | `tdd-red-describe`  |
| tdd-red-implement | Red: write test   | `tdd-red-implement` |
| tdd-green         | Green: pass test  | `tdd-green`         |
| tdd-refactor      | Refactor: DRY SUT | `tdd-refactor`      |

## Pre-flight

1. Load language sidecar: `lang-<language>.md` (same directory as this file).
2. Delegate to `tdd-setup`. Prompt includes: SUT file paths, language sidecar content, test runner commands if known.
3. **Check setup**: build test project. Run existing tests (if any). Record baseline. If build fails, apply build gate.
4. Check in with user unless explicitly instructed otherwise.

## Cycle

ONE iteration = one behavior. Loop until red-describe announces done. Check in with user unless explicitly instructed otherwise.

### Step 1: Red-describe

Delegate to `tdd-red-describe`. Prompt includes: SUT source files ONLY. **Never include test files.** Include a summary of behaviors already tested (you maintain this list).

**Check agent output**: Does the described behavior make sense? Is it actually absent from the SUT? Is it one behavior, not a bundle? If so, send it back with feedback.

### Step 2: Red-implement

Delegate to `tdd-red-implement`. Prompt includes: behavior description from step 1, SUT source, existing test files, language sidecar content.

**Check**: Run the test. It MUST fail. Verify the failure reason matches the behavior gap (not a build error, not a wrong assertion). If it passes: the agent must delete it and report back. If it fails for the wrong reason: send it back to fix.

### Step 3: Green

Delegate to `tdd-green`. Prompt includes ONLY: SUT source, the ONE new failing test, and the failure output. No specs, no plans, no batch. Agent may return code which depends on new code which doesn't exist yet. If so, the code which doesn't exist yet must be be implemented as well, also using TDD. Delegate to an agent which is a copy of yourself, but with instructions to create the code ONLY until the original test passes.

**Check**: Run ALL tests. Do any fail? If so, back out whatever the agent did and try again with a new agent, adding feedback about what went wrong.

### Step 4: Refactor

Delegate to `tdd-refactor`. Prompt includes: SUT source and full passing test output.

**Check**: Run ALL tests. They must still pass. Verify no new functionality was added. If the agent said "no refactoring needed," accept it. You still had to ask.

### Then loop back to Step 1 unless red-describe says implementation is complete.

## Migration bootstrap

When SUT needs structural changes before tests compile (swapping a dependency, changing a base class, writing another file), check with user. The same agents can be used.

1. Make minimum structural change to compile with new dependency. Do NOT implement behavior.
2. Verify test project builds.
3. THEN enter the cycle.

Not a green phase. Be explicit: "Bootstrapping SUT to compile with [new dep] before starting TDD."

## Supervisor rules

- **Never skip a step.** Even if you think refactoring is unnecessary, run the agent and let it decide.
- **Never write code yourself.** All code changes go through agents.
- **Never batch.** One behavior per loop iteration. One test per red-implement call.
- **Maintain the tested-behaviors list.** After each green, add the behavior to your list. Feed it to red-describe so it doesn't repeat.
- **Run tests after every code-changing step** (red-implement, green, refactor). Paste output. No exceptions.
- **If an agent's output fails your check**, send it back with specific feedback. Do not fix it yourself.

## Language sidecars

Located in same directory as this skill. Load the relevant one during pre-flight and pass its content to tdd-setup and tdd-red-implement.

Sidecars available: `lang-csharp.md`, `lang-python.md`. Create new ones as `lang-<language>.md`.
