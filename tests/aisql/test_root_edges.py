"""STEP 5 of the Connection Ledger build — ROOT EDGES. The test
suite, shown to Sunny before any implementation (step discipline).

The last MISSING row and the root ruling: an excluded file (a
refused parse) is deduced from THE ESTATE'S INTAKE — it chains to
the estate root like everything intake-born. The db node (carrying
the registration trace) is ruled THE root: the one kind allowed to
be an origin rather than have one.

- record_exclusion stores the estate root reference at write.
- The adjacency walks excluded_file —excluded_from→ root.
- The ledger row flips (excluded_from / edged; registry 1.25.0);
  a legacy exclusion without the reference counts missing.
- The census's rooted count is EXACTLY the root: one db.

Proves: contract:aisql-design-to-code
"""
import json
import pathlib

import pytest

from aisql.flows import censuses, connect
from aisql.graph import kg1_intake, kg2_mapper
from aisql.graph.read_api import ReadApi

T0 = "2026-09-07T12:00:00Z"
BASE = (pathlib.Path(__file__).resolve().parents[2]
        / "AIVIA_Product" / "estates" / "sepsis")


@pytest.fixture()
def store():
    s = kg1_intake.new_store()
    reg = json.loads((BASE / "registration.json").read_text())
    kg1_intake.apply_registration(s, reg)
    kg2_mapper.record_exclusion(s, "reports/legacy.mqx",
                                "unsupported-dialect (mqx)", T0)
    return s


def test_exclusions_store_the_root_reference(store):
    read = ReadApi(store)
    exc = next(n for n in read.nodes("excluded_file"))
    db = next(n for n in read.nodes("db"))
    assert exc.properties["estate"] == db.identity


def test_exclusions_walk_to_the_root(store):
    read = ReadApi(store)
    adj = connect.build_adjacency(read)
    exc = next(n for n in read.nodes("excluded_file"))
    db = next(n for n in read.nodes("db"))
    edges = {(n, lbl) for n, lbl in adj.get(exc.identity, [])}
    assert (db.identity, "excluded_from") in edges
    back = {(n, lbl) for n, lbl in adj.get(db.identity, [])}
    assert (exc.identity, "excluded_from") in back


def test_ledger_flips_and_census_counts(store):
    ledger = censuses.connection_ledger()
    assert ledger["excluded_file"]["edge"] == "excluded_from"
    assert ledger["excluded_file"]["status"] == "edged"
    c = censuses.connection_census(ReadApi(store))
    assert "excluded_file" not in c["counted_missing_kinds"]
    # THE ROOT RULING: rooted is exactly the one db
    assert c["rooted"] == 1


def test_a_legacy_exclusion_counts_missing(store):
    store.append_node("excluded_file", "old/legacy2.mqx",
                      {"reason": "pre-law exclusion"}, T0, "legacy")
    c = censuses.connection_census(ReadApi(store))
    assert "excluded_file" in c["counted_missing_kinds"]
