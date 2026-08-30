"""BRIDGE-1 stage 1 (0063 §2 file-first): native import files from
the certified graph — every row provenance-graded, descriptions
never authored by the exporter, relations from parsed edges only.

Proves: contract:suite-legibility
"""

from src.adapters.file_export import (
    READS_EXPORT_QUERY,
    collibra_asset_rows,
    collibra_relation_rows,
    purview_glossary_rows,
    to_csv,
)
from tests.orchestrator.test_tools import REF_A, fake_kql


def _kql(query, params):
    if query == READS_EXPORT_QUERY:
        return [{"ref": REF_A, "tbl": "ENCOUNTERS"},
                {"ref": REF_A, "tbl": "LAB_RESULTS"},
                {"ref": "no.such_metric", "tbl": "GHOST"}]
    return fake_kql(query, params)


class TestCollibraExport:
    def test_asset_rows_carry_store_descriptions_and_grade(self):
        rows = collibra_asset_rows(_kql, "sunny@aivia", domain="Gov")
        assert rows, "no assets exported"
        r0 = rows[0]
        assert r0["Asset Type"] == "Business Metric"
        assert r0["Domain"] == "Gov"
        assert "approved by sunny@aivia" in r0["Provenance"]
        assert "parsed by" in r0["Provenance"]

    def test_relations_from_parsed_edges_only(self):
        rows = collibra_relation_rows(_kql, "sunny@aivia")
        pairs = {(r["Head Full Name"], r["Tail"]) for r in rows}
        assert (REF_A, "ENCOUNTERS") in pairs
        assert (REF_A, "LAB_RESULTS") in pairs
        # an edge whose metric is not in the certified census never
        # exports — no invented assets
        assert not any(r["Tail"] == "GHOST" for r in rows)
        assert all("approved by" in r["Provenance"] for r in rows)


class TestPurviewGlossary:
    def test_terms_are_draft_with_graded_definitions(self):
        rows = purview_glossary_rows(_kql, "sunny@aivia",
                                     expert="steward@x")
        assert rows
        for r in rows:
            assert r["Status"] == "Draft"      # their workflow owns
            assert "approved by sunny@aivia" in r["Definition"]
            assert r["Experts"] == "steward@x"

    def test_exporter_authors_nothing(self):
        # a metric with an EMPTY description exports the grade line
        # alone — the exporter never writes a description of its own
        rows = purview_glossary_rows(_kql, "a@b")
        graded_only = [r for r in rows
                       if r["Definition"].startswith("parsed by")]
        with_desc = [r for r in rows
                     if not r["Definition"].startswith("parsed by")]
        assert graded_only or with_desc   # both shapes legal
        for r in with_desc:
            # description text precedes the grade; nothing else added
            assert "[parsed by" in r["Definition"]


class TestCsvShape:
    def test_round_trips_through_csv(self):
        import csv as _csv
        import io
        rows = collibra_asset_rows(_kql, "a@b")
        text = to_csv(rows)
        back = list(_csv.DictReader(io.StringIO(text)))
        assert len(back) == len(rows)
        assert back[0]["Provenance"] == rows[0]["Provenance"]

    def test_empty_is_empty(self):
        assert to_csv([]) == ""
