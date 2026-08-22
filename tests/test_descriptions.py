"""Tests for bottom-up description generation (ADR 0019) — no LLM, fake callback."""

from scripts.seed_sample_data import (
    SAMPLE_DICT_COLUMNS,
    SAMPLE_DICT_TABLES,
    SAMPLE_SQL_SOURCES,
)
from src.descriptions import (
    build_metric_prompt,
    generate_descriptions,
    step_content_hash,
    topological_step_order,
)
from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.models import EdgeType, NodeLayer
from src.parser.sql_parser import parse_sql
from src.steps.build_graph import build_graph_step
from src.steps.parse import parse_step
from src.tree.translate import build_fact_prompt


def _graph():
    parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
    return build_graph_step(
        parse_out.parse_results, list(SAMPLE_DICT_TABLES), list(SAMPLE_DICT_COLUMNS)
    )


def fake_describe(prompt: str) -> str:
    # Distinct per prompt but GROUNDED: the gate drops any >=2-digit
    # literal absent from the fragment, so the fake varies by letters.
    # Phase 2 (clauses 2+5): step responses are LEDGER-shaped — one
    # numbered line per fact ("N| ...") — so every fact counts as voiced
    # and no template-floor identifiers leak into observer tests.
    tag = "".join(chr(ord("a") + int(d)) for d in str(hash(prompt) % 10_000))
    intro = f"produces the {tag} result set"
    # single-digit line numbers only: 2-digit numbers in unmatched lines
    # would (correctly) trip the metric path's grounding gate
    return "\n".join([intro] + [f"{i}| applies the {tag} rule" for i in range(1, 10)])


class TestTopologicalOrder:
    def test_dependencies_come_before_dependents(self):
        g = _graph()
        nodes = rows_to_nodes(g.nodes_rows)
        edges = rows_to_edges(g.edges_rows)
        order = topological_step_order(nodes, edges)
        position = {nid: i for i, nid in enumerate(order)}
        for e in edges:
            if e.edge_type == EdgeType.TRANSFORM_TO_TRANSFORM:
                assert position[e.target_id] < position[e.source_id], (
                    f"dependency {e.target_id} must be described before {e.source_id}"
                )

    def test_every_transformation_is_ordered_exactly_once(self):
        g = _graph()
        nodes = rows_to_nodes(g.nodes_rows)
        order = topological_step_order(nodes, rows_to_edges(g.edges_rows))
        transforms = {n for n, node in nodes.items() if node.layer == NodeLayer.TRANSFORMATION}
        assert set(order) == transforms
        assert len(order) == len(transforms)


