"""The diff kernel (family F — the founding question).

Acceptance corpus shaped like the 2026-08-17 field finding: same-name
proc pairs across schemas, most twins carrying DIFFERENT code — the
kernel must say WHERE they differ, deterministically, and the cached
twin summaries must surface it without a live comparison.
"""

from __future__ import annotations

from src.graph.decomposition_diff import (
    Decomposition,
    DecompStep,
    diff_decompositions,
    diff_many,
    twin_divergence_rows,
)


def _d(entity_id, *steps):
    return Decomposition(entity_id=entity_id, steps=list(steps))


class TestKernel:
    def test_identical_decompositions(self):
        a = _d("rpt.USP_Sepsis",
               DecompStep("screened", "SELECT * FROM ENC", frozenset({"ENC"})),
               DecompStep("flagged", "SELECT * FROM screened WHERE f=1"))
        b = _d("cook.USP_Sepsis",
               DecompStep("screened", "select *  from enc", frozenset({"ENC"})),
               DecompStep("flagged", "SELECT * FROM screened WHERE f=1"))
        r = diff_decompositions(a, b)
        assert r.identical  # whitespace/case forgiven, same as partition
        assert r.rows()[0]["verdict"] == "identical"

    def test_differing_filter_is_localized_to_its_step(self):
        """The founding shape: same steps, ONE filter differs — the
        kernel names the step and shows the fragment diff."""
        a = _d("rpt.USP_Sepsis",
               DecompStep("screened", "SELECT * FROM ENC WHERE age >= 18"),
               DecompStep("final", "SELECT COUNT(*) FROM screened"))
        b = _d("ed.USP_Sepsis",
               DecompStep("screened", "SELECT * FROM ENC WHERE age >= 16"),
               DecompStep("final", "SELECT COUNT(*) FROM screened"))
        r = diff_decompositions(a, b)
        assert not r.identical
        divergent = [p for p in r.aligned if p.divergent]
        assert len(divergent) == 1 and divergent[0].a_name == "screened"
        assert any("18" in ln for ln in divergent[0].fragment_diff)
        assert any("16" in ln for ln in divergent[0].fragment_diff)

    def test_missing_step_is_a_finding(self):
        a = _d("a.USP_X",
               DecompStep("base", "SELECT 1"),
               DecompStep("exclusions", "SELECT 2"))
        b = _d("b.USP_X", DecompStep("base", "SELECT 1"))
        r = diff_decompositions(a, b)
        assert r.only_in_a == ["exclusions"] and r.only_in_b == []
        assert not r.identical
        assert "only in a.USP_X: exclusions" in r.summary_line()

    def test_renamed_identical_step_matches_by_content(self):
        a = _d("a.USP_X", DecompStep("screened_pts", "SELECT * FROM ENC"))
        b = _d("b.USP_X", DecompStep("pt_screen", "SELECT * FROM ENC"))
        r = diff_decompositions(a, b)
        assert r.identical
        assert r.aligned[0].matched_by == "content"

    def test_rewritten_step_matches_by_tables(self):
        """Rewritten fragment, same sources: table-set similarity keeps
        the pair aligned so the diff shows the rewrite, not two losses."""
        a = _d("a.USP_X", DecompStep(
            "s1", "SELECT x FROM ENC JOIN DX ON 1=1",
            frozenset({"ENC", "DX"})))
        b = _d("b.USP_X", DecompStep(
            "step_one", "SELECT x, y FROM ENC INNER JOIN DX ON 1=1",
            frozenset({"ENC", "DX"})))
        r = diff_decompositions(a, b)
        assert r.only_in_a == [] and r.only_in_b == []
        assert r.aligned[0].matched_by == "tables"
        assert not r.aligned[0].fragment_identical

    def test_table_divergence_reported_per_step(self):
        a = _d("a.USP_X", DecompStep("s", "SELECT 1", frozenset({"ENC", "ADT"})))
        b = _d("b.USP_X", DecompStep("s", "SELECT 1", frozenset({"ENC"})))
        r = diff_decompositions(a, b)
        p = r.aligned[0]
        assert p.tables_only_in_a == ["ADT"] and p.tables_only_in_b == []
        assert not r.identical  # fragment equal, sources differ -> divergent

    def test_dissimilar_tables_stay_unmatched_not_guessed(self):
        a = _d("a.USP_X", DecompStep("s1", "SELECT 1", frozenset({"ENC"})))
        b = _d("b.USP_X", DecompStep("s2", "SELECT 2", frozenset({"MEDS"})))
        r = diff_decompositions(a, b)
        assert r.aligned == []
        assert r.only_in_a == ["s1"] and r.only_in_b == ["s2"]

    def test_n_way_is_pairwise_vs_explicit_base(self):
        base = _d("a.USP_X", DecompStep("s", "SELECT 1"))
        others = [_d("b.USP_X", DecompStep("s", "SELECT 1")),
                  _d("c.USP_X", DecompStep("s", "SELECT 9"))]
        results = diff_many([base] + others)
        assert [r.b_id for r in results] == ["b.USP_X", "c.USP_X"]
        assert results[0].identical and not results[1].identical

    def test_deterministic(self):
        a = _d("a.USP_X", DecompStep("p", "SELECT 1", frozenset({"T1", "T2"})),
               DecompStep("q", "SELECT 2", frozenset({"T3"})))
        b = _d("b.USP_X", DecompStep("q2", "SELECT 2x", frozenset({"T3"})),
               DecompStep("p2", "SELECT 1x", frozenset({"T1", "T2"})))
        r1, r2 = diff_decompositions(a, b), diff_decompositions(a, b)
        assert r1.rows() == r2.rows()


