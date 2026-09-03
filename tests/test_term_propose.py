"""TERM-PROPOSE-1/2 — the answer key, authored BEFORE the module
existed (2026-09-04 overnight orders item 4; the corpus answer-key
law applied to a new component).

TERM-PROPOSE-1 (landing_registry `organize_hierarchy`, A2+A3): a
name-family cluster becomes one PARENT CONCEPT term (no proc behind
it) plus N child terms with DISTINCT names and definitions. Naming
is deterministic: parent = the family's shared identity; child =
identity qualified by its ref (the BR-1 mechanism — the family's
whole point is that the bare names collide).

TERM-PROPOSE-2: the proposal payload is assets + relationships
(term<->proc `governs`, term<->report, steward responsibility per
child, parent-child hierarchy) with the attribution prefix
("{product} agent generated: ") and ZERO custom attributes — the
allowed column sets are data, and every rendered row is checked
against them (the zero-schema-footprint ruling, 2026-08-31).

Proves: contract:suite-legibility
"""

from __future__ import annotations

import pytest

from src.branding import product_name
from src.term_propose import (
    COLLIBRA_ASSET_COLUMNS,
    COLLIBRA_RELATION_COLUMNS,
    PURVIEW_TERM_COLUMNS,
    attribution_prefix,
    hierarchy_collibra_asset_rows,
    hierarchy_collibra_relation_rows,
    hierarchy_purview_rows,
    propose_hierarchy,
)

CLUSTER = {
    "id": "cluster:c-042",
    "identity": "Active Diabetics",
    "flag_class": "cousin_conflict",
    "disposition": "open",
    "member_ids": ["canonical:USP_Active_Diabetics",
                   "canonical:USP_Active_Diabetics_v2"],
}

METRICS = {
    "USP_Active_Diabetics": {
        "metric_id": "USP_Active_Diabetics",
        "business_name": "Active Diabetics",
        "description": "Patients with a diabetes diagnosis and an "
                       "encounter in the last year.",
        "steward": "s.chen", "developer": "dev.a",
    },
    "USP_Active_Diabetics_v2": {
        "metric_id": "USP_Active_Diabetics_v2",
        "business_name": "Active Diabetics",
        "description": "Patients with an active diabetes problem-"
                       "list entry.",
        "steward": "m.okafor", "developer": "dev.b",
    },
}

REPORTS = {"USP_Active_Diabetics": ["Diabetes Registry Dashboard"]}


def _payload():
    return propose_hierarchy(CLUSTER, METRICS, REPORTS)


class TestProposeHierarchyAnswers:
    """TERM-PROPOSE-1: the authored payload for the family above."""

    def test_parent_is_the_concept_with_no_proc(self):
        p = _payload()
        assert p["parent"]["name"] == "Active Diabetics"
        assert p["parent"].get("ref") is None, (
            "the parent concept has no proc behind it (registry row)")

    def test_children_have_distinct_qualified_names(self):
        p = _payload()
        names = [c["name"] for c in p["children"]]
        assert names == [
            "Active Diabetics (USP_Active_Diabetics)",
            "Active Diabetics (USP_Active_Diabetics_v2)"]
        assert len(set(names)) == len(names)

    def test_definitions_carry_the_attribution_prefix(self):
        p = _payload()
        prefix = attribution_prefix()
        assert prefix == f"{product_name()} agent generated: "
        assert p["parent"]["definition"].startswith(prefix)
        for c in p["children"]:
            assert c["definition"].startswith(prefix)

    def test_child_definition_is_disclosure_plus_certified_text(self):
        p = _payload()
        d0 = p["children"][0]["definition"]
        assert "One of 2 distinct definitions sharing the name "  \
               "'Active Diabetics'." in d0
        assert ("Patients with a diabetes diagnosis and an "
                "encounter in the last year.") in d0

    def test_parent_definition_counts_its_own_children(self):
        p = _payload()
        assert "2 distinct definitions" in p["parent"]["definition"]

    def test_stewards_ride_per_child(self):
        p = _payload()
        assert [c["steward"] for c in p["children"]] == [
            "s.chen", "m.okafor"]

    def test_relationships_are_the_registry_row(self):
        """parent-child hierarchy + child governs proc + child ->
        report (term assignment) — nothing else, nothing custom."""
        p = _payload()
        kinds = sorted({r["kind"] for r in p["relationships"]})
        assert kinds == ["governs", "parent_child", "report"]
        governs = [r for r in p["relationships"]
                   if r["kind"] == "governs"]
        assert [(r["term"], r["asset"]) for r in governs] == [
            ("Active Diabetics (USP_Active_Diabetics)",
             "USP_Active_Diabetics"),
            ("Active Diabetics (USP_Active_Diabetics_v2)",
             "USP_Active_Diabetics_v2")]
        rep = [r for r in p["relationships"] if r["kind"] == "report"]
        assert [(r["term"], r["asset"]) for r in rep] == [
            ("Active Diabetics (USP_Active_Diabetics)",
             "Diabetes Registry Dashboard")]

    def test_distinct_business_name_stays_bare(self):
        """A member that already carries its own distinct name keeps
        it — qualification is only for names that collide with a
        sibling or the parent concept."""
        metrics = {k: dict(v) for k, v in METRICS.items()}
        metrics["USP_Active_Diabetics_v2"]["business_name"] = (
            "Active Diabetics (Problem List)")
        p = propose_hierarchy(CLUSTER, metrics, REPORTS)
        assert [c["name"] for c in p["children"]] == [
            "Active Diabetics (USP_Active_Diabetics)",
            "Active Diabetics (Problem List)"]

    def test_missing_description_stays_honest(self):
        """A child with no certified description ships the disclosure
        sentence alone — never invented text."""
        metrics = {k: dict(v) for k, v in METRICS.items()}
        metrics["USP_Active_Diabetics_v2"]["description"] = ""
        p = propose_hierarchy(CLUSTER, metrics, REPORTS)
        d1 = p["children"][1]["definition"]
        assert d1.endswith("'Active Diabetics'.")
        assert "None" not in d1


