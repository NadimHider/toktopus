import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from toktopus.adapters.base import BaseAgentAdapter

CLAUDE_DIR = Path.home() / ".claude"

class ClaudeCodeAdapter(BaseAgentAdapter):
    def get_agent_name(self) -> str:
        return "Claude Code (CLI)"

    def is_detected(self) -> bool:
        return CLAUDE_DIR.exists()

    def get_active_session_id(self) -> Optional[str]:
        # Check sessions directory
        sess_dir = CLAUDE_DIR / "sessions"
        if sess_dir.exists():
            files = list(sess_dir.glob("*.json")) + list(sess_dir.glob("*.jsonl"))
            if files:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return files[0].stem

        # Check projects directory
        proj_dir = CLAUDE_DIR / "projects"
        if proj_dir.exists():
            files = list(proj_dir.rglob("*.jsonl")) + list(proj_dir.rglob("*.json"))
            if files:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return files[0].stem

        return None

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.get_active_session_id()

        total_in = 0
        total_out = 0
        total_cache = 0
        active_context = 0
        is_active = False
        last_modified = 0.0
        elapsed_sec = 0.0
        model_name = "Claude 3.7 Sonnet"
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []

        target_file = None
        if sid:
            for cand in [
                CLAUDE_DIR / "sessions" / f"{sid}.json",
                CLAUDE_DIR / "sessions" / f"{sid}.jsonl",
            ]:
                if cand.exists():
                    target_file = cand
                    break

            if not target_file and (CLAUDE_DIR / "projects").exists():
                for p in (CLAUDE_DIR / "projects").rglob(f"*{sid}*"):
                    if p.is_file() and p.suffix in (".json", ".jsonl"):
                        target_file = p
                        break

        if target_file and target_file.exists():
            try:
                st = target_file.stat()
                last_modified = st.st_mtime
                is_active = (time.time() - last_modified) < 180

                if target_file.suffix == ".jsonl":
                    start_ts = 0.0
                    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                d = json.loads(line)
                                in_t = d.get("input_tokens") or d.get("prompt_tokens") or 0
                                out_t = d.get("output_tokens") or d.get("completion_tokens") or 0
                                c_read = d.get("cache_read_input_tokens") or d.get("cache_read_tokens") or 0
                                c_create = d.get("cache_creation_input_tokens") or 0
                                total_cache_turn = c_read + c_create

                                total_in += in_t
                                total_out += out_t
                                total_cache += total_cache_turn

                                turn_tok = in_t + out_t + total_cache_turn
                                if turn_tok > 0:
                                    step_burns.append(turn_tok)

                                if in_t > 0 or total_cache_turn > 0:
                                    active_context = in_t + total_cache_turn

                                m = d.get("model")
                                if m:
                                    model_name = str(m)

                                ts_val = d.get("timestamp")
                                if ts_val:
                                    if start_ts == 0.0:
                                        start_ts = float(ts_val)
                                    elapsed_sec = max(0.0, float(ts_val) - start_ts)

                                recent_steps.append({
                                    "index": idx + 1,
                                    "type": d.get("type", "TURN").upper(),
                                    "status": "DONE",
                                    "tools": d.get("tools", []),
                                    "total_tokens": turn_tok
                                })
                            except Exception:
                                continue
                else:
                    # Single JSON document
                    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        total_in = data.get("input_tokens", 0)
                        total_out = data.get("output_tokens", 0)
                        total_cache = data.get("cache_read_tokens", 0)
                        active_context = data.get("current_context_tokens", total_in + total_cache)
                        m = data.get("model") or data.get("model_name")
                        if m:
                            model_name = str(m)
            except Exception:
                pass

        denom = total_in + total_cache
        cache_eff = round((total_cache / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out + total_cache
        avg_tokens_per_step = int(total_tokens / len(recent_steps)) if recent_steps else 0
        tok_per_sec = 74 if is_active else 0

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
            "cache_read_tokens": total_cache,
            "total_tokens": total_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": avg_tokens_per_step,
            "tokens_per_sec": tok_per_sec,
            "session_elapsed_sec": elapsed_sec,
            "recent_steps_tokens": step_burns if step_burns else [0],
            "recent_steps": recent_steps[-6:],
            "active_subagents": [
                {"name": "code-reviewer", "status": "ACTIVE" if is_active else "IDLE"},
                {"name": "security-auditor", "status": "IDLE"}
            ],
            "is_active": is_active,
            "last_modified": last_modified
        }
