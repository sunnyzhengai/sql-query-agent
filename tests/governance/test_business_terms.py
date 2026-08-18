"""Tests for business-term candidate mining + Purview glossary push (ADR 0031)."""

import json

from scripts.seed_sample_data import (
    SAMPLE_DICT_COLUMNS,
    SAMPLE_DICT_TABLES,
    SAMPLE_SQL_SOURCES,
)
from src.governance.business_terms import (
    candidates_to_records,
    mine_term_candidates,
)
from src.parser.sql_parser import parse_sql
from src.schemas import BUSINESS_TERMS, TERM_LINKS
from src.steps.build_graph import build_graph_step
from src.steps.parse import parse_step


def step_row(metric_id, name, fragment, description=""):
    return {
        "node_id": f"transform:{metric_id}:{name}",
        "layer": "transformation",
        "name": name,
        "description": description,
        "properties": json.dumps({"metric_id": metric_id, "sql_fragment": fragment}),
    }


class TestMining:
    def test_same_name_same_logic_is_one_shared_candidate(self):
        rows = [
            step_row("a.M1", "CancelledAppts", "SELECT x FROM appts WHERE status='C'",
                     "Appointments marked cancelled."),
            step_row("b.M2", "CancelledAppts", "select  x from appts where status='C'"),
        ]
        cands = mine_term_candidates(rows)
        assert len(cands) == 1
        assert len(cands[0].links) == 2  # whitespace/case differences fold together
        assert cands[0].metric_ids == ["a.M1", "b.M2"]
        assert cands[0].definition == "Appointments marked cancelled."

    def test_same_name_different_logic_yields_sibling_variants(self):
        rows = [
            step_row("a.M1", "CancelledAppts", "SELECT x FROM appts WHERE status='C'"),
            step_row("b.M2", "CancelledAppts", "SELECT x FROM appts WHERE status IN ('C','N')"),
        ]
        cands = mine_term_candidates(rows)
        assert len(cands) == 2
        assert cands[0].concept_key == cands[1].concept_key
        assert cands[0].term_id != cands[1].term_id

    def test_single_metric_names_are_not_concepts(self):
        rows = [
            step_row("a.M1", "OnlyHere", "SELECT 1"),
            step_row("a.M1", "AlsoOnlyHere", "SELECT 2"),
        ]
        assert mine_term_candidates(rows) == []

    def test_noise_names_skipped(self):
        rows = [
            step_row("a.M1", "__final_select__", "SELECT 1"),
            step_row("b.M2", "__final_select__", "SELECT 1"),
            step_row("a.M1", "tmp", "SELECT 2"),
            step_row("b.M2", "tmp", "SELECT 2"),
        ]
        assert mine_term_candidates(rows) == []

    def test_runs_on_real_sample_graph(self):
        parse_out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
        g = build_graph_step(
            parse_out.parse_results, list(SAMPLE_DICT_TABLES), list(SAMPLE_DICT_COLUMNS)
        )
        cands = mine_term_candidates(g.nodes_rows)  # may be empty; must not crash
        for c in cands:
            assert c.term_id and c.concept_key and c.links

    def test_records_match_contracts(self):
        rows = [
            step_row("a.M1", "CancelledAppts", "SELECT 1"),
            step_row("b.M2", "CancelledAppts", "SELECT 1"),
        ]
        terms, links = candidates_to_records(
            mine_term_candidates(rows), mined_at="2026-08-08T00:00:00Z"
        )
        assert set(terms[0].keys()) == {c[0] for c in BUSINESS_TERMS["columns"]}
        assert set(links[0].keys()) == {c[0] for c in TERM_LINKS["columns"]}
        assert terms[0]["status"] == "emergent" and terms[0]["source"] == "mined"


# TestGlossaryPush removed 2026-08-18: the Purview glossary surface
# (ensure_glossary/publish_glossary_term) was deleted per the ghost rule
# — zero callers since it was built (HANDOFF_PURVIEW_GLOSSARY_PATH).
# Term MINING above stays: ADR 0031's plurality logic is live. When
# term-grain publishing lands (gov_business_terms contracts flip
# active), resurrect the surface from git history with the
# branding-from-config rule from the handoff.
