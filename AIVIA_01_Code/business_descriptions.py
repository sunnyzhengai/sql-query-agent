"""Phase 07 — business descriptions, THE ELOQUENT MACHINE.

Contract: AIVIA_01_Design/07_business_descriptions_data_contract.md
(APPROVED 2026-10-03). The second of the two machines: an LLM
PROPOSES, a NO-MODEL MECHANICAL GATE verifies every claim against
stored rows, Sunny BLESSES. The floor (the 06 technical sentence)
ships whenever nothing blessed or gate-passed exists — stiff is
allowed, lying is not.

Dry-run evidence: AIVIA_01_Design/dryruns/phase_II_uses_phase_I.md
(14 real calls, 5 rounds, converged round 5). The style grammar
S1-S11 and the gate checks G-1..G-7 are ruled design law.
"""

# ==== L03/L04 PSEUDO CODE — awaiting Sunny's approval ===============
# (standing process: real code lands below only after her stamp;
# the tests are red now. L02's registry seed is staged separately
# for her ratifying hand.)
#
# BASIS_VERSION = "07.2.0"  # Gate v2 + the five-line card (2026-10-03) — the 07 grammar constant: the S-rule
#   wording, the plain-word lexicon, the budgets. Any change bumps
#   and re-pins.
#
# THE DOCKET (per node — everything the proposer may know, and
# the ONLY thing the whitelist trusts):
#   file grain:  the 06 file sentence + its scope sentences + the
#     file's ledger slice (the boundary of the known) + the
#     parameter lines.
#   scope grain: the 06 scope sentence + its condition rows.
#   field grain: the owning scope sentence + the field's defining
#     phrase via the IMPORTABLE 06 renderers (G2a — 06 stays
#     closed).
#
# THE GATE (G-1..G-7, contract law, zero model):
#   G-1 LEXICAL WHITELIST: lowercase word tokens of audience_text;
#     every CONTENT token must appear in docket text, 02 words,
#     the blessing registry, or THE PLAIN-WORD LEXICON — a CLOSED,
#     versioned list in this file (function words + ruled business
#     words like report/data/shows); growth is a ruled row, never
#     silent. Numbers and quoted literals must appear in the
#     docket verbatim. Fail NAMES the token (the semicolon
#     killer).
#   G-2 BANNED (S2): join select query table temp column
#     procedure parameter, @tokens, raw codes (digit tokens not
#     in the docket).
#   G-3 BUDGETS (S8): per-grain sentence counts and <=15 words
#     per sentence; max one parenthetical; no nesting.
#   G-4 TEMPLATE (S7): file grain = exactly the four labeled
#     lines (Who's in it / Each row shows / Time window /
#     Excludes), nothing else.
#   G-5 ANCHORS (S4): restriction verbs (only/excludes/limited/
#     restricted) must anchor to Population or WHERE docket
#     lines; attachment claims to attachment lines.
#   G-6 MUST-SAY (three members): the gap echo (files whose
#     ledger slice carries dynamic_sql_gap), the window (files
#     whose docket carries population-shaping parameters), the
#     Excludes line (files whose docket carries exclusions).
#   G-7 S10 UNBOUND CODES: no bare code in prose; every sighting
#     RECORDED to 07_business_descriptions_code_sightings_output.json (table.column + code +
#     node) — the dictionary-growth flywheel's second engine.
#   gate(audience_text, docket, grain) -> findings list; empty ==
#   pass. Deterministic, byte-testable, fixtures = the dry run's
#   RECORDED REAL outputs.
#
# THE PROMPT CONSTRUCTOR (deterministic, byte-pinned): the ruled
#   SYSTEM text (truth rules + S-rules verbatim from the design)
#   + the per-grain instruction (S7 template for file; budgets
#   for scope/field) + the docket. Repair rounds append the
#   NAMED findings. No concrete example sentences ever ride in a
#   prompt (the prompt-examples-are-data law).
#
# THE PROPOSER LOOP (the only paid path; build-time only):
#   round 1 propose -> gate; findings -> repair round (budget 3,
#   ruled); still failing -> status floor, LAST findings kept on
#   the row. Local seat gpt-5-mini; production gpt-5.4-mini
#   (parity law at the move).
#
# THE EFFECTIVE LADDER (ported law): blessed (registry, Sunny's
#   hand) > gate_passed > floor (the 06 sentence verbatim).
#
# build07(dir05, dir06, out07, dir02, no_llm=False):
#   dockets for every file + scope + field node -> one sheet row
#   each (CONSERVATION: exactly one row per docket node, a test);
#   no_llm=True renders floor-only rows deterministically (the
#   suite's path; zero cost); writes 07_business_descriptions_output.json, the
#   per-file texts (status marks per line), 07_business_descriptions_code_sightings_output
#   .json. The registry is READ-ONLY to the build — a byte-
#   identity test enforces it.
# ====================================================================
# ==== (pseudo code APPROVED 2026-10-03, Sunny: "go" — real code
#       follows) =====================================================
# ==== SUPERSESSION NOTE 2026-10-03 (same day, the debug01 arc):
# the block above is 07.1.0 HISTORY. GATE v2 replaced G-1..G-7:
# the lexical whitelist is RETIRED, the template is FIVE lines
# (One row is: leading), budgets retired, domain knowledge free,
# estate facts must trace, model seat gpt-5.4. The contract's
# "THE GATE v2" section and the design doc's Gate v2 ruling are
# the law the code below implements. ============================

import csv
import json
import re
import time
from pathlib import Path

import technical_descriptions as td

BASIS_VERSION = "07.2.0"  # Gate v2 + the five-line card (2026-10-03)

# The template labels (S7), in ruled order.
TEMPLATE_LABELS = ["One row is:", "Who's in it:",
                   "Each row shows:", "Time window:",
                   "Excludes:"]

# The Business Term card labels (THE ONE-GATE RULING,
# 2026-10-05): phase 09's card rides THIS gate as grain
# "term_card" — one gate, one law, two consumers. The 07 chat
# sheet's free-form "scope" grain stands unchanged (its
# adoption or retirement is Sunny's open ruling).
TERM_CARD_LABELS = ["Definition:", "One row is:", "Keeps:",
                    "Excludes:"]
# the line-ownership markers (shared by the file arm below)
NEGATIVE_MARKERS = ("other than", "excluded", "exclude",
                    " not ", "except")

BANNED_WORDS = {"join", "select", "query", "table", "temp",
                "column", "procedure", "parameter"}

RESTRICTION_WORDS = {"only", "limited", "restricted"}

# THE NEVER-LIST (Gate v2, V-2): format/purpose claim words — the
# lie taxonomy. EXACT token match, grows only by Sunny's ruling.
# The whitelist/lexicon of 07.1.0 is RETIRED (design doc, Gate v2).
NEVER_LIST = {"separator", "delimiter", "comma", "semicolon",
              "formatted", "supports", "enables", "helps",
              "intended", "purpose"}

_SIGHTINGS = []


def reset_sightings():
    del _SIGHTINGS[:]


def code_sightings():
    return list(_SIGHTINGS)


def _tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def _docket_text(docket):
    return docket["text"] if isinstance(docket, dict) else docket


def gate(audience_text, docket, grain, registry=None,
         verdicts=None):
    """GATE v2 (contract law, 2026-10-03): the estate boundary —
    customer-specific facts must trace to the docket; general
    domain knowledge is FREE. No whitelist, no word budgets. No
    model anywhere in here.
    V-1 AMENDED 2026-10-08 (D15 comment-first): digits a
    comment names never ride raw — the annotation's words
    speak; her verdicts (show/omit, recorded on the row) are
    honored here."""
    findings = []
    dtext = _gate_reference(docket)
    toks = _tokens(audience_text)
    verdicts = verdicts or {}
    # the annotation pairs the docket carries: 'words' (digits).
    # Digits riding WITH their words in the text itself are the
    # sanctioned meaning-first shape — only BARE digits draw the
    # use-the-words finding (the fact-voice regression lock).
    pairs = {d: w for w, d in re.findall(
        r"'([^']+)'\s*\((\d+(?:\.\d+)?)\)", dtext)}
    paired_in_text = {d for _, d in re.findall(
        r"'([^']+)'\s*\((\d+(?:\.\d+)?)\)", audience_text)}

    # V-1 grounded values: quoted literals and numbers
    # a quoted VALUE is '-delimited with non-letter boundaries —
    # apostrophes inside words (Who's, patient's) are not quotes
    qpat = r"(?<![A-Za-z])'[^']*'(?![A-Za-z])"
    for q in re.findall(qpat, audience_text):
        if q not in dtext:
            findings.append(f"V-1: quoted {q} not in the docket")
    unquoted = re.sub(qpat, " ", audience_text)
    for n in set(re.findall(r"\b\d+\b", unquoted)):
        if verdicts.get(n) == "show":
            continue                     # her ruling: may ride
        if verdicts.get(n) == "omit":
            findings.append(f"V-1: the number {n} must stay "
                            "out (her ruling: keep it out)")
            continue
        if n in pairs and n not in paired_in_text \
                and pairs[n].lower() not in audience_text.lower():
            # an EXPLAINED number is fine — words anywhere in
            # the card (her intent: translate via the comment);
            # only BARE digits draw the finding
            findings.append(f"V-1: use the annotation's words "
                            f"for {n} ('{pairs[n]}'), not the "
                            "digits")
            continue
        if n not in dtext:
            findings.append(f"V-1: number {n} has no stored "
                            "basis")
            _SIGHTINGS.append({"code": n,
                               "context": audience_text[:120]})

    # V-2 the never-list (exact tokens)
    for t in set(toks):
        if t in NEVER_LIST:
            findings.append(f"V-2: never-list word '{t}'")

    # V-3 register: SQL vocabulary and @tokens
    for t in set(toks):
        if t in BANNED_WORDS or (t.endswith("s")
                                 and t[:-1] in BANNED_WORDS):
            findings.append(f"V-3: SQL word "
                            f"'{t[:-1] if t not in BANNED_WORDS else t}'")
    for m in re.findall(r"@\w+", audience_text):
        findings.append(f"V-3: banned token '{m}'")

    # V-4 the five-line template (file grain) + the field arm
    lines = [ln.strip() for ln in audience_text.splitlines()
             if ln.strip()]
    if grain == "field":
        if len(lines) > 1 or "**" in audience_text \
                or audience_text.strip().startswith("#"):
            findings.append("V-4: a field is one short plain "
                            "paragraph — no markdown, no "
                            "labels, no line breaks")
    if grain == "term_card":
        # the TERM-CARD arm (THE ONE-GATE RULING, 2026-10-05):
        # exactly the four labels, negatives only on Excludes
        if len(lines) != len(TERM_CARD_LABELS) or not all(
                ln.startswith(lab) for ln, lab in
                zip(lines, TERM_CARD_LABELS)):
            findings.append("V-4: the term card is exactly the "
                            "four labeled lines — Definition / "
                            "One row is / Keeps / Excludes, in "
                            "order")
        for ln in lines:
            if not ln.startswith("Excludes:") and any(
                    neg in ln.lower() for neg in NEGATIVE_MARKERS):
                findings.append("V-4: line ownership — negative "
                                "language lives ONLY on Excludes; "
                                "found on: " + ln.split(":")[0])
    if grain == "file":
        for ln in lines:
            if ln.startswith("Who's in it:") and any(
                    neg in ln.lower() for neg in
                    ("other than", "excluded", "exclude",
                     " not ", "except")):
                findings.append(
                    "V-4: line ownership — negatives (other "
                    "than / excluded / not) live ONLY in "
                    "Excludes; Who's in it is the positive "
                    "population")
        if len(lines) != 5 or not all(
                ln.startswith(lab) for ln, lab in
                zip(lines, TEMPLATE_LABELS)):
            findings.append("V-4: template shape — exactly the "
                            "five labeled lines")

        # V-5 the kinds backstop
        for ln in lines:
            if ln.startswith("Each row shows:"):
                bare = re.sub(r"\([^)]*\)", "", ln)
                items = re.split(r"[;,]| and ", bare)
                if len(items) > 10:
                    findings.append(
                        "V-5: drop the field enumeration — the "
                        "complete field list already lives in "
                        "the technical appendix; name at most 5 "
                        f"KINDS ({len(items)} items)")

        # V-6 must-say (exactly three members)
        if isinstance(docket, dict):
            low = audience_text.lower()
            if docket.get("gap") and not any(
                    k in low for k in ("gap", "not described",
                                       "not covered",
                                       "built as a string",
                                       "run time")):
                findings.append("V-6: the gap must be said")
            if docket.get("params") and "window" not in low:
                findings.append("V-6: the window must be said")
            if docket.get("population") and                     "excludes:" not in low:
                findings.append("V-6: the Excludes line must "
                                "exist")

    # V-7 attachment anchor
    has_membership = ("Population:" in dtext
                      or (": " in dtext and
                          "no membership conditions" not in dtext))
    if any(t in RESTRICTION_WORDS for t in toks)             and not has_membership:
        findings.append("V-7: restriction speech without a "
                        "membership row to anchor it")

    return list(dict.fromkeys(findings))


