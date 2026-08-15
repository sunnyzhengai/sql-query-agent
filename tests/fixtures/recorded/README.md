# Recorded ScriptDom Fixtures

Anonymized parse results recorded from a Fabric run — real ScriptDom output,
so offline tests exercise the pipeline against production parser truth
(the sqlglot fallback produces *different* structure on hard cases).

## How to (re)record

1. On Fabric, run the `export_test_fixtures` notebook (repo root; requires the
   crosswalk uploaded; the notebook BLOCKS if any proprietary term survives
   anonymization).
2. Download from `Files/sql-query-agent/fixtures_export/`:
   `parse_results.json`, `dict_tables.json`, `dict_columns.json`, `manifest.json`
3. Place them in this directory.
4. Run `pytest tests/test_recorded_pipeline.py` — it re-scans the files for
   proprietary terms (defense in depth) and replays the full pipeline.
5. Commit. CI replays the pipeline on ScriptDom truth on every push.

Until fixtures are recorded, the recorded-pipeline tests skip (the sample
corpus keeps covering the pipeline via the fallback parser).
