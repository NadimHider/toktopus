import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from toktopus.adapters.base import BaseAgentAdapter
from toktopus.core.system import get_system_telemetry

POSSIBLE_CURSOR_PATHS = [
    Path(os.environ["CURSOR_HOME"]) if os.environ.get("CURSOR_HOME") else None,
    Path.home() / ".cursor",
    Path.home() / "Library" / "Application Support" / "Cursor",
    Path.home() / ".config" / "Cursor",
    Path(os.environ.get("APPDATA", "")) / "Cursor" if os.environ.get("APPDATA") else None
]
POSSIBLE_CURSOR_PATHS = [p for p in POSSIBLE_CURSOR_PATHS if p is not None]

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
            cand_global = base / "User" / "globalStorage" / "state.vscdb"
            if cand_global.exists():
                return cand_global

            direct_cand = base / "globalStorage" / "state.vscdb"
            if direct_cand.exists():
                return direct_cand
        return None

    def get_active_session_id(self) -> Optional[str]:

        tracking_db = Path.home() / ".cursor" / "ai-tracking" / "ai-code-tracking.db"
        if tracking_db.exists():
            conn = None
            try:
                conn = sqlite3.connect(f"file:{tracking_db.as_posix()}?mode=ro", uri=True, timeout=1.0)
                c = conn.cursor()
                c.execute("SELECT conversationId FROM ai_code_hashes ORDER BY createdAt DESC LIMIT 1;")
                row = c.fetchone()
                if row and row[0]:
                    return str(row[0])
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
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


        tracking_db = Path.home() / ".cursor" / "ai-tracking" / "ai-code-tracking.db"
        if tracking_db.exists():
            conn = None
            try:
                st = tracking_db.stat()
                last_modified = st.st_mtime
                cursor_active = cursor_active or ((time.time() - last_modified) < 180)

                conn = sqlite3.connect(f"file:{tracking_db.as_posix()}?mode=ro", uri=True, timeout=1.0)
                cur = conn.cursor()
                cur.execute("SELECT conversationId, model, createdAt FROM ai_code_hashes ORDER BY createdAt DESC LIMIT 5;")
                rows = cur.fetchall()
                if rows:
                    if rows[0][0]:
                        sid = str(rows[0][0])
                    m_val = rows[0][1]
                    if m_val and str(m_val).lower() not in ("false", "true", "none"):
                        model_name = f"{m_val} (Cursor)"


                cur.execute("SELECT COUNT(*) FROM ai_code_hashes WHERE conversationId = ?;", (sid,))
                cnt_row = cur.fetchone()
                gen_count = cnt_row[0] if cnt_row else 0
                if gen_count > 0:

                    total_out = gen_count * 150
                    total_in = gen_count * 800
                    active_context = total_in
                    step_burns = [950] * min(gen_count, 10)
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass


        if vscdb_path and vscdb_path.exists():
            conn = None
            try:
                st = vscdb_path.stat()
                if st.st_mtime > last_modified:
                    last_modified = st.st_mtime
                    cursor_active = cursor_active or ((time.time() - last_modified) < 180)

                conn = sqlite3.connect(f"file:{vscdb_path.as_posix()}?mode=ro", uri=True, timeout=1.0)
                c = conn.cursor()


                c.execute("SELECT value FROM ItemTable WHERE key = 'cursor/applicationOpenModelAppliedConfig' LIMIT 1;")
                m_row = c.fetchone()
                if m_row and m_row[0]:
                    raw = m_row[0]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="ignore")
                    cfg = json.loads(raw)
                    selected = cfg.get("selectedModels", [])
                    if selected and isinstance(selected, list):
                        m_id = selected[0].get("modelId")
                        if m_id and str(m_id).lower() not in ("false", "true", "none"):
                            model_name = f"{m_id} (Cursor)"


                c.execute("SELECT key, value FROM ItemTable WHERE key LIKE 'aiCodeTracking.dailyStats%' ORDER BY key DESC LIMIT 1;")
                row = c.fetchone()
                if row and row[1]:
                    try:
                        val = row[1]
                        if isinstance(val, bytes):
                            val = val.decode("utf-8", errors="ignore")
                        data = json.loads(val)
                        in_t = data.get("promptTokens") or data.get("inputTokens") or 0
                        out_t = data.get("completionTokens") or data.get("outputTokens") or 0
                        c_t = data.get("cachedTokens") or 0
                        if in_t == 0 and out_t == 0:
                            sugg_lines = data.get("composerSuggestedLines") or 0
                            if sugg_lines > 0:
                                out_t = sugg_lines * 12
                                in_t = out_t * 3
                        if in_t > 0 or out_t > 0:
                            total_in = in_t
                            total_out = out_t
                            total_cache = c_t
                            active_context = total_in + total_cache
                            step_burns = [min(4000, (in_t + out_t) // 4)] * 4
                    except Exception:
                        pass

            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        denom = total_in + total_cache
        cache_eff = round((total_cache / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out + total_cache

        tok_per_sec = 0
        if cursor_active:
            tok_per_sec = 55 if total_tokens > 0 else 0

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
            "tokens_per_sec": tok_per_sec,
            "session_elapsed_sec": 0.0,
            "recent_steps_tokens": step_burns[-25:] if step_burns else [0],
            "recent_steps": recent_steps,
            "active_subagents": [],
            "is_active": cursor_active,
            "last_modified": last_modified
        }
