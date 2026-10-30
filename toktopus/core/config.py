import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".config" / "toktopus"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "active_agent": "antigravity",
    "plan_tier": "google-ai-pro",
    "pricing_model": "gemini-3.8-flash",
    "refresh_rate": 0.3,
    "show_benchmarks": False,
}


def load_config() -> Dict[str, Any]:
    merged = dict(DEFAULT_CONFIG)
    try:
        with CONFIG_FILE.open(encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            merged.update(data)
    except (OSError, ValueError, UnicodeError):
        pass
    try:
        rate = float(merged["refresh_rate"])
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError
        merged["refresh_rate"] = rate
    except (ValueError, TypeError, OverflowError):
        merged["refresh_rate"] = DEFAULT_CONFIG["refresh_rate"]
    if merged.get("active_agent") not in {"auto", "antigravity", "claude", "opencode", "cursor", "codex", "pi"}:
        merged["active_agent"] = DEFAULT_CONFIG["active_agent"]
    return merged


def save_config(updates: Dict[str, Any]) -> bool:
    temp_path = None
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        current = load_config()
        current.update(updates)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=CONFIG_DIR, delete=False) as file:
            temp_path = file.name
            json.dump(current, file, indent=2, allow_nan=False)
        os.replace(temp_path, CONFIG_FILE)
        return True
    except (OSError, TypeError, ValueError):
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def get_default_plan_for_agent(agent_key: str) -> str:
    defaults = {
        "antigravity": "google-ai-pro",
        "claude": "claude-pro",
        "opencode": "opencode-zen",
        "cursor": "cursor-pro",
        "codex": "codex-pro",
        "pi": "pi-pro",
    }
    return defaults.get(agent_key, "google-ai-pro")
