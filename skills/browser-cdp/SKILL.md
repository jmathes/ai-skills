---
name: browser-cdp
description: Drive separate Edge window via CDP. Auth-sharing, screenshots, page text, click/type, JS eval. Agent-controlled window only, never touches user's browser.
metadata:
  readme: README.md
---

## CLI

`python3 C:/dev/ai-skills/skills/browser-cdp/scripts/browser.py <cmd>`

| Cmd | Args | Effect |
|-----|------|--------|
| launch | | Start agent Edge, copy auth from main profile |
| navigate | `<url>` | Open URL in clean tab, close all others |
| screenshot | `[path]` | PNG to `C:\dev\screenshots\browser\<ts>.png` |
| text | | stdout: visible page text |
| tabs | | List open tabs |
| tab | `<idx>` | Switch tab |
| click | `<css>` | Click element |
| type | `<css> <text>` | Type into element |
| eval | `<js>` | Run JS, print result |
| status | | Running? Version? Tab count? |
| close | | Kill agent Edge |

## Workflow

`launch` -> `navigate <url>` -> `text` or `screenshot` -> `click`/`type` if needed -> `close`

## Auth

Copies Login Data, Bookmarks, Web Data from main Edge on launch. Cookies locked while Edge runs (normal). Agent Edge maintains its own session. First use of a site may require manual login in agent window; persists after that.

Profile: `%LOCALAPPDATA%\Microsoft\Edge\Agent Data`. Port: 9223.

## Rules

- Always `launch` first
- SEPARATE window. Never touches user's main Edge.
- Never type passwords. Auth from copied credentials + SSO.
- Login prompt = tell user to log in manually in agent window.
- Screenshots: use `view` tool to inspect returned path.

## Deps

`pip install pychrome`