def _table_descriptions(dir02):
    t = td._read(Path(dir02) /
                 "02_emr_data_dictionary_extraction_table.json")
    return {r["table_name"].upper(): r.get("table_description")
            for r in t if r.get("table_description")}


def _source_lines(dir05, dir02, fname):
    """The DOCKET AMENDMENT (2026-10-03, Sunny's find): the 02
    table descriptions of every base table the file reads — the
    dictionary's own words, for the proposer to translate from."""
    descs = _table_descriptions(dir02)
    tables = set()
    for r in td._read(Path(dir05) / "05_semantic_graph_resolves_edges_output.json"):
        if r["to_kind"] == "table" \
                and r["from_id"].split("::")[1] == fname:
            tables.add(r["to_id"].upper())
    return [f"Sources: {t} — {descs[t]}"
            for t in sorted(tables) if t in descs]


def docket_for_file(dir05, dir06, dir02, fname):
    rows = json.loads((Path(dir06) /
                       "06_technical_descriptions_output.json").read_text())
    file_s = next(r["sentence"] for r in rows
                  if r["node_id"] == f"file::{fname}")
    scope_s = [r["sentence"] for r in rows
               if r["grain"] == "scope"
               and r["node_id"].split("::")[1] == fname]
    text = "\n".join([file_s] + scope_s
                     + _source_lines(dir05, dir02, fname))
    return {"text": text,
            "gap": "in this gap" in file_s,
            "params": "Parameters shaping the population"
                      in file_s,
            "population": "Population:" in file_s}


# ---- the prompt constructor (deterministic; example-free by law)

SYSTEM_PROMPT = (
 "You are a senior healthcare BI analyst. You receive a machine-"
 "generated technical description of a report's SQL logic. FIRST "
 "understand what the logic actually does; THEN explain its "
 "MEANING to the people who use the report in your own words — complete, "
 "natural sentences, never mirroring the technical phrasing.\n"
 "USE YOUR DOMAIN KNOWLEDGE freely to explain what standard "
 "healthcare/EMR concepts mean operationally. Decode provable "
 "logic plainly: day-adding date arithmetic usually means an "
 "inclusive end date; a filter accepting a special value or a "
 "listed identifier is a multi-select choice (say what the "
 "special value does); created/deleted rules against an as-of "
 "date mean data as it stood on that date. Stay silent only "
 "about genuinely opaque expressions.\n"
 "THE ESTATE BOUNDARY (hard): every CUSTOMER-SPECIFIC fact — "
 "names, codes, values, filters, formats in THIS data — must "
 "come from the technical description; never guess those; never "
 "invent formats or purposes.\n"
 "REGISTER: no SQL vocabulary, no tokens starting with @, no "
 "symbols like >= or &.\n"
 "RELEVANCE (S12): data-quality housekeeping conditions — "
 "unlinked or incomplete records, record-entry timing checks — "
 "are summarized plainly in Excludes (e.g. records not linked "
 "to a patient); business logic gets the prose. When a record "
 "is excluded for not linking to its reference records, name "
 "what it is missing in plain words; never abstract phrases "
 "like 'related selections' or 'required records'.\n"
 "PLAIN DICTION (S13): plain connectors — in, with, during; "
 "never legal-ese like provided, passed, accepted, subject to.\n"
 "PROMPTS AS CHOICES (S14): multi-select filters driven by "
 "report inputs are 'chosen when running the report'; a special "
 "value that makes a filter true for every row means \"All\" — "
 "say the choice, not the mechanism. Rows kept or dropped by "
 "those selections are described as in, or not in, the chosen "
 "values — never as matching 'required', 'linked', or counted "
 "selections.\n"
 "SPEAK TO THE READER, NEVER ABOUT THEM (S15): never name the "
 "audience in the text — no 'for business users', 'business "
 "reader', 'colleagues'; state the meaning directly, and run-"
 "time choices are made by 'the person running the report'.\n"
 "EFFECTIVE TIME DICTION (S16): an effective date or time is "
 "when the event took effect — never say 'scheduled' or any "
 "planned-future wording for it.\n"
 "NO MECHANISM MARKERS (S17): internal markers — constants, "
 "flag values, helper columns that exist only to mark a match "
 "— are never described; say what the row means instead.\n"
 "NO META-COMMENTARY (S18): never remark on the documentation "
 "itself — what a source list mentions, what is or is not "
 "described there; speak only about the data.\n"
 "ONE HOME PER FACT: each fact speaks once, on the line that "
 "owns it (as-of and date logic belong to Time window).\n"
 "TONE: write in the voice of an experienced clinician "
 "explaining this data to colleagues — the plain, concrete way "
 "clinical staff talk about patients, beds and events; never "
 "the abstract voice of a systems document.")

_GRAIN_INSTRUCTIONS = {
    "file": ("Grain: a whole report dataset. On the 'Each row "
             "shows' line name AT MOST 5 KINDS of information "
             "and no individual fields — the COMPLETE field "
             "list is already published in this report's "
             "technical appendix, so omit fields confidently.\n"
             "Produce exactly these five labeled lines:\n"
             "One row is: <what one row IS, in business "
             "meaning>\n"
             "Who's in it: <the POSITIVE population only: who "
             "+ the window reference (name the reporting "
             "period ONLY — the as-of behavior never appears "
             "here; it lives on Time window) + ONE natural "
             "sentence "
             "for run-time choices (plurals natural; choosing "
             "All includes all). NO negatives here — every "
             "exclusion and housekeeping condition belongs on "
             "the Excludes line>\n"
             "Each row shows: <at most 5 kinds>\n"
             "Time window: <the window and as-of behavior, "
             "decoded>\n"
             "Excludes: <the exclusions, named>"),
    "scope": ("Grain: one selection inside the dataset build. "
              "At most 3 natural sentences describing what this "
              "selection contains."),
    "field": ("Grain: one delivered field. Describe THE FIELD "
              "ONLY in one or two natural sentences — what it "
              "holds and what it means, in plain clinical terms. "
              "The filters shown below are CONTEXT so you "
              "understand the data's scope — NEVER restate the "
              "population, date window or as-of behavior; those "
              "live once, on the report's card. One plain "
              "paragraph: no markdown, no labels, no line "
              "breaks."),
}


def build_prompt(grain, docket_text, findings):
    parts = [SYSTEM_PROMPT, "", _GRAIN_INSTRUCTIONS[grain], "",
             "TECHNICAL DESCRIPTION:", docket_text]
    if findings:
        parts += ["", "GATE OBJECTIONS (resolve every one):"]
        parts += [f"- {f}" for f in findings]
    return "\n".join(parts)


# ---- the effective ladder (ported law)

def effective(row, registry):
    for s in registry.get("sentences", []):
        if s.get("node_id") == row["node_id"] and \
                s.get("blessed_text"):
            return s["blessed_text"]
    return row["audience_text"]


# ---- the build

def _field_nodes(dir05, dir02, dir01=None):
    """Delivery-scope projection outputs — the report fields
    (G2a: minted via the importable 06 machinery)."""
    dir05 = Path(dir05)
    g = td._load_graph(dir05)
    words, values = td._load_words(Path(dir02))
    voice = td._Voice(g, words, values)
    scopes = td._read(dir05 / "05_semantic_graph_scope_output.json")
    out = []
    for sc in scopes:
        if sc["scope_kind"] != "delivery":
            continue
        for pid_ in td._scope_structures(g, sc["node_id"],
                                         "PROJECTION"):
            for k in g["children"].get(pid_, []):
                if k in g["exprs"]:
                    voice.refs = []
                    item = td._payload_item(voice, k,
                                            sc["node_id"])
                    out.append((k, sc["node_id"], item))
    return out


# PSEUDO-CODE — D12 incremental delivery, the 07 arm
# (10_work_wheel.md, ruled 2026-10-07; red tests: test_07
# skip_files x2). APPROVED by Sunny 2026-10-07; the code follows:
#
#   1. New param skip_files=frozenset() — file STEMS already
#      described (deliver() computes them from the hash ledger;
#      callers never type names).
#   2. THE REFUSAL FIRST: skip_files non-empty -> the prior
#      07_business_descriptions_output.json must exist in out07 and hold rows
#      for EVERY skipped stem; anything missing -> ValueError
#      naming the prior sheet. Skipping needs something to carry —
#      never a silent hole.
#   3. The skip lands BEFORE spec construction (the only_file
#      precedent: filter `files`+`six` down to the active set) —
#      NOT at the propose loop. Reason: live-mode specs render
#      FACT VOICES per file, which are themselves paid calls; a
#      skipped file must cost zero, voices included.
#   4. After the active rows build, the skipped files' rows are
#      APPENDED from the prior sheet VERBATIM — text, status,
#      model, basis, untouched. The per-file txt loop keeps the
#      full file list, so every file's txt regenerates (carried
#      rows included) and the sheet stays whole.
#   5. 07_business_descriptions_code_sightings_output.json stays what it is — the audit of
#      THIS run's proposals; carried nodes add none.
#   6. only_file and skip_files compose (only_file first, then
#      skip subtracts); checkpoint behavior among active specs is
#      unchanged.


