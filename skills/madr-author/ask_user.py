#!/usr/bin/env python3
"""ask_user.py — Interactive MADR ADR authoring from template.

Reads template.md, parses <<< >>> placeholders, prompts the user
for each field, and writes a filled-in ADR.

Placeholder syntax:
  <<< prompt [[default: x]] >>>              — simple field
  <<< [[OPTIONAL]] prompt >>>                — Before asking, ask whether user wants to include it
  <<< LABEL [[REPEATED]] | prompt >>>        — After each each answer, ask if user wants to add another.
  <<< FOREACH $COLLECTION$ as "$VAR" >>>     — loop over collected items
  <<< $VAR >>>                               — substitute variable
  {env.$USER}, {YYYY-MM-DD}                  — resolved defaults

Usage:
    python ask_user.py [output_path]
"""

import re
import os
import sys
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) != 2:
    raise Exception("Output path argument required")
TEMPLATE_PATH = sys.argv[1]

PH_RE = re.compile(r"<<<\s*(.*?)\s*>>>")


def resolve_default(raw):
    """Resolve magic default values like {YYYY-MM-DD} and {env.$USER}."""
    if not raw:
        return None
    if "{YYYY-MM-DD}" in raw:
        return date.today().isoformat()
    if "{env.$USER}" in raw:
        return os.environ.get("USER") or os.environ.get("USERNAME", "unknown")
    return raw.strip()


def parse_ph(raw):
    """Parse content inside <<< >>>. Returns a dict describing the placeholder."""
    c = raw.strip()

    # FOREACH $COLLECTION$ as "$VAR"
    m = re.match(r'FOREACH\s+\$(\w+)\$\s+as\s+"\$(\w+)\$?"', c)
    if m:
        return {"type": "foreach", "col": m.group(1), "var": m.group(2)}

    # Variable reference: $NAME$ or $NAME
    m = re.match(r"\$(\w+)\$?$", c)
    if m:
        return {"type": "var", "name": m.group(1)}

    # Field: LABEL [[mods]] | prompt   OR   just prompt text
    m = re.match(r"^([A-Z_]+)\s*((?:\[\[.*?\]\]\s*)*)\|\s*(.*)", c, re.DOTALL)
    if m:
        label = m.group(1)
        mod_zone = m.group(2) + " " + m.group(3)
        prompt = m.group(3)
    else:
        label = None
        mod_zone = c
        prompt = c

    optional = bool(re.search(r"\[\[OPTIONAL\]\]", mod_zone))
    repeated = bool(re.search(r"\[\[REPEATED\]\]", mod_zone))
    dm = re.search(r"\[\[default:\s*(.*?)\]\]", mod_zone)
    default = resolve_default(dm.group(1)) if dm else None

    # Strip modifier tags from the prompt the user sees
    prompt = re.sub(r"\[\[.*?\]\]\s*", "", prompt).strip()

    return {
        "type": "field",
        "label": label,
        "prompt": prompt,
        "optional": optional,
        "repeated": repeated,
        "default": default,
    }


def ask(prompt, default=None, optional=False, repeated=False, context=None):
    """Prompt the user interactively. Returns str, list[str], or None."""
    if context:
        prompt = prompt.replace("{$OPTION}", context)

    if repeated:
        print(f"\n  {prompt}")
        print("  (one per line, blank line when done)")
        items = []
        while True:
            item = input("  • ").strip()
            if not item:
                if items:
                    break
                print("    (need at least one)")
                continue
            items.append(item)
        return items

    tag = "[optional] " if optional else ""
    suf = f" [{default}]" if default else ""
    while True:
        val = input(f"\n  {tag}{prompt}{suf}: ").strip()
        if not val and default:
            return default
        if not val and optional:
            return None
        if val:
            return val
        print("    (required)")


def process_line(line, store, fvar=None, fval=None):
    """Process one template line. Returns list of output lines,
    or [('FOREACH', info)] if a FOREACH directive is encountered."""
    matches = list(PH_RE.finditer(line))
    if not matches:
        return [line]

    # Single placeholder — check for special types
    if len(matches) == 1:
        p = parse_ph(matches[0].group(1))
        if p["type"] == "foreach":
            return [("FOREACH", p)]
        if p["type"] == "field" and p.get("repeated"):
            ctx = fval if fvar else None
            items = ask(p["prompt"], repeated=True, context=ctx)
            if p.get("label"):
                store[p["label"]] = items
            pre = line[: matches[0].start()]
            return [f"{pre}{item}" for item in items]

    # General case: replace all placeholders right-to-left to preserve indices
    result = line
    for m in reversed(matches):
        p = parse_ph(m.group(1))

        if p["type"] == "var":
            val = fval if (fvar and p["name"] == fvar) else store.get(p["name"], "")

        elif p["type"] == "field":
            ctx = fval if fvar else None
            val = ask(
                p["prompt"],
                default=p.get("default"),
                optional=p.get("optional"),
                context=ctx,
            )
            if p.get("label"):
                store[p["label"]] = val
            if val is None:
                return []  # optional field declined — drop entire line
        else:
            continue

        result = result[: m.start()] + str(val) + result[m.end() :]

    return [result]


def flush_output(output, dest):
    """Write current accumulated output to file after each answer."""
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(output) + "\n")


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else None

    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    if not dest:
        dest = input("\n  Save to [adr.md]: ").strip() or "adr.md"

    print("\n  ╔══════════════════════════╗")
    print("  ║     MADR ADR Author      ║")
    print("  ╚══════════════════════════╝\n")

    store = {}
    lines = template.split("\n")
    output = []
    i = 0

    while i < len(lines):
        result = process_line(lines[i], store)

        # FOREACH directive — expand body for each item in the collection
        if result and isinstance(result[0], tuple) and result[0][0] == "FOREACH":
            info = result[0][1]
            body = lines[i + 1 :]
            for item in store.get(info["col"], []):
                print(f"\n  {'─' * 40}")
                print(f"  {item}")
                print(f"  {'─' * 40}")
                for bline in body:
                    output.extend(process_line(bline, store, info["var"], item))
                    flush_output(output, dest)
            break  # FOREACH consumes the rest of the template

        output.extend(result)
        flush_output(output, dest)
        i += 1

    print(f"\n  ✅ Written to {dest}\n")


if __name__ == "__main__":
    main()
