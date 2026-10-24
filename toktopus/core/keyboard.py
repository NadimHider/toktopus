"""
Non-blocking cross-platform keyboard input handler for toktopus.
"""

import sys
import os

try:
    import msvcrt
    WINDOWS = True
except ImportError:
    WINDOWS = False
    import select
    import tty
    import termios

def get_pressed_key() -> str:
    """Check if a key has been pressed without blocking. Return key char or empty string."""
    if WINDOWS:
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            try:
                # Handle special keys / function keys
                if ch in (b'\x00', b'\xe0'):
                    msvcrt.getch()  # consume secondary code
                    return ""
                return ch.decode("utf-8", errors="ignore").lower()
            except Exception:
                return ""
        return ""
    else:
        # Unix/macOS non-blocking read
        try:
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist:
                return sys.stdin.read(1).lower()
        except Exception:
            return ""
        return ""
