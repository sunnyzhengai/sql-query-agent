"""ADR 0054 L0: the red-flag sweep's decision rules — flag classes,
the RATIFIED severity boundaries, conservation, deterministic ids,
and the append-only disposition fold (reason MANDATORY on
accept/retire)."""

import json

from src.governance.red_flags import (
    apply_dispositions,
    sweep,
)


def _step(metric, name, frag):
    return {"node_id": f"transform:{metric}:{name}", "layer": "transformation",
            "name": name, "description": "",
            "properties": json.dumps({"metric_id": metric,
                                      "sql_fragment": frag,
                                      "step_no": 1})}


def _metric(ref, business=None):
    props = {"business_name": business} if business else {}
    return {"node_id": f"canonical:{ref}", "layer": "canonical",
            "name": ref.rsplit(".", 1)[-1], "description": "",
            "properties": json.dumps(props)}


class TestFlagClasses:
    def test_step_misnomer_is_info(self):
        # same step name, materially different logic — Base_Pop shape
        res = sweep([
            _metric("r.A"), _metric("r.B"),
            _step("r.A", "Base_Pop", "SELECT 1 FROM T"),
            _step("r.B", "Base_Pop", "SELECT 2 FROM U WHERE X=1"),
        ], [])
        flags = [f for f in res.flags_rows
                 if f["flag_class"] == "misnomer" and f["grain"] == "step"]
        assert len(flags) == 1
        f = flags[0]
        assert f["severity"] == "INFO" and f["scope"] == "proc-local"
        assert f["member_count"] == 2 and f["distinct_logics"] == 2

    def test_same_logic_same_name_is_clean(self):
        # whitespace/case differences are forgiven by _content_key
        res = sweep([
            _metric("r.A"), _metric("r.B"),
            _step("r.A", "Base_Pop", "SELECT 1  FROM T"),
            _step("r.B", "Base_Pop", "select 1 from t"),
        ], [])
        assert not [f for f in res.flags_rows
                    if f["flag_class"] == "misnomer"]

    def test_step_duplicate_is_info(self):
        # identical logic under different names — copy-paste shape
        res = sweep([
            _metric("r.A"), _metric("r.B"),
            _step("r.A", "Scores", "SELECT X FROM T"),
            _step("r.B", "Ratings", "SELECT X FROM T"),
        ], [])
        dups = [f for f in res.flags_rows
                if f["flag_class"] == "duplicate" and f["grain"] == "step"]
        assert len(dups) == 1 and dups[0]["severity"] == "INFO"
        # single-step metrics with identical logic are ALSO metric-
        # grain duplicates — both grains flag, correctly
        assert [f for f in res.flags_rows
                if f["flag_class"] == "duplicate" and f["grain"] == "metric"]

    def test_metric_name_collision_is_conflict(self):
        res = sweep([
            _metric("reporting.USP_X", "Sepsis Rate"),
            _metric("reports.USP_X", "Sepsis Rate"),
            _step("reporting.USP_X", "s1", "SELECT 1"),
            _step("reports.USP_X", "s1", "SELECT 2 WHERE Y=0"),
        ], [])
        mis = [f for f in res.flags_rows
               if f["flag_class"] == "misnomer" and f["grain"] == "metric"]
        assert len(mis) == 1
        assert mis[0]["severity"] == "CONFLICT"
        assert mis[0]["scope"] == "catalog"

    def test_cousin_containment_conflict_and_info(self):
        # the Legacy-v1 shape: root name's tokens a proper subset
        rows = [
            _metric("r.T", "Sepsis Patient Timeline"),
            _metric("r.T1", "Sepsis Patient Timeline (Legacy v1)"),
            _step("r.T", "s", "SELECT 1"),
            _step("r.T1", "s2", "SELECT 2 WHERE A=1"),
        ]
        res = sweep(rows, [])
        cousins = [f for f in res.flags_rows
                   if f["flag_class"] == "cousin_conflict"]
        assert len(cousins) == 1
        assert cousins[0]["severity"] == "CONFLICT"    # hashes diverge
        # aligned logic → INFO (naming hygiene only)
        rows_aligned = [
            _metric("r.T", "Sepsis Patient Timeline"),
            _metric("r.T1", "Sepsis Patient Timeline (Legacy v1)"),
            _step("r.T", "s", "SELECT 1"),
            _step("r.T1", "s2", "select 1"),
        ]
        res2 = sweep(rows_aligned, [])
        cousins2 = [f for f in res2.flags_rows
                    if f["flag_class"] == "cousin_conflict"]
        assert cousins2 and cousins2[0]["severity"] == "INFO"

    def test_unrelated_names_are_not_cousins(self):
        res = sweep([
            _metric("r.A", "Sepsis Case Details"),
            _metric("r.B", "Sepsis Case Encounters"),
            _step("r.A", "s", "SELECT 1"),
            _step("r.B", "s2", "SELECT 2"),
        ], [])
        assert not [f for f in res.flags_rows
                    if f["flag_class"] == "cousin_conflict"]


