"""Slice 1: the append-only substrate — LC-F2/F3 as structure.

The store has no update and no delete: supersede appends + retires,
retire marks, read declares. These tests pin the shape before
kg1_intake exists (protocol step 4 ordering).

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql.graph.store import Store


def _store_with_one():
    s = Store()
    s.append_node("table", "simemr|dbo|T1", {"description": "d"},
                  as_of="2026-08-01", extract_id="x1")
    return s


def test_append_and_read_current():
    s = _store_with_one()
    versions, complete = s.read("simemr|dbo|T1")
    assert complete == "current"
    assert len(versions) == 1
    assert versions[0].properties["description"] == "d"


def test_no_update_and_no_delete_paths_exist():
    banned = [name for name in dir(Store)
              if "update" in name.lower() or "delete" in name.lower()]
    assert banned == [], f"LC-F2/F3 violated: {banned}"


def test_supersede_appends_and_retires_never_mutates():
    s = _store_with_one()
    s.append_node("table", "simemr|dbo|T1", {"description": "d2"},
                  as_of="2026-09-01", extract_id="x2")
    current, _ = s.read("simemr|dbo|T1")
    assert len(current) == 1 and current[0].properties["description"] == "d2"
    full, complete = s.read("simemr|dbo|T1", mode="all")
    assert complete == "including_retired"
    assert len(full) == 2
    assert full[0].valid_to == "2026-09-01"  # prior retired, still readable


def test_retire_marks_never_removes():
    s = _store_with_one()
    s.retire_node("simemr|dbo|T1", valid_to="2026-09-01")
    current, _ = s.read("simemr|dbo|T1")
    assert current == []
    full, _ = s.read("simemr|dbo|T1", mode="all")
    assert len(full) == 1 and full[0].valid_to == "2026-09-01"


def test_read_mode_is_explicit_never_a_default_surprise():
    s = _store_with_one()
    with pytest.raises(ValueError):
        s.read("simemr|dbo|T1", mode="everything")


def test_state_stamp_changes_on_write_and_holds_on_read():
    s = _store_with_one()
    before = s.state_stamp()
    s.read("simemr|dbo|T1")
    assert s.state_stamp() == before
    s.append_edge("joins_to", "simemr|dbo|T1", "simemr|dbo|T1",
                  {"on": [["A", "A"]], "cardinality": "many_to_one"},
                  as_of="2026-08-01", extract_id="x1")
    assert s.state_stamp() != before
