# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "f7c297eb-4659-4600-ab89-0e860638fb6c",
# META       "default_lakehouse_name": "sql_query_lh",
# META       "default_lakehouse_workspace_id": "1f55e1c1-b660-4715-9b56-4140edce3940",
# META       "known_lakehouses": [
# META         {
# META           "id": "f7c297eb-4659-4600-ab89-0e860638fb6c"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "0776fc8d-1451-838d-47e6-f5c7a0bd174b",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# CELL ********************

"""Fabric Notebook (utility): Export anonymized test fixtures.

Records ScriptDom ground truth for offline testing (the record-replay
strategy): selects a representative subset of ops_parse_results plus the
dictionary rows it references, anonymizes everything through the crosswalk,
BLOCKS if any proprietary term survives, and writes JSON files for download.

Run once per corpus refresh. Afterwards:
  1. Download the files from Files/sql-query-agent/fixtures_export/
  2. Place them in tests/fixtures/recorded/ in the repo
  3. Run: pytest tests/test_recorded_pipeline.py  (validates + replays)
  4. Commit — CI then replays the full pipeline on ScriptDom truth forever

Requires: Files/sql-query-agent/data/synthetic/crosswalk.json uploaded
(the proprietary->anonymized mapping, including _scan_terms).
"""

# %% Cell 1: Setup
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.anonymization import (
    anonymize_record,
    build_replacements,
    get_scan_terms,
    load_crosswalk,
    scan_for_missed,
)
from src.parser.identity import fold_identifier

# The crosswalk can live either next to org_config.yaml (clean wheel-based
# deployments) or at its repo path (full-repo-upload deployments).
CROSSWALK_CANDIDATES = [
    "/lakehouse/default/Files/sql-query-agent/crosswalk.json",
    "/lakehouse/default/Files/sql-query-agent/data/synthetic/crosswalk.json",
]
EXPORT_DIR = "/lakehouse/default/Files/sql-query-agent/fixtures_export"

# How many metrics to record. Selection is spread across the complexity
# range (by cte_count) so hard cases are represented, not just easy ones.
MAX_METRICS = 40

CROSSWALK_PATH = next((p for p in CROSSWALK_CANDIDATES if os.path.exists(p)), None)
if CROSSWALK_PATH is None:
    print("[X] FATAL: crosswalk.json not found. Looked in:")
    for p in CROSSWALK_CANDIDATES:
        print(f"    {p}")
    print("    Upload data/synthetic/crosswalk.json from the repo to")
    print("    Files/sql-query-agent/ (next to org_config.yaml).")
    raise SystemExit("Cannot export without the anonymization crosswalk.")
print(f"Crosswalk file: {CROSSWALK_PATH}")

crosswalk = load_crosswalk(CROSSWALK_PATH)
replacements = build_replacements(crosswalk)
scan_terms = get_scan_terms(crosswalk)
if not scan_terms:
    print("[X] FATAL: crosswalk has no _scan_terms — the leak gate cannot run.")
    raise SystemExit("Add _scan_terms to the crosswalk before exporting.")
print(f"Crosswalk: {len(replacements)} replacement rules, {len(scan_terms)} scan terms")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Select a representative subset
all_results = [r.asDict() for r in spark.table("ops_parse_results").collect()]
all_results.sort(key=lambda r: (r.get("cte_count") or 0, r["metric_id"]))

if len(all_results) <= MAX_METRICS:
    selected = all_results
else:
    step = len(all_results) / MAX_METRICS
    selected = [all_results[int(i * step)] for i in range(MAX_METRICS)]

print(f"Selected {len(selected)}/{len(all_results)} parse results "
      f"(cte_count {selected[0].get('cte_count')} .. {selected[-1].get('cte_count')})")

# Dictionary rows for tables the selected results reference (case-folded match)
referenced = set()
for r in selected:
    for blob in (r.get("ctes_json") or "[]", r.get("final_select_tables") or "[]"):
        for item in json.loads(blob):
            refs = item.get("table_refs", []) if isinstance(item, dict) and "table_refs" in item else (
                [item] if isinstance(item, dict) and "table" in item else [])
            for t in refs:
                name = t["table"] if isinstance(t, dict) else t
                referenced.add(fold_identifier(name))

dict_tables = [r.asDict() for r in spark.table("input_dict_tables").collect()
               if fold_identifier(r["TABLE_NAME"]) in referenced]
dict_columns = [r.asDict() for r in spark.table("input_dict_columns").collect()
                if fold_identifier(r["TABLE_NAME"]) in referenced]
print(f"Dictionary slice: {len(dict_tables)} tables, {len(dict_columns)} columns "
      f"(of {len(referenced)} referenced)")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Anonymize everything
anon_results, anon_tables, anon_columns = [], [], []
total_replacements = 0
for row in selected:
    out, log = anonymize_record(row, replacements)
    anon_results.append(out)
    total_replacements += len(log)
for row in dict_tables:
    out, log = anonymize_record(row, replacements)
    anon_tables.append(out)
    total_replacements += len(log)
for row in dict_columns:
    out, log = anonymize_record(row, replacements)
    anon_columns.append(out)
    total_replacements += len(log)
print(f"Applied anonymization: {total_replacements} replacement hits")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 4: Leak gate — nothing proprietary may leave this tenant
payload = json.dumps({"r": anon_results, "t": anon_tables, "c": anon_columns})
leaks = scan_for_missed(payload, scan_terms)
if leaks:
    print(f"[X] FATAL: {len(leaks)} proprietary term(s) survived anonymization:")
    for warning in leaks[:20]:
        print(warning)
    print("    Extend the crosswalk to cover these, then re-run.")
    raise SystemExit("Export blocked — fixtures are not clean.")
print("[+] Leak gate passed: no scan terms found in the export payload")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 5: Write export files
os.makedirs(EXPORT_DIR, exist_ok=True)
manifest = {
    "exported_at": datetime.now(timezone.utc).isoformat(),
    "parse_results": len(anon_results),
    "dict_tables": len(anon_tables),
    "dict_columns": len(anon_columns),
    "source_corpus_size": len(all_results),
    "crosswalk_rules": len(replacements),
    "scan_terms_checked": len(scan_terms),
}
for fname, data in [
    ("parse_results.json", anon_results),
    ("dict_tables.json", anon_tables),
    ("dict_columns.json", anon_columns),
    ("manifest.json", manifest),
]:
    with open(os.path.join(EXPORT_DIR, fname), "w") as f:
        json.dump(data, f, indent=1)
    print(f"  wrote {fname}")

print("\n=== Export complete ===")
print(f"Download the 4 files from Files/sql-query-agent/fixtures_export/")
print(f"Place them in tests/fixtures/recorded/ and run:")
print(f"  pytest tests/test_recorded_pipeline.py")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
