import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from toktopus.core.benchmarks import (
    BENCHMARK_MATRIX,
    BENCHLM_BASE_URL,
    MAX_BYTES,
    find_model_benchmark,
    get_benchmarks,
    get_benchmarks_last_updated,
    get_benchmarks_source,
    load_benchmarks,
    normalize_benchlm_models,
    refresh_benchmarks_online,
    reset_benchmarks_cache,
)

SAMPLE_RANKINGS_JSON = {
    "schemaVersion": "benchlm-data-current-rankings/v1",
    "dataAsOf": "2026-11-10",
    "surface": "coding",
    "items": [
        {
            "rank": 1,
            "modelKey": "claude-fable-5-2",
            "slug": "claude-fable-5-2",
            "name": "Claude Fable 5.2",
            "creator": "Anthropic",
            "score": 86.57,
            "evidenceStatus": "estimated",
            "scoreInterval90Lower": 73.41,
            "scoreInterval90Upper": 99.73,
            "url": "https://benchlm.ai/models/claude-fable-5-2"
        },
        {
            "rank": 2,
            "modelKey": "claude-opus-5-5",
            "slug": "claude-opus-5-5",
            "name": "Claude Opus 5.5",
            "creator": "Anthropic",
            "score": 82.42,
            "evidenceStatus": "supported",
            "scoreInterval90Lower": 75.10,
            "scoreInterval90Upper": 89.74,
            "url": "https://benchlm.ai/models/claude-opus-5-5"
        }
    ]
}

SAMPLE_PRICING_JSON = {
    "schemaVersion": "data-pricing/v1",
    "dataAsOf": "2026-11-10",
    "items": [
        {
            "modelKey": "claude-fable-5-2",
            "name": "Claude Fable 5.2",
            "current": {
                "input": 8.00,
                "output": 40.00,
                "cachedInput": 2.00
            }
        },
        {
            "modelKey": "claude-opus-5-5",
            "name": "Claude Opus 5.5",
            "current": {
                "input": 4.00,
                "output": 20.00,
                "cachedInput": 1.00
            }
        }
    ]
}


