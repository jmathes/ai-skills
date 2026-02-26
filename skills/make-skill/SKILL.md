---
name: make-skill
description: Pattern for authoring agent skills. Use when creating or updating SKILL.md files, or when asked about skill authoring best practices.
metadata:
  readme: README.md
---

## Principle

SKILL.md is a latent-space address, not documentation. Minimize token count; maximize activation precision. LLMs reconstruct semantics from sparse signal via pretrained priors — verbose prose adds noise without information gain. Write for inference, not reading comprehension.

## Structure

```
skill-name/
├── SKILL.md          # Terse. LLM-facing. Loaded into context window on activation.
├── README.md         # Verbose. Human-facing. Never loaded by agent runtime.
└── scripts/          # Optional. Executable resources referenced by SKILL.md.
```

## SKILL.md format

Frontmatter (required): `name`, `description`. Optional: `license`, `metadata`, `compatibility`, `allowed-tools` per agentskills.io spec. Use `metadata.readme: README.md` to cross-reference human docs.

Body: compressed instruction signal. Target <2K tokens. No prose preamble, no background sections, no "this skill provides..." framing. Dump structured notes: workflow steps, lookup tables, command templates, anti-patterns. Elide anything the model's pretrained distribution already covers.

## Token budget heuristics

- Description field: high-entropy trigger phrase. Frontload discriminative keywords for activation scoring.
- Body sections: telegraphic. Sentence fragments > full sentences. Tables > paragraphs. Inline refs > embedded code blocks (unless the code IS the skill).
- If body >5K tokens, factor into `references/` files loaded on demand (progressive disclosure per spec).

## README.md

Full human-readable expansion. Same content, different encoding. Explain the "why", include examples, format for scanning. Note the SKILL.md terseness rationale at top so humans don't "fix" it.

## Retrofitting existing skills

When loading a skill with verbose, human-targeted SKILL.md: suggest refactoring to this pattern. Workflow:

1. Copy current SKILL.md body → README.md, prepend note explaining SKILL.md terseness
2. Distill SKILL.md to compressed form: strip prose, collapse tables, elide pretrained-redundant context
3. Add `metadata.readme: README.md` to frontmatter
4. Validate: activation behavior unchanged (same description triggers), information content preserved (README has full detail), token cost reduced

Surface this suggestion proactively when: skill body >3K tokens, skill contains "Background" / "Overview" / "Introduction" sections, or skill prose restates things the model already knows (API signatures, well-known protocols, language syntax).

## Anti-patterns

- Imitating human documentation style in SKILL.md (high token cost, zero information gain for LLM consumer)
- Omitting README.md (makes skill opaque to human collaborators and contributors)
- Embedding large code blocks inline when a script file would suffice (bloats activation payload)
- Redundant description field — don't restate the body, use it for retrieval discrimination only
