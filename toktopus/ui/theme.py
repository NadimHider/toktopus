"""
btop-inspired Truecolor Theme Palettes for toktopus.
"""

from rich.theme import Theme

# Hex colors matching btop truecolor neon aesthetic
CYAN = "#00f3ff"
PURPLE = "#b026ff"
EMERALD = "#00ff88"
YELLOW = "#ffe600"
RED = "#ff3366"
DIM_GRAY = "#4b5563"
LIGHT_GRAY = "#9ca3af"
WHITE = "#ffffff"
BG_DARK = "#0d1117"

THEME_CONFIG = Theme({
    "toktopus.title": f"bold {CYAN}",
    "toktopus.subtitle": f"bold {PURPLE}",
    "toktopus.border": CYAN,
    "toktopus.success": f"bold {EMERALD}",
    "toktopus.warning": f"bold {YELLOW}",
    "toktopus.danger": f"bold {RED}",
    "toktopus.dim": DIM_GRAY,
    "toktopus.highlight": f"bold {WHITE}",
    "toktopus.cache": EMERALD,
    "toktopus.input": CYAN,
    "toktopus.output": PURPLE,
})
