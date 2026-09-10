"""THE LIVE TIER — the live-seat rule (Sunny's ruling, 2026-09-09):
wherever production calls a model, a live test calls the SAME model
— same seat, same registry prompt, same estate. This tier proves
what no deterministic test can: that today's actual model produces
proposals and vectors the pipeline handles lawfully (the 'ED → term'
over-marking was invisible to every deterministic test and only
surfaced live).

Run: AIVIA_LIVE=1 pytest tests/live -v   (needs OPENAI_API_KEY in
.env). CI skips this tier by design — a red build must mean broken
code, never a flaky seat or a missing key — and the skip is VISIBLE
in CI output, never silent. I run it locally before any 'done'.

Assertions pin LAWS, not verbatim model output: live models vary in
wording; they must never vary in lawfulness.

Proves: contract:aivia-design-to-code
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("AIVIA_LIVE"),
    reason="live seat tests run with AIVIA_LIVE=1 (the live-seat rule)")

T0 = "2026-09-09T12:00:00Z"


@pytest.fixture(scope="module")
def live_world(tmp_path_factory):
    from aivia.console import EMBEDDING_MODEL, _env_key, build_store, make_embedder, make_interpreter
    from aivia.flows import ask, grounding
    from aivia.graph.read_api import ReadApi
    key = _env_key()
    assert key, "OPENAI_API_KEY missing — the live tier needs it"
    import pathlib
    est = (pathlib.Path(__file__).resolve().parents[2]
           / "AIVIA_Product" / "estates" / "sepsis")
    # the REAL journal: blessed acronyms and every other user
    # decision replay into the live world, exactly as prod boots
    store, base = build_store(
        "sepsis", journal_path=est / "governance" / "journal.jsonl")
    read = ReadApi(store)
    entries = ask.build_index(read)
    semantic = grounding.SemanticIndex(
        entries, make_embedder(key), EMBEDDING_MODEL,
        cache_path=base / ".cache" / "embeddings.json")
    # the interpreter runs UNCACHED — live means today's model, not
    # a remembered proposal
    interpret = make_interpreter(key, cache_path=None)
    return store, semantic, interpret


def _ask(live_world, q):
    from aivia.flows import ask
    store, semantic, interpret = live_world
    return ask.ask(store, q, "person:live-test", T0,
                   interpret_fn=interpret, semantic=semantic)


def test_the_payoff_question_live(live_world):
    """'what reports are about ED' — the question that found the
    over-mark veto (22:27 screenshot) and drove the PBI payoff pin.
    Live law: it answers, and the ED sepsis dashboard is in the
    hits with PBI reports present."""
    r = _ask(live_world, "what reports are about ED")
    assert r["status"] == "answer", r.get("answer") or r
    labels = {h["label"] for h in r["hits"]}
    assert "pbi_report" in labels, sorted(labels)
    names = " ".join(h["name"].lower() for h in r["hits"])
    assert "sepsis" in names and "dashboard" in names


def test_the_overmark_corpse_stays_dead_live(live_world):
    """Whatever today's model marks as a reference, a first question
    with real hits NEVER dies in a clarify veto — role-marks are
    proposals (the 2026-09-08 ruling)."""
    r = _ask(live_world, "what reports are about ED")
    assert r["status"] != "clarify"
    assert r["hits"], "the search returned nothing for a real topic"


def test_the_interpreter_contract_shape_live(live_world):
    """The real seat, the registry prompt, one canonical question:
    the caged proposal carries non-empty mentions and no 'kinds'
    (the cage strips what the law killed)."""
    from aivia.flows import ask
    _store, _semantic, interpret = live_world
    proposal = ask.validate_interpretation(
        interpret("which tables hold antibiotic orders"))
    assert proposal["mentions"]
    assert "kinds" not in proposal


def test_blessed_acronyms_expand_live(live_world):
    """The one-vocabulary law with the real seats: a question
    saying only 'ED' searches the blessed expansions too — visible
    in the trace's searched_as."""
    from aivia.graph.read_api import ReadApi
    store, _semantic, _interpret = live_world
    blessed = {n.properties["name"].lower()
               for n in ReadApi(store).nodes("acronym")}
    if "ed" not in blessed:
        pytest.skip("no blessed ED acronym in this estate build")
    r = _ask(live_world, "things about ED")
    row = next((t for t in r["trace"]
                if t["mention"].lower() == "ed"), None)
    assert row is not None
    assert "emergency department" in row["searched_as"].lower()
