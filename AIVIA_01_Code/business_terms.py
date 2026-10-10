"""Phase 09 — Business Terms, THE GOVERNANCE EXPORT.

Contract: AIVIA_01_Design/09_business_terms_data_contract.md
(D1-D8 STAMPED 2026-10-05). BUSINESS TERM is the reserved
keyword (the vocabulary keyword law): the specific meaning of a
finite data set, defined in a SQL logic block, specific to the
org's reality. The LLM PROPOSES a name and a card, a NO-MODEL
MECHANICAL GATE checks shape and ownership, Sunny BLESSES; only
blessed terms with a report reach the Collibra export.

Tests: AIVIA_01_Test/test_09_business_terms_data_contract.py
(9 locks, RED 2026-10-05 before this file existed).
"""

# ==== PHASE 09 PSEUDO CODE — awaiting Sunny's approval ==============
# (standing process: real code lands below only after her stamp;
# the suite is red now — 9 locks, ModuleNotFoundError.)
#
# BASIS: basis_version on every row = business_descriptions
#   .BASIS_VERSION (the 07 grammar constant, per the contract) —
#   one import, never a second constant to drift.
#
# THE INPUTS (all read-only; the build writes only out09):
#   dir05: 05_semantic_graph_scope_output / 05_semantic_graph_structure_output /
#     05_semantic_graph_predicate_output / 05_semantic_graph_parameter_output /
#     05_semantic_graph_resolves_edges_output
#   dir06: 06_technical_descriptions_output (scope + predicate sentences —
#     already dictionary-voiced; the build NEVER re-words them)
#   dir02: reserved for the voice overlay at the Fabric move;
#     unread this slice (named here so the signature is stable)
#   dir07: 07_business_descriptions_blessings_output.json — ruled truth; the build
#     READS blessings and NEVER writes (bless() is the one door)
#   dir08: 08_pbi_lineage_output.json — the (sql file -> report) tie;
#     FILE MAY BE ABSENT locally (it lives on Fabric): absent ->
#     every row lands report-less, counted, honest.
#
# build09(dir05, dir06, dir02, dir07, dir08, out09,
#         proposer=None):
#
#   1. D2 THE CONCEPT RULE (mechanical): for each scope in the
#      05 scope sheet — collect its structures (owning_scope),
#      then every resolves edge whose from_id sits under one of
#      those structures; any edge with to_kind == "table" ->
#      is_business_concept True, reason "reads table <to_id>";
#      none -> False, reason "parameter-only or constant-only
#      sources". Plumbing rows STAY in the sheet (counted),
#      carry bt_name None, and get NO paid call (lock L1).
#
#   2. D1 THE ROWS: the scope's file name = node_id's second
#      segment. Reports = every 08 row whose executes carries
#      "<file>.sql" -> one sheet row per (scope, report).
#      No 08 match -> ONE row with report = the file name,
#      counted reportless in the ledger, NEVER exported (L2).
#
#   3. D4 THE TECHNICAL DEFINITION (deterministic, zero model):
#      the scope's OWN predicates = predicate-sheet rows whose
#      node_id sits under the scope AND on_class != "join_pair"
#      (join matching was removed from the shape by her ruling;
#      a scope speaks only its own WHERE). Each predicate's
#      BULLET is its 06 sentence VERBATIM — negated False ->
#      Population, negated True -> Exclusions (the mechanical
#      split). Parameters = the FILE's 05 parameter rows, each
#      voiced plainly by rule: strip "@", split CamelCase and
#      underscores, lowercase, prefix "the" -> "the fix start";
#      suffix "(no default)" or "(default: <default_text>)".
#      Render:  "Population:\n- <s>\n- <s>\n\nExclusions:\n
#      - <s>\n\nParameters:\n- <p>"  — a section with zero
#      bullets is OMITTED (honest silence, R7 precedent).
#      No table names, no "@", no Source, no Carries can enter:
#      every bullet is a 06 sentence or a rule-voiced parameter
#      (locks L3/L4).
#
#   4. D3+D5 THE PROPOSAL (the only paid path; concepts only,
#      ONE call per scope — its rows share it): docket = the 06
#      scope sentence + its predicate bullets + the technical
#      definition. proposer(spec) with spec = {"node_id",
#      "docket"}; returns {"bt_name", "business_description"}.
#      proposer=None -> _openai_proposer (the paid seat, model
#      per the 07 parity law; SYSTEM text = the tone law + the
#      keyword law + the card labels + "the name states what
#      the population IS — never echo SQL"; no concrete example
#      sentences ride in the prompt — the examples-are-data
#      law).
#
#   5. THE CARD GATE (mechanical, zero model): the card must be
#      EXACTLY the four labeled lines, in order — "Definition:",
#      "One row is:", "Keeps:", "Excludes:" — and negative
#      language ("other than", "excluded", "exclude", " not ",
#      "except") may appear ONLY on the Excludes line (the
#      line-ownership law at scope grain). Findings -> status
#      "gate_failed", gate_findings kept verbatim on the row;
#      clean -> "gate_passed". ONE round this slice — no repair
#      loop (declared debt, the Echo Law names the build trigger:
#      the first real gate_failed on the census corpus).
#
#   6. D5 THE UNIQUENESS LAW: _normalize(name) = lowercase,
#      strip punctuation, fold each token's trailing "s" (both
#      sides fold identically — census/censuses meet). Walk the
#      sheet in sorted (node_id, report) order; the FIRST
#      occurrence of a normalized name is clean, every later
#      hit gets name_collision = the first row's bt_name —
#      kept, flagged, NEVER silently renamed (L5).
#
#   7. THE BLESSED RESTORE (delta-by-name, the ruled-fields
#      law): registry rows under "terms" — {node_id, report,
#      bt_name, ruling} — override the machine proposal: status
#      "blessed", her name wins. A rebuild regenerates every
#      machine field and may NEVER touch a ruled one (L7).
#
#   8. THE WRITE (deterministic bytes: sorted rows, indent=1,
#      no timestamps — L9):
#      09_business_terms.json  — every row (concepts AND
#        plumbing), fields per the contract incl.
#        name_collision and basis_version
#      09_collibra_export.json — rows where: blessed AND
#        is_business_concept AND report tied via 08 AND
#        name_collision is None AND status != "gate_failed"
#      09_terms_ledger.json    — counts {scopes_total,
#        plumbing_skipped, concepts, report_rows,
#        reportless_rows, blessed, proposed, exported}
#      THE EQUATIONS, asserted before any byte lands (a red
#      ledger does not ship -> raise, write nothing):
#        scopes_total == plumbing_skipped + concepts
#        report_rows + reportless_rows == len(rows)
#        exported == the export file's row count
#
#   returns the sheet rows (the tests' surface).
#
# bless(out09, dir07, node_id, report, ruling):
#   HER HAND ONLY — the ratify clause: the decision is hers, the
#   write is machine-executed at her explicit ruling, recorded
#   verbatim. Refuses (ValueError, named reason) when the row:
#   is absent / is plumbing / is gate_failed (L6) / carries a
#   name_collision (L5). Otherwise: append {node_id, report,
#   bt_name, ruling} to the registry's "terms" list (delta-by-
#   name: one entry per (node_id, report), re-bless replaces),
#   flip the sheet row to blessed, regenerate export + ledger
#   (same deterministic writer as build09 step 8).
#
# _openai_proposer(spec): the paid seat — key from .env /
#   AZURE per the operational facts; NEVER imported by the test
#   suite's path (proposer= is injected there; zero cost, zero
#   network in CI).
# ====================================================================
# ==== (pseudo code APPROVED 2026-10-05, Sunny: "approved. write
#       the actual code" — real code follows) =======================
# ==== SUPERSESSION NOTE 2026-10-05 (same day, the first real
# run's SQL-leak find): THE ONE-GATE RULING replaces two pseudo
# clauses above — (step 5) the 09-local card gate is RETIRED:
# the card is checked by business_descriptions.gate (V-1/V-2/
# V-3/V-7 + the new V-4 SCOPE arm in THAT gate; 09 ships no
# gate of its own, test-locked); the one-round deferral is
# RETIRED (its Echo trigger fired on run 1, twice): repair
# loop budget 3, the _propose_loop pattern; the prompt rides
# bd.SYSTEM_PROMPT. The 09 design D3 + both contracts carry
# the ruling; red tests precede the code change, per the
# standing process. =============================================

