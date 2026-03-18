---
name: madr-author
description: Author ADRs (Architecture Decision Records) interactively. Uses MADR 4.0.0. Use when creating ADRs. Use for reference when checking ADRs.
metadata:
  readme: README.md
---

## Workflow

1. Copy `template.md` from this skill's directory into the target location (ask user where if unclear)
2. Run scripts\ask_user.py targeting the newly copied template.
3. Read the updated template and propose edits. Show the user the completed template and describe your proposed edits. Ask the user for suggestions or changes and apply them to the template until the user is satisfied.

## Rules

- Always use ask_user.py to fill out the template. Don't edit the template directly until ask_user.py is completed.
- Preserve MADR 4.0.0 structure exactly — don't add/rename/reorder sections
