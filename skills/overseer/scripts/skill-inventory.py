#!/usr/bin/env python3
"""Walk the skills directory and output a markdown inventory of all skills.

Usage:
    python skill-inventory.py [--skills-dir PATH]

Defaults:
    --skills-dir    Auto-detects ~/.copilot/skills/
"""

import argparse
import re
import sys
from pathlib import Path


def find_skills_dir(explicit_path: str | None = None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if p.is_dir():
            return p
        print(f"Error: directory not found: {p}", file=sys.stderr)
        sys.exit(2)
    candidates = [
        Path.home() / ".copilot" / "skills",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    print("Error: skills directory not found. Use --skills-dir to specify.", file=sys.stderr)
    sys.exit(2)


def parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {"_no_frontmatter": True}

    fm = {}
    for line in match.group(1).splitlines():
        kv = line.split(":", 1)
        if len(kv) == 2:
            fm[kv[0].strip()] = kv[1].strip()
    return fm


def count_files(directory: Path) -> int:
    """Count all files recursively in a directory."""
    return sum(1 for f in directory.rglob("*") if f.is_file())


def main():
    parser = argparse.ArgumentParser(description="Inventory Copilot CLI skills.")
    parser.add_argument("--skills-dir", type=str, default=None, help="Path to skills directory")
    args = parser.parse_args()

    skills_dir = find_skills_dir(args.skills_dir)

    skills = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        fm = parse_frontmatter(skill_md) if skill_md.exists() else {"_missing": True}
        file_count = count_files(skill_dir)
        size_kb = round(skill_md.stat().st_size / 1024, 1) if skill_md.exists() else 0

        skills.append({
            "dir": skill_dir.name,
            "name": fm.get("name", "*(missing)*"),
            "description": (fm.get("description", "*(none)*"))[:80],
            "files": file_count,
            "size_kb": size_kb,
            "has_frontmatter": "_no_frontmatter" not in fm and "_missing" not in fm,
        })

    print("## Skill Inventory\n")
    print("| Directory | Name | Description | Files | SKILL.md |")
    print("|-----------|------|-------------|-------|----------|")

    for s in skills:
        fm_badge = "✅" if s["has_frontmatter"] else "⚠️"
        print(f"| `{s['dir']}` | {s['name']} | {s['description']} | {s['files']} | {s['size_kb']} KB {fm_badge} |")

    print(f"\n**Total:** {len(skills)} skill(s), {sum(s['files'] for s in skills)} file(s)")


if __name__ == "__main__":
    main()
