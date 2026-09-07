"""Registry conversion — Design-to-Code Protocol step 2.

Reads the seven DRAFT xlsx registries and emits stamped, code-consumable
JSON into AIVIA_Design/registries/. Two operations, kept separate and
auditable:

1. TRANSCRIBE: every sheet becomes a list of row-records keyed by the
   sheet's header row, verbatim — no hand-typed content anywhere.
2. PATCH: rulings already RECORDED (in the ratified doc or the closed
   open register) that the xlsx DRAFTs predate are applied as explicit,
   cited patch entries below. Landing recorded verdicts only — nothing
   here decides anything new. Anything undecided stays flagged in the
   emitted _open list.

Rerunnable: same xlsx + same patches -> byte-identical JSON.
Usage: python3 AIVIA_Design/registries/convert_from_xlsx.py
"""
import json
import os

import openpyxl

BASE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(BASE)

# registry file -> (source xlsx, doc section it restates)
SOURCES = {
    "kg1_technical": ("L1_KG1_Technical_Layer_Registry_DRAFT.xlsx",
                      "Level 1 / KG Layer 1 — source dictionaries technical layer"),
    "kg2_kind_library": ("L1_KG2_Kind_Library_TSQL_Predicates_DRAFT.xlsx",
                         "Level 1 / KG Layer 2 — kind library (T-SQL predicates)"),
    "kg2_logic": ("L1_KG2_Logic_Layer_Registry_DRAFT.xlsx",
                  "Level 1 / KG Layer 2 — logic layer"),
    "kg3_artifacts": ("L1_KG3_Artifact_Layer_Registry_DRAFT.xlsx",
                      "Level 1 / KG Layer 3 — artifact layer"),
    "kg4_concepts": ("L1_KG4_Concept_Layer_Registry_DRAFT.xlsx",
                     "Level 1 / KG Layer 4 — concept layer"),
    "lenses": ("L2_Lenses_Registry_DRAFT.xlsx", "Level 2 — lenses"),
    "flows": ("L3_Flows_Registry_DRAFT.xlsx", "Level 3 — the flows"),
}

# Ratification pass DONE 2026-09-05 (Sunny): drafts 0.1/0.2 -> 1.0.0,
# ratified flips true, doc headings stamped the same breath.
# v1.1.0 (2026-09-06): the twin-graph ruling (ADR 0077,
# AIVIA_Design/Twin_Graph_KG_RULING.md) lands as TWIN_SHEETS below —
# doc headings bumped the same breath (RG-A2).
# v1.2.0 (2026-09-06): PHASE A METAMODEL BUMP — PROJECTION joins
# Structure_Kinds (the A12 un-deferral built); the bump is what makes
# the estate re-parse a versioned regeneration, not an improvisation.
# v1.3.0 (2026-09-06): PHASE B CORRECTION — the meaning-kind library
# gains the two COMPOSITE kinds (file, statement) the nine-kind draft
# missed: the homomorphism law covers EVERY parsed grain, and file/
# statement nodes need kinds too. Caught at the Phase B build when
# PB-1's "every meaning node carries a library kind" met the file
# root (the F7 DistinctPredicate pattern: build-time catch, cited).
# v1.4.0 (2026-09-06): T-2 RULED (Sunny, Phase B gap-check):
# OPERATIONAL statement kinds carry no analytic meaning BY RULING —
# a closed list (Operational_Statement_Kinds), translated with
# subkind operational and voiced never, NOT counted as gaps. The
# degenerate pattern at statement grain; true debt shrinks to the
# kinds that DO carry meaning (INSERT, WHILE, SET @var, unmapped
# expressions).
# v1.5.0 (2026-09-06): THE GAP TAXONOMY (Sunny's Phase-C review
# ruling: "what gaps are ok to have vs what gaps need resolution —
# name the two kinds differently"): every counted class is
# RULED-SILENT (ok forever, contributes no meaning, by ratified
# ruling) or OPEN (needs resolution) with an OWNER — engine (ours,
# shrinks with builds) or estate (the customer's; the product's
# findings). Gap_Classes is the closed assignment; a new counted
# class must join it at birth.
# v1.6.0 (2026-09-06): the PLUG-ALL-HOLES sweep (Sunny: "we are
# paying the price in the output") — CASE/COALESCE/LEFT/TryConvert
# expressions, subquery INTERIORS (lineage truth), INSERT/WHILE/SET,
# comma joins + APPLY, PIVOT reads, star RULED (meaning without
# enumeration — supersedes the counted interim), correlated +
# membership-disambiguated resolution; PrintStatement joins the
# operational list (diagnostic text, no data meaning; surfaced when
# WHILE bodies opened).
# v1.7.0 (2026-09-06): LEDGER CLOSE (Sunny: "close the debt ledger")
# — DELETE (population removal, voiced as removal), GOTO/LABEL
# (loop control captured; LABEL operational), PIVOT transform mapped
# (aggregate + in-values), star-through resolution (the star ruling
# applied at read time: unqualified and scope-star refs bind to the
# UNDERLYING KG1 column, recomputed each run — drift-safe), derived-
# member binding, folded alias + self-qualifier registration. Twin
# gaps hit ZERO; ambiguous 1,275 -> 37; unbound 541 -> 32.
STAMP_VERSION = "1.7.0"
RATIFIED = True
DOC_STAMP = ("v1.0.0 (ratified 2026-09-05, Sunny); v1.1.0 twin-graph "
             "ruling ADR 0077; v1.2.0 Phase A metamodel bump; v1.3.0 "
             "Phase B composite-kinds correction; v1.4.0 T-2 "
             "operational-statements ruling; v1.5.0 the gap taxonomy; v1.6.0 the plug-all-holes sweep; v1.7.0 ledger close "
             "(all 2026-09-06)")
