import time
from typing import Dict, List, Any
import psutil

AI_PROCESS_NAMES = {
    "language_server": "Antigravity Language Server",
    "opencode": "OpenCode CLI / Service",
    "claude": "Claude Code Runner",
    "cursor": "Cursor Agent Process",
    "cursor-agent": "Cursor Background Agent"
}

_CACHED_PROCESSES: List[Dict[str, Any]] = []
_LAST_SCAN_TIME: float = 0.0
_SCAN_INTERVAL: float = 3.0
_INITIALIZED: bool = False

def _scan_ai_processes() -> List[Dict[str, Any]]:
    # Windows process queries are throttled here because calling cmdline across
    # every running process on every tick introduces noticeable latency.
    found_processes: List[Dict[str, Any]] = []

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                raw_name = proc.info.get('name') or ''
                lower_name = raw_name.lower()

                matched_label = None
                for key, label in AI_PROCESS_NAMES.items():
                    if key in lower_name:
                        matched_label = label
                        break

                if not matched_label and lower_name in ("python.exe", "python3.exe", "node.exe", "electron.exe"):
                    try:
                        cmdline_str = " ".join(proc.cmdline() or []).lower()
                        for key, label in AI_PROCESS_NAMES.items():
                            if key in cmdline_str:
                                matched_label = label
                                break
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass

                if matched_label:
                    mem_info = proc.info.get('memory_info')
                    rss_bytes = mem_info.rss if mem_info else 0
                    mem_mb = round(rss_bytes / (1024 * 1024), 1)
                    proc_cpu = proc.info.get('cpu_percent') or 0.0

                    found_processes.append({
                        "pid": proc.info['pid'],
                        "name": raw_name,
                        "label": matched_label,
                        "cpu_percent": proc_cpu,
                        "mem_mb": mem_mb
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass

    found_processes.sort(key=lambda p: p["mem_mb"], reverse=True)
    return found_processes

def get_system_telemetry() -> Dict[str, Any]:
    global _CACHED_PROCESSES, _LAST_SCAN_TIME, _INITIALIZED

    now = time.time()
    if not _INITIALIZED or (now - _LAST_SCAN_TIME) >= _SCAN_INTERVAL:
        _CACHED_PROCESSES = _scan_ai_processes()
        _LAST_SCAN_TIME = now
        _INITIALIZED = True

    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()

    total_ram_gb = round(mem.total / (1024 ** 3), 1)
    used_ram_gb = round(mem.used / (1024 ** 3), 1)
    ram_percent = mem.percent

    total_ai_cpu = sum(p["cpu_percent"] for p in _CACHED_PROCESSES)
    total_ai_mem_mb = sum(p["mem_mb"] for p in _CACHED_PROCESSES)

    return {
        "host_cpu_percent": cpu_percent,
        "host_ram_used_gb": used_ram_gb,
        "host_ram_total_gb": total_ram_gb,
        "host_ram_percent": ram_percent,
        "ai_processes": _CACHED_PROCESSES[:6],
        "total_ai_cpu": round(total_ai_cpu, 1),
        "total_ai_mem_mb": round(total_ai_mem_mb, 1)
    }
