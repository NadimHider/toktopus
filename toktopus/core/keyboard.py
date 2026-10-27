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

_ORIGINAL_TERMIOS = None

def init_keyboard():
    """Put terminal into non-blocking cbreak mode on Unix if interactive."""
    global _ORIGINAL_TERMIOS
    if not WINDOWS and sys.stdin.isatty():
        try:
            _ORIGINAL_TERMIOS = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except Exception:
            _ORIGINAL_TERMIOS = None

def restore_keyboard():
    """Restore original terminal attributes on Unix."""
    global _ORIGINAL_TERMIOS
    if not WINDOWS and _ORIGINAL_TERMIOS is not None and sys.stdin.isatty():
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, _ORIGINAL_TERMIOS)
        except Exception:
            pass
        _ORIGINAL_TERMIOS = None

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
