"""ADR 0055 — the `shapes` suite family (CI leg).

Four strata:
1. Matrix totality — every ratified dimension value covered by a cell
   (instantiated ⊎ excluded-with-reason); no silent uncoverage.
2. Corpus of record — regeneration is byte-identical to the committed
   files (the TRACE_MAP pattern; a palette or generator change without
   a regen fails here).
3. L0 generator — the compose() styles behave (ws normalizes equal,
   semflip normalizes different).
4. End to end — the REAL pipeline (parse → graph → sweep) over the
   corpus, held to the manifest: every planted sin found, none
   invented, boundary cells disclosed.

The live/ask leg (workbench + tenant) is a recorded follow-up behind
Sunny's tenant-load decision — R6 (wrong-kind) documents its own
exclusion for exactly that reason.
"""

import json
from pathlib import Path

import pytest

from src.orchestrator.tools import _content_key
from src.shapes.checker import check_all, run_corpus
from src.shapes.generator import compose, generate, load_palette
from src.shapes.matrix import DIMENSIONS, uncovered

REPO = Path(__file__).resolve().parent.parent.parent
PALETTE_PATH = REPO / "data" / "shapes" / "palette_diabetes.json"
GENERATED = REPO / "data" / "shapes" / "generated"


@pytest.fixture(scope="module")
def palette():
    return load_palette(PALETTE_PATH)


@pytest.fixture(scope="module")
def corpus_run(palette):
    return run_corpus(palette)


# --- 1. totality -------------------------------------------------------


def test_every_dimension_value_is_covered(palette):
    _, manifest = generate(palette)
    assert uncovered(manifest) == [], (
        "ratified dimension values with NO cell (instantiated or "
        "excluded-with-reason) — the matrix has a silent hole")


def test_every_cell_is_instantiated_or_excluded_with_reason(palette):
    _, manifest = generate(palette)
    for c in manifest["cells"]:
        assert c["status"] in ("instantiated", "excluded"), c["cell_id"]
        if c["status"] == "excluded":
            assert c.get("reason"), (
                f"{c['cell_id']}: an exclusion without a reason is a "
                "decision nobody made")
        else:
            assert c.get("files"), f"{c['cell_id']}: no files"


def test_dimension_set_is_the_ratified_one():
    assert set(DIMENSIONS) == {
        "D1_name_relation", "D2_logic_relation", "D3_scope",
        "D4_reference_form", "D5_chain_shape", "D6_hygiene"}


# --- 2. corpus of record ----------------------------------------------


def test_committed_corpus_matches_regeneration(palette):
    files, manifest = generate(palette)
    for relpath, sql in files.items():
        on_disk = (GENERATED / "sql" / relpath)
        assert on_disk.exists(), (
            f"{relpath} missing — run devtools/generate_shapes.py")
        assert on_disk.read_bytes() == sql.encode(), (
            f"{relpath} stale — run devtools/generate_shapes.py")
    committed = json.loads(
        (GENERATED / "shape_manifest.json").read_text())
    assert committed == manifest, (
        "shape_manifest.json stale — run devtools/generate_shapes.py")


# --- 3. L0 generator ---------------------------------------------------


def test_respace_normalizes_equal(palette):
    a = compose(palette, "X_Pop", "lab")
    b = compose(palette, "X_Pop", "lab", style="respace")
    assert a != b
    assert _content_key(a) == _content_key(b)


def test_semflip_normalizes_different(palette):
    a = compose(palette, "X_Pop", "lab")
    b = compose(palette, "X_Pop", "lab", style="semflip")
    assert _content_key(a) != _content_key(b)


def test_crlf_twin_normalizes_equal_after_entry_normalization(palette):
    files, _ = generate(palette)
    a = files["reporting/USP_Crlf_Probe_A.sql"]
    b = files["reporting/USP_Crlf_Probe_B.sql"]
    assert "\r\n" in b and "\r\n" not in a
    assert (_content_key(a)
            == _content_key(b.replace("\r\n", "\n").replace(
                "USP_Crlf_Probe_B", "USP_Crlf_Probe_A")))


# --- 4. end to end -----------------------------------------------------


def test_corpus_parses_with_only_declared_exceptions(corpus_run):
    categories = dict(corpus_run.parse_failures)
    undeclared = {m: c for m, c in categories.items()
                  if c.startswith("UNCLASSIFIED")}
    assert not undeclared, undeclared
    # the ONLY expected parse exception is the dynamic-SQL hygiene cell
    assert set(categories) <= {"reporting.USP_Adhoc_Extract"}


def test_every_instantiated_cell_passes(corpus_run):
    results = check_all(corpus_run)
    failing = {r.cell_id: r.details for r in results if not r.ok}
    assert not failing, (
        "shape cells with expected≠actual:\n"
        + json.dumps(failing, indent=1))