# ==== PSEUDO — 0.8.0 THE NO-FALLBACK GATE (D15, ruled =========
# 2026-10-08 evening; contracts amended same day; AWAITING
# SUNNY'S APPROVAL; red tests before code):
#
#   THE DOCKET:
#   1. File grain gains the header line: td.header_description
#      (the SQL's own "Description:" text) rides the docket
#      FIRST — the card's first-choice wording (her ruling).
#
#   THE GATE (V-1 amendment):
#   2. ANNOTATED NUMBERS: the docket's meaning-first pairs
#      ("'<words>' (<digits>)") are extracted mechanically; a
#      card writing such digits RAW gets the named finding
#      "use the annotation's words, not the digits" — REPAIRABLE
#      (the words are right there).
#   3. BASIS GAPS: a number with NO annotation pair and no
#      other docket grounding = basis_gap — NOT repairable by
#      wording: NO repair rounds (zero paid retries), the row
#      goes straight to awaiting_human.
#
#   THE STATUS (the floor retires as a business text):
#   4. awaiting_human rows: audience_text EMPTY (never the 06
#      sentence), last_proposal + gate_findings kept, plus
#      questions: [{"number", "where" (table.column from the
#      sighting), "finding"}] — her read surface.
#   5. HER VERDICTS, recorded ON the row (no new file):
#      bd.answer(out07, node_id, number, "show" | "omit") —
#      her hand only. "Fix the SQL" needs no function: the
#      file's hash changes and the batch re-takes it.
#   6. THE RE-TAKE: build07's skip-carry carries awaiting_human
#      rows UNCHANGED unless a verdict arrived — a carried row
#      with a verdict moves back to ACTIVE and re-proposes
#      (one paid card), the verdict steering the prompt:
#      show -> the digits may ride; omit -> speak without it.
#   7. Repair rounds stay 3 for every repairable class;
#      basis_gap alone skips them (her words: the goal is not
#      to fall back — surface to the human).
#   (ITEMS 3-7 SUPERSEDED 2026-10-10 by the 0.10.0 ANSWERS
#   FILE block below — basis gaps now ship with the number
#   shown; awaiting_human narrows to wording failures;
#   bd.answer() retires. Items 1-2 stand whole.)
# ===============================================================
#
# ==== PSEUDO — 0.10.0 THE ANSWERS FILE (ruled 2026-10-10, ====
# her words: "when a value is not mapped, can we just show
# it? don't block the description ... log it in the human
# eyes log" + "one file, all answers in it, retire the
# ANSWER cell"; contracts amended same day: 07 status +
# answers file + V-1, 10 D15, 11 D3/D8 + scorecard keys,
# 09 awaiting/publish, 02 second writer; AWAITING SUNNY'S
# APPROVAL; red tests before code):
#
#   THE DEFAULT FLIP (supersedes 0.8.0 items 3-7):
#   1. A basis_gap number no longer blocks: the card SHIPS,
#      the digits spoken plainly through the column's words
#      ("departments 100108047, ..."), claiming NO meaning.
#      Still zero repair rounds, zero escalation for the gap
#      itself; a card that ASSERTS an unstored meaning still
#      fails V-1 — show-plainly never licenses invention.
#   2. The shipped row carries open_questions:
#      [{"number", "where" (table.column), "finding"}].
#      awaiting_human remains ONLY for the wording class
#      that exhausts the 3-round budget (audience_text
#      empty, last_proposal + gate_findings kept, as today).
#
#   THE ONE ANSWERS FILE (the human-eyes log, editable):
#   3. <out07>/07_business_descriptions_answers_output.csv —
#      one row per question: node_id, file, where, value,
#      asked_at, answer (BLANK | meaning text | show |
#      omit), answered_at, status (open | closed),
#      closed_by (comment | answer | dictionary | show |
#      omit). CSV so the data owner fills it in Excel and
#      it can travel.
#   4. MERGE-NEVER-OVERWRITE: describe() APPENDS new
#      question rows (key: node_id + where + value) and
#      never touches a human-filled cell; a question already
#      present (open or closed) is never re-added.
#
#   THE PICKUP (every describe run, before proposing —
#   no watcher, no new daemon):
#   5. For each OPEN row, in order:
#      a. file hash changed (SQL comment added) -> the hash
#         retake as today; close as closed_by=comment.
#      b. answer = meaning text -> write the 02 value
#         meaning (provenance = answers file, dated) ->
#         that one node re-proposes with the meaning in the
#         docket (one paid call); close as closed_by=answer.
#      c. answer = show -> close FREE (the card already
#         shows the number); no retake, closed_by=show.
#      d. answer = omit -> one retake told to speak without
#         it; close as closed_by=omit.
#      e. the 02 dictionary now resolves (where, value) —
#         the F1 bulk route landed -> retake with the
#         meaning; close as closed_by=dictionary.
#   6. The retake is the checkpoint-seed retake (one node,
#      one paid card, nothing else pays); on gate pass the
#      row's open_questions entry clears.
#
#   THE RETIREMENTS + SURFACES:
#   7. bd.answer() RETIRES (no shim — the notebook cell goes
#      with it; the runbook ANSWER step rewrites to "fill
#      the answers CSV, re-run DESCRIBE").
#   8. Delivery txt: a file whose rows carry open_questions
#      prints "DELIVERED WITH QUESTIONS (n)" + the rows;
#      AWAITING keeps only wording failures. Collibra
#      publish PROCEEDS for delivered-with-questions files;
#      the skip stays for awaiting_human + files_waiting.
#   9. Scorecard: status_counts gain
#      delivered_with_questions; new questions block {open,
#      closed_this_run, by_closure}; awaiting[] = wording
#      only; conservation: questions.open == the file's
#      open rows, closed_this_run == sum(by_closure).
# ===============================================================
#
# ==== PSEUDO — 0.11.0 THE UNIFORM SHIP (ruled 2026-10-10 ====
# evening, her words: "ship description for this type of gate
# failures, and register the reason/wording violations ...
# does not stop the production ... does not get lost either";
# her two rulings same sitting: ALL finding classes ship
# (uniform), publish IMMEDIATELY; contracts amended same
# evening: 07 status+answers file, 09 voice+publish, 10 D15,
# 11 scorecard; AWAITING SUNNY'S APPROVAL; red before code):
#
#   THE SHIP (supersedes the 0.10.0 wording-waits rule):
#   1. _propose_loop exhaust WITH text -> status gate_failed,
#      the final text ships as audience_text; findings kept
#      verbatim on the row (the register). Exhaust with NO
#      text (three failed calls) -> awaiting_human, the last
#      class standing.
#   2. effective ladder: blessed > gate_passed > gate_failed
#      (> floor); a blessed sentence still silences a failed
#      card at render, free.
#
#   THE REGISTER (the one answers file grows):
#   3. CSV gains kind (value | wording) + finding columns.
#      MIGRATION READ: an old csv without them reads once as
#      kind=value; every write lands the new header.
#   4. A shipped gate_failed card adds one wording row per
#      finding: kind=wording, value empty, finding verbatim.
#      Value rows now carry their finding text too.
#   5. HER ANSWERS on a wording row:
#      - replacement text -> a BLESSED sentence in the 07
#        registry (dated, provenance = the answers file; the
#        ratify clause's second hand door) -> next build
#        renders her words, ZERO paid calls; closed_by=bless.
#        ALL the node's wording rows close together (one text
#        answers every finding on the card).
#      - "accept" -> the shipped text stands, a recorded
#        waiver; closed_by=accept; no retake.
#      - blank -> stays open; never lost, never re-added.
#   6. A re-proposed node (hash change) whose finding
#      dissolved closes its wording rows as closed_by=comment
#      (same law as value rows).
#
#   THE MIGRATION (free, the PTA/LOTE unblock):
#   7. A CARRIED awaiting_human row WITH last_proposal
#      converts at carry time: status gate_failed,
#      audience_text = last_proposal, findings registered to
#      the csv — zero paid calls. A carried awaiting row with
#      NO text stays awaiting (nothing to ship).
#
#   THE SURFACES:
#   8. ai_delivery: a gate_failed FILE row ships BUSINESS
#      voice (the technical floor no longer stands in);
#      status gate_failed rides the entry; registered
#      findings ride as open_findings; publish proceeds
#      (her ruling) — the Collibra skip keeps only
#      awaiting_human + files_waiting.
#   9. Delivery txt: "DELIVERED WITH FINDINGS (n)" + the
#      findings verbatim under the text; AWAITING remains
#      only for empty-text cards.
#  10. Scorecard: gate_failed joins status_counts;
#      questions{} counts wording rows too (they live in the
#      same csv); by_closure gains bless + accept;
#      awaiting[] = empty-text cards only.
# ===============================================================
#
# ==== PSEUDO — 0.7.0 THE 07 RENAMES (the naming law, ruled ====
# 2026-10-08, step table row 07; AWAITING SUNNY'S APPROVAL):
#   07_business_sheet.json    -> 07_business_descriptions_output.json
#   07_blessing_registry.json -> 07_business_descriptions_blessings_output.json
#   07_code_sightings.json    -> 07_business_descriptions_code_sightings_output.json
#   07_fact_voices.json       -> 07_business_descriptions_fact_voices_output.json
#   07_live_checkpoint.json   -> 07_business_descriptions_checkpoint_output.json
#   TWO MIGRATION READS here (the ledger precedent — a rename
#   must never lose paid or ruled content):
#   - the BLESSING REGISTRY: her ruled truth, carried across
#     runs — new name read first, old honored once, every write
#     lands the new name. business_terms.REGISTRY flips with
#     this landing.
#   - the PRIOR SHEET for skip-carry: a pre-rename tenant's
#     D12 carry must find the old 07_business_descriptions_output.json once,
#     else described files would refuse or re-pay.
#   The other three regenerate whole. Readers: ai_delivery,
#   sqldesc_cli + fixtures, same landing.
# ===============================================================
# ==== THE ANSWERS FILE (0.10.0, ruled 2026-10-10 — "one file,
# all answers in it"; the human-eyes log made editable) =========

ANSWERS_NAME = "07_business_descriptions_answers_output.csv"
_ANSWERS_FIELDS = ["node_id", "file", "kind", "where", "value",
                   "finding", "asked_at", "answer",
                   "answered_at", "status", "closed_by"]
_VALUES_SHEET = "02_emr_data_dictionary_extraction_value.json"


def _read_answers(path):
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        # THE MIGRATION READ (0.11.0): a pre-0.11.0 csv has no
        # kind/finding columns — old rows read as kind=value;
        # every write lands the new header
        r.setdefault("kind", "value")
        r.setdefault("finding", "")
        r["kind"] = r["kind"] or "value"
    return rows


