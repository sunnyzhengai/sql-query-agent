"""Tests for pipeline validation — including the step-6 regression
(2026-08-13): step 6 must be a REAL traversal, not a 2-hop peek.

Found by the admin dashboard's first render: three healthy metrics
false-negatived because their entry transform assembles from temp
tables (zero DIRECT table edges) while the full chain reaches many.
ADR 0018's shallow-traversal disease, second location.
"""

from src.governance.validation import (
    summarize_validation,
    validate_pipeline_per_metric,
)


def edge(src, tgt, etype):
    return {"source_id": src, "target_id": tgt, "edge_type": etype}


def build(edges):
    by_source = {}
    for e in edges:
        by_source.setdefault(e["source_id"], []).append(e)
    return by_source


def run_one(mid, nodes, edges):
    return validate_pipeline_per_metric(
        [mid], {mid}, {n: {} for n in nodes}, build(edges))[0]


class TestStep6RealTraversal:
    def test_deep_chain_reaches_tables(self):
        # canonical -> Final (temp-only) -> Base_Pop -> TABLE
        # the 2026-08-13 regression case: zero direct tech edges on entry
        mid = "reports.USP_NonSevere_Sepsis"
        nodes = [f"canonical:{mid}", f"transform:{mid}:Final",
                 f"transform:{mid}:Base_Pop", "technical:EMRDB.T"]
        edges = [
            edge(f"canonical:{mid}", f"transform:{mid}:Final",
                 "canonical_to_transform"),
            edge(f"transform:{mid}:Final", f"transform:{mid}:Base_Pop",
                 "transform_to_transform"),
            edge(f"transform:{mid}:Base_Pop", "technical:EMRDB.T",
                 "transform_to_technical"),
        ]
        r = run_one(mid, nodes, edges)
        assert r["step6_traversal"] is True
        assert r["tech_reachable"] == 1

    def test_direct_table_still_passes(self):
        mid = "m.Direct"
        edges = [
            edge(f"canonical:{mid}", f"transform:{mid}:S",
                 "canonical_to_transform"),
            edge(f"transform:{mid}:S", "technical:T",
                 "transform_to_technical"),
        ]
        r = run_one(mid, [f"canonical:{mid}", f"transform:{mid}:S"], edges)
        assert r["step6_traversal"] is True

    def test_no_tables_anywhere_fails_honestly(self):
        mid = "m.Island"
        edges = [
            edge(f"canonical:{mid}", f"transform:{mid}:A",
                 "canonical_to_transform"),
            edge(f"transform:{mid}:A", f"transform:{mid}:B",
                 "transform_to_transform"),
        ]
        r = run_one(mid, [f"canonical:{mid}", f"transform:{mid}:A",
                          f"transform:{mid}:B"], edges)
        assert r["step6_traversal"] is False
        assert r["tech_reachable"] == 0

    def test_cycle_terminates(self):
        mid = "m.Cycle"
        edges = [
            edge(f"canonical:{mid}", f"transform:{mid}:A",
                 "canonical_to_transform"),
            edge(f"transform:{mid}:A", f"transform:{mid}:B",
                 "transform_to_transform"),
            edge(f"transform:{mid}:B", f"transform:{mid}:A",
                 "transform_to_transform"),
            edge(f"transform:{mid}:B", "technical:T",
                 "transform_to_technical"),
        ]
        r = run_one(mid, [f"canonical:{mid}"], edges)
        assert r["step6_traversal"] is True   # and we returned at all

    def test_earlier_steps_unchanged(self):
        mid = "m.NoParse"
        r = validate_pipeline_per_metric([mid], set(), {}, {})[0]
        assert r["step2_parsed"] is False
        assert r["step3_canonical"] is False
        assert r["step6_traversal"] is False


class TestSummary:
    def test_summary_counts(self):
        mid = "m.OK"
        edges = [
            edge(f"canonical:{mid}", f"transform:{mid}:S",
                 "canonical_to_transform"),
            edge(f"transform:{mid}:S", "technical:T",
                 "transform_to_technical"),
        ]
        results = validate_pipeline_per_metric(
            [mid], {mid},
            {f"canonical:{mid}": {}, f"transform:{mid}:S": {}},
            build(edges))
        s = summarize_validation(results)
        assert s["s6_traversal"] == 1
