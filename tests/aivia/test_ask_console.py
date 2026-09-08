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


VOCAB = {"tables": "table", "table": "table", "reports": "file",
         "report": "file", "files": "file", "columns": "column",
         "metrics": "metric", "selections": "scope",
         "scopes": "scope", "terms": "term", "drift": "drift",
         "procedures": "file"}


def seed_vocabulary(store):
    """The post-cold-start estate: kind words EARNED as confirmed
    terms (parent kind::K), each citing the steward's seeding act —
    the birth-edge law holds even for fixtures (step 2)."""
    from aivia.graph import kg3_artifacts
    kg3_artifacts.append_usage(store, "confirmed", "person:steward",
                               T0, payload="vocabulary seeding act")
    act = store.current_nodes("usage")[-1]
    for word, kind in VOCAB.items():
        kg3_artifacts.append_term(
            store, f"term::vocab/{word.upper()}", word,
            f"a word for the {kind} kind of node",
            "person:steward", T0, parent=f"kind::{kind}",
            derived_from=[act.identity])


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _base = build_store("sepsis")
    seed_vocabulary(store)
    read = ReadApi(store)
    entries = ask.build_index(read)
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
    # facet cards: 1-2 vectors per entry (name + speech when present)
    assert 20 <= first.embedded_now <= 40

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
    assert result["status"] == "answer"
    assert result["pending_confirmation"]  # L7-D2: inline, non-blocking  # fresh model parse -> HITL
    final = ask.confirm(store, "what reports are about sepsis",
                        result["interpretation"], "person:test", T0,
                        semantic=semantic)
    assert final["status"] == "answer"
    # live find #5 (Sunny: "is 21 correct? I thought 28"): every one
    # of the 28 corpus files carries Sepsis in its name — name
    # containment runs over the WHOLE kind, never a truncated pool,
    # and the answer states which tier found what
    assert "28 file(s) about" in final["answer"]
    # header extended by ADR 0080: the facet bucket joins the
    # provenance (same truth, one more counted tier)
    assert "(28 by name, 0 more by meaning, 0 via their parts)" \
        in final["answer"]
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
    assert first["status"] == "answer"
    assert first["pending_confirmation"]  # L7-D2: inline, non-blocking
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
    # a UNIQUE reference-set (the meaning-book would otherwise
    # answer immediately for meanings other tests confirmed)
    q = "which procedures mention the sepsis dates proc"
    interp = fake_interpreter(
        {q: {"mentions": ["procedures", "USP_IP_SepsisDates"]}})
    first = ask.ask(store, q, "person:test", T0,
                    interpret_fn=interp, semantic=semantic)
    assert first["status"] == "answer"
    assert first["pending_confirmation"]  # L7-D2: inline, non-blocking
    ask.confirm(store, q, first["interpretation"], "person:test", T0,
                semantic=semantic)

    def exploding(qq):
        raise AssertionError("model called on a ledger hit")
    again = ask.ask(store, q, "person:test", T0,
                    interpret_fn=exploding, semantic=semantic)
    assert again["status"] == "answer"
    assert again["via"] == "ledger"