def test_conservation_and_no_dangling(corpus_run):
    # build_graph_step asserts dangling edges + projection
    # conservation internally; the sweep asserts its partition —
    # reaching here means both held. Assert the headline numbers are
    # sane and recorded.
    assert corpus_run.build.node_count > 0
    assert corpus_run.build.flags_swept == (
        corpus_run.build.flags_flagged + corpus_run.build.flags_clean
        + sum(corpus_run.build.flags_excluded.values()))


def test_isolation_realism_corpus_untouched(corpus_run):
    # Sunny's ruling 3: shapes never touch the 28-file realism cohort.
    # The corpus run consumes ONLY generated files + the palette
    # dictionary; no shape metric id may collide with a recorded one.
    recorded = json.loads(
        (REPO / "tests" / "fixtures" / "recorded" /
         "parse_results.json").read_text())
    realism_ids = {r["metric_id"] for r in recorded}
    shape_ids = {p["metric_id"] for p in corpus_run.parse_rows}
    assert not (realism_ids & shape_ids), (
        "shape corpus collides with realism metric ids — isolation "
        "broken")


# --- Phase 2: property surface (seeded, deterministic) ----------------


def test_seeded_compositions_hold_pipeline_invariants(palette):
    """Property leg: ANY composition of (path, style) pairs builds a
    graph whose conservation holds — seeded, deterministic (spec:E2:
    no wall-clock randomness)."""
    import random

    from src.graph.serialization import parsed_sql_to_parse_result_row
    from src.parser.sql_parser import parse_sql
    from src.shapes.generator import _proc, dict_rows
    from src.steps.build_graph import build_graph_step

    rng = random.Random(550055)
    paths = sorted(palette["logic_paths"])
    styles = ["plain", "respace", "semflip"]
    rows = []
    for i in range(12):
        n_ctes = rng.randint(1, 4)
        ctes, prev = [], None
        for j in range(n_ctes):
            name = f"Gen_{i}_{j}"
            ctes.append(compose(palette, name, rng.choice(paths),
                                style=rng.choice(styles)))
            prev = name
        sql = _proc("reporting", f"USP_Gen_{i}", ctes, prev)
        parsed = parse_sql(sql)
        rows.append(parsed_sql_to_parse_result_row(
            f"reporting.USP_Gen_{i}", f"USP_Gen_{i}", parsed))
    tables, columns = dict_rows(palette)
    out = build_graph_step(rows, tables, columns)
    # internal asserts (dangling, projection conservation) passed;
    # every generated proc must have a canonical node
    node_ids = {n["node_id"] for n in out.nodes_rows}
    for i in range(12):
        assert f"canonical:reporting.USP_Gen_{i}" in node_ids


# --- payload 3: the Diabetes Registry Dashboard (ruled 2026-08-25) ---


def test_dashboard_joins_the_shape_graph(corpus_run):
    # acceptance (handoff §PAYLOAD 3 item 5): the pointer-chase shape —
    # the report node exists and links to the U7 composite through the
    # REAL TMDL parse; the two inline-SQL tables are disclosed sources,
    # never silent
    from src.shapes.checker import DASHBOARD_METRIC, DASHBOARD_NAME
    node_ids = {n["node_id"] for n in corpus_run.build.nodes_rows}
    report_id = "report:" + DASHBOARD_NAME.upper()
    assert report_id in node_ids
    assert (report_id, f"canonical:{DASHBOARD_METRIC}",
            "report_to_canonical") in {
        (e["source_id"], e["target_id"], e["edge_type"])
        for e in corpus_run.build.edges_rows}
    by_type = [r["sql_object_type"] for r in corpus_run.report_source_rows]
    assert sorted(by_type) == ["InlineSQL", "InlineSQL",
                               "StoredProcedure"]


def test_dashboard_is_anchored_not_isolated(corpus_run):
    # the report reaches the principal component via U7 — it must NOT
    # appear as a consumption_unanchored island (ADR 0059 Q1)
    from src.graph.topology import analyze
    t = analyze(corpus_run.build.nodes_rows, corpus_run.build.edges_rows)
    assert t.ok and not t.consumption_unanchored


def test_dashboard_description_stays_empty():
    # Sunny's ruling item 2: the report description is the write-back
    # beat's STAGE — it ships empty and stays empty until the demo
    # publishes the certified definition onto it live
    import json as _json
    for item in ("Diabetes Registry Dashboard.SemanticModel",
                 "Diabetes Registry Dashboard.Report"):
        meta = _json.loads((REPO / item / ".platform").read_text())
        assert "description" not in meta["metadata"], (
            f"{item}: description must stay EMPTY (write-back stage)")
        assert meta["metadata"]["displayName"] == \
            "Diabetes Registry Dashboard"


def test_dashboard_tmdl_carries_no_tenant_endpoint():
    # endpoint-hygiene law: the M source uses the workspace-parameter
    # placeholder, exactly like the sepsis precedent
    root = REPO / "Diabetes Registry Dashboard.SemanticModel"
    for tmdl in root.rglob("*.tmdl"):
        text = tmdl.read_text()
        assert ".database.windows.net" not in text
        assert ".fabric.microsoft.com" not in text
