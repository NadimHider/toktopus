import os
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from toktopus.adapters.base import BaseAgentAdapter
from toktopus.core.system import get_system_telemetry

CODEX_DIR = Path(os.environ["CODEX_HOME"]) if os.environ.get("CODEX_HOME") else Path.home() / ".codex"
COPILOT_DIR = Path.home() / ".copilot"

COPILOT_CONFIG_DIRS = [
    CODEX_DIR,
    COPILOT_DIR,
    Path.home() / ".config" / "github-copilot",
    Path(os.environ.get("LOCALAPPDATA", "")) / "github-copilot" if os.environ.get("LOCALAPPDATA") else None
]
COPILOT_CONFIG_DIRS = [p for p in COPILOT_CONFIG_DIRS if p is not None]

class CodexAdapter(BaseAgentAdapter):
    def __init__(self):
        self._cached_session_id: Optional[str] = None
        self._last_session_check: float = 0.0

    def get_agent_name(self) -> str:
        return "Codex / Copilot"

    def is_detected(self) -> bool:
        for p in COPILOT_CONFIG_DIRS:
            if p and p.exists():
                return True
        return False

    def get_active_session_id(self) -> Optional[str]:
        now = time.time()
        if self._cached_session_id and (now - self._last_session_check) < 2.0:
            return self._cached_session_id

        # 1. Check ~/.codex/session_index.jsonl
        index_file = CODEX_DIR / "session_index.jsonl"
        if index_file.exists():
            try:
                latest_id = None
                with open(index_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            if d.get("id"):
                                latest_id = str(d["id"])
                        except Exception:
                            continue
                if latest_id:
                    self._cached_session_id = latest_id
                    self._last_session_check = now
                    return self._cached_session_id
            except Exception:
                pass

        # 2. Check ~/.codex/sessions/**/rollout-*.jsonl
        sessions_root = CODEX_DIR / "sessions"
        if sessions_root.exists():
            try:
                rollouts = list(sessions_root.rglob("rollout-*.jsonl"))
                if rollouts:
                    rollouts.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    # Extract ID from filename or content
                    name = rollouts[0].stem
                    # Filename format: rollout-YYYY-MM-DDTHH-MM-SS-<uuid>
                    parts = name.split("-")
                    if len(parts) >= 5:
                        self._cached_session_id = "-".join(parts[-5:])
                        self._last_session_check = now
                        return self._cached_session_id
                    self._cached_session_id = name
                    self._last_session_check = now
                    return self._cached_session_id
            except Exception:
                pass

        # 3. Check ~/.copilot/data.db
        copilot_db = COPILOT_DIR / "data.db"
        if copilot_db.exists():
            conn = None
            try:
                conn = sqlite3.connect(f"file:{copilot_db.as_posix()}?mode=ro", uri=True, timeout=1.0)
                cur = conn.cursor()
                cur.execute("SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1;")
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

    def _get_thread_title(self, session_id: str) -> Optional[str]:
        index_file = CODEX_DIR / "session_index.jsonl"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            if d.get("id") == session_id:
                                return d.get("thread_name")
                        except Exception:
                            continue
            except Exception:
                pass
        return None

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sys_info = get_system_telemetry()
        ai_procs = sys_info.get("ai_processes", [])
        codex_proc_active = any("codex" in p.get("label", "").lower() or "copilot" in p.get("label", "").lower() for p in ai_procs)

        sid = session_id or self.get_active_session_id()
        if not sid:
            return {
                "agent_name": self.get_agent_name(),
                "session_id": "no-session",
                "title": "Codex / Copilot: Idle",
                "model_name": "OpenAI o3-mini (Codex)",
                "max_context_tokens": 200_000,
                "current_context_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "reasoning_tokens": 0,
                "total_tokens": 0,
                "cache_efficiency": 0.0,
                "tokens_per_step": 0,
                "tokens_per_sec": 0,
                "session_elapsed_sec": 0.0,
                "recent_steps_tokens": [0],
                "recent_steps": [],
                "active_subagents": [],
                "is_active": codex_proc_active,
                "last_modified": 0.0
            }

        total_in = 0
        total_out = 0
        total_cache = 0
        total_reasoning = 0
        active_context = 0
        max_context = 200_000
        model_name = "OpenAI o3-mini (Codex)"
        last_modified = 0.0
        start_time = 0.0
        elapsed_sec = 0.0
        is_active = codex_proc_active
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []

        # Look for matching rollout file
        sessions_root = CODEX_DIR / "sessions"
        target_file = None
        if sessions_root.exists():
            try:
                for rf in sessions_root.rglob("rollout-*.jsonl"):
                    if sid in rf.name:
                        target_file = rf
                        break
                if not target_file:
                    candidates = list(sessions_root.rglob("rollout-*.jsonl"))
                    if candidates:
                        candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        target_file = candidates[0]
            except Exception:
                pass

        if target_file and target_file.exists():
            try:
                st = target_file.stat()
                last_modified = st.st_mtime
                is_active = is_active or ((time.time() - last_modified) < 180)

                with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            t = d.get("type")
                            payload = d.get("payload", {})

                            if t == "session_meta":
                                ts_str = payload.get("timestamp")
                                if ts_str:
                                    clean_ts = ts_str.replace("Z", "+00:00")
                                    start_time = datetime.fromisoformat(clean_ts).timestamp()

                            elif t == "turn_context":
                                m = payload.get("model")
                                if m:
                                    model_name = str(m)

                            elif t == "event_msg" and payload.get("type") == "token_count":
                                info = payload.get("info", {})
                                total_usage = info.get("total_token_usage", {})
                                last_usage = info.get("last_token_usage", {})
                                cw = info.get("model_context_window")
                                if cw:
                                    max_context = int(cw)

                                if total_usage:
                                    total_in = total_usage.get("input_tokens", total_in)
                                    total_out = total_usage.get("output_tokens", total_out)
                                    total_cache = total_usage.get("cached_input_tokens", total_cache)
                                    total_reasoning = total_usage.get("reasoning_output_tokens", total_reasoning)

                                if last_usage:
                                    in_t = last_usage.get("input_tokens", 0)
                                    out_t = last_usage.get("output_tokens", 0)
                                    c_t = last_usage.get("cached_input_tokens", 0)
                                    turn_tok = in_t + out_t + c_t
                                    if turn_tok > 0:
                                        step_burns.append(turn_tok)
                                    active_context = in_t + c_t

                            elif t == "response_item":
                                item_type = payload.get("type")
                                if item_type in ["tool_call", "function_call"] or "name" in payload:
                                    name = payload.get("name") or "tool"
                                    recent_steps.append({
                                        "index": len(recent_steps) + 1,
                                        "type": "TOOL_CALL",
                                        "status": "DONE",
                                        "tools": [name],
                                        "total_tokens": step_burns[-1] if step_burns else 0
                                    })
                        except Exception:
                            continue

                if start_time > 0 and last_modified >= start_time:
                    elapsed_sec = last_modified - start_time
                elif start_time > 0:
                    elapsed_sec = max(0.0, time.time() - start_time)

            except Exception:
                pass

        # Fallback to Copilot data.db if no tokens found in rollouts
        if total_in == 0 and total_out == 0:
            copilot_db = COPILOT_DIR / "data.db"
            if copilot_db.exists():
                conn = None
                try:
                    conn = sqlite3.connect(f"file:{copilot_db.as_posix()}?mode=ro", uri=True, timeout=1.0)
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT id, title, model, total_input_tokens, total_output_tokens,
                               total_cached_tokens, total_reasoning_tokens, context_current_tokens,
                               context_input_token_limit, updated_at
                        FROM sessions WHERE id = ? LIMIT 1;
                    """, (sid,))
                    row = cur.fetchone()
                    if row:
                        sid, db_title, db_model, in_t, out_t, c_t, r_t, cur_t, lim_t, up_at = row
                        total_in = in_t or 0
                        total_out = out_t or 0
                        total_cache = c_t or 0
                        total_reasoning = r_t or 0
                        active_context = cur_t or (total_in + total_cache)
                        if lim_t:
                            max_context = int(lim_t)
                        if db_model:
                            model_name = str(db_model)
                        if up_at:
                            last_modified = float(up_at) / 1000.0 if float(up_at) > 1e11 else float(up_at)
                            is_active = is_active or ((time.time() - last_modified) < 180)
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
        total_tokens = total_in + total_out + total_reasoning + total_cache

        tok_per_sec = 0
        if is_active:
            if step_burns:
                tok_per_sec = max(25, min(300, step_burns[-1] // 2))
            else:
                tok_per_sec = 75

        thread_name = self._get_thread_title(sid)
        display_title = thread_name or f"Codex: {sid[:12]}"

        return {
            "agent_name": self.get_agent_name(),
            "session_id": sid,
            "title": display_title if total_tokens > 0 else "Codex / Copilot: Idle",
            "model_name": model_name,
            "max_context_tokens": max_context,
            "current_context_tokens": active_context,
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cache_read_tokens": total_cache,
            "reasoning_tokens": total_reasoning,
            "total_tokens": total_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": int(total_tokens / len(recent_steps)) if recent_steps else 0,
            "tokens_per_sec": tok_per_sec,
            "session_elapsed_sec": elapsed_sec,
            "recent_steps_tokens": step_burns[-25:] if step_burns else [0],
            "recent_steps": recent_steps[-6:],
            "active_subagents": [],
            "is_active": is_active,
            "last_modified": last_modified
        }
