import os
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from toktopus.adapters.base import BaseAgentAdapter
from toktopus.core.system import get_system_telemetry

POSSIBLE_CURSOR_PATHS = [
    Path.home() / ".cursor",
    Path(os.environ.get("APPDATA", "")) / "Cursor" if os.environ.get("APPDATA") else None
]

class CursorAdapter(BaseAgentAdapter):
    def get_agent_name(self) -> str:
        return "Cursor Agent"

    def is_detected(self) -> bool:
        for p in POSSIBLE_CURSOR_PATHS:
            if p and p.exists():
                return True
        return False

    def _find_vscdb(self) -> Optional[Path]:
        for base in POSSIBLE_CURSOR_PATHS:
            if not base or not base.exists():
                continue
            cand = base / "User" / "globalStorage" / "state.vscdb"
            if cand.exists():
                return cand
        return None

    def get_active_session_id(self) -> Optional[str]:
        # Check tracking db
        tracking_db = Path.home() / ".cursor" / "ai-tracking" / "ai-code-tracking.db"
        if tracking_db.exists():
            try:
                conn = sqlite3.connect(f"file:{tracking_db.as_posix()}?mode=ro", uri=True, timeout=0.5)
                c = conn.cursor()
                c.execute("SELECT conversationId FROM conversation_summaries ORDER BY updatedAt DESC LIMIT 1")
                row = c.fetchone()
                conn.close()
                if row and row[0]:
                    return str(row[0])
            except Exception:
                pass
        return "cursor-workspace"

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sys_info = get_system_telemetry()
        ai_procs = sys_info.get("ai_processes", [])
        cursor_active = any("Cursor" in p.get("label", "") for p in ai_procs)

        sid = session_id or self.get_active_session_id() or "cursor-workspace"
        vscdb_path = self._find_vscdb()

        total_in = 0
        total_out = 0
        total_cache = 0
        active_context = 0
        model_name = "Claude 3.7 Sonnet (Cursor)"
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []
        last_modified = 0.0

        if vscdb_path and vscdb_path.exists():
            try:
                st = vscdb_path.stat()
                last_modified = st.st_mtime
                conn = sqlite3.connect(f"file:{vscdb_path.as_posix()}?mode=ro", uri=True, timeout=0.5)
                c = conn.cursor()

                # Look for token tracking daily stats or composer stats
                c.execute("SELECT key, value FROM ItemTable WHERE key LIKE 'aiCodeTracking.dailyStats%' ORDER BY key DESC LIMIT 1")
                row = c.fetchone()
                if row and row[1]:
                    try:
                        val = row[1]
                        if isinstance(val, bytes):
                            val = val.decode("utf-8", errors="ignore")
                        data = json.loads(val)
                        # Extract real token counts if present in stats
                        total_in = data.get("promptTokens") or data.get("inputTokens") or 0
                        total_out = data.get("completionTokens") or data.get("outputTokens") or 0
                        total_cache = data.get("cachedTokens") or 0
                        active_context = total_in + total_cache
                    except Exception:
                        pass

                # Check recent model preference
                c.execute("SELECT value FROM ItemTable WHERE key = 'cursor/mainBotSelected' LIMIT 1")
                m_row = c.fetchone()
                if m_row and m_row[0]:
                    m_val = m_row[0]
                    if isinstance(m_val, bytes):
                        m_val = m_val.decode("utf-8", errors="ignore")
                    model_name = f"{m_val} (Cursor)"

                conn.close()
            except Exception:
                pass

        denom = total_in + total_cache
        cache_eff = round((total_cache / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out + total_cache

        return {
            "agent_name": self.get_agent_name(),
            "session_id": sid,
            "title": f"Cursor: {sid[:12]}",
            "model_name": model_name,
            "max_context_tokens": 200_000,
            "current_context_tokens": active_context,
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cache_read_tokens": total_cache,
            "total_tokens": total_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": int(total_tokens / len(recent_steps)) if recent_steps else 0,
            "tokens_per_sec": 82 if cursor_active else 0,
            "session_elapsed_sec": 0.0,
            "recent_steps_tokens": step_burns if step_burns else [0],
            "recent_steps": recent_steps,
            "active_subagents": [
                {"name": "composer-agent", "status": "ACTIVE" if cursor_active else "IDLE"}
            ],
            "is_active": cursor_active,
            "last_modified": last_modified
        }
