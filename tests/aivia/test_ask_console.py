"""Tier A exit (ADR 0079): the F10 answer keys go RUNNABLE.

The interpreter and embedder are INJECTED fakes — CI never calls a
model; the cage, the tiers, the connect engine, the ledger, and the
never-regex law are what's proven. The live finds from Sunny's first
testing session stand as corpses under the new pipeline.

Proves: contract:aivia-design-to-code
"""
import hashlib
import json
import pathlib
import re

import pytest

from aivia.flows import ask, grounding
from aivia.graph.read_api import ReadApi
from aivia.lenses import ask_index

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
CASES = json.loads((FIX / "F10_interpreter" / "cases.json").read_text())
T0 = "2026-09-06T12:00:00Z"


def fake_embed(texts):
    """Deterministic bag-of-words hashing: shared words -> nearby
    vectors — enough semantics to prove the tier, zero network."""
    out = []
    for text in texts:
        vec = [0.0] * 64
        for word in re.sub(r"[^a-z0-9 ]", " ", text.lower()).split():
            vec[int(hashlib.sha256(word.encode()).hexdigest(), 16)
                % 64] += 1.0
        out.append(vec)
    return out


def fake_interpreter(mapping):
    def interpret(question):
        return mapping.get(" ".join(question.split()).lower(),
                           {"mentions": [question]})
    return interpret


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _base = build_store("sepsis")
    read = ReadApi(store)
    entries = ask_index.lens_ask_index(read, None)["yield"]
    semantic = grounding.SemanticIndex(entries, fake_embed,
                                       "fake-64", cache_path=None)
    return store, semantic


def _ask(world, q, interpret=None):
    store, semantic = world
    return ask.ask(store, q, "person:test", T0,
                   interpret_fn=interpret, semantic=semantic)


# ---- GR: grounding ---------------------------------------------------
def test_gr1_exact_tier_is_model_free(world):
    store, semantic = world
    calls = []

    def exploding_interpreter(q):
        calls.append(q)
        raise AssertionError("model called for an exact name")
    result = ask.ask(store, "THERA_CLASS_CODE", "person:test", T0,
                     interpret_fn=exploding_interpreter,
                     semantic=semantic)
    assert result["status"] == "answer"
    assert result["via"] == "deterministic"
    assert calls == []
    assert "therapeutic class" in result["answer"]


def test_gr3_kind_words_ground_to_kind_sets(world):
    result = _ask(world, "tables")
    assert result["status"] == "answer"
    assert result["answer"].startswith("90 table(s):")


def test_gr4_vectors_stamped_and_cached(tmp_path, world):
    store, _ = world
    read = ReadApi(store)
    entries = ask_index.lens_ask_index(read, None)["yield"][:20]
    cache = tmp_path / "emb.json"
    first = grounding.SemanticIndex(entries, fake_embed, "fake-64",
                                    cache_path=cache)
    assert first.embedded_now == 20

    def forbidden(texts):
        raise AssertionError("re-embedded an unchanged meaning")
    second = grounding.SemanticIndex(entries, forbidden, "fake-64",
                                     cache_path=cache)
    assert second.embedded_now == 0  # unchanged -> never re-embeds


# ---- CN: connect -----------------------------------------------------
def test_cn2_kind_plus_topic_the_live_find_dies(world):
    store, semantic = world
    interp = fake_interpreter({
        "what reports are about sepsis":
            {"mentions": ["reports", "sepsis"]}})
    result = _ask(world, "what reports are about sepsis", interp)
    assert result["status"] == "confirm"  # fresh model parse -> HITL
    final = ask.confirm(store, "what reports are about sepsis",
                        result["interpretation"], "person:test", T0,
                        semantic=semantic)
    assert final["status"] == "answer"
    # live find #5 (Sunny: "is 21 correct? I thought 28"): every one
    # of the 28 corpus files carries Sepsis in its name — name
    # containment runs over the WHOLE kind, never a truncated pool,
    # and the answer states which tier found what
    assert "28 file(s) about" in final["answer"]
    assert "(28 by name, 0 more by meaning)" in final["answer"]
    assert "USP_ED_SEPSIS" in final["answer"]
    assert "USP_IP_SepsisEncountersWLocations" in final["answer"]
    assert "USP_RPTS_NonSevere_Sepsis" in final["answer"]


