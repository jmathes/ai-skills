# Stakeholder Alignment

> **Note:** The `SKILL.md` in this directory is intentionally terse — it's optimized for LLM consumption, not human reading. This file contains the full human-readable version.

---

## What is this?

A skill that helps you map your work priorities to what your management chain (and other key stakeholders) actually cares about. Most people implicitly do this — they know their boss likes detailed updates or their skip-level cares about innovation. This skill makes it explicit and queryable by an AI assistant.

## Why?

When an AI helps you prioritize work, write updates, or plan your week, it doesn't know that your grand-manager wants to see volume while your direct manager wants to see rigor. Without that context, it optimizes generically. With a stakeholder map, it can help you:

- **Prioritize tasks** by how many stakeholders they satisfy
- **Frame updates** differently for different audiences
- **Identify blind spots** — work that's important but invisible to the people evaluating you
- **Spot high-ROI tasks** that satisfy multiple stakeholders simultaneously

## How it works

### First time setup

When the skill is first activated and no stakeholder file exists, it walks you through an interactive questionnaire:

1. **Who matters?** Identify 2-4 people whose perception of your work affects your career — typically your direct manager, skip-level, and grand-manager, but could include a key peer, product owner, or external partner.

2. **What do they value?** For each person, the skill probes for what "good work" looks like to them:
   - Do they want frequent updates or just results?
   - Do they value thoroughness or speed?
   - Are they looking for innovation, consistency, or visible artifacts?
   - Do they care about technical depth or business impact?
   - What makes them brag about their reports?

3. **Where to store it?** The skill asks where to save your stakeholder notes. Default suggestion is alongside your personal context, but it's your call.

### Ongoing use

Once the stakeholder file exists, the skill is available as context whenever you're:
- Planning what to work on next
- Writing a status update or weekly summary
- Deciding how much detail to put into a deliverable
- Evaluating whether a side project is worth the time

### Example

A stakeholder table might look like:

| Stakeholder | Role | Values | Optimize for |
|-------------|------|--------|-------------|
| Alice | Direct manager | Detail, rigor, self-authored updates | Frequent written updates with milestones, thorough investigation docs |
| Bob | Skip-level | Innovation, AI adoption | Visible AI usage, sharing tools/patterns, being the "AI person" |
| Carol | Grand-manager | Throughput, artifacts | Lots of commits/PRs/docs, dashboards, evidence of activity |

A task like "write a blog post about an AI workflow pattern you built" would score high across all three: it's detailed (Alice), AI-related (Bob), and produces a visible artifact (Carol). That's a high-ROI task.

A task like "quietly refactor internal tests" scores for Alice (rigor) but is invisible to Bob and Carol. Still worth doing, but maybe pair it with a brief writeup to make it visible.

## Periodic review

Stakeholder priorities shift. People get promoted, reorganized, or change focus. The skill prompts for a review quarterly or whenever you mention a role change.
