"""Tests for the variants verb (set-subject consistency check).

Sunny's live questions (2026-08-10) are the fixtures:
  "are they all using the same definition of #Base_Pop_Severe_ED_Scores"
  "is reporting.USP_ED_Sepsis using the same Base_Pop_Severe_ED_Scores
   logic as reports.USP_IP_SEPSIS?"
"""

import json

from src.orchestrator.assemble import NODE_FACTS_QUERY
from src.orchestrator.core import produce_intent
from src.orchestrator.events import JsonlEventSink
from src.orchestrator.variants import (
    FAMILY_QUERY,
    compare_variants,
    variant_facts,
    variants_answer,
)

SQL_A = "SELECT PAT_ENC_CSN_ID\nINTO #X\nFROM T\nWHERE SCORE >= 2"
SQL_A_RESPACED = "select  PAT_ENC_CSN_ID   into #X from T where score >= 2"
SQL_B = "SELECT PAT_ENC_CSN_ID\nINTO #X\nFROM T\nWHERE SCORE >= 3"


def family_kql(members):
    """Fake run_kql serving FAMILY_QUERY + NODE_FACTS_QUERY.
    members: list of (node_id, ref, fragment)."""
    def run_kql(query, params):
        if query == FAMILY_QUERY:
            name = params["p_name"].lower()
            return [{"node_id": n, "ref": r, "name": "Base_Pop_Severe_ED_Scores"}
                    for n, r, _ in members
                    if name == "base_pop_severe_ed_scores"]
        if query == NODE_FACTS_QUERY:
            for n, r, frag in members:
                if n == params["p_node_id"]:
                    return [{"node_id": n, "name": "Base_Pop_Severe_ED_Scores",
                             "properties": json.dumps({"sql_fragment": frag})}]
            return []
        raise AssertionError(f"unexpected query: {query}")
    return run_kql


THREE_PROCS = [
    ("transform:reporting.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores",
     "reporting.USP_ED_Sepsis", SQL_A),
    ("transform:reports.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores",
     "reports.USP_ED_Sepsis", SQL_A_RESPACED),      # same logic, respaced
    ("transform:reports.USP_IP_SEPSIS:Base_Pop_Severe_ED_Scores",
     "reports.USP_IP_SEPSIS", SQL_B),               # drifted: >= 3
]


class TestIntentEdge:
    def test_variants_line_classifies(self):
        chat = lambda s, u: "VARIANTS: #Base_Pop_Severe_ED_Scores"
        intent = produce_intent("are they all the same?", chat)
        assert intent.verb == "variants"
        assert intent.tokens == ("#Base_Pop_Severe_ED_Scores",)

    def test_plain_lines_stay_search(self):
        chat = lambda s, u: "sepsis screening"
        intent = produce_intent("what is sepsis screening?", chat)
        assert intent.verb == "search"
        assert intent.tokens == ("sepsis screening",)

    def test_multi_concept_search_unchanged(self):
        chat = lambda s, u: "alpha\nbeta"
        intent = produce_intent("compare alpha and beta", chat)
        assert intent.verb == "search" and len(intent.tokens) == 2

    def test_empty_variants_name_degrades_to_search(self):
        chat = lambda s, u: "VARIANTS:"
        intent = produce_intent("q", chat)
        assert intent.verb == "search"   # structural validation held


class TestPartition:
    def test_whitespace_and_case_fold_into_one_group(self):
        report = compare_variants("Base_Pop_Severe_ED_Scores",
                                  family_kql(THREE_PROCS))
        assert not report.consistent
        assert len(report.groups) == 2
        # largest group first; refs sorted; the drifted proc isolated
        assert report.groups[0].refs == ("reporting.USP_ED_Sepsis",
                                         "reports.USP_ED_Sepsis")
        assert report.groups[1].refs == ("reports.USP_IP_SEPSIS",)
        assert "3 fragments] -> 2 distinct" in report.basis

    def test_hash_prefix_and_temp_table_prefix_stripped(self):
        # Sunny typed the temp-table spelling: leading # must not miss
        report = compare_variants("#Base_Pop_Severe_ED_Scores",
                                  family_kql(THREE_PROCS))
        assert report is not None and len(report.groups) == 2

    def test_unknown_name_returns_none(self):
        assert compare_variants("Ghost_Step", family_kql(THREE_PROCS)) is None

    def test_all_identical_is_consistent(self):
        members = THREE_PROCS[:2]     # SQL_A + respaced SQL_A only
        report = compare_variants("Base_Pop_Severe_ED_Scores",
                                  family_kql(members))
        assert report.consistent

    def test_replay_same_inputs_same_partition(self):
        r1 = compare_variants("Base_Pop_Severe_ED_Scores",
                              family_kql(THREE_PROCS))
        r2 = compare_variants("Base_Pop_Severe_ED_Scores",
                              family_kql(THREE_PROCS))
        assert r1 == r2


