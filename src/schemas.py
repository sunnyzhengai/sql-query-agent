"""Data contracts for all Delta tables — the single source of truth.

Each table's contract declares five things:
  shape       - columns: (name, type, nullable)
  semantics   - description + column_descriptions (what the data MEANS)
  ownership   - owner (the ONE sanctioned writer) + enrichers (sanctioned
                secondary writers, e.g. description enrichment)
  lineage     - consumers (who reads it: notebooks, adapters, data_agent)
  invariants  - declarative rules the data must satisfy (allowed_values,
                unique, reference)

Contracts are enforced by tests/test_table_contracts.py, which also scans the
pipeline notebooks so declared ownership can never drift from actual code.
Docs, agent instructions, and validation gates are projections of this file —
never author a table fact anywhere else.

Identity obligation (ADR 0015): metric_id ("<schema>.<object_name>") is the
only durable metric identity. Every consumer that projects metrics into
another system must use metric_id as its durable key, and any display name
it shows must be traceable to metric_id at a glance — bare object names
collide across schemas.

Adding a new table (contract-first):
    1. Author the full contract here (shape, semantics, ownership, lineage,
       invariants) and add it to TABLE_REGISTRY
    2. Run pytest tests/test_table_contracts.py — it tells you what's missing
    3. Implement the writer notebook/module declared in owner
    4. Regenerate docs (they project from this registry)

Usage in Fabric notebooks:
    from src.schemas import GRAPH_NODES, to_spark_schema
    nodes_df = spark.createDataFrame(rows, schema=to_spark_schema(GRAPH_NODES))
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.models import EdgeType, NodeLayer

if TYPE_CHECKING:
    from pyspark.sql.types import StructType

# Contract vocabulary — meta-tests validate against these.
DOMAINS = ("input", "operations", "graph", "lpg_export", "output", "governance")
INVARIANT_KINDS = ("allowed_values", "unique", "reference")

NODE_LAYERS = [layer.value for layer in NodeLayer]
EDGE_TYPES = [edge.value for edge in EdgeType]


# =====================================================================
# INPUT domain — customer-provided data, loaded by 01_install
# =====================================================================

SQL_SOURCES = {
    "table_name": "input_sql_sources",
    "must_be_nonempty": True,
    "description": (
        "Customer SQL sources (stored procedures and views). One row per SQL "
        "object; identity comes from the CREATE/ALTER statement inside the "
        "definition, not the filename. TWO writers, one protocol: the manual "
        "file path (01_install / load_sql_files) OVERWRITES the full corpus "
        "at install; the automated extractor (extract_views — the primary "
        "customer path) MERGES incrementally by metric_id, so scheduled "
        "extractions upsert changed objects without erasing rows loaded by "
        "the other writer. Owner stays 01_install for gate attribution; "
        "write_mode describes the owner's install-time write."
    ),
    "domain": "input",
    "status": "active",
    "owner": {"notebook": "01_install", "module": None},
    "utility_writers": ["load_sql_files", "extract_views"],
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["01_install", "02_parse", "06_validate"],
    "columns": [
        ("metric_id", "string", False),
        ("name", "string", False),
        ("sql", "string", False),
        ("steward", "string", True),
        ("developer", "string", True),
        ("source_type", "string", True),
        ("source_schema", "string", True),
    ],
    "column_descriptions": {
        "metric_id": "Unique identifier: schema.object_name extracted from the CREATE/ALTER statement",
        "name": "Object name (proc or view) without schema",
        "sql": "Full original SQL text, normalized to \\n line endings at load",
        "steward": "Business steward, if assigned at load time",
        "developer": "Developer owner, if assigned at load time",
        "source_type": "Object type: procedure or view (null when identity fell back to filename)",
        "source_schema": "Database schema the object belongs to (e.g. reporting)",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"], "fold_case": True},
        {"kind": "allowed_values", "column": "source_type", "values": ["procedure", "view"]},
    ],
}

DICT_TABLES = {
    "table_name": "input_dict_tables",
    "must_be_nonempty": True,
    "description": (
        "Customer data dictionary: one row per warehouse table with its "
        "business description. Loaded from dictionary/dict_tables.csv. "
        "Mandatory — without it the agent gives incomplete answers."
    ),
    "domain": "input",
    "status": "active",
    "owner": {"notebook": "01_install", "module": None},
    "utility_writers": ["load_clarity_dictionary", "load_caboodle_dictionary"],
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["01_install", "03_build_graph", "06_validate", "load_caboodle_dictionary", "export_test_fixtures"],
    "columns": [
        ("TABLE_NAME", "string", False),
        ("DESCRIPTION", "string", True),
    ],
    "column_descriptions": {
        "TABLE_NAME": (
            "Warehouse table name; matched to SQL references case-insensitively "
            "and schema-agnostically (ADR 0016). Original casing preserved for display."
        ),
        "DESCRIPTION": "Business description of the table from the customer's dictionary",
    },
    "invariants": [
        {"kind": "unique", "columns": ["TABLE_NAME"], "fold_case": True},
    ],
}

DICT_COLUMNS = {
    "table_name": "input_dict_columns",
    "must_be_nonempty": True,
    "description": (
        "Customer data dictionary: one row per warehouse column with its "
        "business description. Loaded from dictionary/dict_columns.csv."
    ),
    "domain": "input",
    "status": "active",
    "owner": {"notebook": "01_install", "module": None},
    "utility_writers": ["load_clarity_dictionary", "load_caboodle_dictionary"],
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["01_install", "03_build_graph", "load_caboodle_dictionary", "export_test_fixtures"],
    "columns": [
        ("TABLE_NAME", "string", False),
        ("COLUMN_NAME", "string", False),
        ("DESCRIPTION", "string", True),
    ],
    "column_descriptions": {
        "TABLE_NAME": "Warehouse table the column belongs to",
        "COLUMN_NAME": "Column name",
        "DESCRIPTION": "Business description of the column",
    },
    "invariants": [
        {"kind": "unique", "columns": ["TABLE_NAME", "COLUMN_NAME"], "fold_case": True},
    ],
}


# =====================================================================
# OPERATIONS domain — pipeline mechanics, health, and support
# =====================================================================

PARSE_RESULTS = {
    "table_name": "ops_parse_results",
    "must_be_nonempty": True,
    "description": (
        "Intermediate parse output: the structural extraction of each SQL "
        "source (CTEs, table references, final SELECT) that 03_build_graph "
        "turns into the knowledge graph."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "02_parse", "module": "src/parser/sql_parser.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["03_build_graph", "export_test_fixtures"],
    "columns": [
        ("metric_id", "string", False),
        ("name", "string", False),
        ("ctes_json", "string", True),
        ("final_select_tables", "string", True),
        ("final_select_cte_refs", "string", True),
        ("normalized_sql", "string", True),
        ("cte_count", "integer", True),
        ("table_count", "integer", True),
        ("line_count", "integer", True),
        ("extraction_suppressed", "integer", True),
    ],
    "column_descriptions": {
        "metric_id": "SQL object this parse belongs to (input_sql_sources.metric_id)",
        "name": "Object name",
        "ctes_json": "JSON list of CTE steps: name, sql_fragment, dependencies, tables",
        "final_select_tables": "JSON list of physical tables read by the final SELECT",
        "final_select_cte_refs": "JSON list of CTEs referenced by the final SELECT",
        "normalized_sql": "Cleaned SQL after extraction (verbatim statements, \\n endings)",
        "extraction_suppressed": "AST-walk exceptions suppressed during extraction; "
                                 "nonzero = refs may be missing despite parse success",
        "cte_count": "Number of CTE/temp-table steps extracted",
        "table_count": "Number of distinct physical tables referenced",
        "line_count": "Line count of the source SQL",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"]},
        {"kind": "reference", "column": "metric_id", "references": "input_sql_sources.metric_id"},
    ],
}

PARSE_ERRORS = {
    "table_name": "ops_parse_errors",
    "description": (
        "SQL sources that failed to parse, classified into user-facing "
        "categories with plain-English explanations and suggested actions. "
        "Feeds the agent's /errors command."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "02_parse", "module": "src/parser/error_classifier.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["06_validate", "verify_graph", "data_agent"],
    "columns": [
        ("metric_id", "string", False),
        ("name", "string", False),
        ("error", "string", True),
        ("error_category", "string", True),
        ("user_explanation", "string", True),
        ("suggested_action", "string", True),
        ("line_count", "integer", True),
    ],
    "column_descriptions": {
        "metric_id": "SQL object that failed (input_sql_sources.metric_id)",
        "name": "Object name",
        "error": "Raw error message from the parser",
        "error_category": "Classifier category (no_query, complex_sql, parse_failure, ...)",
        "user_explanation": "Plain-English explanation for non-technical users",
        "suggested_action": "What the admin should do about it",
        "line_count": "Line count of the source SQL",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"]},
    ],
}

PARSE_SUCCESSES = {
    "table_name": "ops_parse_successes",
    "description": (
        "SQL sources that parsed successfully, with extraction counts. The "
        "cte/table/line counts are deliberate derived copies of the same "
        "facts in ops_parse_results, denormalized for the validation gate."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "02_parse", "module": "src/parser/sql_parser.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["02_parse", "06_validate", "verify_graph"],
    "columns": [
        ("metric_id", "string", False),
        ("name", "string", False),
        ("cte_count", "integer", True),
        ("table_count", "integer", True),
        ("line_count", "integer", True),
    ],
    "column_descriptions": {
        "metric_id": "SQL object that parsed (input_sql_sources.metric_id)",
        "name": "Object name",
        "cte_count": "Number of CTE/temp-table steps extracted",
        "table_count": "Number of distinct physical tables referenced",
        "line_count": "Line count of the source SQL",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"]},
    ],
}

BUILD_SUMMARY = {
    "table_name": "ops_build_summary",
    "description": (
        "Append-only pipeline run history: one row per key metric per run "
        "(counts, rates, timings). The audit trail of every build."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "06_validate", "module": None},
    "write_mode": "append",
    "enrichers": [],
    "consumers": ["admin"],
    "columns": [
        ("build_time", "string", False),
        ("metric_key", "string", False),
        ("value", "string", False),
        ("detail", "string", True),
    ],
    "column_descriptions": {
        "build_time": "ISO timestamp of the pipeline run",
        "metric_key": "Name of the recorded measure (e.g. parse_rate)",
        "value": "Measured value",
        "detail": "Optional context for the measure",
    },
    "invariants": [],
}

SETUP_COMPLETENESS = {
    "table_name": "ops_setup_completeness",
    "description": (
        "Queryable setup state: one row per optional enrichment per pipeline "
        "run recording whether it was present. A run without an optional "
        "input is legitimate but degraded — this table is how /health and "
        "admins see it (never only notebook stdout). ADR 0039 amendment."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "03_build_graph", "module": "src/steps/gates.py"},
    "write_mode": "append",
    "enrichers": [],
    "consumers": ["admin", "health"],
    "columns": [
        ("run_at", "string", False),
        ("step", "string", False),
        ("table_name", "string", False),
        ("present", "boolean", False),
        ("remediation", "string", True),
        ("contract_id", "string", False),
    ],
    "column_descriptions": {
        "run_at": "ISO timestamp of the pipeline run that recorded this state",
        "step": "Pipeline step that proceeded with/without the enrichment",
        "table_name": "The optional input table checked",
        "present": "Whether the enrichment existed when the step ran",
        "remediation": "Which utility/notebook provides the enrichment",
        "contract_id": "Stable id of the optional input's contract (ADR 0039)",
    },
    "invariants": [],
}

PIPELINE_VALIDATION = {
    "table_name": "ops_pipeline_validation",
    "description": (
        "Per-metric health check across all six pipeline steps: loaded, "
        "parsed, canonical node, transforms, edges, technical reachability. "
        "Backs the deployment gate and the agent's /coverage command."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "06_validate", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["data_agent", "admin"],
    "columns": [
        ("metric_id", "string", False),
        ("step1_loaded", "boolean", True),
        ("step2_parsed", "boolean", True),
        ("step3_canonical", "boolean", True),
        ("step4_transforms", "boolean", True),
        ("step5_edges", "boolean", True),
        ("step6_traversal", "boolean", True),
        ("transform_count", "integer", True),
        ("edge_count", "integer", True),
        ("tech_reachable", "integer", True),
    ],
    "column_descriptions": {
        "metric_id": "Metric being validated (input_sql_sources.metric_id)",
        "step1_loaded": "Source SQL present in input_sql_sources",
        "step2_parsed": "Parse succeeded (row in ops_parse_successes)",
        "step3_canonical": "Canonical node exists in graph_nodes",
        "step4_transforms": "At least one transformation node exists",
        "step5_edges": "Edges wired from canonical through transforms",
        "step6_traversal": "Technical layer reachable by traversal",
        "transform_count": "Number of transformation nodes for this metric",
        "edge_count": "Number of edges in this metric's subgraph",
        "tech_reachable": "Number of technical nodes reachable",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"]},
    ],
}

INSTALLATION_ERRORS = {
    "table_name": "ops_installation_errors",
    "description": (
        "Known installation/runtime error signatures with root cause, fix, "
        "and prevention. Seeded by 01_install; powers the agent's "
        "/troubleshoot command so failures are diagnosable at a distance."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "01_install", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["data_agent"],
    "columns": [
        ("error_signature", "string", False),
        ("error_category", "string", False),
        ("root_cause", "string", True),
        ("fix", "string", True),
        ("prevention", "string", True),
        ("first_seen", "string", True),
    ],
    "column_descriptions": {
        "error_signature": "Distinctive substring that identifies the error",
        "error_category": "Grouping label (environment, dll, config, data, ...)",
        "root_cause": "What actually causes this error",
        "fix": "Step-by-step resolution",
        "prevention": "How to avoid it next time",
        "first_seen": "When this signature was first catalogued",
    },
    "invariants": [
        {"kind": "unique", "columns": ["error_signature"]},
    ],
}

AGENT_DESCRIPTIONS = {
    "table_name": "ops_agent_descriptions",
    "description": (
        "Cache of agent-generated business descriptions for _PBI metrics, "
        "keyed by SQL hash so unchanged metrics are not re-generated. "
        "Source for the Collibra description publish."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "08_publish_collibra", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["08_publish_collibra", "collibra_adapter"],
    "columns": [
        ("metric_name", "string", False),
        ("description", "string", False),
        ("sql_hash", "string", True),
    ],
    "column_descriptions": {
        "metric_name": "Metric the description belongs to",
        "description": "Agent-generated business-language description",
        "sql_hash": "Hash of the source SQL at generation time (change detection)",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_name"]},
    ],
}


# =====================================================================
# GRAPH domain — the three-layer knowledge graph
# =====================================================================

GRAPH_NODES = {
    "table_name": "graph_nodes",
    "must_be_nonempty": True,
    "description": (
        "All nodes of the knowledge graph in one table, discriminated by "
        "`layer`: canonical (business metrics), transformation (CTE steps "
        "with sql_fragments), technical (warehouse tables/columns enriched "
        "from the data dictionary), and the consumption layer (ADR 0040): "
        "report and measure nodes. The certified ground truth the agent "
        "answers from."
    ),
    "domain": "graph",
    "status": "active",
    "owner": {"notebook": "03_build_graph", "module": "src/graph/builder.py"},
    "write_mode": "overwrite",
    "enrichers": ["07_generate_descriptions"],
    "consumers": [
        "04_build_metric_logic", "05_export_graph_tables", "06_validate",
        "07_generate_descriptions", "08_publish_collibra", "manage_stewards",
        "verify_graph", "data_agent", "11_refresh_search_index",
        "13_publish_pbi",
    ],
    "columns": [
        ("node_id", "string", False),
        ("layer", "string", False),
        ("name", "string", False),
        ("description", "string", True),
        ("properties", "string", True),
    ],
    "column_descriptions": {
        "node_id": "Unique node identifier, prefixed by layer",
        "layer": "Which layer this node belongs to (three SQL layers + report/measure, ADR 0040)",
        "name": "Display name (metric name, CTE name, or table/column name)",
        "description": "Business description (dictionary text or generated translation)",
        "properties": "JSON bag of layer-specific properties (sql_fragment, steward, ...)",
    },
    "invariants": [
        {"kind": "unique", "columns": ["node_id"]},
        {"kind": "allowed_values", "column": "layer", "values": NODE_LAYERS},
    ],
    "relations": [
        # Every parsed metric becomes exactly one canonical node (03's flow contract)
        {"kind": "count_equals", "where": {"layer": "canonical"},
         "other_table": "ops_parse_results"},
    ],
}

GRAPH_EDGES = {
    "table_name": "graph_edges",
    "must_be_nonempty": True,
    "description": (
        "Directed edges wiring the graph layers together: reports -> metrics "
        "-> logic steps -> source tables, plus report -> measure -> column "
        "(ADR 0040). Both endpoints must exist in graph_nodes."
    ),
    "domain": "graph",
    "status": "active",
    "owner": {"notebook": "03_build_graph", "module": "src/graph/builder.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": [
        "04_build_metric_logic", "05_export_graph_tables", "06_validate",
        "07_generate_descriptions", "08_publish_collibra", "verify_graph",
        "data_agent", "13_publish_pbi",
    ],
    "columns": [
        ("source_id", "string", False),
        ("target_id", "string", False),
        ("edge_type", "string", False),
        ("properties", "string", True),
    ],
    "column_descriptions": {
        "source_id": "Origin node (graph_nodes.node_id)",
        "target_id": "Destination node (graph_nodes.node_id)",
        "edge_type": "Which layer boundary this edge crosses",
        "properties": "JSON bag of edge properties",
    },
    "invariants": [
        {"kind": "allowed_values", "column": "edge_type", "values": EDGE_TYPES},
        {"kind": "reference", "column": "source_id", "references": "graph_nodes.node_id"},
        {"kind": "reference", "column": "target_id", "references": "graph_nodes.node_id"},
    ],
}


# =====================================================================
# OUTPUT domain — flattened, agent-facing products
# =====================================================================

METRIC_LOGIC = {
    "table_name": "output_metric_logic",
    "must_be_nonempty": True,
    "description": (
        "The agent's primary table: one pre-joined row per metric with its "
        "calculation logic, source tables, and descriptions. Created by "
        "04_build_metric_logic; descriptions enriched in place by "
        "07_generate_descriptions."
    ),
    "domain": "output",
    "status": "active",
    "owner": {"notebook": "04_build_metric_logic", "module": "src/graph/traversal.py"},
    "write_mode": "overwrite",
    "enrichers": ["07_generate_descriptions"],
    "consumers": [
        "07_generate_descriptions", "08_publish_collibra", "09_publish_purview",
        "data_agent",
    ],
    "columns": [
        ("metric_id", "string", False),
        ("metric_name", "string", False),
        ("business_name", "string", True),
        ("report_name", "string", True),
        ("report_url", "string", True),
        ("description", "string", True),
        ("steward", "string", True),
        ("developer", "string", True),
        ("transform_count", "integer", True),
        ("calculation_logic", "string", True),
        ("source_tables", "string", True),
        ("table_descriptions", "string", True),
    ],
    "column_descriptions": {
        "metric_id": "Metric identifier (input_sql_sources.metric_id)",
        "metric_name": "Display name of the metric (object name)",
        "business_name": "Business-friendly name from PBI report lineage or manual entry (input_metric_names)",
        "report_name": "Power BI report(s) built on this metric, when known",
        "report_url": "Link to the primary report; agents offer it in answers",
        "description": "Business-language summary of what the metric measures",
        "steward": "Business steward accountable for the definition",
        "developer": "Developer accountable for the SQL logic",
        "transform_count": "Number of transformation steps in the calculation",
        "calculation_logic": "Ordered plain-language rendering of the CTE chain",
        "source_tables": "Comma-separated physical tables the metric reads",
        "table_descriptions": "Dictionary descriptions of those source tables",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"]},
        {"kind": "reference", "column": "metric_id", "references": "input_sql_sources.metric_id"},
    ],
    "relations": [
        # One agent-facing row per canonical node (04's flow contract)
        {"kind": "count_equals",
         "other_table": "graph_nodes", "other_where": {"layer": "canonical"}},
    ],
}


# =====================================================================
# LPG_EXPORT domain — typed tables for Fabric Graph Model ingestion
# (camelCase columns are required by Fabric Graph NL2GQL)
# =====================================================================

GRAPH_CANONICAL = {
    "table_name": "graph_canonical",
    "description": "LPG export: canonical (business metric) nodes, flattened for Fabric Graph.",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("nodeId", "string", False),
        ("metricId", "string", False),
        ("name", "string", False),
        ("bareName", "string", False),
        ("businessName", "string", True),
        ("reportName", "string", True),
        ("reportUrl", "string", True),
        ("description", "string", True),
        ("steward", "string", True),
        ("developer", "string", True),
    ],
    "column_descriptions": {
        "nodeId": "Canonical node id (graph_nodes.node_id)",
        "metricId": "Schema-qualified metric identity (ADR 0015) — bare names collide across schemas",
        "name": (
            "Schema-qualified name, identical to metricId (ADR 0020: the NL2GQL "
            "generator filters name with the user's qualified reference)"
        ),
        "bareName": "Bare object name (no schema); repeats across schemas",
        "businessName": "Business-friendly name (PBI report lineage or manual; may be empty)",
        "reportName": "Power BI report(s) built on this metric, when known",
        "reportUrl": "Link to the primary report; the agent offers it in answers",
        "description": "Business description of the metric",
        "steward": "Business steward",
        "developer": "Developer owner",
    },
    "invariants": [
        {"kind": "unique", "columns": ["nodeId"]},
    ],
    "relations": [
        # LPG export must carry every canonical node (05's flow contract)
        {"kind": "count_equals",
         "other_table": "graph_nodes", "other_where": {"layer": "canonical"}},
    ],
}

GRAPH_TRANSFORMATION = {
    "table_name": "graph_transformation",
    "description": "LPG export: transformation (CTE step) nodes with their SQL fragments.",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("nodeId", "string", False),
        ("name", "string", False),
        ("metricId", "string", False),
        ("description", "string", True),
        ("sqlFragment", "string", True),
    ],
    "column_descriptions": {
        "nodeId": "Transformation node id (graph_nodes.node_id)",
        "name": "CTE/step name",
        "metricId": "Metric this step belongs to",
        "description": (
            "Business description of this calculation step (ADR 0019: generated "
            "bottom-up by 07, the smallest certified unit of business definition)"
        ),
        "sqlFragment": "Verbatim SQL fragment for this step",
    },
    "invariants": [
        {"kind": "unique", "columns": ["nodeId"]},
    ],
}

GRAPH_TECHNICAL = {
    "table_name": "graph_technical",
    "description": "LPG export: technical nodes (warehouse tables/columns with dictionary descriptions).",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("nodeId", "string", False),
        ("name", "string", False),
        ("description", "string", True),
        ("tableName", "string", False),
        ("schemaName", "string", True),
        ("databaseName", "string", True),
        ("columnName", "string", True),
    ],
    "column_descriptions": {
        "nodeId": "Technical node id (graph_nodes.node_id)",
        "name": "Display name",
        "description": "Dictionary description",
        "tableName": "Physical table name",
        "schemaName": "Schema, when known",
        "databaseName": "Database, when known",
        "columnName": "Column name, when the node is a column",
    },
    "invariants": [
        {"kind": "unique", "columns": ["nodeId"]},
    ],
}

GRAPH_REPORT = {
    "table_name": "graph_report",
    "description": (
        "LPG export: consumption-layer report nodes (ADR 0040) — Power BI "
        "reports whose semantic models execute metrics."
    ),
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("nodeId", "string", False),
        ("name", "string", False),
        ("description", "string", True),
        ("repoName", "string", True),
        ("semanticModelPath", "string", True),
    ],
    "column_descriptions": {
        "nodeId": "Report node id (graph_nodes.node_id)",
        "name": "Report name from the .SemanticModel folder",
        "description": "Business description (generated by 07 or published back)",
        "repoName": "Source repo, when the devops_git profile fetched it",
        "semanticModelPath": "Path of the .SemanticModel folder at extraction",
    },
    "invariants": [
        {"kind": "unique", "columns": ["nodeId"]},
    ],
}

GRAPH_MEASURE = {
    "table_name": "graph_measure",
    "description": "LPG export: DAX measure / calculated-column nodes (ADR 0040) — the DAX half of the business logic.",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("nodeId", "string", False),
        ("name", "string", False),
        ("description", "string", True),
        ("reportName", "string", False),
        ("pbiTable", "string", True),
        ("daxExpression", "string", True),
        ("expressionType", "string", True),
    ],
    "column_descriptions": {
        "nodeId": "Measure node id (graph_nodes.node_id)",
        "name": "Measure / calculated-column name",
        "description": "Business description of what the DAX computes",
        "reportName": "Report whose semantic model defines it",
        "pbiTable": "PBI table the expression lives on",
        "daxExpression": "Verbatim DAX expression (PHI-gated like SQL fragments)",
        "expressionType": "measure | calculated_column",
    },
    "invariants": [
        {"kind": "unique", "columns": ["nodeId"]},
    ],
}

_LPG_EDGE_COLUMN_DESCRIPTIONS = {
    "sourceId": "Origin node id",
    "targetId": "Destination node id",
}

GRAPH_EDGE_C2T = {
    "table_name": "graph_edge_c2t",
    "description": (
        "LPG export: DERIVED canonical -> transformation closure — metric to "
        "EVERY calculation step (ADR 0020; raw roots-only edges stay in "
        "graph_edges). Shaped so the generator's single-hop CALCULATED_BY "
        "chain is complete."
    ),
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_canonical.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_transformation.nodeId"},
    ],
}

GRAPH_EDGE_T2T = {
    "table_name": "graph_edge_t2t",
    "description": "LPG export: transformation -> transformation edges (step dependency chain).",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_transformation.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_transformation.nodeId"},
    ],
}

GRAPH_EDGE_T2TECH = {
    "table_name": "graph_edge_t2tech",
    "description": "LPG export: transformation -> technical edges (logic step to source table).",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_transformation.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_technical.nodeId"},
    ],
}

GRAPH_EDGE_TAB2COL = {
    "table_name": "graph_edge_tab2col",
    "description": "LPG export: technical table -> technical column edges (columns reachable by traversal).",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_technical.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_technical.nodeId"},
    ],
}

GRAPH_EDGE_USES_TABLE = {
    "table_name": "graph_edge_uses_table",
    "description": (
        "LPG export: DERIVED metric -> technical table edges — the precomputed "
        "transitive closure of the calculation DAG (ADR 0018), so table<->metric "
        "questions are single-hop. Not stored in graph_edges; recomputed every export."
    ),
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": {
        "sourceId": "Metric node id (graph_canonical.nodeId)",
        "targetId": "Technical TABLE node id (graph_technical.nodeId; never a column node)",
    },
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_canonical.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_technical.nodeId"},
    ],
}

GRAPH_EDGE_REPORT2CANONICAL = {
    "table_name": "graph_edge_report2canonical",
    "description": "LPG export: report -> metric edges from TMDL partition lineage (ADR 0040, deterministic).",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_report.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_canonical.nodeId"},
    ],
}

GRAPH_EDGE_REPORT2TECHNICAL = {
    "table_name": "graph_edge_report2technical",
    "description": (
        "LPG export: report -> technical TABLE edges for DirectLake "
        "partitions (ADR 0040 pattern 5 — the model reads a warehouse "
        "table directly; there is no proc to link)."
    ),
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_report.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_technical.nodeId"},
    ],
}

GRAPH_EDGE_REPORT2MEASURE = {
    "table_name": "graph_edge_report2measure",
    "description": "LPG export: report -> measure ownership edges (ADR 0040).",
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_report.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_measure.nodeId"},
    ],
}

GRAPH_EDGE_MEASURE2COLUMN = {
    "table_name": "graph_edge_measure2column",
    "description": (
        "LPG export: measure -> technical column edges from table-qualified "
        "DAX refs (ADR 0040; unresolved refs skipped, never guessed)."
    ),
    "domain": "lpg_export",
    "status": "active",
    "owner": {"notebook": "05_export_graph_tables", "module": None},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["fabric_graph_model (planned)"],
    "columns": [
        ("sourceId", "string", False),
        ("targetId", "string", False),
    ],
    "column_descriptions": dict(_LPG_EDGE_COLUMN_DESCRIPTIONS),
    "invariants": [
        {"kind": "reference", "column": "sourceId", "references": "graph_measure.nodeId"},
        {"kind": "reference", "column": "targetId", "references": "graph_technical.nodeId"},
    ],
}


# =====================================================================
# GOVERNANCE / OPERATIONS extras — error log and steward assignments
# (recovered 2026-08-02 from the dead-code purge), Tier 2 extraction
# tracking, and the remaining PLANNED contracts (no writer yet; the
# single-writer test enforces nothing writes those until activated).
# =====================================================================

DESCRIPTION_CACHE = {
    "table_name": "ops_description_cache",
    "description": (
        "Content-hash cache for generated step descriptions (ADR 0019): one "
        "row per described sql_fragment. Re-runs of 07 only describe new or "
        "changed steps — the hash keys on the fragment plus direct-dependency "
        "names, so unchanged logic never pays a second LLM call."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "07_generate_descriptions", "module": "src/descriptions.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["07_generate_descriptions"],
    "columns": [
        ("content_hash", "string", False),
        ("node_id", "string", False),
        ("description", "string", False),
        ("generated_at", "string", False),
    ],
    "column_descriptions": {
        "content_hash": "step_content_hash(sql_fragment, direct dependency names)",
        "node_id": "Transformation node the description was generated for",
        "description": "Generated one-sentence business description",
        "generated_at": "ISO timestamp of generation",
    },
    "invariants": [
        {"kind": "unique", "columns": ["content_hash"]},
    ],
}

ERROR_LOG = {
    "table_name": "ops_error_log",
    "description": (
        "Persistent append-only error log across pipeline runs with "
        "regression detection: new (first failure), known (still failing), "
        "regressed (passed last run, fails now). Resolutions are computed "
        "per run and reported in the build summary."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "02_parse", "module": "src/governance/error_log.py"},
    "write_mode": "append",
    "enrichers": [],
    "consumers": ["02_parse", "admin"],
    "columns": [
        ("run_id", "string", False),
        ("run_timestamp", "string", False),
        ("metric_id", "string", False),
        ("metric_name", "string", True),
        ("error_type", "string", True),
        ("error_message", "string", True),
        ("line_count", "integer", True),
        ("query_count", "integer", True),
        ("clean_sql_preview", "string", True),
        ("status", "string", True),
    ],
    "column_descriptions": {
        "run_id": "Pipeline run identifier",
        "run_timestamp": "When the run happened",
        "metric_id": "Metric that errored",
        "metric_name": "Display name",
        "error_type": "Error classification",
        "error_message": "Raw error text",
        "line_count": "Source SQL line count",
        "query_count": "Queries extracted before failure",
        "clean_sql_preview": "Preview of the cleaned SQL",
        "status": "new | known | regressed",
    },
    "invariants": [
        {"kind": "allowed_values", "column": "status", "values": ["new", "known", "regressed"]},
    ],
}

EXTRACTION_INSPECTION = {
    "table_name": "ops_extraction_inspection",
    "description": (
        "Side-by-side extraction/parse outcomes per metric with raw and "
        "cleaned SQL, for manual validation during scale testing."
    ),
    "domain": "operations",
    "status": "planned",
    "notes": (
        "Used during the 790-proc scale-testing phase; no writer in the "
        "current pipeline. Keep for the next scale run or drop."
    ),
    "columns": [
        ("metric_id", "string", False),
        ("line_count", "integer", True),
        ("query_count", "integer", True),
        ("extraction_ok", "boolean", True),
        ("extraction_error", "string", True),
        ("parse_ok", "boolean", True),
        ("parse_error", "string", True),
        ("cte_count", "integer", True),
        ("table_count", "integer", True),
        ("raw_sql", "string", True),
        ("clean_sql", "string", True),
    ],
    "column_descriptions": {
        "metric_id": "Metric inspected",
        "line_count": "Source SQL line count",
        "query_count": "Queries extracted",
        "extraction_ok": "ScriptDom extraction succeeded",
        "extraction_error": "Extraction error, if any",
        "parse_ok": "sqlglot parse succeeded",
        "parse_error": "Parse error, if any",
        "cte_count": "CTEs extracted",
        "table_count": "Tables referenced",
        "raw_sql": "Original SQL",
        "clean_sql": "Extracted/cleaned SQL",
    },
    "invariants": [],
}

TRACKING = {
    "table_name": "ops_extraction_tracking",
    "description": (
        "Change tracking for SQL objects extracted from a live SQL Server "
        "(hash-based diff detection), for Tier 2 on-prem extraction. Written "
        "by the extract_views utility notebook, not the core pipeline."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "extract_views", "module": "src/extractor/tracker.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["extract_views"],
    "columns": [
        ("object_name", "string", False),
        ("object_type", "string", False),
        ("schema_name", "string", True),
        ("sql_hash", "string", True),
        ("status", "string", True),
        ("last_seen", "string", True),
    ],
    "column_descriptions": {
        "object_name": "Proc/view name in the source server",
        "object_type": "procedure | view",
        "schema_name": "Schema in the source server",
        "sql_hash": "SHA-256 of the object's SQL at last extraction",
        "status": "new | changed | unchanged | removed",
        "last_seen": "Last extraction timestamp",
    },
    "invariants": [],
}

SYNC_LOG = {
    "table_name": "ops_sync_log",
    "description": "Audit log of catalog publishes (Purview/Collibra): what was pushed, when, result.",
    "domain": "operations",
    "status": "planned",
    "notes": (
        "Publish notebooks (08/09) do not yet write an audit row per push. "
        "Wire in when catalog publishing is validated end-to-end."
    ),
    "columns": [
        ("synced_at", "string", False),
        ("adapter", "string", False),
        ("asset_id", "string", False),
        ("status", "string", False),
        ("message", "string", True),
    ],
    "column_descriptions": {
        "synced_at": "Publish timestamp",
        "adapter": "purview | collibra | pbi",
        "asset_id": "Catalog asset that was written",
        "status": "success | failed | skipped",
        "message": "Error or context message",
    },
    "invariants": [],
}

STEWARD_ASSIGNMENTS = {
    "table_name": "gov_steward_assignments",
    "optional_input": True,
    "remediation": "run notebooks/utilities/manage_stewards to assign stewards",
    "description": (
        "Steward ownership per metric — assigned individually, in bulk, or "
        "by name pattern via the manage_stewards utility notebook. Applied "
        "to canonical graph nodes by 03_build_graph, from where "
        "output_metric_logic and the agent pick them up."
    ),
    "domain": "governance",
    "status": "active",
    "owner": {"notebook": "manage_stewards", "module": "src/governance/steward.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["03_build_graph", "manage_stewards"],
    "columns": [
        ("metric_id", "string", False),
        ("metric_name", "string", False),
        ("steward_name", "string", False),
        ("steward_email", "string", True),
        ("department", "string", True),
        ("assigned_date", "string", True),
        ("assigned_by", "string", True),
    ],
    "column_descriptions": {
        "metric_id": "Metric being assigned (input_sql_sources.metric_id)",
        "metric_name": "Display name of the metric",
        "steward_name": "Business steward accountable for the definition",
        "steward_email": "Steward contact email",
        "department": "Steward's department",
        "assigned_date": "Assignment timestamp (ISO)",
        "assigned_by": "Who made the assignment",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"]},
    ],
}


# =====================================================================
# GOVERNANCE lifecycle — contract drafts (ADRs 0021-0024)
# Planned until writers exist; the shapes are the design deliverable.
# =====================================================================

CERTIFICATION_EVENTS = {
    "table_name": "gov_certification_events",
    "description": (
        "Append-only log of certification lifecycle events. Certification "
        "pins a definition version (ADR 0022): every event records the "
        "definition_hash the reviewer actually saw. Current status per "
        "metric is the latest event; staleness is derived by comparing the "
        "certified hash to the metric's current hash — never stored. "
        "Certification discloses trust, never gates availability (ADR 0021)."
    ),
    "domain": "governance",
    "status": "planned",
    "notes": (
        "Contract draft from the 2026-08-06 governance design pass (ADRs "
        "0021-0024). Writer will be a certify/reject steward interaction "
        "(notebook or agent command); wire before flipping active."
    ),
    "columns": [
        ("event_at", "string", False),
        ("metric_id", "string", False),
        ("definition_hash", "string", False),
        ("definition_version", "integer", False),
        ("action", "string", False),
        ("actor", "string", False),
        ("actor_email", "string", True),
        ("previous_status", "string", True),
        ("new_status", "string", False),
        ("reason", "string", True),
    ],
    "column_descriptions": {
        "event_at": "Event timestamp (ISO)",
        "metric_id": "Metric certified/rejected (input_sql_sources.metric_id)",
        "definition_hash": "SHA-256 of the normalized SQL the reviewer saw (ADR 0022)",
        "definition_version": "Human-facing ordinal for that hash (1, 2, 3...)",
        "action": "dev_certify | steward_certify | reject | revoke | deprecate | reinstate",
        "actor": "Who acted (developer or steward name)",
        "actor_email": "Actor contact email",
        "previous_status": "CertificationStatus before the event",
        "new_status": "CertificationStatus after the event (draft | dev_certified | steward_certified)",
        "reason": "Free-text rationale, required on reject/revoke/deprecate",
    },
    "invariants": [],
}

PUBLISH_LOG = {
    "table_name": "gov_publish_log",
    "description": (
        "Append-only log of every push to an external governance catalog "
        "(Purview, Collibra): assets, descriptions, glossary terms — one "
        "row per attempted publish with its outcome. The admin telemetry "
        "answer to 'what did we push to our DG tools, and did it land?' "
        "(Sunny, 2026-08-11)."
    ),
    "domain": "governance",
    "status": "active",
    "owner": {"notebook": "08_publish_collibra",
              "module": "src/governance/publish_log.py"},
    "write_mode": "append",
    "enrichers": ["09_publish_purview", "13_publish_pbi"],
    "consumers": ["admin telemetry report"],
    "columns": [
        ("published_at", "string", False),
        ("run_id", "string", False),
        ("target", "string", False),
        ("kind", "string", False),
        ("asset_id", "string", False),
        ("name", "string", True),
        ("status", "string", False),
        ("message", "string", True),
    ],
    "column_descriptions": {
        "published_at": "ISO timestamp of the publish attempt",
        "run_id": "Pipeline run identifier the publish belonged to",
        "target": "purview | collibra",
        "kind": "asset | glossary_term",
        "asset_id": "Asset/term identity pushed",
        "name": "Display name pushed",
        "status": "success | skipped | failed (PublishStatus)",
        "message": "Adapter message — term guid, assignment counts, or the error",
    },
    "invariants": [],
}

TURN_EVENTS = {
    "table_name": "gov_turn_events",
    "description": (
        "Append-only log of agent conversation turns with the DECISION "
        "SHAPE (ADR 0035 telemetry): which tools ran, what was read, and "
        "whether the load-bearing decisions were computed by the engine "
        "or assembled by the LLM. Ingested from the surfaces' JSONL by "
        "the agent-events pipeline step; joined to gov_feedback_events "
        "for failure attribution."
    ),
    "domain": "governance",
    "status": "active",
    "owner": {"notebook": "10_ingest_agent_events",
              "module": "src/steps/agent_events.py"},
    "write_mode": "append",
    "enrichers": [],
    "consumers": ["10_ingest_agent_events", "admin telemetry report",
                  "usage flywheel"],
    "columns": [
        ("event_at", "string", False),
        ("user_id", "string", False),
        ("conversation_id", "string", False),
        ("turn_index", "integer", False),
        ("question", "string", False),
        ("tools_used", "string", True),
        ("ids_read", "string", True),
        ("basis", "string", True),
        ("answered", "boolean", False),
        ("verified_by_tool", "boolean", True),
        ("llm_assembled", "boolean", True),
        ("unverified_sameness_language", "boolean", True),
        ("search_only", "boolean", True),
        ("no_tools", "boolean", True),
        ("tool_errors", "integer", True),
        ("trace", "string", True),
    ],
    "column_descriptions": {
        "event_at": "Turn timestamp (ISO)",
        "user_id": "Asker identity (Entra principal from Easy Auth)",
        "conversation_id": "Conversation the turn belongs to",
        "turn_index": "0-based turn number within the conversation",
        "question": "The question as asked",
        "tools_used": "Comma-joined tool names in call order",
        "ids_read": "Comma-joined metric/step ids read this turn",
        "basis": "The code-stamped Basis line shown to the user",
        "answered": "Whether an answer was produced",
        "verified_by_tool": "A same-logic verdict came from check_same_logic",
        "llm_assembled": "2+ fact reads, no verify call — LLM computed in memory",
        "unverified_sameness_language": "Same/different claims with no verify run (highest-risk shape)",
        "search_only": "Answer rested on a candidate list only",
        "no_tools": "No tools ran (refusals, smalltalk)",
        "tool_errors": "Count of tool calls that returned errors",
        "trace": "Full tool trace as JSON (results capped)",
    },
    "invariants": [
        {"kind": "unique", "columns": ["conversation_id", "turn_index",
                                       "event_at"]},
    ],
}

FEEDBACK_EVENTS = {
    "table_name": "gov_feedback_events",
    "description": (
        "Append-only user verdicts on agent turns (thumbs), joined to "
        "gov_turn_events by (conversation_id, turn_index) — the other "
        "half of decision attribution: no-solution patterns land next to "
        "the decision shape that produced them."
    ),
    "domain": "governance",
    "status": "active",
    "owner": {"notebook": "10_ingest_agent_events",
              "module": "src/steps/agent_events.py"},
    "write_mode": "append",
    "enrichers": [],
    "consumers": ["10_ingest_agent_events", "admin telemetry report",
                  "usage flywheel"],
    "columns": [
        ("event_at", "string", False),
        ("user_id", "string", False),
        ("conversation_id", "string", False),
        ("turn_index", "integer", False),
        ("verdict", "string", False),
        ("comment", "string", True),
    ],
    "column_descriptions": {
        "event_at": "Verdict timestamp (ISO)",
        "user_id": "Who gave the verdict",
        "conversation_id": "Conversation of the turn being judged",
        "turn_index": "Turn being judged",
        "verdict": "helpful | not_helpful",
        "comment": "Optional free text",
    },
    "invariants": [],
}

USAGE_EVENTS = {
    "table_name": "gov_usage_events",
    "description": (
        "Append-only log of agent interactions — the flywheel's ground "
        "truth (ADR 0023). One row per question: who asked, what resolved "
        "(or refused), and the asker's verdict on the answer. All usage "
        "weights and steward-queue priorities are derived from this log, "
        "never incremented in place."
    ),
    "domain": "governance",
    "status": "planned",
    "notes": (
        "Contract draft from the 2026-08-06 governance design pass (ADRs "
        "0021-0024). Needs an ingestion point from the Data Agent "
        "conversation surface; refusals log with metric_id null (the "
        "most-wanted-definitions queue)."
    ),
    "columns": [
        ("event_at", "string", False),
        ("user_id", "string", False),
        ("user_name", "string", True),
        ("department", "string", True),
        ("question", "string", False),
        ("metric_id", "string", True),
        ("outcome", "string", False),
        ("feedback", "string", True),
    ],
    "column_descriptions": {
        "event_at": "Event timestamp (ISO)",
        "user_id": "Asker identity (Entra object id, or pseudonymized id)",
        "user_name": "Asker display name",
        "department": "Asker department, if known",
        "question": "The question as asked",
        "metric_id": "Metric the answer resolved to; null when refused",
        "outcome": "answered | refused",
        "feedback": "confirmed | rejected | none — the cheapest certification signal",
    },
    "invariants": [],
}

PERSONAL_DEFINITIONS = {
    "table_name": "gov_personal_definitions",
    "description": (
        "User-owned definitions beside the enterprise graph (ADR 0024): a "
        "personal truth layer the agent answers from for its owner, always "
        "disclosed as personal. Promotion to enterprise runs the standard "
        "certification path and is fed by the flywheel (similar personal "
        "definitions across users surface as promotion candidates)."
    ),
    "domain": "governance",
    "status": "planned",
    "notes": (
        "Contract draft from the 2026-08-06 governance design pass (ADRs "
        "0021-0024). First user-private data in the lakehouse — RLS and "
        "whitepaper coverage required before flipping active."
    ),
    "columns": [
        ("definition_id", "string", False),
        ("owner_user_id", "string", False),
        ("owner_name", "string", True),
        ("name", "string", False),
        ("definition_text", "string", False),
        ("sql_fragment", "string", True),
        ("metric_id", "string", True),
        ("created_at", "string", False),
        ("updated_at", "string", True),
        ("promotion_status", "string", True),
        ("promoted_metric_id", "string", True),
    ],
    "column_descriptions": {
        "definition_id": "Unique id for this personal definition",
        "owner_user_id": "Owning user (Entra object id); only the owner resolves against it",
        "owner_name": "Owner display name (attribution on promotion)",
        "name": "The term as the owner uses it",
        "definition_text": "Plain-language definition, true for the owner",
        "sql_fragment": "Optional SQL logic backing the definition",
        "metric_id": "Enterprise metric this forks, if any",
        "created_at": "Creation timestamp (ISO)",
        "updated_at": "Last edit timestamp (ISO)",
        "promotion_status": "none | candidate | promoted | declined",
        "promoted_metric_id": "Enterprise metric created from this definition, if promoted",
    },
    "invariants": [
        {"kind": "unique", "columns": ["definition_id"]},
    ],
}



BUSINESS_TERMS = {
    "table_name": "gov_business_terms",
    "description": (
        "Business terms as a weighted plurality (ADR 0031): one row = one "
        "named definition; sibling definitions of the same concept share "
        "concept_key and distinct names. Durable human-owned truth — the "
        "graph projects terms per build, never the reverse. Status "
        "discloses trust and never gates (ADR 0021)."
    ),
    "domain": "governance",
    "status": "planned",
    "notes": (
        "Contract draft from ADR 0031 (2026-08-08). Rows come from "
        "candidate mining (src/governance/business_terms.py) reviewed by "
        "a steward, or direct authoring. Wire a writer (utility notebook "
        "or steward flow) before flipping active."
    ),
    "columns": [
        ("term_id", "string", False),
        ("concept_key", "string", False),
        ("name", "string", False),
        ("definition", "string", False),
        ("status", "string", False),
        ("steward", "string", True),
        ("source", "string", False),
        ("created_by", "string", True),
        ("created_at", "string", True),
        ("updated_at", "string", True),
    ],
    "column_descriptions": {
        "term_id": "Unique id for this named definition",
        "concept_key": "Groups sibling definitions of the same concept",
        "name": "Distinct human name (siblings must differ: 'X (scheduling)')",
        "definition": "The definition text (certification pins this text, ADR 0022 spirit)",
        "status": "emergent | certified | disputed | retired — discloses, never hides",
        "steward": "Arbitrating steward, once one engages",
        "source": "mined | authored | promoted",
        "created_by": "Who authored/accepted the term",
        "created_at": "Creation timestamp (ISO)",
        "updated_at": "Last edit timestamp (ISO)",
    },
    "invariants": [
        {"kind": "unique", "columns": ["term_id"]},
        {"kind": "allowed_values", "column": "status",
         "values": ["emergent", "certified", "disputed", "retired"]},
    ],
}

TERM_LINKS = {
    "table_name": "gov_term_links",
    "description": (
        "Which assets define/implement each business term (ADR 0031): "
        "term -> canonical metric or transformation step (DAX measures "
        "when that lane ships). Many-to-many; weight is DERIVED from "
        "endorsements + usage, never stored here."
    ),
    "domain": "governance",
    "status": "planned",
    "notes": (
        "Contract draft from ADR 0031 (2026-08-08). Written alongside "
        "gov_business_terms by the same flow; 03 projects term nodes + "
        "edges into the graph from these rows."
    ),
    "columns": [
        ("term_id", "string", False),
        ("node_ref", "string", False),
        ("node_kind", "string", False),
        ("role", "string", False),
        ("added_by", "string", True),
        ("added_at", "string", True),
    ],
    "column_descriptions": {
        "term_id": "Term (gov_business_terms.term_id)",
        "node_ref": "metric_id for metrics; graph node_id for steps",
        "node_kind": "metric | step (| measure, future)",
        "role": "defines (the definition source) | implements (uses the concept)",
        "added_by": "Who linked it (miner or human)",
        "added_at": "Link timestamp (ISO)",
    },
    "invariants": [
        {"kind": "allowed_values", "column": "node_kind",
         "values": ["metric", "step", "measure"]},
        {"kind": "allowed_values", "column": "role",
         "values": ["defines", "implements"]},
    ],
}

TERM_ENDORSEMENTS = {
    "table_name": "gov_term_endorsements",
    "description": (
        "Append-only citizen-stewardship log (ADR 0031): endorse ('this "
        "is what I meant') and dispute events per term. All term weights "
        "are derived from this log + usage events — recomputable, never "
        "incremented in place (ADR 0023 discipline)."
    ),
    "domain": "governance",
    "status": "planned",
    "notes": (
        "Contract draft from ADR 0031 (2026-08-08). Capture surface rides "
        "the ADR 0023 usage-event wiring (agent feedback or steward UI)."
    ),
    "columns": [
        ("event_at", "string", False),
        ("user_id", "string", False),
        ("term_id", "string", False),
        ("action", "string", False),
        ("context", "string", True),
    ],
    "column_descriptions": {
        "event_at": "Event timestamp (ISO)",
        "user_id": "Who endorsed/disputed (Entra object id or pseudonym)",
        "term_id": "Term acted on (gov_business_terms.term_id)",
        "action": "endorse | dispute",
        "context": "Optional free text (why disputed, question asked, ...)",
    },
    "invariants": [
        {"kind": "allowed_values", "column": "action",
         "values": ["endorse", "dispute"]},
    ],
}

METRIC_NAMES = {
    "table_name": "input_metric_names",
    "description": (
        "Business-friendly display names per metric: metric_id (qualified "
        "or unambiguous bare name, ADR 0016 folding) -> business_name, with "
        "source provenance (pbi_report | manual). Applied to canonical "
        "nodes by 03_build_graph; flows to output_metric_logic and the LPG "
        "export. Ambiguous bare names are skipped, never guessed (ADR 0005)."
    ),
    "domain": "input",
    "status": "active",
    "owner": {"notebook": "12_ingest_semantic_models", "module": "src/steps/semantic_models.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["03_build_graph", "collibra_lineage_match"],
    "optional_input": True,
    "remediation": (
        "run 12_ingest_semantic_models to derive names from PBI semantic "
        "models, or upload a manual metric_id,business_name CSV"
    ),
    "columns": [
        ("metric_id", "string", False),
        ("business_name", "string", False),
        ("source", "string", True),
        ("report_name", "string", True),
        ("report_url", "string", True),
        ("assigned_date", "string", True),
    ],
    "column_descriptions": {
        "metric_id": "Qualified metric_id preferred; bare object name accepted when unambiguous",
        "business_name": "The name the business knows the metric by",
        "source": "pbi_report | manual",
        "report_name": "Originating Power BI report, when source is pbi_report",
        "report_url": "Link to the report (app.powerbi.com); agents offer it in answers",
        "assigned_date": "When the mapping was created (ISO)",
    },
    "invariants": [
        {"kind": "unique", "columns": ["metric_id"], "fold_case": True},
    ],
}

REPORT_SOURCES = {
    "table_name": "input_report_sources",
    "description": (
        "Partition lineage from PBI semantic models (ADR 0040): which SQL "
        "object each PBI table executes, extracted deterministically from "
        "TMDL M expressions by the native TMDL parser. One row per "
        "(report, PBI table) with a resolvable source."
    ),
    "domain": "input",
    "status": "active",
    "owner": {"notebook": "12_ingest_semantic_models", "module": "src/steps/semantic_models.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["03_build_graph"],
    "optional_input": True,
    "remediation": (
        "run 12_ingest_semantic_models with a semantic_models config "
        "section (workspace, folder, or devops_git profile)"
    ),
    "columns": [
        ("report_name", "string", False),
        ("pbi_table", "string", False),
        ("server", "string", True),
        ("database_name", "string", True),
        ("schema_name", "string", True),
        ("sql_object", "string", False),
        ("sql_object_type", "string", True),
        ("repo_name", "string", True),
        ("semantic_model_path", "string", True),
        ("extracted_at", "string", True),
    ],
    "column_descriptions": {
        "report_name": "Report (from the .SemanticModel folder name)",
        "pbi_table": "PBI table whose partition executes the object",
        "server": "Server/DSN named in the M expression",
        "database_name": "Database named in the M expression",
        "schema_name": "Schema of the executed object, when present",
        "sql_object": "Proc/view the partition executes (InlineQuery when literal SQL)",
        "sql_object_type": "View | StoredProcedure | Table | InlineSQL",
        "repo_name": "DevOps repo, when the devops_git profile fetched it",
        "semantic_model_path": "Path of the .SemanticModel folder",
        "extracted_at": "Extraction timestamp (ISO)",
    },
    "invariants": [],
}

DAX_EXPRESSIONS = {
    "table_name": "input_dax_expressions",
    "description": (
        "DAX measures and calculated columns from PBI semantic models "
        "(ADR 0040) — the DAX half of the business logic, parsed by the "
        "native TMDL parser. Becomes measure nodes in the graph."
    ),
    "domain": "input",
    "status": "active",
    "owner": {"notebook": "12_ingest_semantic_models", "module": "src/steps/semantic_models.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["03_build_graph"],
    "optional_input": True,
    "remediation": (
        "run 12_ingest_semantic_models with a semantic_models config "
        "section (workspace, folder, or devops_git profile)"
    ),
    "columns": [
        ("report_name", "string", False),
        ("pbi_table", "string", False),
        ("name", "string", False),
        ("expression", "string", False),
        ("expression_type", "string", False),
    ],
    "column_descriptions": {
        "report_name": "Report whose semantic model defines the expression",
        "pbi_table": "PBI table the expression lives on",
        "name": "Measure / calculated-column name",
        "expression": "Verbatim DAX",
        "expression_type": "measure | calculated_column",
    },
    "invariants": [],
}

PHI_FINDINGS = {
    "table_name": "ops_phi_findings",
    "description": (
        "PHI / hardcoded-literal findings from ingestion-time scanning of "
        "customer SQL (ADR 0025): one row per detected literal with rule, "
        "severity, and disposition. Drives deterministic redaction at "
        "every LLM/catalog egress point; steward dispositions only "
        "unredact confirmed false positives — the default is safe."
    ),
    "domain": "operations",
    "status": "active",
    "owner": {"notebook": "02_parse", "module": "src/phi_scan.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": ["02_parse", "07_generate_descriptions"],
    "columns": [
        ("finding_id", "string", False),
        ("metric_id", "string", False),
        ("rule", "string", False),
        ("matched_text", "string", False),
        ("masked_context", "string", True),
        ("severity", "string", False),
        ("disposition", "string", False),
        ("disposed_by", "string", True),
        ("first_seen", "string", True),
    ],
    "column_descriptions": {
        "finding_id": "Stable id for the finding (hash of metric_id + rule + match)",
        "metric_id": "Metric whose SQL contains the literal (input_sql_sources.metric_id)",
        "rule": "id_literal | date_literal | name_literal | contact_literal | threshold_literal",
        "matched_text": "The literal as found (stays in-tenant; never exported)",
        "masked_context": "Surrounding SQL with the literal masked, for review UI",
        "severity": "high (id/name/contact) | medium (date) | low (threshold)",
        "disposition": "redact | allow | open",
        "disposed_by": "Steward who confirmed a false positive (allow)",
        "first_seen": "When the finding first appeared",
    },
    "invariants": [
        {"kind": "unique", "columns": ["finding_id"]},
        {"kind": "allowed_values", "column": "disposition",
         "values": ["redact", "allow", "open"]},
    ],
}

RUNTIME_ERROR_EVENTS = {
    "table_name": "ops_runtime_error_events",
    "description": (
        "Append-only occurrences of runtime/installation failures with "
        "error-to-data lineage (ADR 0026): each event names the matched "
        "signature, the pipeline stage, and the objects the failure "
        "blocks — so /troubleshoot answers 'what does this failure block?', "
        "not just 'what is this failure?'."
    ),
    "domain": "operations",
    "status": "planned",
    "notes": (
        "Contract draft from ADR 0026 (2026-08-06). "
        "ops_installation_errors stays the signature knowledge base; this "
        "log records occurrences. Wire writers per-notebook when the "
        "blast-radius view lands."
    ),
    "columns": [
        ("event_at", "string", False),
        ("run_id", "string", True),
        ("stage", "string", False),
        ("error_signature", "string", True),
        ("error_message", "string", True),
        ("affected_objects", "string", True),
    ],
    "column_descriptions": {
        "event_at": "When the failure occurred (ISO)",
        "run_id": "Pipeline run identifier, if inside a run",
        "stage": "Which notebook/step failed (01_install ... 09_publish_purview)",
        "error_signature": "Matched ops_installation_errors.error_signature, if recognized",
        "error_message": "Raw error text",
        "affected_objects": "JSON list of metric_ids / table names the failure blocks",
    },
    "invariants": [],
}


SEMANTIC_CATALOG = {
    "table_name": "output_semantic_catalog",
    "description": (
        "Resolution catalog for ask-time semantic search (ADR 0030 L3, "
        "Eventhouse engine probe-verified 2026-08-08): one searchable "
        "document per metric, named calculation step, and business term. "
        "Built by src/steps/semantic_catalog.py; the Eventhouse copy "
        "embeds search_text in-database (ai_embeddings, user "
        "impersonation) and serves semantic_search() to Data Agents — "
        "the stochastic generator never owns resolution."
    ),
    "domain": "output",
    "status": "active",
    "owner": {"notebook": "11_refresh_search_index",
              "module": "src/steps/semantic_catalog.py"},
    "write_mode": "overwrite",
    "consumers": [
        # Non-notebook consumers, declared on trust: the Eventhouse
        # copy (plain `semantic_catalog`) embeds search_text and serves
        # semantic_search() to the orchestrator core and Data Agents.
        "eventhouse_semantic_search", "data_agent", "orchestrator_core",
    ],
    "notes": (
        "Eventhouse copy is named plain semantic_catalog (KQL side); "
        "one-time setup (DDL, encoding policy, semantic_search "
        "function) in devtools/eventhouse_setup.kql; every-run refresh "
        "+ re-embed is notebook 11 (src/steps/search_index.py). The "
        "emb vector lives only in the Eventhouse copy, not in this "
        "Delta shape."
    ),
    "columns": [
        ("node_id", "string", False),
        ("kind", "string", False),
        ("ref", "string", False),
        ("name", "string", False),
        ("business_name", "string", True),
        ("search_text", "string", False),
        ("display_text", "string", False),
    ],
    "column_descriptions": {
        "node_id": "Graph node id (canonical:/transform:) or term:<term_id>",
        "kind": "metric | step | term — consumers dispatch on this",
        "ref": "metric_id for metrics/steps; term_id for terms",
        "name": "Technical name (object, CTE, or term name)",
        "business_name": "Business-friendly name when one exists",
        "search_text": "Composed document the engine embeds and searches",
        "display_text": "How resolution results introduce themselves",
    },
    "invariants": [
        {"kind": "unique", "columns": ["node_id"]},
        {"kind": "allowed_values", "column": "kind",
         "values": ["metric", "step", "term"]},
    ],
}


# Registry of all table contracts — the single source of truth.
TABLE_REGISTRY = {
    s["table_name"]: s
    for s in [
        # input
        SQL_SOURCES, DICT_TABLES, DICT_COLUMNS,
        # operations
        PARSE_RESULTS, PARSE_ERRORS, PARSE_SUCCESSES, BUILD_SUMMARY,
        PIPELINE_VALIDATION, INSTALLATION_ERRORS, AGENT_DESCRIPTIONS,
        DESCRIPTION_CACHE, SETUP_COMPLETENESS,
        # graph
        GRAPH_NODES, GRAPH_EDGES,
        # output
        METRIC_LOGIC,
        # lpg_export
        GRAPH_CANONICAL, GRAPH_TRANSFORMATION, GRAPH_TECHNICAL,
        GRAPH_REPORT, GRAPH_MEASURE,
        GRAPH_EDGE_C2T, GRAPH_EDGE_T2T, GRAPH_EDGE_T2TECH,
        GRAPH_EDGE_REPORT2CANONICAL, GRAPH_EDGE_REPORT2TECHNICAL,
        GRAPH_EDGE_REPORT2MEASURE, GRAPH_EDGE_MEASURE2COLUMN,
        GRAPH_EDGE_TAB2COL, GRAPH_EDGE_USES_TABLE,
        # semantic-model ingestion (ADR 0040)
        REPORT_SOURCES, DAX_EXPRESSIONS,
        # planned (no current writer — see notes on each)
        ERROR_LOG, EXTRACTION_INSPECTION, TRACKING, SYNC_LOG, STEWARD_ASSIGNMENTS,
        # governance lifecycle contract drafts (ADRs 0021-0024)
        CERTIFICATION_EVENTS, USAGE_EVENTS, PERSONAL_DEFINITIONS,
        # PHI scanning + error lineage contract drafts (ADRs 0025-0026)
        PHI_FINDINGS, RUNTIME_ERROR_EVENTS,
        # business-friendly names (planned writer; readers live)
        METRIC_NAMES,
        # business terms as weighted plurality (ADR 0031)
        BUSINESS_TERMS, TERM_LINKS, TERM_ENDORSEMENTS,
        # semantic-search resolution catalog (ADR 0030 L3)
        SEMANTIC_CATALOG,
        # admin telemetry (2026-08-11): DG pushes + agent decision shapes
        PUBLISH_LOG, TURN_EVENTS, FEEDBACK_EVENTS,
    ]
}

# Type mapping for PySpark conversion
_TYPE_MAP = {
    "string": "StringType",
    "integer": "IntegerType",
    "boolean": "BooleanType",
}


def to_spark_schema(schema_def: dict) -> "StructType":
    """Convert a contract's shape to a PySpark StructType.

    Only call this in Fabric notebooks where PySpark is available.
    """
    from pyspark.sql.types import (
        BooleanType,
        IntegerType,
        StringType,
        StructField,
        StructType,
    )

    type_map = {
        "string": StringType(),
        "integer": IntegerType(),
        "boolean": BooleanType(),
    }

    fields = [
        StructField(name, type_map[dtype], nullable)
        for name, dtype, nullable in schema_def["columns"]
    ]
    return StructType(fields)


def validate_columns(df_columns: list[str], schema_def: dict) -> list[str]:
    """Check that a DataFrame has the expected columns. Returns list of errors."""
    expected = {col[0] for col in schema_def["columns"]}
    actual = set(df_columns)

    errors = []
    missing = expected - actual
    if missing:
        errors.append(f"Missing columns in {schema_def['table_name']}: {sorted(missing)}")

    extra = actual - expected
    if extra:
        errors.append(f"Unexpected columns in {schema_def['table_name']}: {sorted(extra)}")

    return errors
