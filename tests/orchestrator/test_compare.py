"""Tests for the compare verb + the conversational entry edge (ADR 0034).

The verb-scorecard game (docs/internal/VERB_SCORECARD.md) is the
acceptance criteria: Sunny's questions Q2-Q6 are the fixtures here.
"""

import json

from src.orchestrator.assemble import METRIC_FACTS_QUERY
from src.orchestrator.compare import (
    BATCH_FRAGMENTS_QUERY,
    SCOPED_RESOLVE_QUERY,
    STEPS_OF_QUERY,
    build_comparison,
    is_field_aspect,
)
from src.orchestrator.core import produce_intent
from src.orchestrator.events import JsonlEventSink

REF_A = "reporting.USP_ED_Sepsis"
REF_B = "reports.USP_ED_Sepsis"

METRICS = {
    REF_A: {
        "metric_id": REF_A, "metric_name": "USP_ED_Sepsis",
        "business_name": "ED Sepsis Screening", "description": "d",
        "steward": "Pat", "developer": "Jane",
        "report_name": "ED Dashboard", "report_url": "https://r/1",
        "transform_count": 3, "source_tables": "ADT, LABS, ORDERS",
        "calculation_logic": "SELECT 1",
    },
    REF_B: {
        "metric_id": REF_B, "metric_name": "USP_ED_Sepsis",
        "business_name": "ED Sepsis (Regulatory)", "description": "d",
        "steward": "Pat", "developer": "Sam",
        "report_name": "Reg Dashboard", "report_url": "https://r/2",
        "transform_count": 3, "source_tables": "ADT, LABS, MEDS",
        "calculation_logic": "SELECT 2",
    },
}

# Both metrics define Scores (identical) and Labs (drifted); A alone
# defines Cultures.
STEPS = {
    REF_A: [("Scores", "SELECT S FROM T WHERE X >= 2"),
            ("Labs", "SELECT L WHERE KIND = 'A'"),
            ("Cultures", "SELECT C")],
    REF_B: [("Scores", "select  s from t where x >= 2"),   # respaced/case
            ("Labs", "SELECT L WHERE KIND = 'B'")],
}


def panel_kql(scoped_rows=None):
    def run_kql(query, params):
        if query == METRIC_FACTS_QUERY:
            row = METRICS.get(params["p_ref"])
            return [row] if row else []
        if query == STEPS_OF_QUERY:
            ref = params["p_ref"]
            return [{"node_id": f"transform:{ref}:{n}", "name": n}
                    for n, _ in STEPS.get(ref, [])]
        if query == BATCH_FRAGMENTS_QUERY:
            wanted = set(json.loads(params["p_ids"]))
            rows = []
            for ref, steps in STEPS.items():
                for n, frag in steps:
                    node_id = f"transform:{ref}:{n}"
                    if node_id in wanted:
                        rows.append({"node_id": node_id, "properties":
                                     json.dumps({"sql_fragment": frag})})
            return rows
        if query == SCOPED_RESOLVE_QUERY:
            return scoped_rows or []
        raise AssertionError(f"unexpected query: {query}")
    return run_kql


