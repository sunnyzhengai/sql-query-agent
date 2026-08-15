# DevOps TMDL Lineage Extraction
# Reads PBI report definitions from Azure DevOps to extract:
# 1. SQL sources (deterministic lineage to views/procs)
# 2. DAX measures and calculated columns (PBI-layer transforms)

# %% Cell 1: Setup
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
# For local: sys.path.insert(0, ".")

from src.extractor.devops_tmdl import DevOpsTmdlClient

# ── DevOps credentials ──
ORG = "CookChildrens"
PROJECT = "Business Intelligence and Analytics"
PAT = ""  # TODO: fill in your DevOps PAT (Code Read scope)

client = DevOpsTmdlClient(ORG, PROJECT, PAT)

# Verify connection
repos = client.list_repos()
print(f"Connected! Found {len(repos)} repos:")
for r in repos[:10]:
    print(f"  {r['name']}")

# %% Cell 2: Extract lineage for one repo
REPO_NAME = "BI-TST-Health Plan"

# Find all semantic models
models = client.find_semantic_models(REPO_NAME)
print(f"\nFound {len(models)} reports in {REPO_NAME}:")
for m in models:
    print(f"  {m['report_name']}")

# %% Cell 3: Extract lineage for a single report (test)
test_model = models[0] if models else None
if test_model:
    lineage = client.extract_report_lineage(REPO_NAME, test_model)

    print(f"\n{'='*80}")
    print(f"Report: {lineage.report_name}")
    print(f"{'='*80}")

    print(f"\nSQL Sources ({len(lineage.sql_sources)}):")
    for s in lineage.sql_sources:
        print(f"  {s.table_name} → {s.schema}.{s.sql_object} ({s.sql_object_type})")
        print(f"    Server: {s.server}, Database: {s.database}")

    print(f"\nDAX Measures ({len([d for d in lineage.dax_expressions if d.expression_type == 'measure'])}):")
    for d in lineage.dax_expressions:
        if d.expression_type == "measure":
            print(f"  [{d.table_name}] {d.name} = {d.expression[:80]}")

    calc_cols = [d for d in lineage.dax_expressions if d.expression_type == 'calculated_column']
    print(f"\nCalculated Columns ({len(calc_cols)}):")
    for d in lineage.dax_expressions:
        if d.expression_type == "calculated_column":
            print(f"  [{d.table_name}] {d.name} = {d.expression[:80]}")

# %% Cell 4: Extract all reports in the repo
all_lineage = client.extract_all_reports(REPO_NAME)

print(f"\n{'='*80}")
print(f"SUMMARY: {REPO_NAME}")
print(f"{'='*80}")
print(f"  Reports:              {len(all_lineage)}")
print(f"  With SQL sources:     {sum(1 for li in all_lineage if li.sql_sources)}")
print(f"  Total SQL sources:    {sum(len(li.sql_sources) for li in all_lineage)}")
n_measures = sum(len([d for d in li.dax_expressions if d.expression_type == 'measure']) for li in all_lineage)
print(f"  Total DAX measures:   {n_measures}")
n_calc = sum(len([d for d in li.dax_expressions if d.expression_type == 'calculated_column']) for li in all_lineage)
print(f"  Total calc columns:   {n_calc}")

# Unique SQL objects referenced
all_sql_objects = set()
for li in all_lineage:
    for s in li.sql_sources:
        all_sql_objects.add(f"{s.schema}.{s.sql_object}")
print(f"  Unique SQL objects:   {len(all_sql_objects)}")
for obj in sorted(all_sql_objects):
    print(f"    {obj}")

# %% Cell 5: Extract across all repos
# Uncomment to scan all repos (may take a few minutes)
# all_repos_lineage = {}
# for repo in repos:
#     repo_name = repo["name"]
#     if not repo_name.startswith("BI-TST-"):
#         continue
#     print(f"\nScanning {repo_name}...")
#     all_repos_lineage[repo_name] = client.extract_all_reports(repo_name)
#
# total_reports = sum(len(v) for v in all_repos_lineage.values())
# total_sources = sum(len(li.sql_sources) for v in all_repos_lineage.values() for l in v)
# print(f"\nTotal: {total_reports} reports, {total_sources} SQL sources across {len(all_repos_lineage)} repos")
