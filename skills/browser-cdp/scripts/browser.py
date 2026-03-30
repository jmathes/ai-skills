"""
browser.py - Drive a separate Edge window via Chrome DevTools Protocol.

Launches Edge with a copy of the user's auth cookies and bookmarks,
connects via CDP on a remote-debugging port, and exposes commands:

  python browser.py launch          # start agent Edge with copied auth
  python browser.py navigate <url>  # go to a URL
  python browser.py screenshot [path]  # capture PNG
  python browser.py text            # get visible text content
  python browser.py tabs            # list open tabs
  python browser.py tab <id>        # switch to tab
  python browser.py click <selector> # click an element (CSS selector)
  python browser.py type <selector> <text>  # type into an element
  python browser.py eval <js>       # evaluate JS, return result
  python browser.py close           # close the agent Edge
  python browser.py status          # is agent Edge running?

Auth: copies Cookies, Login Data, Bookmarks from main Edge profile
into a separate agent profile dir. Main Edge is never touched.
"""

import argparse
import base64
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Suppress pychrome's noisy thread errors on tab close
logging.getLogger("pychrome").setLevel(logging.CRITICAL)
import threading
_original_excepthook = threading.excepthook
def _quiet_excepthook(args):
    if args.exc_type == json.JSONDecodeError:
        return  # pychrome recv loop noise during tab close
    _original_excepthook(args)
threading.excepthook = _quiet_excepthook

try:
    import pychrome
except ImportError:
    print("pip install pychrome", file=sys.stderr)
    sys.exit(1)

# --- Config ---

CDP_PORT = 9223  # not 9222, to avoid conflict with anything else
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_EXE):
    EDGE_EXE = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

MAIN_PROFILE = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Edge" / "User Data"
AGENT_PROFILE = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Edge" / "Agent Data"
SCREENSHOT_DIR = Path(r"C:\dev\screenshots\browser")

# Files to copy from main profile for auth sharing
AUTH_FILES = [
    ("Default/Network/Cookies", "Default/Network/Cookies"),
    ("Default/Network/Cookies-journal", "Default/Network/Cookies-journal"),
    ("Default/Login Data", "Default/Login Data"),
    ("Default/Login Data-journal", "Default/Login Data-journal"),
    ("Default/Bookmarks", "Default/Bookmarks"),
    ("Default/Web Data", "Default/Web Data"),  # autofill, search engines
]

SQLITE_FILES = {"Cookies", "Login Data", "Web Data"}


# --- CDP helpers ---

def get_browser():
    """Get a pychrome Browser connected to agent Edge."""
    return pychrome.Browser(url=CDP_URL)


def is_running():
    try:
        browser = get_browser()
        browser.version()
        return True
    except Exception:
        return False


def _copy_sqlite_db(src, dst):
    """Copy a SQLite database safely, with timeout for locked DBs."""
    import sqlite3
    import threading

    success = [False]
    error = [None]

    def _do_backup():
        try:
            src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=3)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst_conn = sqlite3.connect(str(dst))
            src_conn.backup(dst_conn)
            src_conn.close()
            dst_conn.close()
            success[0] = True
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=_do_backup)
    t.start()
    t.join(timeout=5)
    if t.is_alive() or not success[0]:
        raise OSError(error[0] or "sqlite backup timed out")


# --- Commands ---

