#!/usr/bin/env python3
"""run_tests.py - Test runner for ask_user.py.

For each test*.md in this directory:
1. Parses input lines and expected output from the test file
2. Copies template.md to a temp directory
3. Runs ask_user.py with stdin piped from the input lines
4. Compares the output file to expected result
5. Reports pass/fail with unified diff on failure
"""

import os
import sys
import glob
import shutil
import tempfile
import subprocess
import difflib

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(TESTS_DIR, "..", "..")
TEMPLATE_PATH = os.path.join(SKILL_DIR, "template.md")
ASK_USER_PATH = os.path.join(SKILL_DIR, "ask_user.py")


def parse_test(path):
    """Parse a test file into (input_lines, expected_output_string)."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    delim = '"""'
    parts = content.split(delim)
    if len(parts) < 4:
        raise ValueError(
            f"Need at least two triple-quote blocks in {path}, found {len(parts) - 1}"
        )

    input_block = parts[1]
    expected_block = parts[3]

    # Parse inputs: each non-empty line, strip trailing literal \n
    inputs = []
    for line in input_block.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.endswith("\\n"):
            stripped = stripped[:-2]
        inputs.append(stripped)

    # Strip one leading/trailing newline (artifact of delimiter placement)
    expected = expected_block
    if expected.startswith("\n"):
        expected = expected[1:]
    if expected.endswith("\n"):
        expected = expected[:-1]

    return inputs, expected


def run_test(test_path):
    """Run a single test. Returns (passed: bool, detail: str)."""
    try:
        inputs, expected = parse_test(test_path)
    except ValueError as e:
        return False, f"PARSE ERROR: {e}"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_template = os.path.join(tmpdir, "template.md")
        shutil.copy2(TEMPLATE_PATH, tmp_template)

        stdin_text = "\n".join(inputs) + "\n"

        try:
            result = subprocess.run(
                [sys.executable, ASK_USER_PATH, tmp_template],
                input=stdin_text,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT (30s) - likely waiting for input not provided"

        if result.returncode != 0:
            return False, (
                f"EXIT CODE {result.returncode}\n"
                f"stderr:\n{result.stderr}\n"
                f"stdout:\n{result.stdout}"
            )

        # ask_user.py overwrites the template file with filled output
        try:
            with open(tmp_template, encoding="utf-8") as f:
                actual = f.read()
        except FileNotFoundError:
            return False, "Output file not found - ask_user.py may not have written it"

        # Normalize trailing newline
        actual = actual.rstrip("\n")
        expected = expected.rstrip("\n")

        if actual == expected:
            return True, ""

        diff = difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
        detail = "\n".join(diff)
        detail += "\n\n--- ACTUAL OUTPUT ---\n" + actual + "\n--- END ---"
        return False, detail


def main():
    test_files = sorted(glob.glob(os.path.join(TESTS_DIR, "test*.md")))
    if not test_files:
        print("No test*.md files found in", TESTS_DIR)
        sys.exit(1)

    passed = 0
    failed = 0

    for test_path in test_files:
        name = os.path.basename(test_path)
        ok, detail = run_test(test_path)
        if ok:
            print(f"  \u2705 {name}")
            passed += 1
        else:
            print(f"  \u274c {name}")
            if detail:
                for line in detail.splitlines():
                    print(f"     {line}")
            failed += 1

    print(f"\n  {passed} passed, {failed} failed out of {passed + failed}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