def _write_answers(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=_ANSWERS_FIELDS)
        w.writeheader()
        w.writerows(rows)


def _close_answer(a, how):
    a["status"] = "closed"
    a["closed_by"] = how
    a["answered_at"] = time.strftime("%Y-%m-%d")
    _METER["closures"][how] = \
        _METER["closures"].get(how, 0) + 1


def _dictionary_meaning(dir02, where, value):
    """The F1 bulk route: a stored (table, code) meaning. The
    table must be KNOWN (the where) — a bare code matched across
    every table would invent a basis, and no mechanism may."""
    if not where:
        return None
    table = str(where).split(".")[0].upper()
    vp = Path(dir02) / _VALUES_SHEET
    if not vp.exists():
        return None
    for r in json.loads(vp.read_text()):
        if str(r.get("table_name", "")).upper() == table \
                and str(r.get("code")) == str(value):
            return r.get("meaning")
    return None


def _store_value_meaning(dir02, where, value, meaning):
    """Her filled meaning becomes a 02 value-meaning row —
    the one store, provenance kept (the 02 contract's second
    writer, amended 2026-10-10)."""
    vp = Path(dir02) / _VALUES_SHEET
    vals = json.loads(vp.read_text()) if vp.exists() else []
    vals.append({"table_name": str(where or "").split(".")[0],
                 "code": str(value), "meaning": meaning,
                 "source": ANSWERS_NAME,
                 "dated": time.strftime("%Y-%m-%d")})
    vp.write_text(json.dumps(vals, indent=1))


def _bless_from_answers(out07, bless_texts):
    """0.11.0: a replacement text filled on a wording row lands
    as HER blessed sentence — dated, provenance the answers
    file. Delta-by-name: one sentence per node, the new ruling
    replaces the old."""
    out07 = Path(out07)
    reg_path = out07 / \
        "07_business_descriptions_blessings_output.json"
    read_path = reg_path
    if not read_path.exists():
        legacy = out07 / "07_blessing_registry.json"
        if legacy.exists():
            read_path = legacy
    registry = (json.loads(read_path.read_text())
                if read_path.exists()
                else {"names": [], "sentences": []})
    today = time.strftime("%Y-%m-%d")
    for node_id, text in bless_texts.items():
        registry["sentences"] = [
            s for s in registry.get("sentences", [])
            if s.get("node_id") != node_id]
        registry["sentences"].append(
            {"node_id": node_id, "blessed_text": text,
             "ruling": f"RULED {today} (the data owner, via "
                       f"{ANSWERS_NAME}): wording answer"})
    reg_path.write_text(json.dumps(registry, indent=1))


def _inject_meanings(docket, pairs):
    """The retake's docket carries the answered meaning as an
    annotation pair — the card speaks the words, V-1 grounds
    them."""
    extra = "\n".join(f"- '{m}' ({v})" for v, m in pairs)
    if isinstance(docket, dict):
        docket = dict(docket)
        docket["facts"] = (docket.get("facts") or "") \
            + "\n" + extra
        docket["text"] = (docket.get("text") or "") \
            + "\n" + extra
        return docket
    return docket + "\n" + extra


