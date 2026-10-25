import time
from pathlib import Path
from typing import Dict, Any

_SKILLS_CACHE: Dict[str, Any] = {}
_LAST_CHECK_TIME: float = 0.0
_CACHE_TTL: float = 30.0

def _safe_count_dirs(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    try:
        return sum(1 for p in path.iterdir() if p.is_dir() and not p.name.startswith("."))
    except Exception:
        return 0

def count_skills_and_plugins(agent_key: str = "antigravity") -> Dict[str, int]:
    global _SKILLS_CACHE, _LAST_CHECK_TIME

    now = time.time()
    cache_key = agent_key.lower()

    if cache_key in _SKILLS_CACHE and (now - _LAST_CHECK_TIME) < _CACHE_TTL:
        return _SKILLS_CACHE[cache_key]

    home = Path.home()

    if cache_key == "antigravity":
        skills_dir = home / ".gemini" / "config" / "skills"
        plugins_dir = home / ".gemini" / "config" / "plugins"
        skill_cnt = _safe_count_dirs(skills_dir)
        plugin_cnt = _safe_count_dirs(plugins_dir)
    elif cache_key == "claude":
        skills_dir = home / ".claude" / "skills"
        plugins_dir = home / ".claude" / "plugins"
        skill_cnt = _safe_count_dirs(skills_dir)
        plugin_cnt = _safe_count_dirs(plugins_dir)
    elif cache_key == "cursor":
        skills_dir = home / ".cursor" / "extensions"
        plugins_dir = home / ".cursor" / "plugins"
        skill_cnt = _safe_count_dirs(skills_dir)
        plugin_cnt = _safe_count_dirs(plugins_dir)
    elif cache_key == "opencode":
        skills_dir = home / ".config" / "opencode" / "skills"
        plugins_dir = home / ".local" / "share" / "opencode" / "plugins"
        skill_cnt = _safe_count_dirs(skills_dir)
        plugin_cnt = _safe_count_dirs(plugins_dir)
    else:
        # Default or Codex
        skills_dir = home / ".codex" / "skills"
        plugins_dir = home / ".codex" / "plugins"
        skill_cnt = _safe_count_dirs(skills_dir)
        plugin_cnt = _safe_count_dirs(plugins_dir)

    result = {
        "skills": skill_cnt,
        "plugins": plugin_cnt
    }

    _SKILLS_CACHE[cache_key] = result
    _LAST_CHECK_TIME = now
    return result
