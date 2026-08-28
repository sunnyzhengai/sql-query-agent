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
    op_lineage,
    op_retrieve,
    op_search,
    row_mentions,
)
from tests.orchestrator.test_tools import (
    REF_A,
    REF_B,
    REPORT_ID,
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

    def test_step_record_carries_dep_chain_both_directions(self):
        # B3 (green-lit 2026-08-25, built 2026-08-27): "what feeds
        # this step / what does this step feed" — the
        # transform_to_transform edges on the step record, chain ids
        # surfaced for follow-up retrieve (token law)
        s = OpsSession()
        s.note_user(REF_B)
        op_retrieve([REF_B], fake_kql, s)          # surfaces step ids
        rs = op_retrieve([STEP_2], fake_kql, s)
        row = rs.rows[0]
        assert row["kind"] == "step"
        assert [x["name"] for x in row["fed_by_steps"]] == ["Labs"]
        assert row["feeds_steps"] == []
        assert s.permitted(STEP_3)     # the dep id is now retrievable
        rs2 = op_retrieve([STEP_3], fake_kql, s)
        assert [x["name"] for x in rs2.rows[0]["feeds_steps"]] == [
            "Scores"]
        assert rs2.rows[0]["fed_by_steps"] == []


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

    def test_note_names_are_surfaced_for_retrieval(self):
        """Corpse fixture (1.52.0 suite, 2026-08-21): the model
        retrieved the note's names, the read guarantee refused the
        unsurfaced ids, and the flail burned the round cap. A name
        the machine put on screen is surfaced."""
        s = OpsSession()
        op_search("Sepsis", "exact", fake_kql, s)
        assert s.permitted(REF_A)

    def test_exact_hit_carries_no_note(self):
        rs = op_search("ED Sepsis Screening", "exact", fake_kql,
                       OpsSession())
        assert rs.rows and rs.note == ""

    def test_empty_exact_with_no_near_names_stays_bare(self):
        rs = op_search("zzz", "exact", fake_kql, OpsSession())
        assert rs.rows == [] and rs.note == ""

    def test_table_phrase_notes_source_table_identity(self):
        """Walk find (Sunny, 2026-08-21): 'how is IP_SEPSIS defined' —
        the phrase names a TECHNICAL node invisible to the catalog
        surfaces. The honest empty must say what the thing IS (a
        source table) and who reads it, not 'cannot be provided'."""
        rs = op_search("IP_SEPSIS", "exact", fake_kql, OpsSession())
        assert rs.rows == []
        assert "'IP_SEPSIS' is a SOURCE TABLE read by 2 certified " \
               "metric(s)" in rs.note
        assert "ED Sepsis Screening" in rs.note

    def test_zero_row_filtered_census_carries_the_bridge_note(self):
        """Her live miss: census kind='step' contains='IP_SEPSIS' → 0
        rows → 'cannot be provided'. The empty FILTERED census is an
        honest empty holding a phrase — same law, same note."""
        rs = op_census("step", fake_kql, OpsSession(),
                       contains="IP_SEPSIS")
        assert rs.rows == []
        assert "SOURCE TABLE" in rs.note

    def test_unfiltered_census_never_notes(self):
        rs = op_census("metric", fake_kql, OpsSession())
        assert rs.note == ""

    def test_step_census_filters_by_parent_metric_ref(self):
        """Walk find (Sunny, 2026-08-21): census step
        contains='USP_Severe_Sepsis' returned 0 — the model's op was
        right, but a step's parent ref lived in no scanned field."""
        rs = op_census("step", fake_kql, OpsSession(), contains=REF_A)
        assert [r["of_metric"] for r in rs.rows] == [REF_A]
        assert "parent metric mentions" in rs.universe

    def test_multiword_phrase_degrades_to_productive_tokens(self):
        """Suite find (2026-08-21): the model filtered by the user's
        literal words 'ED logic'; the filler noun matched nothing and
        the honest 0 read as 'none' while the true count sat in a
        note. A zero-match multi-word phrase now degrades to its
        productive tokens with the degradation stamped in the
        universe — the count on screen is the one the question
        meant."""
        rs = op_census("metric", fake_kql, OpsSession(),
                       contains="ED logic")
        assert len(rs.rows) == 2
        assert rs.params["effective_contains"] == "ED"
        assert "no metric mentions 'ED logic' as a phrase" in rs.universe
        assert "'logic' matches nothing and was disregarded" in rs.universe
        assert "count is exact" in rs.universe

    def test_fully_unproductive_phrase_stays_empty_with_bridge_note(self):
        rs = op_census("metric", fake_kql, OpsSession(),
                       contains="zz qq")
        assert rs.rows == []
        assert "effective_contains" not in rs.params

    def test_identifier_phrase_notes_the_matched_form(self):
        """Walk find: 'IP_SEPSIS' matches metric NAMES, never the
        English business names — the note must print the containing
        form, not a business name that doesn't visibly relate."""
        rs = op_search("USP_ED", "exact", fake_kql, OpsSession())
        assert rs.rows == []
        assert "USP_ED_Sepsis" in rs.note
        assert "ED Sepsis Screening" not in rs.note


class TestDecisionLayer:
    """ADR 0052 backfill item 1 (Sunny's order, 2026-08-21): step
    retrieve attaches the decision sites — the WHERE/CASE criteria as
    data, not step-description prose. Sunny rejected the
    summary-flavored drilldown answer; this is its fix."""

    def test_step_retrieve_attaches_decisions(self):
        s = OpsSession()
        s.surfaced.add(STEP_1)
        rs = op_retrieve([STEP_1], fake_kql, s)
        decs = rs.rows[0]["decisions"]
        assert len(decs) == 1
        assert decs[0]["context"] == "WHERE"
        assert decs[0]["predicate_count"] == 2
        assert "SepsisDX = 1" in decs[0]["expression_sql"]

    def test_decision_expression_is_phi_redacted_at_read_time(self):
        """Sunny's rider: decision sites are the payload most likely
        to carry embedded literals (ADR 0025), and the store's rows
        predate the export-side gate — the ask-path redacts at the
        last point before an expression can enter a prompt."""
        s = OpsSession()
        s.surfaced.add(STEP_1)
        rs = op_retrieve([STEP_1], fake_kql, s)
        expr = rs.rows[0]["decisions"][0]["expression_sql"]
        assert "John Smith" not in expr
        assert "<NAME>" in expr

    def test_metric_record_carries_inline_decision_sites(self):
        """M2 design pass (2026-08-21): drill-down needs ZERO hops —
        the metric record carries its top decision sites, PHI-gated,
        with the exact total beside them."""
        s = OpsSession()
        s.surfaced.add(REF_A)
        rs = op_retrieve([REF_A], fake_kql, s)
        row = rs.rows[0]
        sites = row["decision_sites"]
        assert sites and sites[0]["context"] == "WHERE"
        assert sites[0]["step"] == "Scores"
        assert "SepsisDX = 1" in sites[0]["expression_sql"]
        assert "John Smith" not in sites[0]["expression_sql"]  # PHI
        assert row["decision_count"] == 1                      # exact

    def test_metric_retrieve_carries_decision_count(self):
        """The pointer to hop 2 is data: the metric record counts its
        decision sites so the headline can stamp where criteria live."""
        s = OpsSession()
        s.surfaced.add(REF_A)
        rs = op_retrieve([REF_A], fake_kql, s)
        assert rs.rows[0]["decision_count"] == 1

    def test_step_without_decisions_gets_empty_list(self):
        s = OpsSession()
        s.surfaced.add(STEP_2)
        rs = op_retrieve([STEP_2], fake_kql, s)
        assert rs.rows[0]["decisions"] == []


class TestLineage:
    """Walk find 4 (Sunny, 2026-08-21): 'is there any other metrics
    using IP_SEPSIS?' routed to a mention-census — 'using' is the
    READER relation; lineage questions get a lineage primitive."""

    def test_readers_of_table_complete_and_exact(self):
        s = OpsSession()
        rs = op_lineage("IP_SEPSIS", fake_kql, s)
        assert rs.complete is True
        assert "never name mentions" in rs.universe
        assert {r["id"] for r in rs.rows} == {REF_A, REF_B}
        assert all(r["reads_table"] == "IP_SEPSIS" for r in rs.rows)
        assert s.permitted(REF_A)          # readers surfaced for hops

    def test_exact_table_scopes_out_name_cousins(self):
        """1.54.1 corpse: 'IP_SEPSIS' pulled reader pairs for every
        table CONTAINING the phrase; the caption computed the true
        count itself and was floored for it. Exact match scopes to
        that table's readers alone."""
        rs = op_lineage("IP_SEPSIS", fake_kql, OpsSession())
        assert "reads the table 'IP_SEPSIS'" in rs.universe
        assert all(r["reads_table"] == "IP_SEPSIS" for r in rs.rows)

    def test_token_fallback_matches_whole_tokens(self):
        """1.56.1 corpse: lineage(table='ED') substring-matched every
        table containing 'ed' — 80 pairs read as '80 metrics', a
        dishonest turn. The fallback is whole-token, like the census
        learned in 1.50.4."""
        rs = op_lineage("SEPSIS", fake_kql, OpsSession())
        assert rs.rows                      # token of IP_SEPSIS
        assert "whose name has the token 'SEPSIS'" in rs.universe
        rs2 = op_lineage("EP", fake_kql, OpsSession())
        assert rs2.rows == []               # substring of IP_SEPSIS only

    def test_reader_names_are_stamped_in_the_note(self):
        """1.56.1: the gate floored a caption for an invented
        sub-count and the floor lost the reader names — small complete
        results carry their names as machine truth."""
        rs = op_lineage("IP_SEPSIS", fake_kql, OpsSession())
        assert "2 distinct metric(s)" in rs.note
        assert "ED Sepsis Screening" in rs.note

    def test_column_note_pairs_relations_with_names(self):
        rs = op_lineage("", fake_kql, OpsSession(), column="PATIENTMRN")
        assert "Selects 'PATIENTMRN':" in rs.note
        assert "ED Sepsis (Regulatory)" in rs.note

    def test_unknown_table_is_an_honest_empty(self):
        rs = op_lineage("zzz", fake_kql, OpsSession())
        assert rs.rows == [] and rs.complete is True

    def test_blank_table_is_an_op_error(self):
        with pytest.raises(OpError, match="table or column"):
            op_lineage("  ", fake_kql, OpsSession())


class TestColumnsWork:
    """Columns work (registry rank 3, walk probes C2/C3/D4/D5,
    Sunny's order 2026-08-22)."""

    def test_column_blast_radius_via_decision_sites(self):
        s = OpsSession()
        rs = op_lineage("", fake_kql, s, column="SepsisDX")
        assert rs.complete is True
        assert "FILTERS on" in rs.universe
        assert "the column 'SepsisDX'" in rs.universe
        assert {r["id"] for r in rs.rows} == {REF_A, REF_B}
        assert all(r["relation"] == "filters" and
                   r["column"] == "SepsisDX" for r in rs.rows)

    def test_selected_by_these_filtered_by_none(self):
        """Sunny's governance example (ADR 0053): 'PATIENTMRN is
        selected by these metrics and filtered by none' — the pair is
        the answer, from projection edges beside decision sites."""
        rs = op_lineage("", fake_kql, OpsSession(), column="PATIENTMRN")
        assert [r["relation"] for r in rs.rows] == ["selects", "selects"]
        assert {r["id"] for r in rs.rows} == {REF_A, REF_B}
        assert "FILTERS on" in rs.universe and "SELECTS" in rs.universe

    def test_pre_0053_export_says_projection_absent(self):
        """A graph export minted before ADR 0053 has zero projection
        edges — 'selected by none' must not be claimed then."""
        def kql(query, params):
            from src.orchestrator.tools import (
                COLUMN_SELECTS_QUERY as SQ,
            )
            from src.orchestrator.tools import (
                PROJECTION_EDGES_COUNT_QUERY as PQ,
            )
            if query == PQ:
                return [{"Count": 0}]
            if query == SQ:
                return []
            return fake_kql(query, params)
        rs = op_lineage("", kql, OpsSession(), column="PATIENTMRN")
        assert rs.rows == []          # selects fake routed to count-0 path
        assert "predates the ADR 0053 edges" in rs.note

    def test_table_and_column_together_is_an_op_error(self):
        with pytest.raises(OpError, match="not both"):
            op_lineage("T", fake_kql, OpsSession(), column="C")

    def test_retrieve_resolves_a_user_named_table(self):
        """D4: 'what columns does IP_SEPSIS have' — the table record,
        columns from the dictionary edges, readers from lineage."""
        s = OpsSession()
        s.note_user("what columns does IP_SEPSIS have")
        rs = op_retrieve(["IP_SEPSIS"], fake_kql, s)
        row = rs.rows[0]
        assert row["kind"] == "table"
        assert row["columns"] == ["PATIENTMRN", "SepsisDX"]
        assert "ED Sepsis Screening" in row["read_by"]

    def test_step_sites_carry_their_columns(self):
        """C3: the site names the columns its predicates decide on."""
        s = OpsSession()
        s.surfaced.add(STEP_1)
        rs = op_retrieve([STEP_1], fake_kql, s)
        assert rs.rows[0]["decisions"][0]["columns"] == [
            "PatientName", "SepsisDX"]


class TestReportLinks:
    """ADR 0052 backfill item 2 (Sunny's order, 2026-08-21): the
    pointer chase — reports were searchable but hollow. Metric
    retrieve lists its reports; report retrieve carries the parsed
    TMDL links, and every linked id is surfaced for the next hop."""

    def test_metric_retrieve_lists_and_surfaces_reports(self):
        s = OpsSession()
        s.surfaced.add(REF_A)
        rs = op_retrieve([REF_A], fake_kql, s)
        reports = rs.rows[0]["reports"]
        assert reports == [{"id": REPORT_ID,
                            "name": "ED Ops Dashboard"}]
        assert s.permitted(REPORT_ID)      # next hop is legal

    def test_report_retrieve_carries_links_and_surfaces_targets(self):
        s = OpsSession()
        s.surfaced.add(REPORT_ID)
        rs = op_retrieve([REPORT_ID], fake_kql, s)
        row = rs.rows[0]
        assert row["kind"] == "report"
        assert row["report_name"] == "ED Ops Dashboard"
        assert [e["id"] for e in row["executes_metrics"]] == [REF_A]
        assert [e["name"] for e in row["measures"]] == ["Screen Rate"]
        assert s.permitted(REF_A)          # chase continues


class TestTokenDegradedContainment:
    """Suite find (2026-08-21): the model paraphrased the user's name
    into 'Sepsis Case Definition' — full-phrase containment went dark
    and no sibling stamp fired. A multi-word phrase that matches
    nothing degrades to its productive tokens, same law as the
    census."""

    def test_paraphrased_phrase_still_rides_companions_along(self):
        s = OpsSession()
        rs = op_search("ED Sepsis Definition", "semantic", fake_kql, s)
        flagged = [r for r in rs.rows if r.get("name_match")]
        assert flagged, "degraded containment companions must ride"
        assert any(r["id"] == REF_B for r in flagged)

    def test_exact_empty_note_uses_degraded_companions(self):
        rs = op_search("ED Sepsis Definition", "exact", fake_kql,
                       OpsSession())
        assert rs.rows == []
        assert "closest by name:" in rs.note
        assert "ED Sepsis Screening" in rs.note


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


class TestNonEvidenceStamp:
    def test_column_probe_with_metric_name_is_stamped(self):
        # live-eval corpse 2026-08-27 (temp-0): lineage(column=
        # <metric name>) let the coverage caveat legitimize an
        # absence claim — the phrase is not a column; the result is
        # NON-EVIDENCE and redirects to the record
        from src.orchestrator.ops import NON_EVIDENCE_STAMP, op_lineage
        s = OpsSession()
        rs = op_lineage("", fake_kql, s, column="ED Sepsis Screening")
        assert not rs.rows
        assert NON_EVIDENCE_STAMP in rs.note
        assert "not a column" in rs.note
        assert s.permitted(REF_A)          # redirect target surfaced

    def test_real_column_with_no_edges_keeps_the_honest_caveat(self):
        # the caveat path for a REAL-shaped column stays unstamped —
        # coverage-absent is honest evidence, not a category error
        from src.orchestrator.ops import NON_EVIDENCE_STAMP, op_lineage
        rs = op_lineage("", fake_kql, OpsSession(),
                        column="TOTALLY_UNKNOWN_COL")
        assert NON_EVIDENCE_STAMP not in rs.note


class TestUnanchoredReportState:
    def test_zero_link_report_carries_the_typed_state(self):
        # G1 extension ruling constraint 2: the answer carries the
        # state — "executes a target outside this catalog"
        from tests.orchestrator.test_tools import FOREIGN_REPORT_ID
        s = OpsSession()
        s.note_user(FOREIGN_REPORT_ID)
        rs = op_retrieve([FOREIGN_REPORT_ID], fake_kql, s)
        row = rs.rows[0]
        assert "outside this catalog" in row["link_state"]

    def test_linked_report_has_no_state_note(self):
        s = OpsSession()
        s.note_user(REPORT_ID)
        rs = op_retrieve([REPORT_ID], fake_kql, s)
        assert "link_state" not in rs.rows[0]
