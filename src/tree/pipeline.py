"""The round trip — ADR 0044 clause 6 and spec §13's law:

    ACCEPT(desc) ⟺ κ(ρ(τ(tree))) = κ(tree)

Bounded bounces with the diff named to the translator; exhausted
retries degrade to the deterministic template — the system's worst
output is stilted truth, never hope. Every result carries provenance
from the closed set {round_trip_verified, template_fallback, flagged}
(spec:B2). Fabrication has no constructible path: the translator can't
copy an error from SQL it never sees (clause 2), a sympathetic judge
can't wave one through (clauses 3+4), silence is counted (clause 5),
and exhaustion degrades to truth (this module).
"""

from __future__ import annotations

from src.tree.diff import tree_diff
from src.tree.extract import DecisionTree
from src.tree.render import render_template
from src.tree.translate import translate_tree, tree_facts
from src.tree.verify import build_reconstruction_prompt, parse_reconstruction

PROVENANCE = ("round_trip_verified", "template_fallback", "flagged")


def verified_describe(tree: DecisionTree, dict_lines: "list[str]",
                      translator, reconstructor, max_rounds: int = 3,
                      name: str = "step",
                      deps: "list[tuple[str, str]] | None" = None,
                      ) -> "tuple[str, str]":
    """τ → ρ → deterministic judge, bounced up to max_rounds.

    Returns (text, provenance). A projection-only step (no facts) is
    template text by construction — verified vacuously."""
    facts = tree_facts(tree)
    if not facts:
        return render_template([], step_name=name), "round_trip_verified"

    feedback = ""
    for _ in range(max_rounds):
        def describe(prompt, _fb=feedback):
            return translator(prompt + _fb)
        tr = translate_tree(tree, dict_lines, describe, name=name, deps=deps)
        recon = parse_reconstruction(
            reconstructor(build_reconstruction_prompt(tr.text, dict_lines)))
        diffs = tree_diff(facts, recon)
        if not diffs:
            return tr.text, "round_trip_verified"
        feedback = (
            "\n\nYour previous translation FAILED blind verification — a "
            "reader reconstructed different decisions than the facts "
            "state:\n- " + "\n- ".join(diffs[:10])
            + "\nRewrite so every numbered decision is unambiguous."
        )
    return render_template(facts, step_name=name), "template_fallback"


def provenance_fallout_row(node_id: str, provenance: str,
                           run_at: str = "") -> dict:
    """A non-verified description is escalation material (ADR 0045 §3:
    novelty always escalates — 'flagged' means neither the model nor
    the code could resolve it)."""
    return {
        "run_at": run_at,
        "stage": "600_provenance",
        "entity_id": node_id,
        "reason_code": f"description_{provenance}",
        "reason_text": (
            "description did not round-trip verify; published as "
            f"{provenance} (ADR 0044 clause 6)"),
        "contract_id": "contract:graph_nodes",
        "resolution": ("escalated" if provenance == "flagged"
                       else "auto_resolved"),
    }
