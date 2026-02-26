#!/usr/bin/env python3
"""Analyze session history for usage patterns that suggest skill improvements.

Surfaces:
  - Repeated topics across sessions (potential skills)
  - Frequently edited files (hotspots)
  - Sessions with high turn counts (complex work, maybe needs better priming)
  - Stale sessions (started but abandoned)
  - Skill loading frequency (which skills are actually used)

Usage:
    python usage-patterns.py [--days N] [--db PATH]

Defaults:
    --days 14       Analyze the last N days
    --db            Auto-detects ~/.copilot/session-store.db
"""

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def find_db(explicit_path: str | None = None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
        print(f"Error: DB not found at {p}", file=sys.stderr)
        sys.exit(2)
    candidates = [
        Path.home() / ".copilot" / "session-store.db",
    ]
    for c in candidates:
        if c.exists():
            return c
    print("Error: session-store.db not found. Use --db to specify path.", file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Analyze AI usage patterns.")
    parser.add_argument("--days", type=int, default=14, help="Look back N days (default: 14)")
    parser.add_argument("--db", type=str, default=None, help="Path to session-store.db")
    args = parser.parse_args()

    db_path = find_db(args.db)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    print(f"# Usage Pattern Analysis — last {args.days} days\n")

    # 1. Session volume and complexity
    sessions = conn.execute("""
        SELECT s.id, s.summary, s.branch, s.created_at, s.updated_at,
               (SELECT COUNT(*) FROM turns t WHERE t.session_id = s.id) as turn_count,
               (SELECT COUNT(*) FROM session_files sf WHERE sf.session_id = s.id) as files_touched
        FROM sessions s
        WHERE s.updated_at >= ?
        ORDER BY s.updated_at DESC
    """, (cutoff,)).fetchall()

    total = len(sessions)
    if total == 0:
        print("No sessions found in this period.")
        return

    with_summary = sum(1 for s in sessions if s["summary"])
    avg_turns = sum(s["turn_count"] for s in sessions) / total if total else 0
    high_turn = [s for s in sessions if s["turn_count"] > 20]
    empty = [s for s in sessions if s["turn_count"] == 0]

    print("## Session Overview\n")
    print(f"- **Total sessions:** {total}")
    print(f"- **With summaries:** {with_summary} ({round(with_summary/total*100)}%)")
    print(f"- **Average turns:** {avg_turns:.1f}")
    print(f"- **High-complexity (>20 turns):** {len(high_turn)}")
    print(f"- **Empty (0 turns):** {len(empty)}")

    if high_turn:
        print(f"\n### High-Complexity Sessions\n")
        print("| Turns | Summary |")
        print("|-------|---------|")
        for s in sorted(high_turn, key=lambda x: x["turn_count"], reverse=True)[:10]:
            summary = (s["summary"] or "*(none)*")[:60]
            print(f"| {s['turn_count']} | {summary} |")

    # 2. Frequently edited files (hotspots)
    file_edits = conn.execute("""
        SELECT sf.file_path, COUNT(DISTINCT sf.session_id) as session_count
        FROM session_files sf
        JOIN sessions s ON sf.session_id = s.id
        WHERE s.updated_at >= ? AND sf.tool_name IN ('edit', 'create')
        GROUP BY sf.file_path
        HAVING session_count > 1
        ORDER BY session_count DESC
        LIMIT 15
    """, (cutoff,)).fetchall()

    if file_edits:
        print("\n## File Hotspots (edited in multiple sessions)\n")
        print("| Sessions | File |")
        print("|----------|------|")
        for f in file_edits:
            short_path = f["file_path"].replace(str(Path.home()), "~")
            print(f"| {f['session_count']} | `{short_path}` |")

    # 3. Branch activity (what projects are active)
    branches = conn.execute("""
        SELECT s.branch, COUNT(*) as session_count,
               MAX(s.updated_at) as last_active
        FROM sessions s
        WHERE s.updated_at >= ? AND s.branch IS NOT NULL AND s.branch != ''
        GROUP BY s.branch
        ORDER BY session_count DESC
        LIMIT 10
    """, (cutoff,)).fetchall()

    if branches:
        print("\n## Active Branches\n")
        print("| Branch | Sessions | Last Active |")
        print("|--------|----------|-------------|")
        for b in branches:
            print(f"| `{b['branch']}` | {b['session_count']} | {b['last_active'][:10]} |")

    # 4. Repeated words in first user messages (topic clustering)
    first_messages = conn.execute("""
        SELECT t.user_message
        FROM turns t
        JOIN sessions s ON t.session_id = s.id
        WHERE t.turn_index = 0 AND s.updated_at >= ? AND t.user_message IS NOT NULL
    """, (cutoff,)).fetchall()

    if first_messages:
        # Simple word frequency (skip common words)
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through", "during",
            "before", "after", "and", "but", "or", "nor", "not", "so", "yet",
            "it", "its", "this", "that", "these", "those", "i", "you", "we",
            "they", "he", "she", "my", "your", "our", "their", "me", "us",
            "him", "her", "them", "what", "which", "who", "whom", "how", "when",
            "where", "why", "if", "then", "else", "all", "each", "every", "any",
            "some", "no", "about", "up", "out", "just", "also", "like", "make",
            "get", "set", "use", "need", "want", "let", "know", "see", "look",
            "think", "go", "come", "take", "give", "tell", "say", "put", "run",
        }
        words: Counter[str] = Counter()
        for msg in first_messages:
            for word in msg["user_message"].lower().split():
                cleaned = "".join(c for c in word if c.isalnum())
                if len(cleaned) > 3 and cleaned not in stop_words:
                    words[cleaned] += 1

        frequent = [(w, c) for w, c in words.most_common(25) if c > 1]
        if frequent:
            print("\n## Recurring Topics (from first messages)\n")
            print("| Word | Occurrences |")
            print("|------|-------------|")
            for word, count in frequent:
                print(f"| {word} | {count} |")

    # 5. Refs created (commits, PRs, issues)
    refs = conn.execute("""
        SELECT sr.ref_type, COUNT(*) as count
        FROM session_refs sr
        JOIN sessions s ON sr.session_id = s.id
        WHERE s.updated_at >= ?
        GROUP BY sr.ref_type
        ORDER BY count DESC
    """, (cutoff,)).fetchall()

    if refs:
        print("\n## References Created\n")
        for r in refs:
            print(f"- **{r['ref_type']}:** {r['count']}")

    print(f"\n---\n*Analysis covers {total} sessions from {cutoff[:10]} to now.*")
    conn.close()


if __name__ == "__main__":
    main()
