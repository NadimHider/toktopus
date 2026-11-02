import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from toktopus.core.model_health import MAX_BYTES, load_model_health, parse_results
from toktopus.ui.model_health import render_model_health

CSV = "series_day,date_utc,model,arm,family,samples,scored,errors,score,output_tokens_median,cli_version,harness_hash,funding_source,runner\n1,2026-09-24,model,measured,all,78,78,0,0.5,588,2.1,abc,max,host\n1,2026-09-24,model,measured,math,4,4,0,0.5,500,2.1,abc,max,host\n"


class ModelHealthTests(unittest.TestCase):
    def test_rejects_invalid_and_duplicate_results(self):
        for data in ("bad,schema\na,b", CSV.replace("0.5", "nan"), CSV.replace("0.5", "1.1"), CSV + CSV.splitlines()[1] + "\n", CSV.replace(",78,78,", ",78,79,")):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    parse_results(data)

    def test_offline_is_network_free(self):
        with tempfile.TemporaryDirectory() as directory, patch("toktopus.core.model_health.urlopen") as fetch:
            result = load_model_health(cache_path=Path(directory) / "cache.json")
            self.assertEqual(result["status"], "unavailable")
            fetch.assert_not_called()

    def test_failed_refresh_preserves_cache_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            timestamp = "2020-01-01T00:00:00+00:00"
            content = json.dumps({"csv": CSV, "fetched_at": timestamp})
            path.write_text(content, encoding="utf-8")
            with patch("toktopus.core.model_health.urlopen", side_effect=OSError("offline")):
                result = load_model_health(True, path)
            self.assertEqual(len(result["rows"]), 2)
            self.assertEqual(result["fetched_at"], timestamp)
            self.assertTrue(result["stale"])
            self.assertTrue(result["error"])
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_refresh_caches_valid_results_and_bounds_read(self):
        with tempfile.TemporaryDirectory() as directory, patch("toktopus.core.model_health.urlopen") as fetch:
            fetch.return_value.__enter__.return_value.read.return_value = CSV.encode()
            path = Path(directory) / "cache.json"
            result = load_model_health(True, path)
            self.assertEqual(len(result["rows"]), 2)
            self.assertIsNone(result["error"])
            fetch.return_value.__enter__.return_value.read.assert_called_once_with(MAX_BYTES + 1)
            self.assertEqual(load_model_health(cache_path=path)["sha256"], result["sha256"])

    def test_bad_download_does_not_replace_good_cache(self):
        with tempfile.TemporaryDirectory() as directory, patch("toktopus.core.model_health.urlopen") as fetch:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps({"csv": CSV, "fetched_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
            fetch.return_value.__enter__.return_value.read.return_value = b"<html>error</html>"
            result = load_model_health(True, path)
            self.assertEqual(len(result["rows"]), 2)
            self.assertTrue(result["error"])

    def test_view_separates_aggregate_and_family_rows(self):
        console = Console(record=True, width=180)
        console.print(render_model_health({"rows": parse_results(CSV), "source": "public", "stale": True}))
        rendered = console.export_text()
        self.assertIn("not summed", rendered)
        self.assertIn("math", rendered)
        self.assertIn("No statistical drift verdict", rendered)


if __name__ == "__main__":
    unittest.main()
