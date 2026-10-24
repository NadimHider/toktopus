"""
Adapter Registry and Auto-Detector for toktopus.
"""

from typing import Dict, List, Optional
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
    """Retrieve adapter by name or fallback to antigravity."""
    return ADAPTERS.get(name.lower(), ADAPTERS["antigravity"])

def auto_detect_active_agent() -> str:
    """Automatically detect whichever agent has the most recent activity."""
    newest_agent = "antigravity"
    newest_mtime = 0.0

    for key, adapter in ADAPTERS.items():
        if adapter.is_detected():
            try:
                telemetry = adapter.get_session_telemetry()
                mtime = telemetry.get("last_modified", 0.0)
                if mtime > newest_mtime:
                    newest_mtime = mtime
                    newest_agent = key
            except Exception:
                continue

    return newest_agent
