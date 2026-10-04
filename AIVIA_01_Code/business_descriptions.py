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
# BASIS_VERSION = "07.1.0" — the 07 grammar constant: the S-rule
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

import json
import re
from pathlib import Path

import technical_descriptions as td

BASIS_VERSION = "07.1.0"

# The template labels (S7), in ruled order.
TEMPLATE_LABELS = ["Who's in it:", "Each row shows:",
                   "Time window:", "Excludes:"]

BANNED_WORDS = {"join", "select", "query", "table", "temp",
                "column", "procedure", "parameter"}

RESTRICTION_STEMS = {"only", "exclude", "limited", "restricted"}

# Function words — structural English, never content claims.
FUNCTION_WORDS = set("""
a an the and or of for to in on at by with from as is are was
were be been has have had it its it's this that these those each
every all any no not when where who whose which while during
either both than then there their they them he she s t who's
what how if will can may must into onto over under after before
between per also such same one two three
excludes time specific type category
""".split())
# ('excludes'/'time': OUR OWN S7 template labels — structural,
#  never content claims; the first live run's gate defect)

# THE DESCRIBING VOCABULARY (S9 appendix, RATIFIED 2026-10-03 —
# one enumerated ruling; never grows case-by-case again; the
# NEVER list words are deliberately absent: separator delimiter
# comma semicolon formatted / purpose words / superlative claims
# / domain words — only the docket may supply those).
PLAIN_LEXICON = set("""
shows lists holds carries contains includes covers combines
groups counts adds attaches brings draws keeps returns records
marks labels names identifies appears belongs derives applies
matches links ties pairs gathers collects summarizes totals
measures tracks reflects represents describes indicates means
refers relates remains stays spans ranges starts begins ends
stops
row record field value list set group count total amount period
range window date time day month year start end beginning source
category type kind status flag detail details summary item entry
text name label identifier description information selection
report dataset data result
single multiple several separate combined related linked matching
matched recorded available missing blank empty present absent
active inactive current specific configurable optional defined
stated listed shown included excluded grouped
only limited restricted excluding
within during across together otherwise alongside plus without
whether
marked lacking apply demographics context speaking entered about
none begin
""".split())
# the stem pool — membership runs through the same prefix-
# tolerant matcher the docket uses, so 'values'/'value',
# 'attached'/'attaches', 'begins'/'begin' all meet
PLAIN_STEMS = None  # built after _stem is defined (below)
# (ruled 2026-10-03 with the S-set; grown same day at the first
# live run: date/missing/identifier/begin/end/details — generic
# business words only; domain claims like admission/discharge/
# transfer stay BLOCKED, the gate's job. 'separator' is
# deliberately ABSENT — the round-2 fabrication must always
# fail here)

_SIGHTINGS = []


def reset_sightings():
    del _SIGHTINGS[:]


def code_sightings():
    return list(_SIGHTINGS)