def build07(dir05, dir06, out07, dir02, no_llm=False,
            proposer=None, only_file=None,
            skip_files=frozenset(), defer_files=frozenset()):
    """The build command's door. no_llm=True renders floor-only
    rows deterministically (the suite's path, zero cost). The
    live path (harness laws, amended 2026-10-03): explicit call
    timeout, CHECKPOINT-PER-NODE with resume (completed nodes
    are never re-paid), one progress line per node.
    skip_files (D12, 2026-10-07): stems already described — zero
    cost, voices included; their rows carry from the prior sheet.
    defer_files (D12 batch door): stems new-but-beyond-max_new —
    NOT in this run at all: no rows, no carry, no refusal."""
    dir05, dir06 = Path(dir05), Path(dir06)
    out07, dir02 = Path(out07), Path(dir02)
    six = json.loads((dir06 / "06_technical_descriptions_output.json")
                     .read_text())
    files = sorted({r["node_id"].split("::")[1] for r in six
                    if r["grain"] == "file"})
    if only_file:
        files = [f for f in files if f == only_file]
        six = [r for r in six
               if r["node_id"].split("::")[1] == only_file]
    defer_files = frozenset(defer_files)
    if defer_files:
        files = [f for f in files if f not in defer_files]
        six = [r for r in six
               if r["node_id"].split("::")[1] not in defer_files]
    skip_files = frozenset(skip_files) & set(files)
    # THE PICKUP (0.10.0, ruled 2026-10-10 — supersedes the
    # verdict-on-the-row retake): the answers file is the one
    # human door. A filled answer on a carried row closes its
    # question — show closes FREE, omit re-proposes without the
    # number, a meaning lands in 02 and re-proposes with it; a
    # 02 dictionary row that arrived since (the F1 bulk route)
    # closes the same way. Only the answered nodes re-pay; their
    # siblings seed the checkpoint (the retake mechanics stand).
    answers_path = out07 / ANSWERS_NAME
    answers = _read_answers(answers_path)
    retake_verdicts = {}
    retake_meanings = {}
    checkpoint_seed = {}
    carried = []
    if skip_files:
        sheet_path = out07 / "07_business_descriptions_output.json"
        if not sheet_path.exists():
            # THE MIGRATION READ (2026-10-08): a pre-rename
            # tenant's carry must not refuse or re-pay
            legacy = out07 / "07_business_sheet.json"
            if legacy.exists():
                sheet_path = legacy
        if not sheet_path.exists():
            raise ValueError(
                "skip_files needs the prior 07_business_descriptions_output.json "
                f"in {out07} — nothing to carry")
        prior_rows = json.loads(sheet_path.read_text())
        have = {r["node_id"].split("::")[1] for r in prior_rows}
        missing = sorted(skip_files - have)
        if missing:
            raise ValueError(
                "the prior 07_business_descriptions_output.json has no rows "
                "for: " + ", ".join(missing))
        carried = [r for r in prior_rows
                   if r["node_id"].split("::")[1] in skip_files]
        # THE CONVERT (0.11.0, free — the PTA/LOTE unblock): a
        # carried awaiting row that HOLDS a rejected card ships
        # it — status gate_failed, zero paid calls; its numbered
        # questions become open value questions, its findings
        # register below. An awaiting row with NO text stays.
        converted = []
        for r in carried:
            if r.get("status") == "awaiting_human" \
                    and r.get("last_proposal"):
                r = dict(r)
                r["status"] = "gate_failed"
                r["audience_text"] = r.pop("last_proposal")
                r["open_questions"] = [
                    q for q in r.pop("questions", [])
                    if q.get("number")]
            converted.append(r)
        carried = converted
        by_id = {r["node_id"]: r for r in carried}
        retake_ids = set()
        bless_texts = {}
        for a in answers:
            if a.get("status") != "open":
                continue
            row = by_id.get(a["node_id"])
            if row is None:
                continue
            ans = (a.get("answer") or "").strip()
            if a.get("kind") == "wording":
                # 0.11.0: a wording row takes "accept" (the
                # shipped text stands, recorded waiver) or her
                # REPLACEMENT TEXT (-> a blessed sentence,
                # applied below); blank stays open
                if ans == "accept":
                    _close_answer(a, "accept")
                elif ans:
                    bless_texts[a["node_id"]] = ans
                continue
            if ans == "show":
                if row.get("status") == "awaiting_human":
                    # a BLOCKED row (an 0.8.0/0.9.0 tenant's
                    # carry, or a wording failure): no text
                    # shipped — show must re-propose, steered
                    retake_verdicts.setdefault(
                        a["node_id"], {})[str(a["value"])] = \
                        "show"
                    retake_ids.add(a["node_id"])
                else:
                    # the card already shows the number —
                    # closes FREE
                    row = dict(row)
                    row["open_questions"] = [
                        q for q in row.get("open_questions", [])
                        if str(q.get("number")) != str(a["value"])]
                    by_id[a["node_id"]] = row
                _close_answer(a, "show")
            elif ans == "omit":
                retake_verdicts.setdefault(
                    a["node_id"], {})[str(a["value"])] = "omit"
                retake_ids.add(a["node_id"])
                _close_answer(a, "omit")
            elif ans:
                # her meaning: the 02 store grows, the retake
                # speaks it (one paid card)
                _store_value_meaning(dir02, a.get("where"),
                                     a["value"], ans)
                retake_meanings.setdefault(
                    a["node_id"], []).append((a["value"], ans))
                retake_ids.add(a["node_id"])
                _close_answer(a, "answer")
            else:
                m = _dictionary_meaning(dir02, a.get("where"),
                                        a["value"])
                if m is not None:
                    retake_meanings.setdefault(
                        a["node_id"], []).append((a["value"], m))
                    retake_ids.add(a["node_id"])
                    _close_answer(a, "dictionary")
        carried = list(by_id.values())
        if bless_texts:
            # HER REPLACEMENT TEXT -> the blessed sentence (the
            # ratify clause's second hand door: the fill IS her
            # dated ruling, provenance the answers file); free —
            # the render below speaks her words, no paid call.
            # ALL the node's open wording rows close together.
            _bless_from_answers(out07, bless_texts)
            for a in answers:
                if a.get("kind") == "wording" \
                        and a.get("status") == "open" \
                        and a["node_id"] in bless_texts:
                    _close_answer(a, "bless")
        if retake_ids:
            retake_files = {n.split("::")[1] for n in retake_ids}
            checkpoint_seed = {
                r["node_id"]: r for r in carried
                if r["node_id"].split("::")[1] in retake_files
                and r["node_id"] not in retake_ids}
            carried = [r for r in carried
                       if r["node_id"].split("::")[1]
                       not in retake_files]
            skip_files = skip_files - retake_files
    active = [f for f in files if f not in skip_files]
    six = [r for r in six
           if r["node_id"].split("::")[1] not in skip_files]
    reg_path = out07 / "07_business_descriptions_blessings_output.json"
    if not reg_path.exists():
        # THE MIGRATION READ (2026-10-08): her blessings survive
        # the rename — the old name is honored when the new one
        # is absent; every write lands the new name.
        legacy_reg = out07 / "07_blessing_registry.json"
        if legacy_reg.exists():
            reg_path = legacy_reg
    registry = (json.loads(reg_path.read_text())
                if reg_path.exists()
                else {"names": [], "sentences": []})

    # the ordered node specs: (node_id, grain, docket, floor)
    # FILE grain rides DOCKET v2 (FACTS/CONTEXT + fact voices,
    # ruled 2026-10-04); voices are skipped under no_llm.
    specs = []
    for f in active:
        if no_llm:
            docket, _items = docket_v2_for_file(
                dir05, dir06, dir02, f)
        else:
            _, items = render_facts(dir05, dir06, dir02, f)
            t_v = time.monotonic()
            voices = voice_facts(
                items, out07 / "07_business_descriptions_fact_voices_output.json", registry)
            _meter_stage("fact_voices", time.monotonic() - t_v)
            docket, _items = docket_v2_for_file(
                dir05, dir06, dir02, f, voices=voices)
        (out07 / f"{f}.facts.txt").write_text(
            docket["facts"] + "\n")
        floor = next(r["sentence"] for r in six
                     if r["node_id"] == f"file::{f}")
        specs.append((f"file::{f}", "file", docket, floor))
    src_by_file = {f: "\n".join(_source_lines(dir05, dir02, f))
                   for f in active}
    for r in six:
        if r["grain"] == "scope":
            fname = r["node_id"].split("::")[1]
            docket = r["sentence"] + (
                "\n" + src_by_file[fname]
                if src_by_file.get(fname) else "")
            specs.append((r["node_id"], "scope", docket,
                          r["sentence"]))
    field_shared = {}
    for expr_id, scope_id, item in _field_nodes(dir05, dir02):
        fname = scope_id.split("::")[1]
        if only_file and fname != only_file:
            continue
        if fname in skip_files or fname in defer_files:
            continue
        ffacts = render_field_facts(dir05, dir06, dir02, fname,
                                    expr_id, scope_id,
                                    shared=field_shared)
        specs.append((expr_id, "field",
                      {"facts": ffacts, "text": ffacts,
                       "gap": False, "params": False,
                       "population": False},
                      item))

    reset_sightings()
    rows = []
    if no_llm:
        for node_id, grain, docket, floor in specs:
            rows.append({"node_id": node_id, "grain": grain,
                         "audience_text": floor,
                         "status": "floor", "gate_findings": [],
                         "rounds_used": 0, "model": None,
                         "basis_version": BASIS_VERSION})
    else:
        run = proposer or _propose_loop
        ck_path = out07 / "07_business_descriptions_checkpoint_output.json"
        done = dict(checkpoint_seed)   # the retake's siblings
        if ck_path.exists():
            done.update(json.loads(ck_path.read_text()))
        total = len(specs)
        for i, (node_id, grain, docket, floor) in \
                enumerate(specs, 1):
            if node_id in done:
                rows.append(done[node_id])
                continue
            t_run = time.monotonic()
            if node_id in retake_meanings:
                # the answered meaning rides the docket as an
                # annotation pair — the retake speaks the words
                docket = _inject_meanings(
                    docket, retake_meanings[node_id])
            if run is _propose_loop:
                text, status, findings, used = run(
                    grain, _docket_text(docket), docket,
                    registry,
                    verdicts=retake_verdicts.get(node_id))
                questions = last_questions()
            else:
                res = run(grain, _docket_text(docket), docket,
                          registry)
                text, status, findings, used = res[0], res[1], \
                    res[2], res[3]
                # an injected proposer MAY return a 5th element:
                # the shipped card's open questions (0.10.0)
                questions = (list(res[4]) if len(res) > 4
                             else [])
            _meter_stage("cards_field" if grain == "field"
                         else "cards_file_scope",
                         time.monotonic() - t_run)
            # D4: the row records the seat that actually wrote
            # the shipped (or last-attempted) text; an injected
            # proposer has no seat — None is the honest record.
            seat_used = _LAST_SEAT if run is _propose_loop \
                else None
            # D15: awaiting_human ships NO business text — the
            # floor never rides the business slot again
            if status == "awaiting_human":
                shown = ""
            elif status == "floor":
                shown = floor
            else:
                shown = text
            row = {"node_id": node_id, "grain": grain,
                   "audience_text": shown,
                   "status": status, "gate_findings": findings,
                   "rounds_used": used, "model": seat_used,
                   "basis_version": BASIS_VERSION}
            if status not in ("floor", "awaiting_human"):
                # 0.10.0: the shipped card's basis gaps ride
                # OUT as open questions — shown, logged, never
                # a block
                row["open_questions"] = questions
            if status in ("floor", "awaiting_human") and text:
                row["last_proposal"] = text  # her eye: what
                #                      wanted saying, and why not
            if status == "awaiting_human":
                # the V-code label's own digit must not win
                # (the "V-1: number 999" slip, caught by the
                # suite): strip the label, then read the number
                row["questions"] = [
                    {"number": m.group(1) if m else None,
                     "finding": f}
                    for f in findings
                    for m in [re.search(
                        r"\b(\d+(?:\.\d+)?)\b",
                        re.sub(r"^V-\d+:", "", f))]]
            rows.append(row)
            done[node_id] = row
            ck_path.write_text(json.dumps(done, indent=1))
            print(f"[{i}/{total}] {node_id.split('::')[-1]} -> "
                  f"{status} ({used})", flush=True)
        if ck_path.exists():
            ck_path.unlink()  # the sheet lands whole below

    rows.extend(carried)  # the skipped files' prior rows, verbatim

    # THE MERGE (0.10.0): the engine only ADDS question rows and
    # closes what resolved — a human-filled cell is never
    # touched, a known question never re-enters. A re-proposed
    # node whose old question dissolved closed by the SQL itself
    # (the inline comment — closed_by comment).
    def _askable(r):
        # shipped rows ask through open_questions; awaiting rows
        # (the wording class, and pre-0.10.0 carries) ask through
        # their numbered questions — ONE file holds them all
        if r.get("status") == "awaiting_human":
            return [q for q in r.get("questions", [])
                    if q.get("number")]
        return r.get("open_questions", [])

    spec_ids = {s[0] for s in specs} if not no_llm else set()
    open_now = {}
    findings_now = {}
    for r in rows:
        open_now[r["node_id"]] = {
            str(q.get("number")) for q in _askable(r)}
        findings_now[r["node_id"]] = (
            set(r.get("gate_findings", []))
            if r.get("status") == "gate_failed" else set())
    for a in answers:
        if a.get("status") != "open" \
                or (a.get("answer") or "").strip():
            continue
        if a["node_id"] not in spec_ids:
            continue
        if a.get("kind") == "wording":
            # the SQL changed and the finding dissolved
            if a.get("finding") not in \
                    findings_now.get(a["node_id"], set()):
                _close_answer(a, "comment")
        elif str(a["value"]) not in \
                open_now.get(a["node_id"], set()):
            _close_answer(a, "comment")
    known = {(a["node_id"], a.get("where") or "",
              str(a["value"])) for a in answers
             if a.get("kind") != "wording"}
    known_w = {(a["node_id"], a.get("finding") or "")
               for a in answers if a.get("kind") == "wording"}
    today = time.strftime("%Y-%m-%d")
    for r in rows:
        stem = r["node_id"].split("::")[1] \
            if "::" in r["node_id"] else r["node_id"]
        for q in _askable(r):
            key = (r["node_id"], q.get("where") or "",
                   str(q.get("number")))
            if key in known:
                continue
            known.add(key)
            answers.append(
                {"node_id": r["node_id"], "file": stem,
                 "kind": "value",
                 "where": q.get("where") or "",
                 "value": str(q.get("number")),
                 "finding": q.get("finding") or "",
                 "asked_at": today,
                 "answer": "", "answered_at": "",
                 "status": "open", "closed_by": ""})
        # 0.11.0 THE REGISTER: a shipped gate_failed card adds
        # one wording row per finding — never lost, never again
        # a block
        if r.get("status") == "gate_failed":
            for f in r.get("gate_findings", []):
                wkey = (r["node_id"], f)
                if wkey in known_w:
                    continue
                known_w.add(wkey)
                answers.append(
                    {"node_id": r["node_id"], "file": stem,
                     "kind": "wording", "where": "",
                     "value": "", "finding": f,
                     "asked_at": today,
                     "answer": "", "answered_at": "",
                     "status": "open", "closed_by": ""})
    if answers:
        _write_answers(answers_path, answers)

    (out07 / "07_business_descriptions_output.json").write_text(
        json.dumps(rows, indent=1))
    (out07 / "07_business_descriptions_code_sightings_output.json").write_text(
        json.dumps(code_sightings(), indent=1))

    by_file = {}
    for r in rows:
        key = r["node_id"].split("::")[1] if "::" in r["node_id"] \
            else r["node_id"]
        by_file.setdefault(key, []).append(r)
    for f in files:
        lines = [f"==== {f} ====", f"basis {BASIS_VERSION}", ""]
        for r in by_file.get(f, []):
            eff = effective(r, registry)
            lines.append(f"[{r['status']}] {r['grain']}: {eff}")
        (out07 / f"{f}.txt").write_text("\n".join(lines) + "\n")
    print(f"07 build: {len(rows)} rows over {len(files)} files; "
          f"sightings {len(code_sightings())}; "
          f"{'floor-only (no-llm)' if no_llm else 'live'}")
    return rows


# ---- the paid proposer loop (build-time only; never in tests)

# ==== TIERED SEATS — PSEUDO CODE (written BEFORE code; design
#      11_tiered_seats.md D1-D8 + contract, drafted 2026-10-09;
#      awaiting Sunny's approval) ==============================
#
# D1. THE TWO SEATS, pinned module constants (no env knob):
#       _MODEL_LARGE = "gpt-5.4"      (today's seat, unchanged)
#       _MODEL_SMALL = "gpt-5.4-mini"
#     _MODEL_NAME is RETIRED; every reader of it moves to the
#     seat map below. THE PRICE CARD beside them:
#       _PRICE_CARD = {seat: {"input_per_1m": USD,
#                             "output_per_1m": USD}}
#     values land on measurement day from OpenAI's published
#     pricing (per the placeholder law, the red test refuses a
#     placeholder card at ship).
#
# D2. SEAT BY GRAIN (Q1 ruled "use SMALL"):
#       _SEAT_BY_GRAIN = {"file": LARGE, "scope": LARGE,
#                         "term_card": SMALL, "field": SMALL}
#     (fact voices: SMALL, wired in voice_facts below.)
#
# D3. THE ESCALATION, inside the existing budget of 3:
#     in _propose_loop, the seat for a round is
#       seat = _SEAT_BY_GRAIN[grain]
#       if seat is SMALL and round_no == 3: seat = LARGE
#         (meter: escalations.fired += 1; .landed += 1 when
#          THAT round's gate comes back clean)
#     BASIS GAPS UNCHANGED: the "has no stored basis" return
#     already exits on round 1 — it never reaches round 3,
#     so it can never escalate (D15 stands whole).
#
# D4. THE SEAT RECORD: _openai_caller(prompt, seat) returns the
#     text AND tells the meter {seat, usage} (the API's own
#     usage counts, verbatim). _propose_loop returns the seat
#     of its LAST attempt alongside (text, status, findings,
#     rounds); build07 writes row["model"] = that seat —
#     the actual writer, never a constant.
#
# D6b. THE ACCOUNT REFUSAL (the Echo build): class
#     AccountRefusal(RuntimeError) raised by _openai_caller on
#     401 AuthenticationError, or 429 whose body says
#     insufficient_quota — message carries the provider text +
#     the named fix. EVERY round loop (here, voice_facts,
#     bt._propose) re-raises it BEFORE its catch-all
#     (`except AccountRefusal: raise`): the batch dies at the
#     FIRST refusal — no burned rounds, nothing recorded
#     described (describe() writes no ledger/delivery/sheet on
#     the way out; the checkpoint keeps the already-paid cards).
#     Timeouts and transient errors stay failed rounds, as today.
#
# D8. THE RUN METER (module-level, the scorecard's source):
#     reset_meter() zeroes it (describe() calls it at start,
#     beside reset_sightings); the meter accumulates, per run:
#       seats:   {seat: {calls, input_tokens, output_tokens}}
#       causes:  {finding-class: count} — class = the finding
#                text up to its first ":" ("V-1", "V-5",
#                "call failed", ...), counted at EVERY round
#       rounds:  {1: n, 2: n, 3: n} — the round a landed card
#                landed on
#       escalations: {fired, landed}
#       voices:  {proposed, blessed_reused, failed}
#     meter() returns a plain dict; sqldesc_cli builds the
#     scorecard from it + the sheet rows + its own clock.
#
# VOICES (D2/D3): voice_facts tries SMALL once; a voice the
#     voice-gate refuses gets exactly ONE LARGE retry; still
#     refused -> the recorded miss (machine fact ships), as
#     today; store entry "model" = the seat of the kept text.
# ================================================================

