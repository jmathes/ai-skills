"""
send — Send a message to a marionette session via named pipe.

Usage:
    python3 send.py <session-name> "message text"
    echo "message" | python3 send.py <session-name> --stdin
"""

from __future__ import annotations

import argparse
import sys

import win32file

PIPE_PREFIX: str = r"\\.\pipe\marionette-"


def send_message(session_name: str, message: str) -> bool:
    """Send a message to a marionette session's named pipe."""
    pipe_path: str = PIPE_PREFIX + session_name
    try:
        handle: int = win32file.CreateFile(
            pipe_path,
            win32file.GENERIC_WRITE,
            0,     # no sharing
            None,  # security
            win32file.OPEN_EXISTING,
            0,     # flags
            None,  # template
        )
        win32file.WriteFile(handle, message.encode("utf-8"))
        win32file.CloseHandle(handle)
        return True
    except Exception as e:
        print(f"Error sending to {session_name}: {e}", file=sys.stderr)
        return False


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Send message to marionette session",
    )
    parser.add_argument("session", help="Target session name")
    parser.add_argument("message", nargs="?", help="Message text")
    parser.add_argument("--stdin", action="store_true", help="Read message from stdin")
    args: argparse.Namespace = parser.parse_args()

    if args.stdin:
        message: str = sys.stdin.read()
    elif args.message:
        message = args.message
    else:
        print("Error: provide a message or use --stdin", file=sys.stderr)
        sys.exit(1)

    # ConPTY expects \r for Enter (not \r\n — that double-submits in some apps)
    if not message.endswith("\r"):
        message = message.rstrip("\n").rstrip("\r") + "\r"

    ok: bool = send_message(args.session, message)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
