"""R5.b THE BLESSED NAME, slice 1 (Grammar_Floor v2.8.0, ratified
2026-09-12): the registry loader + the GATE-SUBJ family + the render
wiring. The model never enters the render path — this slice ships the
machinery; the proposer batch waits on riders (c)/(d).

A3 (the gate corpus): one hand-authored candidate per violation
class, each killed by its named gate. A1 (the fallback proof) rides
the F4 byte-exact suite — no blessed_name nodes exist in those
worlds, so every floor recomputes identically.

Proves: contract:aivia-design-to-code
"""
import json

from aivia.flows import gates, glossary, produce
from aivia.graph import kg3_artifacts
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store

T0 = "2026-09-12T20:00:00Z"
TBL = "SIMEMR|dbo|MED_ADMIN_RECORDS"
COL = TBL + "|MAR_ACTION_CODE"
COL_DESC = "The MAR_ACTION_CATEGORY_NUMBER linked to this administration."
TBL_DESC = ("This table holds the active medication administration "
            "data, encompassing all scheduled and completed "
            "administrations that are currently displayed on the MAR.")
TAKEN = TBL + "|TAKEN_TIME"
TAKEN_DESC = "The time designated by the user when the action occurred."
DEPART = "SIMEMR|dbo|HOSPITAL_ENCOUNTERS|ED_DEPARTURE_TIME"
DEPART_DESC = "The timestamp indicating when the patient exited the ED."


def _world():
    store = Store()
    store.append_node("table", TBL, {"description": TBL_DESC},
                      T0, "test")
    for cid, desc in ((COL, COL_DESC), (TAKEN, TAKEN_DESC),
                      (DEPART, DEPART_DESC)):
        store.append_node("column", cid, {"description": desc},
                          T0, "test")
    return store, ReadApi(store)


def _bless(store, target, words, desc, by="person:sunny"):
    kg3_artifacts.append_blessed_name(
        store, target=target, words=words,
        description_hash=glossary.description_hash(desc),
        approved_by=by, approved_at=T0)


# ---- A3: the gate corpus — each violation class killed by name ----

def test_gate_passes_selection_from_vendor_words():
    # "administration" from the description, "action" from the name
    assert gates.check_blessed_words(
        "administration action", COL_DESC, "MAR_ACTION_CODE") == []


def test_gate_subj1_kills_words_the_vendor_never_wrote():
    # right idea, wrong words — fabrication dies mechanically
    v = gates.check_blessed_words(
        "delivery method", COL_DESC, "MAR_ACTION_CODE")
    assert any("GATE-SUBJ-1" in x and "delivery" in x for x in v)
    assert any("GATE-SUBJ-1" in x and "method" in x for x in v)


def test_gate_subj1_stem_matching_is_a_closed_table():
    # plural strip: "administrations" (source) covers "administration"
    assert gates.check_blessed_words(
        "scheduled administrations", TBL_DESC,
        "MED_ADMIN_RECORDS") == []


def test_gate_subj2_kills_values_not_in_source():
    v = gates.check_blessed_words(
        "route 11", "The route of administration.", "MED_ROUTE_CODE")
    assert any("GATE-SUBJ-2" in x and "11" in x for x in v)


def test_gate_subj3_kills_raw_identifiers():
    v = gates.check_blessed_words(
        "the MAR_ACTION_CODE", COL_DESC, "MAR_ACTION_CODE")
    assert any("GATE-SUBJ-3" in x for x in v)
    # identifier SHAPE (underscore token) dies even lowercased
    v2 = gates.check_blessed_words(
        "mar_action_category_number", COL_DESC, "MAR_ACTION_CODE")
    assert any("GATE-SUBJ-3" in x for x in v2)


def test_gate_subj4_shape_violations_each_named():
    long = gates.check_blessed_words(
        "the active medication administration data record",
        TBL_DESC, "MED_ADMIN_RECORDS")
    assert any("GATE-SUBJ-4" in x for x in long)
    art = gates.check_blessed_words(
        "the administration", COL_DESC, "MAR_ACTION_CODE")
    assert any("leading article" in x for x in art)
    prep = gates.check_blessed_words(
        "administration of", COL_DESC, "MAR_ACTION_CODE")
    assert any("trailing preposition" in x for x in prep)
    assert gates.check_blessed_words("", COL_DESC, "X") \
        == ["GATE-SUBJ-4: empty candidate"]