import json
import re
from pathlib import Path

import ai_delivery
import business_descriptions as bd

BASIS_VERSION = bd.BASIS_VERSION  # the 07 grammar constant — one truth

# ==== CONSOLIDATION NOTE 2026-10-05 (same day, her ruling:
# "all we need is a consolidated file... name it ai_delivery
# .json"): the three 09 output files are RETIRED — build09 now
# writes the terms[] + counts.09 keys of ai_delivery.json via
# the ai_delivery module; the row diet applies (no report_tie /
# scope_kind / concept_reason; audit fields only on failures;
# plumbing is a counted skip, not a row); bless() delegates to
# ai_delivery.bless_term. The 09 contract carries the ruling. ====

# The repair budget (the one-gate ruling, 2026-10-05 — the 07
# _propose_loop precedent; the one-round debt retired the day
# its Echo trigger fired).
REPAIR_BUDGET = 3
REGISTRY = "07_business_descriptions_blessings_output.json"
REGISTRY_OLD = "07_blessing_registry.json"   # pre-0.7.0 tenants


def _read(path):
    return json.loads(Path(path).read_text())


def _maybe(path, default):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else default


def _file_of(node_id):
    return node_id.split("::")[1]


def _concept_verdict(scope_id, structures, edges):
    """D2 — mechanical: any resolves edge from this scope's
    structures to a dictionary table makes it a concept."""
    own = [s["node_id"] for s in structures
           if s["owning_scope"] == scope_id]
    for e in sorted(edges, key=lambda e: e["from_id"]):
        if e.get("to_kind") != "table":
            continue
        if any(e["from_id"] == sid or e["from_id"].startswith(sid + "::")
               for sid in own):
            return True, f"reads table {e['to_id']}"
    return False, "parameter-only or constant-only sources"


