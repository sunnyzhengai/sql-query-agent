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
        assert s.permitted("flag:misnomer:step:aaa111bbb222")

    def test_flags_plural_normalizes(self):
        s = OpsSession()
        rs = op_census("flags", fake_kql, s)
        assert len(rs.rows) == 2

    def test_contains_filters_by_identity_or_class(self):
        s = OpsSession()
        rs = op_census("flag", fake_kql, s, contains="cousin_conflict")
        assert len(rs.rows) == 1
        assert rs.rows[0]["flag_class"] == "cousin_conflict"


class TestFlagRetrieve:
    def test_full_flag_record_with_members_and_drill(self):
        s = OpsSession()
        op_census("flag", fake_kql, s)
        rec = op_retrieve(["flag:misnomer:step:aaa111bbb222"],
                          fake_kql, s)
        [row] = rec.rows
        assert row["kind"] == "flag"
        assert row["distinct_logics"] == 2
        assert isinstance(row["members"], list) and len(row["members"]) == 2
        assert "gov_red_flags" in row["drill_query"]
        # member refs surfaced for the next hop
        assert s.permitted(REF_A)


class TestVerdictStamps:
    def test_step_name_stamp_carries_the_recorded_flag(self):
        # W8's close of W6: the sameness answer is a machine verdict
        # read — the census stamp names the flag beside the caveat
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="Scores")
        assert SAMENESS_CAVEAT in rs.note
        assert "flag:misnomer:step:aaa111bbb222" in rs.note
        assert "2 distinct logic(s)" in rs.note
        assert s.permitted("flag:misnomer:step:aaa111bbb222")

    def test_metric_retrieve_stamps_variants_exist(self):
        s = OpsSession()
        op_search("ed sepsis", "semantic", fake_kql, s)
        rec = op_retrieve([REF_A], fake_kql, s)
        assert "certified variants exist" in rec.note
        assert "no official is designated yet" in rec.note
        assert s.permitted("flag:cousin_conflict:metric:ccc333ddd444")
