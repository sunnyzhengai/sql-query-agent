"""ADR 0054 L0: the agent's flag surface — census kind 'flag',
retrieve of a flag record, the single-row sameness verdict riding the
step-name stamp, and the variants-exist stamp on metric retrieval."""

from src.orchestrator.ops import (
    SAMENESS_CAVEAT,
    OpsSession,
    op_census,
    op_retrieve,
    op_search,
)
from tests.orchestrator.test_tools import REF_A, fake_kql


class TestFlagCensus:
    def test_census_kind_flag_enumerates_verdicts(self):
        s = OpsSession()
        rs = op_census("flag", fake_kql, s)
        assert rs.complete
        assert len(rs.rows) == 2
        assert {r["kind"] for r in rs.rows} == {"flag"}
        assert "flags disclose, never gate" in rs.universe
        # flag ids are surfaced → retrievable next hop
        assert s.permitted("cluster:misnomer:step:aaa111bbb222")

    def test_flags_plural_normalizes(self):
        s = OpsSession()
        rs = op_census("flags", fake_kql, s)
        assert len(rs.rows) == 2

    def test_contains_filters_by_identity_or_class(self):
        s = OpsSession()
        rs = op_census("flag", fake_kql, s, contains="cousin_conflict")
        assert len(rs.rows) == 1
        assert rs.rows[0]["flag_class"] == "cousin_conflict"

    def test_census_cites_the_sweep_receipt(self):
        s = OpsSession()
        rs = op_census("flag", fake_kql, s)
        assert "sweep receipt: 63 item(s) swept" in rs.universe

    def test_pre_sweep_store_refuses_the_bare_zero(self):
        # smoke find 2026-08-26: zero clusters + no receipt = a store
        # that PREDATES the sweep — a bare 0 would be the false-empty
        # class; the op must refuse with the remediation
        import pytest

        from src.orchestrator.ops import OpError
        from src.orchestrator.tools import (
            GOV_FLAGS_QUERY,
            GOV_SWEEP_META_QUERY,
        )

        def pre_sweep_kql(query, params):
            if query in (GOV_FLAGS_QUERY, GOV_SWEEP_META_QUERY):
                return []
            return fake_kql(query, params)

        with pytest.raises(OpError) as e:
            op_census("flag", pre_sweep_kql, OpsSession())
        assert "predates the graph-native sweep" in str(e.value)
        assert "not proven zero flags" in str(e.value)


class TestFlagRetrieve:
    def test_full_flag_record_with_members_and_drill(self):
        s = OpsSession()
        op_census("flag", fake_kql, s)
        rec = op_retrieve(["cluster:misnomer:step:aaa111bbb222"],
                          fake_kql, s)
        [row] = rec.rows
        assert row["kind"] == "flag"
        assert row["distinct_logics"] == 2
        assert isinstance(row["members"], list) and len(row["members"]) == 2
        assert "member_of" in row["drill_query"]
        # member NODES surfaced for the next hop (graph-native:
        # cluster members ARE the org nodes — steps here)
        assert s.permitted(f"transform:{REF_A}:Scores")


class TestVerdictStamps:
    def test_step_name_stamp_carries_the_recorded_flag(self):
        # W8's close of W6: the sameness answer is a machine verdict
        # read — the census stamp names the flag beside the caveat
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="Scores")
        assert SAMENESS_CAVEAT in rs.note
        assert "cluster:misnomer:step:aaa111bbb222" in rs.note
        assert "2 distinct logic(s)" in rs.note
        assert s.permitted("cluster:misnomer:step:aaa111bbb222")

    def test_metric_retrieve_stamps_variants_exist(self):
        s = OpsSession()
        op_search("ed sepsis", "semantic", fake_kql, s)
        rec = op_retrieve([REF_A], fake_kql, s)
        assert "certified variants exist" in rec.note
        assert "no official is designated yet" in rec.note
        assert s.permitted("cluster:cousin_conflict:metric:ccc333ddd444")


class TestMemberLabelCollisions:
    """RW-BATCH-4 polish (re-walk 2026-08-29): the misnomer card
    rendered "USP_Active_Diabetics, USP_Active_Diabetics" — the
    shared bare name hid the very difference the flag surfaces.
    Colliding names schema-qualify (the W3a mechanism, reused)."""

    def test_colliding_names_qualify_distinct_names_stay_bare(self):
        from src.orchestrator.ops import _member_labels
        labels = _member_labels(
            ["USP_Active_Diabetics", "USP_Active_Diabetics",
             "USP_DM_Registry"],
            ["metric:reporting.USP_Active_Diabetics",
             "metric:staging.USP_Active_Diabetics",
             "metric:reporting.USP_DM_Registry"])
        assert labels == [
            "USP_Active_Diabetics (reporting.USP_Active_Diabetics)",
            "USP_Active_Diabetics (staging.USP_Active_Diabetics)",
            "USP_DM_Registry"]

    def test_store_without_ids_falls_back_to_bare_names(self):
        from src.orchestrator.ops import _member_labels
        assert _member_labels(["A", "A"], []) == ["A", "A"]

    def test_census_rows_carry_qualified_member_names(self):
        from src.orchestrator.tools import GOV_FLAG_MEMBER_NAMES_QUERY

        def kql(query, params):
            if query == GOV_FLAG_MEMBER_NAMES_QUERY:
                return [{
                    "cluster": "cluster:misnomer:step:aaa111bbb222",
                    "member_names": ["USP_Active_Diabetics",
                                     "USP_Active_Diabetics"],
                    "member_ids": [
                        "metric:reporting.USP_Active_Diabetics",
                        "metric:staging.USP_Active_Diabetics"]}]
            return fake_kql(query, params)

        s = OpsSession()
        rs = op_census("flag", kql, s)
        [row] = [r for r in rs.rows
                 if r["id"] == "cluster:misnomer:step:aaa111bbb222"]
        assert row["member_names"] == [
            "USP_Active_Diabetics (reporting.USP_Active_Diabetics)",
            "USP_Active_Diabetics (staging.USP_Active_Diabetics)"]
