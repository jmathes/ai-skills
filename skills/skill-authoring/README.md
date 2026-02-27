# Skill Authoring Template

> **Note:** The `SKILL.md` in this directory is intentionally terse — it's optimized for LLM consumption, not human reading. This file contains the full human-readable version.

---

## What is this?

A meta-skill: a template and pattern for writing good agent skills. It enforces a key insight — SKILL.md files are read by LLMs, not humans, so they should be written for LLMs.

## The core idea

Large language models are massively overparameterized relative to the learnable structure in their training data. This means they reconstruct meaning from sparse, compressed input — they don't need the verbose, explanatory prose that humans rely on. A few well-chosen keywords and structured notes activate the right latent concepts as effectively as (often more effectively than) paragraphs of explanation.

Writing SKILL.md files in human-documentation style wastes context window tokens without adding information for the LLM consumer. It's like sending a JPEG when the receiver already has the codebook — you only need to send the residuals.

## The pattern

Every skill directory should contain:

| File | Audience | Purpose |
|------|----------|---------|
| `SKILL.md` | LLMs | Terse, compressed instructions. Loaded into the agent's context window on activation. Target <2K tokens. |
| `README.md` | Humans | Full explanation with background, examples, and rationale. Never loaded by the agent runtime. |
| `scripts/` | Both | Executable resources. Referenced by SKILL.md, documented in README.md. |

## Why both files?

- **SKILL.md alone** works for LLMs but is opaque to human collaborators who want to understand, contribute to, or evaluate the skill.
- **README.md alone** wastes tokens when loaded into a context window and may hit the recommended 5K token limit for skill bodies.
- **Both together** serve each audience in its native format.

## SKILL.md writing guidelines

1. **Frontmatter:** `name` and `description` are required. Use `metadata.readme: README.md` to point humans to the readable version.
2. **Description field:** Think of it as a retrieval query, not a summary. Frontload the most discriminative keywords — these determine whether the skill gets activated.
3. **Body:** Use sentence fragments, tables, and inline references. Skip introductions, background sections, and "this skill provides..." framing. If the model already knows it from pretraining, don't repeat it.
4. **Code:** Reference scripts by path rather than embedding them inline, unless the code block IS the instruction.
5. **Size:** Keep under 2K tokens ideally, 5K max. If larger, split into referenced files in `references/` or `scripts/`.

## TODO

### Automated pretrained-redundancy detection

The linter currently can't detect whether a skill's content is already in the model's pretrained distribution — the one check that requires human judgment today. But this is automatable in principle: spin up an agent *without* the skill loaded and test whether it can already reproduce the skill's content. If it can, the skill is pretrained-redundant noise.

Challenges:
- Model-dependent: what's redundant for GPT-5 may not be for Haiku. The check needs to be parameterized by model.
- Scoring: need a threshold for "the model already knows this" vs "the model gets it roughly right but the skill adds precision."
- Cost: running a model query per skill per lint pass may be expensive. Could cache results keyed by (model, skill-content-hash).

This would close the last gap in fully automated skill quality scoring.

## References

- [Agent Skills Specification](https://agentskills.io/specification) — the cross-agent spec for SKILL.md format
- [Creating agent skills for GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills) — official GitHub docs