class TestTwinSummaries:
    """Doctrine level 3: cached kernel output for same-bare-name groups
    — built from graph rows exactly as 04 will call it."""

    def _graph(self):
        # two cross-schema twins: USP_Sepsis (DIFFERENT code — the 16/25
        # field shape) and USP_Falls (identical copies)
        def node(nid, layer, name, props=None):
            import json
            return {"node_id": nid, "layer": layer, "name": name,
                    "description": "", "properties": json.dumps(props or {})}

        def edge(s, t, et):
            return {"source_id": s, "target_id": t, "edge_type": et,
                    "properties": "{}"}

        nodes = [
            node("canonical:rpt.USP_Sepsis", "canonical", "USP_Sepsis"),
            node("canonical:ed.USP_Sepsis", "canonical", "USP_Sepsis"),
            node("canonical:rpt.USP_Falls", "canonical", "USP_Falls"),
            node("canonical:ed.USP_Falls", "canonical", "USP_Falls"),
            node("transform:rpt.USP_Sepsis/screened", "transformation",
                 "screened", {"sql_fragment": "SELECT * FROM ENC WHERE age >= 18"}),
            node("transform:ed.USP_Sepsis/screened", "transformation",
                 "screened", {"sql_fragment": "SELECT * FROM ENC WHERE age >= 16"}),
            node("transform:rpt.USP_Falls/base", "transformation",
                 "base", {"sql_fragment": "SELECT * FROM FALLS"}),
            node("transform:ed.USP_Falls/base", "transformation",
                 "base", {"sql_fragment": "SELECT * FROM FALLS"}),
            node("tech:ENC", "technical", "ENC", {"table": "ENC"}),
            node("tech:FALLS", "technical", "FALLS", {"table": "FALLS"}),
        ]
        edges = [
            edge("canonical:rpt.USP_Sepsis", "transform:rpt.USP_Sepsis/screened",
                 "canonical_to_transform"),
            edge("canonical:ed.USP_Sepsis", "transform:ed.USP_Sepsis/screened",
                 "canonical_to_transform"),
            edge("canonical:rpt.USP_Falls", "transform:rpt.USP_Falls/base",
                 "canonical_to_transform"),
            edge("canonical:ed.USP_Falls", "transform:ed.USP_Falls/base",
                 "canonical_to_transform"),
            edge("transform:rpt.USP_Sepsis/screened", "tech:ENC",
                 "transform_to_technical"),
            edge("transform:ed.USP_Sepsis/screened", "tech:ENC",
                 "transform_to_technical"),
            edge("transform:rpt.USP_Falls/base", "tech:FALLS",
                 "transform_to_technical"),
            edge("transform:ed.USP_Falls/base", "tech:FALLS",
                 "transform_to_technical"),
        ]
        return nodes, edges

    def test_twin_groups_get_cached_verdicts(self):
        nodes, edges = self._graph()
        rows = twin_divergence_rows(nodes, edges, run_at="t0")
        by_key = {r["group_key"]: r for r in rows}
        assert set(by_key) == {"usp_sepsis", "usp_falls"}
        assert by_key["usp_sepsis"]["verdict"] == "divergent"
        assert by_key["usp_sepsis"]["divergent_steps"] == 1
        assert by_key["usp_falls"]["verdict"] == "identical"
        assert "ed.USP_Sepsis" in by_key["usp_sepsis"]["metric_ids"]
        assert by_key["usp_sepsis"]["computed_at"] == "t0"

    def test_singletons_produce_no_rows(self):
        nodes, edges = self._graph()
        nodes = [n for n in nodes if "Falls" not in n["node_id"]
                 and "FALLS" not in n["node_id"]]
        rows = twin_divergence_rows(nodes, edges, run_at="t0")
        assert {r["group_key"] for r in rows} == {"usp_sepsis"}