# ---- the registry loader + seeder (delta-by-target, gated) ----

def _registry(tmp_path, rows):
    (tmp_path / "blessed_subjects.json").write_text(json.dumps(rows))
    return tmp_path


def _row(words, desc, status="blessed", by="person:sunny", h=None):
    return {"words": words, "status": status, "blessed_by": by,
            "blessed_at": T0,
            "description_hash": h or glossary.description_hash(desc)}


def test_seed_births_blessed_name_nodes_from_the_registry(tmp_path):
    store, read = _world()
    gdir = _registry(tmp_path, {
        COL: _row("administration action", COL_DESC),
        TBL: _row("medication administration", TBL_DESC)})
    counts = glossary.seed_blessed_names(store, read, gdir)
    assert counts["seeded"] == 2
    got = {n.properties["target"]: n.properties["words"]
           for n in read.nodes("blessed_name")}
    assert got == {COL: "administration action",
                   TBL: "medication administration"}
    # delta-by-target: a second boot births nothing
    again = glossary.seed_blessed_names(store, read, gdir)
    assert again["seeded"] == 0 and again["already"] == 2


def test_seed_counts_never_silent(tmp_path):
    store, read = _world()
    gdir = _registry(tmp_path, {
        COL: _row("administration action", COL_DESC,
                  status="proposed"),           # only BLESSED voices
        TAKEN: _row("taken time", TAKEN_DESC,
                    h="0" * 64),                # stale hash
        DEPART: _row("delivery method", DEPART_DESC),  # gate kill
        "SIMEMR|dbo|GHOST|X": _row("ghost", "A ghost."),
        TBL: _row("medication administration", TBL_DESC,
                  by="agent:proposer")})        # machines never rule
    counts = glossary.seed_blessed_names(store, read, gdir)
    assert counts["seeded"] == 0
    assert counts["skipped_status"] == 1
    assert counts["stale"] == 1
    assert counts["rejected"] == 2  # gate kill + machine blessing
    assert counts["missing_target"] == 1
    assert read.nodes("blessed_name") == []


def test_seed_absent_registry_is_a_counted_zero(tmp_path):
    store, read = _world()
    counts = glossary.seed_blessed_names(store, read, tmp_path)
    assert counts["seeded"] == 0


def test_blessing_is_a_human_act():
    store, _ = _world()
    try:
        kg3_artifacts.append_blessed_name(
            store, target=COL, words="administration action",
            description_hash=glossary.description_hash(COL_DESC),
            approved_by="agent:proposer", approved_at=T0)
        raise AssertionError("machine blessing must refuse")
    except kg3_artifacts.RefusalKG3:
        pass


# ---- the render wiring: blessed words at every position ----

def _ref(col_id, ref):
    return {"kind": "column_ref", "ref": ref, "resolves_to": col_id}


def test_blessed_name_speaks_in_value_predicates():
    store, read = _world()
    _bless(store, COL, "administration action", COL_DESC)
    voice = produce._Voice(read, {})
    pred = {"kind": "COMPARE_EQ", "node": "predicate",
            "subject": _ref(COL, "MA.MAR_ACTION_CODE"),
            "comparand": {"kind": "literal", "value": "1"}}
    assert produce._voice_predicate(pred, voice) \
        == "The administration action is 1."


def test_unblessed_stays_the_heuristic_fallback():
    # A1 at unit grain: no blessed_name node, today's words verbatim
    store, read = _world()
    voice = produce._Voice(read, {})
    assert voice.subject(_ref(COL, "MA.MAR_ACTION_CODE")) \
        == "mar_action_category_number linked"


def test_blessed_names_speak_both_relation_sides():
    store, read = _world()
    _bless(store, TAKEN, "taken time", TAKEN_DESC)
    _bless(store, DEPART, "ed exit time", DEPART_DESC)
    voice = produce._Voice(read, {})
    pred = {"kind": "COMPARE_LT", "node": "predicate",
            "subject": _ref(TAKEN, "MA.TAKEN_TIME"),
            "comparand": _ref(DEPART, "B.ED_DEPARTURE_TIME")}
    assert produce._voice_predicate(pred, voice) \
        == "The taken time is before the ed exit time."