class TestPanel:
    def test_scalars_typed_verdicts(self):
        fs = build_comparison(REF_A, REF_B, panel_kql())
        assert fs.kind == "comparison"
        assert fs.facts["same_steward"] == "yes (Pat)"
        assert "no (" in fs.facts["same_developer"]
        assert "Jane" in fs.facts["same_developer"]
        assert fs.facts["whole_calculation_identical"] == "no"

    def test_table_set_algebra(self):
        fs = build_comparison(REF_A, REF_B, panel_kql())
        assert fs.facts["shared_tables"] == "ADT, LABS"
        assert fs.facts["tables_only_in_subject_1"] == "ORDERS"
        assert fs.facts["tables_only_in_subject_2"] == "MEDS"

    def test_shared_steps_two_depths(self):
        # shared by NAME vs shared by LOGIC — computed separately
        fs = build_comparison(REF_A, REF_B, panel_kql())
        assert fs.facts["shared_step_names"] == "Labs, Scores"
        assert fs.facts["shared_steps_with_identical_logic"] == "Scores"
        assert fs.facts["shared_steps_with_different_logic"] == "Labs"
        assert "2 shared names" in fs.basis
        assert "1 identical, 1 drifted" in fs.basis

    def test_concept_aspect_matches_and_diffs(self):
        scoped = [
            {"node_id": f"transform:{REF_A}:Labs", "kind": "step",
             "ref": REF_A, "name": "Labs", "business_name": "",
             "display_text": "d", "closeness": 0.72},
            {"node_id": f"transform:{REF_B}:Labs", "kind": "step",
             "ref": REF_B, "name": "Labs", "business_name": "",
             "display_text": "d", "closeness": 0.70},
        ]
        fs = build_comparison(REF_A, REF_B, panel_kql(scoped),
                              chosen_aspect="lab criteria")
        assert fs.facts["'lab criteria' in ED Sepsis Screening"] == "Labs"
        assert fs.facts["'lab criteria' logic identical"] == "no"
        assert "KIND = 'B'" in fs.facts["'lab criteria' diff"]
        assert "scoped to both subjects" in fs.basis

    def test_concept_aspect_no_match_is_honest(self):
        fs = build_comparison(REF_A, REF_B, panel_kql(scoped_rows=[]),
                              chosen_aspect="unicorn logic")
        assert ("no step clearly matches"
                in fs.facts["'unicorn logic' in ED Sepsis Screening"])

    def test_ambiguous_concept_invokes_choose(self):
        scoped = [
            {"node_id": f"transform:{REF_A}:Labs", "kind": "step",
             "ref": REF_A, "name": "Labs", "business_name": "",
             "display_text": "d", "closeness": 0.70},
            {"node_id": f"transform:{REF_A}:Cultures", "kind": "step",
             "ref": REF_A, "name": "Cultures", "business_name": "",
             "display_text": "d", "closeness": 0.65},
            {"node_id": f"transform:{REF_B}:Labs", "kind": "step",
             "ref": REF_B, "name": "Labs", "business_name": "",
             "display_text": "d", "closeness": 0.68},
        ]
        calls = []
        def choose(label, candidates):
            calls.append((label, [c.name for c in candidates]))
            return 1                      # the human picks Cultures
        fs = build_comparison(REF_A, REF_B, panel_kql(scoped),
                              chosen_aspect="micro", choose=choose)
        assert len(calls) == 1            # only side A was ambiguous
        assert calls[0][1] == ["Labs", "Cultures"]
        assert fs.facts["'micro' in ED Sepsis Screening"] == "Cultures"

    def test_weak_concept_skips_the_quiz_entirely(self):
        # Live find (2026-08-10): 'sepsis definition' matched nothing
        # above the floor, and the chooser dumped 32 steps on the user.
        # Below the floor: no choose call, honest note, panel answers.
        scoped = [
            {"node_id": f"transform:{REF_A}:S{i}", "kind": "step",
             "ref": REF_A, "name": f"S{i}", "business_name": "",
             "display_text": "d", "closeness": 0.56 - i / 100}
            for i in range(30)
        ]
        calls = []
        fs = build_comparison(
            REF_A, REF_B, panel_kql(scoped), chosen_aspect="sepsis definition",
            choose=lambda label, cands: calls.append(1) or 0)
        assert not calls                  # the user was never quizzed
        note = fs.facts["'sepsis definition' in ED Sepsis Screening"]
        assert "no step clearly matches" in note
        assert "0.56" in note             # honest about how weak it was

    def test_choices_capped_at_five(self):
        scoped = [
            {"node_id": f"transform:{REF_A}:S{i}", "kind": "step",
             "ref": REF_A, "name": f"S{i}", "business_name": "",
             "display_text": "d", "closeness": 0.75 - i / 100}
            for i in range(12)
        ]
        seen = {}
        def choose(label, candidates):
            seen["n"] = len(candidates)
            return None                   # 'n' = skip the zoom
        fs = build_comparison(REF_A, REF_B, panel_kql(scoped),
                              chosen_aspect="micro", choose=choose)
        assert seen["n"] == 5             # never the whole inventory
        assert "zoom skipped" in fs.facts["'micro' in ED Sepsis Screening"]

    def test_field_aspect_needs_no_resolution(self):
        assert is_field_aspect("developer")
        assert is_field_aspect("Source Tables")
        assert not is_field_aspect("ED sepsis definition")
        # field aspect: panel runs, no scoped query issued (panel_kql
        # would raise on an unexpected SCOPED call with scoped_rows=None
        # returning [] — assert no aspect keys appear instead)
        fs = build_comparison(REF_A, REF_B, panel_kql(),
                              chosen_aspect="developer")
        assert not any("'developer'" in k for k in fs.facts)

    def test_replay_same_inputs_same_panel(self):
        assert (build_comparison(REF_A, REF_B, panel_kql())
                == build_comparison(REF_A, REF_B, panel_kql()))

    def test_empty_fragments_never_claim_identity(self):
        # Live find (2026-08-10): two steps with no recorded SQL compared
        # as "identical" — empty==empty is a data gap, not a verdict.
        import copy
        steps = copy.deepcopy(STEPS)
        steps[REF_A][0] = ("Scores", "")
        def run_kql(query, params):
            if query == BATCH_FRAGMENTS_QUERY:
                wanted = set(json.loads(params["p_ids"]))
                return [{"node_id": f"transform:{ref}:{n}", "properties":
                         json.dumps({"sql_fragment": frag})}
                        for ref, ss in steps.items() for n, frag in ss
                        if f"transform:{ref}:{n}" in wanted]
            return panel_kql()(query, params)
        fs = build_comparison(REF_A, REF_B, run_kql)
        assert "Scores" in fs.facts["shared_steps_where_logic_not_comparable"]
        assert fs.facts["shared_steps_with_identical_logic"] == "(none)"

    def test_empty_whole_logic_cannot_verify(self):
        import copy
        metrics = copy.deepcopy(METRICS)
        metrics[REF_A]["calculation_logic"] = None
        def run_kql(query, params):
            if query == METRIC_FACTS_QUERY:
                row = metrics.get(params["p_ref"])
                return [row] if row else []
            return panel_kql()(query, params)
        fs = build_comparison(REF_A, REF_B, run_kql)
        assert fs.facts["whole_calculation_identical"].startswith("cannot verify")


