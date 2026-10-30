

import sys

try:
    import msvcrt
    WINDOWS = True
except ImportError:
    WINDOWS = False
    import select
    import termios
    import tty

_ORIGINAL_TERMIOS = None

def init_keyboard():
    pass
    global _ORIGINAL_TERMIOS
    if not WINDOWS and sys.stdin.isatty():
        try:
            _ORIGINAL_TERMIOS = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except Exception:
            _ORIGINAL_TERMIOS = None

def restore_keyboard():
    pass
    global _ORIGINAL_TERMIOS
    if not WINDOWS and _ORIGINAL_TERMIOS is not None and sys.stdin.isatty():
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, _ORIGINAL_TERMIOS)
        except Exception:
            pass
        _ORIGINAL_TERMIOS = None

def get_pressed_key() -> str:
    pass
    if WINDOWS:
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            try:

                if ch in (b'\x00', b'\xe0'):
                    msvcrt.getch()
                    return ""
                return ch.decode("utf-8", errors="ignore").lower()
            except Exception:
                return ""
        return ""
    else:

        try:
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist:
                return sys.stdin.read(1).lower()
        except Exception:
            return ""
        return ""
