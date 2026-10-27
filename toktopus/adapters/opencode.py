import os
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from toktopus.adapters.base import BaseAgentAdapter

POSSIBLE_OPENCODE_DIRS = [
    Path(os.environ["OPENCODE_HOME"]) if os.environ.get("OPENCODE_HOME") else None,
    Path.home() / ".local" / "share" / "opencode",
    Path(os.environ.get("LOCALAPPDATA", "")) / "opencode" if os.environ.get("LOCALAPPDATA") else None,
    Path(os.environ.get("APPDATA", "")) / "opencode" if os.environ.get("APPDATA") else None,
    Path.home() / ".config" / "opencode"
]
POSSIBLE_OPENCODE_DIRS = [p for p in POSSIBLE_OPENCODE_DIRS if p is not None]

class OpenCodeAdapter(BaseAgentAdapter):
    def __init__(self):
        self._db_path = self._find_opencode_db()
        self._cached_session_id: Optional[str] = None
        self._last_session_check: float = 0.0

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
        if not self._db_path or not self._db_path.exists():
            self._db_path = self._find_opencode_db()
        if self._db_path and self._db_path.exists():
            return True
        for d in POSSIBLE_OPENCODE_DIRS:
            if d and d.exists():
                return True
        return False

    def get_active_session_id(self) -> Optional[str]:
        now = time.time()
        if self._cached_session_id and (now - self._last_session_check) < 2.0:
            return self._cached_session_id

        if not self._db_path or not self._db_path.exists():
            self._db_path = self._find_opencode_db()

        if not self._db_path or not self._db_path.exists():
            return None

        conn = None
        try:
            conn = sqlite3.connect(f"file:{self._db_path.as_posix()}?mode=ro", uri=True, timeout=1.0)
            cur = conn.cursor()
            cur.execute("SELECT id FROM session_v2 ORDER BY time_updated DESC LIMIT 1;")
            row = cur.fetchone()
            if row and row[0]:
                self._cached_session_id = str(row[0])
                self._last_session_check = now
                return self._cached_session_id
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return None

    def _get_context_limit(self, model_str: str) -> int:
        lower = model_str.lower()
        if "gemini" in lower or "mimo" in lower or "zen" in lower:
            return 1_000_000
        elif "claude" in lower or "sonnet" in lower or "opus" in lower:
            return 200_000
        elif "deepseek" in lower:
            return 128_000
        elif "gpt-4" in lower or "o1" in lower or "o3" in lower:
            return 128_000
        return 500_000

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.get_active_session_id()

        if not self._db_path or not self._db_path.exists():
            self._db_path = self._find_opencode_db()

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
                "cache_write_tokens": 0,
                "reasoning_tokens": 0,
                "total_tokens": 0,
                "cache_efficiency": 0.0,
                "tokens_per_step": 0,
                "tokens_per_sec": 0,
                "session_elapsed_sec": 0.0,
                "session_cost": 0.0,
                "recent_steps_tokens": [0],
                "recent_steps": [],
                "active_subagents": [],
                "is_active": False,
                "last_modified": 0.0
            }

        total_in = 0
        total_out = 0
        total_cache_read = 0
        total_cache_write = 0
        total_reasoning = 0
        active_context = 0
        is_active = False
        last_modified = 0.0
        elapsed_sec = 0.0
        session_cost = 0.0
        title = f"OpenCode: {sid[:10]}"
        model_name = "opencode-zen"
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []

        conn = None
        try:
            conn = sqlite3.connect(f"file:{self._db_path.as_posix()}?mode=ro", uri=True, timeout=1.0)
            cur = conn.cursor()

            # Query available columns in session_v2 dynamically
            cur.execute("PRAGMA table_info(session_v2);")
            cols = [c[1] for c in cur.fetchall()]

            has_cache_write = "tokens_cache_write" in cols
            has_reasoning = "tokens_reasoning" in cols
            has_cost = "cost" in cols

            query_cols = [
                "id", "title", "slug", "tokens_input", "tokens_output", "tokens_cache_read",
                "tokens_reasoning" if has_reasoning else "0 AS tokens_reasoning",
                "tokens_cache_write" if has_cache_write else "0 AS tokens_cache_write",
                "cost" if has_cost else "0.0 AS cost",
                "model", "time_created", "time_updated"
            ]
            sql = f"SELECT {', '.join(query_cols)} FROM session_v2 WHERE id = ? LIMIT 1;"
            cur.execute(sql, (sid,))
            row = cur.fetchone()

            if not row:
                sql_latest = f"SELECT {', '.join(query_cols)} FROM session_v2 ORDER BY time_updated DESC LIMIT 1;"
                cur.execute(sql_latest)
                row = cur.fetchone()

            if row:
                (
                    row_sid, row_title, slug, in_tok, out_tok, cache_read_tok,
                    reason_tok, cache_write_tok, cost_val, model_json, t_create, t_update
                ) = row

                sid = str(row_sid)
                total_in = in_tok or 0
                total_out = out_tok or 0
                total_cache_read = cache_read_tok or 0
                total_cache_write = cache_write_tok or 0
                total_reasoning = reason_tok or 0
                session_cost = float(cost_val or 0.0)
                active_context = total_in + total_cache_read

                display_title = row_title or slug or sid[:10]
                title = f"OpenCode: {display_title}"

                if model_json:
                    try:
                        if str(model_json).strip().startswith("{"):
                            m_data = json.loads(model_json)
                            model_name = m_data.get("id") or m_data.get("model") or model_name
                            if m_data.get("variant") and m_data.get("variant") != "default":
                                model_name = f"{model_name} ({m_data['variant']})"
                        else:
                            model_name = str(model_json).strip()
                    except Exception:
                        model_name = str(model_json).strip()

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
                    ORDER BY seq DESC LIMIT 8;
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
                            # Extract tokens from message if available
                            usage = d.get("usage") or d.get("tokens") or {}
                            if isinstance(usage, dict):
                                step_tok = usage.get("total") or (usage.get("input", 0) + usage.get("output", 0))
                            if step_tok == 0 and "text" in d:
                                # Estimate rough token count from text length
                                step_tok = len(d["text"]) // 4
                        except Exception:
                            pass

                    turn_type = (m_type or "STEP").upper()
                    recent_steps.append({
                        "index": m_seq or len(recent_steps) + 1,
                        "type": turn_type,
                        "status": "DONE",
                        "tools": tools,
                        "total_tokens": step_tok
                    })
                    if step_tok > 0:
                        step_burns.append(step_tok)

        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        total_cache = total_cache_read + total_cache_write
        denom = total_in + total_cache_read
        cache_eff = round((total_cache_read / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out + total_reasoning + total_cache
        avg_tokens_per_step = int(total_tokens / len(recent_steps)) if recent_steps else 0

        # Calculate throughput
        tok_per_sec = 0
        if is_active:
            if step_burns:
                tok_per_sec = max(20, min(350, step_burns[-1] // 2))
            else:
                tok_per_sec = 85

        max_ctx = self._get_context_limit(model_name)

        return {
            "agent_name": self.get_agent_name(),
            "session_id": sid,
            "title": title,
            "model_name": model_name,
            "max_context_tokens": max_ctx,
            "current_context_tokens": active_context,
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cache_read_tokens": total_cache_read,
            "cache_write_tokens": total_cache_write,
            "reasoning_tokens": total_reasoning,
            "total_tokens": total_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": avg_tokens_per_step,
            "tokens_per_sec": tok_per_sec,
            "session_elapsed_sec": elapsed_sec,
            "session_cost": session_cost,
            "recent_steps_tokens": step_burns[-25:] if step_burns else [0],
            "recent_steps": recent_steps[-6:],
            "active_subagents": [],
            "is_active": is_active,
            "last_modified": last_modified
        }
