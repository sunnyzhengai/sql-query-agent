"""The reachability contract's teeth (ADR 0052).

Totality: every NodeLayer, EdgeType, and catalog kind carries exactly
one row — a new layer cannot land in the graph invisible by accident.
Fidelity: a row claiming reach names implementation text the marker
must actually appear in; a row claiming exclusion states a reason.
"""

import inspect

import src.orchestrator.ops as ops_mod
import src.orchestrator.tools as tools_mod
from src.models import EdgeType, NodeLayer
from src.orchestrator.tools import CATALOG_KINDS
from src.reachability import REACHABILITY


class TestTotality:
    def test_every_node_layer_has_a_row(self):
        for layer in NodeLayer:
            rows = [r for r in REACHABILITY
                    if r["payload"].split(":")[0] == "node"
                    and r["payload"].split(":")[1] == layer.value]
            assert rows, (
                f"NodeLayer.{layer.name} has no reachability row — "
                "declare an op or an exclusion (ADR 0052)")

    def test_every_edge_type_has_exactly_one_row(self):
        for et in EdgeType:
            rows = [r for r in REACHABILITY
                    if r["payload"] == f"edge:{et.value}"]
            assert len(rows) == 1, (
                f"EdgeType.{et.name} needs exactly one reachability "
                f"row, found {len(rows)} (ADR 0052)")

    def test_every_catalog_kind_has_exactly_one_row(self):
        for k in CATALOG_KINDS:
            rows = [r for r in REACHABILITY
                    if r["payload"] == f"catalog:{k}"]
            assert len(rows) == 1, f"catalog kind {k!r} needs one row"

    def test_no_orphan_rows(self):
        """Single classification: every row maps back to a real
        NodeLayer / EdgeType / catalog kind."""
        layers = {v.value for v in NodeLayer}
        edges = {v.value for v in EdgeType}
        for r in REACHABILITY:
            head, _, rest = r["payload"].partition(":")
            if head == "node":
                assert rest.split(":")[0] in layers, r["payload"]
            elif head == "edge":
                assert rest in edges, r["payload"]
            elif head == "catalog":
                assert rest in CATALOG_KINDS, r["payload"]
            else:
                raise AssertionError(f"unknown payload {r['payload']}")

    def test_payloads_unique(self):
        keys = [r["payload"] for r in REACHABILITY]
        assert len(keys) == len(set(keys))


class TestFidelity:
    def test_reachable_rows_markers_exist_in_implementation(self):
        for r in REACHABILITY:
            if r["status"] != "reachable":
                continue
            marker = r.get("marker") or ""
            for qname in r.get("queries", ()):
                text = getattr(tools_mod, qname)
                assert isinstance(text, str), qname
                if marker:
                    assert marker in text, (
                        f"{r['payload']}: marker {marker!r} not in "
                        f"{qname} — the row claims reach the query "
                        "doesn't implement")
            for opname in r.get("ops", ()):
                fn = getattr(ops_mod, opname)
                if marker:
                    assert marker in inspect.getsource(fn), (
                        f"{r['payload']}: marker {marker!r} not in "
                        f"source of {opname}")

    def test_excluded_rows_state_a_reason(self):
        for r in REACHABILITY:
            if r["status"] == "excluded":
                assert len(r.get("reason", "")) >= 20, (
                    f"{r['payload']}: an exclusion is a decision on "
                    "record — state why")

    def test_statuses_are_binary(self):
        assert {r["status"] for r in REACHABILITY} <= {
            "reachable", "excluded"}
