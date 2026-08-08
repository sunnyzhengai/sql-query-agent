"""Tests for business-term candidate mining + Purview glossary push (ADR 0031)."""

import json

from scripts.seed_sample_data import (
    SAMPLE_DICT_COLUMNS,
    SAMPLE_DICT_TABLES,
    SAMPLE_SQL_SOURCES,
)
from src.adapters.purview import PurviewAdapter, PurviewConfig
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


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body)

    def json(self):
        return self._body


class TestGlossaryPush:
    def adapter(self):
        return PurviewAdapter(
            PurviewConfig(account_name="test"), access_token="fake-token"
        )

    def test_term_created_and_assigned_to_multiple_assets(self, monkeypatch):
        calls = []

        def fake_post(url, headers=None, json=None, timeout=None):
            calls.append(("POST", url, json))
            if url.endswith("/glossary/term"):
                return FakeResponse(200, {"guid": "term-1"})
            return FakeResponse(200, {})

        def fake_get(url, headers=None, params=None, timeout=None):
            qn = params["attr:qualifiedName"]
            if qn == "missing-asset":
                return FakeResponse(404, {})
            return FakeResponse(200, {"entity": {"guid": f"guid-{qn}"}})

        monkeypatch.setattr("requests.post", fake_post)
        monkeypatch.setattr("requests.get", fake_get)

        result = self.adapter().publish_glossary_term(
            glossary_guid="gl-1",
            name="Cancelled Appointment (scheduling)",
            definition="Appointments marked cancelled before start.",
            asset_qualified_names=["asset-a", "asset-b", "missing-asset"],
            status="certified",
            weight=214,
        )
        assert result.status.value == "success"
        assert "2 assets assigned" in result.message
        assert "1 not found" in result.message

        term_call = next(c for c in calls if c[1].endswith("/glossary/term"))
        assert term_call[2]["anchor"] == {"glossaryGuid": "gl-1"}
        assert "status: certified" in term_call[2]["longDescription"]
        assert "usage weight: 214" in term_call[2]["longDescription"]

        assign_call = next(c for c in calls if "assignedEntities" in c[1])
        assert assign_call[2] == [{"guid": "guid-asset-a"}, {"guid": "guid-asset-b"}]

    def test_siblings_cross_linked_via_see_also(self, monkeypatch):
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            if url.endswith("/glossary/term"):
                captured.update(json)
                return FakeResponse(200, {"guid": "term-2"})
            return FakeResponse(200, {})

        monkeypatch.setattr("requests.post", fake_post)
        result = self.adapter().publish_glossary_term(
            glossary_guid="gl-1", name="X (variant)", definition="d",
            asset_qualified_names=[], see_also_guids=["term-1"],
        )
        assert result.status.value == "success"
        assert captured["seeAlso"] == [{"termGuid": "term-1"}]

    def test_failed_term_create_reports(self, monkeypatch):
        monkeypatch.setattr(
            "requests.post",
            lambda url, **kw: FakeResponse(403, {"error": "forbidden"}),
        )
        result = self.adapter().publish_glossary_term(
            glossary_guid="gl-1", name="X", definition="d",
            asset_qualified_names=[],
        )
        assert result.status.value == "failed"
        assert "403" in result.message
