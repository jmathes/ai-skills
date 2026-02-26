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

- Prioritize: tasks serving multiple stakeholders = highest ROI
- Frame updates: match tone/content to recipient's values column
- Flag zero-stakeholder tasks: needs reframing or is genuinely low priority

## Review

Prompt quarterly or on role change: "Stakeholders still accurate? Priorities shifted?"
