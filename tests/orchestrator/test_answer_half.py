"""Tests for assemble, narrate, events, and the CLI loop (offline)."""

import json

import pytest

from src.orchestrator.assemble import (
    METRIC_FACTS_QUERY,
    NODE_FACTS_QUERY,
    AssemblyError,
    assemble,
)
from src.orchestrator.cli import chat_loop, render_candidates
from src.orchestrator.core import Candidate, resolve
from src.orchestrator.events import JsonlEventSink, PickEvent
from src.orchestrator.narrate import narrate
from src.schemas import USAGE_EVENTS

METRIC_ROW = {
    "metric_id": "reporting.USP_ED_Sepsis", "metric_name": "USP_ED_Sepsis",
    "business_name": "ED Sepsis Screening", "description": "Measures X.",
    "steward": None, "developer": None,
    "report_name": "ED Dashboard", "report_url": "https://r/1",
    "transform_count": 43, "source_tables": "A, B",
    "calculation_logic": "-- Base_Pop SELECT ...",
}
NODE_ROW = {
    "node_id": "transform:reporting.USP_ED_Sepsis:Base_Pop",
    "name": "Base_Pop", "description": "Distinct encounters.",
    "properties": json.dumps(
        {"metric_id": "reporting.USP_ED_Sepsis", "sql_fragment": "SELECT 1"}
    ),
}


def fake_kql(query, params):
    if query == METRIC_FACTS_QUERY:
        return [METRIC_ROW] if params["p_ref"] == METRIC_ROW["metric_id"] else []
    if query == NODE_FACTS_QUERY:
        return [NODE_ROW] if params["p_node_id"] == NODE_ROW["node_id"] else []
    raise AssertionError(f"unexpected query: {query}")


def cand(kind, node_id, ref):
    return Candidate(node_id=node_id, kind=kind, ref=ref, name="n",
                     business_name="", display_text="d", closeness=0.5,
                     total_matches=1)


class TestAssemble:
    def test_metric_fixed_lookup(self):
        fs = assemble(cand("metric", "canonical:reporting.USP_ED_Sepsis",
                           "reporting.USP_ED_Sepsis"), fake_kql)
        assert fs.facts["business_name"] == "ED Sepsis Screening"
        assert fs.basis == "output_metric_logic[metric_id='reporting.USP_ED_Sepsis'] -> 1 row"

    def test_step_joins_parent_metric(self):
        fs = assemble(cand("step", NODE_ROW["node_id"],
                           "reporting.USP_ED_Sepsis"), fake_kql)
        assert fs.facts["step_name"] == "Base_Pop"
        assert fs.facts["sql_fragment"] == "SELECT 1"
        assert fs.facts["parent_business_name"] == "ED Sepsis Screening"
        assert "graph_nodes" in fs.basis and "output_metric_logic" in fs.basis

    def test_missing_facts_raise_honestly(self):
        with pytest.raises(AssemblyError):
            assemble(cand("metric", "canonical:ghost", "ghost"), fake_kql)

    def test_unknown_kind_raises(self):
        with pytest.raises(AssemblyError):
            assemble(cand("term", "term:x", "x"), fake_kql)


class TestNarrate:
    def test_prose_plus_code_stamped_basis(self):
        fs = assemble(cand("metric", "canonical:reporting.USP_ED_Sepsis",
                           "reporting.USP_ED_Sepsis"), fake_kql)
        seen = {}
        def chat(system, user):
            seen.update(system=system, user=user)
            return "It measures X."
        out = narrate(fs, chat)
        assert out.startswith("It measures X.")
        assert out.endswith(f"Basis: {fs.basis}")       # stamped by code
        assert "ED Sepsis Screening" in seen["user"]     # facts in prompt
        assert "steward" not in seen["user"]             # nulls omitted
        assert "never substitute the business name" in seen["system"]

    def test_rule5_wording_cannot_leak_as_output(self):
        # Live regression (2026-08-10): "write NO Used-in line" was pasted
        # verbatim into an answer. The rule must never contain words that
        # read as content to emit.
        from src.orchestrator.narrate import NARRATE_SYSTEM
        assert "write NO Used-in" not in NARRATE_SYSTEM
        assert "NO Used-in line" not in NARRATE_SYSTEM


