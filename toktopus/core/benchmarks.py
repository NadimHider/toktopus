import json
import urllib.request
from typing import List, Dict, Any, Optional

BENCHMARK_LAST_UPDATED: str = "2026-10-25"

BENCHMARK_MATRIX: List[Dict[str, Any]] = [
    {
        "id": "gpt-6-1",
        "name": "GPT 6.1",
        "provider": "OpenAI",
        "coding_elo": 1540,
        "swe_bench": 84.6,
        "humaneval": 98.4,
        "throughput_tps": 115,
        "price_in": 2.00,
        "price_out": 8.00,
        "rank": 1
    },
    {
        "id": "claude-5-5",
        "name": "Claude 5.5",
        "provider": "Anthropic",
        "coding_elo": 1535,
        "swe_bench": 83.9,
        "humaneval": 98.1,
        "throughput_tps": 95,
        "price_in": 2.50,
        "price_out": 10.00,
        "rank": 2
    },
    {
        "id": "deepseek-r4-1-flash",
        "name": "DeepSeek R4.1 Flash",
        "provider": "DeepSeek",
        "coding_elo": 1495,
        "swe_bench": 78.4,
        "humaneval": 96.5,
        "throughput_tps": 240,
        "price_in": 0.08,
        "price_out": 0.32,
        "rank": 3
    },
    {
        "id": "gemini-3-8-flash",
        "name": "Gemini 3.8 Flash",
        "provider": "Google DeepMind",
        "coding_elo": 1480,
        "swe_bench": 76.2,
        "humaneval": 95.8,
        "throughput_tps": 185,
        "price_in": 0.10,
        "price_out": 0.40,
        "rank": 4
    },
    {
        "id": "claude-3-7-sonnet",
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "coding_elo": 1402,
        "swe_bench": 70.3,
        "humaneval": 94.8,
        "throughput_tps": 74,
        "price_in": 3.00,
        "price_out": 15.00,
        "rank": 5
    },
    {
        "id": "o3-mini",
        "name": "OpenAI o3-mini",
        "provider": "OpenAI",
        "coding_elo": 1395,
        "swe_bench": 71.7,
        "humaneval": 95.2,
        "throughput_tps": 98,
        "price_in": 1.10,
        "price_out": 4.40,
        "rank": 6
    },
    {
        "id": "gemini-2-5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "Google DeepMind",
        "coding_elo": 1388,
        "swe_bench": 63.8,
        "humaneval": 94.2,
        "throughput_tps": 110,
        "price_in": 1.25,
        "price_out": 5.00,
        "rank": 7
    },
    {
        "id": "deepseek-r1",
        "name": "DeepSeek-R1",
        "provider": "DeepSeek",
        "coding_elo": 1365,
        "swe_bench": 51.4,
        "humaneval": 92.8,
        "throughput_tps": 38,
        "price_in": 0.55,
        "price_out": 2.19,
        "rank": 8
    },
    {
        "id": "qwen-2-5-coder-32b",
        "name": "Qwen 2.5 Coder 32B",
        "provider": "Alibaba Cloud",
        "coding_elo": 1335,
        "swe_bench": 46.8,
        "humaneval": 92.7,
        "throughput_tps": 88,
        "price_in": 0.20,
        "price_out": 0.20,
        "rank": 9
    }
]

_LIVE_CACHE: Optional[List[Dict[str, Any]]] = None
_CURRENT_UPDATED_DATE: str = BENCHMARK_LAST_UPDATED

def get_benchmarks_last_updated() -> str:
    global _CURRENT_UPDATED_DATE
    return _CURRENT_UPDATED_DATE

def get_benchmarks() -> List[Dict[str, Any]]:
    global _LIVE_CACHE
    if _LIVE_CACHE:
        return _LIVE_CACHE
    return sorted(BENCHMARK_MATRIX, key=lambda m: m["coding_elo"], reverse=True)

def find_model_benchmark(model_id_or_name: str) -> Dict[str, Any]:
    query = (model_id_or_name or "").lower()
    for m in get_benchmarks():
        if m["id"] in query or m["name"].lower() in query or query in m["name"].lower():
            return m
    return BENCHMARK_MATRIX[0]

def refresh_benchmarks_online(timeout_sec: float = 2.0) -> bool:
    global _LIVE_CACHE, _CURRENT_UPDATED_DATE
    url = "https://raw.githubusercontent.com/NadimHider/toktopus/main/data/benchmarks.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "toktopus-monitor"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if resp.status == 200:
                raw_data = json.loads(resp.read().decode("utf-8"))
                if isinstance(raw_data, dict) and "models" in raw_data:
                    data = raw_data["models"]
                    if "last_updated" in raw_data:
                        _CURRENT_UPDATED_DATE = str(raw_data["last_updated"])
                else:
                    data = raw_data

                if isinstance(data, list) and len(data) > 0:
                    _LIVE_CACHE = sorted(data, key=lambda m: m.get("coding_elo", 0), reverse=True)
                    return True
    except Exception:
        pass
    return False
