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
#     RECORDED to 07_code_sightings.json (table.column + code +
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
#   suite's path; zero cost); writes 07_business_sheet.json, the
#   per-file texts (status marks per line), 07_code_sightings
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

import json
import re
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


def gate(audience_text, docket, grain, registry=None):
    """GATE v2 (contract law, 2026-10-03): the estate boundary —
    customer-specific facts must trace to the docket; general
    domain knowledge is FREE. No whitelist, no word budgets. No
    model anywhere in here."""
    findings = []
    dtext = _gate_reference(docket)
    toks = _tokens(audience_text)

    # V-1 grounded values: quoted literals and numbers
    # a quoted VALUE is '-delimited with non-letter boundaries —
    # apostrophes inside words (Who's, patient's) are not quotes
    qpat = r"(?<![A-Za-z])'[^']*'(?![A-Za-z])"
    for q in re.findall(qpat, audience_text):
        if q not in dtext:
            findings.append(f"V-1: quoted {q} not in the docket")
    unquoted = re.sub(qpat, " ", audience_text)
    for n in set(re.findall(r"\b\d+\b", unquoted)):
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
    for r in td._read(Path(dir05) / "05_resolves_edges.json"):
        if r["to_kind"] == "table" \
                and r["from_id"].split("::")[1] == fname:
            tables.add(r["to_id"].upper())
    return [f"Sources: {t} — {descs[t]}"
            for t in sorted(tables) if t in descs]


def docket_for_file(dir05, dir06, dir02, fname):
    rows = json.loads((Path(dir06) /
                       "06_description_sheet.json").read_text())
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
    scopes = td._read(dir05 / "05_scope_sheet.json")
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


