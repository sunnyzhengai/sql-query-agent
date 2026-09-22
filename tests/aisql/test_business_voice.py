"""BV1–BV6 — Brief_Business_Voice acceptance pins (Grammar_Floor
§R16 THE BUSINESS VOICE TIER + THE MEANING LADDER, ratified
2026-09-20; every ruling quoted in the brief).

Authored RED before the mechanism (test-first law). The pins:
  BV1 the worked example — #ED_BORDER's stored description IS the
      gated business sentence, byte-exact (verbatim law).
  BV2 nothing invented — clinician knowledge with no source row is
      REJECTED with the untraceable words named.
  BV3 nothing dropped — a proposal missing a condition's witness is
      REJECTED naming the missing witness.
  BV4 store only the business voice — the technical voice derives
      on demand and is stored NOWHERE on the node.
  BV5 the proposer reads every touched dictionary row (the FL35
      remedy) — materials carry the vendor sentences verbatim and
      the prompt embeds them.
  BV6 staleness — a row whose basis no longer matches falls to the
      mechanical floor, tier named.
Plus the seat pins: the field law (machine refresh never overwrites
`blessed`) and the double-run/dispute/reject registry statuses.

Proves: contract:aisql-design-to-code
"""
import json
import pathlib

import pytest

from aisql.console import build_store
from aisql.flows import business_voice, produce
from aisql.graph.read_api import ReadApi
from aisql.lenses import decisions

REPO = pathlib.Path(__file__).resolve().parents[2]

# The brief's worked example — Sunny's "good." (2026-09-20); the
# acceptance shape, byte-pinned.
BLESSED_SENTENCE = (
    "The base population's ED encounters that had an "
    "'ED BOARDER PATIENTS' event — one row per encounter, "
    "carrying only its encounter id; a membership list.")

# The canonical kill (the brief's rejection demo): true clinical
# knowledge, zero source rows in this estate.
INVENTED = (
    "The base population's ED encounters where the patient "
    "boarded awaiting an inpatient bed — one row per encounter, "
    "carrying only its encounter id; a membership list.")

# BV3's candidate: the boarder-event condition vanished entirely.
DROPPED = (
    "The base population's ED encounters — one row per encounter, "
    "carrying only its encounter id; a membership list.")


@pytest.fixture(scope="module")
def world():
    store, _base = build_store("sepsis")
    read = ReadApi(store)
    for _key, tree in sorted(read.trees().items()):
        for sc in decisions.named_scopes(tree):
            if sc["name_key"].endswith("::#ED_BORDER"):
                return store, read, tree, sc
    raise AssertionError("no #ED_BORDER scope in the sepsis estate")


GLOSSARY = REPO / "AIVIA_Product" / "estates" / "sepsis" / "glossary"


def _node(read, sc):
    return next(n for n in read.nodes("scope")
                if n.identity == sc["name_key"])


def _mats(read, tree, sc):
    """Materials exactly as the writer computes them — acronym
    expansions included (B8.b: blessed vocabulary IS rung-0
    material, R16's own list)."""
    return business_voice.materials(
        read, tree, sc,
        acronyms=business_voice.load_acronym_expansions(GLOSSARY))


def test_bv1_ed_border_speaks_the_blessed_sentence(world):
    _store, read, _tree, sc = world
    assert _node(read, sc).properties["description"] \
        == BLESSED_SENTENCE


def test_bv2_invention_rejected_with_words_named(world):
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    violations = business_voice.check_sentence(INVENTED, mech, mats)
    assert violations, "clinician knowledge must never pass the gate"
    text = " ".join(violations)
    for word in ("boarded", "awaiting", "inpatient"):
        assert word in text, f"the untraceable word '{word}' " \
            "must be NAMED in the violations"


def test_bv3_dropped_condition_rejected_named(world):
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    violations = business_voice.check_sentence(DROPPED, mech, mats)
    assert violations, "a dropped condition must never pass"
    assert any("2600000007" in v or "ED BOARDER PATIENTS" in v
               for v in violations), \
        "the missing witness must be NAMED"


