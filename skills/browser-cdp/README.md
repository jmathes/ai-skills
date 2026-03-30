# browser-cdp

> The SKILL.md for this skill is intentionally terse. It's written for LLM context windows, not human reading. This README is the human-readable companion.

## What it does

Drives a **separate** Microsoft Edge window via the Chrome DevTools Protocol (CDP). The agent gets its own browser process with copied authentication from your main Edge profile. Your main browser is never touched.

## Why

AI agents sometimes need to access authenticated web pages (Azure DevOps, IcM, Teams web, SharePoint, internal wikis). These sites use Microsoft Entra SSO. Rather than fighting OAuth app registrations and admin consent, this tool just opens a real browser with your real credentials.

## How it works

1. **Launch:** Copies Login Data, Bookmarks, and Web Data from your main Edge profile into a separate "Agent Data" profile directory. Cookies are typically locked by the running Edge process, so the agent Edge maintains its own cookie jar. Starts Edge with `--remote-debugging-port=9223` and `--user-data-dir` pointing to the agent profile.

2. **Navigate:** Opens the target URL in a new tab, then closes all other tabs (Edge opens default tabs on startup; this ensures a clean state regardless of defaults).

3. **Interact:** Screenshots via `Page.captureScreenshot`, text extraction via `document.body.innerText`, click/type via CSS selectors and JS evaluation, all through the pychrome CDP client library.

4. **Close:** Closes all tabs, which shuts down the agent Edge process.

## Authentication

The agent profile gets a copy of your Login Data (SSO credentials, saved passwords) on each launch. Cookies can't be copied while your main Edge is running (exclusive file lock), so the agent Edge builds its own cookie jar.

First time you navigate to a Microsoft SSO site in the agent Edge, it may prompt for login. Log in once manually. The session persists in the agent profile across future launches.

Agent profile location: `%LOCALAPPDATA%\Microsoft\Edge\Agent Data`

## Prerequisites

- Microsoft Edge (already installed on Windows)
- Python 3.10+
- `pip install pychrome`

## Commands

```
python browser.py launch              # Start agent Edge
python browser.py navigate <url>      # Go to URL (new tab, close others)
python browser.py screenshot [path]   # Capture PNG
python browser.py text                # Get visible page text
python browser.py tabs                # List open tabs
python browser.py tab <index>         # Switch to tab
python browser.py click <selector>    # Click element by CSS selector
python browser.py type <selector> <t> # Type into element
python browser.py eval <js>           # Evaluate JavaScript
python browser.py status              # Is agent Edge running?
python browser.py close               # Shut down agent Edge
```

## Security notes

- The agent Edge runs with your credentials. It can access anything you can access.
- It runs in a **separate process and profile**. It cannot see or modify your main browser's tabs, history, or state.
- The agent is instructed (via SKILL.md rules) to never type passwords and to ask the user to handle login prompts manually.
- Screenshots are saved to `C:\dev\screenshots\browser\` with timestamps.

## Architecture

```
User's main Edge (untouched)
    |
    | Login Data, Bookmarks, Web Data copied on launch
    v
Agent Edge (separate process, port 9223)
    ^
    | CDP (Chrome DevTools Protocol) over WebSocket
    |
browser.py (pychrome client)
    ^
    | CLI invocation
    |
Copilot CLI agent (shells out to browser.py)
```
