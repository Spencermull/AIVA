"""Robot Decision Controller

Purpose:
Translates keyboard input into robot movement commands.

Responsibilities:
- Capture raw keypresses over SSH without requiring Enter
- Map WASD / arrow keys to movement commands
- Send commands to the serial bridge
"""

import sys
import tty
import termios

# Elegoo Smart Car V4.0 serial command map
COMMANDS = {
    # WASD
    "w": "F",
    "s": "B",
    "a": "L",
    "d": "R",
    " ": "S",
    # Arrow keys (escape sequences)
    "\x1b[A": "F",
    "\x1b[B": "B",
    "\x1b[D": "L",
    "\x1b[C": "R",
}

LABELS = {"F": "Forward", "B": "Backward", "L": "Left", "R": "Right", "S": "Stop"}


def _read_key() -> str:
    """Read a keypress (including escape sequences) without waiting for Enter."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        # Escape sequence: read up to 2 more bytes
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return ch + ch2 + ch3
            return ch + ch2
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def run_keyboard_controller(bridge) -> None:
    """
    Interactive keyboard control loop.

    Controls:
        W / Up Arrow    Forward
        S / Down Arrow  Backward
        A / Left Arrow  Left
        D / Right Arrow Right
        Space           Stop
        Q               Quit
    """
    print("\nKeyboard control active.")
    print("  W/A/S/D or arrow keys to move")
    print("  Space to stop")
    print("  Q to quit\n")

    last_cmd = None

    while True:
        key = _read_key().lower()

        if key in ("q", "\x03"):  # Q or Ctrl+C
            print("\nQuitting — stopping car.")
            bridge.send("S")
            break

        cmd = COMMANDS.get(key) or COMMANDS.get(key.upper())
        if cmd and cmd != last_cmd:
            bridge.send(cmd)
            print(f"\r  {LABELS[cmd]}   ", end="", flush=True)
            last_cmd = cmd
