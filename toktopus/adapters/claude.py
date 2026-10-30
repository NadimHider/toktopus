import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from toktopus.adapters.base import BaseAgentAdapter

CLAUDE_DIR = Path(os.environ["CLAUDE_HOME"]) if os.environ.get("CLAUDE_HOME") else Path.home() / ".claude"
CLAUDE_JSON = Path(os.environ["CLAUDE_HOME"]) / ".claude.json" if os.environ.get("CLAUDE_HOME") else Path.home() / ".claude.json"

class ClaudeCodeAdapter(BaseAgentAdapter):
    def __init__(self):
        self._cached_session_id: Optional[str] = None
        self._last_session_check: float = 0.0
        self._cached_files: List[Path] = []
        self._last_scan_time: float = 0.0
        self._scan_ttl: float = 3.0

    def get_agent_name(self) -> str:
        return "Claude Code (CLI)"

    def is_detected(self) -> bool:
        return CLAUDE_DIR.exists() or CLAUDE_JSON.exists()

    def _scan_recent_log_files(self) -> List[Path]:
        now = time.time()
        if self._cached_files and (now - self._last_scan_time) < self._scan_ttl:
            return self._cached_files

        found: List[Path] = []

        sess_dir = CLAUDE_DIR / "sessions"
        if sess_dir.exists():
            try:
                for p in sess_dir.iterdir():
                    if p.is_file() and p.suffix in (".json", ".jsonl"):
                        found.append(p)
            except Exception:
                pass

        proj_dir = CLAUDE_DIR / "projects"
        if proj_dir.exists():
            try:
                for p in proj_dir.rglob("*.json*"):
                    if p.is_file() and p.suffix in (".json", ".jsonl"):
                        found.append(p)
            except Exception:
                pass

        if found:
            try:
                found.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            except Exception:
                pass

        self._cached_files = found
        self._last_scan_time = now
        return self._cached_files

    def _get_project_state_from_claude_json(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        if not CLAUDE_JSON.exists():
            return None
        try:
            with open(CLAUDE_JSON, "r", encoding="utf-8", errors="ignore") as f:
                d = json.load(f)
            projects = d.get("projects", {})
            if not projects or not isinstance(projects, dict):
                return None

            best_proj = None
            best_mtime = 0.0

            cwd_str = os.getcwd().replace("\\", "/").rstrip("/")
            for proj_path, proj_data in projects.items():
                if not isinstance(proj_data, dict):
                    continue

                clean_p = proj_path.replace("\\", "/").rstrip("/")
                if clean_p.lower() == cwd_str.lower():
                    return (proj_path, proj_data)

                st = proj_data.get("lastStartTime") or 0.0
                if st > best_mtime:
                    best_mtime = st
                    best_proj = (proj_path, proj_data)

            return best_proj
        except Exception:
            return None

    def get_active_session_id(self) -> Optional[str]:
        now = time.time()
        if self._cached_session_id and (now - self._last_session_check) < 2.0:
            return self._cached_session_id


        state = self._get_project_state_from_claude_json()
        if state and state[1].get("lastSessionId"):
            self._cached_session_id = state[1]["lastSessionId"]
            self._last_session_check = now
            return self._cached_session_id


        files = self._scan_recent_log_files()
        if files:
            self._cached_session_id = files[0].stem
            self._last_session_check = now
            return self._cached_session_id

        return None

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.get_active_session_id()

        total_in = 0
        total_out = 0
        total_cache_read = 0
        total_cache_create = 0
        total_reasoning = 0
        active_context = 0
        is_active = False
        last_modified = 0.0
        elapsed_sec = 0.0
        session_cost = 0.0
        model_name = "Claude 3.7 Sonnet"
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []


        claude_state = self._get_project_state_from_claude_json()
        if claude_state:
            p_path, p_data = claude_state
            if not sid or p_data.get("lastSessionId") == sid:
                sid = sid or p_data.get("lastSessionId")
                total_in = p_data.get("lastTotalInputTokens", 0)
                total_out = p_data.get("lastTotalOutputTokens", 0)
                total_cache_read = p_data.get("lastTotalCacheReadInputTokens", 0)
                total_cache_create = p_data.get("lastTotalCacheCreationInputTokens", 0)
                active_context = total_in + total_cache_read + total_cache_create
                session_cost = float(p_data.get("lastCost") or 0.0)

                dur_ms = p_data.get("lastDuration") or 0
                if dur_ms:
                    elapsed_sec = dur_ms / 1000.0

                start_ms = p_data.get("lastStartTime") or 0
                if start_ms:
                    last_modified = start_ms / 1000.0
                    is_active = (time.time() - last_modified) < 180

                model_usage = p_data.get("lastModelUsage")
                if model_usage and isinstance(model_usage, dict):
                    model_name = list(model_usage.keys())[0]


        files = self._scan_recent_log_files()
        target_file = None
        if sid:
            for f in files:
                if sid in f.name:
                    target_file = f
                    break
        if not target_file and files:
            target_file = files[0]

        if target_file and target_file.exists():
            try:
                st = target_file.stat()
                file_mtime = st.st_mtime
                if file_mtime > last_modified:
                    last_modified = file_mtime
                    is_active = (time.time() - last_modified) < 180

                if target_file.suffix == ".jsonl":
                    start_ts = 0.0
                    last_step_ts = 0.0
                    turn_durations = []
                    file_in = 0
                    file_out = 0
                    file_c_read = 0
                    file_c_create = 0
                    file_reasoning = 0

                    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                d = json.loads(line)
                                usage = d.get("usage") or d.get("message", {}).get("usage") or {}
                                in_t = d.get("input_tokens") or d.get("prompt_tokens") or usage.get("input_tokens") or usage.get("prompt_tokens") or 0
                                out_t = d.get("output_tokens") or d.get("completion_tokens") or usage.get("output_tokens") or usage.get("completion_tokens") or 0
                                c_read = d.get("cache_read_input_tokens") or d.get("cache_read_tokens") or usage.get("cache_read_input_tokens") or usage.get("cache_read_tokens") or 0
                                c_create = d.get("cache_creation_input_tokens") or usage.get("cache_creation_input_tokens") or 0
                                reason_t = d.get("thinking_tokens") or usage.get("thinking_tokens") or 0

                                file_in += in_t
                                file_out += out_t
                                file_c_read += c_read
                                file_c_create += c_create
                                file_reasoning += reason_t

                                turn_tok = in_t + out_t + c_read + c_create + reason_t
                                if turn_tok > 0:
                                    step_burns.append(turn_tok)

                                if in_t > 0 or (c_read + c_create) > 0:
                                    active_context = in_t + c_read + c_create

                                m = d.get("model") or d.get("message", {}).get("model")
                                if m:
                                    model_name = str(m)

                                ts_val = d.get("timestamp")
                                if ts_val:
                                    ts_f = float(ts_val)
                                    if start_ts == 0.0:
                                        start_ts = ts_f
                                    if last_step_ts > 0 and ts_f > last_step_ts:
                                        turn_durations.append(ts_f - last_step_ts)
                                    last_step_ts = ts_f
                                    elapsed_sec = max(elapsed_sec, ts_f - start_ts)

                                tools = d.get("tools") or []
                                recent_steps.append({
                                    "index": idx + 1,
                                    "type": d.get("type", "TURN").upper(),
                                    "status": "DONE",
                                    "tools": tools if isinstance(tools, list) else [str(tools)],
                                    "input_tokens": in_t,
                                    "output_tokens": out_t,
                                    "cache_tokens": c_read,
                                    "cache_read_tokens": c_read,
                                    "cache_creation_tokens": c_create,
                                    "reasoning_tokens": reason_t,
                                    "total_tokens": turn_tok
                                })
                            except Exception:
                                continue

                    if file_in > 0 or file_out > 0 or file_c_read > 0:
                        total_in = file_in
                        total_out = file_out
                        total_cache_read = file_c_read
                        total_cache_create = file_c_create
                        total_reasoning = file_reasoning

                elif target_file.suffix == ".json":
                    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            in_t = data.get("input_tokens", 0)
                            out_t = data.get("output_tokens", 0)
                            c_read = data.get("cache_read_tokens", 0)
                            c_create = data.get("cache_creation_tokens", 0)
                            if in_t > 0 or out_t > 0:
                                total_in = in_t
                                total_out = out_t
                                total_cache_read = c_read
                                total_cache_create = c_create
                                active_context = data.get("current_context_tokens", in_t + c_read + c_create)
                            m = data.get("model") or data.get("model_name")
                            if m:
                                model_name = str(m)
            except Exception:
                pass

        total_cache = total_cache_read + total_cache_create
        denom = total_in + total_cache_read
        cache_eff = round((total_cache_read / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out + total_cache + total_reasoning
        avg_tokens_per_step = int(total_tokens / len(recent_steps)) if recent_steps else 0


        tok_per_sec = 0
        if is_active:
            if recent_steps:
                recent_out = recent_steps[-1].get("total_tokens", 0)
                tok_per_sec = max(15, min(300, recent_out // 2)) if recent_out > 0 else 60
            else:
                tok_per_sec = 60

        display_sid = sid if sid else "no-active-session"
        title = f"Claude: {display_sid[:12]}" if sid else "Claude Code: Idle"

        return {
            "agent_name": self.get_agent_name(),
            "session_id": display_sid,
            "title": title,
            "model_name": model_name,
            "max_context_tokens": 200_000,
            "current_context_tokens": active_context,
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cache_read_tokens": total_cache_read,
            "cache_creation_tokens": total_cache_create,
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
