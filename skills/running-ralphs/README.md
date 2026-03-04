# Running Ralphs

> **Note:** The `SKILL.md` in this directory is intentionally terse — it's optimized for LLM consumption, not human reading. This file contains the full human-readable version.

---

A pattern for parallel redundant agentic execution: spawn multiple AI agents with the same goal but different constraints, let them race, compare outputs, and keep the best.

## Name

"Running Ralphs" — like a horse race where every horse is named Ralph. You don't care which Ralph wins; you care that one of them finishes well. Most will faceplant. That's the point.

## The Problem

AI agents are nondeterministic. Given the same task, two runs can produce wildly different quality. A single run might hit a dead end, hallucinate a dependency, or take an architectural path that paints itself into a corner. You won't know until it's done.

Meanwhile, token cost is plummeting. An agent run that would have cost $50 a year ago costs $2 today. Your time hasn't gotten cheaper.

## The Pattern

1. **Clone the workspace** — each Ralph gets its own isolated copy (separate git clone, separate branch, separate directory). No shared mutable state.
2. **Vary one axis** — methodology (TDD vs. ad-hoc), model (Sonnet vs. Opus), constraints ("no external deps" vs. "use whatever"), prompt verbosity, or starting point.
3. **Same finish line** — identical acceptance criteria for all Ralphs. Tests pass, builds succeed, spec is met.
4. **Let them race** — launch all Ralphs, work on something else (or watch the overseer monitor them).
5. **Compare and scavenge** — diff the outputs. Keep the best implementation. Extract useful pieces from the losers: tests, edge cases, docs, architectural ideas.

## When It Works

- The task has **clear acceptance criteria** (if you can't tell who won, you can't run a race)
- **Multiple valid paths** exist (if there's one obvious solution, parallelism is waste)
- **Cost of a bad result exceeds cost of N runs** (if the task is trivial, just run it once)
- You want to **evaluate a methodology** — Running Ralphs is a natural A/B test for process changes

## When It Doesn't

- **Trivial tasks** — one agent, one try, done
- **Subjective outputs** — creative writing, open-ended design (no finish line to compare against)
- **Shared mutable state** — if Ralphs would edit the same branch or files, they'll corrupt each other

## Real Example

Migrating a cache implementation from `System.Runtime.Caching` to `Microsoft.Extensions.Caching.Memory`:

- **Ralph A**: Implementation-first. Experienced session with prior context, 5 tests already written ad-hoc.
- **Ralph B**: Strict TDD. Fresh checkout, `test-driven-development` skill enforcing the red-green-refactor cycle.
- **Same acceptance criteria**: all tests pass, no references to `System.Runtime.Caching`, builds clean.
- **Comparison**: which produced better tests? Cleaner code? More edge cases? Did TDD discipline produce a meaningfully different architecture?

## Scavenging Losers

The losing Ralphs aren't waste:

- **Tests** from the TDD Ralph can be transplanted into the winning implementation
- **Edge cases** one Ralph found that others missed are free bug prevention
- **Documentation or ADRs** generated as side effects have value independent of the code
- **Architectural ideas** might be better even if that Ralph's implementation was worse

## Efficiency Notes

- Use an **overseer session** to monitor Ralphs without context-switching yourself
- **Stagger launches** if you want to observe early behavior before committing to all N
- **Context-only prompts** (no action items) let Ralphs initialize without immediately racing — you control the start
- **Named WT windows** (GUIDs via `wt.exe -w`) prevent Ralphs from accidentally adding tabs to each other's terminals

## Cost Model

The break-even question: is `N × agent_cost` less than `your_hourly_rate × time_to_recover_from_a_bad_single_run`?

With current pricing, N=2–3 is almost always worth it for any task that takes more than 30 minutes of agent time. The comparison diff alone teaches you things about your codebase that a single run never would.
