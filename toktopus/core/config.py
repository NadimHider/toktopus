import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path.home() / ".config" / "toktopus"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "active_agent": "antigravity",
    "plan_tier": "google-ai-pro",
    "pricing_model": "gemini-3.8-flash",
    "refresh_rate": 1.0,
    "show_benchmarks": False
}

def load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            return merged
    except Exception:
        return dict(DEFAULT_CONFIG)

def save_config(updates: Dict[str, Any]) -> bool:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        current = load_config()
        current.update(updates)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return True
    except Exception:
        return False

def get_default_plan_for_agent(agent_key: str) -> str:
    defaults = {
        "antigravity": "google-ai-pro",
        "claude": "claude-pro",
        "opencode": "opencode-zen",
        "cursor": "cursor-pro",
        "codex": "codex-pro"
    }
    return defaults.get(agent_key, "google-ai-pro")
