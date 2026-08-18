# Collibra Asset Match: which Collibra PBI Report asset gets the description?
# Publishing-side matching, NOT lineage (lineage is TMDL partition parsing,
# ADR 0040). Exact TMDL-derived report names (input_metric_names) match
# deterministically; the _PBI-suffix fuzzy heuristic is the fallback for
# objects 060_ingest_semantic_models has not covered.
# Uses credentials from org_config.yaml.

# %% Cell 1: Setup
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
# For local: sys.path.insert(0, ".")

from src.adapters.collibra_lineage import CollibraClient
from src.adapters.collibra_lineage_match import CollibraLineageMatcher
from src.config import load_config

config = load_config()
collibra_cfg = config.adapters.collibra

base = collibra_cfg.base_url.replace("/rest/2.0", "")
client = CollibraClient(base, collibra_cfg.username, collibra_cfg.password)

print("Testing connection...")
if client.test_connection():
    print("Connected!")
else:
    print("Connection failed.")

# %% Cell 2: Match procs/views to PBI reports
# Add your _PBI-suffixed procs and views here.
# Only names ending in _PBI will be matched; others are skipped.

objects = [
    # -- Views --
    # {"object_name": "V_CCHP_SomeReport_PBI", "object_type": "VIEW"},
    # {"object_name": "V_CCHP_340B_Charges_PBI", "object_type": "VIEW"},
    # -- Procs --
    # {"object_name": "USP_CCHP_ED_Sepsis_PBI", "object_type": "SQL_STORED_PROCEDURE"},
    # {"object_name": "USP_CCHP_IP_Sepsis_Compliance_PBI", "object_type": "SQL_STORED_PROCEDURE"},
]

# To auto-populate from extraction_tracking, uncomment:
# import pandas as pd
# tracking = spark.read.format("delta").load("Tables/extraction_tracking")
# objects = [
#     {"object_name": row.object_name, "object_type": row.object_type}
#     for row in tracking.collect()
# ]

# Exact names from TMDL lineage (060_ingest_semantic_models): objects in
# this mapping match deterministically, skipping the fuzzy heuristic.
known_report_names = {}
if spark.catalog.tableExists("input_metric_names"):  # noqa: F821
    for row in spark.table("input_metric_names").collect():  # noqa: F821
        # first-listed report is the naming report (see semantic_models)
        first_report = (row["report_name"] or "").split(";")[0].strip()
        if row["source"] == "pbi_report" and first_report:
            known_report_names[row["metric_id"].split(".")[-1]] = first_report
    print(f"Exact report names from input_metric_names: {len(known_report_names)}")

matcher = CollibraLineageMatcher(client, min_score=0.5)
result = matcher.match_objects(objects, known_report_names=known_report_names)
print(result)

# %% Cell 3: Review matches
print(f"\n{'='*80}")
print(f"MATCHED ({len(result.matched)})")
print(f"{'='*80}")
for m in result.matched:
    print(f"  {m.object_name}")
    print(f"    key:    '{m.extracted_key}'")
    print(f"    report: {m.report_name}")
    print(f"    score:  {m.score:.2f}")
    print()

if result.unmatched_objects:
    print(f"{'='*80}")
    print(f"UNMATCHED ({len(result.unmatched_objects)})")
    print(f"{'='*80}")
    for name in result.unmatched_objects:
        from src.adapters.collibra_lineage_match import extract_match_key
        print(f"  {name}  (key: '{extract_match_key(name)}')")

# %% Cell 4: Test a single name interactively
from src.adapters.collibra_lineage_match import extract_match_key

test_name = "V_CCHP_340B_Charges_PBI"  # TODO: change to test different names
key = extract_match_key(test_name)
print(f"Object:  {test_name}")
print(f"Key:     {key}")

if key:
    match = matcher.match_object(test_name)
    if match:
        print(f"Matched: {match.report_name} (score={match.score:.2f})")
    else:
        print("No match found above threshold")
