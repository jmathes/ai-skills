#!/usr/bin/env python3
"""Generate a draft daily summary from session activity.

Usage:
    python daily-summary.py [--date YYYY-MM-DD] [--db PATH]

Defaults:
    --date      Today (Pacific time, UTC-8)
    --db        Auto-detects ~/.copilot/session-store.db
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PST = timezone(timedelta(hours=-8))


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
    parser = argparse.ArgumentParser(description="Generate daily work summary from sessions.")
    parser.add_argument("--date", type=str, default=None, help="Date in YYYY-MM-DD (default: today PST)")
    parser.add_argument("--db", type=str, default=None, help="Path to session-store.db")
    args = parser.parse_args()

    db_path = find_db(args.db)

    if args.date:
        target_date = args.date
    else:
        target_date = datetime.now(PST).strftime("%Y-%m-%d")

    # Convert PST date to UTC range
    day_start_pst = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=PST)
    day_start_utc = day_start_pst.astimezone(timezone.utc).isoformat()
    day_end_utc = (day_start_pst + timedelta(days=1)).astimezone(timezone.utc).isoformat()

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # Sessions active during this day
    sessions = conn.execute("""
        SELECT s.id, s.summary, s.branch, s.repository, s.created_at, s.updated_at,
               (SELECT COUNT(*) FROM turns t WHERE t.session_id = s.id) as turn_count
        FROM sessions s
        WHERE s.updated_at >= ? AND s.created_at < ?
        ORDER BY s.updated_at ASC
    """, (day_start_utc, day_end_utc)).fetchall()

    if not sessions:
        print(f"No sessions found for {target_date}.")
        return

    print(f"# Daily Summary — {target_date}\n")

    # Get checkpoints for these sessions (richest summary data)
    session_ids = [s["id"] for s in sessions]
    placeholders = ",".join("?" for _ in session_ids)

    checkpoints = conn.execute(f"""
        SELECT c.session_id, c.title, c.overview, c.work_done
        FROM checkpoints c
        WHERE c.session_id IN ({placeholders})
        ORDER BY c.session_id, c.checkpoint_number DESC
    """, session_ids).fetchall()

    cp_by_session = {}
    for cp in checkpoints:
        if cp["session_id"] not in cp_by_session:
            cp_by_session[cp["session_id"]] = cp

    # Get files edited
    files_edited = conn.execute(f"""
        SELECT sf.session_id, sf.file_path, sf.tool_name
        FROM session_files sf
        WHERE sf.session_id IN ({placeholders}) AND sf.tool_name IN ('edit', 'create')
    """, session_ids).fetchall()

    files_by_session = {}
    for f in files_edited:
        files_by_session.setdefault(f["session_id"], []).append(f["file_path"])

    # Get refs (commits, PRs, issues)
    refs = conn.execute(f"""
        SELECT sr.session_id, sr.ref_type, sr.ref_value
        FROM session_refs sr
        WHERE sr.session_id IN ({placeholders})
    """, session_ids).fetchall()

    refs_by_session = {}
    for r in refs:
        refs_by_session.setdefault(r["session_id"], []).append(
            f"{r['ref_type']}:{r['ref_value']}"
        )

    # Output
    for s in sessions:
        sid = s["id"]
        summary = s["summary"] or "*(no summary)*"
        branch = s["branch"] or "—"

        print(f"## {summary}\n")
        print(f"- **Session:** `{sid[:8]}`")
        print(f"- **Branch:** {branch}")
        print(f"- **Turns:** {s['turn_count']}")

        cp = cp_by_session.get(sid)
        if cp:
            if cp["work_done"]:
                print(f"\n**Work done:**\n{cp['work_done']}")
            elif cp["overview"]:
                print(f"\n**Overview:**\n{cp['overview']}")

        files = files_by_session.get(sid, [])
        if files:
            print(f"\n**Files touched:** {len(files)}")
            for f in files[:10]:
                print(f"  - `{f}`")
            if len(files) > 10:
                print(f"  - *...and {len(files) - 10} more*")

        session_refs = refs_by_session.get(sid, [])
        if session_refs:
            print(f"\n**Refs:** {', '.join(session_refs)}")

        print()

    print(f"---\n**Total:** {len(sessions)} session(s) active on {target_date}")
    conn.close()


if __name__ == "__main__":
    main()