def test_blessed_name_speaks_in_recordedness():
    store, read = _world()
    _bless(store, TAKEN, "medication time", TAKEN_DESC)
    voice = produce._Voice(read, {})
    pred = {"kind": "NULL_CHECK", "node": "predicate",
            "subject": _ref(TAKEN, "MA.TAKEN_TIME")}
    assert produce._voice_predicate(pred, voice) \
        == "The medication time is not recorded."


def test_temporal_union_blessing_only_adds_evidence():
    # rider (c) RULED: a blessed name without a temporal noun must
    # not flip the verb numeric — the fallback words join the test
    store, read = _world()
    _bless(store, TAKEN, "administration clock", TAKEN_DESC)
    _bless(store, DEPART, "ed exit moment", DEPART_DESC)
    voice = produce._Voice(read, {})
    pred = {"kind": "COMPARE_LT", "node": "predicate",
            "subject": _ref(TAKEN, "MA.TAKEN_TIME"),
            "comparand": _ref(DEPART, "B.ED_DEPARTURE_TIME")}
    # name words carry "time" — temporal survives the blessing
    assert produce._voice_predicate(pred, voice) \
        == "The administration clock is before the ed exit moment."


def test_declared_type_is_temporal_truth():
    # rider (c) AMENDED (Sunny, 2026-09-13: "we can get the data
    # type from the EMR's dictionary"): a declared temporal type
    # decides the verb outright — no word test needed
    store, read = _world()
    when = TBL + "|EVENT_INSTANT"
    store.append_node("column", when,
                      {"description": "The moment recorded.",
                       "data_type": "DATETIME"}, T0, "test")
    voice = produce._Voice(read, {})
    pred = {"kind": "COMPARE_LT", "node": "predicate",
            "subject": _ref(when, "MA.EVENT_INSTANT"),
            "comparand": {"kind": "literal", "value": "'2024-01-01'"}}
    assert "is before" in produce._voice_predicate(pred, voice)


def test_non_temporal_type_never_removes_evidence():
    # EVIDENCE ONLY ADDS: VARCHAR dates are an EMR fact of life —
    # a non-temporal type never VETOES the word test; the spoken
    # "time" still wins the temporal verb
    store, read = _world()
    when = TBL + "|ARRIVAL_TIME"
    store.append_node("column", when,
                      {"description": "The time the patient "
                                      "arrived.",
                       "data_type": "VARCHAR(10)"}, T0, "test")
    voice = produce._Voice(read, {})
    pred = {"kind": "COMPARE_LT", "node": "predicate",
            "subject": _ref(when, "MA.ARRIVAL_TIME"),
            "comparand": {"kind": "literal", "value": "'08:00'"}}
    assert "is before" in produce._voice_predicate(pred, voice)