class TestFacts:
    def test_divergent_facts_carry_groups_and_diff(self):
        fs = variants_answer("Base_Pop_Severe_ED_Scores",
                             family_kql(THREE_PROCS))
        assert fs.kind == "variants"
        assert fs.facts["all_agree"] == "no"
        assert fs.facts["distinct_definitions"] == 2
        assert "reports.USP_IP_SEPSIS" in fs.facts["definition_2_used_by"]
        assert "SCORE >= 3" in fs.facts["diff_definition_1_vs_2"]
        assert fs.basis.startswith("semantic_catalog[step name=")

    def test_consistent_facts_expose_the_shared_sql(self):
        fs = variants_answer("Base_Pop_Severe_ED_Scores",
                             family_kql(THREE_PROCS[:2]))
        assert fs.facts["all_agree"] == "yes"
        assert fs.facts["sql_fragment"] == SQL_A   # representative original

    def test_single_member_family_is_an_answer_not_an_error(self):
        fs = variants_answer("Base_Pop_Severe_ED_Scores",
                             family_kql(THREE_PROCS[:1]))
        assert "nothing to compare" in fs.facts["all_agree"]


class TestCliVariantsFlow:
    def drive(self, replies, chat, run_kql, tmp_path):
        from src.orchestrator.cli import chat_loop
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        out = []
        say = lambda *a: out.append(" ".join(str(x) for x in a))
        it = iter(replies)
        chat_loop(chat, run_kql, sink, ask=lambda p="": next(it), say=say)
        return "\n".join(out)

    def chat(self, system, user):
        if "VARIANTS" in system:      # entry edge (intent prompt)
            return "VARIANTS: #Base_Pop_Severe_ED_Scores"
        return "No — 2 of 3 procs agree; reports.USP_IP_SEPSIS differs."

    def test_sunny_family_question_no_pick_menu(self, tmp_path):
        text = self.drive(
            ["are they all using the same definition of "
             "#Base_Pop_Severe_ED_Scores", "q"],
            self.chat, family_kql(THREE_PROCS), tmp_path)
        assert "reports.USP_IP_SEPSIS differs" in text
        assert "Pick a number" not in text          # set-subject: no pick
        assert "-> 2 distinct" in text              # code-stamped basis

    def test_sunny_pairwise_question_same_verb(self, tmp_path):
        seen = {}
        def chat(system, user):
            if "VARIANTS" in system:
                return "VARIANTS: Base_Pop_Severe_ED_Scores"
            seen["narrate_user"] = user
            return "No — their definitions differ on the score threshold."
        text = self.drive(
            ["is reporting.USP_ED_Sepsis using the same "
             "Base_Pop_Severe_ED_Scores logic as reports.USP_IP_SEPSIS?",
             "q"],
            chat, family_kql(THREE_PROCS), tmp_path)
        assert "differ on the score threshold" in text
        # the narrate edge received the user's actual question for framing
        assert "reports.USP_IP_SEPSIS" in seen["narrate_user"]
        assert "ONLY these facts" in seen["narrate_user"]

    def test_followup_sql_shows_each_definition(self, tmp_path):
        text = self.drive(
            ["are they all using the same definition of "
             "#Base_Pop_Severe_ED_Scores", "show me its sql", "q"],
            self.chat, family_kql(THREE_PROCS), tmp_path)
        assert "definition 1 sql" in text and "definition 2 sql" in text
        assert "SCORE >= 3" in text
        assert "(cached from your last answer)" in text

    def test_misfired_classification_degrades_to_search(self, tmp_path):
        def chat(system, user):
            if "VARIANTS" in system:
                return "VARIANTS: Ghost_Step"
            return "Prose."
        def run_kql(query, params):
            if query == FAMILY_QUERY:
                return []
            from src.orchestrator.core import RESOLVE_QUERY
            assert query == RESOLVE_QUERY
            return []
        text = self.drive(["do ghosts agree?", "q"], chat, run_kql, tmp_path)
        assert "searching instead" in text
        assert "Nothing in the certified knowledge base" in text