CONVERTED_ON = "2026-09-05"


def sheet_records(ws):
    rows = []
    for row in ws.iter_rows(values_only=True):
        vals = ["" if v is None else str(v).strip() for v in row]
        while vals and vals[-1] == "":
            vals.pop()
        if vals:
            rows.append(vals)
    if not rows:
        return []
    header = rows[0]
    recs = []
    for vals in rows[1:]:
        rec = {}
        for i, v in enumerate(vals):
            key = header[i] if i < len(header) else f"col_{i}"
            rec[key] = v
        recs.append(rec)
    return recs


# ---- PATCHES: recorded rulings the DRAFT xlsx predate. Each entry is
# (registry, sheet, match: {col: value-prefix}, set: {col: new value}, citation)
PATCHES = [
    ("kg1_technical", "Node_Types",
     {"Node kind": "table", "Property": "grain"},
     {"Required": "opportunistic — never required",
      "Shape / allowed values": "declared by grain phrase on core tables only; "
      "absent + gap-listed elsewhere, never guessed",
      "Notes": "RULING APPLIED at conversion: doc ratified grain opportunistic "
      "(field-calibrated 2026-09-04); register D11 CLOSED 2026-09-05. "
      "Supersedes the xlsx OPEN/tbd row."},
     "doc §KG1 grain (2026-09-04) + register D11"),
    ("kg1_technical", "Edge_Types",
     {"Edge": "contains", "From": "db"},
     {"Direction rationale": "parent->child per the ratified two-part "
      "convention: CONTAINMENT points parent->child; REFERENCE points toward "
      "the more stable node (doc edge-direction convention, ratified "
      "2026-09-05; register D13 CLOSED). Supersedes the xlsx 'unresolved' note."},
     "doc edge-direction convention (2026-09-05) + register D13"),
    ("kg1_technical", "Node_Types",
     {"Node kind": "db", "Property": "description"},
     {"Required": "no — RULING APPLIED at conversion (A1 refined "
      "2026-09-05): the db is minted from the DBA registration "
      "prerequisite, never extract-derived; no extract description "
      "exists at minting. An org-supplied description may supersede "
      "later through the normal lifecycle."},
     "register A1 refined (2026-09-05)"),
    ("kg1_technical", "Node_Types",
     {"Node kind": "schema", "Property": "description"},
     {"Required": "no — CORRECTION APPLIED at conversion (caught by "
      "CHECK-TL-4 over the F1 build, 2026-09-05): the ratified contract "
      "has no schema-description extract part (§3: schema arrives as the "
      "per-table containment field) and the F1 answer key's schema nodes "
      "carry none. The draft row contradicted both ratified artifacts."},
     "CONTRACT_DATALOAD §3 + F1 answer key (CHECK-TL-4 catch)"),
    ("kg1_technical", "Node_Types",
     {"Node kind": "column", "Property": "description"},
     {"Required": "when documented — absence is a COUNTED documentation "
      "gap, never a refusal. CORRECTION APPLIED 2026-09-06 (sepsis "
      "shakedown): org-catalog columns arrive undescribed by "
      "construction — a vendor dictionary never documents the org's own "
      "tables; the ruled fallback posture (readable name + counted "
      "coverage gap) already acknowledged undocumented columns."},
     "sepsis shakedown finding + the ruled fallback posture (2026-09-06)"),
    ("kg2_kind_library", "TSQL_Denominator",
     {"ScriptDom type": "BooleanIsDistinctFromExpression"},
     {"ScriptDom type": "DistinctPredicate",
      "Detail / reason": "SQL 2022 null-safe equality; revisit on first "
      "estate sighting. CORRECTED at conversion 2026-09-05: ScriptDom "
      "actually emits DistinctPredicate — the draft's guessed type name "
      "would have broken the reflected-denominator check; caught by the "
      "F7 remainder case at the slice-2 build."},
     "F7 remainder case catch (2026-09-05)"),
    ("kg2_kind_library", "Predicate_Kinds",
     {"Kind": "QUANTIFIED_COMPARE"},
     {"Roles": "subject, selection",
      "Notes": "RG-1 RULED 2026-09-05 (Sunny): comparison-op and quantifier "
      "are PROPERTIES of the predicate node, never roles — roles are edges "
      "to expression children, and an operator/quantifier is not an "
      "expression. The Roles sheet's quantifier row retires under the same "
      "ruling; roles stay a pure edge vocabulary."},
     "RG-1 ruling (2026-09-05)"),
    ("kg3_artifacts", "Classes",
     {"Class": "usage event"},
     {"Payload": "action: asked|ran|confirmed; asked carries OUTCOME "
      "(matched|ambiguous|no-match); no about edge on no-match; inquiry text "
      "as payload post phi_gate",
      "Notes": "RULING APPLIED at conversion: register H5 CLOSED 2026-09-05 "
      "(asked carries outcome; no about on no-match). relied_on cut stands."},
     "register H5 (2026-09-05)"),
]

