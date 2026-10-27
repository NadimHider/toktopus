import os
import time
import subprocess
import shutil
from typing import Dict, List, Any, Optional
import psutil

AI_PROCESS_NAMES = {
    "antigravity": "Antigravity Agent",
    "opencode": "OpenCode CLI / Service",
    "claude": "Claude Code Runner",
    "cursor": "Cursor Agent Process",
    "cursor-agent": "Cursor Background Agent",
    "copilot": "GitHub Copilot Agent",
    "codex": "OpenAI Codex Process"
}

_CACHED_PROCESSES: List[Dict[str, Any]] = []
_CACHED_GPU: Optional[Dict[str, Any]] = None
_LAST_SCAN_TIME: float = 0.0
_SCAN_INTERVAL: float = 3.0
_INITIALIZED: bool = False

def _scan_ai_processes() -> List[Dict[str, Any]]:
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

                # Also inspect language_server if it explicitly mentions antigravity or gemini
                if not matched_label and "language_server" in lower_name:
                    try:
                        cmdline_str = " ".join(proc.cmdline() or []).lower()
                        if "antigravity" in cmdline_str or "gemini" in cmdline_str:
                            matched_label = "Antigravity Language Server"
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass

                # Inspect script runners on Windows, Linux, and macOS
                is_script_runner = lower_name in (
                    "python.exe", "python3.exe", "node.exe", "electron.exe",
                    "python", "python3", "node", "electron"
                )
                if not matched_label and is_script_runner:
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

def _scan_gpu_telemetry() -> Optional[Dict[str, Any]]:
    if not shutil.which("nvidia-smi"):
        return None

    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,memory.total,name",
            "--format=csv,noheader,nounits"
        ]
        creationflags = 0x08000000 if os.name == "nt" else 0
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1.0, creationflags=creationflags)
        if proc.returncode == 0 and proc.stdout.strip():
            first_line = proc.stdout.strip().splitlines()[0]
            parts = [p.strip() for p in first_line.split(",")]
            if len(parts) >= 4:
                return {
                    "gpu_util_percent": float(parts[0]),
                    "vram_used_mb": float(parts[1]),
                    "vram_total_mb": float(parts[2]),
                    "gpu_name": parts[3]
                }
    except Exception:
        pass
    return None

def get_system_telemetry() -> Dict[str, Any]:
    global _CACHED_PROCESSES, _CACHED_GPU, _LAST_SCAN_TIME, _INITIALIZED

    now = time.time()
    if not _INITIALIZED or (now - _LAST_SCAN_TIME) >= _SCAN_INTERVAL:
        _CACHED_PROCESSES = _scan_ai_processes()
        _CACHED_GPU = _scan_gpu_telemetry()
        _LAST_SCAN_TIME = now
        _INITIALIZED = True

    cpu_percent = psutil.cpu_percent(interval=None) or 0.0
    mem = psutil.virtual_memory()

    total_ram_gb = round(mem.total / (1024 ** 3), 1)
    used_ram_gb = round(mem.used / (1024 ** 3), 1)
    ram_percent = mem.percent or 0.0

    total_ai_cpu = sum(p.get("cpu_percent", 0.0) or 0.0 for p in _CACHED_PROCESSES)
    total_ai_mem_mb = sum(p.get("mem_mb", 0.0) or 0.0 for p in _CACHED_PROCESSES)

    return {
        "host_cpu_percent": cpu_percent,
        "host_ram_used_gb": used_ram_gb,
        "host_ram_total_gb": total_ram_gb,
        "host_ram_percent": ram_percent,
        "ai_processes": _CACHED_PROCESSES[:6],
        "total_ai_cpu": round(total_ai_cpu, 1),
        "total_ai_mem_mb": round(total_ai_mem_mb, 1),
        "gpu": _CACHED_GPU
    }
