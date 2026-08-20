"""The admin companion (ADR 0048 item 4): facts from registries, a
diagnosis that is a path of real admin-graph edges, an LLM that can
only rephrase — never decide (E3/E6)."""

import pytest

from src.admin_graph import build_admin_graph
from src.companion import diagnose, explain_step, step_explanation_lines


class TestExplainStep:
    def test_projects_requirements_producers_and_products(self):
        info = explain_step("300_build_graph")
        req_tables = {r["table"] for r in info["requires"]}
        assert "input_dict_tables" in req_tables
        producer = next(r["producer"] for r in info["requires"]
                        if r["table"] == "input_dict_tables")
        assert producer == "040_dict_clarity"
        produced = {p["table"] for p in info["produces"]}
        assert "graph_nodes" in produced and "graph_decision_sites" in produced
        assert "precondition_gate" in info["gates"]

    def test_lines_are_admin_readable(self):
        lines = step_explanation_lines(explain_step("500_validate"))
        text = "\n".join(lines)
        assert text.startswith("500_validate — ")
        assert "Needs before it runs:" in text

    def test_unknown_step_answers_with_the_list_not_a_trace(self):
        with pytest.raises(KeyError, match="known steps: .*300_build_graph"):
            explain_step("305_build_graf")


class TestDiagnose:
    def _graph(self, error_rows=None):
        return build_admin_graph(error_rows=error_rows)

    def test_diagnosis_is_a_path_of_real_edges(self):
        g = self._graph()
        row = {"reason_text": "input_dict_tables is missing column(s) ORIGIN",
               "contract_id": "contract:input_dict_tables"}
        d = diagnose(row, g.nodes_rows, g.edges_rows)
        assert d["found"]
        real = {(e["source_id"], e["target_id"]) for e in g.edges_rows}
        for src, kind, dst in d["hops"]:
            if kind == "produced_by":  # walked against the produces edge
                assert (dst, src) in real
            else:
                assert (src, dst) in real
        text = "\n".join(d["caption_lines"])
        assert "040_dict_clarity" in text
        assert "Symptom: input_dict_tables is missing column(s) ORIGIN" in text
        assert "ADR" in text  # the decision behind the check is cited

    def test_unmatched_contract_escalates_never_guesses(self):
        g = self._graph()
        d = diagnose({"reason_code": "weird", "contract_id": "contract:nope"},
                     g.nodes_rows, g.edges_rows)
        assert not d["found"] and not d["hops"]
        assert "novelty escalates" in "\n".join(d["caption_lines"])

    def test_narrate_receives_facts_and_ships_beside_caption(self):
        g = self._graph()
        seen = {}

        def narrate(prompt):
            seen["prompt"] = prompt
            return "In plain words: rerun the dictionary loader."

        row = {"reason_text": "gate failure",
               "contract_id": "contract:input_dict_tables"}
        d = diagnose(row, g.nodes_rows, g.edges_rows, narrate=narrate)
        assert "changing no facts" in seen["prompt"]
        assert "040_dict_clarity" in seen["prompt"]  # facts, not the question
        assert d["narrative"].startswith("In plain words")
        assert d["caption_lines"]  # deterministic caption always ships

    def test_narration_failure_never_kills_the_diagnosis(self):
        g = self._graph()

        def broken(prompt):
            raise RuntimeError("llm down")

        d = diagnose({"contract_id": "contract:input_dict_tables"},
                     g.nodes_rows, g.edges_rows, narrate=broken)
        assert d["found"] and d["narrative"] is None
