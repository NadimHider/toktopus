import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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

def _get_agent_recency(name: str, adapter: BaseAgentAdapter) -> float:
    try:
        if name == "antigravity":
            sid = adapter.get_active_session_id()
            if sid:
                ag = adapter  # type: ignore
                t1 = ag.ag_dir / "brain" / sid / ".system_generated" / "logs" / "transcript.jsonl"
                if t1.exists():
                    return t1.stat().st_mtime
                t2 = ag.ag_dir / "brain" / sid / ".system_generated" / "logs" / "transcript_full.jsonl"
                if t2.exists():
                    return t2.stat().st_mtime
        elif name == "claude":
            home = Path.home()
            c_json = home / ".claude.json"
            mtime = 0.0
            if c_json.exists():
                mtime = max(mtime, c_json.stat().st_mtime)
            files = adapter._scan_recent_log_files()  # type: ignore
            if files:
                mtime = max(mtime, files[0].stat().st_mtime)
            return mtime
        elif name == "opencode":
            op = adapter  # type: ignore
            if op._db_path and op._db_path.exists():
                return op._db_path.stat().st_mtime
        elif name == "codex":
            home = Path.home()
            rollouts_dir = home / ".codex" / "sessions"
            if rollouts_dir.exists():
                files = list(rollouts_dir.rglob("rollout-*.jsonl"))
                if files:
                    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    return files[0].stat().st_mtime
            idx_file = home / ".codex" / "session_index.jsonl"
            if idx_file.exists():
                return idx_file.stat().st_mtime
        elif name == "cursor":
            home = Path.home()
            tracking_db = home / ".cursor" / "ai-tracking" / "ai-code-tracking.db"
            if tracking_db.exists():
                return tracking_db.stat().st_mtime
    except Exception:
        pass
    return 0.0

def auto_detect_active_agent() -> str:
    now = time.time()
    recent_candidates: List[Tuple[str, float]] = []

    for name, adapter in ADAPTERS.items():
        if adapter.is_detected():
            mtime = _get_agent_recency(name, adapter)
            if mtime > 0:
                recent_candidates.append((name, mtime))

    # 1. Recency first: if an agent had session activity in the last 180 seconds, pick it
    if recent_candidates:
        recent_candidates.sort(key=lambda x: x[1], reverse=True)
        top_name, top_mtime = recent_candidates[0]
        if (now - top_mtime) < 180:
            return top_name

    # 2. Check running processes
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

    # 3. Overall most recent session data
    if recent_candidates:
        return recent_candidates[0][0]

    return "antigravity"