def test_cn1_two_mentions_connect_and_speak(world):
    store, semantic = world
    q = "how does THERA_CLASS_CODE relate to USP_ED_SEPSIS"
    interp = fake_interpreter({
        q.lower(): {"mentions": ["THERA_CLASS_CODE",
                                 "reporting/USP_ED_SEPSIS.sql"]}})
    first = _ask(world, q, interp)
    assert first["status"] == "confirm"
    final = ask.confirm(store, q, first["interpretation"],
                        "person:test", T0, semantic=semantic)
    assert final["status"] == "answer"
    assert "connects to" in final["answer"]
    assert "hop(s))" in final["answer"]


def test_cn3_single_mention_neighborhood(world):
    result = _ask(world, "emr|dbo|ED_ENCOUNTERS_DM")
    assert result["status"] == "answer"
    assert "Connected:" in result["answer"]


def test_metric_two_layer_answer_survives(world):
    result = _ask(world, "metrics")
    assert "GOVERNED metrics (minted concepts): 0" in result["answer"]
    assert "PRACTICED metrics" in result["answer"]
    assert "::delivery" in result["answer"]


# ---- ST: steer -------------------------------------------------------
def test_st1_ambiguity_clarifies_with_candidates(world):
    result = _ask(world, "MEDICATION_ID")
    assert result["status"] == "clarify"
    assert len(result["candidates"]) >= 2
    picked = _ask(world, result["candidates"][0]["identity"])
    assert picked["status"] == "answer"


# ---- RM: remember ----------------------------------------------------
def test_rm1_confirmed_interpretation_skips_the_model(world):
    store, semantic = world
    q = "which procedures mention sepsis"
    interp = fake_interpreter(
        {q: {"mentions": ["procedures", "sepsis"]}})
    first = ask.ask(store, q, "person:test", T0,
                    interpret_fn=interp, semantic=semantic)
    assert first["status"] == "confirm"
    ask.confirm(store, q, first["interpretation"], "person:test", T0,
                semantic=semantic)

    def exploding(qq):
        raise AssertionError("model called on a ledger hit")
    again = ask.ask(store, q, "person:test", T0,
                    interpret_fn=exploding, semantic=semantic)
    assert again["status"] == "answer"
    assert again["via"] == "ledger"


def test_rm_cage_rejects_bad_interpretations(world):
    store, semantic = world
    for bad in ({"mentions": []}, {"answer": "42"},
                {"mentions": ["a"] * 9}, "not a dict"):
        result = ask.ask(store, "zzz unfindable question",
                         "person:test", T0,
                         interpret_fn=lambda q, b=bad: b,
                         semantic=semantic)
        assert result["status"] == "form"  # refused, never guessed


# ---- LW: the never-regex census -------------------------------------
def test_lw1_no_regex_touches_question_text():
    """The law's census over the question-receiving module: the
    grammar is DELETED, not hidden — ask.py contains no regex at
    all; mechanical string-tool regex elsewhere stays legal."""
    source = (pathlib.Path(__file__).resolve().parents[2]
              / "aivia" / "flows" / "ask.py").read_text()
    assert "import re" not in source
    assert "_OP_GRAMMAR" not in source


def test_usage_events_h5_shapes(world):
    store, _ = world
    events = store.current_nodes("usage")
    assert events, "every ask lands an event"
    for e in events:
        if e.properties.get("action") == "asked":
            assert e.properties["outcome"] in ("matched", "ambiguous",
                                               "no-match")
            if e.properties["outcome"] != "matched":
                assert e.properties.get("about") is None


# ---- SF: the seat-failure law (live find #6, ADR 0079 Law 3) --------
def test_sf1_exploding_interpreter_is_an_outcome_not_a_crash(world):
    store, semantic = world

    def exploding(q):
        raise RuntimeError("429 rate limit")
    result = ask.ask(store, "zz some novel free text question zz",
                     "person:test", T0, interpret_fn=exploding,
                     semantic=semantic)
    assert result["status"] == "form"       # degraded, never dead
    assert result.get("seat_down") is True  # countable, bannerable
    assert "unavailable" in result["answer"].lower()


