import time
from pathlib import Path
from typing import Dict, List, Tuple
from toktopus.adapters.base import BaseAgentAdapter
from toktopus.adapters.antigravity import AntigravityAdapter
from toktopus.adapters.claude import ClaudeCodeAdapter
from toktopus.adapters.opencode import OpenCodeAdapter
from toktopus.adapters.cursor import CursorAdapter
from toktopus.adapters.codex import CodexAdapter
from toktopus.core.system import get_system_telemetry

ADAPTERS: Dict[str, BaseAgentAdapter] = {
    "antigravity": AntigravityAdapter(),
    "claude": ClaudeCodeAdapter(),
    "opencode": OpenCodeAdapter(),
    "cursor": CursorAdapter(),
    "codex": CodexAdapter()
}

KEY_MAP = {
    "1": "antigravity",
    "2": "claude",
    "3": "opencode",
    "4": "cursor",
    "5": "codex"
}

def get_adapter(name: str) -> BaseAgentAdapter:
    return ADAPTERS.get(name.lower(), ADAPTERS["antigravity"])

def auto_detect_active_agent() -> str:
    # 1. First check running processes
    sys_telemetry = get_system_telemetry()
    ai_procs = sys_telemetry.get("ai_processes", [])
    for p in ai_procs:
        lbl = p.get("label", "").lower()
        if "antigravity" in lbl:
            return "antigravity"
        elif "opencode" in lbl:
            return "opencode"
        elif "claude" in lbl:
            return "claude"
        elif "cursor" in lbl:
            return "cursor"
        elif "copilot" in lbl or "codex" in lbl:
            return "codex"

    # 2. Check recent modification times across agent session data
    home = Path.home()
    recency_candidates: List[Tuple[str, float]] = []

    # Antigravity
    ag_brain = home / ".gemini" / "antigravity-cli" / "brain"
    if ag_brain.exists():
        try:
            subdirs = [d for d in ag_brain.iterdir() if d.is_dir() and not d.name.startswith(".")]
            if subdirs:
                subdirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                recency_candidates.append(("antigravity", subdirs[0].stat().st_mtime))
        except Exception:
            pass

    # OpenCode
    for op_path in [home / ".local" / "share" / "opencode" / "opencode.db", home / ".config" / "opencode"]:
        if op_path.exists():
            try:
                recency_candidates.append(("opencode", op_path.stat().st_mtime))
                break
            except Exception:
                pass

    # Claude Code
    claude_sessions = home / ".claude" / "sessions"
    if claude_sessions.exists():
        try:
            files = list(claude_sessions.glob("*.json*"))
            if files:
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                recency_candidates.append(("claude", files[0].stat().st_mtime))
        except Exception:
            pass

    # Cursor
    cursor_tracking = home / ".cursor" / "ai-tracking" / "ai-code-tracking.db"
    if cursor_tracking.exists():
        try:
            recency_candidates.append(("cursor", cursor_tracking.stat().st_mtime))
        except Exception:
            pass

    # Codex
    codex_dir = home / ".codex"
    if codex_dir.exists():
        try:
            files = list(codex_dir.glob("*.json*"))
            if files:
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                recency_candidates.append(("codex", files[0].stat().st_mtime))
        except Exception:
            pass

    if recency_candidates:
        recency_candidates.sort(key=lambda x: x[1], reverse=True)
        return recency_candidates[0][0]

    return "antigravity"