class TestConservationAndReceipts:
    def test_partition_sums_and_no_fragment_excluded(self):
        res = sweep([
            _metric("r.A"),
            _step("r.A", "s1", "SELECT 1"),
            _step("r.A", "empty", ""),
        ], [])
        assert res.excluded == {"no_fragment": 1}
        res.assert_conservation()

    def test_unparsed_metric_excluded(self):
        res = sweep([_metric("r.Ghost")], [])
        assert res.excluded == {"unparsed": 1}

    def test_flag_ids_are_deterministic_and_carry_receipts(self):
        rows = [
            _metric("r.A"), _metric("r.B"),
            _step("r.A", "Base_Pop", "SELECT 1"),
            _step("r.B", "Base_Pop", "SELECT 2"),
        ]
        f1 = sweep(rows, []).flags_rows[0]
        f2 = sweep(rows, []).flags_rows[0]
        assert f1["flag_id"] == f2["flag_id"]          # spec:E2
        members = json.loads(f1["members"])
        assert all("content_key" in m for m in members)
        assert f1["flag_id"] in f1["drill_query"]
        assert f1["blast_basis"]                        # never bare

    def test_blast_radius_counts_linked_reports_for_metric_flags(self):
        edges = [{"source_id": "report:dash", "target_id": "canonical:reporting.USP_X",
                  "edge_type": "report_to_canonical"}]
        res = sweep([
            _metric("reporting.USP_X", "Sepsis Rate"),
            _metric("reports.USP_X", "Sepsis Rate"),
            _step("reporting.USP_X", "s", "SELECT 1"),
            _step("reports.USP_X", "s", "SELECT 2"),
        ], edges)
        mis = [f for f in res.flags_rows if f["grain"] == "metric"
               and f["flag_class"] == "misnomer"][0]
        assert mis["blast_radius"] == 1
        assert "report" in mis["blast_basis"]


class TestDispositions:
    def _flags(self):
        return sweep([
            _metric("r.A"), _metric("r.B"),
            _step("r.A", "Base_Pop", "SELECT 1"),
            _step("r.B", "Base_Pop", "SELECT 2"),
        ], []).flags_rows

    def test_accept_requires_reason(self):
        flags = self._flags()
        out = apply_dispositions(flags, [
            {"flag_id": flags[0]["flag_id"], "kind": "accept",
             "actor": "pat"}])
        assert out.rejected and "MANDATORY" in out.rejected[0]["rejected"]
        assert out.flags_rows[0]["disposition"] == "open"

    def test_retire_mints_supersedes_and_duplicate_of(self):
        flags = self._flags()
        out = apply_dispositions(flags, [
            {"flag_id": flags[0]["flag_id"], "kind": "retire",
             "member": "r.B", "official": "r.A", "actor": "pat",
             "reason": "dead copy"}])
        assert ("r.A", "r.B", "supersedes") in out.minted_edges
        assert ("r.B", "r.A", "duplicate_of") in out.minted_edges
        assert out.flags_rows[0]["disposition"] == "retire"

    def test_certify_records_official_for_scope(self):
        flags = self._flags()
        out = apply_dispositions(flags, [
            {"flag_id": flags[0]["flag_id"], "kind": "certify",
             "member": "r.A", "scope": "catalog", "actor": "pat"}])
        assert out.official_props == [{
            "node_ref": "r.A", "official_for_scope": "catalog",
            "steward": "pat", "at": ""}]

    def test_unknown_flag_and_kind_are_rejected_rows(self):
        flags = self._flags()
        out = apply_dispositions(flags, [
            {"flag_id": "flag:nope", "kind": "accept", "reason": "x"},
            {"flag_id": flags[0]["flag_id"], "kind": "bless",
             "reason": "x"}])
        assert len(out.rejected) == 2


class TestFlatSurface:
    """F-1 (field find 2026-08-27, ruled a PRODUCT export): cluster
    rows carry the six governance fields as REAL top-level columns —
    no consumer parses the properties JSON to answer flag questions."""

    _ROWS = None      # built once below

    @classmethod
    def _flags(cls):
        from src.governance.red_flags import sweep
        return sweep([
            _metric("r.A"), _metric("r.B"),
            _step("r.A", "Base_Pop", "SELECT 1 FROM T"),
            _step("r.B", "Base_Pop", "SELECT 2 FROM U WHERE X=1"),
        ], []).flags_rows

    def test_cluster_nodes_carry_flat_columns(self):
        from src.governance.red_flags import (
            FLAT_FLAG_COLUMNS,
            reify_clusters,
        )
        nodes, _ = reify_clusters(self._flags())
        clusters = [n for n in nodes
                    if n["node_id"].startswith("cluster:")]
        assert clusters
        for n in clusters:
            for col in FLAT_FLAG_COLUMNS:
                assert n.get(col) is not None, (n["node_id"], col)
            props = json.loads(n["properties"])
            # flat values mirror the bag — one writer, two shapes
            assert n["flag_class"] == props["flag_class"]
            assert n["member_count"] == props["member_count"]
            assert n["disposition"] in (props["disposition"], "open")

    def test_loggroup_nodes_are_not_stamped_flat(self):
        from src.governance.red_flags import reify_clusters
        nodes, _ = reify_clusters(self._flags())
        for n in nodes:
            if n["node_id"].startswith("loggroup:"):
                assert "flag_class" not in n


class TestSelfDescription:
    """RW-7 (2026-08-28): the sweep says WHY it minted each flag —
    one business sentence per cluster, class-specific, never a bare
    count line."""

    def test_every_cluster_carries_a_why_sentence(self):
        from src.governance.red_flags import reify_clusters, sweep
        out = sweep([
            _metric("r.A"), _metric("r.B"),
            _step("r.A", "Base_Pop", "SELECT 1 FROM T"),
            _step("r.B", "Base_Pop", "SELECT 2 FROM U WHERE X=1"),
        ], [])
        nodes, _ = reify_clusters(out.flags_rows)
        for n in nodes:
            if n["node_id"].startswith("cluster:"):
                d = n["description"]
                assert "one name is doing" in d or "answer to" in d \
                    or "identical logic" in d or "grains" in d, d
                assert "flags disclose, never gate" in d
