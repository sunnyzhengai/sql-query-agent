"""NOTEBOOK_REGISTRY — the contract for the driver layer (ADR 0042).

Sunny's brief, verbatim intent: "like our data contract for the engine,
do we have a contract for our notebooks? ... I need a contract to stop
us, and it should tie notebooks to their source and their outcomes."
The threat model is the AI collaborators themselves: the demonstrated
failure mode is locally-reasonable expedience under deadline — regex in
notebooks, logic patched into notebooks. Discipline that lives in
intent decays exactly when pressure arrives; only mechanical
enforcement survives. tests/test_notebook_contract.py enforces every
field below against the notebook sources.

Fields per notebook:
  family          acquisition | derivation | publisher | verification
  serves          Layer-0 question families (A-G, QUESTION_MAP.md) the
                  notebook ultimately exists for. >=1 required — a
                  notebook serving no family is by definition a ghost.
  purpose         one line, human
  entry_points    names the notebook may import from src.steps.*
                  (src.steps.gates is globally permitted). Everything
                  else the notebook needs must come from src/ modules
                  on the allowed-import list — never be defined inline.
  wrappers        the ONLY function defs permitted in the notebook —
                  thin runtime shims (CLR init, closures over spark)
                  that cannot live in src/. Empty means none.
  gates           required call names that must appear in the source
                  (precondition_gate / postcondition_gate /
                  find_duplicate_identities ...). Deviations from the
                  family default are visible here as data, not hidden.
  requires_engine minimum src.__version__ (major.minor floor) the
                  notebook's cell 0 must assert via require_engine —
                  kills the version-skew class from the field week.

FIELD-PATCH LAW: a deployment may patch a notebook ONLY as a marked
cell:  # FIELD PATCH <date> <handoff-ref> <sunset condition>
The marker is ILLEGAL in the repo (CI enforces its absence): patches
exist only in deployments and die on the next sync.

QUESTION FAMILIES (Layer 0, approved 2026-08-18): A Meaning,
B Provenance, C Impact, D Discovery, E Trust, F Consistency, G Health.
"""

from __future__ import annotations

FAMILIES = ("acquisition", "derivation", "publisher", "verification")
QUESTION_FAMILIES = ("A", "B", "C", "D", "E", "F", "G")

# The engine floor asserted by every notebook this release. Raise it
# when a notebook starts depending on newer src/ surface.
ENGINE_FLOOR = "1.24"