def _voice_param(row):
    """D4 voice law: '@FixStart' -> 'the fix start (no default)'."""
    name = row["name"].lstrip("@").replace("_", " ")
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    spoken = "the " + " ".join(words.lower().split())
    d = row.get("default_text")
    return f"{spoken} ({'default: ' + str(d) if d else 'no default'})"


def _technical_definition(scope_id, structures, preds, sentences,
                          fparams):
    """D4 — deterministic: every bullet is a 06 sentence verbatim
    or a rule-voiced parameter; negated -> Exclusions; an empty
    section is omitted (honest silence)."""
    own = [s["node_id"] for s in structures
           if s["owning_scope"] == scope_id]
    mine = sorted((p for p in preds
                   if p.get("on_class") != "join_pair"
                   and any(p["node_id"].startswith(sid + "::")
                           for sid in own)),
                  key=lambda p: p["node_id"])
    pop = [sentences[p["node_id"]] for p in mine
           if not p["negated"] and p["node_id"] in sentences]
    exc = [sentences[p["node_id"]] for p in mine
           if p["negated"] and p["node_id"] in sentences]
    par = [_voice_param(r)
           for r in sorted(fparams, key=lambda r: r["name"])]
    parts = [label + "".join(f"\n- {b}" for b in bullets)
             for label, bullets in (("Population:", pop),
                                    ("Exclusions:", exc),
                                    ("Parameters:", par))
             if bullets]
    return "\n\n".join(parts)


def _propose(proposer, node_id, docket):
    """THE REPAIR LOOP over THE ONE GATE (business_descriptions
    .gate, grain term_card — 09 ships no gate of its own). Named
    findings return to the proposer; budget 3; a call failure is
    a failed round, never a dead build (the 07 precedent).
    TIERED (11 D2/D3): the round rides the spec; the paid
    proposer seats SMALL on rounds 1-2, LARGE on round 3, and
    reports its seat as "_seat" — the row's honest model record.
    An AccountRefusal stops the batch at the first refusal."""
    findings, prop, seat = [], None, None
    for round_no in range(1, REPAIR_BUDGET + 1):
        try:
            prop = proposer({"node_id": node_id, "docket": docket,
                             "findings": list(findings),
                             "round": round_no})
        except bd.AccountRefusal:
            raise  # D6b: never a failed round
        except Exception as exc:  # noqa: BLE001
            findings = [f"call failed: {type(exc).__name__}: "
                        f"{str(exc)[:200]}"]
            bd._meter_causes(findings)
            continue
        if isinstance(prop, dict) and "_seat" in prop:
            seat = prop.pop("_seat")
            if seat == bd._MODEL_LARGE:
                bd._METER["escalations"]["fired"] += 1
        findings = bd.gate(prop["business_description"], docket,
                           "term_card")
        if not findings:
            bd._meter_round(round_no)
            if seat == bd._MODEL_LARGE:
                bd._METER["escalations"]["landed"] += 1
            return prop, "gate_passed", [], round_no, seat
        bd._meter_causes(findings)
    prop = prop or {"bt_name": None, "business_description": None}
    return prop, "gate_failed", findings, REPAIR_BUDGET, seat




