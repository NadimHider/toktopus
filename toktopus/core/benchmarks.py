"""
AI Model Benchmark Index and leaderboards for toktopus.
Tracks LMSYS Chatbot Arena Coding ELO, SWE-bench, HumanEval, and throughput.
"""

from typing import List, Dict, Any

# Benchmark data matrix (calibrated against Chatbot Arena & SWE-bench Verified)
BENCHMARK_MATRIX: List[Dict[str, Any]] = [
    {
        "id": "claude-3-7-sonnet",
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "coding_elo": 1372,
        "swe_bench": 70.3,
        "humaneval": 92.4,
        "throughput_tps": 74,
        "price_in": 3.00,
        "price_out": 15.00,
        "rank": 1
    },
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
        "provider": "Google DeepMind",
        "coding_elo": 1345,
        "swe_bench": 48.6,
        "humaneval": 89.2,
        "throughput_tps": 142,
        "price_in": 0.10,
        "price_out": 0.40,
        "rank": 2
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "OpenAI",
        "coding_elo": 1338,
        "swe_bench": 53.8,
        "humaneval": 90.2,
        "throughput_tps": 108,
        "price_in": 2.50,
        "price_out": 10.00,
        "rank": 3
    },
    {
        "id": "deepseek-r1",
        "name": "DeepSeek-R1",
        "provider": "DeepSeek",
        "coding_elo": 1340,
        "swe_bench": 49.2,
        "humaneval": 91.5,
        "throughput_tps": 32,
        "price_in": 0.55,
        "price_out": 2.19,
        "rank": 4
    },
    {
        "id": "deepseek-v3",
        "name": "DeepSeek-V3",
        "provider": "DeepSeek",
        "coding_elo": 1320,
        "swe_bench": 49.2,
        "humaneval": 88.5,
        "throughput_tps": 62,
        "price_in": 0.14,
        "price_out": 0.28,
        "rank": 5
    },
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash-Lite",
        "provider": "Google DeepMind",
        "coding_elo": 1285,
        "swe_bench": 39.4,
        "humaneval": 84.1,
        "throughput_tps": 185,
        "price_in": 0.075,
        "price_out": 0.30,
        "rank": 6
    },
    {
        "id": "claude-3-5-haiku",
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic",
        "coding_elo": 1270,
        "swe_bench": 40.6,
        "humaneval": 85.0,
        "throughput_tps": 120,
        "price_in": 0.80,
        "price_out": 4.00,
        "rank": 7
    }
]

def get_benchmarks() -> List[Dict[str, Any]]:
    """Return list of models sorted by Coding ELO."""
    return sorted(BENCHMARK_MATRIX, key=lambda m: m["coding_elo"], reverse=True)

def find_model_benchmark(model_id_or_name: str) -> Dict[str, Any]:
    """Find benchmark entry matching a model identifier or return default."""
    query = model_id_or_name.lower().replace("_", "-")
    for m in BENCHMARK_MATRIX:
        if m["id"] in query or query in m["id"] or m["name"].lower() in query:
            return m
    # Fallback to Gemini 3.8 Flash
    return BENCHMARK_MATRIX[1]
