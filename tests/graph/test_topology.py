"""ADR 0059 — the topology axioms' CI leg: L0 for the union-find
analyzer, G2 mapping totality, and the recorded-corpus baseline
(the one-off measurement made permanent: 1 principal component, 0
orphans, 0 dangling at 6,669 nodes / 14,994 edges)."""

import csv
import importlib.util
import json
from pathlib import Path

from src.graph.topology import DEGREE_ZERO_EXCLUSIONS, Topology, analyze
from src.models import EDGE_PROVENANCE, PROVENANCE_CLASSES, EdgeType

REPO = Path(__file__).resolve().parent.parent.parent


def _n(nid, layer):
    return {"node_id": nid, "layer": layer, "name": nid,
            "description": "", "properties": "{}"}


def _e(s, t, et="transform_to_technical"):
    return {"source_id": s, "target_id": t, "edge_type": et,
            "properties": "{}"}


# --- G2 totality -------------------------------------------------------


def test_every_edge_type_has_exactly_one_provenance_class():
    assert set(EDGE_PROVENANCE) == set(EdgeType), (
        "EDGE_PROVENANCE and EdgeType drifted — a new edge type "
        "cannot ship without its provenance class (G2)")
    for et, cls in EDGE_PROVENANCE.items():
        assert cls in PROVENANCE_CLASSES, f"{et}: {cls!r}"


# --- L0 analyzer -------------------------------------------------------


class TestAnalyzer:
    def test_clean_graph_is_ok(self):
        t = analyze(
            [_n("canonical:m", "canonical"),
             _n("transform:m:s", "transformation"),
             _n("tech:DBO.T", "technical")],
            [_e("canonical:m", "transform:m:s",
                "canonical_to_transform"),
             _e("transform:m:s", "tech:DBO.T")])
        assert t.ok and t.components == 1 and t.principal_size == 3

    def test_dangling_edge_violates(self):
        t = analyze([_n("canonical:m", "canonical")],
                    [_e("canonical:m", "ghost:x")])
        assert not t.ok and t.dangling_edges

    def test_degree_zero_derived_node_violates(self):
        t = analyze([_n("canonical:m", "canonical"),
                     _n("canonical:orphan", "canonical"),
                     _n("transform:m:s", "transformation")],
                    [_e("canonical:m", "transform:m:s",
                        "canonical_to_transform")])
        assert not t.ok and t.degree_zero == ["canonical:orphan"]

    def test_receipt_node_is_the_enumerated_exclusion(self):
        t = analyze([_n("canonical:m", "canonical"),
                     _n("transform:m:s", "transformation"),
                     _n("govmeta:sweep", "governance")],
                    [_e("canonical:m", "transform:m:s",
                        "canonical_to_transform")])
        assert t.ok
        assert t.excluded_degree_zero == {
            "govmeta:sweep": "build_receipt"}
        assert "govmeta:sweep" in DEGREE_ZERO_EXCLUSIONS

    def test_stray_derived_component_violates(self):
        t = analyze(
            [_n("canonical:a", "canonical"),
             _n("transform:a:s", "transformation"),
             _n("canonical:b", "canonical"),
             _n("transform:b:s", "transformation")],
            [_e("canonical:a", "transform:a:s",
                "canonical_to_transform"),
             _e("canonical:b", "transform:b:s",
                "canonical_to_transform")])
        assert not t.ok
        assert len(t.stray_derived_components) == 1

    def test_foundation_island_is_legitimate_and_enumerated(self):
        # the FOUNDATION EXCEPTION (Sunny, 2026-08-26): a sovereign
        # dictionary table nothing reads yet — connected internally
        # (table->column), enumerated, never a finding
        t = analyze(
            [_n("canonical:m", "canonical"),
             _n("transform:m:s", "transformation"),
             _n("tech:DBO.UNREAD", "technical"),
             _n("tech:DBO.UNREAD.COL", "technical")],
            [_e("canonical:m", "transform:m:s",
                "canonical_to_transform"),
             _e("tech:DBO.UNREAD", "tech:DBO.UNREAD.COL",
                "table_to_column")])
        assert t.ok
        assert len(t.foundation_islands) == 1
        assert t.components == 2

    def test_unmapped_edge_type_violates(self):
        t = analyze([_n("canonical:a", "canonical"),
                     _n("canonical:b", "canonical")],
                    [_e("canonical:a", "canonical:b", "mystery_link")])
        assert not t.ok
        assert t.unmapped_edge_types == ["UNKNOWN:mystery_link"]


# --- the recorded-corpus baseline, permanent --------------------------


def test_recorded_corpus_holds_the_measured_baseline():
    spec = importlib.util.spec_from_file_location(
        "rpl", REPO / "scripts" / "run_pipeline_local.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pr, tables, columns = mod.load_recorded(
        REPO / "tests" / "fixtures" / "recorded")
    names = list(csv.DictReader(
        open(REPO / "data" / "demo" / "input_metric_names.csv")))
    from src.steps.build_graph import build_graph_step
    out = build_graph_step(pr, tables, columns,
                           metric_name_records=names)
    t = analyze(out.nodes_rows, out.edges_rows)
    assert t.ok, t.summary()
    # the ratified invariants: ONE principal derived component, zero
    # orphans, zero dangling, empty isolation list on this corpus
    assert t.components == 1 and not t.foundation_islands
    # the measured baseline (2026-08-26): shrink = extraction
    # regression; growth is expected
    assert t.node_count >= 6669, t.summary()
    assert t.edge_count >= 14994, t.summary()


def test_shape_corpus_holds_the_axioms():
    from src.shapes.checker import run_corpus
    from src.shapes.generator import load_palette
    run = run_corpus(load_palette(
        REPO / "data" / "shapes" / "palette_diabetes.json"))
    t = analyze(run.build.nodes_rows, run.build.edges_rows)
    assert t.ok, t.summary()
    # the shape palette deliberately includes codeset tables no
    # scenario reads end-to-end — legitimate foundation islands are
    # PERMITTED here; strays and orphans are not
    assert not t.stray_derived_components and not t.degree_zero


def test_summary_names_every_axiom_leg():
    s = Topology(node_count=1, edge_count=0, components=1).summary()
    for word in ("components", "dangling", "degree-0", "unmapped"):
        assert word in s
