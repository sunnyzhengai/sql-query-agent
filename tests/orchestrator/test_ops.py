"""Tests for the ADR 0036 primitive algebra: search modes, merged
retrieve, compare kernels, session result sets and their self-declared
completeness."""

import pytest

from src.orchestrator.ops import (
    OpError,
    OpsSession,
    normalize_kind,
    op_census,
    op_compare,
    op_retrieve,
    op_search,
    row_mentions,
)
from tests.orchestrator.test_tools import (
    REF_A,
    REF_B,
    STEP_1,
    STEP_2,
    STEP_3,
    fake_kql,
)


class TestCensus:
    """Field find (2026-08-20, web-UI test): 'how many metrics are
    there' was planned as exact search for the word 'metrics' — kind
    words are categories, and enumeration needs its own primitive."""

    def test_enumerates_a_kind_completely_with_exact_count(self):
        s = OpsSession()
        rs = op_census("metric", fake_kql, s)
        assert rs.complete is True
        assert "count is exact" in rs.universe
        assert {r["id"] for r in rs.rows} == {REF_A, REF_B}
        assert s.permitted(REF_A)  # census surfaces ids for later reads

    def test_plural_kind_word_normalizes(self):
        assert normalize_kind("Metrics") == "metric"
        assert normalize_kind("reports") == "report"
        assert normalize_kind("dashboards") is None

    def test_unknown_kind_is_an_op_error_naming_the_kinds(self):
        with pytest.raises(OpError, match="metric, step, term"):
            op_census("dashboards", fake_kql, OpsSession())


class TestSearch:
    def test_semantic_mode_declares_incompleteness(self):
        s = OpsSession()
        rs = op_search("ed sepsis", "semantic", fake_kql, s)
        assert rs.ref == "R1" and rs.op == "search"
        assert rs.complete is False
        assert "NOT an exhaustive list" in rs.universe
        assert any(r["id"] == REF_A for r in rs.rows)
        assert s.permitted(REF_A)          # surfaced for later retrieve

    def test_exact_mode_declares_completeness(self):
        s = OpsSession()
        rs = op_search("Scores", "exact", fake_kql, s)
        assert rs.complete is True
        assert rs.params["mode"] == "exact"
        assert {r["id"] for r in rs.rows} == {STEP_1, STEP_2}

    def test_rows_carry_business_identity(self):
        """Live ask 2026-08-13: the basic tier is customer-facing — a
        search row must say what the thing MEANS (description) and, for
        steps, whose metric it belongs to (business name + step #),
        never bare CTE names."""
        s = OpsSession()
        rs = op_search("ed sepsis", "semantic", fake_kql, s)
        metric = next(r for r in rs.rows if r["kind"] == "metric")
        assert metric["description"] == "measures ED Sepsis Screening"
        step = next(r for r in rs.rows if r["kind"] == "step")
        assert step["business_name"] == "ED Sepsis Screening"  # parent's
        assert step["step_no"] == 1
        assert step["description"] == "what Scores computes"

    def test_mode_is_mandatory_and_validated(self):
        with pytest.raises(OpError, match="mode"):
            op_search("x", "fuzzy", fake_kql, OpsSession())


class TestRetrieve:
    def test_metric_record_includes_steps(self):
        s = OpsSession()
        s.note_user(REF_B)
        rs = op_retrieve([REF_B], fake_kql, s)
        row = rs.rows[0]
        assert row["kind"] == "metric"
        assert row["business_name"] == "ED Sepsis (Regulatory)"
        assert {x["name"] for x in row["steps"]} == {"Scores", "Labs"}
        assert s.permitted(STEP_3)         # step ids surfaced via retrieve

    def test_unsurfaced_id_refused(self):
        with pytest.raises(OpError, match="not been surfaced"):
            op_retrieve([REF_A], fake_kql, OpsSession())


class TestCompareKernels:
    def prepared(self):
        s = OpsSession()
        s.note_user(f"{REF_A} {REF_B}")
        op_retrieve([REF_A, REF_B], fake_kql, s)      # R1
        return s

    def test_partition_over_metrics(self):
        s = self.prepared()
        rs = op_compare(["R1"], "logic", fake_kql, s)
        groups = [r for r in rs.rows if "group" in r]
        assert len(groups) == 2                       # SELECT 1 vs SELECT 2
        assert rs.complete is True

    def test_partition_n_way_over_steps(self):
        s = OpsSession()
        rs = op_search("Scores", "exact", fake_kql, s)     # R1: 2 steps
        out = op_compare([rs.ref], None, fake_kql, s)
        groups = [r for r in out.rows if "group" in r]
        assert len(groups) == 1                       # respaced == same
        assert sorted(groups[0]["members"]) == sorted([STEP_1, STEP_2])

    def test_set_algebra_on_tables(self):
        s = self.prepared()
        rs = op_compare(["R1"], "tables", fake_kql, s)
        assert rs.rows[0]["shared"] == ["ADT"]
        only = {r["id"]: r["only_here"] for r in rs.rows[1:]}
        assert only[REF_A] == ["LABS"] and only[REF_B] == ["MEDS"]

    def test_field_diff_computes_agreement(self):
        s = self.prepared()
        same = op_compare(["R1"], "steward", fake_kql, s)
        assert same.rows[0]["all_equal"] is True      # both Pat
        diff = op_compare(["R1"], "developer", fake_kql, s)
        assert diff.rows[0]["all_equal"] is False     # Jane vs Sam

    def test_needs_two_items(self):
        s = OpsSession()
        s.note_user(REF_A)
        op_retrieve([REF_A], fake_kql, s)
        with pytest.raises(OpError, match="at least two"):
            op_compare(["R1"], None, fake_kql, s)


