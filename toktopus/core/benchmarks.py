import hashlib
import json
import os
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from toktopus.core.config import CONFIG_DIR, get_benchlm_api_key
from toktopus.core.pricing import PRICING_TABLE

BENCHMARK_LAST_UPDATED: str = "2026-10-25"
BENCHLM_BASE_URL: str = "https://data.benchlm.ai/v1"
BENCHLM_CACHE_FILE: Path = CONFIG_DIR / "benchlm.json"
MAX_BYTES: int = 2_000_000
STALE_SECONDS: int = 24 * 3600

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
_CURRENT_SOURCE: str = "Bundled Index"
_CURRENT_SURFACE: str = "coding"


def get_benchmarks_last_updated() -> str:
    global _CURRENT_UPDATED_DATE
    return _CURRENT_UPDATED_DATE


def get_benchmarks_source() -> str:
    global _CURRENT_SOURCE
    return _CURRENT_SOURCE


def get_benchmarks_surface() -> str:
    global _CURRENT_SURFACE
    return _CURRENT_SURFACE


def fetch_benchlm_rankings(
    api_key: str,
    surface: str = "coding",
    limit: int = 50,
    timeout_sec: float = 6.0,
) -> Optional[Dict[str, Any]]:
    if not api_key:
        return None
    url = f"{BENCHLM_BASE_URL}/rankings/current?surface={surface}&limit={limit}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "toktopus/1.7.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if resp.status == 200:
                data = resp.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    return None
                return json.loads(data.decode("utf-8"))
    except Exception:
        return None
    return None


def fetch_benchlm_pricing(
    api_key: str,
    max_pages: int = 4,
    timeout_sec: float = 5.0,
) -> Dict[str, Dict[str, float]]:
    price_map: Dict[str, Dict[str, float]] = {}
    if not api_key:
        return price_map
    offset = 0
    for _ in range(max_pages):
        url = f"{BENCHLM_BASE_URL}/pricing?limit=100&offset={offset}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "User-Agent": "toktopus/1.7.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status != 200:
                    break
                raw = resp.read(MAX_BYTES + 1)
                data = json.loads(raw.decode("utf-8"))
                items = data.get("items", [])
                if not items:
                    break
                for p in items:
                    cur = p.get("current") or {}
                    pin = float(cur.get("input") or 0.0)
                    pout = float(cur.get("output") or 0.0)
                    cached = float(cur.get("cachedInput") or 0.0)
                    val = {"input": pin, "output": pout, "cached": cached}
                    for k in (p.get("modelKey"), p.get("slug"), p.get("name")):
                        if k:
                            price_map[str(k).lower().strip()] = val
                next_off = data.get("pagination", {}).get("nextOffset")
                if not next_off or next_off <= offset:
                    break
                offset = next_off
        except Exception:
            break
    return price_map


def normalize_benchlm_models(
    rankings_data: Dict[str, Any],
    pricing_map: Optional[Dict[str, Dict[str, float]]] = None,
) -> List[Dict[str, Any]]:
    if not isinstance(rankings_data, dict):
        return []
    items = rankings_data.get("items", [])
    if not isinstance(items, list):
        return []

    p_map = pricing_map or {}
    models: List[Dict[str, Any]] = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        model_key = str(item.get("modelKey") or item.get("slug") or f"model-{idx + 1}")
        name = str(item.get("name") or model_key.replace("-", " ").title())
        creator = str(item.get("creator") or "Unknown")
        score = float(item.get("score") or 0.0)

        # Scale BenchAlign composite (0-100) to Coding ELO index (~1100 - 1650)
        coding_elo = int(round(1000 + score * 7.0))

        # Look up price in BenchLM pricing map
        m_lower = model_key.lower().strip()
        s_lower = str(item.get("slug") or "").lower().strip()
        n_lower = name.lower().strip()

        prices = p_map.get(m_lower) or p_map.get(s_lower) or p_map.get(n_lower) or {}
        price_in = float(prices.get("input") or 0.0)
        price_out = float(prices.get("output") or 0.0)

        # If price not found in BenchLM, consult Toktopus local pricing table
        if price_in == 0.0 and price_out == 0.0:
            for p_key, p_val in PRICING_TABLE.items():
                p_k_lower = p_key.lower()
                p_name_lower = str(p_val.get("name") or "").lower()
                if p_k_lower in m_lower or p_k_lower in n_lower or n_lower in p_name_lower:
                    price_in = float(p_val.get("input") or 0.0)
                    price_out = float(p_val.get("output") or 0.0)
                    break

        swe_bench = round(score, 1)
        humaneval = round(min(99.9, max(score + 10.0, 50.0)), 1)
        rank_val = int(item.get("rank") or (idx + 1))

        models.append({
            "id": model_key,
            "name": name,
            "provider": creator,
            "coding_elo": coding_elo,
            "swe_bench": swe_bench,
            "humaneval": humaneval,
            "throughput_tps": 100,
            "price_in": price_in,
            "price_out": price_out,
            "rank": rank_val,
            "evidence_status": str(item.get("evidenceStatus") or "supported"),
            "score_interval_lower": item.get("scoreInterval90Lower"),
            "score_interval_upper": item.get("scoreInterval90Upper"),
            "url": item.get("url") or f"https://benchlm.ai/models/{model_key}",
        })

    return sorted(models, key=lambda m: m.get("coding_elo", 0), reverse=True)