_MODEL_LARGE = "gpt-5.4"       # today's seat, unchanged (D1)
_MODEL_SMALL = "gpt-5.4-mini"  # the small seat (D1)
_SEAT_BY_GRAIN = {"file": _MODEL_LARGE, "scope": _MODEL_LARGE,
                  "term_card": _MODEL_SMALL, "field": _MODEL_SMALL}
_PRICE_CARD = {
    # PINNED 2026-10-09 (measurement day, the 11 contract) from
    # developers.openai.com/api/docs/pricing, Standard tier —
    # frozen until a re-pin; the usage dashboard verifies.
    _MODEL_LARGE: {"input_per_1m": 2.50, "output_per_1m": 15.00},
    _MODEL_SMALL: {"input_per_1m": 0.75, "output_per_1m": 4.50},
}
REPAIR_BUDGET = 3
CALL_TIMEOUT_S = 120  # harness law 2026-10-03: a wedged socket
#                       can never hang the build


class AccountRefusal(RuntimeError):
    """D6b: the seat says the ACCOUNT cannot pay (bad key, no
    credits) — the batch stops at the first refusal; nothing is
    recorded described."""


def _check_account_refusal(exc):
    """Raise AccountRefusal for account-level errors ONLY; a
    plain rate limit or timeout stays a failed round."""
    name = type(exc).__name__
    msg = str(exc)
    if name == "AuthenticationError":
        raise AccountRefusal(
            "the seat refused the account (bad key): " + msg[:300]
            + " — re-run the key cell with the real key, then "
            "re-run this cell; nothing was recorded described"
        ) from exc
    if name == "RateLimitError" and "insufficient_quota" in msg:
        raise AccountRefusal(
            "the seat refused the account (no credits remaining): "
            + msg[:300] + " — add credits on the billing page, "
            "then re-run this cell; nothing was recorded described"
        ) from exc
    return None


# ---- the run meter (D8): the scorecard's one source, counted
#      at call time from the rows and the clock, never estimated.

_METER = {}


def reset_meter():
    _METER.clear()
    _METER.update({
        "seats": {},
        "causes": {},
        "rounds": {"1": 0, "2": 0, "3": 0},
        "escalations": {"fired": 0, "landed": 0},
        "voices": {"proposed": 0, "blessed_reused": 0,
                   "failed": 0},
        "closures": {"comment": 0, "answer": 0, "dictionary": 0,
                     "show": 0, "omit": 0, "bless": 0,
                     "accept": 0},
        "stage_s": {}})


reset_meter()


def meter():
    return json.loads(json.dumps(_METER))  # a copy, always


