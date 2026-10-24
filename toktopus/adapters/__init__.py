from pathlib import Path
from typing import Dict
from toktopus.adapters.base import BaseAgentAdapter
from toktopus.adapters.antigravity import AntigravityAdapter
from toktopus.adapters.claude import ClaudeCodeAdapter
from toktopus.adapters.opencode import OpenCodeAdapter
from toktopus.adapters.cursor import CursorAdapter

ADAPTERS: Dict[str, BaseAgentAdapter] = {
    "antigravity": AntigravityAdapter(),
    "claude": ClaudeCodeAdapter(),
    "opencode": OpenCodeAdapter(),
    "cursor": CursorAdapter()
}

KEY_MAP = {
    "1": "antigravity",
    "2": "claude",
    "3": "opencode",
    "4": "cursor"
}

def get_adapter(name: str) -> BaseAgentAdapter:
    return ADAPTERS.get(name.lower(), ADAPTERS["antigravity"])

def auto_detect_active_agent() -> str:
    # Quick disk check without heavy payload parsing
    home = Path.home()
    
    ag_path = home / ".gemini" / "antigravity-cli" / "brain"
    if ag_path.exists():
        return "antigravity"

    claude_path = home / ".claude" / "sessions"
    if claude_path.exists():
        return "claude"

    opencode_path = home / ".local" / "share" / "opencode"
    if opencode_path.exists():
        return "opencode"

    cursor_path = home / ".cursor"
    if cursor_path.exists():
        return "cursor"

    return "antigravity"