def test_bv4_technical_voice_derives_never_stores(world):
    _store, read, tree, sc = world
    node = _node(read, sc)
    mech = produce.scope_sentence(read, tree, sc)
    # the ruling: "store only the business voice, derive the
    # technical voice" — the floor stays recomputable on demand...
    assert mech and mech != BLESSED_SENTENCE
    # ...and is stored NOWHERE on the node
    for key, value in node.properties.items():
        if key == "description":
            continue
        assert not (isinstance(value, str) and mech in value), \
            f"the technical voice leaked into stored field '{key}'"


def test_bv5_proposer_reads_every_dictionary_row(world):
    _store, read, tree, sc = world
    mats = _mats(read, tree, sc)
    joined = " ".join(mats.values())
    # the vendor's own sentences, verbatim (FL35's remedy)
    assert "associating records" in joined          # ED_PATIENT_INFO
    assert "regarding the current event records" in joined  # ED_EVENT_INFO
    mech = produce.scope_sentence(read, tree, sc)
    prompt = business_voice.proposal_prompt(mech, mats)
    assert "associating records" in prompt
    assert "regarding the current event records" in prompt


def test_bv6_gate_dirty_stale_falls_to_the_floor(world):
    """FL36 ruled (Sunny "approve re-anchor-when-gate-clean",
    2026-09-21): a basis move that BREAKS the sentence (a word no
    longer traces) still silences the row — the floor voices."""
    _store, read, tree, sc = world
    rows = {sc["name_key"]: {"status": "blessed",
                             "sentence": "a sentence from dead "
                                         "materials",
                             "basis_hash": "no-longer-the-basis"}}
    sentence, tier = business_voice.effective_sentence(
        read, tree, sc, rows,
        acronyms=business_voice.load_acronym_expansions(GLOSSARY))
    assert tier == "stale"
    assert sentence == produce.scope_sentence(read, tree, sc)


def test_fl36_stale_but_gate_clean_re_anchors(world):
    """FL36's other half: the basis moved but every word still
    traces and nothing is dropped — the sentence keeps voicing
    with its status carried, and the hash re-anchors in place so
    blessing converges."""
    _store, read, tree, sc = world
    rows = {sc["name_key"]: {"status": "blessed",
                             "sentence": BLESSED_SENTENCE,
                             "basis_hash": "an-anchor-that-moved"}}
    sentence, tier = business_voice.effective_sentence(
        read, tree, sc, rows,
        acronyms=business_voice.load_acronym_expansions(GLOSSARY))
    assert (sentence, tier) == (BLESSED_SENTENCE, "blessed")
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    assert rows[sc["name_key"]]["basis_hash"] \
        == business_voice.basis_hash(mech, mats)  # re-anchored


def test_fl36_the_committed_registry_is_anchored(world):
    """The repo's own registry self-heals at boot: after
    build_store the #ED_BORDER row's hash matches its live basis
    (the writer persists re-anchors, stamped re_anchored_at when
    one fired)."""
    import pathlib
    _store, read, tree, sc = world
    glossary = (pathlib.Path(__file__).resolve().parents[2]
                / "AIVIA_Product" / "estates" / "sepsis" / "glossary")
    rows = business_voice.load_rows(glossary)
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    assert rows[sc["name_key"]]["basis_hash"] \
        == business_voice.basis_hash(mech, mats)


def test_gate_passes_the_blessed_sentence(world):
    """The acceptance sentence itself is gate-clean — REJECTED
    would mean the gate and the ruled example disagree."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    assert business_voice.check_sentence(
        BLESSED_SENTENCE, mech, mats) == []


def test_effective_tier_order(world):
    """blessed > proposed > floor; a fresh gated row voices with
    its status carried (ruling 5)."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    fresh = business_voice.basis_hash(mech, mats)
    rows = {sc["name_key"]: {"status": "proposed",
                             "sentence": BLESSED_SENTENCE,
                             "basis_hash": fresh}}
    sentence, tier = business_voice.effective_sentence(
        read, tree, sc, rows,
        acronyms=business_voice.load_acronym_expansions(GLOSSARY))
    assert (sentence, tier) == (BLESSED_SENTENCE, "proposed")
    assert business_voice.effective_sentence(
        read, tree, sc, {}) == (mech, "floor")


