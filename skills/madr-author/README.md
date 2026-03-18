# MADR Author

> **Note:** The `SKILL.md` in this directory is intentionally terse — it's optimized for LLM consumption, not human reading. This file contains the full human-readable version.

## What This Does

Interactive ADR authoring using the [MADR 4.0.0](https://adr.github.io/madr/) template. The agent copies the template to your target location and walks you through each section one question at a time, filling in your answers.

## Usage

Tell the agent to create a new ADR (e.g., "new ADR", "create an ADR", "write a decision record"). It will:

1. Ask where to put it
2. Walk through each section with focused questions
3. Offer sensible defaults (today's date, "proposed" status)
4. Let you skip optional sections
5. Write the completed ADR and show it for review

## Template Source

The included `template.md` is the MADR 4.0.0 full template (from [adr/madr](https://github.com/adr/madr)) with HTML comments stripped. Sections marked optional in the MADR spec (Decision Drivers, Confirmation, More Information) can be omitted during authoring.

## License

The MADR template is licensed under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). This skill wraps it with an interactive workflow.
