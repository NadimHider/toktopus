import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME_DIR = Path.home()

AGENT_SKILL_PATHS: Dict[str, List[Path]] = {
    "antigravity": [
        HOME_DIR / ".gemini" / "config" / "skills",
        HOME_DIR / ".gemini" / "config" / "plugins",
        HOME_DIR / ".gemini" / "antigravity-cli" / "skills"
    ],
    "claude": [
        HOME_DIR / ".claude" / "skills",
        HOME_DIR / ".claude" / "plugins"
    ],
    "opencode": [
        HOME_DIR / ".config" / "opencode" / "skills",
        HOME_DIR / ".local" / "share" / "opencode" / "skills",
        Path(os.environ.get("LOCALAPPDATA", "")) / "opencode" / "skills" if os.environ.get("LOCALAPPDATA") else None,
        Path(os.environ.get("APPDATA", "")) / "opencode" / "skills" if os.environ.get("APPDATA") else None
    ],
    "codex": [
        HOME_DIR / ".codex" / "skills",
        HOME_DIR / ".copilot" / "skills",
        Path(os.environ.get("LOCALAPPDATA", "")) / "github-copilot" / "skills" if os.environ.get("LOCALAPPDATA") else None
    ],
    "cursor": [
        HOME_DIR / ".cursor" / "skills",
        HOME_DIR / ".cursor" / "extensions",
        Path(os.environ.get("APPDATA", "")) / "Cursor" / "skills" if os.environ.get("APPDATA") else None,
        Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "skills" if os.environ.get("APPDATA") else None
    ],
    "pi": [
        HOME_DIR / ".pi" / "skills",
        HOME_DIR / ".config" / "pi" / "skills"
    ]
}


for _k in AGENT_SKILL_PATHS:
    AGENT_SKILL_PATHS[_k] = [p for p in AGENT_SKILL_PATHS[_k] if p is not None]

_SKILLS_CACHE: Dict[str, Any] = {}
_LAST_CHECK_TIME: float = 0.0
_CACHE_TTL: float = 15.0

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
    cache_key = (agent_key or "antigravity").lower()

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
    elif cache_key == "pi":
        skills_dir = home / ".pi" / "skills"
        plugins_dir = home / ".config" / "pi" / "plugins"
        skill_cnt = _safe_count_dirs(skills_dir)
        plugin_cnt = _safe_count_dirs(plugins_dir)
    else:
        skills_dir = home / ".codex" / "skills"
        plugins_dir = home / ".codex" / "plugins"
        skill_cnt = _safe_count_dirs(skills_dir)
        plugin_cnt = _safe_count_dirs(plugins_dir)

    result = {
        "skills": skill_cnt,
        "plugins": plugin_cnt,
        "skills_count": skill_cnt,
        "plugins_count": plugin_cnt
    }

    _SKILLS_CACHE[cache_key] = result
    _LAST_CHECK_TIME = now
    return result

def get_all_agents_skill_summary() -> Dict[str, Dict[str, int]]:
    agents = ["antigravity", "claude", "opencode", "cursor", "codex", "pi"]
    return {ag: count_skills_and_plugins(ag) for ag in agents}

def _parse_frontmatter(content: str) -> tuple[Dict[str, str], str]:
    frontmatter: Dict[str, str] = {}
    body = content

    pattern = r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        fm_text = match.group(1)
        body = match.group(2)
        for line in fm_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                clean_k = k.strip()
                clean_v = v.strip().strip("\"'")
                frontmatter[clean_k] = clean_v

    return frontmatter, body

def _build_frontmatter_text(frontmatter: Dict[str, str]) -> str:
    if not frontmatter:
        return ""
    lines = ["---"]
    for k, v in frontmatter.items():
        lines.append(f"{k}: {v}")
    lines.append("---\n")
    return "\n".join(lines)

def list_installed_skills(agent_key: Optional[str] = None) -> List[Dict[str, Any]]:
    agents_to_check = [agent_key.lower()] if agent_key else list(AGENT_SKILL_PATHS.keys())
    results: List[Dict[str, Any]] = []
    seen_paths = set()

    for ag in agents_to_check:
        base_paths = AGENT_SKILL_PATHS.get(ag, [])
        for base_p in base_paths:
            if not base_p.exists():
                continue


            try:
                for entry in base_p.iterdir():
                    if not entry.is_dir() or entry.name.startswith("."):
                        continue


                    skill_md = entry / "SKILL.md"
                    if not skill_md.exists():

                        for f in entry.iterdir():
                            if f.name.lower() == "skill.md":
                                skill_md = f
                                break


                    if not skill_md.exists():
                        nested_skills = entry / "skills"
                        if nested_skills.exists() and nested_skills.is_dir():
                            for n_entry in nested_skills.iterdir():
                                if n_entry.is_dir() and not n_entry.name.startswith("."):
                                    n_md = n_entry / "SKILL.md"
                                    if n_md.exists() and str(n_md) not in seen_paths:
                                        seen_paths.add(str(n_md))
                                        results.append(_inspect_skill_dir(n_entry, n_md, ag))
                        continue

                    if skill_md.exists() and str(skill_md) not in seen_paths:
                        seen_paths.add(str(skill_md))
                        results.append(_inspect_skill_dir(entry, skill_md, ag))
            except Exception:
                continue

    results.sort(key=lambda x: (x["agent"], x["name"]))
    return results