def _tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def _stem(tok):
    """Suffix-tolerant normal form (the probe's find: 'location'
    must meet 'located', 'creation' meet 'created')."""
    for suf in ("ation", "tion", "ing", "ion", "ed", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 4:
            return tok[:-len(suf)]
    return tok


PLAIN_STEMS = PLAIN_LEXICON | {_stem(w) for w in PLAIN_LEXICON}


def _in_pool(stem, pool):
    """Prefix-tolerant membership (one matcher for docket,
    lexicon and registry pools)."""
    if stem in pool:
        return True
    return len(stem) >= 4 and any(
        len(d) >= 4 and (d.startswith(stem) or stem.startswith(d))
        for d in pool)


def _sentences_of(text, grain):
    if grain == "file":
        parts = []
        for line in text.splitlines():
            line = line.strip()
            for label in TEMPLATE_LABELS:
                if line.startswith(label):
                    line = line[len(label):].strip()
            if line:
                if label == "Excludes:":
                    parts.extend(p.strip() for p in
                                 line.split(";") if p.strip())
                else:
                    parts.extend(p.strip() for p in
                                 re.split(r"[.!?]", line)
                                 if p.strip())
        return parts
    return [p.strip() for p in re.split(r"[.!?]", text)
            if p.strip()]


def _docket_text(docket):
    return docket["text"] if isinstance(docket, dict) else docket


def gate(audience_text, docket, grain, registry=None):
    """G-1..G-7 (contract law): findings list; empty == pass.
    No model anywhere in here."""
    findings = []
    dtext = _docket_text(docket)
    dtokens = {_stem(t) for t in _tokens(dtext)}
    rtokens = set()
    for row in (registry or {}).get("names", []):
        rtokens |= {_stem(t) for t in
                    _tokens(str(row.get("blessed_name", "")))}

    # G-1 lexical whitelist — fail NAMES the token
    quoted = re.findall(r"'[^']*'", audience_text)
    for q in quoted:
        if q not in dtext:
            findings.append(f"G-1: {q} has no stored basis")
    for tok in _tokens(audience_text):
        if tok in FUNCTION_WORDS:
            continue
        stem = _stem(tok)
        if _in_pool(stem, PLAIN_STEMS) or _in_pool(stem, dtokens) \
                or _in_pool(stem, rtokens):
            continue
        findings.append(f"G-1: '{tok}' has no stored basis")

    # G-2 banned vocabulary
    for tok in _tokens(audience_text):
        if _stem(tok) in BANNED_WORDS or tok in BANNED_WORDS:
            findings.append(f"G-2: banned word '{_stem(tok)}'")
    for m in re.findall(r"@\w+", audience_text):
        findings.append(f"G-2: banned token '{m}'")

    # G-3 budgets
    for s in _sentences_of(audience_text, grain):
        n = len(s.split())
        if n > 15:
            findings.append(f"G-3: sentence exceeds 15 words "
                            f"({n})")
    if audience_text.count("(") > 1:
        findings.append("G-3: more than one parenthetical")
    if re.search(r"\([^)]*\(", audience_text):
        findings.append("G-3: nested parenthetical")

    # G-4 template (file grain)
    if grain == "file":
        lines = [ln.strip() for ln in audience_text.splitlines()
                 if ln.strip()]
        shape_ok = (len(lines) == 4 and all(
            ln.startswith(lab) for ln, lab in
            zip(lines, TEMPLATE_LABELS)))
        if not shape_ok:
            findings.append("G-4: template shape — exactly the "
                            "four labeled lines")

    # G-5 anchors: restriction speech needs membership rows
    has_membership = ("Population:" in dtext
                      or "Excludes" in dtext
                      or (": " in dtext and
                          "no membership conditions" not in dtext))
    if any(_stem(t) in RESTRICTION_STEMS
           for t in _tokens(audience_text)
           if t not in FUNCTION_WORDS) and not has_membership:
        findings.append("G-5: restriction speech without a "
                        "membership row to anchor it")

    # G-6 must-say (file grain, exactly three members)
    if grain == "file" and isinstance(docket, dict):
        low = audience_text.lower()
        if docket.get("gap") and not any(
                k in low for k in ("gap", "not described",
                                   "not covered",
                                   "built as a string",
                                   "run time")):
            findings.append("G-6: the gap must be said")
        if docket.get("params") and "window" not in low:
            findings.append("G-6: the window must be said")
        if docket.get("population") and \
                "excludes:" not in low:
            findings.append("G-6: the Excludes line must exist")

    # G-7 unbound codes never surface (S10) — sighting recorded
    unquoted = re.sub(r"'[^']*'", " ", audience_text)
    for tok in re.findall(r"\b\d+\b", unquoted):
        findings.append(f"G-7: raw code '{tok}' must not "
                        "surface in business prose")
        _SIGHTINGS.append({"code": tok,
                           "context": audience_text[:120]})
    return list(dict.fromkeys(findings))  # deduped, order kept


def docket_for_file(dir05, dir06, dir02, fname):
    rows = json.loads((Path(dir06) /
                       "06_description_sheet.json").read_text())
    file_s = next(r["sentence"] for r in rows
                  if r["node_id"] == f"file::{fname}")
    scope_s = [r["sentence"] for r in rows
               if r["grain"] == "scope"
               and r["node_id"].split("::")[1] == fname]
    text = "\n".join([file_s] + scope_s)
    return {"text": text,
            "gap": "in this gap" in file_s,
            "params": "Parameters shaping the population"
                      in file_s,
            "population": "Population:" in file_s}


# ---- the prompt constructor (deterministic; example-free by law)

SYSTEM_PROMPT = (
 "You write business descriptions of report data for healthcare "
 "BI consumers. You receive a TECHNICAL description rendered "
 "mechanically from parsed SQL.\n"
 "TRUTH RULES (hard): claim only what the technical text states; "
 "never invent purposes, formats, separators, counts, or "
 "meanings; 'attaching'/'attachment rule' text ADDS information "
 "to rows and never restricts who is in the data; do not decode "
 "system default expressions — say 'a configurable window'; a "
 "bare code whose meaning the text does not state must never "
 "appear — say 'a specific recorded type'; translate technical "
 "phrasing into plain words and never copy uppercase tokens, "
 "abbreviations, or quoted literals verbatim.\n"
 "STYLE RULES (hard): one claim per sentence; sentences at most "
 "15 words; no nested parentheticals and at most one short "
 "parenthetical; no SQL vocabulary (join, select, query, table, "
 "temp, column, procedure, parameter); no tokens starting with "
 "@; no field inventories or abbreviations — name KINDS of "
 "information; plain present tense, active voice. Output only "
 "what the template asks — no preamble.")

_GRAIN_INSTRUCTIONS = {
    "file": ("Grain: a whole report dataset. Produce EXACTLY "
             "these four labeled lines, nothing else:\n"
             "Who's in it: <who the rows are about, one "
             "sentence>\n"
             "Each row shows: <the KINDS of information one row "
             "carries, one sentence, no field names>\n"
             "Time window: <the window, one short phrase>\n"
             "Excludes: <each exclusion as a short plain-English "
             "phrase, semicolon-separated>"),
    "scope": ("Grain: one selection inside the dataset build. "
              "At most 3 sentences, each at most 15 words, "
              "describing what this selection contains."),
    "field": ("Grain: one delivered field. At most 2 sentences, "
              "each at most 15 words."),
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
    specs = []
    for f in files:
        docket = docket_for_file(dir05, dir06, dir02, f)
        floor = next(r["sentence"] for r in six
                     if r["node_id"] == f"file::{f}")
        specs.append((f"file::{f}", "file", docket, floor))
    for r in six:
        if r["grain"] == "scope":
            specs.append((r["node_id"], "scope", r["sentence"],
                          r["sentence"]))
    for expr_id, scope_id, item in _field_nodes(dir05, dir02):
        if only_file and scope_id.split("::")[1] != only_file:
            continue
        owner = next((r["sentence"] for r in six
                      if r["node_id"] == scope_id), "")
        specs.append((expr_id, "field", owner + "\n" + item,
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

_MODEL_NAME = "gpt-5-mini"
REPAIR_BUDGET = 3
CALL_TIMEOUT_S = 120  # harness law 2026-10-03: a wedged socket
#                       can never hang the build


def _openai_caller(prompt):
    from build_abstract_names import load_openai_key
    from openai import OpenAI
    client = OpenAI(api_key=load_openai_key(),
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