def cmd_launch(args):
    """Launch agent Edge with copied auth."""
    if is_running():
        print(f"Agent Edge already running on port {CDP_PORT}")
        return

    # Create agent profile dir
    agent_default = AGENT_PROFILE / "Default" / "Network"
    agent_default.mkdir(parents=True, exist_ok=True)
    (AGENT_PROFILE / "Default").mkdir(parents=True, exist_ok=True)

    # Copy auth files: raw copy first (fast), sqlite backup as fallback
    copied = 0
    skipped = []
    for src_rel, dst_rel in AUTH_FILES:
        src = MAIN_PROFILE / src_rel.replace("/", os.sep)
        dst = AGENT_PROFILE / dst_rel.replace("/", os.sep)
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        basename = Path(src_rel).name
        # Try raw copy first (works for unlocked files)
        try:
            with open(src, "rb") as f:
                data = f.read()
            with open(dst, "wb") as f:
                f.write(data)
            copied += 1
            continue
        except (PermissionError, OSError):
            pass
        # Fallback: sqlite backup with timeout (for locked SQLite DBs)
        if basename in SQLITE_FILES:
            try:
                _copy_sqlite_db(src, dst)
                copied += 1
                continue
            except Exception:
                pass
        skipped.append(basename)

    print(f"Copied {copied} auth files to agent profile")
    if skipped:
        print(f"  Locked by Edge (normal): {', '.join(skipped)}", file=sys.stderr)
        print("  Agent Edge will use its own cookies. Log in once if needed.", file=sys.stderr)

    # Launch Edge
    cmd = [
        EDGE_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={AGENT_PROFILE}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=msEdgeEnableNurturingFramework",
    ]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    # Wait for CDP to come up
    for _ in range(30):
        if is_running():
            print(f"Agent Edge running on port {CDP_PORT}")
            return
        time.sleep(0.5)

    print("Edge started but CDP not responding after 15s", file=sys.stderr)
    sys.exit(1)


def cmd_navigate(args):
    """Navigate to a URL in a clean tab."""
    if not is_running():
        print("Agent Edge not running. Run: browser.py launch", file=sys.stderr)
        sys.exit(1)

    browser = get_browser()

    # Open a new tab with the target URL
    new_tab = browser.new_tab(url=args.url)

    # Close all other tabs
    for tab in browser.list_tab():
        if tab.id != new_tab.id:
            browser.close_tab(tab)

    # Wait for page to load
    new_tab.start()
    new_tab.call_method("Page.enable")
    loaded = [False]

    def on_load(**kwargs):
        loaded[0] = True

    new_tab.set_listener("Page.loadEventFired", on_load)
    deadline = time.time() + 20
    while not loaded[0] and time.time() < deadline:
        new_tab.wait(0.5)
    new_tab.stop()

    # Settle after redirects
    time.sleep(1)
    print(f"Navigated to {args.url}")


