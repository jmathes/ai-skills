---
name: stakeholder-alignment
description: Map work priorities to management chain expectations. Use when planning work, prioritizing tasks, writing updates, or when asked about stakeholder strategy.
metadata:
  readme: README.md
---

## Setup (if no stakeholder file exists)

Walk user through questionnaire:
1. "Who are 2-4 people whose opinion of your work matters most?" (manager, skip, grand-manager, key peer, PO)
2. Per person: "What does [name] value?" — probe: detail vs speed, artifacts vs quiet reliability, innovation vs consistency, written vs verbal, political vs technical
3. "Where to store?" — suggest `~/.copilot/skills/personal-context/stakeholders.md`
4. Generate table, save

## File format

```
| Stakeholder | Role | Values | Optimize for |
```

## Use

When loaded (typically via overseer or personal-context), passively evaluate work against stakeholder values:

- If a task produces artifacts but nobody's being told → suggest a quick ping or update
- If effort is invisible to all stakeholders → flag: reframe it or deprioritize
- If a small addition (ADR, dashboard widget, commit message wording) would make work land better with a specific stakeholder → suggest it inline
- If work naturally serves multiple stakeholders → call that out as high-ROI
- Frame suggestions as "[manager] would want to see X" or "this is a [grand-manager] artifact" — tie to the person, not the abstraction

Don't generate matrices or audits unprompted. Just nudge when something is close to landing well but missing a stakeholder angle.

## Quarterly review

Prompt quarterly or on role change: "Stakeholders still accurate? Priorities shifted?"
