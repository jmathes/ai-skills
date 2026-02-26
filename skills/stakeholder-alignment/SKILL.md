---
name: stakeholder-alignment
description: Map work priorities to management chain expectations. Use when planning work, prioritizing tasks, writing updates, or when asked about stakeholder strategy.
metadata:
  readme: README.md
---

## Purpose

Maintain awareness of what each person in management chain values. Use this to prioritize work, frame updates, and identify tasks with multi-stakeholder ROI.

## Setup

On first activation, if no stakeholder file exists, walk the user through creating one:

1. Ask: "Who are the 2-4 people whose opinion of your work matters most? (direct manager, skip-level, grand-manager, key peer, product owner, etc.)"
2. For each: "What does [name] value? What makes them think you're doing a good job?" — probe for: detail vs speed, visible artifacts vs quiet reliability, innovation vs consistency, written updates vs verbal, political alignment vs technical depth
3. Ask: "Where should I store your stakeholder notes?" — suggest `~/.copilot/skills/personal-context/stakeholders.md` or a path the user prefers
4. Generate a stakeholder table and save it

## Stakeholder file format

```markdown
| Stakeholder | Role | Values | Optimize for |
|-------------|------|--------|-------------|
| Name | Direct manager | Detail, rigor | Frequent written updates, thorough plans |
| Name | Skip-level | Innovation, visibility | Demos, shared artifacts, being "the X person" |
```

## Ongoing use

When prioritizing tasks or framing updates:
- Check which stakeholders a task serves
- Best ROI = tasks that satisfy multiple stakeholders simultaneously
- When writing updates, match tone/content to the recipient's "values" column
- Flag when a task serves zero stakeholders — it may be important but needs framing, or it's actually low priority

## Periodic review

Prompt user quarterly or on role changes: "Are your stakeholders still accurate? Has anyone's priorities shifted?"