class TestEvents:
    def test_jsonl_sink_appends_and_maps_to_contract(self, tmp_path):
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        ev = PickEvent(
            event_at="2026-08-09T00:00:00Z", user_id="u1", question="q?",
            token="q", candidates_shown=("a", "b"),
            picked_node_id="a", picked_ref="m.X", total_matches=2,
        )
        sink.record(ev)
        sink.record(ev)
        lines = (tmp_path / "e.jsonl").read_text().splitlines()
        assert len(lines) == 2
        row = ev.to_usage_event_row()
        assert set(row) == {c[0] for c in USAGE_EVENTS["columns"]}
        assert row["outcome"] == "answered" and row["metric_id"] == "m.X"

    def test_decline_maps_to_refused(self):
        ev = PickEvent(event_at="t", user_id="u", question="q", token="q",
                       candidates_shown=("a",), picked_node_id=None,
                       picked_ref=None, total_matches=1)
        assert ev.to_usage_event_row()["outcome"] == "refused"


class TestCliLoop:
    def scripted(self, inputs):
        it = iter(inputs)
        return lambda prompt="": next(it)

    def collect(self):
        out = []
        return out, lambda *a: out.append(" ".join(str(x) for x in a))

    def run_kql_for_loop(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            return [{
                "node_id": "canonical:reporting.USP_ED_Sepsis",
                "kind": "metric", "ref": "reporting.USP_ED_Sepsis",
                "name": "USP_ED_Sepsis", "business_name": "ED Sepsis Screening",
                "display_text": "ED Sepsis Screening (metric)",
                "closeness": 0.44, "total_matches": 1,
            }]
        return fake_kql(query, params)

    def test_full_loop_question_pick_answer_event(self, tmp_path):
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out, say = self.collect()
        chat = lambda s, u: ("ED sepsis screening" if "search phrase" in s
                             else "The metric measures X.")
        chat_loop(chat, self.run_kql_for_loop, sink,
                  ask=self.scripted(["how is ed screening done?", "1", "q"]),
                  say=say)
        text = "\n".join(out)
        assert "1. ED Sepsis Screening" in text        # candidate shown
        assert "The metric measures X." in text        # narrated answer
        assert "Basis:" in text                        # stamped provenance
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        assert events[0]["picked_ref"] == "reporting.USP_ED_Sepsis"

    def test_refusal_and_decline_both_record(self, tmp_path):
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out, say = self.collect()
        def run_kql(query, params):
            from src.orchestrator.core import RESOLVE_QUERY
            assert query == RESOLVE_QUERY
            return []
        chat_loop(lambda s, u: "unicorn velocity", run_kql, sink,
                  ask=self.scripted(["unicorns?", "q"]), say=say)
        text = "\n".join(out)
        assert "Nothing in the certified knowledge base" in text
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        assert events[0]["picked_node_id"] is None

    def test_single_candidate_still_requires_pick(self, tmp_path):
        # no bypass: 1 candidate is presented exactly like 10
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out, say = self.collect()
        chat = lambda s, u: ("token" if "search phrase" in s else "Prose.")
        chat_loop(chat, self.run_kql_for_loop, sink,
                  ask=self.scripted(["q?", "1", "q"]), say=say)
        assert "Pick a number" in "\n".join(out)


class TestRendering:
    def test_weak_matches_labeled_closeness_visible(self):
        rows = [{
            "node_id": "a", "kind": "step", "ref": "r", "name": "N",
            "business_name": "", "display_text": "d",
            "closeness": 0.36, "total_matches": 12,
        }]
        result = resolve("t", lambda q, p: rows)
        text = render_candidates(result)
        assert "closeness 0.36" in text and "(weak match)" in text
        assert "Found 12 related item(s); showing 1" in text


class TestCompareFlow:
    """'Compare X and Y': two tokens -> two pick rounds -> one comparison."""

    def run_kql(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            token = params["token"]
            row = {
                "node_id": f"canonical:m.{token}", "kind": "metric",
                "ref": "reporting.USP_ED_Sepsis",
                "name": f"USP_{token}", "business_name": token.title(),
                "display_text": f"{token} (metric)",
                "closeness": 0.5, "total_matches": 1,
            }
            return [row]
        return fake_kql(query, params)

    def test_two_tokens_two_picks_one_comparison(self, tmp_path):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        def chat(system, user):
            if "search phrase" in system:
                return "alpha\nbeta"           # entry edge splits into 2
            return "Alpha does X; Beta does Y."  # exit edge compares
        it = iter(["compare alpha and beta", "1", "1", "q"])
        chat_loop(chat, self.run_kql, sink, ask=lambda p="": next(it), say=say)
        text = "\n".join(out)
        assert "For 'alpha':" in text and "For 'beta':" in text
        assert "Alpha does X; Beta does Y." in text
        assert text.count("output_metric_logic[metric_id=") >= 1  # stamped basis
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        assert len(events) == 2                  # one pick event per concept


class TestPickEscape:
    """A new question typed at the pick prompt escapes the menu."""

    def run_kql(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            if params["token"] == "second topic":
                return []          # new question resolves to nothing
            return [{
                "node_id": "canonical:reporting.USP_ED_Sepsis",
                "kind": "metric", "ref": "reporting.USP_ED_Sepsis",
                "name": "USP_ED_Sepsis", "business_name": "ED Sepsis Screening",
                "display_text": "d", "closeness": 0.44, "total_matches": 1,
            }]
        return fake_kql(query, params)

    def test_question_at_pick_prompt_becomes_new_question(self, tmp_path):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        def chat(system, user):
            return "second topic" if "second" in user else "first topic"
        it = iter(["first question", "what about something else second", "q"])
        chat_loop(chat, self.run_kql, sink, ask=lambda p="": next(it), say=say)
        text = "\n".join(out)
        assert "(Taking that as a new question.)" in text
        assert "Nothing in the certified knowledge base" in text  # new q refused
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        assert events[0]["picked_node_id"] is None   # abandoned list = decline
        assert len(events) == 2

    def test_out_of_range_number_still_reprompts(self, tmp_path):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        chat = lambda s, u: ("topic" if "search phrase" in s else "Prose.")
        it = iter(["q1", "9", "1", "q"])
        chat_loop(chat, self.run_kql, sink, ask=lambda p="": next(it), say=say)
        text = "\n".join(out)
        assert "between 1 and 1" in text
        assert "Prose." in text


class TestConfirmation:
    """The strong signal: endorsement is the verdict AFTER reading."""

    def run_kql(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            return [{
                "node_id": "canonical:reporting.USP_ED_Sepsis",
                "kind": "metric", "ref": "reporting.USP_ED_Sepsis",
                "name": "USP_ED_Sepsis", "business_name": "ED Sepsis Screening",
                "display_text": "d", "closeness": 0.44, "total_matches": 1,
            }]
        return fake_kql(query, params)

    def drive(self, tmp_path, replies):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        chat = lambda s, u: ("topic" if "search phrase" in s else "Prose.")
        it = iter(replies)
        chat_loop(chat, self.run_kql, sink, ask=lambda p="": next(it), say=say)
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        return "\n".join(out), events

    def test_yes_records_confirmed_endorsement(self, tmp_path):
        _, events = self.drive(tmp_path, ["q1", "1", "y", "q"])
        assert len(events) == 2                       # pick + confirmation
        assert events[1]["verdict"] == "confirmed"
        from src.orchestrator.events import ConfirmEvent
        row = ConfirmEvent(**{k: events[1][k] for k in
            ("event_at", "user_id", "question", "picked_node_id",
             "picked_ref", "verdict")}).to_usage_event_row()
        assert row["feedback"] == "confirmed"

    def test_no_records_rejection(self, tmp_path):
        _, events = self.drive(tmp_path, ["q1", "1", "n", "q"])
        assert events[1]["verdict"] == "rejected"

    def test_enter_skips_no_signal(self, tmp_path):
        _, events = self.drive(tmp_path, ["q1", "1", "", "q"])
        assert len(events) == 1                       # pick only

    def test_new_question_at_confirm_escapes(self, tmp_path):
        text, events = self.drive(
            tmp_path, ["q1", "1", "something entirely new", "1", "", "q"])
        assert "(Taking that as a new question.)" in text
        assert len(events) == 2                       # two picks, no verdicts


class TestLiveFindings20260810:
    """Sunny's live session (2026-08-10): escape keys corrupted a pick,
    and an over-split token produced near-duplicate candidate lists."""

    def run_kql(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            return [{
                "node_id": "canonical:reporting.USP_ED_Sepsis",
                "kind": "metric", "ref": "reporting.USP_ED_Sepsis",
                "name": "USP_ED_Sepsis", "business_name": "ED Sepsis Screening",
                "display_text": "d", "closeness": 0.44, "total_matches": 1,
            }]
        return fake_kql(query, params)

    def drive(self, tmp_path, replies, chat=None):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        chat = chat or (lambda s, u: ("topic" if "search phrase" in s
                                      else "Prose."))
        it = iter(replies)
        chat_loop(chat, self.run_kql, sink, ask=lambda p="": next(it), say=say)
        events = [json.loads(x) for x in
                  (tmp_path / "e.jsonl").read_text().splitlines()]
        return "\n".join(out), events

    def test_escape_char_glued_to_digit_still_picks(self, tmp_path):
        # the live bug: Esc echoed as ^[ made "2" a non-digit -> new question
        text, events = self.drive(tmp_path, ["q1", "\x1b1", "", "q"])
        assert "(Taking that as a new question.)" not in text
        assert "Prose." in text
        assert events[0]["picked_ref"] == "reporting.USP_ED_Sepsis"

    def test_arrow_key_alone_reprompts(self, tmp_path):
        text, events = self.drive(tmp_path, ["q1", "\x1b[A", "1", "", "q"])
        assert "(Taking that as a new question.)" not in text
        assert "Prose." in text

    def test_empty_pick_reply_never_false_matches(self, tmp_path):
        # empty reply must re-prompt — not exact-match an empty business_name
        from src.orchestrator.core import parse_pick
        c = cand("metric", "canonical:x", "x")     # business_name == ""
        assert parse_pick("", (c,)) is None
        text, events = self.drive(tmp_path, ["q1", "", "1", "", "q"])
        assert "Prose." in text
        assert len(events) == 1                    # one pick, no phantom

    def test_duplicate_token_list_shown_once(self, tmp_path):
        # over-split single concept -> second (identical) list is skipped:
        # one pick round, one answer, one pick event
        def chat(system, user):
            if "search phrase" in system:
                return "sepsis metrics\nsepsis definition metrics"
            return "Prose."
        text, events = self.drive(tmp_path, ["which metrics defined sepsis",
                                             "1", "", "q"], chat=chat)
        assert "(Skipping 'sepsis definition metrics'" in text
        assert text.count("Pick a number") == 1
        assert "Prose." in text
        assert len(events) == 1

    def test_duplicate_list_math(self):
        from src.orchestrator.core import duplicate_list
        a = {"n1", "n2", "n3", "n4"}
        assert duplicate_list({"n1", "n2", "n9", "n10"}, [a])      # 2/4 = 0.5
        assert not duplicate_list({"n1", "n8", "n9", "n10"}, [a])  # 1/4
        assert not duplicate_list(set(), [a])                      # empty new
        assert not duplicate_list({"n1"}, [])                      # no priors


class TestFollowUpDetail:
    """Sunny's live case (2026-08-09): 'show me its sql' after an answer
    must show THAT answer's SQL — never re-resolve into weak ODBC steps."""

    def run_kql(self, query, params):
        from src.orchestrator.core import RESOLVE_QUERY
        if query == RESOLVE_QUERY:
            assert params["token"] != "sql", "follow-up leaked into resolution"
            return [{
                "node_id": "canonical:reporting.USP_ED_Sepsis",
                "kind": "metric", "ref": "reporting.USP_ED_Sepsis",
                "name": "USP_ED_Sepsis", "business_name": "ED Sepsis Screening",
                "display_text": "d", "closeness": 0.44, "total_matches": 1,
            }]
        return fake_kql(query, params)

    def drive(self, tmp_path, replies):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        chat = lambda s, u: ("topic" if "search phrase" in s else "Prose.")
        it = iter(replies)
        chat_loop(chat, self.run_kql, sink, ask=lambda p="": next(it), say=say)
        return "\n".join(out)

    def test_show_me_its_sql_uses_last_answer(self, tmp_path):
        text = self.drive(tmp_path,
                          ["how is ed screening done?", "1", "",
                           "show me its sql", "q"])
        assert "--- SQL for ED Sepsis Screening ---" in text
        assert "-- Base_Pop SELECT ..." in text          # the actual SQL
        assert "(cached from your last answer)" in text  # basis honesty
        assert "weak match" not in text                  # never re-resolved

    def test_owner_and_tables_and_link_commands(self, tmp_path):
        text = self.drive(tmp_path,
                          ["how is ed screening done?", "1", "",
                           "who owns it?", "tables?", "show the link", "q"])
        assert "steward = (none assigned)" in text
        assert "A, B" in text                            # source tables
        assert "ED Dashboard — https://r/1" in text

    def test_detail_before_any_answer_prompts_kindly(self, tmp_path):
        text = self.drive(tmp_path, ["show me its sql", "q"])
        assert "Ask about a metric first" in text

    def test_real_questions_with_command_words_still_resolve(self, tmp_path):
        # "which metrics read from sql server tables" is NOT a detail command
        from src.orchestrator.cli import match_detail_command
        assert match_detail_command("which metrics read from sql server tables") is None
        assert match_detail_command("show me its sql") == "sql"
        assert match_detail_command("who owns it?") == "owner"
        assert match_detail_command("link?") == "link"
