#!/usr/bin/env python3
"""Query the Copilot CLI session store and output a markdown summary of recent sessions.

Usage:
    python session-summary.py [--days N] [--limit N] [--db PATH]

Defaults:
    --days 3        Show sessions active in the last N days
    --limit 20      Maximum sessions to show
    --db            Auto-detects ~/.copilot/session-store.db
"""

import argparse
import sqlite3
import sys
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
    parser = argparse.ArgumentParser(description="Summarize recent Copilot CLI sessions.")
    parser.add_argument("--days", type=int, default=3, help="Look back N days (default: 3)")
    parser.add_argument("--limit", type=int, default=20, help="Max sessions (default: 20)")
    parser.add_argument("--db", type=str, default=None, help="Path to session-store.db")
    args = parser.parse_args()

    db_path = find_db(args.db)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    sessions = conn.execute("""
        SELECT s.id, s.summary, s.branch, s.repository, s.created_at, s.updated_at,
               (SELECT COUNT(*) FROM turns t WHERE t.session_id = s.id) as turn_count,
               (SELECT COUNT(*) FROM session_files sf WHERE sf.session_id = s.id) as files_touched
        FROM sessions s
        WHERE s.updated_at >= ?
        ORDER BY s.updated_at DESC
        LIMIT ?
    """, (cutoff, args.limit)).fetchall()

    if not sessions:
        print(f"No sessions found in the last {args.days} day(s).")
        return

    print(f"## Sessions active in the last {args.days} day(s)\n")
    print(f"| ID (short) | Summary | Branch | Turns | Files | Last Active |")
    print(f"|------------|---------|--------|-------|-------|-------------|")

    for s in sessions:
        short_id = s["id"][:8]
        summary = (s["summary"] or "*(no summary)*")[:50]
        branch = s["branch"] or "—"
        updated = s["updated_at"][:16] if s["updated_at"] else "—"
        print(f"| `{short_id}` | {summary} | {branch} | {s['turn_count']} | {s['files_touched']} | {updated} |")

    print(f"\n**Total:** {len(sessions)} session(s)")

    # Show sessions with checkpoints
    session_ids = [s["id"] for s in sessions]
    placeholders = ",".join("?" for _ in session_ids)
    checkpoints = conn.execute(f"""
        SELECT c.session_id, c.title, c.checkpoint_number
        FROM checkpoints c
        WHERE c.session_id IN ({placeholders})
        ORDER BY c.session_id, c.checkpoint_number
    """, session_ids).fetchall()

    if checkpoints:
        print("\n### Checkpoints\n")
        for cp in checkpoints:
            short_id = cp["session_id"][:8]
            print(f"- `{short_id}` #{cp['checkpoint_number']}: {cp['title'] or '(untitled)'}")

    conn.close()


if __name__ == "__main__":
    main()