def test_intake_carries_data_type_opportunistically(tmp_path):
    # the CONTRACT_DATALOAD amendment: columns.csv MAY carry
    # data_type; absent = today's behavior, present = stored
    import pathlib
    import shutil

    from aivia.flows import inbound
    from aivia.graph import kg1_intake
    fix = (pathlib.Path(__file__).resolve().parents[2]
           / "AIVIA_Product" / "fixtures" / "F1_minimal_estate")
    snap = tmp_path / "snap"
    shutil.copytree(fix / "simemr_snapshot", snap)
    rows = (snap / "columns.csv").read_text().splitlines()
    rows[0] += ",data_type"
    rows[1] += ",DATETIME"  # first column gains a declared type;
    # the rest stay short — DictReader yields None, absent stays
    # absent
    (snap / "columns.csv").write_text("\n".join(rows))
    store = Store()
    reg = json.loads((fix / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    inbound.receive_extract(store, reg, kg1_intake.load_snapshot(snap),
                            known_packs={"simemr-pack-0.1",
                                         "org-pack-0.1"})
    read = ReadApi(store)
    typed = {n.identity: n.properties.get("data_type")
             for n in read.nodes("column")
             if n.properties.get("data_type")}
    assert list(typed.values()) == ["DATETIME"]
    untyped = [n for n in read.nodes("column")
               if "data_type" not in n.properties]
    assert untyped  # absent stays absent — no empty shells


def test_temporal_union_reaches_value_comparisons_too():
    # the dictionary phrase ("The time designated…") is the
    # fallback for a VALUE comparison — its "time" survives a
    # blessing that dropped the word
    store, read = _world()
    _bless(store, TAKEN, "administration clock", TAKEN_DESC)
    voice = produce._Voice(read, {})
    pred = {"kind": "COMPARE_GTE", "node": "predicate",
            "subject": _ref(TAKEN, "MA.TAKEN_TIME"),
            "comparand": {"kind": "literal", "value": "'08:00'"}}
    assert produce._voice_predicate(pred, voice) \
        == "The administration clock is on or after '08:00'."


def test_blessed_table_name_speaks_in_source_phrases():
    store, read = _world()
    _bless(store, TBL, "medication administration", TBL_DESC)
    voice = produce._Voice(read, {})
    assert produce._source_phrase(
        "dbo.MED_ADMIN_RECORDS", TBL, [], blessed=voice.blessed) \
        == "medication administration records"
    # unblessed = today's name mechanics, stutter and all
    assert produce._source_phrase(
        "dbo.MED_ADMIN_RECORDS", TBL, []) \
        == "med admin records records"


# ---- THE NAMER SEAT (riders c/d ruled 2026-09-12): proposals
# ---- only, injected model, content-keyed cache, field law ----

class _FakeNamer:
    """Scripted namer: returns per-target answers in order; counts
    every call (the zero-spend cache proof)."""

    def __init__(self, script):
        self.script = dict(script)
        self.calls = 0

    def __call__(self, name, description):
        self.calls += 1
        answers = self.script[name]
        return answers.pop(0) if len(answers) > 1 else answers[0]


def _wired_world():
    """A store whose edges make the worklist: one condition
    resolving to COL, one scope reading TBL, one param edge that
    must be EXCLUDED."""
    store, read = _world()
    store.append_node("condition", "f::#s::cond#1",
                      {"kind": "COMPARE_EQ"}, T0, "test")
    store.append_node("param", "f::param/@d", {"name": "@d"},
                      T0, "test")
    store.append_node("scope", "f::#s", {"name": "#s"}, T0, "test")
    store.append_edge("resolves_to", "f::#s::cond#1", COL,
                      {"role": "subject"}, T0, "test")
    store.append_edge("resolves_to", "f::#s::cond#1", "f::param/@d",
                      {"role": "comparand"}, T0, "test")
    store.append_edge("reads", "f::#s", TBL, {}, T0, "test")
    return store, read


def test_name_worklist_is_what_actually_voices():
    _, read = _wired_world()
    from aivia.flows import enrich
    assert enrich.name_worklist(read) == [COL, TBL]  # param OUT


def test_name_worklist_dictionary_mode_covers_kg1():
    # rider (d) extension (Sunny, 2026-09-13: "why are we not
    # running for the dictionary"): a blessed name is per-column
    # truth, not per-file — dictionary mode sweeps ALL of KG1
    _, read = _wired_world()
    from aivia.flows import enrich
    full = enrich.name_worklist(read, scope="dictionary")
    assert DEPART in full  # never voiced by any condition — in
    assert set(enrich.name_worklist(read)) <= set(full)
    assert full == sorted(c for c in full if c.count("|") == 3) \
        + sorted(t for t in full if t.count("|") == 2)


def test_namer_double_run_agree_lands_proposed(tmp_path):
    from aivia.flows import enrich
    _, read = _wired_world()
    namer = _FakeNamer({"MAR_ACTION_CODE": ["administration action"],
                        "MED_ADMIN_RECORDS":
                        ["medication administration"]})
    counts = enrich.propose_blessed_names(
        read, tmp_path, namer, model="test-model",
        prompt_version="1.0.0", run_at=T0)
    assert counts["proposed"] == 2 and counts["model_calls"] == 4
    rows = glossary.load_blessed_subjects(tmp_path)
    row = rows[COL]
    assert row["status"] == "proposed"  # NEVER blessed by machine
    assert row["words"] == "administration action"
    assert row["description_hash"] == glossary.description_hash(COL_DESC)
    assert row["proposer"] == {"model": "test-model",
                               "prompt_version": "1.0.0", "runs": 2}
    # the seeder refuses the machine row until Sunny flips it
    store2, read2 = _world()
    seeded = glossary.seed_blessed_names(store2, read2, tmp_path)
    assert seeded["seeded"] == 0 and seeded["skipped_status"] == 2


def test_namer_disagreement_is_disputed_never_voiced(tmp_path):
    from aivia.flows import enrich
    _, read = _wired_world()
    namer = _FakeNamer({"MAR_ACTION_CODE":
                        ["administration action", "mar action"],
                        "MED_ADMIN_RECORDS":
                        ["medication administration"]})
    counts = enrich.propose_blessed_names(
        read, tmp_path, namer, model="m", prompt_version="1.0.0",
        run_at=T0)
    assert counts["disputed"] == 1 and counts["proposed"] == 1
    row = glossary.load_blessed_subjects(tmp_path)[COL]
    assert row["status"] == "disputed"
    assert row["candidates"] == ["administration action",
                                 "mar action"]
    assert "words" not in row  # a tie never voices


def test_namer_gate_kill_is_rejected_with_named_violations(tmp_path):
    from aivia.flows import enrich
    _, read = _wired_world()
    namer = _FakeNamer({"MAR_ACTION_CODE": ["delivery method"],
                        "MED_ADMIN_RECORDS":
                        ["medication administration"]})
    counts = enrich.propose_blessed_names(
        read, tmp_path, namer, model="m", prompt_version="1.0.0",
        run_at=T0)
    assert counts["rejected"] == 1
    row = glossary.load_blessed_subjects(tmp_path)[COL]
    assert row["status"] == "rejected"
    assert any("GATE-SUBJ-1" in v for v in row["violations"])


def test_namer_cache_spends_nothing_on_rerun(tmp_path):
    from aivia.flows import enrich
    _, read = _wired_world()
    cache = tmp_path / "names_cache.json"
    script = {"MAR_ACTION_CODE": ["administration action"],
              "MED_ADMIN_RECORDS": ["medication administration"]}
    n1 = _FakeNamer(script)
    enrich.propose_blessed_names(
        read, tmp_path, n1, model="m", prompt_version="1.0.0",
        run_at=T0, cache_path=cache)
    assert n1.calls == 4
    # registry wiped, cache kept: the re-run is FREE
    (tmp_path / "blessed_subjects.json").unlink()
    n2 = _FakeNamer(script)
    counts = enrich.propose_blessed_names(
        read, tmp_path, n2, model="m", prompt_version="1.0.0",
        run_at=T0, cache_path=cache)
    assert n2.calls == 0 and counts["proposed"] == 2
    # registry intact, same hash + prompt: rows are KEPT, no calls
    n3 = _FakeNamer(script)
    counts = enrich.propose_blessed_names(
        read, tmp_path, n3, model="m", prompt_version="1.0.0",
        run_at=T0, cache_path=cache)
    assert n3.calls == 0 and counts["kept"] == 2


def test_field_law_blessed_rows_are_machine_untouchable(tmp_path):
    from aivia.flows import enrich
    _, read = _wired_world()
    blessed_row = {"words": "sunny's own words",
                   "status": "blessed", "blessed_by": "person:sunny",
                   "blessed_at": T0,
                   "description_hash": "0" * 64}  # even STALE
    (tmp_path / "blessed_subjects.json").write_text(
        json.dumps({COL: blessed_row}))
    namer = _FakeNamer({"MAR_ACTION_CODE": ["administration action"],
                        "MED_ADMIN_RECORDS":
                        ["medication administration"]})
    counts = enrich.propose_blessed_names(
        read, tmp_path, namer, model="m", prompt_version="1.0.0",
        run_at=T0)
    assert counts["blessed_kept"] == 1
    assert glossary.load_blessed_subjects(tmp_path)[COL] == blessed_row


def test_namer_nothing_to_select_writes_no_row(tmp_path):
    from aivia.flows import enrich
    store, read = _wired_world()
    ghost = TBL + "|C2"
    store.append_node("column", ghost, {"description": ""},
                      T0, "test")
    store.append_edge("resolves_to", "f::#s::cond#1", ghost,
                      {"role": "comparand"}, T0, "test")
    namer = _FakeNamer({"MAR_ACTION_CODE": ["administration action"],
                        "MED_ADMIN_RECORDS":
                        ["medication administration"]})
    counts = enrich.propose_blessed_names(
        read, tmp_path, namer, model="m", prompt_version="1.0.0",
        run_at=T0)
    assert counts["nothing_to_select"] == 1
    assert ghost not in glossary.load_blessed_subjects(tmp_path)
