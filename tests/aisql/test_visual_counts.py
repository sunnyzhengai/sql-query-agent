"""FS1 — the graph visual's counts-vs-key re-verify (ruled by
Sunny "a", 2026-09-17; Contract_Surfaces FS1; rides M5, landing
BEFORE the batch's republish).

The visual was the ONLY live surface with no automated re-verify:
counts were checked by eye at each republish — the F2 failure
class (a consumer silently dropping data with no test watching).
This pin runs the generator's own counting step and holds it to
the answer key; the eye keeps layout, readability, and card text.

Proves: contract:aisql-design-to-code
"""
import importlib.util
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
KEY = json.loads(
    (REPO / "AIVIA_Product" / "estates" / "ed_sepsis_dev"
     / "expected_m_gates.json").read_text())


def _generator():
    spec = importlib.util.spec_from_file_location(
        "generate_m1",
        REPO / "devtools" / "graph_visual" / "generate_m1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_visual_counts_match_the_answer_key():
    mod = _generator()
    counts = mod.build_payload()["counts"]
    want = KEY["census_after"]["M6"]
    assert counts["nodes"] == want["nodes"]
    assert sum(counts["edges"].values()) \
        == sum(want["edges"].values())