def load_benchmarks(
    refresh: bool = False,
    cache_path: Optional[Path] = None,
    api_key: Optional[str] = None,
    surface: str = "coding",
    timeout_sec: float = 6.0,
) -> Dict[str, Any]:
    global _LIVE_CACHE, _CURRENT_UPDATED_DATE, _CURRENT_SOURCE, _CURRENT_SURFACE
    if cache_path is not None:
        path = Path(cache_path)
    else:
        path = CONFIG_DIR / f"benchlm_{surface}.json" if surface != "coding" else BENCHLM_CACHE_FILE
    effective_key = api_key or get_benchlm_api_key()

    snapshot: Dict[str, Any] = {
        "models": [],
        "last_updated": _CURRENT_UPDATED_DATE,
        "source": _CURRENT_SOURCE,
        "surface": surface,
        "status": "unavailable",
        "stale": False,
        "error": None,
    }

    # 1. First, check if valid cache exists on disk
    cached_models = None
    if path.exists():
        try:
            if path.stat().st_size <= MAX_BYTES * 2:
                cached = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(cached, dict) and "models" in cached and cached["models"]:
                    cached_models = cached["models"]
                    data_date = cached.get("dataAsOf") or cached.get("last_updated") or BENCHMARK_LAST_UPDATED
                    src = cached.get("source") or f"BenchLM Cached ({surface})"
                    fetched_at_str = cached.get("fetched_at")
                    stale = False
                    if fetched_at_str:
                        try:
                            fetched_dt = datetime.fromisoformat(fetched_at_str)
                            age = (datetime.now(timezone.utc) - fetched_dt).total_seconds()
                            stale = age > STALE_SECONDS
                        except Exception:
                            stale = True

                    if cache_path is None:
                        _LIVE_CACHE = cached_models
                        _CURRENT_UPDATED_DATE = str(data_date)
                        _CURRENT_SOURCE = src
                        _CURRENT_SURFACE = cached.get("surface", surface)

                    snapshot.update({
                        "models": cached_models,
                        "last_updated": str(data_date),
                        "source": src,
                        "surface": cached.get("surface", surface),
                        "status": "cached",
                        "stale": stale,
                    })
        except Exception:
            pass

    # If refresh is NOT requested, and we found cached models, return immediately
    if not refresh and cached_models:
        return snapshot

    # 2. If refresh is requested (or no cache exists and key is present)
    if refresh or (cached_models is None and effective_key):
        if effective_key:
            rankings = fetch_benchlm_rankings(effective_key, surface=surface, timeout_sec=timeout_sec)
            if rankings and isinstance(rankings, dict) and "items" in rankings and rankings["items"]:
                pricing_map = fetch_benchlm_pricing(effective_key, timeout_sec=timeout_sec)
                models = normalize_benchlm_models(rankings, pricing_map)

                if models:
                    data_date = str(rankings.get("dataAsOf") or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                    now_iso = datetime.now(timezone.utc).isoformat()
                    src_label = f"BenchLM Live ({surface})"

                    cache_payload = {
                        "schemaVersion": "toktopus-benchmarks/v1",
                        "dataAsOf": data_date,
                        "fetched_at": now_iso,
                        "surface": surface,
                        "source": src_label,
                        "models": models,
                    }

                    temp_file = None
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        with tempfile.NamedTemporaryFile(
                            mode="w", encoding="utf-8", dir=path.parent, delete=False
                        ) as f:
                            temp_file = f.name
                            json.dump(cache_payload, f, indent=2)
                        os.replace(temp_file, path)
                        temp_file = None
                    except Exception as e:
                        snapshot["error"] = f"Fetched data but failed to save cache: {e}"
                    finally:
                        if temp_file and os.path.exists(temp_file):
                            try:
                                os.unlink(temp_file)
                            except OSError:
                                pass

                    if cache_path is None:
                        _LIVE_CACHE = models
                        _CURRENT_UPDATED_DATE = data_date
                        _CURRENT_SOURCE = src_label
                        _CURRENT_SURFACE = surface

                    snapshot.update({
                        "models": models,
                        "last_updated": data_date,
                        "source": src_label,
                        "surface": surface,
                        "status": "fresh",
                        "stale": False,
                        "error": None,
                    })
                    return snapshot
            else:
                snapshot["error"] = "Failed to retrieve valid rankings from BenchLM REST API."
        else:
            snapshot["error"] = "BenchLM API key is not configured."

    # If we get here, network refresh failed or was not possible
    # If we have valid cached models from earlier, return them with the error recorded
    if cached_models:
        snapshot.update({
            "models": cached_models,
            "status": "cached",
            "stale": True,
        })
        return snapshot

    # 3. Fallback to bundled data if no cache exists
    _LIVE_CACHE = sorted(BENCHMARK_MATRIX, key=lambda m: m["coding_elo"], reverse=True)
    _CURRENT_UPDATED_DATE = BENCHMARK_LAST_UPDATED
    _CURRENT_SOURCE = "Bundled Index"

    snapshot.update({
        "models": _LIVE_CACHE,
        "last_updated": _CURRENT_UPDATED_DATE,
        "source": _CURRENT_SOURCE,
        "surface": surface,
        "status": "fallback",
        "stale": True,
    })
    return snapshot


def reset_benchmarks_cache() -> None:
    global _LIVE_CACHE, _CURRENT_UPDATED_DATE, _CURRENT_SOURCE, _CURRENT_SURFACE
    _LIVE_CACHE = None
    _CURRENT_UPDATED_DATE = BENCHMARK_LAST_UPDATED
    _CURRENT_SOURCE = "Bundled Index"
    _CURRENT_SURFACE = "coding"


def get_benchmarks(surface: str = "coding") -> List[Dict[str, Any]]:
    global _LIVE_CACHE, _CURRENT_SURFACE
    if _LIVE_CACHE is not None and _CURRENT_SURFACE == surface:
        return _LIVE_CACHE
    snapshot = load_benchmarks(refresh=False, surface=surface)
    return snapshot.get("models", BENCHMARK_MATRIX)


def find_model_benchmark(model_id_or_name: str) -> Dict[str, Any]:
    query = (model_id_or_name or "").lower().strip()
    if not query:
        benchmarks = get_benchmarks()
        return benchmarks[0] if benchmarks else BENCHMARK_MATRIX[0]

    q_hyphen = query.replace(".", "-")
    q_tokens = query.replace("-", " ").replace(".", " ").split()

    # 1. Direct or partial match in live/cached benchmarks
    for m in get_benchmarks():
        m_id = str(m.get("id") or "").lower()
        m_name = str(m.get("name") or "").lower()
        if (
            query == m_id
            or query == m_name
            or query in m_id
            or query in m_name
            or q_hyphen in m_id
            or m_id in q_hyphen
        ):
            return m

    # 2. Token overlap in live/cached benchmarks
    if len(q_tokens) >= 2:
        for m in get_benchmarks():
            m_text = (str(m.get("id") or "") + " " + str(m.get("name") or "")).lower()
            if all(t in m_text for t in q_tokens):
                return m

    # 3. Check bundled offline matrix
    for m in BENCHMARK_MATRIX:
        m_id = str(m.get("id") or "").lower()
        m_name = str(m.get("name") or "").lower()
        if (
            query == m_id
            or query == m_name
            or query in m_id
            or query in m_name
            or q_hyphen in m_id
            or m_id in q_hyphen
        ):
            return m

    benchmarks = get_benchmarks()
    return benchmarks[0] if benchmarks else BENCHMARK_MATRIX[0]


def refresh_benchmarks_online(
    timeout_sec: float = 6.0,
    surface: str = "coding",
    api_key: Optional[str] = None,
) -> bool:
    snapshot = load_benchmarks(
        refresh=True,
        surface=surface,
        api_key=api_key,
        timeout_sec=timeout_sec,
    )
    return snapshot.get("status") == "fresh"

