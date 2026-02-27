#!/usr/bin/env python3
"""Lint SKILL.md files against the skill-authoring pattern.

Scans skill directories for SKILL.md files and checks them against
the terse-skills authoring guidelines. Reports exact violations and
heuristic warnings with per-skill scores.

Usage:
    python lint_skills.py [DIR ...]

If no directories given, scans:
    ~/.copilot/skills
    + any paths in skill_directories from ~/.copilot/config.json
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── thresholds ──────────────────────────────────────────────────────
TOKEN_WARN = 2000  # soft limit (guideline says <2K)
TOKEN_FAIL = 3000  # hard limit (retrofitting trigger)
CODE_BLOCK_LINE_LIMIT = 20  # lines in a fenced block before flagging
FILLER_PHRASES = [
    r"\bthis skill\b",
    r"\bis designed to\b",
    r"\bhelps you\b",
    r"\bprovides a\b",
    r"\bthis skill provides\b",
    r"\bthis skill ensures\b",
    r"\bthis skill is\b",
]
HUMAN_DOC_HEADINGS = re.compile(
    r"^#{1,3}\s*(Background|Overview|Introduction|Purpose)\s*$", re.IGNORECASE
)
DESCRIPTION_OVERLAP_THRESHOLD = 0.45  # keyword overlap ratio
PROSE_RATIO_THRESHOLD = 0.60  # paragraph lines / total content lines


@dataclass
class Finding:
    level: str  # "FAIL", "WARN", "INFO"
    check: str
    message: str


@dataclass
class SkillReport:
    path: Path
    name: str = ""
    findings: list = field(default_factory=list)

    @property
    def fails(self):
        return [f for f in self.findings if f.level == "FAIL"]

    @property
    def warns(self):
        return [f for f in self.findings if f.level == "WARN"]


def approx_tokens(text: str) -> int:
    """Rough token estimate: chars/4 for English markdown."""
    return len(text) // 4


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body. Returns (meta_dict, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    meta = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip("'\"")
    # crude nested parse for metadata.readme
    if "metadata" in meta and meta["metadata"] == "":
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("readme:"):
                meta["metadata.readme"] = stripped.split(":", 1)[1].strip()
    body = text[end + 3:].strip()
    return meta, body


def extract_keywords(text: str) -> set:
    """Extract lowercase alphanumeric tokens >=3 chars."""
    return {w.lower() for w in re.findall(r"[a-zA-Z0-9_-]{3,}", text)}


def count_code_block_lines(body: str) -> list[int]:
    """Return list of line-counts for each fenced code block."""
    blocks = []
    in_block = False
    count = 0
    for line in body.splitlines():
        if line.strip().startswith("```"):
            if in_block:
                blocks.append(count)
                in_block = False
                count = 0
            else:
                in_block = True
                count = 0
        elif in_block:
            count += 1
    return blocks


def prose_ratio(body: str) -> float:
    """Ratio of plain-paragraph lines to total non-empty content lines."""
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines:
        return 0.0
    structured = 0
    for l in lines:
        s = l.strip()
        if (
            s.startswith("#")
            or s.startswith("|")
            or s.startswith("-")
            or s.startswith("*")
            or s.startswith("```")
            or s.startswith(">")
            or re.match(r"^\d+\.", s)
        ):
            structured += 1
    prose = len(lines) - structured
    return prose / len(lines)


def lint_skill(skill_dir: Path) -> SkillReport:
    skill_md = skill_dir / "SKILL.md"
    report = SkillReport(path=skill_md)

    if not skill_md.exists():
        report.findings.append(Finding("INFO", "missing", "No SKILL.md found"))
        return report

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    meta, body = parse_frontmatter(text)
    report.name = meta.get("name", skill_dir.name)

    # ── Exact checks ───────────────────────────────────────────────

    # 1. Frontmatter: name
    if not meta.get("name"):
        report.findings.append(Finding("FAIL", "no-name", "Missing `name` in frontmatter"))

    # 2. Frontmatter: description
    desc = meta.get("description", "")
    if not desc:
        report.findings.append(Finding("FAIL", "no-description", "Missing `description` in frontmatter"))

    # 3. metadata.readme
    has_readme_meta = "metadata.readme" in meta or "readme" in meta.get("metadata", "")
    readme_exists = (skill_dir / "README.md").exists()
    if not readme_exists:
        report.findings.append(Finding("FAIL", "no-readme", "No README.md alongside SKILL.md"))
    if readme_exists and not has_readme_meta:
        report.findings.append(
            Finding("WARN", "no-readme-ref", "README.md exists but no `metadata.readme` in frontmatter")
        )

    # 4. Token count
    tokens = approx_tokens(body)
    if tokens > TOKEN_FAIL:
        report.findings.append(
            Finding("FAIL", "token-count", f"Body ≈{tokens} tokens (limit: {TOKEN_FAIL})")
        )
    elif tokens > TOKEN_WARN:
        report.findings.append(
            Finding("WARN", "token-count", f"Body ≈{tokens} tokens (soft limit: {TOKEN_WARN})")
        )

    # 5. Human-doc headings
    for i, line in enumerate(body.splitlines(), 1):
        if HUMAN_DOC_HEADINGS.match(line.strip()):
            report.findings.append(
                Finding("FAIL", "human-heading", f'Human-doc heading "{line.strip()}" (line {i})')
            )

    # 6. Large inline code blocks
    block_sizes = count_code_block_lines(body)
    for i, size in enumerate(block_sizes):
        if size > CODE_BLOCK_LINE_LIMIT:
            report.findings.append(
                Finding("WARN", "large-code-block", f"Code block #{i+1} is {size} lines (limit: {CODE_BLOCK_LINE_LIMIT})")
            )

    # ── Heuristic checks ──────────────────────────────────────────

    # 7. Filler preamble phrases
    body_lower = body.lower()
    for pattern in FILLER_PHRASES:
        if re.search(pattern, body_lower):
            report.findings.append(
                Finding("WARN", "filler-phrase", f"Filler phrase detected: {pattern}")
            )
            break  # one is enough to flag

    # 8. Description / body keyword overlap
    if desc:
        desc_kw = extract_keywords(desc)
        body_kw = extract_keywords(body)
        if desc_kw and body_kw:
            overlap = len(desc_kw & body_kw) / len(desc_kw)
            if overlap > DESCRIPTION_OVERLAP_THRESHOLD:
                report.findings.append(
                    Finding(
                        "WARN",
                        "desc-overlap",
                        f"Description keywords {overlap:.0%} overlap with body (may be restating instead of discriminating)",
                    )
                )

    # 9. Prose ratio
    pr = prose_ratio(body)
    if pr > PROSE_RATIO_THRESHOLD:
        report.findings.append(
            Finding("WARN", "high-prose", f"Prose ratio {pr:.0%} (threshold: {PROSE_RATIO_THRESHOLD:.0%})")
        )

    return report


def discover_skill_dirs(roots: list[Path]) -> list[Path]:
    """Find all directories containing SKILL.md, recursively."""
    dirs = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("SKILL.md"):
            dirs.append(path.parent)
    return sorted(set(dirs))


def default_roots() -> list[Path]:
    """Get skill directories from ~/.copilot/config.json + default."""
    roots = [Path.home() / ".copilot" / "skills"]
    config_path = Path.home() / ".copilot" / "config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            for d in cfg.get("skill_directories", []):
                roots.append(Path(d))
        except (json.JSONDecodeError, KeyError):
            pass
    return roots


def main():
    if len(sys.argv) > 1:
        roots = [Path(a) for a in sys.argv[1:]]
    else:
        roots = default_roots()

    skill_dirs = discover_skill_dirs(roots)
    if not skill_dirs:
        print("No SKILL.md files found.")
        return

    reports = [lint_skill(d) for d in skill_dirs]

    # ── Output ─────────────────────────────────────────────────────
    total_fail = 0
    total_warn = 0

    for r in reports:
        if not r.findings:
            continue
        label = r.name or r.path.parent.name
        fails = r.fails
        warns = r.warns
        total_fail += len(fails)
        total_warn += len(warns)

        icon = "❌" if fails else "⚠️" if warns else "✅"
        print(f"\n{icon}  {label}  ({r.path})")
        for f in r.findings:
            tag = {"FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}[f.level]
            print(f"   {tag} [{f.check}] {f.message}")

    # Clean skills
    clean = [r for r in reports if not r.findings]
    if clean:
        print(f"\n✅  Clean ({len(clean)}):", ", ".join(r.name or r.path.parent.name for r in clean))

    print(f"\n{'─'*60}")
    print(f"Scanned {len(reports)} skills: {total_fail} errors, {total_warn} warnings")
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()
