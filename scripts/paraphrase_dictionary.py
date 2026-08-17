"""Paraphrase dictionary descriptions — original prose must not survive.

The source dictionary descriptions derive from vendor documentation
(verdict 2026-08-16: no vendor-proprietary content anywhere, including
prose). This script rewrites every DESCRIPTION in dict_tables.csv and
dict_columns.csv via the configured LLM endpoint, in place, preserving
technical meaning and identifiers.

Run AFTER anonymize_dictionary.py (the regeneration order is:
anonymize_sql -> anonymize_dictionary -> paraphrase_dictionary).

A content-hash cache (data/synthetic/.paraphrase_cache.json) makes
re-runs cheap and idempotent: unchanged source text never re-calls the
LLM. Outputs failing the proprietary-term scan are retried once, then
reported loudly and left UNWRITTEN (the row keeps a stub) — silence is
not an option for the egress standard.

Usage:
    python scripts/paraphrase_dictionary.py [--limit N] [--workers N]
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.anonymization import get_scan_terms, load_crosswalk, scan_for_missed  # noqa: E402
from src.llm_client import chat_completion  # noqa: E402

TABLES_CSV = PROJECT_ROOT / "data" / "synthetic" / "dict_tables.csv"
COLUMNS_CSV = PROJECT_ROOT / "data" / "synthetic" / "dict_columns.csv"
CACHE_PATH = PROJECT_ROOT / "data" / "synthetic" / ".paraphrase_cache.json"
CROSSWALK = PROJECT_ROOT / "data" / "synthetic" / "crosswalk.json"

SYSTEM = (
    "You rewrite data-dictionary descriptions in your own words. Rules: "
    "keep the exact technical meaning; keep every table and column "
    "identifier EXACTLY as written (UPPER_SNAKE tokens); one to two "
    "sentences; plain factual tone; no vendor or product names; never "
    "add information that is not in the original."
)


def _load_llm_config():
    import yaml

    cfg = yaml.safe_load(open(PROJECT_ROOT / "org_config.yaml")) or {}
    llm = cfg.get("llm") or {}  # local config may lack the block the tenant copy has
    key_file = PROJECT_ROOT / llm.get("api_key_file", "llm_api_key.txt")
    return (
        llm.get("endpoint", "https://api.openai.com/v1"),
        key_file.read_text().strip(),
        llm.get("model", "gpt-4o-mini"),
    )


def paraphrase_all(limit: "int | None" = None, workers: int = 12) -> int:
    endpoint, api_key, model = _load_llm_config()
    cache = json.load(open(CACHE_PATH)) if CACHE_PATH.exists() else {}
    scan_terms = get_scan_terms(load_crosswalk(CROSSWALK), [])
    failures: "list[str]" = []

    def rewrite(text: str, label: str) -> str:
        key = hashlib.sha256(text.encode()).hexdigest()[:24]
        if key in cache:
            return cache[key]
        import time

        out = ""
        for attempt in (1, 2, 3):
            try:
                out = chat_completion(
                    SYSTEM,
                    f"Rewrite this description:\n{text}",
                    endpoint=endpoint, api_key=api_key, model=model,
                    timeout=90,
                ).strip().strip('"')
            except Exception:  # noqa: BLE001 — transport hiccup: back off, retry
                time.sleep(3 * attempt)
                continue
            if out and out.lower() != text.lower() and not scan_for_missed(out, scan_terms):
                cache[key] = out
                return out
        failures.append(f"{label}: scan/identity failure after retry: {out[:80]!r}")
        return "(description pending re-anonymization)"

    def process(path: Path, label_fields: "tuple[str, ...]") -> None:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        todo = [r for r in rows if r["DESCRIPTION"].strip()]
        if limit:
            todo = todo[:limit]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(
                lambda r: rewrite(
                    r["DESCRIPTION"].strip(),
                    ".".join(r[k] for k in label_fields)),
                todo,
            ))
        for r, new in zip(todo, results):
            r["DESCRIPTION"] = new
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{path.name}: {len(todo)} descriptions rewritten")

    try:
        process(TABLES_CSV, ("TABLE_NAME",))
        process(COLUMNS_CSV, ("TABLE_NAME", "COLUMN_NAME"))
    finally:
        json.dump(cache, open(CACHE_PATH, "w"))

    if failures:
        print(f"\n[!] {len(failures)} descriptions could NOT be cleanly "
              f"paraphrased (stubbed, fix by hand):")
        for f_ in failures[:20]:
            print(f"  {f_}")
    return len(failures)


if __name__ == "__main__":
    limit = None
    workers = 12
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if "--workers" in sys.argv:
        workers = int(sys.argv[sys.argv.index("--workers") + 1])
    sys.exit(1 if paraphrase_all(limit, workers) else 0)
