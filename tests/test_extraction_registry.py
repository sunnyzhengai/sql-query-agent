"""EXTRACTION_REGISTRY meta-tests (spec:C1 — the completeness frontier).

The registry converts "did we think of it?" from an unbounded worry
into a one-page review. These tests keep it well-formed, pinned to the
code it cites, and permanently carrying the incident that motivated it.
"""

from pathlib import Path

from src.extraction_registry import EXTRACTION_REGISTRY
from src.schemas import TABLE_REGISTRY

REPO = Path(__file__).parent.parent

REFERENCES = {"D", "P", "M", "O", "Gov"}


def test_every_row_is_functor_xor_exclusion():
    """spec:C1 — (∃ F_k) ∨ (∃ exclusion(k)); no third state."""
    for kind, row in EXTRACTION_REGISTRY.items():
        assert row["reference"] in REFERENCES, kind
        if row["status"] == "extracted":
            assert row.get("extractor", {}).get("module"), kind
            assert row.get("targets"), kind
            assert row.get("conservation", {}).get("check"), (
                f"{kind}: an extractor without a conservation citation "
                f"is a silent-drop risk (spec:C2)")
            assert "exclusion_reason" not in row, kind
        elif row["status"] == "excluded":
            assert row.get("exclusion_reason", "").strip(), kind
            assert "extractor" not in row, kind
        else:
            raise AssertionError(f"{kind}: unknown status {row['status']}")


def test_extractor_modules_exist_on_disk():
    for kind, row in EXTRACTION_REGISTRY.items():
        if row["status"] != "extracted":
            continue
        module = row["extractor"]["module"]
        assert (REPO / module).exists(), (
            f"{kind} cites extractor module {module} which does not exist")


def test_conservation_citations_resolve():
    """Every cited test file exists; every cited ops/input table is a
    registered contract — a conservation claim must point at something
    real."""
    known_tables = set(TABLE_REGISTRY)
    for kind, row in EXTRACTION_REGISTRY.items():
        if row["status"] != "extracted":
            continue
        text = row["conservation"]["home"] + " " + row["conservation"]["check"]
        for token in text.replace(",", " ").replace("(", " ").split():
            if token.startswith("tests/"):
                assert (REPO / token.rstrip(";)")).exists(), (
                    f"{kind} cites missing test file {token}")
            if token.startswith(("ops_", "input_", "graph_", "gov_")):
                name = token.rstrip(";).")
                assert name in known_tables, (
                    f"{kind} cites unregistered table {name}")


def test_the_joins_incident_row_is_pinned():
    """THE acceptance test (spec:C1 origin): before 1.27.0 the vendor
    join map J_D had no functor and no exclusion — the missing-EMR-joins
    incident existed at the inventory level. This registry run against
    that state shows dictionary_joins as a missing row. The row may
    evolve (1b regenerates from decision sites) but may never vanish or
    regress to excluded."""
    row = EXTRACTION_REGISTRY.get("dictionary_joins")
    assert row is not None, "the incident row is gone — spec:C1 regression"
    assert row["status"] == "extracted"
    assert "joinable" in row["targets"]


def test_every_reference_structure_is_covered():
    """An entire reference class (D/P/M/O/Gov) silently vanishing from
    the inventory would be the incident at a larger grain."""
    covered = {row["reference"] for row in EXTRACTION_REGISTRY.values()}
    assert covered == REFERENCES, f"uncovered references: {REFERENCES - covered}"


def test_ruled_exclusions_present():
    """Sunny's 2026-08-19 ruling: Snowflake and Databricks/dbt are
    explicit exclusion rows — visible roadmap pressure, never silent
    scope."""
    for kind in ("snowflake_views", "databricks_dbt_models"):
        row = EXTRACTION_REGISTRY[kind]
        assert row["status"] == "excluded"
        assert "ADR 0001" in row["exclusion_reason"] or "native parser" \
            in row["exclusion_reason"] or "dialect law" in row["exclusion_reason"]
