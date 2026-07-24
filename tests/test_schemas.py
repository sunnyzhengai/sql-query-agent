"""Tests for schema contracts.

Validates that schema definitions are well-formed and consistent.
"""

from src.schemas import TABLE_REGISTRY, validate_columns


def test_all_tables_have_columns():
    """Every registered table must have at least one column."""
    for name, schema in TABLE_REGISTRY.items():
        assert len(schema["columns"]) > 0, f"{name} has no columns"


def test_all_columns_have_valid_types():
    """Every column must have a recognized type."""
    valid_types = {"string", "integer", "boolean"}
    for name, schema in TABLE_REGISTRY.items():
        for col_name, col_type, _ in schema["columns"]:
            assert col_type in valid_types, (
                f"{name}.{col_name} has invalid type '{col_type}'"
            )


def test_no_duplicate_column_names():
    """No table should have duplicate column names."""
    for name, schema in TABLE_REGISTRY.items():
        col_names = [col[0] for col in schema["columns"]]
        assert len(col_names) == len(set(col_names)), (
            f"{name} has duplicate columns: {col_names}"
        )


def test_table_names_are_unique():
    """All table names must be unique."""
    names = [s["table_name"] for s in TABLE_REGISTRY.values()]
    assert len(names) == len(set(names))


def test_primary_tables_have_non_nullable_key():
    """Core tables should have at least one non-nullable column."""
    for name, schema in TABLE_REGISTRY.items():
        non_nullable = [col for col in schema["columns"] if not col[2]]
        assert len(non_nullable) > 0, f"{name} has no non-nullable columns"


def test_validate_columns_catches_missing():
    """validate_columns should report missing columns."""
    from src.schemas import GRAPH_NODES
    errors = validate_columns(["node_id", "layer"], GRAPH_NODES)
    assert len(errors) > 0
    assert "Missing columns" in errors[0]


def test_validate_columns_catches_extra():
    """validate_columns should report unexpected columns."""
    from src.schemas import GRAPH_NODES
    all_cols = [c[0] for c in GRAPH_NODES["columns"]] + ["bogus_column"]
    errors = validate_columns(all_cols, GRAPH_NODES)
    assert len(errors) > 0
    assert "Unexpected columns" in errors[0]


def test_validate_columns_passes_when_correct():
    """validate_columns should return empty list when columns match."""
    from src.schemas import GRAPH_NODES
    cols = [c[0] for c in GRAPH_NODES["columns"]]
    errors = validate_columns(cols, GRAPH_NODES)
    assert errors == []
