---
name: skill-authoring
description: Pattern for authoring and improving agent skills. Use when creating, updating, or retrofitting SKILL.md files, or when asked about skill best practices.
metadata:
  readme: README.md
---

## Principle

SKILL.md is a latent-space address, not documentation. Maximize information density — like a student's class notes, not a textbook. LLMs reconstruct semantics from sparse signal via pretrained priors; verbose prose adds noise without information gain. Write for inference, not reading comprehension.

## Proper Structure

```
skill-name/
├── SKILL.md          # Terse. LLM-facing. Loaded into context window on activation.
├── README.md         # Verbose. Human-facing. Never loaded by agent runtime.
└── scripts/          # Optional. Executable resources referenced by SKILL.md.
```

## SKILL.md format

Frontmatter (required): `name`, `description`. Optional: `license`, `metadata`, `compatibility`, `allowed-tools` per agentskills.io spec. Use `metadata.readme: README.md` to cross-reference human docs.

Body: compressed instruction signal. Target <2K tokens. No prose preamble, no background sections, no "provides..." / "ensures..." / "is designed to..." framing. Dump structured notes: workflow steps, lookup tables, command templates, anti-patterns. Elide anything the model's pretrained distribution already covers.

## Token budget heuristics

- Description field: high-entropy trigger phrase. Frontload discriminative keywords for activation scoring.
- Body sections: telegraphic. Sentence fragments > full sentences. Tables > paragraphs. Inline refs > embedded code blocks (unless the code IS the skill).
- Large code blocks: only problematic when pretrained-redundant (CLI help text, well-known API signatures, standard config). Novel/project-specific code is information-dense and fine inline.
- If body >5K tokens, factor into `references/` files loaded on demand (progressive disclosure per spec).

## README.md

Full human-readable expansion. Same content, different encoding. Explain the "why", include examples, format for scanning. Note the SKILL.md terseness rationale at top so humans don't "fix" it.

A missing README.md is a strong signal the SKILL.md is doing double-duty as human docs — filler phrases and explanatory prose confirm it. Retrofitting always starts by extracting human-readable content into README.md.

## Skill vs. context

Two categories share SKILL.md format and benefit from the same compression:

- **Skills** — crystallized, transferrable knowledge (tools, patterns, workflows). Ideally stable.
- **Context files** — in-progress mental state around an active project (expectations, progress, people). Ephemeral by nature.

Both are loaded identically by the agent runtime. Both benefit from max information density. The linter applies to both.

## Retrofitting existing skills

When loading a skill with verbose, human-targeted SKILL.md: suggest refactoring to this pattern. Workflow:

1. Copy current SKILL.md body → README.md, prepend note explaining SKILL.md terseness
2. Distill SKILL.md to compressed form: strip prose, collapse tables, elide pretrained-redundant context
3. Add `metadata.readme: README.md` to frontmatter
4. Validate: activation behavior unchanged (same description triggers), information content preserved (README has full detail), token cost reduced

Surface this suggestion proactively when: skill body >3K tokens, skill contains "Background" / "Overview" / "Introduction" sections, or skill prose restates things the model already knows (API signatures, well-known protocols, language syntax).

## Anti-patterns

- Human documentation style in SKILL.md (high token cost, zero LLM information gain)
- Omitting README.md (makes skill opaque to human collaborators)
- Pretrained-redundant code blocks (CLI help text, well-known specs — the model already has these)
- Redundant description field — don't restate the body, use it for retrieval discrimination only

## Automated lint

`scripts/lint_skills.py` — scans all skill directories and flags violations.

```
python scripts/lint_skills.py [DIR ...]   # explicit roots
python scripts/lint_skills.py             # auto-discovers from ~/.copilot/config.json
```

Checks (5 exact, 3 heuristic):

| Check | Level | Type |
|---|---|---|
| Missing `name`/`description` in frontmatter | FAIL | exact |
| No README.md alongside SKILL.md | FAIL | exact |
| Body >3K tokens | FAIL | exact |
| Human-doc headings (Overview/Background/Introduction/Purpose) | FAIL | exact |
| Large inline code blocks (>20 lines) | WARN | exact |
| Filler phrases ("provides a", "is designed to", etc.) | WARN | heuristic |
| Description/body keyword overlap >45% | WARN | heuristic |
| Prose ratio >60% | WARN | heuristic |
