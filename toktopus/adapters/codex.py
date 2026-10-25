import os
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List

from toktopus.adapters.base import BaseAgentAdapter
from toktopus.core.system import get_system_telemetry

COPILOT_CONFIG_DIRS = [
    Path.home() / ".config" / "github-copilot",
    Path.home() / ".copilot",
    Path.home() / ".codex",
    Path(os.environ.get("LOCALAPPDATA", "")) / "github-copilot" if os.environ.get("LOCALAPPDATA") else None
]

class CodexAdapter(BaseAgentAdapter):
    def get_agent_name(self) -> str:
        return "Codex / Copilot"

    def is_detected(self) -> bool:
        for p in COPILOT_CONFIG_DIRS:
            if p and p.exists():
                return True
        if shutil.which("copilot") or shutil.which("github-copilot-cli") or shutil.which("codex"):
            return True
        return False

    def get_active_session_id(self) -> Optional[str]:
        codex_dir = Path.home() / ".codex"
        if codex_dir.exists():
            files = list(codex_dir.glob("*.jsonl")) + list(codex_dir.glob("*.json"))
            if files:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return files[0].stem
        return "codex-session"

    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sys_info = get_system_telemetry()
        ai_procs = sys_info.get("ai_processes", [])
        codex_active = any("codex" in p.get("label", "").lower() or "copilot" in p.get("label", "").lower() for p in ai_procs)

        sid = session_id or self.get_active_session_id() or "codex-session"

        total_in = 0
        total_out = 0
        total_cache = 0
        active_context = 0
        model_name = "OpenAI o3-mini (Codex)"
        last_modified = 0.0
        elapsed_sec = 0.0
        step_burns: List[int] = []
        recent_steps: List[Dict[str, Any]] = []

        # Parse real session files if present in ~/.codex/
        codex_dir = Path.home() / ".codex"
        if codex_dir.exists():
            files = list(codex_dir.glob("*.jsonl")) + list(codex_dir.glob("*.json"))
            if files:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                target = files[0]
                try:
                    st = target.stat()
                    last_modified = st.st_mtime
                    codex_active = codex_active or ((time.time() - last_modified) < 180)

                    if target.suffix == ".jsonl":
                        with open(target, "r", encoding="utf-8", errors="ignore") as f:
                            for idx, line in enumerate(f):
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    d = json.loads(line)
                                    in_t = d.get("prompt_tokens") or d.get("input_tokens") or 0
                                    out_t = d.get("completion_tokens") or d.get("output_tokens") or 0
                                    c_tok = d.get("cached_tokens") or 0

                                    total_in += in_t
                                    total_out += out_t
                                    total_cache += c_tok

                                    turn_tok = in_t + out_t + c_tok
                                    if turn_tok > 0:
                                        step_burns.append(turn_tok)
                                    if in_t > 0 or c_tok > 0:
                                        active_context = in_t + c_tok

                                    recent_steps.append({
                                        "index": idx + 1,
                                        "type": d.get("type", "TURN").upper(),
                                        "status": "DONE",
                                        "tools": d.get("tools", []),
                                        "total_tokens": turn_tok
                                    })
                                except Exception:
                                    continue
                except Exception:
                    pass

        denom = total_in + total_cache
        cache_eff = round((total_cache / denom) * 100, 1) if denom > 0 else 0.0
        total_tokens = total_in + total_out + total_cache

        return {
            "agent_name": self.get_agent_name(),
            "session_id": sid,
            "title": f"Codex: {sid[:12]}" if total_tokens > 0 else "Codex / Copilot: Idle",
            "model_name": model_name,
            "max_context_tokens": 200_000,
            "current_context_tokens": active_context,
            "input_tokens": total_in,
            "output_tokens": total_out,
            "cache_read_tokens": total_cache,
            "total_tokens": total_tokens,
            "cache_efficiency": cache_eff,
            "tokens_per_step": int(total_tokens / len(recent_steps)) if recent_steps else 0,
            "tokens_per_sec": 98 if codex_active else 0,
            "session_elapsed_sec": elapsed_sec,
            "recent_steps_tokens": step_burns if step_burns else [0],
            "recent_steps": recent_steps[-6:],
            "active_subagents": [
                {"name": "code-generator", "status": "ACTIVE" if codex_active else "IDLE"}
            ],
            "is_active": codex_active,
            "last_modified": last_modified
        }
