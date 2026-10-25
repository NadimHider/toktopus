import os
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from toktopus.adapters.base import BaseAgentAdapter

POSSIBLE_OPENCODE_DIRS = [
    Path.home() / ".local" / "share" / "opencode",
    Path(os.environ.get("APPDATA", "")) / "opencode" if os.environ.get("APPDATA") else None,
    Path.home() / ".config" / "opencode"
]

class OpenCodeAdapter(BaseAgentAdapter):
    def __init__(self):
        self._db_path = self._find_opencode_db()

    def _find_opencode_db(self) -> Optional[Path]:
        for d in POSSIBLE_OPENCODE_DIRS:
            if d and d.exists():
                db = d / "opencode.db"
                if db.exists():
                    return db
        return None

    def get_agent_name(self) -> str:
        return "OpenCode v2 / Mini"

    def is_detected(self) -> bool:
        if self._db_path and self._db_path.exists():
            return True
        for d in POSSIBLE_OPENCODE_DIRS:
            if d and d.exists():
                return True
        return False

    def get_active_session_id(self) -> Optional[str]:
        if not self._db_path or not self._db_path.exists():
            return None

        try:
            conn = sqlite3.connect(f"file:{self._db_path.as_posix()}?mode=ro", uri=True, timeout=0.5)
            cur = conn.cursor()
            cur.execute("SELECT id FROM session_v2 ORDER BY time_updated DESC LIMIT 1;")
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return str(row[0])
        except Exception:
            pass
        return None

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.get_active_session_id()
        if not self._db_path or not self._db_path.exists() or not sid:
            return {
                "agent_name": self.get_agent_name(),
                "session_id": sid or "no-session",
                "title": "OpenCode: Idle",
                "model_name": "opencode-zen",
                "max_context_tokens": 1_000_000,
                "current_context_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "total_tokens": 0,
                "cache_efficiency": 0.0,
                "tokens_per_step": 0,
                "tokens_per_sec": 0,
                "session_elapsed_sec": 0.0,
                "recent_steps_tokens": [0],
                "recent_steps": [],
                "active_subagents": [
                    {"name": "build", "status": "IDLE"},
                    {"name": "explore", "status": "IDLE"}
                ],
                "is_active": False,
                "last_modified": 0.0
            }

        total_in = 0
        total_out = 0
        total_cache = 0
        active_context = 0
        is_active = False
        last_modified = 0.0
        elapsed_sec = 0.0
        title = f"OpenCode: {sid[:10]}"
        model_name = "opencode-zen"
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []

        try:
            conn = sqlite3.connect(f"file:{self._db_path.as_posix()}?mode=ro", uri=True, timeout=0.5)
            cur = conn.cursor()

            # Query the target session
            cur.execute("""
                SELECT id, title, slug, tokens_input, tokens_output, tokens_cache_read,
                       tokens_reasoning, model, time_created, time_updated
                FROM session_v2 WHERE id = ? LIMIT 1;
            """, (sid,))
            row = cur.fetchone()

            if not row:
                # If specified session not found, pick the most recent one with non-zero tokens or latest
                cur.execute("""
                    SELECT id, title, slug, tokens_input, tokens_output, tokens_cache_read,
                           tokens_reasoning, model, time_created, time_updated
                    FROM session_v2 ORDER BY time_updated DESC LIMIT 1;
                """)
                row = cur.fetchone()

            if row:
                sid, row_title, slug, in_tok, out_tok, cache_tok, reason_tok, model_json, t_create, t_update = row
                total_in = in_tok or 0
                total_out = out_tok or 0
                total_cache = cache_tok or 0
                active_context = total_in + total_cache

                display_title = row_title or slug or sid[:10]
                title = f"OpenCode: {display_title}"

                if model_json:
                    try:
                        m_data = json.loads(model_json)
                        model_name = m_data.get("id") or model_name
                    except Exception:
                        pass

                if t_update:
                    last_modified = t_update / 1000.0
                    is_active = (time.time() - last_modified) < 180

                if t_create and t_update:
                    elapsed_sec = max(0.0, (t_update - t_create) / 1000.0)

                # Query messages for this session
                cur.execute("""
                    SELECT type, seq, time_created, data
                    FROM session_message
                    WHERE session_id = ?
                    ORDER BY seq DESC LIMIT 6;
                """, (sid,))
                msg_rows = cur.fetchall()

                for m_type, m_seq, m_time, m_data in reversed(msg_rows):
                    tools = []
                    step_tok = 0
                    if m_data:
                        try:
                            d = json.loads(m_data)
                            for a in d.get("agents", []):
                                if a:
                                    tools.append(str(a))
                        except Exception:
                            pass
                    recent_steps.append({
                        "index": m_seq or len(recent_steps) + 1,
                        "type": (m_type or "STEP").upper(),
                        "status": "DONE",
                        "tools": tools,
                        "total_tokens": step_tok
                    })
                    if step_tok > 0:
                        step_burns.append(step_tok)

            conn.close()
        except Exception:
            pass

        denom = total_in + total_cache
        cache_eff = round((total_cache / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out + total_cache
        avg_tokens_per_step = int(total_tokens / len(recent_steps)) if recent_steps else 0
        tok_per_sec = 128 if is_active else 0

        return {
            "agent_name": self.get_agent_name(),
            "session_id": sid,
            "title": title,
            "model_name": model_name,
            "max_context_tokens": 1_000_000,
            "current_context_tokens": active_context,
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cache_read_tokens": total_cache,
            "total_tokens": total_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": avg_tokens_per_step,
            "tokens_per_sec": tok_per_sec,
            "session_elapsed_sec": elapsed_sec,
            "recent_steps_tokens": step_burns if step_burns else [0],
            "recent_steps": recent_steps,
            "active_subagents": [
                {"name": "build", "status": "ACTIVE" if is_active else "IDLE"},
                {"name": "explore", "status": "IDLE"}
            ],
            "is_active": is_active,
            "last_modified": last_modified
        }
