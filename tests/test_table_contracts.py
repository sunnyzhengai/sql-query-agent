"""Contract meta-tests: enforce the data contracts in TABLE_REGISTRY.

Every Delta table's contract declares shape, semantics (descriptions),
ownership (single owner + sanctioned enrichers/utility writers), consumers,
and invariants. These tests keep the contracts complete and — critically —
pinned to code ground truth: the writer scan covers the pipeline notebooks
AND the notebooks/ utility tree, so a rogue writer, a renamed table, or an
unregistered table fails CI.
"""

import re
from pathlib import Path

from src.config import LakehouseConfig
from src.schemas import DOMAINS, INVARIANT_KINDS, TABLE_REGISTRY

REPO_ROOT = Path(__file__).resolve().parent.parent

# Notebooks that write via a loop/constant variable instead of a literal
# table name. If a new notebook writes indirectly, it must be declared here —
# the scanner fails on any unresolved saveAsTable(<identifier>) otherwise.
NOTEBOOK_INDIRECT_WRITES = {
    "05_export_graph_tables": [
        "graph_canonical", "graph_transformation", "graph_technical",
        "graph_dimension", "graph_edge_c2t", "graph_edge_t2t",
        "graph_edge_t2tech", "graph_edge_tech2dim", "graph_edge_tab2col",
    ],
    "load_clarity_dictionary": ["input_dict_tables", "input_dict_columns"],
    "load_sql_files": ["input_sql_sources"],
}

# config.<section>.<attr> table-name indirections the scanner can resolve.
# lakehouse attrs resolve via LakehouseConfig defaults; extractor's
# tracking_table default is mirrored here because ExtractorConfig requires
# connection arguments to instantiate.
CONFIG_EXTRACTOR_DEFAULTS = {"tracking_table": "ops_extraction_tracking"}

# Notebooks that read via a helper/variable instead of a literal table name.
NOTEBOOK_INDIRECT_READS = {
    "02_parse": ["input_sql_sources"],  # via a load helper taking name_or_path
}

DOMAIN_PREFIXES = {
    "input": ("input_",),
    "operations": ("ops_",),
    "graph": ("graph_",),
    "lpg_export": ("graph_",),
    "output": ("output_",),
    "governance": ("gov_",),
}


def _notebook_files():
    """All code that can write Delta tables: pipeline + utility notebooks."""
    pipeline = list(REPO_ROOT.glob("[0-9][0-9]_*.Notebook/notebook-content.py"))
    utilities = [
        p for p in REPO_ROOT.glob("notebooks/**/*.py")
        if p.name != "__init__.py"
    ]
    return sorted(pipeline) + sorted(utilities)


def _stem(path: Path) -> str:
    if path.name == "notebook-content.py":
        return path.parent.name.removesuffix(".Notebook")
    return path.stem


def _observed_writers():
    """Scan notebook code for Delta writes: {table_name: set(writer_stems)}."""
    lakehouse_defaults = LakehouseConfig()
    observed = {}
    for path in _notebook_files():
        stem = _stem(path)
        text = path.read_text()

        tables = re.findall(r'saveAsTable\("([A-Za-z_]+)"\)', text)
        for attr in re.findall(r"saveAsTable\(config\.lakehouse\.(\w+)\)", text):
            tables.append(getattr(lakehouse_defaults, attr))
        for attr in re.findall(r"saveAsTable\(config\.extractor\.(\w+)\)", text):
            tables.append(CONFIG_EXTRACTOR_DEFAULTS[attr])
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


def _observed_readers():
    """Scan notebook code for Delta reads: {table_name: set(reader_stems)}.

    Only literal and config-resolved reads are attributed. Variable reads
    (postcondition-gate fetch lambdas, 06's invariant checker) are
    cross-cutting validation, not dataflow consumers, and are ignored.
    """
    lakehouse_defaults = LakehouseConfig()
    observed = {}
    for path in _notebook_files():
        stem = _stem(path)
        text = path.read_text()

        tables = re.findall(r'spark\.table\("([A-Za-z_]+)"\)', text)
        for attr in re.findall(r"spark\.table\(config\.lakehouse\.(\w+)\)", text):
            tables.append(getattr(lakehouse_defaults, attr))
        for attr in re.findall(r"spark\.table\(config\.extractor\.(\w+)\)", text):
            tables.append(CONFIG_EXTRACTOR_DEFAULTS[attr])
        tables.extend(NOTEBOOK_INDIRECT_READS.get(stem, []))

        for table in tables:
            if table in TABLE_REGISTRY:
                observed.setdefault(table, set()).add(stem)
    return observed


def _declared_writers(contract) -> set:
    return {
        contract["owner"]["notebook"],
        *contract.get("enrichers", []),
        *contract.get("utility_writers", []),
    }


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


def test_declared_writers_match_code_ground_truth():
    """The load-bearing test: every observed write must be declared, and
    every declared writer must actually write."""
    observed = _observed_writers()

    for table, writers in observed.items():
        assert table in TABLE_REGISTRY, (
            f"notebooks write table '{table}' (by {sorted(writers)}) "
            f"but it has no contract in TABLE_REGISTRY"
        )

    for name, contract in _active().items():
        declared = _declared_writers(contract)
        actual = observed.get(name, set())
        assert actual == declared, (
            f"{name}: contract declares writers {sorted(declared)} "
            f"but code shows {sorted(actual)}"
        )

    for name in _planned():
        assert name not in observed, (
            f"{name}: marked 'planned' but notebooks write it — set status active"
        )


def test_declared_consumers_match_code_ground_truth():
    """The read side of the dataflow DAG: every literal/config-resolved read
    in notebook code must be a declared consumer, and every declared
    notebook consumer must actually read. Non-notebook consumers
    (data_agent, admin, adapters) are declared on trust."""
    observed = _observed_readers()
    stems = {_stem(p) for p in _notebook_files()}

    for name, contract in _active().items():
        declared = set(contract.get("consumers", []))
        declared_stems = {c for c in declared if c in stems}
        actual = observed.get(name, set())
        assert actual == declared_stems, (
            f"{name}: contract declares notebook consumers {sorted(declared_stems)} "
            f"but code shows readers {sorted(actual)}"
        )


def test_relations_are_well_formed():
    for name, contract in TABLE_REGISTRY.items():
        columns = {c[0] for c in contract["columns"]}
        for rel in contract.get("relations", []):
            assert rel["kind"] == "count_equals", f"{name}: unknown relation kind"
            other = rel["other_table"]
            assert other in TABLE_REGISTRY, f"{name}: relation to unregistered {other}"
            if rel.get("where"):
                assert set(rel["where"]) <= columns, f"{name}: relation where on unknown columns"
            if rel.get("other_where"):
                other_cols = {c[0] for c in TABLE_REGISTRY[other]["columns"]}
                assert set(rel["other_where"]) <= other_cols, (
                    f"{name}: relation other_where on unknown columns of {other}"
                )


def test_column_types_are_convertible():
    from src.schemas import _TYPE_MAP

    for name, contract in TABLE_REGISTRY.items():
        for col, dtype, _nullable in contract["columns"]:
            assert dtype in _TYPE_MAP, f"{name}.{col}: unknown type {dtype}"