def _meter_usage(seat, usage):
    s = _METER["seats"].setdefault(
        seat, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
    s["calls"] += 1
    if usage is not None:
        s["input_tokens"] += getattr(usage, "prompt_tokens", 0) or 0
        s["output_tokens"] += (getattr(usage, "completion_tokens",
                                       0) or 0)


def _meter_causes(findings):
    for f in findings:
        cls = str(f).split(":", 1)[0].strip()
        _METER["causes"][cls] = _METER["causes"].get(cls, 0) + 1


def _meter_round(n):
    _METER["rounds"][str(n)] = _METER["rounds"].get(str(n), 0) + 1


def _meter_stage(name, seconds):
    _METER["stage_s"][name] = (_METER["stage_s"].get(name, 0.0)
                               + seconds)


def _load_key():
    """The seat's key, runtime-offered (the 0.5.1 law: the
    ENVIRONMENT WINS FIRST — a notebook that set the secret is
    the offer; only then the repo's .env reader. Fixed
    2026-10-05 at the Fabric rehearsal: the 0.3.0 chat wheel
    also ships build_abstract_names, so the import path is not
    wheel-safe — ImportError caught too)."""
    import os
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        from build_abstract_names import load_openai_key
        return load_openai_key()
    except ImportError:
        raise RuntimeError("no OPENAI_API_KEY offered at runtime")


def _openai_caller(prompt, seat=None):
    from openai import OpenAI
    # Accept-Encoding identity (rehearsal find #6, 2026-10-06):
    # Fabric cluster images carry a stale brotli whose process()
    # rejects httpx2's new kwarg — every compressed response
    # died in the decoder (TypeError). Uncompressed responses
    # skip the decoder entirely; works on any cluster.
    seat = seat or _MODEL_LARGE
    client = OpenAI(api_key=_load_key(),
                    timeout=CALL_TIMEOUT_S, max_retries=2,
                    default_headers={
                        "Accept-Encoding": "identity"})
    try:
        r = client.chat.completions.create(
            model=seat,
            messages=[{"role": "user", "content": prompt}])
    except Exception as exc:
        _check_account_refusal(exc)  # D6b: 401/no-credits = stop
        raise
    _meter_usage(seat, getattr(r, "usage", None))
    return r.choices[0].message.content.strip()


def _call_with_seat(caller, prompt, seat):
    """Callers may take (prompt) or (prompt, seat): the standing
    suite's one-arg injected callers stay valid (test-locked)."""
    import inspect
    try:
        takes_seat = len(inspect.signature(caller).parameters) >= 2
    except (TypeError, ValueError):
        takes_seat = False
    return caller(prompt, seat) if takes_seat else caller(prompt)


# the seat of _propose_loop's LAST attempt — build07 reads it
# right after the loop returns to stamp the row's "model" (D4);
# single-threaded by the run law, like _SIGHTINGS.
_LAST_SEAT = None


_LAST_QUESTIONS = []


def last_questions():
    """0.10.0 (ruled 2026-10-10): the open questions of the most
    recent _propose_loop card — basis gaps that SHIPPED with the
    number shown plainly. build07 mirrors them onto the row and
    into the answers file."""
    return [dict(q) for q in _LAST_QUESTIONS]


def _questions_from(basis_findings):
    """A question per basis finding: the number (the V-label's
    own digit never wins — the 'V-1: number 999' slip), the
    where (table.column when the sighting knows it; None is the
    honest record until it does), the finding verbatim."""
    out = []
    for f in basis_findings:
        m = re.search(r"\b(\d+(?:\.\d+)?)\b",
                      re.sub(r"^V-\d+:", "", f))
        out.append({"number": m.group(1) if m else None,
                    "where": None, "finding": f})
    return out


def _propose_loop(grain, docket_text, docket, registry,
                  caller=None, verdicts=None):
    """D15 AS AMENDED 2026-10-10 (0.10.0, her ruling: "don't
    block the description"): a BASIS GAP (a number with no
    annotation and no grounding) is still never repairable by
    wording and never escalates — but it no longer blocks: the
    card SHIPS with the number spoken plainly, the gap rides out
    as an open QUESTION (last_questions). Only the WORDING class
    repairs, and an exhausted budget lands awaiting_human —
    never a technical text in the business slot. A card that
    ASSERTS an unstored meaning still fails: show-plainly never
    licenses invention (the non-basis V-checks are untouched).
    Her verdicts steer the prompt and the gate.
    TIERED (11 D2/D3): SMALL grains run rounds 1-2 on the small
    seat and round 3 on the large one."""
    global _LAST_SEAT, _LAST_QUESTIONS
    _LAST_QUESTIONS = []
    caller = caller or _openai_caller
    base = _SEAT_BY_GRAIN.get(grain, _MODEL_LARGE)
    findings = []
    if verdicts:
        findings = [
            (f"her ruling: the number {n} may be shown"
             if v == "show" else
             f"her ruling: the number {n} must not appear — "
             "speak without it")
            for n, v in sorted(verdicts.items())]
    text = ""
    basis = []
    for round_no in range(1, REPAIR_BUDGET + 1):
        seat = base
        if base == _MODEL_SMALL and round_no == REPAIR_BUDGET:
            seat = _MODEL_LARGE  # the escalation (D3)
            _METER["escalations"]["fired"] += 1
        _LAST_SEAT = seat
        prompt = build_prompt(grain, docket_text, findings)
        try:
            text = _call_with_seat(caller, prompt, seat)
        except AccountRefusal:
            raise  # D6b: the batch stops, never a failed round
        except Exception as exc:  # noqa: BLE001 — ANY call
            # failure is a failed round, never a dead build
            # (the 2026-10-03 APITimeoutError crash find)
            findings = [f"call failed: {type(exc).__name__}: "
                        f"{str(exc)[:200]}"]
            _meter_causes(findings)
            continue
        findings = gate(text, docket, grain, registry,
                        verdicts=verdicts)
        basis = [f for f in findings
                 if "has no stored basis" in f]
        findings = [f for f in findings if f not in basis]
        if not findings:
            _meter_round(round_no)
            if seat != base:
                _METER["escalations"]["landed"] += 1
            if basis:
                _meter_causes(basis)  # the ask stays countable
                _LAST_QUESTIONS = _questions_from(basis)
            return text, "gate_passed", [], round_no
        # only the wording findings feed the repair prompt —
        # a basis gap cannot be reworded into a basis
        _meter_causes(findings + basis)
    if text:
        # 0.11.0 (uniform ship, her ruling): the exhausted card
        # SHIPS its final text — the wording findings stay on
        # the row as the register, the basis gaps ride out as
        # open questions. Only an EMPTY text still waits.
        _LAST_QUESTIONS = _questions_from(basis)
        return text, "gate_failed", findings, REPAIR_BUDGET
    return text, "awaiting_human", findings + basis, REPAIR_BUDGET


# ==== FIELD DOCKET v2 — PSEUDO CODE (written before code;
#      ruled 2026-10-04, the single-file deep track) ===============
#
# render_field_facts(dir05, dir06, dir02, fname, expr_id,
#                    scope_id, shared) -> facts text
#   FIELD line  : the output's NAMED defining phrase — the 06
#                 payload item rendered through the name-overlay
#                 voice (td._payload_item on a _NamedVoice), so
#                 lineage (built in / read through / origins)
#                 rides in, named.
#   FILTER lines: the owning file's SHAPED nine (render_facts,
#                 computed once per file and shared across its
#                 fields) — a field sentence inherits the
#                 population truth.
#   V-1 is scoped to this facts text; no CONTEXT for fields
#   (small dockets); must-say flags off (file-grain law only).
#   The field FLOOR stays the plain 06 item verbatim.
# ====================================================================
# ==== THE NAME LADDER — PSEUDO CODE (written BEFORE code this
#      time; ruled 2026-10-04, the naming law in
#      Design_Proprietary_Term_Assets.md) ===========================
#
# load_names(dir03, registry) -> {(kind, OBJECT_NAME): short}
#   ONE source: 03_chat_abstract_names.json (the estate's naming
#   asset; no 07 store exists, by ruling). Per row:
#     sunny_synonyms[0] if present          (her hand)
#     else a registry blessed_name for the object
#     else synonyms[0]                      (the ruled short name)
#   Keys: ('table', 'CLARITY_ADT') and
#         ('column', 'CLARITY_ADT.EVENT_TYPE_C').
#
# render_facts gains the overlay:
#   - FILTER/ATTACHMENT lines are RE-RENDERED through the
#     importable 06 machinery (td._Voice + _voice_predicate)
#     with words overridden by the ladder: subject words for
#     (T,C) = names[('column', 'T.C')] when present, else the
#     R5 description words. The 06 floor itself is untouched —
#     the overlay exists only in 07's FACTS.
#   - SOURCES lines read "short name (TABLE_NAME) — description".
#   fact keys keep the node+hash law, so renamed facts
#   re-propose their voices once and settle.
#
# the voice prompt is corrected the same slice: codes and VALUES
#   stay exact; CONCEPTS may be renamed plainly (the earlier
#   prompt made the voicer preserve awkward subject words as if
#   they were names).
# ====================================================================
# ==== DOCKET v2 + THE FACT-VOICE LAYER — PSEUDO CODE ================
# (RETROACTIVE, added 2026-10-04 at Sunny's catch — this slice
# was built contract->red->code without the pseudo step; the
# process law stands, the miss is recorded, the design is
# documented here as the law requires.)
#
# render_facts(dir05, dir06, dir02, fname) -> (text, items)
#   Assembly ONLY from resolver-bound rows (the EMH law):
#   SOURCES   = the 02 table descriptions of tables the file's
#               resolves edges actually bind (never grep).
#   FILTERS   = the 06 predicate sentences whose node sits under
#               a WHERE/HAVING structure or carries on_class
#               population_filter — each line already carries its
#               bound meaning ('Census' (6), the department
#               names) because 06 rendered it from binds.
#   ATTACHMENTS = join_pair + lookup_shaping predicate sentences
#               (speak as additions, never membership).
#   PARAMETERS / OUTPUTS = the file floor's own lines (verbatim).
#   items     = [(fact_key, machine_fact)] for the voice layer;
#               fact_key = node_id + sha1(fact)[:8] so a CHANGED
#               fact re-proposes and an unchanged one never does
#               (delta-by-name).
#
# voice_facts(items, store_path, registry, voicer) -> {key: text}
#   ladder per fact: BLESSED (registry row w/ fact_key)
#     > stored gated PROPOSED voice
#     > the machine fact itself (when no voice or the voice
#       failed its gate).
#   a NEW fact -> one scoped call ("rewrite this one condition
#   plainly; keep every code/value/name EXACTLY") -> the voice
#   gate (V-1/V-2/V-3 against THE FACT ALONE: a voice may carry
#   only its own fact's values — the lying-voicer test) ->
#   stored as status proposed|failed with findings. Machine
#   writes PROPOSED only; blessing stays her hand.
#   A failed call = a recorded miss, never a dead build.
#
# docket_v2_for_file(...) -> (docket, items)
#   docket.facts   = the FACTS text, each voiced fact showing
#                    "      plain: <voice>" under its machine
#                    line (values stay visible for V-1).
#   docket.text    = facts + "CONTEXT (grounds nothing)" + the
#                    raw SQL (interpretation fuel only).
#   gate reference = _gate_reference() -> docket.facts ALONE.
#   must-say flags ride from the file floor as before.
#
# build07 wiring: FILE grain only this slice; <file>.facts.txt
#   lands tracked (proposer grounding + gate reference + her
#   audit, one artifact); no_llm skips voicing, stays
#   deterministic.
# ====================================================================

import hashlib  # noqa: E402

DIR01_DEFAULT = str(Path(__file__).resolve().parents[1]
                    / "AIVIA_01_Data" / "01_subject_sql_files")


def _dir01(offered=None):
    """The corpus home: explicit offer > AI_SQL_DIR environment
    offer (deliver sets it — the runner always knows its sql
    folder) > the repo default. The rehearsal's second
    repo-relative crash, fixed 2026-10-05; sweep says this was
    the last one."""
    import os
    return offered or os.environ.get("AI_SQL_DIR") \
        or DIR01_DEFAULT


def _gate_reference(docket):
    """V-1 scoped (2026-10-04): FACTS alone grounds values."""
    if isinstance(docket, dict) and docket.get("facts"):
        return docket["facts"]
    return _docket_text(docket)


def render_facts(dir05, dir06, dir02, fname, dir03=None,
                 registry=None):
    """The FACTS block — every line printed from a resolver-bound
    row; assembly is never grep, never hand. Names ride the
    ladder (the 03 asset; Design_Proprietary_Term_Assets.md).
    -> (text, items) where items = [(fact_key, machine_fact)]."""
    dir05, dir06 = Path(dir05), Path(dir06)
    names = load_names(_dir03(dir03),
                       registry or {"names": []})
    ng, nvoice, nsql = _facts_renderer(dir05, dir02, names)
    six = json.loads((dir06 / "06_technical_descriptions_output.json")
                     .read_text())
    file_s = next(r["sentence"] for r in six
                  if r["node_id"] == f"file::{fname}")
    preds = [r for r in six if r["grain"] == "predicate"
             and r["node_id"].split("::")[1] == fname]
    pred_rows = {p["node_id"]: p for p in
                 td._read(dir05 / "05_semantic_graph_predicate_output.json")}

    scopes_sheet = td._read(dir05 / "05_semantic_graph_scope_output.json")
    filters = _shape_filter_lines(ng, nvoice, nsql, scopes_sheet,
                                  fname)
    sub_paths = tuple(sc["node_id"] for sc in scopes_sheet
                      if sc["scope_kind"] == "subquery")
    attachments = []
    for r in sorted(preds, key=lambda x: x["node_id"]):
        if r["node_id"].startswith(sub_paths):
            continue
        meta = pred_rows.get(r["node_id"], {})
        if meta.get("on_class") in ("join_pair",
                                    "lookup_shaping"):
            sent = _named_fact(ng, nvoice, nsql, r["node_id"]) \
                or r["sentence"]
            attachments.append((r["node_id"], sent))
        elif meta.get("on_class") == "population_filter":
            # THE VIEW-SHAPE FIND (D15 night, 2026-10-08): a
            # chained-JOIN view carries its whole population in
            # ON clauses — the docket honors the 05 layer's
            # CLASS, never the housing; without this the card
            # had zero filter lines to ground on.
            sent = _named_fact(ng, nvoice, nsql, r["node_id"]) \
                or r["sentence"]
            filters.append((r["node_id"], sent))

    params_line = next((ln for ln in file_s.splitlines()
                        if ln.startswith("Parameters shaping")),
                       "Parameters: none bound to filters")
    presents = next((ln for ln in file_s.splitlines()
                     if ln.startswith("Presents:")),
                    "Presents: (none)")

    items = []
    for nid, fact in filters + attachments:
        key = nid + ":" + hashlib.sha1(
            fact.encode()).hexdigest()[:8]
        items.append((key, fact))

    lines = [f"FACTS — {fname}", "", "SOURCES:"]
    for ln in _source_lines(dir05, dir02, fname):
        body = ln[len("Sources: "):]
        tname = body.split(" — ")[0].strip()
        short = names.get(("table", tname))
        lines.append("  " + (f"{short} ({tname}) — "
                             + body.split(" — ", 1)[1]
                             if short and " — " in body
                             else body))
    lines += ["", "WHO-IS-IN FILTERS (each line is one parsed, "
              "bound condition):"]
    lines += [f"  - {s}" for _, s in filters]
    lines += ["", "ATTACHMENTS (add information to rows; never "
              "restrict membership):"]
    lines += [f"  - {s}" for _, s in attachments]
    lines += ["", params_line, "", presents]
    return "\n".join(lines), items


def _voice_gate(voice, fact):
    """A voice may carry only its own fact's values; same
    register laws as everything else."""
    probe = {"facts": fact, "text": fact}
    f = []
    for x in gate(voice, probe, "scope"):
        if x.startswith(("V-1", "V-2", "V-3")):
            f.append(x)
    return f


_VOICE_PROMPT = (
    "Rewrite this one data condition in plain business English "
    "— one short sentence, natural words; keep every code and "
    "value EXACTLY as written; concepts may be renamed plainly; "
    "no SQL vocabulary; the plain, concrete voice of an "
    "experienced clinician, never a systems document. A "
    "condition that an identifier is "
    "recorded means the record is LINKED to that entity — say "
    "the linkage (the record is linked to a patient), not the "
    "field mechanics; recordedness of an ordinary data column "
    "stays 'has a recorded <x>'.\n")


def _openai_voicer(fact, seat=None):
    return _openai_caller(_VOICE_PROMPT + fact,
                          seat or _MODEL_SMALL)


def _voicer_takes_seat(voicer):
    import inspect
    try:
        return len(inspect.signature(voicer).parameters) >= 2
    except (TypeError, ValueError):
        return False


def voice_facts(items, store_path, registry, voicer=None):
    """One scoped call per NEW fact; stored; blessed > gated
    proposed > the machine fact. Machine writes PROPOSED only.
    TIERED (11 D2/D3): the SMALL seat voices first; a voice the
    gate refuses gets exactly ONE LARGE retry, then the recorded
    miss. One-arg voicers (the standing suite) keep the old
    single-attempt contract."""
    store_path = Path(store_path)
    store = (json.loads(store_path.read_text())
             if store_path.exists() else {})
    blessed = {s.get("fact_key"): s.get("blessed_text")
               for s in registry.get("sentences", [])
               if s.get("fact_key") and s.get("blessed_text")}
    voicer = voicer or _openai_voicer
    tiered = _voicer_takes_seat(voicer)
    out = {}
    changed = False
    for key, fact in items:
        if key in blessed:
            _METER["voices"]["blessed_reused"] += 1
            out[key] = blessed[key]
            continue
        if key not in store:
            seat = _MODEL_SMALL if tiered else None
            try:
                voice = (voicer(fact, _MODEL_SMALL) if tiered
                         else voicer(fact))
            except AccountRefusal:
                raise  # D6b: the batch stops at the first refusal
            except Exception as exc:  # noqa: BLE001 — a failed
                voice = None          # voice is a recorded miss,
                findings = [f"call failed: {type(exc).__name__}: "
                        f"{str(exc)[:200]}"]
            else:
                findings = _voice_gate(voice, fact)
            if findings and tiered:  # ONE LARGE retry (D3)
                seat = _MODEL_LARGE
                try:
                    retry = voicer(fact, _MODEL_LARGE)
                except AccountRefusal:
                    raise
                except Exception as exc:  # noqa: BLE001
                    retry = None
                    findings = [f"call failed: "
                                f"{type(exc).__name__}: "
                                f"{str(exc)[:200]}"]
                else:
                    retry_findings = _voice_gate(retry, fact)
                    if not retry_findings:
                        voice, findings = retry, []
            store[key] = {"machine_fact": fact,
                          "voice": None if findings else voice,
                          "status": ("failed" if findings
                                     else "proposed"),
                          "findings": findings,
                          "model": seat,
                          "basis_version": BASIS_VERSION}
            _METER["voices"]["failed" if findings
                             else "proposed"] += 1
            changed = True
        entry = store[key]
        out[key] = entry["voice"] or fact
    if changed:
        store_path.write_text(json.dumps(store, indent=1))
    return out


def docket_v2_for_file(dir05, dir06, dir02, fname, voices=None,
                       dir01=None):
    """FACTS (+voices beside their facts) and CONTEXT (raw SQL),
    with the must-say flags. The gate reads FACTS alone.
    D15 (2026-10-08): the file's own header Description: rides
    the FACTS first — the card's first-choice wording, her
    ruling; read at build time, stored nowhere."""
    facts, items = render_facts(dir05, dir06, dir02, fname)
    head = td.header_description(_dir01(dir01), fname)
    if head:
        facts = ("- THE FILE'S OWN WORDS (its header): "
                 + head + "\n" + facts)
    if voices:
        lines = []
        bykey = {k: v for k, v in voices.items()}
        fact_to_voice = {f: bykey.get(k) for k, f in items}
        for ln in facts.splitlines():
            lines.append(ln)
            v = fact_to_voice.get(ln.strip().lstrip("- ").strip())
            core = ln.strip()[2:] if ln.strip().startswith("- ") \
                else None
            v = fact_to_voice.get(core)
            if v and v != core:
                lines.append(f"      plain: {v}")
        facts = "\n".join(lines)
    sql_path = Path(_dir01(dir01)) / f"{fname}.sql"
    if not sql_path.exists():
        sql_path = Path(_dir01(dir01)) / fname
    context = (sql_path.read_text(encoding="utf-8-sig")
               if sql_path.exists() else "")
    base = docket_for_file(dir05, dir06, dir02, fname)
    return {"facts": facts,
            "text": facts + "\n\nCONTEXT (interpretation only — "
            "grounds nothing):\n" + context,
            "gap": base["gap"], "params": base["params"],
            "population": base["population"]}, items


# bd.answer() RETIRED 2026-10-10 (her word: "one file, all
# answers in it, retire the ANSWER cell") — every human answer
# lands in the answers CSV (ANSWERS_NAME above); the next
# describe run picks it up.


# ==== THE NAME LADDER (code; pseudo above) ==========================

DIR03_DEFAULT = str(Path(__file__).resolve().parents[1]
                    / "AIVIA_01_Data" / "03_chat_bot")


def _dir03(offered=None):
    """The naming asset's home: an explicit offer first, then
    the AI_NAMES_DIR environment offer (the runtime-offered
    precedent — the wheel ships no asset, the runner points at
    one), then the repo default. Added 2026-10-05 at the Fabric
    rehearsal crash."""
    import os
    return offered or os.environ.get("AI_NAMES_DIR") \
        or DIR03_DEFAULT


def load_names(dir03, registry):
    """ONE naming asset (the 03 abstracts): sunny_synonyms[0] >
    a registry blessed_name > synonyms[0]. ABSENCE IS HONEST
    (2026-10-05): the asset is one rung of the name ladder,
    never a requirement — no file means blessed-names-only and
    the deterministic fallback words stand."""
    try:
        rows = json.loads((Path(dir03) /
                           "03_chat_abstract_names.json")
                          .read_text())
    except FileNotFoundError:
        rows = []
    blessed = {str(n.get("object_name")): n.get("blessed_name")
               for n in registry.get("names", [])
               if n.get("blessed_name")}
    names = {}
    for r in rows:
        kind, oname = r.get("object_kind"), r.get("object_name")
        if kind not in ("table", "column") or not oname:
            continue

        def _lst(v):
            if isinstance(v, list):
                return v
            try:
                out = json.loads(str(v).replace("'", '"'))
                return out if isinstance(out, list) else []
            except Exception:  # noqa: BLE001 — a malformed row
                return []      # never kills the ladder

        sunny = _lst(r.get("sunny_synonyms"))
        syns = _lst(r.get("synonyms"))
        short = (sunny[0] if sunny
                 else blessed.get(oname)
                 or (syns[0] if syns else None))
        if short:
            names[(kind, oname)] = short
    return names


class _NamedVoice(td._Voice):
    """The 07 voice seat (ruled 2026-10-04, her 'pat id' find):
    recordedness name-words consult the name ladder first; the
    06 floor keeps its own R5.c law untouched."""

    def name_words(self, expr_id):
        self.refs.append(expr_id)
        for r in self.g["resolves"].get(expr_id, []):
            if r["to_kind"] == "column":
                tu, cu = r["to_id"].split(".", 1)
                hit = self.words.get((tu.upper(), cu.upper()))
                if hit:
                    return hit[0]
        return super().name_words(expr_id)


def _facts_renderer(dir05, dir02, names, dir01=None):
    """A 07-side render seat: the 06 machinery with the name
    overlay — the 06 floor itself stays untouched."""
    dir05 = Path(dir05)
    g = td._load_graph(dir05)
    words, values = td._load_words(Path(dir02))
    for (kind, oname), short in names.items():
        if kind == "column" and "." in oname:
            t, c = oname.split(".", 1)
            words[(t.upper(), c.upper())] = (short, False)
    voice = _NamedVoice(g, words, values)
    sql_lines = td._load_sql(Path(_dir01(dir01)))
    return g, voice, sql_lines



def _exists_inline(g, voice, sql_lines, pred_id, sub_scope):
    """The shape law: an EXISTS condition inlines its
    sub-selection's own condition (the L03 floor-form deferral
    closes)."""
    src = "another selection"
    if sub_scope:
        for fid in td._scope_structures(g, sub_scope, "FROM"):
            for k in g["children"].get(fid, []):
                e = g["exprs"].get(k, {})
                if e.get("expression_kind") == "table_ref":
                    src = e.get("raw_text") or src
        for wid in td._scope_structures(g, sub_scope, "WHERE"):
            leaves = []
            phrase = td._compose(wid, g, voice, sql_lines,
                                 leaves, True)
            if phrase:
                return (f"A matching entry exists in {src} "
                        f"where {td._lower_first(phrase)}.")
    return f"A matching entry exists in {src}."


def _shape_filter_lines(g, voice, sql_lines, scopes, fname):
    """ONE line per TOP-LEVEL condition (her 13-vs-9 ruling):
    leaves speak; OR-groups compose on one line; EXISTS inlines;
    sub-selection leaves never enter."""
    subs = {}
    for sc in scopes:
        if sc["scope_kind"] == "subquery" \
                and sc["node_id"].split("::")[1] == fname:
            subs.setdefault(sc["owning_statement"],
                            []).append(sc["node_id"])
    for v in subs.values():
        v.sort()
    mains = [sc for sc in scopes
             if sc["node_id"].split("::")[1] == fname
             and sc["scope_kind"] != "subquery"]
    lines = []

    def emit(node_id, stmt_id):
        kind = g["struct_kind"].get(node_id)
        pred = g["pred_by_id"].get(node_id)
        if pred is not None:
            if pred["predicate_kind"] == "EXISTS_SELECTION":
                q = subs.get(stmt_id, [])
                sub = q.pop(0) if q else None
                lines.append((node_id,
                              _exists_inline(g, voice, sql_lines,
                                             node_id, sub)))
            else:
                voice.refs = []
                sent = td._leaf_sentence(pred, voice, g,
                                         sql_lines)
                if sent:
                    lines.append((node_id, sent))
            return
        if kind == "AND":
            for k in g["children"].get(node_id, []):
                emit(k, stmt_id)
            return
        if kind in ("OR", "NOT"):
            leaves = []
            phrase = td._compose(node_id, g, voice, sql_lines,
                                 leaves, True)
            if phrase:
                lines.append((node_id,
                              phrase[0].upper() + phrase[1:]
                              + "."))

    for sc in mains:
        stmt_id = sc.get("owning_statement")
        for wid in [k for k in g["children"].get(sc["node_id"],
                                                 [])
                    if g["struct_kind"].get(k) in ("WHERE",
                                                   "HAVING")]:
            for k in g["children"].get(wid, []):
                emit(k, stmt_id)
    return lines


def _named_fact(g, voice, sql_lines, node_id):
    pred = g["pred_by_id"].get(node_id)
    if pred is None:
        return None
    voice.refs = []
    return td._leaf_sentence(pred, voice, g, sql_lines)


# ==== FIELD DOCKET v2 (code; pseudo above) ==========================

_FIELD_SHARED = {}


def render_field_facts(dir05, dir06, dir02, fname, expr_id,
                       scope_id, shared=None):
    """A field's FACTS: its named defining phrase + the owning
    file's shaped filters (computed once per file)."""
    key = (str(dir05), fname)
    cache = shared if shared is not None else _FIELD_SHARED
    if key not in cache:
        facts_text, _ = render_facts(dir05, dir06, dir02, fname)
        names = load_names(_dir03(), {"names": []})
        g, voice, sql = _facts_renderer(dir05, dir02, names)
        filt = []
        on = False
        for ln in facts_text.splitlines():
            if ln.startswith("WHO-IS-IN"):
                on = True
                continue
            if ln.startswith("ATTACHMENTS"):
                break
            if on and ln.strip().startswith("- "):
                filt.append(ln.strip())
        cache[key] = (g, voice, sql, filt)
    g, voice, sql, filt = cache[key]
    voice.refs = []
    item = td._payload_item(voice, expr_id, scope_id)
    lines = [f"FIELD: {item}", "",
             "THE OWNING SELECTION'S FILTERS (every row of this "
             "field already passed these):"]
    lines += ["  " + ln for ln in filt]
    return "\n".join(lines)
