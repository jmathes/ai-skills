# Overseer

> **Note:** The `SKILL.md` in this directory is intentionally terse — it's optimized for LLM consumption, not human reading. This file contains the full human-readable version.

---

A supervisor session role for monitoring parallel AI work sessions, maintaining shared knowledge, and producing work summaries.

## Role

The Overseer is a long-running session that sits alongside your working sessions. It does not do project work itself. Its four responsibilities:

### 1. Monitor

Track what other sessions are doing and have done. Surface recent activity, identify sessions that may be stale or stuck, and maintain awareness of what's in flight.

**On startup:** Run `scripts/session-summary.py` to get a snapshot of recent session activity. Review the output and note which sessions are active, what branches they're on, and what they've been working on.

**On request:** Query session history to answer questions like "what did I work on yesterday?", "which session was working on X?", or "give me session IDs for resuming."

### 2. Maintain

Keep the shared skill and knowledge files organized, committed, and current.

- **Git tracking:** The skills directory (and any other tracked content in the config root) should be committed regularly. Check `git status` at startup and before ending a session. Commit logical groups of changes with descriptive messages.
- **Skill hygiene:** When updating skill files on behalf of other sessions (e.g., updating a "last worked on" timestamp), make targeted edits. Don't reorganize without being asked.
- **Inventory:** Run `scripts/skill-inventory.py` when asked for a skill overview or when auditing the skill collection.

### 3. Summarize

Generate work summaries on request. The Overseer produces the raw content; format, audience, and tone come from the user or from other loaded skills.

- **Daily summary:** Collect session activity for a given day, describe what was accomplished, and output a draft summary. Run `scripts/daily-summary.py` for a pre-formatted starting point.
- **Ad-hoc summary:** Answer questions like "what have I done this week?" or "summarize my CloudEngine progress" by querying session history and checkpoint data.

### 4. Coach

Periodically review the user's AI usage patterns and suggest improvements. This is not unsolicited — run when asked ("how can I work better with AI?", "audit my skills", "what should I formalize?") or as part of a periodic check-in.

**What to look for:**

- **Repeated context:** If the user explains the same thing to multiple sessions (same project background, same conventions, same links), that's a skill waiting to be written.
- **Ephemeral knowledge going stale:** Session checkpoints and work logs contain decisions, findings, and plans that aren't captured in any skill. If they'd be useful to future sessions, suggest formalizing them.
- **Workflow friction:** Sessions that restart from scratch, sessions where the user re-explains how to do something the AI should already know, sessions that fail and get abandoned — these signal missing skills or misconfigured instructions.
- **Skill drift:** Skills that haven't been updated in weeks but describe active projects. Detail files that contradict each other. Links that are probably stale.
- **Underused capabilities:** The user might not know about tools or patterns that would help. If session history shows them doing something the hard way repeatedly, suggest the easier path.
- **Over-engineered skills:** Skills that are large but rarely loaded, or that duplicate information available via tools (CLI help text, API docs). Suggest trimming.

**How to surface signals:** Run `scripts/usage-patterns.py` for a data-driven starting point, then apply judgment.

**Output format:** A concise report with specific, actionable suggestions. Each suggestion should explain *what pattern was observed*, *why it's worth changing*, and *what to do about it*. Don't dump a laundry list — prioritize by impact.

## Implementation — Copilot CLI

This section describes how the Overseer discovers state in GitHub Copilot CLI. If porting to another tool, replace this section.

### Session Store

Copilot CLI maintains a SQLite database (`session_store`) queryable via the `sql` tool with `database: "session_store"`. Key tables:

| Table | Contents |
|-------|----------|
| `sessions` | id, cwd, repository, branch, summary, created_at, updated_at |
| `turns` | session_id, turn_index, user_message, assistant_response, timestamp |
| `checkpoints` | session_id, checkpoint_number, title, overview, work_done, next_steps |
| `session_files` | session_id, file_path, tool_name (edit/create) |
| `session_refs` | session_id, ref_type (commit/pr/issue), ref_value |
| `search_index` | FTS5 virtual table — use `MATCH` for full-text search |

**Important:** The session store uses keyword search (FTS5), not semantic search. Expand queries with synonyms: for "bug fix" search `bug OR fix OR error OR crash OR regression`.

### Scripts

Helper scripts reduce LLM token usage by handling repetitive queries:

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/session-summary.py` | Query recent session activity | Markdown table of sessions |
| `scripts/skill-inventory.py` | Walk skills/ and extract frontmatter | Markdown table of skills |
| `scripts/daily-summary.py` | Collect a day's session activity | Markdown draft of accomplishments |
| `scripts/usage-patterns.py` | Analyze session history for coaching signals | Markdown report of patterns |

Run with: `python <script> [args]`

### Config Root

The Overseer manages content under the Copilot CLI config root (typically `~/.copilot/`). This directory may be git-tracked. The Overseer should:

- Check `git status` at startup
- Commit changes in logical groups
- Not commit ephemeral content (session-state/ should be gitignored)

### Skill Files

Skills are SKILL.md files in subdirectories of `<config_root>/skills/`. Each has YAML frontmatter with at minimum `name` and `description`. The Overseer maintains these files but does not need to understand the skill loading mechanism — the runtime handles that.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Doing project work from the Overseer | Mixes concerns, clutters session history | Open/resume a dedicated session for that project |
| Reorganizing skills without being asked | Disruptive, loses user's mental model | Suggest improvements, wait for approval |
| Hardcoding audience or format in summaries | Makes the skill non-shareable | Let user or companion skills specify format |
| Reading every session's full turn history | Expensive, slow | Use summaries, checkpoints, and search_index first |