class TestGeneration:
    def test_every_step_and_metric_gets_a_description(self):
        g = _graph()
        result = generate_descriptions(g.nodes_rows, g.edges_rows, fake_describe)
        nodes = rows_to_nodes(g.nodes_rows)
        transforms = [n for n, x in nodes.items() if x.layer == NodeLayer.TRANSFORMATION]
        metrics = [n for n, x in nodes.items() if x.layer == NodeLayer.CANONICAL]
        for nid in transforms + metrics:
            assert nid in result.descriptions, f"{nid} missing description"
        assert not result.failed

    def test_cache_prevents_regeneration(self):
        g = _graph()
        cache: dict = {}
        first = generate_descriptions(g.nodes_rows, g.edges_rows, fake_describe, cache=cache)
        assert first.generated > 0 and first.cache_hits == 0

        calls = []
        def counting(prompt):
            calls.append(prompt)
            return "regenerated"
        second = generate_descriptions(g.nodes_rows, g.edges_rows, counting, cache=cache)
        # steps AND metric compositions come from the cache — reruns
        # with unchanged inputs and prompts cost zero LLM calls
        assert second.cache_hits == first.generated
        assert len(calls) == 0

    def test_changed_fragment_changes_hash(self):
        assert step_content_hash("SELECT 1", ["a"]) != step_content_hash("SELECT 2", ["a"])
        assert step_content_hash("SELECT 1", ["a"]) != step_content_hash("SELECT 1", ["b"])
        assert step_content_hash("SELECT 1", ["b", "a"]) == step_content_hash("SELECT 1", ["a", "b"])

    def test_prompt_version_is_part_of_every_cache_key(self):
        """Live find 2026-08-13: vague descriptions survived a rerun
        because the cache key knew only the SQL, not the prompt that
        read it. The version constant must appear in both hashes."""
        import src.descriptions as d
        h_step = step_content_hash("SELECT 1", ["a"])
        h_metric = d.metric_content_hash("USP_X", [("Final", "cohort")], 3)
        original = d.PROMPT_VERSION
        try:
            d.PROMPT_VERSION = original + "-next"
            assert step_content_hash("SELECT 1", ["a"]) != h_step
            assert d.metric_content_hash(
                "USP_X", [("Final", "cohort")], 3) != h_metric
        finally:
            d.PROMPT_VERSION = original

    def test_existing_node_descriptions_do_not_block_regeneration(self):
        """The cache is the ONLY skip authority — a prompt upgrade must
        reach nodes that already carry text from the old prompt."""
        g = _graph()
        rows = [dict(r) for r in g.nodes_rows]
        for r in rows:
            r["description"] = "already certified"
        result = generate_descriptions(rows, g.edges_rows, fake_describe)
        assert result.generated > 0

    def test_vague_fillers_are_flagged_not_retried(self):
        g = _graph()
        result = generate_descriptions(
            g.nodes_rows, g.edges_rows,
            lambda p: "Filtered by specific departments.")
        assert result.vague              # every node flagged
        assert set(result.vague) <= set(result.descriptions)  # still kept

    def test_raw_identifiers_are_flagged(self):
        """Live find 2026-08-14: ADT_DEPARTMENT_ID / #SDX /
        `pd.PatEncCSNID` all over the customer-facing workbench."""
        g = _graph()
        result = generate_descriptions(
            g.nodes_rows, g.edges_rows,
            lambda p: "Joins on ADT_DEPARTMENT_ID from #SDX.")
        assert result.jargon
        # a CLEAN fake must voice every fact (ledger-shaped) — otherwise
        # the template floor honestly prints raw identifiers, which is
        # the floor working, not a jargon regression
        clean_lines = ["Includes emergency department stays."] + [
            f"{i}| includes emergency department stays over 6 hours"
            for i in range(1, 10)]
        clean = generate_descriptions(
            g.nodes_rows, g.edges_rows, lambda p: "\n".join(clean_lines))
        assert not clean.jargon

    def test_step_prompt_carries_the_data_dictionary(self):
        """The graph's own dictionary is the translation material —
        the model is never asked to invent business meanings."""
        g = _graph()
        prompts = []

        def capture(p):
            prompts.append(p)
            return "ok"
        generate_descriptions(g.nodes_rows, g.edges_rows, capture)
        step_prompts = [p for p in prompts if "calculation step" in p]
        assert any("Data dictionary" in p for p in step_prompts), (
            "no step prompt carried dictionary lines — check "
            "TRANSFORM_TO_TECHNICAL wiring")

    def test_dictionary_changes_regenerate(self):
        assert step_content_hash("SELECT 1", ["a"], ["- T: patients"]) \
            != step_content_hash("SELECT 1", ["a"], ["- T: encounters"])

    def test_one_bad_step_does_not_kill_the_batch(self):
        g = _graph()
        flaky = {"n": 0}
        def sometimes(prompt):
            flaky["n"] += 1
            if flaky["n"] == 1:
                raise RuntimeError("transient")
            return "ok"
        result = generate_descriptions(g.nodes_rows, g.edges_rows, sometimes)
        assert len(result.failed) == 1
        assert result.generated > 0
        # the WHY is captured, not just the fact (field find 2026-08-20)
        nid, reason = result.failed_reasons[0]
        assert nid == result.failed[0]
        assert reason.startswith("generation_error: RuntimeError: transient")


class TestPrompts:
    def test_step_prompt_is_fact_shaped_and_carries_deps(self):
        """Phase 2 (clause 2): the step prompt carries typed FACTS and
        dependency context — there is no parameter through which a SQL
        statement could arrive (contract-tested in test_tree_contract)."""
        facts = [{"node_id": "site0.0", "kind": "predicate", "op": "BETWEEN",
                  "context": "where", "column": "ADT_ARRIVAL_DATE",
                  "columns": ["ADT_ARRIVAL_DATE"],
                  "operands": ["@s", "@e"],
                  "expression_sql": "ADT_ARRIVAL_DATE BETWEEN @s AND @e",
                  "must_voice": True}]
        p = build_fact_prompt("EligibleEncounters", facts,
                              deps=[("Base", "base pop")])
        assert "1| context=where op=BETWEEN" in p
        assert "Base: base pop" in p
        assert "SELECT" not in p

    def test_metric_prompt_uses_root_descriptions_not_sql(self):
        p = build_metric_prompt("USP_X", [("FinalData", "assembles the cohort")], 42)
        assert "assembles the cohort" in p
        assert "42" in p
        assert "SELECT" not in p

    def test_metric_prompt_bans_invented_purpose(self):
        p = build_metric_prompt("USP_X", [("FinalData", "assembles the cohort")], 42)
        assert "grounded ONLY in the step descriptions" in p
        assert "unless a step description states them" in p