# Lens catalog rows the DRAFT predates — reads/yields transcribed from the
# L2 Code Structure Map (authored 2026-09-05, the newer artifact).
ADD_ROWS = [
    ("lenses", "Catalog_v1",
     {"Lens": "referenced-keys",
      "Reads": "inbound joins_to groups per table (L1)",
      "Yields": "declared reference keys per table (distinct column-sets)",
      "Completeness note": "total — RULING APPLIED at conversion: register "
      "D12 CLOSED 2026-09-05 (derived from inbound joins_to, never stored)"},
     "register D12 (2026-09-05)"),
    ("lenses", "Catalog_v1",
     {"Lens": "correspondence",
      "Reads": "minted concepts (basis), current relatedness families",
      "Yields": "corresponds|dispersed|merged|new per family",
      "Completeness note": "total over minted — RULING APPLIED at conversion: "
      "register H7 CLOSED 2026-09-05 (S4 overlap-maximal rule; ties -> "
      "ambiguous, human rules). DEFERRED from v1 (compares prior state)"},
     "register H7 (2026-09-05)"),
    ("lenses", "Catalog_v1",
     {"Lens": "current",
      "Reads": "version chains, dispositions (accepted_version pins)",
      "Yields": "the current version per artifact (the A6 selection)",
      "Completeness note": "total over artifacts; non-empty by "
      "construction — RULING APPLIED at conversion: A6 model-first "
      "ruling (2026-09-05) 'current is derived' lands as a catalog row; "
      "the draft catalog predated it (caught at the slice-4 build)"},
     "register A6 (2026-09-05)"),
    ("lenses", "Catalog_v1",
     {"Lens": "demand",
      "Reads": "no-match asked events (redacted payloads)",
      "Yields": "unanswered-question themes + counts",
      "Completeness note": "total over ledger — RULING APPLIED at conversion: "
      "register H5 CLOSED 2026-09-05. DEFERRED from v1 (reads the ask surface)"},
     "register H5 (2026-09-05)"),
]

def _fr(stage, check, rule, asserts, v1="yes"):
    return {"Stage": stage, "Named check(s)": check, "Doc rule": rule,
            "Check asserts": asserts, "v1": v1}


_DEF_IN = "deferred (inward flow entire — no ask surface in v1)"
# Row-per-rule expansion RULED 2026-09-05; transcribed from doc Level 3
# (each stage ratified 2026-09-04). The doc remains authority.
_FLOW_RULES = [
    _fr("OUT-1 produce", "PROD-1",
        "every run lands the GENERATION-RUN EVENT: author = agent identity; "
        "basis = model/prompt/lens/metamodel versions + worklist; "
        "accounting shipped u absent = attempted, one conservation line per "
        "class attempted (A9), killed-lines counted per shipped artifact",
        "conservation event per run; the run event is the ONLY production "
        "ledger"),
    _fr("OUT-1 produce", "PROD-2",
        "the STALENESS LENS is the worklist (basis moved, no artifact yet, "
        "or explicit human request); nobody hand-picks; full regeneration = "
        "a version bump making everything stale — the same rule",
        "worklist == staleness-lens output"),
    _fr("OUT-1 produce", "PROD-3",
        "deterministic composition + bounded model smoothing (linguistic "
        "seat only) + the class gate; the model never adds a fact",
        "gate outcomes in closed vocabularies"),
    _fr("OUT-1 produce", "PROD-4",
        "writes layer-3 machine versions ONLY; against human-owned "
        "artifacts it may APPEND a superseding version — rendered proposed "
        "by the ownership lens, never current",
        "human-owned never overwritten"),
    _fr("OUT-1 produce", "PROD-5",
        "replay floor: same graph + same versions -> identical skeletons "
        "and gate verdicts; prose may vary, truth may not; model failure "
        "degrades to the deterministic floor",
        "replay determinism of the floor"),
    _fr("OUT-2 approve", "APPR-1",
        "the approval surface WRITES DISPOSITIONS ONLY — it renders lenses, "
        "never touches artifacts, trees, or the technical layer",
        "writer census"),
    _fr("OUT-3 land", "LAND-1",
        "a send is an outward, irreversible act — it requires an accepting "
        "disposition on the artifact AND a named human confirmation of the "
        "send itself; no autonomy mode exempts it (B4)",
        "no send without accepting disposition + human confirmation"),
    _fr("OUT-3 land", "LAND-2",
        "anti-repeat: no send for logic whose current outcome is denied "
        "unless a new version exists (standing rule R2, read from the "
        "current-outcome lens)",
        "anti-repeat enforced via current-outcome lens"),
    _fr("OUT-3 land", "LAND-3",
        "every send lands a proposal SENT event before transport; every "
        "later look lands an OBSERVED event; current outcome is the lens",
        "sent event precedes transport"),
    _fr("OUT-3 land", "LAND-4",
        "target-native forms only; ZERO custom attributes — native column "
        "sets held as data; attribution is the prefix in text, never a "
        "schema footprint",
        "zero custom attributes in payloads"),
    _fr("OUT-3 land", "LAND-5",
        "look-before-write: at send time read the ONE object about to be "
        "touched, never the catalog at large (R3); what was seen lands as "
        "an observed event",
        "observations append-only"),
    _fr("IN-1 match", "MATCH-1",
        "writes ONE thing — usage event asked, at inquiry arrival (every "
        "inquiry is a fact, especially unanswerable ones); nothing else, "
        "ever", "writer census (asked only)", _DEF_IN),
    _fr("IN-1 match", "MATCH-2",
        "outcomes, closed set: matched | ambiguous | no-match; no-match is "
        "typed and counted — the honest empty, never a shrug",
        "closed outcome set", _DEF_IN),
    _fr("IN-1 match", "MATCH-3",
        "completeness declared on every result: top-K is never 'all that "
        "exists'; enumeration questions use primitives that declare "
        "totality (B3)", "completeness on every result", _DEF_IN),
    _fr("IN-1 match", "MATCH-4",
        "match proposes, evidence disposes: output is candidate GRAPH "
        "OBJECTS (ids) + the evidence trail — never generated text posing "
        "as fact", "candidates are ids + evidence, never text", _DEF_IN),
    _fr("IN-1 match", "MATCH-5",
        "ambiguous goes to the HUMAN with candidates (intent judgment is "
        "human's); no silent pick among near-ties",
        "ambiguity reaches the human", _DEF_IN),
    _fr("IN-2 ground", "GRND-1",
        "writes usage events only — confirmed when the human accepts, ran "
        "when they execute; run result rows are DISPLAY-ONLY and never "
        "enter the graph or the mind's evidence",
        "writer census (confirmed | ran only)", _DEF_IN),
    _fr("IN-2 ground", "GRND-2",
        "the answer is ARRANGED EVIDENCE; the answer text is a CAPTION "
        "adding no claim the evidence doesn't carry",
        "caption gate — no ungrounded claim in answer text", _DEF_IN),
    _fr("IN-2 ground", "GRND-3",
        "quantified claims inherit the match's declared completeness — "
        "'all' and counts only over results declared total (B3)",
        "quantifiers only over declared-complete results", _DEF_IN),
    _fr("IN-2 ground", "GRND-4",
        "headlines and counts are rendered by code from result metadata, "
        "never model-written",
        "headlines/counts rendered by code", _DEF_IN),
    _fr("IN-3 generate", "GEN-1",
        "generated SQL composes only from declared reality — existing "
        "tables/columns, joins along declared joins_to paths (the builder "
        "WALKS the join graph), documented value sets; a deterministic "
        "validator checks every reference and join against layer 1 before "
        "the draft reaches the human",
        "validator totality; refusals name the missing declared path",
        _DEF_IN),
    _fr("IN-3 generate", "GEN-2",
        "the parser door: a draft becomes estate ONLY by the human "
        "adopting it into their source and the inbound flow parsing it "
        "like any customer file — zero trust shortcuts",
        "no side channel — the inbound door is the only door", _DEF_IN),
    _fr("IN-3 generate", "GEN-3",
        "the draft is DISPLAY-ONLY: delivered through the answer surface, "
        "writes nothing; a discarded draft leaves no residue",
        "drafts write nothing", _DEF_IN),
    _fr("IN-3 generate", "GEN-4",
        "trigger: a no-match outcome AND an explicit human request — "
        "generation is an act someone asks for, never an automatic "
        "consolation",
        "generation only on no-match + human request", _DEF_IN),
]