def test_rm3_meaning_book_new_phrasing_same_meaning(world):
    store, semantic = world
    # L2-D1: confirmation attaches to the REFERENCE-SET — a new
    # phrasing resolving to a confirmed meaning answers immediately,
    # no model re-confirm (the phrasebook became a meaning-book)
    q1 = "list procedures about the sepsis dates proc"
    i1 = fake_interpreter(
        {q1: {"mentions": ["procedures", "USP_IP_SepsisDates"]}})
    r1 = ask.ask(store, q1, "person:test", T0,
                 interpret_fn=i1, semantic=semantic)
    assert r1["via"] in ("meaning-book", "model")
    if r1.get("pending_confirmation"):
        ask.confirm(store, q1, r1["interpretation"], "person:test",
                    T0, semantic=semantic)
    q2 = "show me procs concerning the sepsis dates procedure"
    i2 = fake_interpreter(
        {q2: {"mentions": ["procedures", "USP_IP_SepsisDates"]}})
    r2 = ask.ask(store, q2, "person:test", T0,
                 interpret_fn=i2, semantic=semantic)
    assert r2["status"] == "answer"
    assert r2["via"] == "meaning-book"
    assert not r2.get("pending_confirmation")


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
    ref = fake_interpreter({"it": {"mentions": ["it"],
                                   "references": {"it": "singular"}}})
    follow = ask.ask(store, "it", "person:test", T0,
                     interpret_fn=ref, semantic=semantic,
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
        ["those", "reports/USP_RPTS_ED_Sepsis.sql"],
        "references": {"those": "set"}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic,
                     context=context)
    assert result["status"] == "answer"
    assert result["pending_confirmation"]  # L7-D2: inline, non-blocking
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
    ref1 = fake_interpreter({"the first one": {
        "mentions": ["the first one"],
        "references": {"the first one": "ordinal:1"}}})
    follow = ask.ask(store, "the first one", "person:test", T0,
                     interpret_fn=ref1, semantic=semantic,
                     context=context)
    assert follow["status"] == "answer"
    ref10 = fake_interpreter({"the tenth one": {
        "mentions": ["the tenth one"],
        "references": {"the tenth one": "ordinal:10"}}})
    deep = ask.ask(store, "the tenth one", "person:test", T0,
                   interpret_fn=ref10, semantic=semantic,
                   context=context[:3])
    assert deep["status"] == "clarify"  # out of range -> honest


def test_fu5_empty_context_is_honest(world):
    store, semantic = world
    ref = fake_interpreter({"those": {
        "mentions": ["those"], "references": {"those": "set"}}})
    result = ask.ask(store, "those", "person:test", T0,
                     interpret_fn=ref, semantic=semantic,
                     context=None)
    assert result["status"] == "clarify"
    assert "refer back" in str(result.get("answer", "")).lower() \
        or "refer back" in str(result.get("mention", "")).lower() \
        or result.get("reason") == "no-context"