def test_b6_skeleton_words_are_not_facts(world):
    """B6 (Sunny "agree with your fix to class 1", 2026-09-21):
    connective English and spelled small numbers are sentence
    skeleton — the gate kills invented FACTS, never glue. His
    batch measured the defect: 'where' alone killed 98 rows."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    glued = ("The base population's ED encounters where the event "
             "type includes '2600000007' (noted 'ED BOARDER "
             "PATIENTS') — one row per encounter, carrying only "
             "its encounter id; a membership list.")
    assert business_voice.check_sentence(glued, mech, mats) == []
    # the fact-word direction is untouched: inventions still die
    assert business_voice.check_sentence(INVENTED, mech, mats)


def test_b6_rejected_rows_rejudge_free(world, tmp_path):
    """B6's second half: a `rejected` verdict is re-judged at
    every batch from its stored candidates — the gate is code and
    code changes; no model call is spent on the re-judge."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    # the tmp glossary holds no acronym ledger — the basis the
    # batch will compute there carries none
    mats = business_voice.materials(read, tree, sc)
    bhash = business_voice.basis_hash(mech, mats)
    glued = ("The base population's ED encounters where the event "
             "type includes '2600000007' (noted 'ED BOARDER "
             "PATIENTS') — one row per encounter, carrying only "
             "its encounter id; a membership list.")
    business_voice.save_rows(tmp_path, {sc["name_key"]: {
        "status": "rejected", "sentence": glued,
        "basis_hash": bhash,
        "violations": ["GATE-BV2: 'where' traces to no source row"],
        "proposer": {"model": "test-double", "prompt_version": "t1",
                     "runs": 1}}})
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({
        f"{sc['name_key']}|{bhash}|test-double|t1": [glued]}))

    def seat(prompt: str) -> str:
        return "wording that traces to nothing sourced anywhere"

    counts = business_voice.propose_sentences(
        read, tmp_path, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z",
        cache_path=cache_path)
    row = business_voice.load_rows(tmp_path)[sc["name_key"]]
    assert row["status"] == "proposed"  # the gate widened, free
    assert row["sentence"] == glued
    assert "violations" not in row
    assert counts["re_judged"] >= 1