class TestSessionRegistry:
    def test_refs_increment_and_rows_accumulate(self):
        s = OpsSession()
        r1 = op_search("ed sepsis", "semantic", fake_kql, s)
        r2 = op_search("Scores", "exact", fake_kql, s)
        assert (r1.ref, r2.ref) == ("R1", "R2")
        assert len(s.rows_of(["R1", "R2"])) == len(r1.rows) + len(r2.rows)
        assert s.rows_of(["R99"]) == []


class TestAspectHonesty:
    def test_content_is_a_partition_alias(self):
        s = OpsSession()
        rs = op_search("Scores", "exact", fake_kql, s)
        out = op_compare([rs.ref], "content", fake_kql, s)
        assert any("group" in r for r in out.rows)      # partition ran

    def test_unknown_field_is_an_honest_miss(self):
        s = OpsSession()
        s.note_user(f"{REF_A} {REF_B}")
        op_retrieve([REF_A, REF_B], fake_kql, s)
        out = op_compare(["R1"], "flavour", fake_kql, s)
        assert "no item has a field 'flavour'" in out.rows[0]["error"]
        # offers real fields (list widened to 16 when freshness
        # columns joined the card, 2026-08-19)
        assert "steward" in out.rows[0]["error"]


class TestStepAlignmentKernel:
    """The fourth kernel (ADR 0043): WHERE two metrics diverge —
    aligned steps, missing steps, fragment diffs. Family F."""

    def prepared(self):
        s = OpsSession()
        s.note_user(f"{REF_A} {REF_B}")
        op_retrieve([REF_A, REF_B], fake_kql, s)
        return s

    def test_missing_step_is_the_finding(self):
        s = self.prepared()
        rs = op_compare(["R1"], "steps", fake_kql, s)
        verdict = rs.rows[0]
        # Scores aligns (respaced == identical, same forgiveness as the
        # partition kernel); Labs exists only in REF_B
        assert verdict["verdict"] == "divergent"
        assert verdict["aligned_steps"] == 1
        assert verdict["divergent_steps"] == 0
        assert verdict["steps_only_in"][REF_B] == ["Labs"]
        assert verdict["steps_only_in"][REF_A] == []
        assert rs.complete is True
        assert "step-aligned" in rs.universe

    def test_steps_aspect_refuses_step_selections(self):
        s = OpsSession()
        rs = op_search("Scores", "exact", fake_kql, s)  # rows are steps
        with pytest.raises(OpError, match="at least two metrics"):
            op_compare([rs.ref], "steps", fake_kql, s)


class TestTopicFilteredCensus:
    """2026-08-21: 'how many X mention T' is a data operation — the
    complete enumeration filtered by containment, count exact."""

    def test_contains_filters_the_complete_enumeration(self):
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="Regulatory")
        assert rs.complete is True
        assert len(rs.rows) == 1
        assert "mentions 'Regulatory'" in rs.universe
        assert "count is exact" in rs.universe

    def test_no_filter_unchanged(self):
        rs = op_census("metric", fake_kql, OpsSession())
        assert len(rs.rows) == 2 and "certified catalog — the count" in rs.universe

    def test_short_token_counts_whole_tokens_not_substrings(self):
        """1.50.4, pre-empting Sunny's walk question 'how many metrics
        contain ED logic': both fake metrics mention ED as a token
        ('ED Sepsis Screening', 'USP_ED_Sepsis') — and none would be
        excluded by the fix — but the count must come from the token
        predicate, exercised end-to-end through the census."""
        rs = op_census("metric", fake_kql, OpsSession(), contains="ED")
        assert len(rs.rows) == 2
        assert "mentions 'ED'" in rs.universe


class TestExactEmptyBridgeNote:
    """Walk step 1 (Sunny, 2026-08-21): 'how is Sepsis Case defined'
    ran exact, got an honest 0, and the one-round floor carried no
    did-you-mean. The empty exact result now computes its own
    near-names — bridge material is data, present even if the engine
    never takes a second round."""

    def test_empty_exact_search_notes_near_names(self):
        rs = op_search("Sepsis", "exact", fake_kql, OpsSession())
        assert rs.rows == [] and rs.complete is True
        assert "Nothing is NAMED 'Sepsis' exactly" in rs.note
        assert "ED Sepsis Screening" in rs.note

    def test_exact_hit_carries_no_note(self):
        rs = op_search("ED Sepsis Screening", "exact", fake_kql,
                       OpsSession())
        assert rs.rows and rs.note == ""

    def test_empty_exact_with_no_near_names_stays_bare(self):
        rs = op_search("zzz", "exact", fake_kql, OpsSession())
        assert rs.rows == [] and rs.note == ""


class TestRowMentions:
    """The 'mentions T' predicate is the SPEC shared by op_census and
    the suite oracle — pinned here at L0 because the suite, sharing it,
    cannot catch its bugs."""

    def test_whole_token_not_substring(self):
        assert not row_mentions(
            {"name": "X", "description": "well defined and created"}, "ED")

    def test_underscore_is_a_token_boundary(self):
        assert row_mentions({"name": "USP_ED_SEPSIS"}, "ED")

    def test_space_and_case_insensitive(self):
        assert row_mentions({"business_name": "ed sepsis screening"}, "ED")

    def test_json_keys_and_ids_never_count(self):
        """The 1.50.3 filter scanned json.dumps(row): the key string
        'business_name' made needle 'name' match EVERY row, and ids
        counted despite the stamped universe naming only name,
        business name, and description."""
        assert not row_mentions(
            {"id": "reports.USP_NAME", "name": "X",
             "business_name": None, "description": None}, "name")

    def test_none_fields_are_safe(self):
        assert not row_mentions(
            {"name": None, "business_name": None, "description": None}, "ED")
