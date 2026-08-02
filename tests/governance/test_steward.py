"""Tests for steward assignment management (gov_steward_assignments writer logic)."""

from src.governance.steward import StewardManager
from src.graph.builder import GraphBuilder
from src.schemas import STEWARD_ASSIGNMENTS

METRICS = [
    {"metric_id": "reporting.USP_ED_CENSUS", "name": "USP_ED_CENSUS"},
    {"metric_id": "reporting.USP_OR_CENSUS", "name": "USP_OR_CENSUS"},
    {"metric_id": "reporting.USP_READMIT", "name": "USP_READMIT"},
]


def test_assign_and_roundtrip_through_records():
    manager = StewardManager()
    manager.assign("m1", "Metric One", "Dr. Smith", steward_email="s@org.com")

    reloaded = StewardManager()
    reloaded.load_from_records(manager.to_records())
    assert reloaded.assignments["m1"].steward_name == "Dr. Smith"
    assert reloaded.assignments["m1"].steward_email == "s@org.com"


def test_assign_by_pattern_is_case_insensitive():
    manager = StewardManager()
    results = manager.assign_by_pattern("CENSUS", "Dr. Smith", METRICS)
    assert {r.metric_id for r in results} == {
        "reporting.USP_ED_CENSUS", "reporting.USP_OR_CENSUS",
    }


def test_get_unassigned():
    manager = StewardManager()
    manager.assign_by_pattern("census", "Dr. Smith", METRICS)
    unassigned = manager.get_unassigned([m["metric_id"] for m in METRICS])
    assert unassigned == ["reporting.USP_READMIT"]


def test_apply_to_graph_sets_canonical_properties_only():
    builder = GraphBuilder()
    builder.add_canonical_node("reporting.USP_ED_CENSUS", "USP_ED_CENSUS")
    builder.add_technical_node("encounter")

    manager = StewardManager()
    manager.assign(
        "reporting.USP_ED_CENSUS", "USP_ED_CENSUS", "Dr. Smith",
        department="Emergency",
    )
    updated = manager.apply_to_graph(builder)

    assert updated == 1
    canonical = builder.nodes["canonical:reporting.USP_ED_CENSUS"]
    assert canonical.properties["steward"] == "Dr. Smith"
    assert canonical.properties["department"] == "Emergency"


def test_records_match_the_gov_steward_assignments_contract():
    """Module output must align with the STEWARD_ASSIGNMENTS data contract."""
    manager = StewardManager()
    manager.assign("m1", "Metric One", "Dr. Smith")
    record_keys = set(manager.to_records()[0])
    contract_columns = {c[0] for c in STEWARD_ASSIGNMENTS["columns"]}
    assert record_keys == contract_columns