NOTEBOOK_REGISTRY: "dict[str, dict]" = {
    "010_ingest_sql_filedrop": {
        "family": "acquisition",
        "serves": ["A", "B", "C", "D", "F"],
        "purpose": "Load dropped .sql files into input_sql_sources",
        "entry_points": [],
        "wrappers": [],
        "gates": ["find_duplicate_identities"],
        "requires_engine": ENGINE_FLOOR,
    },
    "020_ingest_sql_folders": {
        "family": "acquisition",
        "serves": ["A", "B", "C", "D", "F"],
        "purpose": "Load configured ABFS folders of .sql into input_sql_sources",
        "entry_points": [],
        "wrappers": [],
        # identity derives from the shared CREATE-header pattern
        # (src.parser.identity) and the collision assert
        "gates": ["CREATE_HEADER_SPARK_PATTERN"],
        "requires_engine": ENGINE_FLOOR,
    },
    "030_ingest_sql_live": {
        "family": "acquisition",
        "serves": ["A", "B", "C", "D", "F"],
        "purpose": "Live extraction from the customer SQL source (merge)",
        "entry_points": [],
        "wrappers": [],
        "gates": [],  # identity + change tracking live in the extractor
        "requires_engine": ENGINE_FLOOR,
    },
    "040_dict_clarity": {
        "family": "acquisition",
        "serves": ["A", "B"],
        "purpose": "Primary dictionary load (formatted CSVs or raw export)",
        "entry_points": [],
        "wrappers": [],
        "gates": ["find_duplicate_identities"],
        "requires_engine": ENGINE_FLOOR,
    },
    "050_dict_caboodle": {
        "family": "acquisition",
        "serves": ["A", "B"],
        "purpose": "Merge a second dictionary source (primary wins)",
        "entry_points": [],
        "wrappers": [],
        "gates": [],
        "requires_engine": ENGINE_FLOOR,
    },
    "100_install": {
        "family": "verification",
        "serves": ["G"],
        "purpose": "Environment verification + ingestion-state report",
        "entry_points": [],
        "wrappers": [],
        "gates": [],
        "requires_engine": ENGINE_FLOOR,
    },
    "200_parse": {
        "family": "derivation",
        "serves": ["A", "B", "C", "F", "G"],
        "purpose": "Parse the SQL corpus with ScriptDom into parse tables",
        "entry_points": ["parse_step"],
        # CLR/ScriptDom init is runtime-specific and cannot live in src/
        "wrappers": ["_parse_raw", "parse_with_scriptdom",
                     "extract_with_scriptdom"],
        "gates": ["precondition_gate", "postcondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "300_build_graph": {
        "family": "derivation",
        "serves": ["A", "B", "C", "F"],
        "purpose": "Build the knowledge graph (nodes/edges, all layers, "
                   "decision trees)",
        "entry_points": ["build_graph_step"],
        "wrappers": [],
        "gates": ["precondition_gate", "postcondition_gate"],
        # decision-tree outputs (ADR 0044 phase 1) need the 1.26 wheel
        "requires_engine": "1.26",
    },
    "400_build_metric_logic": {
        "family": "derivation",
        "serves": ["A", "E"],
        "purpose": "Flatten the graph into the metric card table",
        "entry_points": ["metric_logic_step"],
        "wrappers": [],
        "gates": ["precondition_gate", "postcondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "800_export_graph_tables": {
        "family": "derivation",
        "serves": ["B", "C"],
        "purpose": "Export typed tables for the Fabric Graph model",
        "entry_points": ["export_step"],
        "wrappers": [],
        "gates": ["precondition_gate", "postcondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "500_validate": {
        "family": "verification",
        "serves": ["G"],
        "purpose": "Pipeline validation + deployment readiness gate + "
                   "leaf grounding (spec:C4)",
        "entry_points": ["dictionary_coverage_threshold", "tech_table_names",
                         "readiness_gate", "stale_metrics"],
        "wrappers": ["_fetch", "_table_exists"],
        "gates": ["precondition_gate"],
        # leaf grounding (spec:C4) needs the 1.29 wheel
        "requires_engine": "1.29",
    },
    "600_generate_descriptions": {
        "family": "derivation",
        "serves": ["A"],
        "purpose": "Bottom-up LLM descriptions over the calculation DAG",
        "entry_points": [],
        "wrappers": ["describe"],  # closes over the endpoint credentials
        "gates": ["precondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "610_generate_agent_descriptions": {
        "family": "derivation",
        "serves": ["A"],
        "purpose": "Data-Agent metric descriptions (owns ops_agent_descriptions)",
        "entry_points": ["plan_generation", "sql_hash", "run_generation",
                         "canary_check", "STATUS_OK"],
        "wrappers": ["save", "generate"],  # close over spark / the agent client
        "gates": ["precondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "900_publish_collibra": {
        "family": "publisher",
        "serves": ["A", "E"],
        "purpose": "Publish descriptions onto Collibra report assets",
        "entry_points": ["STATUS_OK"],
        "wrappers": [],
        "gates": ["precondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "910_publish_purview": {
        "family": "publisher",
        "serves": ["A", "E"],
        "purpose": "Publish metric cards to the Purview Data Map",
        "entry_points": [],
        "wrappers": [],
        "gates": ["precondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "950_ingest_agent_events": {
        "family": "acquisition",
        "serves": ["G"],
        "purpose": "Fold agent conversation events into gov_* telemetry",
        "entry_points": ["parse_agent_events", "dedupe_events"],
        "wrappers": ["_existing_keys"],
        "gates": [],
        "requires_engine": ENGINE_FLOOR,
    },
    "700_refresh_search_index": {
        "family": "derivation",
        "serves": ["D"],
        "purpose": "Rebuild the semantic catalog + Eventhouse re-embed",
        "entry_points": ["COVERAGE_QUERY", "embed_command",
                         "refresh_search_index", "build_semantic_catalog"],
        "wrappers": [],
        "gates": ["precondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "060_ingest_semantic_models": {
        "family": "acquisition",
        "serves": ["A", "B", "E", "G"],
        "purpose": "Ingest PBI semantic models (lineage, DAX, names, fallout)",
        "entry_points": ["semantic_models_step"],
        "wrappers": [],
        "gates": ["postcondition_gate"],
        "requires_engine": ENGINE_FLOOR,
    },
    "920_publish_pbi": {
        "family": "publisher",
        "serves": ["A", "E"],
        "purpose": "Publish certified descriptions onto PBI reports",
        "entry_points": ["STATUS_OK"],
        "wrappers": [],
        "gates": [],
        "requires_engine": ENGINE_FLOOR,
    },
}

# Imports notebooks may use, by top-level module name. Logic modules are
# all under src/ — the point is that NOTHING else supplies logic.
ALLOWED_IMPORTS = frozenset({
    "src",
    # runtime + IO surface
    "pyspark", "notebookutils", "yaml",
    # ScriptDom CLR bootstrap (cannot live in src/)
    "pythonnet", "clr", "System", "Microsoft",
    # stdlib-minimal
    "os", "sys", "json", "time", "datetime", "uuid", "collections",
    "functools", "pathlib",
})