# Rows retired by ruling: (registry, sheet, match, citation)
REMOVE_ROWS = [
    ("kg2_kind_library", "Roles", {"Role": "quantifier"},
     "RG-1 ruling (2026-09-05): quantifier is a predicate property"),
]

# Whole sheets added by ruling — transcribed from the doc, cited per sheet.
ADD_SHEETS = {
    "kg2_logic": {
        "Scope_Identity": [
            {"Item": "_ruling",
             "Definition": "All eight flags RULED 2026-09-05 (Sunny): this "
             "sheet restates the doc's Disambiguation models A3/A4 and "
             "register row A11 as registry rows. Doc is authority; "
             "transcribed verbatim-in-substance."},
            {"Item": "name_key (A3)",
             "Definition": "key(scope_i) := file :: name if i = 1st "
             "occurrence of name in file order; file :: name#i otherwise. "
             "Total over all scopes with names.",
             "Branch / witness": "Branch (explicit, counted): removing "
             "occurrence 1 retires ALL keys of that name; survivors "
             "re-mint; displaced attachments surface for re-attach. "
             "Witness: two WITH Base -> Base, Base#2; edit elsewhere "
             "changes neither."},
            {"Item": "delivery scopes (A11)",
             "Definition": "the file's final emitter scope mints "
             "file :: delivery (single emitter); plural emitters mint "
             "file :: delivery_1..n in statement order AND surface on the "
             "DBA list.",
             "Branch / witness": "register A11 (RULED 2026-09-05); "
             "witnessed by fixtures F2 expected_trees + F3 "
             "decisions_membership keys."},
            {"Item": "attachment domain (A4)",
             "Definition": "about-targets := named nodes only (file, named "
             "scope, KG1 nodes, layer-3 citizens, concepts). Unnamed nodes "
             "are outside the domain — a domain bound, not a branch.",
             "Branch / witness": "Witness: subquery logic is described at "
             "its named ancestor."},
        ],
    },
    "flows": {
        "Rules_to_Checks": _FLOW_RULES,  # defined below, row per check
    },
}

# The v1 flag column — MVP scope as data (ruled 2026-09-05: the registry's
# v1 flag is the authority; prose lens-counts retired from service).
V1_LENSES = {"ownership", "authorship", "version", "standing",
             "current", "current-outcome", "staleness", "decisions(class)",
             "degenerate", "join-compliance", "relatedness",
             "working-set", "gap-census", "referenced-keys"}
DEFER_WHY = {
    "divergence": "compares prior state; v1 is first contact",
    "concept-drift": "compares prior state; v1 is first contact",
    "correspondence": "compares prior state; v1 is first contact",
    "expertise": "reads the deferred ask surface",
    "blast-radius": "reads the deferred ask surface",
    "demand": "reads the deferred ask surface",
}

