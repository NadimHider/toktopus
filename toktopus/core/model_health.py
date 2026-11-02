"""Read-only LiveNerf results. Refreshes are explicit and never run inference."""
import csv
import hashlib
import io
import json
import math
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from toktopus.core.config import CONFIG_DIR

SOURCE_URL = "https://raw.githubusercontent.com/ninjahawk/livenerf/main/results/daily.csv"
CACHE_FILE = CONFIG_DIR / "livenerf.json"
MAX_BYTES = 2_000_000
STALE_SECONDS = 48 * 3600


def parse_results(text):
    reader = csv.DictReader(io.StringIO(text))
    required = {"series_day", "date_utc", "model", "arm", "family", "samples", "scored", "errors", "score", "output_tokens_median", "cli_version", "harness_hash", "funding_source", "runner"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("LiveNerf CSV schema is unsupported")
    rows, seen = [], set()
    for raw in reader:
        row = {key: raw[key] for key in required}
        date.fromisoformat(row["date_utc"])
        for key in ("series_day", "samples", "scored", "errors"):
            row[key] = int(row[key])
            if row[key] < 0:
                raise ValueError("Negative sample counts")
        for key in ("score", "output_tokens_median"):
            row[key] = float(row[key])
            if not math.isfinite(row[key]) or row[key] < 0:
                raise ValueError("Invalid numeric result")
        if row["score"] > 1 or row["scored"] > row["samples"] or row["errors"] > row["samples"]:
            raise ValueError("Invalid score or counts")
        identity = tuple(row[k] for k in ("series_day", "model", "arm", "family"))
        if identity in seen:
            raise ValueError("Duplicate result row")
        seen.add(identity)
        rows.append(row)
    if not rows:
        raise ValueError("LiveNerf CSV is empty")
    return sorted(rows, key=lambda r: (r["date_utc"], r["model"], r["arm"], r["family"]))


def load_model_health(refresh=False, cache_path=None):
    """Return rows, source, fetched_at, sha256, status, stale and error.

    Without refresh this function only reads the cache. A failed refresh preserves
    the previous valid snapshot, including its original retrieval timestamp.
    """
    path = Path(cache_path) if cache_path is not None else CACHE_FILE
    snapshot = {"rows": [], "source": SOURCE_URL, "fetched_at": None, "sha256": None}
    error = None
    try:
        if path.stat().st_size > MAX_BYTES * 2:
            raise ValueError("Cache exceeds size limit")
        cached = json.loads(path.read_text(encoding="utf-8"))
        rows = parse_results(cached["csv"])
        fetched = datetime.fromisoformat(cached["fetched_at"])
        if fetched.tzinfo is None:
            raise ValueError("Missing retrieval timezone")
        snapshot.update(rows=rows, fetched_at=fetched.isoformat(), sha256=hashlib.sha256(cached["csv"].encode()).hexdigest())
    except FileNotFoundError:
        pass
    except (OSError, ValueError, TypeError, KeyError):
        error = "Cached results could not be read; refresh to retrieve a valid copy."
    if refresh:
        try:
            with urlopen(Request(SOURCE_URL, headers={"User-Agent": "Toktopus-model-health"}), timeout=8) as response:
                data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("LiveNerf response exceeds size limit")
            text = data.decode("utf-8-sig")
            rows = parse_results(text)
            fetched_at = datetime.now(timezone.utc).isoformat()
            snapshot.update(rows=rows, fetched_at=fetched_at, sha256=hashlib.sha256(text.encode()).hexdigest())
            error = None
            temp = None
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
                    temp = file.name
                    json.dump({"csv": text, "fetched_at": fetched_at}, file)
                os.replace(temp, path)
                temp = None
            except OSError:
                error = "Results fetched, but the local cache could not be saved."
            finally:
                if temp:
                    try:
                        os.unlink(temp)
                    except OSError:
                        pass
        except (OSError, ValueError, UnicodeError, TypeError):
            error = "Refresh failed; showing the last valid cached results if available."
    age = None
    if snapshot["fetched_at"]:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(snapshot["fetched_at"])).total_seconds()
    snapshot.update(status="cached" if snapshot["rows"] else "unavailable", stale=age is None or age > STALE_SECONDS, error=error)
    return snapshot
