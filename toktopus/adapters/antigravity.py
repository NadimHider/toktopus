import os
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from toktopus.adapters.base import BaseAgentAdapter

USER_HOME = Path.home()
GEMINI_DIR = USER_HOME / ".gemini"

POSSIBLE_AG_DIRS = [
    Path(os.environ["ANTIGRAVITY_HOME"]) if os.environ.get("ANTIGRAVITY_HOME") else None,
    Path(os.environ["GEMINI_CLI_HOME"]) if os.environ.get("GEMINI_CLI_HOME") else None,
    Path(os.environ["GEMINI_HOME"]) / "antigravity-cli" if os.environ.get("GEMINI_HOME") else None,
    GEMINI_DIR / "antigravity-cli",
    GEMINI_DIR / "antigravity"
]
POSSIBLE_AG_DIRS = [p for p in POSSIBLE_AG_DIRS if p is not None]

class AntigravityAdapter(BaseAgentAdapter):
    def __init__(self):
        self.ag_dir = self._find_ag_dir()
        self._active_conv_id: Optional[str] = None
        self._cached_session_id: Optional[str] = None
        self._last_session_check: float = 0.0
        self._cached_telemetry: Optional[Dict[str, Any]] = None
        self._active_transcript_path: Optional[Path] = None
        self._last_file_mtime: float = 0.0
        self._last_file_size: int = 0
        self._last_read_pos: int = 0

        self._steps: List[Dict[str, Any]] = []
        self._step_burns: List[int] = []
        self._subagents: List[Dict[str, Any]] = []
        self._total_input: int = 0
        self._total_output: int = 0
        self._total_cache: int = 0
        self._total_reasoning: int = 0
        self._current_context_tokens: int = 0
        self._session_start_time: float = 0.0
        self._last_step_time: float = 0.0
        self._last_turn_duration_sec: float = 0.0

    def _find_ag_dir(self) -> Path:
        for p in POSSIBLE_AG_DIRS:
            if p.exists():
                return p
        return POSSIBLE_AG_DIRS[0] if POSSIBLE_AG_DIRS else GEMINI_DIR / "antigravity-cli"

    def get_agent_name(self) -> str:
        return "Antigravity 2.0"

    def is_detected(self) -> bool:
        if not self.ag_dir.exists():
            self.ag_dir = self._find_ag_dir()
        return self.ag_dir.exists()

    def get_active_session_id(self) -> Optional[str]:
        now = time.time()
        if self._cached_session_id and (now - self._last_session_check) < 2.0:
            return self._cached_session_id

        if not self.ag_dir.exists():
            self.ag_dir = self._find_ag_dir()

        brain_dir = self.ag_dir / "brain"
        if not brain_dir.exists():
            return None

        # Sort conversation directories by actual transcript modification time
        try:
            candidates: List[tuple] = []
            for d in brain_dir.iterdir():
                if not d.is_dir() or d.name.startswith("."):
                    continue
                t1 = d / ".system_generated" / "logs" / "transcript.jsonl"
                t2 = d / ".system_generated" / "logs" / "transcript_full.jsonl"
                mtime = 0.0
                if t1.exists():
                    try:
                        mtime = max(mtime, t1.stat().st_mtime)
                    except Exception:
                        pass
                if t2.exists():
                    try:
                        mtime = max(mtime, t2.stat().st_mtime)
                    except Exception:
                        pass
                if mtime == 0.0:
                    try:
                        mtime = d.stat().st_mtime
                    except Exception:
                        pass
                candidates.append((d.name, mtime))

            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                self._cached_session_id = candidates[0][0]
                self._last_session_check = now
                return self._cached_session_id
        except Exception:
            pass

        return None

    def _get_configured_model(self) -> str:
        settings_path = self.ag_dir / "settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8", errors="ignore") as f:
                    cfg = json.load(f)
                    m = cfg.get("model")
                    if m:
                        return str(m)
            except Exception:
                pass
        return "Gemini 3.8 Flash (Pro Plan)"

    def _get_context_limit_for_model(self, model_name: str) -> int:
        lower = model_name.lower()
        if "gemini" in lower:
            return 2_000_000
        elif "claude" in lower:
            return 200_000
        elif "gpt-4" in lower or "o1" in lower or "o3" in lower:
            return 128_000
        elif "deepseek" in lower:
            return 128_000
        return 1_000_000

    def _reset_cache(self) -> None:
        self._steps.clear()
        self._step_burns.clear()
        self._subagents.clear()
        self._total_input = 0
        self._total_output = 0
        self._total_cache = 0
        self._total_reasoning = 0
        self._current_context_tokens = 0
        self._last_file_mtime = 0.0
        self._last_file_size = 0
        self._last_read_pos = 0
        self._session_start_time = 0.0
        self._last_step_time = 0.0
        self._last_turn_duration_sec = 0.0

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        conv_id = session_id or self.get_active_session_id() or "default"
        if conv_id != self._active_conv_id:
            self._reset_cache()
            self._cached_telemetry = None
            self._active_conv_id = conv_id
            self._active_transcript_path = None

        brain_dir = self.ag_dir / "brain"
        log_dir = brain_dir / conv_id / ".system_generated" / "logs"

        compact_path = log_dir / "transcript.jsonl"
        full_path = log_dir / "transcript_full.jsonl"
        transcript_path = compact_path if compact_path.exists() else full_path

        # If transcript path switched between compact and full, reset cached offset
        if self._active_transcript_path and self._active_transcript_path != transcript_path:
            self._reset_cache()
        self._active_transcript_path = transcript_path

        is_active = False
        last_modified = 0.0

        if transcript_path.exists():
            try:
                st = transcript_path.stat()
                last_modified = st.st_mtime
                is_active = (time.time() - last_modified) < 120

                # Fast path: return cached payload if transcript file size and mtime are unchanged
                if (
                    self._cached_telemetry is not None
                    and st.st_mtime == self._last_file_mtime
                    and st.st_size == self._last_file_size
                ):
                    self._cached_telemetry["is_active"] = is_active
                    elapsed = max(0.0, time.time() - self._session_start_time) if self._session_start_time > 0 else 0.0
                    self._cached_telemetry["session_elapsed_sec"] = elapsed
                    return self._cached_telemetry

                # If file was truncated or rotated, reset incremental counters
                if st.st_size < self._last_file_size:
                    self._reset_cache()

                with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                    if self._last_read_pos > 0 and self._last_read_pos <= st.st_size:
                        f.seek(self._last_read_pos)
                    else:
                        self._reset_cache()

                    bytes_parsed = self._last_read_pos
                    while True:
                        line_start_pos = f.tell()
                        line = f.readline()
                        if not line:
                            break
                        # Guard against partially flushed lines: only commit if line ends with newline
                        if not line.endswith("\n") and not line.endswith("\r"):
                            # Incomplete trailing line, rewind to line start and stop
                            f.seek(line_start_pos)
                            break

                        stripped = line.strip()
                        if not stripped:
                            bytes_parsed = f.tell()
                            continue

                        try:
                            s = json.loads(stripped)
                            in_tok = s.get("input_tokens") or 0
                            out_tok = s.get("output_tokens") or 0
                            cache_tok = s.get("cache_read_tokens") or 0
                            reason_tok = s.get("thinking_tokens") or s.get("reasoning_tokens") or s.get("thoughtsTokenCount") or 0

                            step_total = in_tok + out_tok + cache_tok + reason_tok
                            self._total_input += in_tok
                            self._total_output += out_tok
                            self._total_cache += cache_tok
                            self._total_reasoning += reason_tok

                            # Track first turn timestamp as session start time
                            created_str = s.get("created_at")
                            if created_str:
                                try:
                                    clean_ts = created_str.replace("Z", "+00:00")
                                    dt = datetime.fromisoformat(clean_ts)
                                    step_epoch = dt.timestamp()
                                    if self._session_start_time == 0.0 or step_epoch < self._session_start_time:
                                        self._session_start_time = step_epoch
                                    if self._last_step_time > 0 and step_epoch > self._last_step_time:
                                        self._last_turn_duration_sec = max(0.2, step_epoch - self._last_step_time)
                                    self._last_step_time = max(self._last_step_time, step_epoch)
                                except Exception:
                                    pass

                            if in_tok > 0 or cache_tok > 0:
                                self._current_context_tokens = in_tok + cache_tok

                            if step_total > 0:
                                self._step_burns.append(step_total)

                            tool_names = []
                            for tc in s.get("tool_calls", []):
                                t_name = tc.get("toolSummary") or tc.get("name") or "tool"
                                tool_names.append(t_name)
                                if t_name == "invoke_subagent" or "subagent" in t_name.lower():
                                    args = tc.get("args") or {}
                                    role = args.get("Role") or args.get("TypeName") or "Subagent"
                                    existing = [sa["name"] for sa in self._subagents]
                                    if role not in existing:
                                        self._subagents.append({"name": role, "status": "ACTIVE"})

                            step_info = {
                                "index": s.get("step_index", len(self._steps) + 1),
                                "type": s.get("type", "STEP"),
                                "status": s.get("status", "DONE"),
                                "tools": tool_names,
                                "input_tokens": in_tok,
                                "output_tokens": out_tok,
                                "cache_tokens": cache_tok,
                                "reasoning_tokens": reason_tok,
                                "total_tokens": step_total
                            }
                            self._steps.append(step_info)
                            bytes_parsed = f.tell()
                        except Exception:
                            # If corrupted line, skip it and advance
                            bytes_parsed = f.tell()
                            continue

                    self._last_read_pos = bytes_parsed
                    self._last_file_mtime = st.st_mtime
                    self._last_file_size = st.st_size

            except Exception:
                pass

        if self._session_start_time == 0.0 and last_modified > 0:
            self._session_start_time = last_modified

        denom = self._total_input + self._total_cache
        cache_eff = round((self._total_cache / denom) * 100, 1) if denom > 0 else 0.0
        step_count = len(self._steps)
        total_session_tokens = self._total_input + self._total_output + self._total_cache + self._total_reasoning
        avg_tokens_per_step = int(total_session_tokens / step_count) if step_count > 0 else 0

        # Calculate throughput using real output tokens and turn duration when active
        tokens_per_sec = 0
        if is_active:
            if self._steps:
                recent_out = self._steps[-1].get("output_tokens", 0) + self._steps[-1].get("reasoning_tokens", 0)
                if recent_out > 0 and self._last_turn_duration_sec > 0:
                    tokens_per_sec = max(10, min(600, int(recent_out / self._last_turn_duration_sec)))
                elif recent_out > 0:
                    tokens_per_sec = max(30, min(300, recent_out // 2))
                else:
                    tokens_per_sec = 0
            else:
                tokens_per_sec = 0

        title = self._get_title_from_db(conv_id) or f"Session {conv_id[:8]}"
        configured_model = self._get_configured_model()
        max_ctx = self._get_context_limit_for_model(configured_model)

        active_context = self._current_context_tokens
        if active_context == 0 and self._steps:
            last_step = self._steps[-1]
            active_context = last_step.get("input_tokens", 0) + last_step.get("cache_tokens", 0)

        elapsed_sec = max(0.0, time.time() - self._session_start_time) if self._session_start_time > 0 else 0.0

        # Remove fake fallback subagents
        active_subagents = self._subagents[-4:] if self._subagents else []

        self._cached_telemetry = {
            "agent_name": self.get_agent_name(),
            "session_id": conv_id,
            "title": title,
            "model_name": configured_model,
            "max_context_tokens": max_ctx,
            "current_context_tokens": active_context,
            "input_tokens": self._total_input,
            "output_tokens": self._total_output,
            "cache_read_tokens": self._total_cache,
            "reasoning_tokens": self._total_reasoning,
            "total_tokens": total_session_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": avg_tokens_per_step,
            "tokens_per_sec": tokens_per_sec,
            "session_elapsed_sec": elapsed_sec,
            "recent_steps_tokens": self._step_burns[-25:] if self._step_burns else [0],
            "recent_steps": self._steps[-6:] if self._steps else [],
            "active_subagents": active_subagents,
            "is_active": is_active,
            "last_modified": last_modified
        }
        return self._cached_telemetry

    def _get_title_from_db(self, conv_id: str) -> Optional[str]:
        db_path = self.ag_dir / "conversation_summaries.db"
        if not db_path.exists():
            return None
        conn = None
        try:
            uri = f"file:{db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=1.0)
            cur = conn.cursor()
            cur.execute("SELECT title FROM conversation_summaries WHERE conversation_id = ?", (conv_id,))
            row = cur.fetchone()
            if row and row[0]:
                return row[0].strip()
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return None