# Whole sheets added by the TWIN-GRAPH RULING (ratified 2026-09-06,
# Sunny; ADR 0077; full ruling AIVIA_Design/Twin_Graph_KG_RULING.md).
# Landing recorded verdicts only, per this file's charter.
_TG = "twin-graph ruling (2026-09-06)"
TWIN_SHEETS = {
    "kg2_kind_library": {
        "Structure_Kinds_Phase_A": [
            {"Kind": "PROJECTION",
             "Meaning": "the SELECT list — what the scope outputs; one "
             "member per output column (name + expression subtree, "
             "position-ordered)",
             "T-SQL sources": "SelectScalarExpression per member; "
             "SelectStarExpression -> COUNTED remainder "
             "(star_projection) until star expansion is ruled; any "
             "other select element -> counted remainder (closes the "
             "silent-skip hole the Phase A build found)",
             "Notes": "Phase A build 2026-09-06 (ADR 0077): the A12 "
             "deferral lifted by its own planned recovery path — "
             "metamodel bump + re-parse. Lives beside Structure_Kinds "
             "(sheet-add keeps the xlsx untouched; merge at next "
             "draft-workbook revision)."},
        ],
        "Meaning_Node_Kinds": [
            {"Kind": "_ruling", "Definition": _TG + " 2d: the closed "
             "meaning-node library — one kind per translated node in KG2b, "
             "the meaning twin. Doc is authority."},
            {"Kind": "selection", "Definition": "a scope's meaning; carries "
             "grain where derivable", "Deciding example": "#Base_Pop -> 'a "
             "selection of patient encounters'"},
            {"Kind": "source", "Definition": "a FROM/JOIN ref w/ join kind; "
             "resolves to a KG1 table or a same-tree selection node (the "
             "handle)", "Deciding example": "INNER JOIN #Base_Pop -> "
             "'restricted to records also present in the base-population "
             "selection'"},
            {"Kind": "condition", "Definition": "a predicate's meaning; "
             "kinds = the ratified R4 closed set; DEGENERATE is a subkind — "
             "translated always, voiced never",
             "Deciding example": "DX_CODE LIKE 'E11%' -> 'the diagnosis "
             "code starts with E11'; WHERE 1=1 -> degenerate"},
            {"Kind": "projection", "Definition": "what an output column IS "
             "(rides the A12 un-deferral)",
             "Deciding example": "FIRST_TIME_LINE = ROW_NUMBER() OVER (...) "
             "-> 'the first scored row per encounter'"},
            {"Kind": "grouping", "Definition": "GROUP BY/HAVING context; "
             "shapes grain",
             "Deciding example": "GROUP BY ENCOUNTER_ID -> 'one row per "
             "encounter'"},
            {"Kind": "window", "Definition": "ORDER BY/TOP/window functions; "
             "shapes which rows",
             "Deciding example": "TOP 1 ORDER BY SCORE DESC -> 'the "
             "highest-scoring row'"},
            {"Kind": "combination", "Definition": "UNION w/ dedup flag",
             "Deciding example": "UNION ALL -> 'combined, duplicates kept'"},
            {"Kind": "reference", "Definition": "an operand's meaning (the "
             "R5 material as nodes)",
             "Deciding example": "E.APPT_STATUS_C -> 'the appointment "
             "status'"},
            {"Kind": "gap", "Definition": "a counted untranslated node; "
             "reason-coded per the 0044 pattern",
             "Deciding example": "dynamic SQL body -> gap(dynamic_sql)"},
            {"Kind": "file", "Definition": "COMPOSITE (Phase B "
             "correction, 2026-09-06): the file's meaning, composed "
             "from its statements' meanings — the homomorphism law "
             "reaches the root; never a separate invention",
             "Deciding example": "USP_ED_SEPSIS -> composed from its "
             "staging chain"},
            {"Kind": "statement", "Definition": "COMPOSITE (Phase B "
             "correction, 2026-09-06): one executable command's "
             "meaning, composed from its scopes/predicates; a "
             "statement the mapper counted unmapped twins as a gap",
             "Deciding example": "SELECT INTO -> composed from its "
             "selection; UPDATE (unmapped) -> gap(unmapped_statement)"},
        ],
        "Operational_Statement_Kinds": [
            {"ScriptDom type": "_ruling", "Rationale": "T-2 RULED "
             "(Sunny, 2026-09-06, Phase B gap-check): these statement "
             "kinds carry NO analytic meaning — they tune the engine, "
             "manage staging lifecycle, or declare plumbing; none "
             "shapes what the data MEANS. Translated with subkind "
             "'operational', voiced never — presence is the "
             "homomorphism law, silence is policy (the degenerate "
             "pattern at statement grain). The list is CLOSED: adding "
             "a kind is a ruling, never a code default."},
            {"ScriptDom type": "CreateIndexStatement",
             "Rationale": "performance tuning; no data meaning"},
            {"ScriptDom type": "DropIndexStatement",
             "Rationale": "performance tuning; no data meaning"},
            {"ScriptDom type": "DropTableStatement",
             "Rationale": "staging lifecycle cleanup"},
            {"ScriptDom type": "TruncateTableStatement",
             "Rationale": "staging lifecycle cleanup"},
            {"ScriptDom type": "PredicateSetStatement",
             "Rationale": "session options (SET NOCOUNT ...)"},
            {"ScriptDom type": "SetTransactionIsolationLevelStatement",
             "Rationale": "session options"},
            {"ScriptDom type": "DeclareVariableStatement",
             "Rationale": "plumbing declaration; a variable's MEANING "
             "arrives where it is assigned/used (SET @var MAPPED "
             "2026-09-06 — assignments carry logic)"},
            {"ScriptDom type": "PrintStatement",
             "Rationale": "diagnostic text to the console; no data "
             "meaning (surfaced when WHILE bodies opened, 2026-09-06)"},
            {"ScriptDom type": "LabelStatement",
             "Rationale": "a jump marker; the MEANING lives on the "
             "GOTO that targets it (ledger close, 2026-09-06)"},
        ],
        "Gap_Classes": [
            {"Counted class": "_ruling", "Kind": "-", "Owner": "-",
             "Meaning": "Sunny's Phase-C taxonomy ruling (2026-09-06): "
             "RULED-SILENT = ok to have forever, contributes no "
             "meaning, by ratified ruling; OPEN = needs resolution, "
             "owner engine (ours) or estate (the customer's finding). "
             "Closed: a new counted class joins this sheet at birth."},
            {"Counted class": "operational statements",
             "Kind": "RULED-SILENT", "Owner": "-",
             "Meaning": "engine tuning / staging lifecycle / plumbing "
             "(the v1.4.0 closed list); translated, voiced never"},
            {"Counted class": "degenerate predicates",
             "Kind": "RULED-SILENT", "Owner": "-",
             "Meaning": "both-sides-literal (1=1); decides nothing"},
            {"Counted class": "outer-join match conditions",
             "Kind": "RULED-SILENT", "Owner": "-",
             "Meaning": "rows survive without a match — voicing as a "
             "filter would lie (v1.3.0); counted in the ledger"},
            {"Counted class": "unmapped statement kinds",
             "Kind": "OPEN", "Owner": "engine",
             "Meaning": "carry real meaning; map evidence-ordered. "
             "INSERT/WHILE/SET (plug-all-holes) then DELETE/GOTO "
             "(ledger close) ALL MAPPED 2026-09-06; the class is "
             "EMPTY — it remains for future estates' kinds"},
            {"Counted class": "unmapped query shapes and table "
             "references",
             "Kind": "OPEN", "Owner": "engine",
             "Meaning": "UNION (ABX corpse) then PIVOT (ledger close) "
             "ALL MAPPED 2026-09-06; the class is EMPTY — it remains "
             "for future estates' shapes"},
            {"Counted class": "star projection",
             "Kind": "RESOLVED", "Owner": "-",
             "Meaning": "RULED 2026-09-06: a star translates as "
             "'every column of the source at read time' — meaning "
             "without enumeration, drift-safe by construction; it "
             "left the gap ledger entirely"},
            {"Counted class": "ambiguous unqualified refs",
             "Kind": "OPEN", "Owner": "engine",
             "Meaning": "ledger close 2026-09-06: star-through + "
             "derived-member + folded-alias binding shrank the class "
             "1,275 -> 37 (sepsis); the residue is genuinely "
             "undecidable without running the SQL — counted forever"},
            {"Counted class": "refs into unmapped-statement scopes",
             "Kind": "OPEN", "Owner": "engine",
             "Meaning": "downstream of the unmapped kinds; close "
             "those and these close free"},
            {"Counted class": "documentation gaps (no dictionary "
             "words)", "Kind": "OPEN", "Owner": "estate",
             "Meaning": "the customer's doc debt; runbook 4c + the "
             "steward description workflow work it down"},
            {"Counted class": "drift refs (columns nowhere declared)",
             "Kind": "OPEN", "Owner": "estate",
             "Meaning": "silently-failing reports — THE product "
             "finding; resolution is a human act (fix the report or "
             "the dictionary), kept counted forever"},
        ],
    },
    "kg2_logic": {
        "Meaning_Twin": [
            {"Item": "_ruling", "Definition": _TG + " 2c/2e: KG2b, the "
             "meaning graph — the parsed graph's homomorphic twin, built "
             "only by the TRANSLATOR. Doc is authority."},
            {"Item": "kind", "Definition": "from the closed "
             "Meaning_Node_Kinds library (kg2_kind_library)"},
            {"Item": "content", "Definition": "the translated meaning "
             "material (steward-voiced words, resolved value meanings, "
             "composed phrases)"},
            {"Item": "points_at", "Definition": "edge to exactly ONE KG2a "
             "node — the homomorphism; gap nodes point at the counted "
             "site, reason-coded"},
            {"Item": "draws_from", "Definition": "edges to every KG1 node "
             "consulted — derived meaning cites its sources; the "
             "object-grain staleness basis"},
            {"Item": "content_key", "Definition": "meaning identity: hash "
             "over (kind, operand identities resolved to KG1 ids or scope "
             "paths, literal values, children's content_keys, join kind)"},
            {"Item": "basis", "Definition": "translator + metamodel "
             "version stamps"},
            {"Item": "law: homomorphism", "Definition": "translated + gap "
             "== every KG2a node, no third bucket — queryable"},
            {"Item": "law: composition", "Definition": "composite nodes "
             "(scope, statement, file) translate by composing children's "
             "meanings — never a separate invention"},
            {"Item": "law: content_key invariance", "Definition":
             "INVARIANT to formatting/whitespace, alias names, AND/join "
             "order, comments; SENSITIVE to any column, operator, literal "
             "value, join kind, or structural change"},
            {"Item": "law: regeneration", "Definition": "regenerates with "
             "KG2a at the FILE quantum; a version bump regenerates the "
             "whole layer"},
            {"Item": "law: projection un-deferral", "Definition": "the A12 "
             "deferral LIFTED — SELECT list enters KG2a as a structure "
             "kind, one projection-member node per output column"},
        ],
    },
    "kg1_technical": {
        "Incremental_Intake": [
            {"Item": "_ruling", "Definition": _TG + " 2a/5a + "
             "CONTRACT_DATALOAD §13. Doc is authority."},
            {"Item": "content_hash", "Definition": "on every KG1 object "
             "(db/schema/table/column): hash over the object's declared "
             "syntax + semantics as loaded"},
            {"Item": "loaded_at", "Definition": "load stamp + "
             "source-snapshot identity on every object"},
            {"Item": "rule: incremental mode", "Definition": "intake diffs "
             "by hash; only changed objects write; unchanged hash writes "
             "nothing (INTAKE-13)"},
            {"Item": "rule: equivalence audit", "Definition": "scheduled "
             "full parallel load compares against incremental state; any "
             "delta is a COUNTED finding (INTAKE-12), never silently "
             "reconciled"},
            {"Item": "rule: staleness export", "Definition": "the "
             "changed-object set feeds object-grain staleness — only "
             "KG2b meaning nodes whose draws_from cite a changed object "
             "retranslate"},
        ],
    },
    "lenses": {
        "Builders_and_Readings": [
            {"Item": "_ruling", "Definition": _TG + " 3: the lens STRATUM "
             "retires into two contracts; this sheet + Reclassification "
             "are the authority over the Catalog_v1 rows where they "
             "differ. Doc is authority."},
            {"Item": "BUILDER contract", "Definition": "loader -> KG1 · "
             "parser -> KG2a · TRANSLATOR -> KG2b (the 'translation lens' "
             "renamed to what it is). Deterministic; versioned, stamps "
             "every node written; writes ONLY its own layer; total with "
             "counted gaps; version bump rebuilds everything it governs. "
             "Governance has NO builder."},
            {"Item": "READING contract", "Definition": "named, versioned, "
             "deterministic, writes nothing; kept for citability "
             "(dispositions and concept bases quote reading output by "
             "version); most are versioned queries"},
            {"Item": "survival principle", "Definition": "a reading exists "
             "iff its yield is ABOUT the graph for one consumer — status, "
             "aggregation, comparison — never meaning itself; the "
             "translator absorbed everything secretly computing meaning"},
        ],
        "Reclassification_2026_09_06": [
            {"Entry": "decisions(class)", "Class": "RETIRED — subsumed by "
             "the translator (membership/grain/value/path become "
             "meaning-node kinds)"},
            {"Entry": "degenerate", "Class": "RELOCATED — the condition "
             "subkind in the meaning twin"},
            {"Entry": "relatedness", "Class": "COMPUTED READING (over KG2b "
             "content_keys; feeds concept minting; full contract entry)"},
            {"Entry": "ownership", "Class": "query (event-derivation; "
             "rules unchanged)"},
            {"Entry": "authorship", "Class": "query (event-derivation; "
             "rules unchanged)"},
            {"Entry": "version", "Class": "query (chain depth)"},
            {"Entry": "standing", "Class": "query (event-derivation)"},
            {"Entry": "current", "Class": "query (derived current "
             "pointers)"},
            {"Entry": "current-outcome", "Class": "query (latest "
             "observation)"},
            {"Entry": "staleness", "Class": "query (stamp arithmetic; "
             "gains KG1 object grain)"},
            {"Entry": "join-compliance", "Class": "query (comparison: KG2b "
             "source nodes vs KG1 declared paths)"},
            {"Entry": "divergence", "Class": "query (anchor mismatch)"},
            {"Entry": "concept-drift", "Class": "query (anchor mismatch vs "
             "concept basis)"},
            {"Entry": "expertise", "Class": "query (usage aggregation)"},
            {"Entry": "blast-radius", "Class": "query (traversal + usage)"},
            {"Entry": "working-set", "Class": "query (resolves_to "
             "aggregation)"},
            {"Entry": "gap-census", "Class": "query (gap-node counting; "
             "gains untranslated counts)"},
            {"Entry": "referenced-keys", "Class": "query (inbound joins_to "
             "groups)"},
            {"Entry": "correspondence", "Class": "deferred (unchanged "
             "posture); query-shaped when it lands"},
            {"Entry": "demand", "Class": "deferred (unchanged posture); "
             "query-shaped when it lands"},
        ],
    },
    "kg3_artifacts": {
        "Governance_Overlay": [
            {"Item": "_ruling", "Definition": _TG + " 2f: kg3_artifacts + "
             "kg4_concepts merge into KG3, the governance overlay — one "
             "Governance_Layer_Registry. Doc is authority."},
            {"Item": "concept joins the classes", "Definition": "keeping "
             "its four ratified rules (human-mint-only, append-only, "
             "nameless — the term carries the name, basis snapshot); a "
             "concept's about-edges target a SET of meaning anchors (the "
             "family, by content_key)"},
            {"Item": "THE ANCHOR RULE", "Definition": "about targets a "
             "MEANING IDENTITY — a KG2b content_key at a scope path, or a "
             "KG1 object — never a KG2a syntax node, never a node "
             "instance"},
            {"Item": "corollary S1", "Definition": "same content_key after "
             "regeneration -> the artifact survives silently (was a "
             "rule)"},
            {"Item": "corollary S2", "Definition": "changed content_key -> "
             "flagged orphan (the drift finding); deleted scope -> "
             "orphaned with similarity candidates (was a rule)"},
            {"Item": "corollary: free churn", "Definition": "syntax-only "
             "churn (reformat, alias rename) costs zero governance"},
        ],
    },
    "kg4_concepts": {
        "Merged_Into_Governance": [
            {"Item": "_ruling", "Definition": _TG + " 2f: SUPERSEDED AS A "
             "LAYER — concept is a citizen class of the governance overlay "
             "(kg3_artifacts Governance_Overlay sheet). Sheets below stand "
             "as the ratified class-rule record."},
        ],
    },
    "flows": {
        "Change_Quanta": [
            {"Layer": "_ruling", "Data-change quantum": _TG + " 5a",
             "Note": "changes trigger updates; total reload retires as the "
             "DATA path but stays as the RULE path. Doc is authority."},
            {"Layer": "KG1", "Data-change quantum": "object (content_hash "
             "diff)", "Note": "only changed objects write; mechanical "
             "equivalence audit (INTAKE-12)"},
            {"Layer": "KG2 (both twins)", "Data-change quantum": "file "
             "(content hash) + the draws_from ripple from KG1 changes",
             "Note": "parse + translate same run, atomic; stamp check "
             "forbids readable half-state"},
            {"Layer": "KG3", "Data-change quantum": "never regenerates",
             "Note": "anchors re-check by content_key after any KG2b "
             "change: survive silently or flag as drift"},
            {"Layer": "ALL", "Data-change quantum": "RULE changes are "
             "TOTAL by design", "Note": "a version bump regenerates "
             "everything it governs — partial regeneration under a new "
             "rule is the grandfathering hazard in pipeline form"},
        ],
        "Twin_Graph_Phasing": [
            {"Phase": "A", "Ships": "metamodel bump + A12 projection "
             "re-parse (KG2a complete)",
             "Gate": "real ED-sepsis gap-check output"},
            {"Phase": "B", "Ships": "the translator + stored KG2b + "
             "conservation equation green over the sepsis corpus",
             "Gate": "real ED-sepsis gap-check output"},
            {"Phase": "C", "Ships": "voicing-policy port (Floor Grammar "
             "major) + full gap-check rerun; findings 1-4 corpses become "
             "standing tests", "Gate": "Sunny's gap-check verdict"},
            {"Phase": "D", "Ships": "governance registry merge + anchor "
             "migration (orphans are FINDINGS, not errors)",
             "Gate": "real ED-sepsis gap-check output"},
            {"Phase": "independent", "Ships": "KG1 incremental intake — "
             "any time after A", "Gate": "mechanical equivalence audit "
             "green (INTAKE-12)"},
        ],
    },
}