def test_sf2_exploding_embedder_degrades_semantic_tier_only(world):
    store, _ = world
    read = ReadApi(store)
    entries = ask_index.lens_ask_index(read, None)["yield"]
    built = grounding.SemanticIndex(entries, fake_embed, "fake-64",
                                    cache_path=None)

    def explode(texts):
        raise RuntimeError("embed seat down")
    built.embed_fn = explode  # the QUERY embed now fails
    result = ask.ask(store, "zz nothing matches this zz",
                     "person:test", T0, interpret_fn=None,
                     semantic=built)
    assert result["status"] in ("form", "answer")  # never an exception
    # and a deterministic ask through the same broken index still works
    ok = ask.ask(store, "THERA_CLASS_CODE", "person:test", T0,
                 interpret_fn=None, semantic=built)
    assert ok["status"] == "answer" and ok["via"] == "deterministic"


def test_sf3_deterministic_asks_immune_to_model_weather(world):
    store, _ = world

    def explode_i(q):
        raise RuntimeError("down")
    result = ask.ask(store, "tables", "person:test", T0,
                     interpret_fn=explode_i, semantic=None)
    assert result["status"] == "answer"
    assert result["answer"].startswith("90 table(s):")


# ---- FU: follow-up context (Law 4, live find #7) --------------------
def test_fu2_it_takes_the_single_subject(world):
    store, semantic = world
    first = ask.ask(store, "emr|dbo|ED_ENCOUNTERS_DM", "person:test",
                    T0, semantic=semantic)
    assert first["status"] == "answer"
    assert first["context_set"]  # every answer yields its context
    follow = ask.ask(store, "it", "person:test", T0,
                     semantic=semantic,
                     context=first["context_set"])
    assert follow["status"] == "answer"
    assert "ED_ENCOUNTERS_DM" in follow["answer"]


def test_fu1_those_filters_by_connection(world):
    store, semantic = world
    first = ask.ask(store, "emr|dbo|ADT_EVENTS|ENCOUNTER_ID",
                    "person:test", T0, semantic=semantic)
    assert first["status"] == "answer"
    context = first["context_set"]
    assert any("::" in c for c in context)  # the citing scopes rode in
    q = "which of those are in the ED sepsis report"
    interp = fake_interpreter({q.lower(): {"mentions":
        ["those", "reports/USP_RPTS_ED_Sepsis.sql"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic,
                     context=context)
    assert result["status"] == "confirm"
    final = ask.confirm(store, q, result["interpretation"],
                        "person:test", T0, semantic=semantic,
                        context=context)
    assert final["status"] == "answer"
    assert "USP_RPTS_ED_Sepsis" in final["answer"]
    assert "USP_IP_SEPSIS.sql" not in final["answer"]  # filtered OUT


def test_fu3_ordinals_index_the_context(world):
    store, semantic = world
    first = ask.ask(store, "emr|dbo|ADT_EVENTS|ENCOUNTER_ID",
                    "person:test", T0, semantic=semantic)
    context = first["context_set"]
    follow = ask.ask(store, "the first one", "person:test", T0,
                     semantic=semantic, context=context)
    assert follow["status"] == "answer"
    deep = ask.ask(store, "the tenth one", "person:test", T0,
                   semantic=semantic, context=context[:3])
    assert deep["status"] == "clarify"  # out of range -> honest


def test_fu5_empty_context_is_honest(world):
    store, semantic = world
    result = ask.ask(store, "those", "person:test", T0,
                     semantic=semantic, context=None)
    assert result["status"] == "clarify"
    assert "refer back" in str(result.get("answer", "")).lower() \
        or "refer back" in str(result.get("mention", "")).lower() \
        or result.get("reason") == "no-context"


def test_fu4_confirmed_followups_store_context_snapshot(world):
    store, semantic = world
    first = ask.ask(store, "emr|dbo|ADT_EVENTS|ENCOUNTER_ID",
                    "person:test", T0, semantic=semantic)
    q = "show those again please"
    interp = fake_interpreter({q: {"mentions": ["those"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic,
                     context=first["context_set"])
    assert result["status"] == "confirm"
    ask.confirm(store, q, result["interpretation"], "person:test",
                T0, semantic=semantic, context=first["context_set"])
    # the ledger replays WITHOUT live context: the snapshot rides
    def exploding(qq):
        raise AssertionError("model called on a ledger hit")
    again = ask.ask(store, q, "person:test", T0,
                    interpret_fn=exploding, semantic=semantic,
                    context=None)
    assert again["status"] == "answer" and again["via"] == "ledger"