class TestMeasureDescriptions:
    """DAX measures get the same walk treatment as SQL steps (ADR 0040)."""

    def _rows(self):
        import json
        nodes = [
            {"node_id": "measure:R:T[Rate]", "layer": "measure", "name": "Rate",
             "description": "", "properties": json.dumps({
                 "dax_expression": "DIVIDE(SUM(T[num]), SUM(T[den]))",
                 "expression_type": "measure", "report_name": "R",
                 "pbi_table": "T"})},
            {"node_id": "tech:DBO.V.NUM", "layer": "technical", "name": "num",
             "description": "Numerator: compliant encounters",
             "properties": json.dumps({"table": "V", "schema": "DBO",
                                       "column": "num"})},
        ]
        edges = [
            {"source_id": "measure:R:T[Rate]", "target_id": "tech:DBO.V.NUM",
             "edge_type": "measure_to_column", "properties": "{}"},
        ]
        return nodes, edges

    def test_measure_described_with_column_dictionary(self):
        from src.descriptions import generate_descriptions
        nodes, edges = self._rows()
        prompts = []

        def fake(prompt):
            prompts.append(prompt)
            return "Share of compliant encounters."

        result = generate_descriptions(nodes, edges, fake)
        assert result.descriptions["measure:R:T[Rate]"] == \
            "Share of compliant encounters."
        assert "DIVIDE" in prompts[0]
        assert "Numerator: compliant encounters" in prompts[0]

    def test_measure_cache_hit_on_rerun(self):
        from src.descriptions import generate_descriptions
        nodes, edges = self._rows()
        cache = {}
        generate_descriptions(nodes, edges, lambda p: "Text.", cache=cache)
        rerun = generate_descriptions(
            nodes, edges, lambda p: (_ for _ in ()).throw(AssertionError()),
            cache=cache)
        assert rerun.cache_hits >= 1 and rerun.generated == 0

    def test_measure_without_expression_fails_loudly(self):
        import json

        from src.descriptions import generate_descriptions
        nodes = [{"node_id": "measure:R:T[X]", "layer": "measure", "name": "X",
                  "description": "", "properties": json.dumps({})}]
        result = generate_descriptions(nodes, [], lambda p: "t")
        assert "measure:R:T[X]" in result.failed
        assert dict(result.failed_reasons)["measure:R:T[X]"].startswith(
            "no_dax_expression")


class TestMetricScopeRule:
    """Walk corpse (Sunny, 2026-08-21 evening, find 2): metric
    descriptions claimed 'without applying any filtering decisions' on
    metrics carrying hundreds of decision sites — the final_select's
    true no-WHERE fact over-scoped to the whole metric, and the engine
    faithfully repeated the poisoned text."""

    CORPSE = ("This metric reports severe sepsis incidence.\n"
              "Business logic:\n"
              "- The outcome is calculated by aggregating data from "
              "122 calculation steps without applying any filtering "
              "decisions.")

    def test_corpse_is_a_violation_when_sites_exist(self):
        from src.descriptions import metric_scope_violations
        out = metric_scope_violations(self.CORPSE, 427)
        assert out and "427 decision sites" in out[0]

    def test_no_sites_means_absence_claims_are_legal(self):
        from src.descriptions import metric_scope_violations
        assert metric_scope_violations(self.CORPSE, 0) == []

    def test_variant_phrasings_are_caught(self):
        from src.descriptions import metric_scope_violations
        for line in ("No filtering criteria are applied to the data.",
                     "The data is not filtered at this stage.",
                     "Without any filters, all rows are included."):
            assert metric_scope_violations(line, 5), line

    def test_prompt_carries_the_decision_count(self):
        from src.descriptions import build_metric_prompt
        p = build_metric_prompt("M", [("s", "d")], 122, 427)
        assert "427" in p and "decision site" in p

    def test_hash_regenerates_when_count_changes(self):
        from src.descriptions import metric_content_hash
        a = metric_content_hash("M", [("s", "d")], 122, 0)
        b = metric_content_hash("M", [("s", "d")], 122, 427)
        assert a != b