# Undecided items carried forward as flags, never resolved here.
OPEN_FLAGS = {}


def convert():
    log = []
    for name, (xlsx, doc_section) in SOURCES.items():
        wb = openpyxl.load_workbook(os.path.join(DESIGN, xlsx))
        sheets = {ws.title: sheet_records(ws) for ws in wb}
        applied = []
        for (reg, sheet, match, sets, cite) in PATCHES:
            if reg != name:
                continue
            hits = [r for r in sheets[sheet]
                    if all(r.get(c, "").startswith(v) for c, v in match.items())]
            assert len(hits) == 1, f"{reg}/{sheet}: patch matched {len(hits)} rows"
            hits[0].update(sets)
            applied.append(cite)
        for (reg, sheet, row, cite) in ADD_ROWS:
            if reg != name:
                continue
            assert not any(r.get("Lens") == row.get("Lens")
                           for r in sheets[sheet]), f"{reg}: duplicate add"
            sheets[sheet].append(dict(row))
            applied.append(cite)
        for (reg, sheet, match, cite) in REMOVE_ROWS:
            if reg != name:
                continue
            hits = [r for r in sheets[sheet]
                    if all(r.get(c, "").startswith(v) for c, v in match.items())]
            assert len(hits) == 1, f"{reg}/{sheet}: remove matched {len(hits)}"
            sheets[sheet].remove(hits[0])
            applied.append(cite)
        for sheet, rows in ADD_SHEETS.get(name, {}).items():
            assert sheet not in sheets, f"{name}: sheet {sheet} exists"
            sheets[sheet] = [dict(r) for r in rows]
            applied.append(f"sheet {sheet} added (all-eight ruling 2026-09-05)")
        for sheet, rows in TWIN_SHEETS.get(name, {}).items():
            assert sheet not in sheets, f"{name}: sheet {sheet} exists"
            sheets[sheet] = [dict(r) for r in rows]
            applied.append(f"sheet {sheet} added ({_TG}, ADR 0077)")
        if name == "lenses":
            for row in sheets["Catalog_v1"]:
                lens = row["Lens"]
                assert lens in V1_LENSES or lens in DEFER_WHY, \
                    f"lens {lens} unassigned to v1/deferred"
                row["v1"] = ("yes" if lens in V1_LENSES
                             else f"deferred ({DEFER_WHY[lens]})")
            applied.append("v1 flag column (ruled 2026-09-05: registry v1 "
                           "flag is the authority; prose lens-counts retired)")
        out = {
            "registry": name,
            "stamp": {
                "version": STAMP_VERSION,
                "doc_section": doc_section,
                "doc_stamp": DOC_STAMP,
                "ratified": RATIFIED,
                "converted_on": CONVERTED_ON,
                "converted_from": xlsx,
            },
            "rulings_applied_at_conversion": applied,
            "_open": OPEN_FLAGS.get(name, []),
            "sheets": sheets,
        }
        path = os.path.join(BASE, name + ".json")
        with open(path, "w") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        log.append(f"{name}: {sum(len(v) for v in sheets.values())} rows, "
                   f"{len(applied)} ruling(s) applied, "
                   f"{len(OPEN_FLAGS.get(name, []))} open flag(s)")
    print("\n".join(log))


if __name__ == "__main__":
    convert()