def _inspect_skill_dir(dir_path: Path, skill_md_path: Path, agent_name: str) -> Dict[str, Any]:
    name = dir_path.name
    desc = ""
    mtime = 0.0
    size = 0

    if skill_md_path.exists():
        try:
            st = skill_md_path.stat()
            mtime = st.st_mtime
            size = st.st_size
            with open(skill_md_path, "r", encoding="utf-8", errors="ignore") as f:
                header = f.read(2048)
            fm, body = _parse_frontmatter(header)
            desc = fm.get("description", "")
            if not desc:

                for line in body.splitlines():
                    clean = line.strip().lstrip("#").strip()
                    if clean:
                        desc = clean[:120]
                        break
            name = fm.get("name", name)
        except Exception:
            pass

    return {
        "name": name,
        "agent": agent_name,
        "path": str(dir_path),
        "skill_file": str(skill_md_path),
        "description": desc,
        "size_bytes": size,
        "last_modified": mtime
    }

def get_skill(skill_name: str, agent_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    target = skill_name.strip().lower()
    all_skills = list_installed_skills(agent_key)

    matched = None
    for s in all_skills:
        if s["name"].lower() == target:
            matched = s
            break
        if target in s["name"].lower():
            matched = s

    if not matched:

        p = Path(skill_name)
        if p.exists():
            md_path = p if p.name.lower() == "skill.md" else (p / "SKILL.md")
            if md_path.exists():
                matched = _inspect_skill_dir(p if p.is_dir() else p.parent, md_path, agent_key or "custom")

    if not matched:
        return None

    skill_file = Path(matched["skill_file"])
    if not skill_file.exists():
        return None

    try:
        with open(skill_file, "r", encoding="utf-8", errors="ignore") as f:
            full_content = f.read()

        fm, instructions = _parse_frontmatter(full_content)
        return {
            "name": matched["name"],
            "agent": matched["agent"],
            "folder_path": matched["path"],
            "skill_file": str(skill_file),
            "frontmatter": fm,
            "description": fm.get("description", matched.get("description", "")),
            "instructions": instructions.strip(),
            "full_content": full_content,
            "size_bytes": len(full_content.encode("utf-8")),
            "last_modified": skill_file.stat().st_mtime
        }
    except Exception:
        return None

def modify_skill(
    skill_name: str,
    instruction_delta: str,
    agent_key: Optional[str] = None,
    mode: str = "append",
    new_description: Optional[str] = None,
    backup: bool = True
) -> bool:
    skill_info = get_skill(skill_name, agent_key)
    if not skill_info:
        return False

    file_path = Path(skill_info["skill_file"])
    if not file_path.exists():
        return False

    try:
        if backup:
            bak_path = file_path.with_suffix(".md.bak")
            shutil.copy2(file_path, bak_path)

        fm = skill_info.get("frontmatter", {})
        if new_description is not None:
            fm["description"] = new_description

        orig_instructions = skill_info.get("instructions", "")
        clean_delta = instruction_delta.strip()

        if mode == "append":
            new_instructions = orig_instructions + "\n\n" + clean_delta if orig_instructions else clean_delta
        elif mode == "prepend":
            new_instructions = clean_delta + "\n\n" + orig_instructions if orig_instructions else clean_delta
        elif mode == "replace":
            new_instructions = clean_delta
        else:
            new_instructions = orig_instructions + "\n\n" + clean_delta

        fm_header = _build_frontmatter_text(fm)
        final_text = fm_header + new_instructions.strip() + "\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_text)


        _SKILLS_CACHE.clear()
        return True
    except Exception:
        return False

def create_skill(
    skill_name: str,
    agent_key: str = "antigravity",
    instructions: str = "",
    description: str = ""
) -> Optional[Path]:
    ag = (agent_key or "antigravity").lower()
    base_paths = AGENT_SKILL_PATHS.get(ag)
    if not base_paths:
        base_paths = AGENT_SKILL_PATHS["antigravity"]

    target_dir = base_paths[0] / skill_name
    target_dir.mkdir(parents=True, exist_ok=True)

    skill_file = target_dir / "SKILL.md"
    fm = {
        "name": skill_name,
        "description": description or f"Skill {skill_name} for {agent_key}"
    }

    fm_text = _build_frontmatter_text(fm)
    body = instructions.strip() if instructions else f"# {skill_name}\n\nInstructions for {skill_name}."
    full_text = fm_text + body + "\n"

    try:
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        _SKILLS_CACHE.clear()
        return skill_file
    except Exception:
        return None

def copy_skill(skill_name: str, from_agent: str, to_agent: str) -> bool:
    src_info = get_skill(skill_name, from_agent)
    if not src_info:
        return False

    dest_paths = AGENT_SKILL_PATHS.get(to_agent.lower())
    if not dest_paths:
        return False

    dest_dir = dest_paths[0] / src_info["name"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "SKILL.md"

    try:
        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(src_info["full_content"])
        _SKILLS_CACHE.clear()
        return True
    except Exception:
        return False