def test_b7_repair_round_fixes_or_hands_to_sunny(world, tmp_path):
    """B7 (Sunny 2026-09-21: "can you either propose to the llm to
    fix the error or propose to me so i can manually fix it?" —
    BOTH, layered): a gate-rejected candidate earns ONE repair
    call whose prompt carries the named violations; the repaired
    sentence re-gates. Still dirty -> the row stays rejected with
    sentence + violations for Sunny's hand, repair_spent so no
    batch ever pays for it twice."""
    _store, read, tree, sc = world
    seen = []

    def seat(prompt: str) -> str:
        seen.append(prompt)
        if "'2600000007'" in prompt:  # the #ED_BORDER materials
            if "GATE-BV" in prompt:  # the repair round
                return BLESSED_SENTENCE
            return INVENTED
        return "unrelated words tracing nowhere"

    counts = business_voice.propose_sentences(
        read, tmp_path, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z")
    row = business_voice.load_rows(tmp_path)[sc["name_key"]]
    assert row["status"] == "proposed"
    assert row["sentence"] == BLESSED_SENTENCE
    assert row.get("repaired") is True
    assert counts["repaired_ok"] >= 1
    repair_prompts = [p for p in seen
                      if "'2600000007'" in p and "GATE-BV" in p]
    assert repair_prompts and "boarded" in repair_prompts[0], \
        "the repair prompt names the violations"
    # every hopeless scope stays rejected WITH its material for
    # Sunny's hand: the sentence + the named violations
    rejected = [r for r in business_voice.load_rows(tmp_path).values()
                if r["status"] == "rejected"]
    assert rejected
    assert all(r.get("sentence") and r.get("violations")
               and r.get("repair_spent") for r in rejected)


def test_b7_repair_never_pays_twice(world, tmp_path):
    """A repair_spent row re-judges free forever; the seat is
    never consulted for it again while its basis stands."""
    _store, read, tree, sc = world

    def seat(prompt: str) -> str:
        return "unrelated words tracing nowhere"

    business_voice.propose_sentences(
        read, tmp_path, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z")

    def dead_seat(prompt: str) -> str:
        raise AssertionError("no paid call may repeat")

    counts = business_voice.propose_sentences(
        read, tmp_path, dead_seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:01:00Z")
    assert counts["model_calls"] == 0
    assert counts["seat_error"] == 0


def test_b6b_possessive_apostrophes_are_not_quotes(world):
    """B6.b (the #AllMeds live find, 2026-09-21): the R5.c
    owner-possessive voice ("the med admin record's taken time is
    before the base pop selection's ed departure time") is NOT a
    quoted literal — the witness extractor must never pair
    possessive apostrophes into a nonsense witness no sentence
    can contain."""
    _store, read, _tree, _sc = world
    from aisql.lenses import decisions
    for _k, tree in sorted(read.trees().items()):
        for sc in decisions.named_scopes(tree):
            if sc["name_key"] == \
                    "reporting/USP_ED_SEPSIS.sql::#AllMeds":
                mech = produce.scope_sentence(read, tree, sc)
                assert "record's" in mech  # the possessive voice
                for lit, noted in business_voice.witness_pairs(mech):
                    assert not lit.startswith("s "), \
                        f"possessive fragment paired: {lit!r}"
                # his batch's exact rejected sentence is clean once
                # the false witness dies (its only violation)
                rejected = (
                    "The selection includes records of medication "
                    "administrations where the taken time is "
                    "before the base population's ED departure "
                    "time while in ED, the route of administration "
                    "is intravenous, and the MAR action category "
                    "number is one of 16 values, carrying the "
                    "encounter id, the order med id, the taken "
                    "time, the medication name, the thera class "
                    "code, the med route code, and 6 additional "
                    "columns.")
                mats = _mats(read, tree, sc)
                assert business_voice.check_sentence(
                    rejected, mech, mats) == []
                return
    raise AssertionError("no #AllMeds scope found")


def test_b6b_more_skeleton_words(world):
    """'before'/'after' (temporal prepositions), 'match(es)' (the
    membership verb R14 itself speaks), 'condition(s)' (a core
    slot's own name) are skeleton, never facts."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    glued = ("The base population's ED encounters before and "
             "after matching the condition that the event type "
             "matches '2600000007' (noted 'ED BOARDER PATIENTS') "
             "— one row per encounter, carrying only its "
             "encounter id; a membership list.")
    assert business_voice.check_sentence(glued, mech, mats) == []


def test_b6c_payload_accepts_carry_inflections(world):
    """B6.c (the #LacticAcid live find, 2026-09-21): "it carries
    the time line …" IS the payload frame — the witness check
    accepts every carry-family inflection, not the one word
    'carrying'."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    inflected = ("The base population's ED encounters that had an "
                 "'ED BOARDER PATIENTS' event — one row per "
                 "encounter, and it carries only its encounter id.")
    assert business_voice.check_sentence(inflected, mech, mats) == []


def test_b8_witnesses_come_from_condition_rows(world):
    """B8.2 (Sunny "agreed. go.", 2026-09-21): witnesses read per
    CONDITION ROW, never by scanning the whole mechanical sentence
    — quote pairing is local to one clause, so raw-fragment and
    cross-clause artifacts (the ABX class) cannot manufacture
    witnesses."""
    _store, read, tree, sc = world
    texts = business_voice.scope_witness_texts(read, sc)
    assert any("2600000007" in t for t in texts)
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    # the blessed sentence stays clean under the graph path
    assert business_voice.check_sentence(
        BLESSED_SENTENCE, mech, mats, witness_texts=texts) == []
    # dropping the single-value condition still kills, named
    v = business_voice.check_sentence(
        DROPPED, mech, mats, witness_texts=texts)
    assert any("2600000007" in x or "ED BOARDER PATIENTS" in x
               for x in v)


def test_b8_list_witnesses_compress(world):
    """B8.1 (Sunny "1: compression acceptable"): a multi-value
    list condition requires NO verbatim witness — the full list
    stays one drill-down away; single literals and their noted
    words remain required."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    texts = ["The order set id is one of the values '40400100', "
             "'40400058', '40400196' (noted 'Sepsis Pathway')",
             "The event type is '2600000007' (noted 'ED BOARDER "
             "PATIENTS')"]
    kept_list_out = ("The base population's ED encounters that had "
                     "an 'ED BOARDER PATIENTS' event — one row per "
                     "encounter, carrying only its encounter id; "
                     "a membership list.")
    assert business_voice.check_sentence(
        kept_list_out, mech, mats, witness_texts=texts) == []


def test_b8_splice_rung_restores_the_dropped_clause(world, tmp_path):
    """B8.3 (Sunny "can you add it back mechanically…?" — yes):
    when the repair still drops a witness and no word is invented,
    the missing condition's FLOOR CLAUSE splices on mechanically;
    the row lands proposed, marked spliced — nothing waits on a
    person."""
    _store, read, tree, sc = world

    def seat(prompt: str) -> str:
        if "'2600000007'" in prompt:  # every round for #ED_BORDER
            return ("The base population's ED encounters — one row "
                    "per encounter, carrying only its encounter "
                    "id; a membership list.")  # witness dropped
        return "unrelated words tracing nowhere"

    business_voice.propose_sentences(
        read, tmp_path, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z")
    row = business_voice.load_rows(tmp_path)[sc["name_key"]]
    assert row["status"] == "proposed"
    assert row.get("spliced") is True
    assert "2600000007" in row["sentence"] \
        or "ED BOARDER PATIENTS" in row["sentence"]


def test_b8_synonym_ledger_llm_nominates_guard_verifies(world,
                                                        tmp_path):
    """B8.4 (Sunny: "if LLM can be used in this can we leverage
    it? or does it need to be mechanical?" — the LLM NOMINATES,
    a mechanical stem guard verifies, the pair lands as DATA the
    gate consumes deterministically)."""
    _store, read, tree, sc = world

    def seat(prompt: str) -> str:
        if "grammatical form" in prompt:  # the synonym seat
            return json.dumps({"associative": "associating",
                               "boarded": "weight"})
        if "'2600000007'" in prompt:
            return ("The base population's ED visits, associative "
                    "with an 'ED BOARDER PATIENTS' event — one row "
                    "per encounter, carrying only its encounter "
                    "id; a membership list.")
        return "unrelated words tracing nowhere"

    business_voice.propose_sentences(
        read, tmp_path, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z")
    row = business_voice.load_rows(tmp_path)[sc["name_key"]]
    ledger = business_voice.load_synonyms(tmp_path)
    assert "associative" in ledger \
        and ledger["associative"]["source_word"] == "associating"
    # the guard: no shared stem -> the nomination dies; 'boarded'
    # never launders through 'weight'
    assert "boarded" not in ledger
    # 'visits' has no source either — the row must NOT have passed
    # on the strength of an unguarded mapping alone
    assert row["status"] in ("proposed", "rejected")
    if row["status"] == "rejected":
        assert any("visits" in v for v in row["violations"])


def test_b8b_acronym_expansions_are_material(world):
    """B8.b: blessed/matched acronym expansions ARE rung-0
    material (R16's own list names blessed vocabulary) — 'adt' is
    blessed 'Admission, Discharge, Transfer' in this estate, and
    any scope touching an adt-named source may speak it."""
    _store, read, _tree, _sc = world
    exps = business_voice.load_acronym_expansions(GLOSSARY)
    assert "adt" in exps and "Admission" in exps["adt"]
    for _k, tree in sorted(read.trees().items()):
        for sc in decisions.named_scopes(tree):
            if sc["name_key"] == "reporting/USP_ED_SEPSIS.sql::#ADT":
                mats = business_voice.materials(read, tree, sc,
                                                acronyms=exps)
                assert any("Admission, Discharge, Transfer" in v
                           for v in mats.values())
                return
    raise AssertionError("no #ADT scope")


def test_b8b_floor_words_are_never_inventions(world):
    """B8.b: the condition rows' own words (the floor voice) join
    the allowed set — a spliced floor clause can never kill
    itself."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    texts = ["The dispense action is 'DISPENSE'",
             "The event type is '2600000007' (noted 'ED BOARDER "
             "PATIENTS')"]
    cand = (BLESSED_SENTENCE.rstrip(".")
            + "; also: The dispense action is 'DISPENSE'.")
    assert business_voice.check_sentence(
        cand, mech, mats, witness_texts=texts) == []


def test_b8b_witness_noise_is_waived(world):
    """B8.b: raw-SQL echoes, dated changelog comments, and symbol
    literals are drill-down material, never business witnesses;
    real labels stay required."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    texts = [
        "The value_set unique is 3016 (noted 'and "
        "cntl.VALUE_SET_ABBR='Antibacterial'')",
        "The taken time is before the departure (noted "
        "'09.23.2020; MAKE SURE THE Antibiotics WERE GIVEN')",
        "The value set abbr ends with '^Y'",
        "The event type is '2600000007' (noted 'ED BOARDER "
        "PATIENTS')",
    ]
    v = business_voice.check_sentence(
        BLESSED_SENTENCE, mech, mats, witness_texts=texts)
    assert v == [], f"noise witnesses must be waived: {v}"
    v2 = business_voice.check_sentence(
        DROPPED, mech, mats, witness_texts=texts)
    assert any("2600000007" in x or "ED BOARDER" in x for x in v2), \
        "the real label stays required"


def test_b8b_synonym_prompt_carries_vocabulary(world):
    """B8.b: each seat call is stateless — the synonym prompt
    must CARRY the source vocabulary; a tombstone from an older
    prompt version earns exactly one re-ask."""
    prompt = business_voice.synonym_prompt(
        ["administered"], vocabulary=["administration", "record"])
    assert "administration" in prompt
    old_tomb = {"administered": {"source_word": None,
                                 "prompt_version": "s-old"}}
    fresh_tomb = {"administered": {
        "source_word": None,
        "prompt_version": business_voice.SYN_PROMPT_VERSION}}
    mapped = {"administered": {"source_word": "administration"}}
    ask = business_voice.synonym_worklist
    assert ask(["administered"], old_tomb) == ["administered"]
    assert ask(["administered"], fresh_tomb) == []
    assert ask(["administered"], mapped) == []


def test_b9_output_names_are_material(world):
    """B9.1 (Sunny "go", 2026-09-21): the author's own output
    aliases (projection names) are source words — 'Department
    Rollup' is the SQL's alias, not an invention."""
    _store, read, _tree, _sc = world
    for _k, tree in sorted(read.trees().items()):
        for sc in decisions.named_scopes(tree):
            if sc["name_key"] == ("reporting/"
                                  "USP_IP_Sepsis_ComplianceByShift"
                                  ".sql::delivery"):
                mats = business_voice.materials(read, tree, sc)
                assert any("Department Rollup" in v
                           for v in mats.values())
                return
    raise AssertionError("no ComplianceByShift delivery")


def test_b9_ing_ed_forms_fold(world):
    """B9.2: -ing/-ed inflections fold deterministically —
    'looking' traces through 'look', 'making' through 'make'; no
    list, no model."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    texts = ["The action is 'LOOK FOR THE MAKE'"]
    cand = (BLESSED_SENTENCE.rstrip(".")
            + ", looking and making toward 'LOOK FOR THE MAKE'.")
    assert business_voice.check_sentence(
        cand, mech, mats, witness_texts=texts) == []


def test_b9_token_subset_satisfies_a_witness(world):
    """B9.3: a witness is about CONTENT, not byte-substrings — a
    paraphrase carrying every content word (inflection-tolerant)
    satisfies it; a witness whose words are genuinely absent
    stays required."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    texts = ["The time line is 1 (noted 'LOOK FOR FIRST "
             "ANTIBIOTIC ADMINISTRATION ONLY')",
             "The shift is 'AM (Day Shift)'",
             "The event type is '2600000007' (noted 'ED BOARDER "
             "PATIENTS')"]
    cand = (BLESSED_SENTENCE.rstrip(".")
            + ", looking for the first antibiotic administration "
            "only.")
    v = business_voice.check_sentence(cand, mech, mats,
                                      witness_texts=texts)
    assert not any("ANTIBIOTIC" in x for x in v), v
    assert any("AM (Day Shift)" in x for x in v), \
        "genuinely absent words stay required"


def test_b9_witness_violations_dedupe(world):
    """B9.4: four conditions sharing one noted yield ONE
    violation, not four."""
    _store, read, tree, sc = world
    mech = produce.scope_sentence(read, tree, sc)
    mats = _mats(read, tree, sc)
    texts = [f"The shift {i} flag is 'AM (Day Shift)'"
             for i in range(4)] + [
        "The event type is '2600000007' (noted 'ED BOARDER "
        "PATIENTS')"]
    v = business_voice.check_sentence(BLESSED_SENTENCE, mech, mats,
                                      witness_texts=texts)
    assert len([x for x in v if "AM (Day Shift)" in x]) == 1


def test_b10_alias_carried_acronym_reaches_material(world):
    """B10 (FL37, Sunny "ok build b10", 2026-09-21): B9.1 ruled the
    projection's output aliases ARE source words — the acronym pass
    must read their tokens too. The live specimen: los is blessed
    'Length Of Stay' (his hand, 2026-09-21) and the
    USP_IP_SepsisEncountersDetails delivery's ONLY clean 'los'
    token is the alias [LOS Hours] — the source column LosHours
    folds to the single word 'loshours', so before B10 the
    blessing could not reach the scope and its row stayed rejected
    on "'length' traces to no source row"."""
    _store, read, _tree, _sc = world
    exps = business_voice.load_acronym_expansions(GLOSSARY)
    assert "los" in exps and "Length Of Stay" in exps["los"]
    for _k, tree in sorted(read.trees().items()):
        for sc in decisions.named_scopes(tree):
            if sc["name_key"] == ("reporting/USP_IP_SepsisEncounters"
                                  "Details.sql::delivery"):
                mats = business_voice.materials(read, tree, sc,
                                                acronyms=exps)
                assert any("Length Of Stay" in v
                           for v in mats.values()), (
                    "the blessed los expansion never reached the "
                    "delivery scope's materials — the alias "
                    "[LOS Hours] is its only 'los' carrier")
                return
    raise AssertionError("no delivery scope in "
                         "USP_IP_SepsisEncountersDetails")


def test_b9_acronym_form_guard():
    """B9.5's mechanical half: initials or in-order subsequence —
    the acronym analogue of the stem guard."""
    g = business_voice.acronym_form_guard
    assert g("los", "length of stay")
    assert g("adt", "Admission, Discharge, Transfer")
    assert g("mrn", "medical record number")
    assert g("pt", "patient")
    assert not g("abx", "antibiotics")      # the x maps to nothing
    assert not g("rollup", "department")
    assert not g("los", "location of service center extra")


def test_b9_acronym_nomination_lands_as_proposed(world, tmp_path):
    """B9.5: an unreviewed ledger token touched by a killed scope
    earns ONE expansion nomination; the form guard verifies; the
    row lands `proposed` in the ACRONYM LEDGER (its ruled home)
    and serves the gate from then on — Sunny blesses or kills at
    leisure, nothing waits."""
    _store, read, tree, sc = world
    (tmp_path / "acronym_ledger.json").write_text(json.dumps(
        # literal: shape — a minimal unreviewed ledger row
        {"ed": {"status": "unreviewed"}}))

    def seat(prompt: str) -> str:
        if "abbreviate" in prompt:
            return "emergency department"
        if "'2600000007'" in prompt:
            return ("The base population's emergency department "
                    "encounters that had an 'ED BOARDER PATIENTS' "
                    "event — one row per encounter, carrying only "
                    "its encounter id; a membership list.")
        return "unrelated words tracing nowhere"

    business_voice.propose_sentences(
        read, tmp_path, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z")
    led = json.loads((tmp_path / "acronym_ledger.json").read_text())
    assert led["ed"]["status"] == "proposed"
    assert led["ed"]["expansions"] == ["emergency department"]
    row = business_voice.load_rows(tmp_path)[sc["name_key"]]
    assert row["status"] == "proposed"
    assert "emergency department" in row["sentence"]
    exps = business_voice.load_acronym_expansions(tmp_path)
    assert exps.get("ed") == "emergency department"


def test_seat_field_law_and_statuses(world, tmp_path):
    """The sentence seat is SINGLE-RUN, gate-first (Sunny "ok,
    agreed" 2026-09-21 — the double-run law stays R5.b's, for
    word-sized output; for sentences the GATE carries the honesty
    load and wording variance is not a verdict). One model call
    per scope; statuses are proposed/rejected only; `blessed` is a
    ruled status the machine may never overwrite (the field law)."""
    _store, read, tree, sc = world
    glossary_dir = tmp_path
    ruled = {sc["name_key"]: {"status": "blessed",
                              "sentence": BLESSED_SENTENCE,
                              "basis_hash": "ruled-by-sunny"}}
    business_voice.save_rows(glossary_dir, ruled)
    calls = {"n": 0}

    def seat(prompt: str) -> str:
        calls["n"] += 1
        return f"run {calls['n']} differs from every other run"

    counts = business_voice.propose_sentences(
        read, glossary_dir, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z")
    after = business_voice.load_rows(glossary_dir)
    assert after[sc["name_key"]]["sentence"] == BLESSED_SENTENCE
    assert after[sc["name_key"]]["status"] == "blessed"
    assert counts["blessed_kept"] >= 1
    assert "disputed" not in counts  # the verdict retired wholesale
    assert counts["model_calls"] == calls["n"]  # ONE call per scope
    assert not [r for r in after.values()
                if r.get("status") == "disputed"]
    # wording that traces to nothing still dies at the gate
    assert counts["rejected"] >= 1


def test_prior_disputed_rows_resolve_on_rerun(world, tmp_path):
    """The 156-row migration path: a row the OLD double-run law
    marked `disputed` is NOT 'kept' on re-run — its first cached
    candidate goes to the gate and the row re-lands as
    proposed/rejected, zero new model calls when cached."""
    _store, read, tree, sc = world
    glossary_dir = tmp_path
    mech = produce.scope_sentence(read, tree, sc)
    mats = business_voice.materials(read, tree, sc)  # tmp: no ledger
    bhash = business_voice.basis_hash(mech, mats)
    stale_law = {sc["name_key"]: {
        "status": "disputed", "basis_hash": bhash,
        "candidates": [BLESSED_SENTENCE, "a differing second run"],
        "proposer": {"model": "test-double", "prompt_version": "t1",
                     "runs": 2}}}
    business_voice.save_rows(glossary_dir, stale_law)
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({
        f"{sc['name_key']}|{bhash}|test-double|t1":
            [BLESSED_SENTENCE, "a differing second run"]}))

    def seat(prompt: str) -> str:  # pragma: no cover — cache wins
        raise AssertionError("the cached pair must be spent, "
                             "never a new paid call")

    business_voice.propose_sentences(
        read, glossary_dir, seat, model="test-double",
        prompt_version="t1", run_at="2026-09-21T00:00:00Z",
        cache_path=cache_path)
    after = business_voice.load_rows(glossary_dir)
    row = after[sc["name_key"]]
    assert row["status"] == "proposed"  # gate-clean first candidate
    assert row["sentence"] == BLESSED_SENTENCE
    assert "candidates" not in row