class TestRenderedRowsAnswers:
    """TERM-PROPOSE-2: the payload rendered to the stage-1 native
    file shapes — zero custom attributes, checked as data."""

    def test_purview_rows_use_parent_term_name(self):
        rows = hierarchy_purview_rows([_payload()])
        assert rows[0]["Name"] == "Active Diabetics"
        assert rows[0]["Parent Term Name"] == ""
        kids = rows[1:]
        assert all(r["Parent Term Name"] == "Active Diabetics"
                   for r in kids)
        assert all(r["Status"] == "Draft" for r in rows), (
            "their workflow owns promotion — Draft always")

    def test_purview_columns_are_the_native_set_only(self):
        for row in hierarchy_purview_rows([_payload()]):
            assert tuple(row.keys()) == PURVIEW_TERM_COLUMNS

    def test_collibra_asset_columns_are_native_only(self):
        rows = hierarchy_collibra_asset_rows([_payload()])
        assert [r["Name"] for r in rows] == [
            "Active Diabetics",
            "Active Diabetics (USP_Active_Diabetics)",
            "Active Diabetics (USP_Active_Diabetics_v2)"]
        for row in rows:
            assert tuple(row.keys()) == COLLIBRA_ASSET_COLUMNS
        assert "Provenance" not in COLLIBRA_ASSET_COLUMNS, (
            "attribution is the definition PREFIX, never a column "
            "that would become a custom attribute (zero schema "
            "footprint)")

    def test_collibra_relations_cover_the_registry_row(self):
        rows = hierarchy_collibra_relation_rows([_payload()])
        rels = sorted({r["Relation"] for r in rows})
        assert rels == ["governs", "hierarchical", "responsible"]
        for row in rows:
            assert tuple(row.keys()) == COLLIBRA_RELATION_COLUMNS

    def test_duplicate_names_across_clusters_refuse_to_render(self):
        """assert_unique_names (BR-1) guards this surface too — two
        clusters yielding the same term name is an integrity error,
        never a silent overwrite in the customer's catalog."""
        from src.adapters.file_export import ExportIntegrityError
        with pytest.raises(ExportIntegrityError):
            hierarchy_purview_rows([_payload(), _payload()])


class TestStoreDrivenLeg:
    """term_hierarchy_payloads over the shared fake store: OPEN
    conflict-class METRIC-grain flags only (a step-grain misnomer is
    console rename work, not a glossary hierarchy), members joined
    to their certified metric rows and report edges."""

    @staticmethod
    def _kql(query, params):
        from src.orchestrator.tools import GOV_FLAG_MEMBER_NAMES_QUERY
        from src.term_propose import REPORTS_EXPORT_QUERY
        from tests.adapters.test_file_export import REF_A, REF_B
        from tests.adapters.test_file_export import _kql as bridge_kql
        if query == GOV_FLAG_MEMBER_NAMES_QUERY:
            return [
                {"cluster": "cluster:cousin_conflict:metric:"
                            "ccc333ddd444",
                 "member_ids": [f"canonical:{REF_A}",
                                f"canonical:{REF_B}"],
                 "member_names": ["ED Sepsis Screening",
                                  "ED Sepsis (Regulatory)"]},
            ]
        if query == REPORTS_EXPORT_QUERY:
            return [{"ref": REF_A, "report": "Sepsis Dashboard"}]
        return bridge_kql(query, params)

    def test_only_the_metric_family_becomes_a_hierarchy(self):
        from src.term_propose import term_hierarchy_payloads
        from tests.adapters.test_file_export import REF_A
        payloads = term_hierarchy_payloads(self._kql)
        assert len(payloads) == 1, (
            "the step-grain misnomer flag must not become a term "
            "hierarchy")
        from tests.adapters.test_file_export import REF_B
        p = payloads[0]
        assert p["parent"]["name"] == "ED Sepsis Screening"
        # both members carry the SAME business name on the metric
        # surface (the store truth this leg reads), so both qualify
        assert [c["name"] for c in p["children"]] == [
            f"ED Sepsis Screening ({REF_A})",
            f"ED Sepsis Screening ({REF_B})"]
        assert "Screens ED arrivals." in p["children"][0]["definition"]
        rep = [r for r in p["relationships"] if r["kind"] == "report"]
        assert [(r["term"], r["asset"]) for r in rep] == [
            (f"ED Sepsis Screening ({REF_A})", "Sepsis Dashboard")]
