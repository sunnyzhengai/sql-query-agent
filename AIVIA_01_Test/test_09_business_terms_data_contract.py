"""Phase 09 contract tests (09_business_terms_data_contract.md,
D1-D8 STAMPED 2026-10-05; THE CONSOLIDATION RULING same day:
one delivery file, ai_delivery.json — each step updates its
keys; the consumption-rule row diet; retired: the standalone
sheet, the export, the ledger).

Fixtures are SYNTHETIC with invented names only (the estate
boundary). The LLM seat is INJECTED (proposer=) — deterministic,
free, offline; production's paid seat is never touched here.

The locks:
  L1  D2 concept rule: plumbing is NOT a row — a counted skip;
      no LLM call for it
  L2  D1 placement: tied terms under reports[], untied under
      reportless_files[]; structure replaces report_tie
  L3  D4 technical definition: Population / Exclusions /
      Parameters, negated -> Exclusions
  L4  D4 voice law: no SQL, no table names, no @
  L5  D5 uniqueness: collision flagged, never renamed; no bless
  L6  the one gate fails a bad card; failing rows carry
      gate_findings + rounds_used; no bless, no blessed rows
  L7  bless flips in place via the registry; ruled fields
      survive a rebuild; the row diet holds on clean rows
  L8  counts.09 equations (a test, not advice)
  L9  byte determinism of ai_delivery.json
  L10 one gate: no local gate; every check is grain term_card
  L11 the term-card arm lives in business_descriptions.gate
  L12 the repair loop feeds named findings back (budget 3)
  L13 only_file scopes the run AND preserves other files' terms
  L14 the retired files are never written
  L15 assemble writes reports/description keys, preserves terms
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
sys.path.insert(0, str(CODE_DIR))

A = "file::FIX_RPT_ALPHA"
B = "file::FIX_RPT_BETA"
A_DELIV = A + "::scope/delivery"
A_SUB = A + "::stmt/1::scope/sub1"
B_DELIV = B + "::scope/delivery"
RETIRED = ("09_business_terms.json", "09_collibra_export.json",
           "09_terms_ledger.json")


# ------------------------- the synthetic fixture (invented names)

def _w(d, name, obj):
    (d / name).write_text(json.dumps(obj, indent=1))


def _fixture(tmp_path):
    d05, d06, d02, d07, d08, out = (
        tmp_path / n for n in ("05", "06", "02", "07", "08", "09"))
    for d in (d05, d06, d02, d07, d08, out):
        d.mkdir()

    _w(d05, "05_semantic_graph_scope_output.json", [
        {"node_id": A_DELIV, "scope_name": "delivery",
         "scope_kind": "delivery", "operation": "select",
         "owning_statement": A + "::stmt/1",
         "evidence": {"fragment": "SELECT fix"}},
        {"node_id": A_SUB, "scope_name": "sub1",
         "scope_kind": "subquery", "operation": "select",
         "owning_statement": A + "::stmt/1",
         "evidence": {"fragment": "SELECT value"}},
        {"node_id": B_DELIV, "scope_name": "delivery",
         "scope_kind": "delivery", "operation": "select",
         "owning_statement": B + "::stmt/1",
         "evidence": {"fragment": "SELECT fix"}},
    ])
    _w(d05, "05_semantic_graph_structure_output.json", [
        {"node_id": A_DELIV + "::structure/FROM/1",
         "structure_kind": "FROM", "position": 1,
         "owning_scope": A_DELIV, "evidence": {"fragment": "f"}},
        {"node_id": A_DELIV + "::structure/WHERE/1",
         "structure_kind": "WHERE", "position": 2,
         "owning_scope": A_DELIV, "evidence": {"fragment": "w"}},
        {"node_id": A_SUB + "::structure/FROM/1",
         "structure_kind": "FROM", "position": 1,
         "owning_scope": A_SUB, "evidence": {"fragment": "p"}},
        {"node_id": B_DELIV + "::structure/FROM/1",
         "structure_kind": "FROM", "position": 1,
         "owning_scope": B_DELIV, "evidence": {"fragment": "f"}},
        {"node_id": B_DELIV + "::structure/WHERE/1",
         "structure_kind": "WHERE", "position": 2,
         "owning_scope": B_DELIV, "evidence": {"fragment": "w"}},
    ])
    _w(d05, "05_semantic_graph_predicate_output.json", [
        {"node_id": A_DELIV + "::structure/WHERE/1::pred/1",
         "predicate_kind": "COMPARE_EQ", "negated": False,
         "position": 1, "on_class": "where",
         "evidence": {"fragment": "fx.FLAG = 1"}},
        {"node_id": A_DELIV + "::structure/WHERE/1::pred/2",
         "predicate_kind": "IN_LIST", "negated": True,
         "position": 2, "on_class": "where",
         "evidence": {"fragment": "fx.UNIT NOT IN ('X')"}},
        {"node_id": B_DELIV + "::structure/WHERE/1::pred/1",
         "predicate_kind": "COMPARE_EQ", "negated": False,
         "position": 1, "on_class": "where",
         "evidence": {"fragment": "fx.FLAG = 1"}},
    ])
    _w(d05, "05_semantic_graph_parameter_output.json", [
        {"node_id": A + "::param/@FixStart", "name": "@FixStart",
         "kind": "procedure_parameter", "data_type": "DATE",
         "default_text": None,
         "evidence": {"fragment": "@FixStart DATE"}},
    ])
    _w(d05, "05_semantic_graph_resolves_edges_output.json", [
        {"from_id": A_DELIV + "::structure/FROM/1::expr/1",
         "ref_text": "fixdb..FIX_TABLE_ONE", "to_kind": "table",
         "to_id": "FIX_TABLE_ONE", "match_basis": "exact"},
        {"from_id": B_DELIV + "::structure/FROM/1::expr/1",
         "ref_text": "fixdb..FIX_TABLE_TWO", "to_kind": "table",
         "to_id": "FIX_TABLE_TWO", "match_basis": "exact"},
    ])

    def _row(nid, grain, sentence):
        return {"node_id": nid, "grain": grain,
                "sentence": sentence, "basis_version": "06.3.0",
                "evidence_refs": [nid]}
    _w(d06, "06_technical_descriptions_output.json", [
        _row(A, "file", "Delivers a selection of alpha records."),
        _row(B, "file", "Delivers a selection of beta records."),
        _row(A_DELIV, "scope",
             "This is a selection of alpha fix records."),
        _row(A_SUB, "scope",
             "This is a selection from a run-time choice list."),
        _row(B_DELIV, "scope",
             "This is a selection of beta fix records."),
        _row(A_DELIV + "::structure/WHERE/1::pred/1", "predicate",
             "The fix flag of the alpha record is recorded."),
        _row(A_DELIV + "::structure/WHERE/1::pred/2", "predicate",
             "The fix unit is none of the values 'FIX DEPT ONE'."),
        _row(B_DELIV + "::structure/WHERE/1::pred/1", "predicate",
             "The fix flag of the beta record is recorded."),
    ])

    _w(d07, "07_business_descriptions_blessings_output.json",
       {"_law": "test fixture", "names": [], "sentences": []})
    _w(d08, "08_pbi_lineage_output.json", [
        {"name": "Fix Dashboard",
         "executes": ["FIX_RPT_ALPHA.sql"], "bound_fields": {},
         "bindings": [], "source": "tmdl (fix)"},
    ])
    return d05, d06, d02, d07, d08, out


_GOOD_CARD = ("Definition: The alpha fix selection.\n"
              "One row is: one alpha fix record.\n"
              "Keeps: records where the fix flag is recorded.\n"
              "Excludes: records in the unit FIX DEPT ONE.")

# the collision pair: same name after normalization
_NAMES = {A_DELIV: "Fix Census Events",
          B_DELIV: "fix census event."}


def _proposer(spec):
    return {"bt_name": _NAMES[spec["node_id"]],
            "business_description": _GOOD_CARD}


def _delivery(out):
    # THE NAMING LAW (2026-10-08): the delivery writes
    # 12_ai_delivery_output.json. RED until the 0.7.0 code lands.
    return json.loads(
        (out / "12_ai_delivery_output.json").read_text())


def _terms(delivery):
    """Flatten: [(parent_kind, parent, row)]."""
    out = []
    for e in delivery["reports"]:
        for t in e.get("terms", []):
            out.append(("report", e, t))
    for e in delivery["reportless_files"]:
        for t in e.get("terms", []):
            out.append(("reportless", e, t))
    return out


def _get(delivery, node_id):
    for _, _, t in _terms(delivery):
        if t["node_id"] == node_id:
            return t
    raise AssertionError(f"no term row {node_id}")


def _build(tmp_path, proposer=_proposer, **kw):
    import business_terms as bt
    dirs = _fixture(tmp_path)
    bt.build09(*dirs, proposer=proposer, **kw)
    return bt, _delivery(dirs[-1]), dirs


# ---------------------------------------------------- the locks

def test_09_l1_concept_rule_and_no_llm_for_plumbing(tmp_path):
    called = []

    def spy(spec):
        called.append(spec["node_id"])
        return _proposer(spec)

    _, delivery, _ = _build(tmp_path, proposer=spy)
    assert sorted(called) == [A_DELIV, B_DELIV]
    ids = [t["node_id"] for _, _, t in _terms(delivery)]
    assert A_SUB not in ids              # plumbing is not a row
    skipped = delivery["counts"]["09"]["skipped"]
    assert any(s["node_id"] == A_SUB and "parameter" in s["reason"]
               for s in skipped)


def test_09_l2_placement_replaces_report_tie(tmp_path):
    _, delivery, _ = _build(tmp_path)
    rep = next(e for e in delivery["reports"]
               if e["report"] == "Fix Dashboard")
    assert "FIX_RPT_ALPHA.sql" in rep["files"]
    assert any(t["node_id"] == A_DELIV for t in rep["terms"])
    free = next(e for e in delivery["reportless_files"]
                if e["file"] == "FIX_RPT_BETA")
    assert any(t["node_id"] == B_DELIV for t in free["terms"])
    assert "report_tie" not in _get(delivery, A_DELIV)


def test_09_l3_technical_definition_sections_and_split(tmp_path):
    _, delivery, _ = _build(tmp_path)
    td = _get(delivery, A_DELIV)["technical_definition"]
    p, e, pa = (td.index("Population:"), td.index("Exclusions:"),
                td.index("Parameters:"))
    assert p < e < pa
    flag = td.index("fix flag of the alpha record")
    unit = td.index("none of the values 'FIX DEPT ONE'")
    assert p < flag < e < unit < pa
    assert "no default" in td[pa:]
    assert td.count("\n- ") >= 3


def test_09_l4_technical_definition_voice_law(tmp_path):
    _, delivery, _ = _build(tmp_path)
    td = _get(delivery, A_DELIV)["technical_definition"]
    assert "FIX_TABLE_ONE" not in td
    assert "@" not in td
    assert "fix start" in td.lower()
    assert "Source" not in td and "Carries" not in td
    assert "SELECT" not in td and "WHERE" not in td


def test_09_l5_collision_flagged_never_silently_renamed(tmp_path):
    bt, delivery, dirs = _build(tmp_path)
    a, b = _get(delivery, A_DELIV), _get(delivery, B_DELIV)
    assert a["name_collision"] is None
    assert b["name_collision"] is not None
    assert b["bt_name"] == _NAMES[B_DELIV]
    try:
        bt.bless(dirs[-1], dirs[3], B_DELIV, "FIX_RPT_BETA",
                 "RULED t")
        raise AssertionError("a collided row must not bless")
    except ValueError:
        pass


def test_09_l6_bad_card_fails_with_audit_no_bless(tmp_path):
    def bad(spec):
        return {"bt_name": "Fix Thing " + spec["node_id"][7:16],
                "business_description":
                    "Definition: x.\nOne row is: y.\n"
                    "Keeps: records other than held ones."}

    bt, delivery, dirs = _build(tmp_path, proposer=bad)
    r = _get(delivery, A_DELIV)
    assert r["status"] == "gate_failed"
    assert r["gate_findings"] and r["rounds_used"] == 3
    try:
        bt.bless(dirs[-1], dirs[3], A_DELIV, "Fix Dashboard",
                 "RULED t")
        raise AssertionError("a failed card must not bless")
    except ValueError:
        pass
    assert not any(t["bt_name_status"] == "blessed"
                   for _, _, t in _terms(delivery))


def test_09_l7_bless_in_place_diet_and_rebuild_survival(tmp_path):
    bt, delivery, dirs = _build(tmp_path)
    out, d07 = dirs[-1], dirs[3]
    clean = _get(delivery, A_DELIV)
    assert clean["status"] == "gate_passed"
    for dead in ("gate_findings", "rounds_used", "report_tie",
                 "scope_kind", "concept_reason", "basis_version"):
        assert dead not in clean, dead   # the row diet
    assert delivery["basis"]["07"]       # basis once, at the top
    bt.bless(out, d07, A_DELIV, "Fix Dashboard", "RULED test")
    bt.build09(*dirs, proposer=_proposer)   # the rebuild
    delivery = _delivery(out)
    r = _get(delivery, A_DELIV)
    assert r["bt_name_status"] == "blessed"
    assert r["blessing"] == "RULED test"
    assert delivery["counts"]["09"]["blessed"] == 1


def test_09_l8_counts_equations(tmp_path):
    _, delivery, _ = _build(tmp_path)
    c = delivery["counts"]["09"]
    assert c["scopes_total"] == \
        c["plumbing_skipped"] + c["concepts"]
    assert c["report_rows"] + c["reportless_rows"] == \
        len(_terms(delivery))
    assert c["plumbing_skipped"] == len(c["skipped"])


def test_09_l9_byte_determinism(tmp_path):
    import business_terms as bt
    d1, d2 = tmp_path / "one", tmp_path / "two"
    d1.mkdir()
    d2.mkdir()
    f1, f2 = _fixture(d1), _fixture(d2)
    bt.build09(*f1, proposer=_proposer)
    bt.build09(*f2, proposer=_proposer)
    assert (f1[-1] / "12_ai_delivery_output.json").read_bytes() \
        == (f2[-1] / "12_ai_delivery_output.json").read_bytes()


def test_09_l10_one_gate_no_local_gate(tmp_path, monkeypatch):
    import business_descriptions as bd
    import business_terms as bt
    assert not hasattr(bt, "card_gate")
    grains = []
    real = bd.gate

    def spy(text, docket, grain, registry=None):
        grains.append(grain)
        return real(text, docket, grain, registry)

    monkeypatch.setattr(bd, "gate", spy)
    dirs = _fixture(tmp_path)
    bt.build09(*dirs, proposer=_proposer)
    assert grains and set(grains) == {"term_card"}


def test_09_l11_term_card_arm_lives_in_the_one_gate():
    import business_descriptions as bd
    docket = "the fix flag of the alpha record / FIX DEPT ONE"
    assert bd.gate(_GOOD_CARD, docket, "term_card") == []
    shape = bd.gate("Definition: a thing.", docket, "term_card")
    assert any("four labeled lines" in f for f in shape)
    neg = _GOOD_CARD.replace(
        "Keeps: records where the fix flag is recorded.",
        "Keeps: records other than held ones.")
    owned = bd.gate(neg, docket, "term_card")
    assert any("ONLY on Excludes" in f for f in owned)
    leak = _GOOD_CARD.replace("the fix flag", "@FixFlag")
    assert any("@FixFlag" in f
               for f in bd.gate(leak, docket, "term_card"))


def test_09_l12_repair_loop_feeds_findings_back(tmp_path):
    rounds_seen = []

    def learning(spec):
        rounds_seen.append(list(spec["findings"]))
        if spec["findings"]:
            return _proposer(spec)
        bad = dict(_proposer(spec))
        bad["business_description"] = _GOOD_CARD.replace(
            "the fix flag", "@FixFlag")
        return bad

    _, delivery, _ = _build(tmp_path, proposer=learning)
    r = _get(delivery, A_DELIV)
    assert r["status"] == "gate_passed"
    assert "rounds_used" not in r        # audit only on failure
    assert rounds_seen[0] == [] and rounds_seen[1]


def test_09_l13_only_file_scopes_and_preserves(tmp_path):
    import business_terms as bt
    dirs = _fixture(tmp_path)
    bt.build09(*dirs, proposer=_proposer)          # full run

    def renamer(spec):
        return {"bt_name": "Alpha Renamed Term",
                "business_description": _GOOD_CARD}

    bt.build09(*dirs, proposer=renamer,
               only_file="FIX_RPT_ALPHA")          # partial run
    delivery = _delivery(dirs[-1])
    assert _get(delivery, A_DELIV)["bt_name"] == \
        "Alpha Renamed Term"
    assert _get(delivery, B_DELIV)["bt_name"] == \
        _NAMES[B_DELIV]                  # untouched by the filter


def test_09_l14_retired_files_never_written(tmp_path):
    _, _, dirs = _build(tmp_path)
    for name in RETIRED:
        assert not (dirs[-1] / name).exists(), name


def test_09_l15_assemble_writes_descriptions_preserves_terms(
        tmp_path):
    import ai_delivery
    import business_terms as bt
    dirs = _fixture(tmp_path)
    d06, d07, d08, out = dirs[1], dirs[3], dirs[4], dirs[-1]
    bt.build09(*dirs, proposer=_proposer)
    _w(d07, "07_business_descriptions_output.json", [
        {"node_id": A, "grain": "file", "status": "gate_passed",
         "audience_text": "One row is: one alpha fix record."},
    ])
    ai_delivery.assemble(out, d07, d08, d06)
    delivery = _delivery(out)
    rep = next(e for e in delivery["reports"]
               if e["report"] == "Fix Dashboard")
    assert rep["description"]["voice"] == "business"
    assert rep["description"]["text"].startswith("One row is:")
    free = next(e for e in delivery["reportless_files"]
                if e["file"] == "FIX_RPT_BETA")
    assert free["description"]["voice"] == "technical"  # 06 floor
    assert any(t["node_id"] == A_DELIV for t in rep["terms"])
    assert any(t["node_id"] == B_DELIV for t in free["terms"])


# --------------------------------------- incremental delivery (D12)
# 10_work_wheel.md D12, ruled 2026-10-07: a skipped file's terms are
# never re-proposed — its rows survive in ai_delivery.json untouched
# (the L13 only_file precedent, inverted: skip names the DONE set).

def test_09_l16_skip_files_no_proposals_terms_carried(tmp_path):
    bt, delivery1, dirs = _build(tmp_path)        # the prior full run
    alpha_before = _get(delivery1, A_DELIV)

    called = []

    def spy(spec):
        called.append(spec["node_id"])
        return _proposer(spec)

    bt.build09(*dirs, proposer=spy,
               skip_files={"FIX_RPT_ALPHA"})
    delivery2 = _delivery(dirs[-1])
    assert all(not n.startswith(A) for n in called), called
    assert any(n.startswith(B) for n in called)
    assert _get(delivery2, A_DELIV) == alpha_before
    assert _get(delivery2, B_DELIV)


def test_09_l17_defer_files_dropped_without_carry(tmp_path):
    """D12 batch door: a deferred file proposes nothing and lands
    nothing — and unlike skip, nothing prior is required."""
    bt, _, dirs = _build(tmp_path)

    called = []

    def spy(spec):
        called.append(spec["node_id"])
        return _proposer(spec)

    bt.build09(*dirs, proposer=spy,
               defer_files={"FIX_RPT_BETA"})
    assert all(not n.startswith(B) for n in called), called


# ------------------- the delivered-goods ruling (2026-10-08, 0.7.0)
# 09 contract amendment + D14: membership = the ledger; a report
# appears from its first described file with files_described[] +
# files_waiting[]; waiting files appear nowhere; gate_failed rides
# out honestly; no ledger at all = legacy unfiltered (home estate).

LEDGER_OUT = "10_corpus_ledger_output.json"


def _ledgered(out, *stems):
    _w(out, LEDGER_OUT,
       {"hashes": {s + ".sql": "fix-hash" for s in stems}})


def test_09_l18_membership_is_the_ledger(tmp_path):
    """Alpha described, beta waiting: beta appears NOWHERE."""
    import ai_delivery
    dirs = _fixture(tmp_path)
    d06, d07, d08, out = dirs[1], dirs[3], dirs[4], dirs[-1]
    _ledgered(out, "FIX_RPT_ALPHA")
    ai_delivery.assemble(out, d07, d08, d06)
    delivery = _delivery(out)
    rep = next(e for e in delivery["reports"]
               if e["report"] == "Fix Dashboard")
    assert rep["files_described"] == ["FIX_RPT_ALPHA.sql"]
    assert rep["files_waiting"] == []          # complete
    assert delivery["reportless_files"] == []  # beta is waiting


def test_09_l19_half_described_report_says_its_lists(tmp_path):
    """A two-file report enters on its first described file and
    names what is missing; a zero-described report is absent."""
    import ai_delivery
    dirs = _fixture(tmp_path)
    d06, d07, d08, out = dirs[1], dirs[3], dirs[4], dirs[-1]
    _w(d08, "08_pbi_lineage_output.json", [
        {"name": "Fix Dashboard",
         "executes": ["FIX_RPT_ALPHA.sql", "FIX_RPT_BETA.sql"],
         "bound_fields": {}, "bindings": [],
         "source": "tmdl (fix)"},
        {"name": "Fix Other",
         "executes": ["FIX_RPT_BETA.sql"], "bound_fields": {},
         "bindings": [], "source": "tmdl (fix)"},
    ])
    _ledgered(out, "FIX_RPT_ALPHA")
    ai_delivery.assemble(out, d07, d08, d06)
    delivery = _delivery(out)
    assert [e["report"] for e in delivery["reports"]] \
        == ["Fix Dashboard"]                    # Fix Other: zero
    rep = delivery["reports"][0]
    assert rep["files_described"] == ["FIX_RPT_ALPHA.sql"]
    assert rep["files_waiting"] == ["FIX_RPT_BETA.sql"]
    assert "alpha" in rep["description"]["text"]
    assert "beta" not in rep["description"]["text"]


def test_09_l20_gate_failed_status_rides_out(tmp_path):
    """Processed-but-failed is honest: technical voice, status
    gate_failed — distinguishable from never-processed."""
    import ai_delivery
    dirs = _fixture(tmp_path)
    d06, d07, d08, out = dirs[1], dirs[3], dirs[4], dirs[-1]
    _w(d07, "07_business_descriptions_output.json", [
        {"node_id": A, "grain": "file", "status": "gate_failed",
         "audience_text": "A card that failed the gate."},
    ])
    _ledgered(out, "FIX_RPT_ALPHA")
    ai_delivery.assemble(out, d07, d08, d06)
    rep = _delivery(out)["reports"][0]
    assert rep["description"]["voice"] == "technical"
    assert rep["description"]["status"] == "gate_failed"


def test_09_l21_no_ledger_is_legacy_unfiltered(tmp_path):
    """The home estate has no ledger: membership unfiltered —
    one law, two honest modes (work always has a ledger)."""
    import ai_delivery
    dirs = _fixture(tmp_path)
    d06, d07, d08, out = dirs[1], dirs[3], dirs[4], dirs[-1]
    ai_delivery.assemble(out, d07, d08, d06)
    delivery = _delivery(out)
    assert [e["report"] for e in delivery["reports"]] \
        == ["Fix Dashboard"]
    assert [e["file"] for e in delivery["reportless_files"]] \
        == ["FIX_RPT_BETA"]


def test_09_l23_awaiting_human_ships_no_text_and_its_questions(
        tmp_path):
    """D15 (2026-10-08 evening): a described file whose card
    awaits her ships NO business text — voice none, questions
    on the entry; never the technical floor in the slot."""
    import ai_delivery
    dirs = _fixture(tmp_path)
    d06, d07, d08, out = dirs[1], dirs[3], dirs[4], dirs[-1]
    _w(d07, "07_business_descriptions_output.json", [
        {"node_id": A, "grain": "file",
         "status": "awaiting_human", "audience_text": "",
         "last_proposal": "wanted 999",
         "questions": [{"number": "999",
                        "finding": "V-1: number 999 has no "
                                   "stored basis"}]},
    ])
    _ledgered(out, "FIX_RPT_ALPHA")
    ai_delivery.assemble(out, d07, d08, d06)
    rep = _delivery(out)["reports"][0]
    assert rep["description"]["status"] == "awaiting_human"
    assert rep["description"]["text"] == ""
    assert rep["description"]["voice"] == "none"
    (q,) = rep["questions"]
    assert q["number"] == "999"


def test_09_l22_load_migrates_the_old_delivery_name(tmp_path):
    """A pre-rename tenant's ai_delivery.json (terms, blessings)
    is read once; every write lands the new name."""
    import ai_delivery
    dirs = _fixture(tmp_path)
    d06, d07, d08, out = dirs[1], dirs[3], dirs[4], dirs[-1]
    _w(out, "ai_delivery.json", {
        "basis": {"fix": "old-name-marker"}, "reports": [],
        "reportless_files": [], "counts": {}})
    assert ai_delivery.load(out)["basis"] \
        == {"fix": "old-name-marker"}
    ai_delivery.assemble(out, d07, d08, d06)
    assert (out / "12_ai_delivery_output.json").exists()
