# Test-Driven Development

> **Note:** The `SKILL.md` in this directory is intentionally terse — it's optimized for LLM consumption, not human reading. This file contains the full human-readable version.

---

## What is this?

A skill that teaches AI agents to practice test-driven development: write a failing test, write minimal code to make it pass, then refactor. The red-green-refactor cycle.

## Language-specific extensions

Language-specific TDD patterns live in sidecar markdown files (e.g., `lang-python.md`, `lang-csharp.md`). The main SKILL.md contains instructions for detecting the active language and loading the relevant sidecar. This keeps the core skill lean while supporting deep, framework-specific guidance per language.

Each language sidecar has a companion README for human readers:

| Sidecar | Human README | Language |
|---------|-------------|----------|
| `lang-python.md` | [lang-python-README.md](lang-python-README.md) | Python (pytest, pytest-describe) |
| `lang-csharp.md` | [lang-csharp-README.md](lang-csharp-README.md) | C# (xUnit, Xunit.Combinatorial, FluentAssertions) |

## Contributing

Add a `lang-{language}.md` file for new language support. Keep it terse (agent-facing). Add human-readable examples to this README.
