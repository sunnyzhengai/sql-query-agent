"""BRIDGE-1 stage 1 (0063 §2 file-first): native import files from
the certified graph — every row provenance-graded, descriptions
never authored by the exporter, relations from parsed edges only.
BR-1: colliding names qualify + disclose (duplicate-Name class
structurally dead). BR-2: stewardship pre-fills from the store.

Proves: contract:suite-legibility
"""

import pytest

from src.adapters.file_export import (
    METRIC_EXPORT_QUERY,
    READS_EXPORT_QUERY,
    ExportIntegrityError,
    assert_unique_names,
    collibra_asset_rows,
    collibra_relation_rows,
    purview_glossary_rows,
    to_csv,
)
from tests.orchestrator.test_tools import fake_kql

REF_A = "reporting.USP_ED_Sepsis"
REF_B = "reports.USP_ED_Sepsis"


def _kql(query, params):
    if query == METRIC_EXPORT_QUERY:
        return [
            {"metric_id": REF_A, "metric_name": "USP_ED_Sepsis",
             "business_name": "ED Sepsis Screening",
             "description": "Screens ED arrivals.",
             "steward": "steward@x", "developer": "dev@x"},
            {"metric_id": REF_B, "metric_name": "USP_ED_Sepsis",
             "business_name": "ED Sepsis Screening",
             "description": "Regulatory variant.",
             "steward": "", "developer": ""},
            {"metric_id": "reporting.USP_Unique",
             "metric_name": "USP_Unique",
             "business_name": "Unique Metric",
             "description": "", "steward": "s2@x",
             "developer": "d2@x"},
        ]
    if query == READS_EXPORT_QUERY:
        return [{"ref": REF_A, "tbl": "ENCOUNTERS"},
                {"ref": "no.such_metric", "tbl": "GHOST"}]
    return fake_kql(query, params)


class TestBR1NameCollisions:
    def test_colliding_names_qualify_and_disclose(self):
        rows = purview_glossary_rows(_kql, "sunny@aivia")
        names = [r["Name"] for r in rows]
        assert f"ED Sepsis Screening ({REF_A})" in names
        assert f"ED Sepsis Screening ({REF_B})" in names
        assert "Unique Metric" in names       # singles stay bare
        twin = next(r for r in rows if REF_A in r["Name"])
        assert "2 definitions share the name" in twin["Definition"]
        assert "unresolved" in twin["Definition"]

    def test_no_duplicate_name_in_any_export(self):
        for rows in (collibra_asset_rows(_kql, "a@b"),
                     purview_glossary_rows(_kql, "a@b")):
            names = [r["Name"] for r in rows]
            assert len(names) == len(set(names))

    def test_integrity_gate_raises_on_residual_dupes(self):
        with pytest.raises(ExportIntegrityError, match="duplicate"):
            assert_unique_names([{"Name": "X"}, {"Name": "X"}],
                                "test")

    def test_relations_use_the_qualified_head(self):
        rows = collibra_relation_rows(_kql, "a@b")
        head = next(r for r in rows if r["Head Full Name"] == REF_A)
        assert head["Head"] == f"ED Sepsis Screening ({REF_A})"
        assert not any(r["Tail"] == "GHOST" for r in rows)


class TestBR2Stewardship:
    def test_stewards_and_experts_prefill_from_the_store(self):
        rows = purview_glossary_rows(_kql, "a@b",
                                     expert="fallback@x")
        by_ref = {r["Name"]: r for r in rows}
        a = by_ref[f"ED Sepsis Screening ({REF_A})"]
        assert a["Stewards"] == "steward@x"
        assert a["Experts"] == "dev@x"
        # storeless row falls back to the engagement arg
        b = by_ref[f"ED Sepsis Screening ({REF_B})"]
        assert b["Stewards"] == "fallback@x"

    def test_collibra_assets_carry_stewards(self):
        rows = collibra_asset_rows(_kql, "a@b")
        assert any(r["Stewards"] == "steward@x" for r in rows)


class TestGradesAndShape:
    def test_every_row_graded_and_draft(self):
        for r in purview_glossary_rows(_kql, "sunny@aivia"):
            assert r["Status"] == "Draft"
            assert "approved by sunny@aivia" in r["Definition"]
        for r in collibra_asset_rows(_kql, "sunny@aivia"):
            assert "approved by sunny@aivia" in r["Provenance"]

    def test_round_trips_through_csv(self):
        import csv as _csv
        import io
        rows = collibra_asset_rows(_kql, "a@b")
        back = list(_csv.DictReader(io.StringIO(to_csv(rows))))
        assert len(back) == len(rows)

    def test_empty_is_empty(self):
        assert to_csv([]) == ""