def cmd_screenshot(args):
    """Capture a screenshot."""
    if not is_running():
        print("Agent Edge not running.", file=sys.stderr)
        sys.exit(1)

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    if args.path:
        out_path = Path(args.path)
    else:
        ts = time.strftime("%Y-%m-%dT%H%M%S")
        out_path = SCREENSHOT_DIR / f"{ts}.png"

    browser = get_browser()
    tab = browser.list_tab()[0]
    tab.start()
    result = tab.call_method("Page.captureScreenshot", format="png")
    tab.stop()

    img_data = base64.b64decode(result["data"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_data)
    print(str(out_path))


def cmd_text(args):
    """Get visible text content of the page."""
    if not is_running():
        print("Agent Edge not running.", file=sys.stderr)
        sys.exit(1)

    browser = get_browser()
    tab = browser.list_tab()[0]
    tab.start()
    result = tab.call_method(
        "Runtime.evaluate",
        expression="document.body.innerText",
        returnByValue=True,
    )
    tab.stop()

    text = result.get("result", {}).get("value", "")
    print(text)


def cmd_tabs(args):
    """List open tabs."""
    if not is_running():
        print("Agent Edge not running.", file=sys.stderr)
        sys.exit(1)

    browser = get_browser()
    for i, tab in enumerate(browser.list_tab()):
        # Activate and query for title
        browser.activate_tab(tab)
        tab.start()
        result = tab.call_method(
            "Runtime.evaluate",
            expression="document.title",
            returnByValue=True,
        )
        url_result = tab.call_method(
            "Runtime.evaluate",
            expression="window.location.href",
            returnByValue=True,
        )
        tab.stop()
        title = result.get("result", {}).get("value", "(untitled)")
        url = url_result.get("result", {}).get("value", "")
        print(f"[{i}] {title}  {url}")


def cmd_tab(args):
    """Switch to a tab by index."""
    if not is_running():
        print("Agent Edge not running.", file=sys.stderr)
        sys.exit(1)

    browser = get_browser()
    tabs = browser.list_tab()
    idx = int(args.index)
    if idx >= len(tabs):
        print(f"Tab {idx} not found. {len(tabs)} tabs open.", file=sys.stderr)
        sys.exit(1)

    browser.activate_tab(tabs[idx])
    print(f"Switched to tab {idx}")


def cmd_click(args):
    """Click an element by CSS selector."""
    if not is_running():
        print("Agent Edge not running.", file=sys.stderr)
        sys.exit(1)

    browser = get_browser()
    tab = browser.list_tab()[0]
    tab.start()
    result = tab.call_method(
        "Runtime.evaluate",
        expression=f"""
            (() => {{
                const el = document.querySelector({json.dumps(args.selector)});
                if (!el) return 'NOT_FOUND';
                el.click();
                return 'OK';
            }})()
        """,
        returnByValue=True,
    )
    tab.stop()

    val = result.get("result", {}).get("value", "")
    if val == "NOT_FOUND":
        print(f"Element not found: {args.selector}", file=sys.stderr)
        sys.exit(1)
    print(f"Clicked: {args.selector}")


def cmd_type(args):
    """Type text into an element."""
    if not is_running():
        print("Agent Edge not running.", file=sys.stderr)
        sys.exit(1)

    browser = get_browser()
    tab = browser.list_tab()[0]
    tab.start()
    result = tab.call_method(
        "Runtime.evaluate",
        expression=f"""
            (() => {{
                const el = document.querySelector({json.dumps(args.selector)});
                if (!el) return 'NOT_FOUND';
                el.focus();
                return 'OK';
            }})()
        """,
        returnByValue=True,
    )
    val = result.get("result", {}).get("value", "")
    if val == "NOT_FOUND":
        tab.stop()
        print(f"Element not found: {args.selector}", file=sys.stderr)
        sys.exit(1)

    tab.call_method("Input.insertText", text=args.text)
    tab.stop()
    print(f"Typed into: {args.selector}")


def cmd_eval(args):
    """Evaluate JavaScript and print the result."""
    if not is_running():
        print("Agent Edge not running.", file=sys.stderr)
        sys.exit(1)

    browser = get_browser()
    tab = browser.list_tab()[0]
    tab.start()
    result = tab.call_method(
        "Runtime.evaluate",
        expression=args.js,
        returnByValue=True,
    )
    tab.stop()

    val = result.get("result", {}).get("value", "")
    print(json.dumps(val, indent=2) if isinstance(val, (dict, list)) else str(val))


def cmd_close(args):
    """Close the agent Edge."""
    if not is_running():
        print("Agent Edge not running.")
        return

    try:
        browser = get_browser()
        # Close all tabs, which shuts down the browser
        for tab in browser.list_tab():
            browser.close_tab(tab)
    except Exception:
        pass

    print("Agent Edge closed")


def cmd_status(args):
    """Check if agent Edge is running."""
    if is_running():
        browser = get_browser()
        info = browser.version()
        print(f"Running: {info.get('Browser', 'unknown')}")
        tabs = browser.list_tab()
        print(f"Tabs: {len(tabs)}")
    else:
        print("Not running")


def main():
    parser = argparse.ArgumentParser(
        description="Drive Edge via CDP",
        prog="browser.py",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("launch", help="Start agent Edge with copied auth")
    sub.add_parser("status", help="Check if agent Edge is running")
    sub.add_parser("close", help="Close agent Edge")
    sub.add_parser("tabs", help="List open tabs")
    sub.add_parser("text", help="Get page text content")

    p_nav = sub.add_parser("navigate", help="Navigate to URL")
    p_nav.add_argument("url")

    p_ss = sub.add_parser("screenshot", help="Capture screenshot")
    p_ss.add_argument("path", nargs="?", default=None)

    p_tab = sub.add_parser("tab", help="Switch to tab by index")
    p_tab.add_argument("index")

    p_click = sub.add_parser("click", help="Click element by CSS selector")
    p_click.add_argument("selector")

    p_type = sub.add_parser("type", help="Type into element")
    p_type.add_argument("selector")
    p_type.add_argument("text")

    p_eval = sub.add_parser("eval", help="Evaluate JavaScript")
    p_eval.add_argument("js")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "launch": cmd_launch,
        "navigate": cmd_navigate,
        "screenshot": cmd_screenshot,
        "text": cmd_text,
        "tabs": cmd_tabs,
        "tab": cmd_tab,
        "click": cmd_click,
        "type": cmd_type,
        "eval": cmd_eval,
        "close": cmd_close,
        "status": cmd_status,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
