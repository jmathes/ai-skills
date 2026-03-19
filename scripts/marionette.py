"""
marionette — stdin multiplexer for cross-session IPC.

Wraps a child process in a ConPTY (pseudo-terminal), forwarding both
real TTY input and messages from a named pipe. The child gets a proper
terminal so interactive shells (pwsh, cmd, etc.) work correctly.

Usage:
    python3 marionette.py --name <session-name> -- <command> [args...]
    python3 marionette.py --name Overseer -- copilot --yolo

The named pipe is created at: \\\\.\\pipe\\marionette-<session-name>

Sending messages:
    python3 send.py <session-name> "your message here"
"""

from __future__ import annotations

import argparse
import msvcrt
import os
import re
import shutil
import sys
import threading
import time
from typing import Callable

import pywintypes
import win32file
import win32pipe
from winpty import PTY

PIPE_PREFIX: str = r"\\.\pipe\marionette-"

WriteFunc = Callable[[str], None]

# Terminal query responses that ConPTY emits but the host should consume,
# not display. These are responses to DA1, DA2, DSR, DECRPM queries.
_TERMINAL_RESPONSE_RE: re.Pattern[str] = re.compile(
    r"\x1b\["       # CSI
    r"[\?>\!]?"     # optional private/secondary prefix
    r"[\d;]*"       # numeric params
    r"[c\$ynR]"     # DA1(c), DA2(c), DSR(n/R), DECRPM($y)
)


def create_named_pipe(name: str) -> tuple[int, str]:
    """Create a Windows named pipe server. Returns (pipe_handle, pipe_path)."""
    pipe_path: str = PIPE_PREFIX + name
    pipe: int = win32pipe.CreateNamedPipe(
        pipe_path,
        win32pipe.PIPE_ACCESS_INBOUND,
        (
            win32pipe.PIPE_TYPE_MESSAGE
            | win32pipe.PIPE_READMODE_MESSAGE
            | win32pipe.PIPE_WAIT
        ),
        win32pipe.PIPE_UNLIMITED_INSTANCES,
        4096,
        4096,
        0,
        None,
    )
    return pipe, pipe_path


def pipe_listener(
    pipe_name: str,
    write_to_pty: WriteFunc,
    stop_event: threading.Event,
) -> None:
    """Listen on a named pipe, forward complete messages to PTY input."""
    while not stop_event.is_set():
        pipe, _ = create_named_pipe(pipe_name)
        try:
            win32pipe.ConnectNamedPipe(pipe, None)
            while not stop_event.is_set():
                try:
                    hr, data = win32file.ReadFile(pipe, 4096)
                    if data:
                        message: str = data.decode("utf-8", errors="replace")
                        write_to_pty(message)
                except pywintypes.error as e:
                    if e.winerror == 109:
                        break
                    raise
        except pywintypes.error:
            if stop_event.is_set():
                break
        finally:
            try:
                win32pipe.DisconnectNamedPipe(pipe)
                win32file.CloseHandle(pipe)
            except Exception:
                pass


def _filter_terminal_responses(text: str) -> str:
    """Strip terminal query responses (DA1, DA2, DSR, DECRPM) from PTY output."""
    return _TERMINAL_RESPONSE_RE.sub("", text)


def pty_reader(pty: PTY, stop_event: threading.Event) -> None:
    """Read output from the ConPTY and write it to the real console."""
    while not stop_event.is_set():
        try:
            output: str = pty.read(blocking=False)
            if output:
                filtered: str = _filter_terminal_responses(output)
                if filtered:
                    sys.stdout.write(filtered)
                    sys.stdout.flush()
            else:
                time.sleep(0.01)
        except Exception:
            if stop_event.is_set():
                break
            # Check if child is still alive
            if not pty.isalive():
                break
            time.sleep(0.01)


def tty_reader(write_to_pty: WriteFunc, stop_event: threading.Event) -> None:
    """Read keystrokes from the real console and forward to the PTY."""
    while not stop_event.is_set():
        try:
            if msvcrt.kbhit():
                ch: bytes = msvcrt.getwch()
                write_to_pty(ch)
            else:
                time.sleep(0.005)
        except EOFError:
            break
        except Exception:
            if stop_event.is_set():
                break
            time.sleep(0.01)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="stdin multiplexer for cross-session IPC"
    )
    parser.add_argument(
        "--name", required=True, help="Session name (used for pipe naming)"
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER,
        help="Command to wrap (after --)",
    )
    args: argparse.Namespace = parser.parse_args()

    cmd: list[str] = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("Error: no command specified", file=sys.stderr)
        sys.exit(1)

    pipe_name: str = args.name
    stop_event: threading.Event = threading.Event()

    # Resolve the executable
    appname: str = shutil.which(cmd[0]) or cmd[0]
    cmdline: str | None = " ".join(cmd[1:]) if len(cmd) > 1 else None

    # Get terminal size for the PTY
    cols, rows = shutil.get_terminal_size()

    # Create ConPTY and spawn the child process
    pty: PTY = PTY(cols, rows)
    pty.spawn(appname, cmdline=cmdline)

    lock: threading.Lock = threading.Lock()

    def write_to_pty(text: str) -> None:
        """Thread-safe write to the ConPTY input."""
        with lock:
            try:
                pty.write(text)
            except Exception:
                stop_event.set()

    pipe_path: str = PIPE_PREFIX + pipe_name
    print(f"marionette: pipe at {pipe_path}", file=sys.stderr)

    # Start threads
    pipe_thread: threading.Thread = threading.Thread(
        target=pipe_listener,
        args=(pipe_name, write_to_pty, stop_event),
        daemon=True,
    )
    pipe_thread.start()

    pty_out_thread: threading.Thread = threading.Thread(
        target=pty_reader,
        args=(pty, stop_event),
        daemon=True,
    )
    pty_out_thread.start()

    tty_thread: threading.Thread = threading.Thread(
        target=tty_reader,
        args=(write_to_pty, stop_event),
        daemon=True,
    )
    tty_thread.start()

    # Wait for child to exit
    while pty.isalive():
        time.sleep(0.1)

    stop_event.set()
    exitstatus: int | None = pty.get_exitstatus()
    sys.exit(exitstatus if exitstatus is not None else 1)


if __name__ == "__main__":
    main()
