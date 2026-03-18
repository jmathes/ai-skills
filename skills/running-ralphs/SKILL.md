---
name: running-ralphs
description: Race N agents on the same task with varied constraints. A/B testing for agentic workflows — compare results, keep the winner, scavenge the losers.
metadata:
  readme: README.md
---

## Pattern

Spawn N independent agents (separate sessions, windows, or subprocesses) with the same task. Vary one axis per Ralph: methodology, model, constraints, starting point. Let them race. Compare outputs. Keep the best; scavenge useful pieces from the rest.

## When to use

- Task has clear acceptance criteria (tests pass, builds, matches spec)
- Multiple valid implementation paths exist
- Cost of bad output > cost of N parallel runs
- You want to evaluate a methodology (TDD vs. ad-hoc, different models, etc.)

## When NOT to use

- Task is trivial or deterministic (one obvious solution)
- Outputs can't be meaningfully compared (creative writing, open-ended design)
- Shared mutable state would cause conflicts (same branch, same files)

## Setup

1. **Isolate**: each Ralph gets its own workspace (separate clone, branch, or directory). No shared mutable state.
2. **Vary**: pick one axis to differentiate. Examples:
   - Methodology: TDD vs. implementation-first
   - Model: Sonnet vs. Opus vs. GPT
   - Constraints: "no helper libraries" vs. "use whatever"
   - Prompt style: detailed spec vs. minimal guidance
3. **Same goal**: identical acceptance criteria. Tests, build, spec — whatever "done" means.
4. **Launch**: use the overseer or launch scripts to spawn sessions. Context-only prompts (no action items) so you can stagger starts or observe.

## Evaluation

Compare Ralphs on:

| Axis | How |
|------|-----|
| Correctness | Do tests pass? Does it build? Does it match spec? |
| Code quality | Diff the implementations. Which is cleaner? |
| Completeness | Which covered more edge cases? |
| Speed | Wall clock to first passing build |
| Methodology artifacts | TDD Ralph has tests; ad-hoc Ralph may not |

## Scavenging

Losing Ralphs aren't waste. Extract:
- Tests from the TDD Ralph into the winning implementation
- Edge cases one Ralph found that others missed
- Documentation or ADRs generated as side effects
- Architectural ideas (even if implementation was worse)

## Anti-patterns

| Avoid | Why |
|-------|-----|
| Same workspace | Ralphs clobber each other's files |
| No acceptance criteria | Can't compare without a finish line |
| Too many axes varied | Can't attribute differences to methodology vs. noise |
| Ignoring losers | Scavenge before discarding |
