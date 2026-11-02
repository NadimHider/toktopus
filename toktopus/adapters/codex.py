import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from toktopus.adapters.base import BaseAgentAdapter
from toktopus.core.native_events import read_native_events
from toktopus.core.system import get_system_telemetry

CODEX_DIR = Path(os.environ["CODEX_HOME"]) if os.environ.get("CODEX_HOME") else Path.home() / ".codex"
class CodexAdapter(BaseAgentAdapter):
    def __init__(self):
        self._cached_session_id: Optional[str] = None
        self._last_session_check: float = 0.0

    def get_agent_name(self) -> str:
        return "Codex"

    def is_detected(self) -> bool:
        return CODEX_DIR.exists()

    def get_active_session_id(self) -> Optional[str]:
        now = time.time()
        if self._cached_session_id and (now - self._last_session_check) < 2.0:
            return self._cached_session_id


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


        sessions_root = CODEX_DIR / "sessions"
        if sessions_root.exists():
            try:
                rollouts = list(sessions_root.rglob("rollout-*.jsonl"))
                if rollouts:
                    rollouts.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                    name = rollouts[0].stem

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
        codex_proc_active = any("codex" in p.get("label", "").lower() for p in ai_procs)

        sid = session_id or self.get_active_session_id()
        if not sid:
            return {
                "agent_name": self.get_agent_name(),
                "session_id": "no-session",
                "title": "Codex: Idle",
                "model_name": "Unknown",
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
        model_name = "Unknown"
        last_modified = 0.0
        start_time = 0.0
        elapsed_sec = 0.0
        is_active = codex_proc_active
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []


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
                                    r_t = last_usage.get("reasoning_output_tokens", 0)
                                    turn_tok = in_t + out_t
                                    if turn_tok > 0:
                                        step_burns.append(turn_tok)
                                    active_context = in_t

                            elif t == "response_item":
                                item_type = payload.get("type")
                                if item_type in ["tool_call", "function_call"] or "name" in payload:
                                    name = payload.get("name") or "tool"
                                    recent_steps.append({
                                        "index": len(recent_steps) + 1,
                                        "type": "TOOL_CALL",
                                        "status": "DONE",
                                        "tools": [name],
                                        "input_tokens": in_t if 'in_t' in locals() else 0,
                                        "output_tokens": out_t if 'out_t' in locals() else 0,
                                        "cache_tokens": c_t if 'c_t' in locals() else 0,
                                        "reasoning_tokens": r_t if 'r_t' in locals() else 0,
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


        denom = total_in
        cache_eff = round((total_cache / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out
        if target_file:
            try:
                recent_steps, _ = read_native_events(target_file, 'codex')
            except (OSError, ValueError):
                recent_steps = []

        tok_per_sec = 0
        thread_name = self._get_thread_title(sid)
        display_title = thread_name or f"Codex: {sid[:12]}"

        return {
            "agent_name": self.get_agent_name(),
            "session_id": sid,
            "title": display_title if total_tokens > 0 else "Codex: Idle",
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
            "tokens_per_sec_available": False,
            "token_semantics": "input includes cache; output includes reasoning",
            "session_elapsed_sec": elapsed_sec,
            "recent_steps_tokens": step_burns[-25:] if step_burns else [0],
            "recent_steps": recent_steps[-1000:],
            "active_subagents": [],
            "is_active": is_active,
            "last_modified": last_modified
        }