# PSEUDO-CODE — D12 incremental delivery, the 09 arm
# (10_work_wheel.md, ruled 2026-10-07; red test: test_09 l16).
# APPROVED by Sunny 2026-10-07; the code follows:
#
#   1. New param skip_files=frozenset() — file STEMS already
#      described (deliver() computes them; nobody types names).
#   2. The arm is SMALL because L13 already built the carry:
#      update_terms preserves every file OUTSIDE files_in_run.
#      So: (a) drop the skipped files' scopes before the propose
#      loop — zero paid calls, zero concept verdicts for them;
#      (b) keep skipped stems OUT of files_in_run — their existing
#      term rows in ai_delivery.json survive verbatim.
#   3. Conservation stays honest: run_ids is built from the
#      FILTERED scopes, so the every-scope-accounted equation
#      checks the active set exactly.
#   4. NO refusal arm here, deliberately (asymmetric with 07,
#      said out loud): a described file can legitimately carry
#      zero term rows (all-plumbing files never propose), so
#      "skipped but absent from the delivery" is not provably a
#      hole at this layer. Run integrity is the 07 arm's refusal
#      + the deliver() ledger. [flag for Sunny at this review]
#   5. only_file and skip_files compose (only_file first).


def build09(dir05, dir06, dir02, dir07, dir08, out09,
            proposer=None, only_file=None,
            skip_files=frozenset(), defer_files=frozenset()):
    """only_file (her ask, 2026-10-05): limit the run to one
    corpus file for cheap iteration — the outputs then hold
    THAT file's rows only; the full-estate run is the one that
    ships to Fabric.
    skip_files (D12, 2026-10-07): stems already described — their
    scopes never propose; their delivery rows survive because
    files_in_run excludes them (the L13 carry).
    defer_files (D12 batch door): new-but-beyond-max_new — out of
    this run entirely; nothing prior required, nothing written."""
    dir05, dir06, dir07, dir08 = (Path(dir05), Path(dir06),
                                  Path(dir07), Path(dir08))
    _ = dir02  # reserved: the voice overlay at the Fabric move
    proposer = proposer or _openai_proposer
    scopes = sorted(_read(dir05 / "05_semantic_graph_scope_output.json"),
                    key=lambda s: s["node_id"])
    if only_file:
        scopes = [s for s in scopes
                  if _file_of(s["node_id"]) == only_file]
    if skip_files:
        scopes = [s for s in scopes
                  if _file_of(s["node_id"]) not in skip_files]
    if defer_files:
        scopes = [s for s in scopes
                  if _file_of(s["node_id"]) not in defer_files]
    structures = _read(dir05 / "05_semantic_graph_structure_output.json")
    preds = _read(dir05 / "05_semantic_graph_predicate_output.json")
    params = _read(dir05 / "05_semantic_graph_parameter_output.json")
    edges = _read(dir05 / "05_semantic_graph_resolves_edges_output.json")
    sentences = {r["node_id"]: r["sentence"]
                 for r in _read(dir06 / "06_technical_descriptions_output.json")}
    registry = _maybe(dir07 / REGISTRY, None)
    if registry is None:   # the migration read (2026-10-08)
        registry = _maybe(dir07 / REGISTRY_OLD, {})
    blessed = {(t["node_id"], t["report"]): t
               for t in registry.get("terms", [])}
    by_file = {}
    for rep in _maybe(dir08 / "08_pbi_lineage_output.json", []):
        for f in rep.get("executes", []):
            key = f[:-4] if f.endswith(".sql") else f
            by_file.setdefault(key, []).append(rep["name"])

    placed, skipped = [], []
    for sc in scopes:
        sid = sc["node_id"]
        fname = _file_of(sid)
        concept, reason = _concept_verdict(sid, structures, edges)
        if not concept:  # plumbing: a counted skip, never a row
            skipped.append({"node_id": sid, "reason": reason})
            continue
        fparams = [p for p in params
                   if _file_of(p["node_id"]) == fname]
        td = _technical_definition(sid, structures, preds,
                                   sentences, fparams)
        docket = "\n\n".join(
            x for x in (sentences.get(sid, ""), td) if x)
        prop, status, findings, rounds, seat = _propose(
            proposer, sid, docket)
        tied = sorted(by_file.get(fname, []))
        for rep in (tied or [None]):
            row = {
                "node_id": sid,
                "bt_name": prop["bt_name"],
                "bt_name_status": "proposed",
                "name_collision": None,
                "business_description":
                    prop["business_description"],
                "technical_definition": td,
                "status": status,
                "model": seat,  # D4: the actual seat, or None
                #                 for an injected proposer
            }
            if status == "gate_failed":  # audit only on failure
                row["gate_findings"] = findings
                row["rounds_used"] = rounds
            t = blessed.get((sid, rep or fname))
            if t:  # the blessed restore — ruled fields win
                row["bt_name"] = t["bt_name"]
                row["bt_name_status"] = "blessed"
                row["blessing"] = t["ruling"]
            placed.append((rep, fname, row))

    # conservation of the run: every scope is a concept row
    # family or a counted skip — before any byte lands
    run_ids = {sc["node_id"] for sc in scopes}
    seen_ids = ({r[2]["node_id"] for r in placed}
                | {s["node_id"] for s in skipped})
    if run_ids != seen_ids:
        raise ValueError(f"scope conservation red: "
                         f"{sorted(run_ids ^ seen_ids)}")
    files_in_run = ({only_file} if only_file
                    else {_file_of(i) for i in run_ids})
    return ai_delivery.update_terms(out09, placed, skipped,
                                    BASIS_VERSION, files_in_run)


