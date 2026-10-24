import os
from typing import Dict, List, Any
import psutil

AI_PROCESS_PATTERNS = [
    "language_server",
    "opencode",
    "claude",
    "cursor",
    "cursor-agent",
    "agy"
]

def get_system_telemetry() -> Dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    
    total_ram_gb = round(mem.total / (1024 ** 3), 1)
    used_ram_gb = round(mem.used / (1024 ** 3), 1)
    ram_percent = mem.percent

    ai_processes: List[Dict[str, Any]] = []
    total_ai_cpu = 0.0
    total_ai_mem_mb = 0.0

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'cmdline']):
            try:
                pname = (proc.info['name'] or '').lower()
                cmdline = " ".join(proc.info['cmdline'] or []).lower()

                matched_label = None
                if "language_server" in pname or "language_server" in cmdline:
                    matched_label = "Antigravity Language Server"
                elif "opencode" in pname or "opencode" in cmdline:
                    matched_label = "OpenCode CLI / Service"
                elif "claude" in pname or "claude" in cmdline:
                    matched_label = "Claude Code Runner"
                elif "cursor" in pname or "cursor" in cmdline:
                    matched_label = "Cursor Agent Process"
                elif any(pat in pname for pat in AI_PROCESS_PATTERNS):
                    matched_label = proc.info['name']

                if matched_label:
                    mem_mb = round((proc.info['memory_info'].rss or 0) / (1024 * 1024), 1)
                    proc_cpu = proc.info['cpu_percent'] or 0.0
                    
                    total_ai_cpu += proc_cpu
                    total_ai_mem_mb += mem_mb

                    ai_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "label": matched_label,
                        "cpu_percent": proc_cpu,
                        "mem_mb": mem_mb
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass

    ai_processes.sort(key=lambda p: p["mem_mb"], reverse=True)

    return {
        "host_cpu_percent": cpu_percent,
        "host_ram_used_gb": used_ram_gb,
        "host_ram_total_gb": total_ram_gb,
        "host_ram_percent": ram_percent,
        "ai_processes": ai_processes[:6],
        "total_ai_cpu": round(total_ai_cpu, 1),
        "total_ai_mem_mb": round(total_ai_mem_mb, 1)
    }
