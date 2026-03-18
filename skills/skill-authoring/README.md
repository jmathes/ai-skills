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
| `scripts/` | Both | Executable resources. Referenced by SKILL.md, documented in README.md. **Anything automatable MUST be a script.** |

## Why both files?

- **SKILL.md alone** works for LLMs but is opaque to human collaborators who want to understand, contribute to, or evaluate the skill.
- **README.md alone** wastes tokens when loaded into a context window and may hit the recommended 5K token limit for skill bodies.
- **Both together** serve each audience in its native format.

## Why maximize helper scripts?

Any skill behavior that *can* be a script *must* be a script. This isn't a suggestion — it's a core principle. The reasons are compounding:

1. **Greater introspection of LLM behavior.** When the LLM calls a script, you can see exactly what input it provided and what output it received. When the LLM does the same work inline, the reasoning is a black box buried in token generation. Scripts create observable boundaries.

2. **More determinism.** A Python script that parses JSON or calls an API produces the same output every time. An LLM doing the same work inline may hallucinate field names, reformat data inconsistently, or skip steps depending on context window pressure. Scripts are reproducible; inline LLM behavior is probabilistic.

3. **Less token usage.** Every token the LLM spends on deterministic work (data formatting, API calls, validation) is a token not spent on judgment, synthesis, and reasoning — the things LLMs are actually good at. Scripts offload the mechanical work.

4. **Less context window usage.** Script output is typically compact and structured. Inline LLM reasoning for the same task consumes context window with chain-of-thought tokens that serve no downstream purpose. Scripts return only the result.

The rule of thumb: if you could write a unit test for the behavior, it should be a script.

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
