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
    "description": (
        "Customer SQL source files (stored procedures and views) loaded from "
        "Files/sql-query-agent/sql_input/. One row per SQL object; identity "
        "comes from the CREATE/ALTER statement inside the file, not the filename."
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
    ],
    "column_descriptions": {
        "metric_id": "SQL object this parse belongs to (input_sql_sources.metric_id)",
        "name": "Object name",
        "ctes_json": "JSON list of CTE steps: name, sql_fragment, dependencies, tables",
        "final_select_tables": "JSON list of physical tables read by the final SELECT",
        "final_select_cte_refs": "JSON list of CTEs referenced by the final SELECT",
        "normalized_sql": "Cleaned SQL after extraction (verbatim statements, \\n endings)",
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
    "description": (
        "All nodes of the three-layer knowledge graph in one table, "
        "discriminated by `layer`: canonical (business metrics), "
        "transformation (CTE steps with sql_fragments), technical (warehouse "
        "tables/columns enriched from the data dictionary), and dimension "
        "(filter columns). The certified ground truth the agent answers from."
    ),
    "domain": "graph",
    "status": "active",
    "owner": {"notebook": "03_build_graph", "module": "src/graph/builder.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": [
        "04_build_metric_logic", "05_export_graph_tables", "06_validate",
        "08_publish_collibra", "manage_stewards", "verify_graph", "data_agent",
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
        "layer": "Which of the three layers (+dimension) this node belongs to",
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
    "description": (
        "Directed edges wiring the graph layers together: metric -> logic "
        "steps -> source tables -> dimensions. Both endpoints must exist in "
        "graph_nodes."
    ),
    "domain": "graph",
    "status": "active",
    "owner": {"notebook": "03_build_graph", "module": "src/graph/builder.py"},
    "write_mode": "overwrite",
    "enrichers": [],
    "consumers": [
        "04_build_metric_logic", "05_export_graph_tables", "06_validate",
        "08_publish_collibra", "verify_graph", "data_agent",
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
        "metric_name": "Display name of the metric",
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
        ("sqlFragment", "string", True),
    ],
    "column_descriptions": {
        "nodeId": "Transformation node id (graph_nodes.node_id)",
        "name": "CTE/step name",
        "metricId": "Metric this step belongs to",
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

GRAPH_DIMENSION = {
    "table_name": "graph_dimension",
    "description": "LPG export: dimension nodes (filterable columns branching off technical nodes).",
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
        ("columnName", "string", False),
    ],
    "column_descriptions": {
        "nodeId": "Dimension node id (graph_nodes.node_id)",
        "name": "Display name",
        "description": "Dictionary description",
        "tableName": "Physical table the dimension column lives in",
        "columnName": "The dimension column",
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

GRAPH_EDGE_TECH2DIM = {
    "table_name": "graph_edge_tech2dim",
    "description": "LPG export: technical -> dimension edges (table to its filterable columns).",
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
        {"kind": "reference", "column": "targetId", "references": "graph_dimension.nodeId"},
    ],
}


# =====================================================================
# GOVERNANCE / OPERATIONS extras — error log and steward assignments
# (recovered 2026-08-02 from the dead-code purge), Tier 2 extraction
# tracking, and the remaining PLANNED contracts (no writer yet; the
# single-writer test enforces nothing writes those until activated).
# =====================================================================

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


# Registry of all table contracts — the single source of truth.
TABLE_REGISTRY = {
    s["table_name"]: s
    for s in [
        # input
        SQL_SOURCES, DICT_TABLES, DICT_COLUMNS,
        # operations
        PARSE_RESULTS, PARSE_ERRORS, PARSE_SUCCESSES, BUILD_SUMMARY,
        PIPELINE_VALIDATION, INSTALLATION_ERRORS, AGENT_DESCRIPTIONS,
        # graph
        GRAPH_NODES, GRAPH_EDGES,
        # output
        METRIC_LOGIC,
        # lpg_export
        GRAPH_CANONICAL, GRAPH_TRANSFORMATION, GRAPH_TECHNICAL, GRAPH_DIMENSION,
        GRAPH_EDGE_C2T, GRAPH_EDGE_T2T, GRAPH_EDGE_T2TECH, GRAPH_EDGE_TECH2DIM,
        GRAPH_EDGE_TAB2COL, GRAPH_EDGE_USES_TABLE,
        # planned (no current writer — see notes on each)
        ERROR_LOG, EXTRACTION_INSPECTION, TRACKING, SYNC_LOG, STEWARD_ASSIGNMENTS,
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