def bless(out09, dir07, node_id, report, ruling):
    """HER HAND ONLY — delegates to the one delivery writer
    (the consolidation ruling; the ratify clause rides there)."""
    return ai_delivery.bless_term(out09, dir07, node_id, report,
                                  ruling)


# The term instruction rides bd.SYSTEM_PROMPT (THE ONE-GATE
# RULING: the 07 voice laws — tone, one-home-per-fact, say the
# choice not the mechanism — are the shared algorithm). Shapes
# only — no concrete example sentences (the examples-are-data
# law).
TERM_INSTRUCTION = (
    "You write a BUSINESS TERM for a data governance glossary: "
    "the specific meaning of a finite data set defined by one "
    "SQL selection, for business readers.\n"
    "THE NAME states what the population IS, in business words — "
    "short, specific, no SQL vocabulary, never an echo of code.\n"
    "THE CARD is exactly four labeled lines, in this order, each "
    "on its own line:\n"
    "Definition: <one glossary sentence — what this population "
    "or selection IS>\n"
    "One row is: <the grain, in business meaning>\n"
    "Keeps: <only the membership conditions this selection "
    "itself applies; stay silent if it applies none>\n"
    "Excludes: <its own exclusions — ALL negative language "
    "lives here and only here>\n"
    "Decode every run-time parameter into plain words (the "
    "chosen dates, the chosen areas); never show @names, "
    "function calls, or numeric codes.")


# ==== TIERED SEATS, THE 09 ARM — PSEUDO CODE (written BEFORE
#      code; 11_tiered_seats.md D2/D3, Q1 RULED "use SMALL";
#      awaiting Sunny's approval) ================================
#
# _propose passes the round into the spec:
#   spec = {"node_id", "docket", "findings", "round": round_no}
# _openai_proposer seats by the ruled ladder:
#   seat = SMALL on rounds 1-2, LARGE on round 3 (the
#   escalation; bd's meter counts fired/landed) — via
#   bd._openai_caller(prompt, seat), so usage and the seat
#   record ride bd's one meter.
# The term row's "model" = the seat of the LAST attempt
# (D4's honesty rule, same as the 07 rows).
# AccountRefusal re-raises BEFORE the catch-all in _propose
# (D6b): a dead wallet stops the batch at the first refusal.
# Injected test proposers see "round" in the spec — the
# seat-by-grain lock proves the ladder without one paid call.
# ================================================================


def _openai_proposer(spec):
    """The paid seat (build-time only; tests always inject).
    TIERED (11 D2/D3): term cards are a SMALL grain — rounds
    1-2 on the small seat, round 3 on the large one."""
    seat = (bd._MODEL_SMALL
            if spec.get("round", 1) < REPAIR_BUDGET
            else bd._MODEL_LARGE)
    prompt = (bd.SYSTEM_PROMPT + "\n\n" + TERM_INSTRUCTION
              + "\n\nTHE BLOCK'S MEANING:\n" + spec["docket"]
              + "\n\nReturn line 1 as 'NAME: <the name>' then "
              "the four card lines, nothing else.")
    if spec.get("findings"):
        prompt += ("\n\nREPAIR — your previous card failed "
                   "these checks; fix every one:\n- "
                   + "\n- ".join(spec["findings"]))
    text = bd._openai_caller(prompt, seat)
    lines = [ln for ln in text.split("\n") if ln.strip()]
    name = ""
    if lines and lines[0].upper().startswith("NAME:"):
        name = lines.pop(0).split(":", 1)[1].strip()
    return {"bt_name": name,
            "business_description": "\n".join(lines),
            "_seat": seat}
