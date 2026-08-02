"""Contract meta-tests: enforce the data contracts in TABLE_REGISTRY.

Every Delta table's contract declares shape, semantics (descriptions),
ownership (single writer), consumers, and invariants. These tests keep the
contracts complete and — critically — pinned to code ground truth: the
single-writer test scans the pipeline notebooks for actual writes, so a
rogue writer, a renamed table, or an unregistered table fails CI.
"""

import re
from pathlib import Path

from src.config import LakehouseConfig
from src.schemas import DOMAINS, INVARIANT_KINDS, TABLE_REGISTRY

REPO_ROOT = Path(__file__).resolve().parent.parent

# Notebooks that write via a loop variable instead of a literal table name.
# If a new notebook writes indirectly, it must be declared here — the scanner
# fails on any unresolved saveAsTable(<identifier>) otherwise.
NOTEBOOK_INDIRECT_WRITES = {
    "05_export_graph_tables": [
        "graph_canonical", "graph_transformation", "graph_technical",
        "graph_dimension", "graph_edge_c2t", "graph_edge_t2t",
        "graph_edge_t2tech", "graph_edge_tech2dim",
    ],
}

DOMAIN_PREFIXES = {
    "input": ("input_",),
    "operations": ("ops_",),
    "graph": ("graph_",),
    "lpg_export": ("graph_",),
    "output": ("output_",),
    "governance": ("gov_",),
}


def _pipeline_notebooks():
    return sorted(REPO_ROOT.glob("[0-9][0-9]_*.Notebook/notebook-content.py"))


def _observed_writers():
    """Scan notebook code for Delta writes: {table_name: set(notebook_stems)}."""
    lakehouse_defaults = LakehouseConfig()
    observed = {}
    for path in _pipeline_notebooks():
        stem = path.parent.name.removesuffix(".Notebook")
        text = path.read_text()

        tables = re.findall(r'saveAsTable\("([A-Za-z_]+)"\)', text)
        for attr in re.findall(r"saveAsTable\(config\.lakehouse\.(\w+)\)", text):
            tables.append(getattr(lakehouse_defaults, attr))
        tables.extend(NOTEBOOK_INDIRECT_WRITES.get(stem, []))

        unresolved = [
            m for m in re.findall(r"saveAsTable\((\w+)\)", text)
            if stem not in NOTEBOOK_INDIRECT_WRITES
        ]
        assert not unresolved, (
            f"{stem} writes via variable(s) {unresolved} — add the notebook to "
            f"NOTEBOOK_INDIRECT_WRITES with the tables it writes"
        )

        for table in tables:
            observed.setdefault(table, set()).add(stem)
    return observed


def _active():
    return {n: c for n, c in TABLE_REGISTRY.items() if c["status"] == "active"}


def _planned():
    return {n: c for n, c in TABLE_REGISTRY.items() if c["status"] == "planned"}


def test_every_table_has_semantics():
    for name, contract in TABLE_REGISTRY.items():
        assert contract.get("description", "").strip(), f"{name}: missing description"
        assert contract.get("domain") in DOMAINS, f"{name}: bad domain {contract.get('domain')}"
        assert contract.get("status") in ("active", "planned"), f"{name}: bad status"


def test_every_column_has_a_description():
    for name, contract in TABLE_REGISTRY.items():
        columns = {c[0] for c in contract["columns"]}
        described = set(contract.get("column_descriptions", {}))
        assert columns == described, (
            f"{name}: undescribed columns {sorted(columns - described)}; "
            f"descriptions for nonexistent columns {sorted(described - columns)}"
        )
        empty = [c for c, d in contract["column_descriptions"].items() if not d.strip()]
        assert not empty, f"{name}: empty descriptions for {empty}"


def test_table_name_prefix_matches_domain():
    for name, contract in TABLE_REGISTRY.items():
        prefixes = DOMAIN_PREFIXES[contract["domain"]]
        assert name.startswith(prefixes), (
            f"{name}: domain '{contract['domain']}' requires prefix {prefixes}"
        )


def test_active_tables_declare_owner_and_consumers():
    for name, contract in _active().items():
        owner = contract.get("owner") or {}
        assert owner.get("notebook"), f"{name}: active table missing owner.notebook"
        assert contract.get("consumers"), f"{name}: active table missing consumers"
        assert contract.get("write_mode") in ("overwrite", "append"), (
            f"{name}: bad write_mode"
        )


def test_planned_tables_explain_themselves():
    for name, contract in _planned().items():
        assert contract.get("notes", "").strip(), (
            f"{name}: planned table needs a notes field explaining intent/status"
        )


def test_invariants_are_well_formed():
    for name, contract in TABLE_REGISTRY.items():
        columns = {c[0] for c in contract["columns"]}
        for inv in contract.get("invariants", []):
            kind = inv.get("kind")
            assert kind in INVARIANT_KINDS, f"{name}: unknown invariant kind {kind}"
            if kind == "allowed_values":
                assert inv["column"] in columns, f"{name}: invariant on unknown column"
                assert inv["values"], f"{name}: allowed_values with no values"
            elif kind == "unique":
                assert set(inv["columns"]) <= columns, f"{name}: unique on unknown columns"
            elif kind == "reference":
                assert inv["column"] in columns, f"{name}: reference from unknown column"
                target_table, target_col = inv["references"].split(".")
                assert target_table in TABLE_REGISTRY, (
                    f"{name}: reference to unregistered table {target_table}"
                )
                target_cols = {c[0] for c in TABLE_REGISTRY[target_table]["columns"]}
                assert target_col in target_cols, (
                    f"{name}: reference to unknown column {inv['references']}"
                )


def test_single_writer_matches_code_ground_truth():
    """The load-bearing test: declared ownership must equal observed writes."""
    observed = _observed_writers()

    for table, writers in observed.items():
        assert table in TABLE_REGISTRY, (
            f"notebooks write table '{table}' (by {sorted(writers)}) "
            f"but it has no contract in TABLE_REGISTRY"
        )

    for name, contract in _active().items():
        declared = {contract["owner"]["notebook"], *contract.get("enrichers", [])}
        actual = observed.get(name, set())
        assert actual == declared, (
            f"{name}: contract declares writers {sorted(declared)} "
            f"but code shows {sorted(actual)}"
        )

    for name in _planned():
        assert name not in observed, (
            f"{name}: marked 'planned' but notebooks write it — set status active"
        )


def test_column_types_are_convertible():
    from src.schemas import _TYPE_MAP

    for name, contract in TABLE_REGISTRY.items():
        for col, dtype, _nullable in contract["columns"]:
            assert dtype in _TYPE_MAP, f"{name}.{col}: unknown type {dtype}"