def test_fu4_confirmed_followups_store_context_snapshot(world):
    store, semantic = world
    first = ask.ask(store, "emr|dbo|ADT_EVENTS|ENCOUNTER_ID",
                    "person:test", T0, semantic=semantic)
    q = "show those again please"
    interp = fake_interpreter({q: {"mentions": ["those"],
                                   "references": {"those": "set"}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic,
                     context=first["context_set"])
    assert result["status"] == "answer"
    assert result["pending_confirmation"]  # L7-D2: inline, non-blocking
    ask.confirm(store, q, result["interpretation"], "person:test",
                T0, semantic=semantic, context=first["context_set"])
    # the ledger replays WITHOUT live context: the snapshot rides
    def exploding(qq):
        raise AssertionError("model called on a ledger hit")
    again = ask.ask(store, q, "person:test", T0,
                    interpret_fn=exploding, semantic=semantic,
                    context=None)
    assert again["status"] == "answer" and again["via"] == "ledger"


# ---- CS: the conversation surface (find #7 second leg) --------------
@pytest.fixture()
def surface(world):
    """The REAL console server on an ephemeral port, model-free —
    the surface itself is what's under test."""
    import threading
    from http.server import ThreadingHTTPServer

    from aivia import console
    store, semantic = world
    calls = []

    def recording_interpreter(question):
        calls.append(question)
        if question.strip().lower() == "it":
            return {"mentions": ["it"],
                    "references": {"it": "singular"}}
        return {"mentions": ["sepsis"]}

    handler = console.make_handler(store, "sepsis",
                                   recording_interpreter, semantic, {})
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", calls
    srv.shutdown()


def _round(base, **params):
    import urllib.parse
    import urllib.request
    url = base + "/round?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def test_cs1_context_is_conversation_scoped(surface):
    base, _calls = surface
    first = _round(base, q="emr|dbo|ED_ENCOUNTERS_DM", c="conv-a")
    assert first["status"] == "answer"
    assert first["context_set"]
    # conversation B never sees A's context
    other = _round(base, q="it", c="conv-b")
    assert other["status"] == "clarify"
    # conversation A resolves its own anaphor
    follow = _round(base, q="it", c="conv-a")
    assert follow["status"] == "answer"
    assert "ED_ENCOUNTERS_DM" in follow["html"]


def test_cs2_rounds_are_data_page_is_a_shell(surface):
    base, _calls = surface
    import urllib.request
    with urllib.request.urlopen(base + "/", timeout=10) as r:
        shell = r.read().decode()
    # the shell is a transcript surface: a log to append to, a form
    # the client intercepts — never a server-rendered answer
    assert 'id="log"' in shell or "id=log" in shell
    assert "fetch(" in shell
    result = _round(base, q="tables", c="conv-c")
    assert set(result) >= {"status", "html", "context_set"}
    assert result["status"] == "answer"


def test_cs3_the_cage_holds_at_the_surface(surface):
    base, calls = surface
    _round(base, q="emr|dbo|ED_ENCOUNTERS_DM", c="conv-d")
    q2 = "what sepsis things exist here"
    _round(base, q=q2, c="conv-d")
    # the interpreter saw ONE question, verbatim — no prior answer
    # text, no transcript (the cage holds at the surface)
    assert calls == [q2]


# ---- GR-5/6 + CN-5: the path tier and the report floor (finds #8/#9)
def test_gr5_path_tier_decorated_names_never_guess(world):
    store, _semantic = world
    read = ReadApi(store)
    index = ask.build_index(read)
    kinds = ask._earned_vocabulary(ReadApi(store))
    # semantic=None: if these fell past the deterministic tiers they
    # would come back unknown — the .sql decoration never demotes an
    # exact ask to the guessing tier (live find #8)
    for mention in ("USP_ED_SEPSIS.sql",
                    "reporting/USP_ED_SEPSIS.sql"):
        g = grounding.ground(mention, index, kinds, None)
        assert g["outcome"] == "matched", mention
        assert g["tier"] == "path"
        assert g["entity"]["identity"].endswith(
            "reporting/USP_ED_SEPSIS.sql")


def test_gr5_ambiguous_suffix_is_candidates_never_a_pick():
    index = [
        {"kind": "file", "identity": "repo://a/x/FOO.sql",
         "name": "FOO", "folded": "FOO", "words": ""},
        {"kind": "file", "identity": "repo://b/x/FOO.sql",
         "name": "FOO", "folded": "FOO", "words": ""},
    ]
    g = grounding.ground("x/FOO.sql", index, {}, None)
    assert g["tier"] == "path"
    assert g["outcome"] == "candidates"
    assert len(g["candidates"]) == 2


def test_gr6_files_embed_meaning_not_names(world):
    store, _semantic = world
    read = ReadApi(store)
    index = ask.build_index(read)
    files = [e for e in index if e["kind"] == "file"]
    assert files
    target = next(e for e in files
                  if e["identity"].endswith(
                      "reporting/USP_ED_SEPSIS.sql"))
    # the file's words are its report floor's delivery lead — never
    # empty, never the bare name (find #8's 0.05-band noise dies)
    assert target["words"]
    assert "selection" in target["words"] or "record" in target["words"]


def test_cn5_the_report_floor_speaks_meaning(world):
    store, semantic = world
    result = ask.ask(store, "reporting/USP_ED_SEPSIS.sql",
                     "person:test", T0, semantic=semantic)
    assert result["status"] == "answer"
    answer = result["answer"]
    # deliveries lead — never census-first
    assert not answer.split("\n")[2].startswith("A procedure of")
    low = answer.lower()
    assert "deliver" in low
    # the spine: base selections voiced, intermediates COUNTED
    assert "selection" in low
    assert "intermediate" in low
    # the census closes (honest mechanics, last)
    assert "67 steps" in answer
    assert answer.index("deliver") < answer.index("67 steps")
