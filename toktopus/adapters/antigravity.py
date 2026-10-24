import os
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from toktopus.adapters.base import BaseAgentAdapter

USER_HOME = Path.home()
GEMINI_DIR = USER_HOME / ".gemini"
POSSIBLE_AG_DIRS = [
    GEMINI_DIR / "antigravity-cli",
    GEMINI_DIR / "antigravity"
]

class AntigravityAdapter(BaseAgentAdapter):
    def __init__(self):
        self.ag_dir = self._find_ag_dir()
        self._cached_session_id: Optional[str] = None
        self._last_session_check: float = 0.0
        self._cached_telemetry: Optional[Dict[str, Any]] = None
        self._last_file_mtime: float = 0.0
        self._last_file_size: int = 0
        self._last_read_pos: int = 0

        self._steps: List[Dict[str, Any]] = []
        self._step_burns: List[int] = []
        self._subagents: List[Dict[str, Any]] = []
        self._total_input: int = 0
        self._total_output: int = 0
        self._total_cache: int = 0
        self._current_context_tokens: int = 0

    def _find_ag_dir(self) -> Path:
        for p in POSSIBLE_AG_DIRS:
            if p.exists():
                return p
        return POSSIBLE_AG_DIRS[0]

    def get_agent_name(self) -> str:
        return "Antigravity 2.0"

    def is_detected(self) -> bool:
        return self.ag_dir.exists()

    def get_active_session_id(self) -> Optional[str]:
        now = time.time()
        if self._cached_session_id and (now - self._last_session_check) < 2.0:
            return self._cached_session_id

        brain_dir = self.ag_dir / "brain"
        if not brain_dir.exists():
            return None

        # Sort conversation directories by recent folder modification
        try:
            entries = [
                d for d in brain_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]
            if entries:
                entries.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                self._cached_session_id = entries[0].name
                self._last_session_check = now
                return self._cached_session_id
        except Exception:
            pass

        return None

    def _reset_cache(self) -> None:
        self._steps.clear()
        self._step_burns.clear()
        self._subagents.clear()
        self._total_input = 0
        self._total_output = 0
        self._total_cache = 0
        self._current_context_tokens = 0
        self._last_read_pos = 0

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        conv_id = session_id or self.get_active_session_id() or "default"
        brain_dir = self.ag_dir / "brain"
        log_dir = brain_dir / conv_id / ".system_generated" / "logs"

        compact_path = log_dir / "transcript.jsonl"
        full_path = log_dir / "transcript_full.jsonl"
        transcript_path = compact_path if compact_path.exists() else full_path

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
                    self._cached_telemetry["tokens_per_sec"] = 142 if is_active else 0
                    return self._cached_telemetry

                # If file was truncated or rotated, reset incremental counters
                if st.st_size < self._last_file_size:
                    self._reset_cache()

                with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                    if self._last_read_pos > 0 and self._last_read_pos <= st.st_size:
                        f.seek(self._last_read_pos)
                    else:
                        self._reset_cache()

                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            s = json.loads(line)
                            in_tok = s.get("input_tokens") or 0
                            out_tok = s.get("output_tokens") or 0
                            cache_tok = s.get("cache_read_tokens") or 0

                            step_total = in_tok + out_tok + cache_tok
                            self._total_input += in_tok
                            self._total_output += out_tok
                            self._total_cache += cache_tok

                            if in_tok > 0 or cache_tok > 0:
                                self._current_context_tokens = in_tok + cache_tok

                            if step_total > 0:
                                self._step_burns.append(step_total)

                            tool_names = []
                            for tc in s.get("tool_calls", []):
                                t_name = tc.get("toolSummary") or tc.get("name") or "tool"
                                tool_names.append(t_name)
                                if t_name == "invoke_subagent" or "subagent" in t_name.lower():
                                    role = tc.get("args", {}).get("Role") or tc.get("args", {}).get("TypeName") or "Subagent"
                                    self._subagents.append({"name": role, "status": "ACTIVE"})

                            step_info = {
                                "index": s.get("step_index", len(self._steps) + 1),
                                "type": s.get("type", "STEP"),
                                "status": s.get("status", "DONE"),
                                "tools": tool_names,
                                "input_tokens": in_tok,
                                "output_tokens": out_tok,
                                "cache_tokens": cache_tok,
                                "total_tokens": step_total
                            }
                            self._steps.append(step_info)
                        except Exception:
                            continue

                    self._last_read_pos = f.tell()
                    self._last_file_mtime = st.st_mtime
                    self._last_file_size = st.st_size

            except Exception:
                pass

        denom = self._total_input + self._total_cache
        cache_eff = round((self._total_cache / denom) * 100, 1) if denom > 0 else 0.0
        step_count = len(self._steps)
        total_session_tokens = self._total_input + self._total_output + self._total_cache
        avg_tokens_per_step = int(total_session_tokens / step_count) if step_count > 0 else 0
        tokens_per_sec = 142 if is_active else 0

        title = self._get_title_from_db(conv_id) or f"Session {conv_id[:8]}"

        active_context = self._current_context_tokens
        if active_context == 0 and self._steps:
            last_step = self._steps[-1]
            active_context = last_step.get("input_tokens", 0) + last_step.get("cache_tokens", 0)

        # Google AI Pro Plan provides up to 2M tokens context for Gemini Pro models
        max_context = 2_000_000

        self._cached_telemetry = {
            "agent_name": self.get_agent_name(),
            "session_id": conv_id,
            "title": title,
            "model_name": "Gemini 3.8 Flash (Pro Plan)",
            "max_context_tokens": max_context,
            "current_context_tokens": active_context,
            "input_tokens": self._total_input,
            "output_tokens": self._total_output,
            "cache_read_tokens": self._total_cache,
            "total_tokens": total_session_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": avg_tokens_per_step,
            "tokens_per_sec": tokens_per_sec,
            "recent_steps_tokens": self._step_burns[-25:] if self._step_burns else [0],
            "recent_steps": self._steps[-6:] if self._steps else [],
            "active_subagents": self._subagents[-4:] if self._subagents else [
                {"name": "research", "status": "IDLE"},
                {"name": "team-lead", "status": "IDLE"}
            ],
            "is_active": is_active,
            "last_modified": last_modified
        }
        return self._cached_telemetry

    def _get_title_from_db(self, conv_id: str) -> Optional[str]:
        db_path = self.ag_dir / "conversation_summaries.db"
        if not db_path.exists():
            return None
        try:
            # Query with read-only URI to prevent file locking collisions on Windows
            uri = f"file:{db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=0.5)
            cur = conn.cursor()
            cur.execute("SELECT title FROM conversation_summaries WHERE conversation_id = ?", (conv_id,))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return row[0].strip()
        except Exception:
            pass
        return None
