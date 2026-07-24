"""Centralized Delta table schema definitions.

Single source of truth for all table schemas used across notebooks.
Import these instead of defining StructType inline.

Usage in Fabric notebooks:
    from src.schemas import GRAPH_NODES_SCHEMA, GRAPH_EDGES_SCHEMA
    nodes_df = spark.createDataFrame(rows, schema=GRAPH_NODES_SCHEMA)

Adding a new table:
    1. Define the schema constant here
    2. Add it to TABLE_REGISTRY
    3. Import it in your notebook
"""

from __future__ import annotations

# These types are only available in PySpark (Fabric notebooks).
# Define schemas as plain dicts so src/ stays importable without PySpark,
# and provide a helper to convert to StructType at runtime.

GRAPH_NODES = {
    "table_name": "graph_nodes",
    "columns": [
        ("node_id", "string", False),
        ("layer", "string", False),
        ("name", "string", False),
        ("description", "string", True),
        ("properties", "string", True),
    ],
}

GRAPH_EDGES = {
    "table_name": "graph_edges",
    "columns": [
        ("source_id", "string", False),
        ("target_id", "string", False),
        ("edge_type", "string", False),
        ("properties", "string", True),
    ],
}

METRIC_LOGIC = {
    "table_name": "metric_logic",
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
}

SQL_SOURCES = {
    "table_name": "sql_sources",
    "columns": [
        ("metric_id", "string", False),
        ("name", "string", False),
        ("sql", "string", False),
        ("steward", "string", True),
        ("developer", "string", True),
        ("source_type", "string", True),
        ("source_schema", "string", True),
    ],
}

PARSE_ERRORS = {
    "table_name": "parse_errors",
    "columns": [
        ("metric_id", "string", False),
        ("name", "string", False),
        ("error", "string", True),
        ("line_count", "integer", True),
    ],
}

PARSE_SUCCESSES = {
    "table_name": "parse_successes",
    "columns": [
        ("metric_id", "string", False),
        ("name", "string", False),
        ("cte_count", "integer", True),
        ("table_count", "integer", True),
        ("line_count", "integer", True),
    ],
}

BUILD_SUMMARY = {
    "table_name": "build_summary",
    "columns": [
        ("build_time", "string", False),
        ("metric_key", "string", False),
        ("value", "string", False),
        ("detail", "string", True),
    ],
}

EXTRACTION_INSPECTION = {
    "table_name": "extraction_inspection",
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
}

ERROR_LOG = {
    "table_name": "error_log",
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
}

PIPELINE_VALIDATION = {
    "table_name": "pipeline_validation",
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
}

STEWARD_ASSIGNMENTS = {
    "table_name": "steward_assignments",
    "columns": [
        ("metric_id", "string", False),
        ("steward", "string", True),
        ("developer", "string", True),
        ("assigned_at", "string", True),
        ("assigned_by", "string", True),
    ],
}

SYNC_LOG = {
    "table_name": "sync_log",
    "columns": [
        ("synced_at", "string", False),
        ("adapter", "string", False),
        ("asset_id", "string", False),
        ("status", "string", False),
        ("message", "string", True),
    ],
}

TRACKING = {
    "table_name": "extraction_tracking",
    "columns": [
        ("object_name", "string", False),
        ("object_type", "string", False),
        ("schema_name", "string", True),
        ("sql_hash", "string", True),
        ("status", "string", True),
        ("last_seen", "string", True),
    ],
}

# Registry of all tables — use for validation and health checks
TABLE_REGISTRY = {
    s["table_name"]: s
    for s in [
        GRAPH_NODES, GRAPH_EDGES, METRIC_LOGIC, SQL_SOURCES,
        PARSE_ERRORS, PARSE_SUCCESSES, BUILD_SUMMARY,
        EXTRACTION_INSPECTION, ERROR_LOG, PIPELINE_VALIDATION,
        STEWARD_ASSIGNMENTS, SYNC_LOG, TRACKING,
    ]
}

# Type mapping for PySpark conversion
_TYPE_MAP = {
    "string": "StringType",
    "integer": "IntegerType",
    "boolean": "BooleanType",
}


def to_spark_schema(schema_def: dict) -> "StructType":
    """Convert a schema definition to a PySpark StructType.

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