class TestIntentParsing:
    def test_compare_with_aspect(self):
        line = f"COMPARE: {REF_A} | {REF_B} | on=ED sepsis definition"
        intent = produce_intent("q", lambda s, u: line)
        assert intent.verb == "compare"
        assert intent.tokens == (REF_A, REF_B)
        assert intent.aspect == "ED sepsis definition"

    def test_compare_without_aspect(self):
        intent = produce_intent("q", lambda s, u: f"COMPARE: {REF_A} | {REF_B}")
        assert intent.verb == "compare" and intent.aspect is None

    def test_malformed_compare_degrades_to_search(self):
        intent = produce_intent("q", lambda s, u: "COMPARE: only-one-side")
        assert intent.verb == "search"

    def test_unsupported_reasons_validated(self):
        ok = produce_intent("q", lambda s, u: "UNSUPPORTED: lineage")
        assert ok.verb == "unsupported" and ok.tokens == ("lineage",)
        bad = produce_intent("q", lambda s, u: "UNSUPPORTED: astrology")
        assert bad.verb == "search"

    def test_context_is_passed_to_the_llm(self):
        seen = {}
        def chat(s, u):
            seen["user"] = u
            return "topic"
        produce_intent("and this?", chat, context="Last answer covered: X")
        assert seen["user"].startswith("Last answer covered: X")
        assert seen["user"].endswith("Question: and this?")


class TestScorecardFixtures:
    """The game's questions, end to end through the CLI dispatch."""

    def drive(self, replies, chat, run_kql, tmp_path):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        it = iter(replies)
        chat_loop(chat, run_kql, sink, ask=lambda p="": next(it), say=say)
        path = tmp_path / "e.jsonl"
        events = ([json.loads(x) for x in path.read_text().splitlines()]
                  if path.exists() else [])
        return "\n".join(out), events

    def compare_chat(self, aspect=None):
        def chat(system, user):
            if "typed request" in system:
                line = f"COMPARE: {REF_A} | {REF_B}"
                if aspect:
                    line += f" | on={aspect}"
                return line
            return "Computed comparison narrated."
        return chat

    def test_q3_same_developer_no_pick_menus(self, tmp_path):
        # "were these two metrics written by the same developer"
        text, events = self.drive(
            ["were these two metrics written by the same developer", "q"],
            self.compare_chat(), panel_kql(), tmp_path)
        assert "Computed comparison narrated." in text
        assert "Pick a number" not in text       # refs bound directly
        assert "1 identical, 1 drifted" in text  # code-stamped basis

    def test_q2_aspect_comparison_flows(self, tmp_path):
        scoped = [
            {"node_id": f"transform:{REF_A}:Labs", "kind": "step",
             "ref": REF_A, "name": "Labs", "business_name": "",
             "display_text": "d", "closeness": 0.6},
            {"node_id": f"transform:{REF_B}:Labs", "kind": "step",
             "ref": REF_B, "name": "Labs", "business_name": "",
             "display_text": "d", "closeness": 0.58},
        ]
        text, _ = self.drive(
            ["are these two metrics using the same ED sepsis definition",
             "q"],
            self.compare_chat("ED sepsis definition"), panel_kql(scoped),
            tmp_path)
        assert "Computed comparison narrated." in text
        assert "scoped to both subjects" in text

    def test_q6_lineage_refuses_honestly_and_logs(self, tmp_path):
        def chat(system, user):
            if "typed request" in system:
                return "UNSUPPORTED: lineage"
            return "should never narrate"
        text, events = self.drive(
            ["which metrics are downstream of the ADT table", "q"],
            chat, panel_kql(), tmp_path)
        assert "aren't supported yet" in text
        assert "should never narrate" not in text
        assert "Pick a number" not in text       # no adjacent pick list
        assert events[0]["token"] == "unsupported:lineage"
        assert events[0]["picked_node_id"] is None

    def test_unbindable_subject_falls_to_resolution_pick(self, tmp_path):
        # the LLM names a subject loosely -> resolve + human pick binds it
        def chat(system, user):
            if "typed request" in system:
                return f"COMPARE: ed sepsis screening | {REF_B}"
            return "Narrated."
        def run_kql(query, params):
            from src.orchestrator.core import RESOLVE_QUERY
            if query == RESOLVE_QUERY:
                return [{
                    "node_id": f"canonical:{REF_A}", "kind": "metric",
                    "ref": REF_A, "name": "USP_ED_Sepsis",
                    "business_name": "ED Sepsis Screening",
                    "display_text": "d", "closeness": 0.6,
                    "total_matches": 1,
                }]
            return panel_kql()(query, params)
        text, events = self.drive(
            ["compare ed sepsis screening to the regulatory one", "1", "q"],
            chat, run_kql, tmp_path)
        assert "Pick a number" in text           # binding went through pick
        assert "Narrated." in text
        assert events[0]["picked_ref"] == REF_A  # the bind was recorded