class TestBenchLMIntegration(unittest.TestCase):
    def setUp(self):
        reset_benchmarks_cache()

    def tearDown(self):
        reset_benchmarks_cache()

    def test_normalize_benchlm_models(self):
        pricing_map = {
            "claude-fable-5-2": {"input": 8.0, "output": 40.0},
            "claude-opus-5-5": {"input": 4.0, "output": 20.0},
        }
        models = normalize_benchlm_models(SAMPLE_RANKINGS_JSON, pricing_map)
        self.assertEqual(len(models), 2)
        
        m1 = models[0]
        self.assertEqual(m1["id"], "claude-fable-5-2")
        self.assertEqual(m1["name"], "Claude Fable 5.2")
        self.assertEqual(m1["provider"], "Anthropic")
        self.assertEqual(m1["rank"], 1)
        self.assertEqual(m1["swe_bench"], 86.6)
        self.assertEqual(m1["price_in"], 8.0)
        self.assertEqual(m1["price_out"], 40.0)
        self.assertGreater(m1["coding_elo"], 1500)

        # Ensure sorted by ELO descending
        self.assertGreater(models[0]["coding_elo"], models[1]["coding_elo"])

    def test_normalize_handles_empty_and_malformed(self):
        self.assertEqual(normalize_benchlm_models({}), [])
        self.assertEqual(normalize_benchlm_models({"items": "invalid"}), [])
        self.assertEqual(normalize_benchlm_models({"items": [{"broken": "data"}]}), [
            {
                "id": "model-1",
                "name": "Model 1",
                "provider": "Unknown",
                "coding_elo": 1000,
                "swe_bench": 0.0,
                "humaneval": 50.0,
                "throughput_tps": 100,
                "price_in": 0.0,
                "price_out": 0.0,
                "rank": 1,
                "evidence_status": "supported",
                "score_interval_lower": None,
                "score_interval_upper": None,
                "url": "https://benchlm.ai/models/model-1",
            }
        ])

    def test_offline_load_reads_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_file = Path(tmp_dir) / "benchlm.json"
            fetched_at = datetime.now(timezone.utc).isoformat()
            cache_data = {
                "schemaVersion": "toktopus-benchmarks/v1",
                "dataAsOf": "2026-11-10",
                "fetched_at": fetched_at,
                "source": "BenchLM Live (coding)",
                "surface": "coding",
                "models": [
                    {
                        "id": "cached-model-1",
                        "name": "Cached Model 1",
                        "provider": "TestProvider",
                        "coding_elo": 1550,
                        "swe_bench": 80.0,
                        "humaneval": 90.0,
                        "throughput_tps": 100,
                        "price_in": 1.0,
                        "price_out": 2.0,
                        "rank": 1,
                    }
                ]
            }
            cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

            with patch("urllib.request.urlopen") as mock_url:
                snapshot = load_benchmarks(refresh=False, cache_path=cache_file)
                mock_url.assert_not_called()
                self.assertEqual(snapshot["status"], "cached")
                self.assertFalse(snapshot["stale"])
                self.assertEqual(len(snapshot["models"]), 1)
                self.assertEqual(snapshot["models"][0]["id"], "cached-model-1")

    def test_stale_cache_detection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_file = Path(tmp_dir) / "benchlm.json"
            old_time = (datetime.now(timezone.utc) - timedelta(hours=36)).isoformat()
            cache_data = {
                "schemaVersion": "toktopus-benchmarks/v1",
                "dataAsOf": "2026-11-08",
                "fetched_at": old_time,
                "source": "BenchLM Live (coding)",
                "models": [{"id": "old-model", "name": "Old", "coding_elo": 1400}]
            }
            cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

            snapshot = load_benchmarks(refresh=False, cache_path=cache_file)
            self.assertEqual(snapshot["status"], "cached")
            self.assertTrue(snapshot["stale"])

    def test_refresh_saves_cache_and_bounds_network(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_file = Path(tmp_dir) / "benchlm.json"
            
            rankings_bytes = json.dumps(SAMPLE_RANKINGS_JSON).encode("utf-8")
            pricing_bytes = json.dumps(SAMPLE_PRICING_JSON).encode("utf-8")

            def mock_urlopen(req, timeout=None):
                mock_resp = MagicMock()
                mock_resp.status = 200
                if "rankings" in req.full_url:
                    mock_resp.read.return_value = rankings_bytes
                else:
                    mock_resp.read.return_value = pricing_bytes
                mock_resp.__enter__.return_value = mock_resp
                return mock_resp

            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                snapshot = load_benchmarks(
                    refresh=True,
                    cache_path=cache_file,
                    api_key="test-key",
                    surface="coding"
                )
                self.assertEqual(snapshot["status"], "fresh")
                self.assertFalse(snapshot["stale"])
                self.assertEqual(len(snapshot["models"]), 2)
                self.assertTrue(cache_file.exists())

                # Verify cached file is valid JSON with models
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                self.assertEqual(len(cached["models"]), 2)
                self.assertEqual(cached["models"][0]["id"], "claude-fable-5-2")

    def test_failed_refresh_preserves_existing_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_file = Path(tmp_dir) / "benchlm.json"
            original_content = json.dumps({
                "schemaVersion": "toktopus-benchmarks/v1",
                "dataAsOf": "2026-11-09",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source": "BenchLM Cached",
                "models": [{"id": "preserved-model", "name": "Preserved", "coding_elo": 1500}]
            })
            cache_file.write_text(original_content, encoding="utf-8")

            with patch("urllib.request.urlopen", side_effect=OSError("Network unreachable")):
                snapshot = load_benchmarks(
                    refresh=True,
                    cache_path=cache_file,
                    api_key="test-key"
                )
                self.assertEqual(snapshot["status"], "cached")
                self.assertEqual(snapshot["models"][0]["id"], "preserved-model")
                self.assertEqual(cache_file.read_text(encoding="utf-8"), original_content)

    def test_find_model_benchmark(self):
        m1 = find_model_benchmark("claude-3-7-sonnet")
        self.assertIn("Claude", m1["name"])

        m2 = find_model_benchmark("gemini-2-5-pro")
        self.assertIn("Gemini", m2["name"])

        m3 = find_model_benchmark("non-existent-quantum-model-xyz")
        self.assertIsNotNone(m3)
        self.assertIn("id", m3)


if __name__ == "__main__":
    unittest.main()