def build07(dir05, dir06, out07, dir02, no_llm=False,
            proposer=None, only_file=None):
    """The build command's door. no_llm=True renders floor-only
    rows deterministically (the suite's path, zero cost). The
    live path (harness laws, amended 2026-10-03): explicit call
    timeout, CHECKPOINT-PER-NODE with resume (completed nodes
    are never re-paid), one progress line per node."""
    dir05, dir06 = Path(dir05), Path(dir06)
    out07, dir02 = Path(out07), Path(dir02)
    six = json.loads((dir06 / "06_description_sheet.json")
                     .read_text())
    files = sorted({r["node_id"].split("::")[1] for r in six
                    if r["grain"] == "file"})
    if only_file:
        files = [f for f in files if f == only_file]
        six = [r for r in six
               if r["node_id"].split("::")[1] == only_file]
    reg_path = out07 / "07_blessing_registry.json"
    registry = (json.loads(reg_path.read_text())
                if reg_path.exists()
                else {"names": [], "sentences": []})

    # the ordered node specs: (node_id, grain, docket, floor)
    # FILE grain rides DOCKET v2 (FACTS/CONTEXT + fact voices,
    # ruled 2026-10-04); voices are skipped under no_llm.
    specs = []
    for f in files:
        if no_llm:
            docket, _items = docket_v2_for_file(
                dir05, dir06, dir02, f)
        else:
            _, items = render_facts(dir05, dir06, dir02, f)
            voices = voice_facts(
                items, out07 / "07_fact_voices.json", registry)
            docket, _items = docket_v2_for_file(
                dir05, dir06, dir02, f, voices=voices)
        (out07 / f"{f}.facts.txt").write_text(
            docket["facts"] + "\n")
        floor = next(r["sentence"] for r in six
                     if r["node_id"] == f"file::{f}")
        specs.append((f"file::{f}", "file", docket, floor))
    src_by_file = {f: "\n".join(_source_lines(dir05, dir02, f))
                   for f in files}
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
        ck_path = out07 / "07_live_checkpoint.json"
        done = (json.loads(ck_path.read_text())
                if ck_path.exists() else {})
        total = len(specs)
        for i, (node_id, grain, docket, floor) in \
                enumerate(specs, 1):
            if node_id in done:
                rows.append(done[node_id])
                continue
            text, status, findings, used = run(
                grain, _docket_text(docket), docket, registry)
            row = {"node_id": node_id, "grain": grain,
                   "audience_text": text if status != "floor"
                   else floor,
                   "status": status, "gate_findings": findings,
                   "rounds_used": used, "model": _MODEL_NAME,
                   "basis_version": BASIS_VERSION}
            if status == "floor" and text:
                row["last_proposal"] = text  # her eye: what
                #                      wanted saying, and why not
            rows.append(row)
            done[node_id] = row
            ck_path.write_text(json.dumps(done, indent=1))
            print(f"[{i}/{total}] {node_id.split('::')[-1]} -> "
                  f"{status} ({used})", flush=True)
        if ck_path.exists():
            ck_path.unlink()  # the sheet lands whole below

    (out07 / "07_business_sheet.json").write_text(
        json.dumps(rows, indent=1))
    (out07 / "07_code_sightings.json").write_text(
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

_MODEL_NAME = "gpt-5.4"  # her ruling: the large seat
REPAIR_BUDGET = 3
CALL_TIMEOUT_S = 120  # harness law 2026-10-03: a wedged socket
#                       can never hang the build


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


def _openai_caller(prompt):
    from openai import OpenAI
    client = OpenAI(api_key=_load_key(),
                    timeout=CALL_TIMEOUT_S, max_retries=2)
    r = client.chat.completions.create(
        model=_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content.strip()


def _propose_loop(grain, docket_text, docket, registry,
                  caller=None):
    caller = caller or _openai_caller
    findings = []
    text = ""
    for round_no in range(1, REPAIR_BUDGET + 1):
        prompt = build_prompt(grain, docket_text, findings)
        try:
            text = caller(prompt)
        except Exception as exc:  # noqa: BLE001 — ANY call
            # failure is a failed round, never a dead build
            # (the 2026-10-03 APITimeoutError crash find)
            findings = [f"call failed: {type(exc).__name__}"]
            continue
        findings = gate(text, docket, grain, registry)
        if not findings:
            return text, "gate_passed", [], round_no
    return text, "floor", findings, REPAIR_BUDGET


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
    six = json.loads((dir06 / "06_description_sheet.json")
                     .read_text())
    file_s = next(r["sentence"] for r in six
                  if r["node_id"] == f"file::{fname}")
    preds = [r for r in six if r["grain"] == "predicate"
             and r["node_id"].split("::")[1] == fname]
    pred_rows = {p["node_id"]: p for p in
                 td._read(dir05 / "05_predicate_sheet.json")}

    scopes_sheet = td._read(dir05 / "05_scope_sheet.json")
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


def _openai_voicer(fact):
    return _openai_caller(_VOICE_PROMPT + fact)


def voice_facts(items, store_path, registry, voicer=None):
    """One scoped call per NEW fact; stored; blessed > gated
    proposed > the machine fact. Machine writes PROPOSED only."""
    store_path = Path(store_path)
    store = (json.loads(store_path.read_text())
             if store_path.exists() else {})
    blessed = {s.get("fact_key"): s.get("blessed_text")
               for s in registry.get("sentences", [])
               if s.get("fact_key") and s.get("blessed_text")}
    voicer = voicer or _openai_voicer
    out = {}
    changed = False
    for key, fact in items:
        if key in blessed:
            out[key] = blessed[key]
            continue
        if key not in store:
            try:
                voice = voicer(fact)
            except Exception as exc:  # noqa: BLE001 — a failed
                voice = None          # voice is a recorded miss,
                findings = [f"call failed: {type(exc).__name__}"]
            else:
                findings = _voice_gate(voice, fact)
            store[key] = {"machine_fact": fact,
                          "voice": None if findings else voice,
                          "status": ("failed" if findings
                                     else "proposed"),
                          "findings": findings,
                          "model": _MODEL_NAME,
                          "basis_version": BASIS_VERSION}
            changed = True
        entry = store[key]
        out[key] = entry["voice"] or fact
    if changed:
        store_path.write_text(json.dumps(store, indent=1))
    return out


def docket_v2_for_file(dir05, dir06, dir02, fname, voices=None,
                       dir01=None):
    """FACTS (+voices beside their facts) and CONTEXT (raw SQL),
    with the must-say flags. The gate reads FACTS alone."""
    facts, items = render_facts(dir05, dir06, dir02, fname)
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
