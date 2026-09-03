"""Bottom-up description generation over the calculation DAG (ADR 0019).

A CTE is the smallest certified unit of business definition. Descriptions
are generated in topological order — every step's direct dependencies are
described before the step itself — then each metric's description is
composed from its ROOT steps' descriptions (summaries of summaries, never
raw SQL walls).

This module is pure orchestration: ordering, prompts, content-hash caching.
The LLM is a callback `describe(prompt) -> str`, so tests run with a fake,
devtools plugs in a local OpenAI-compatible endpoint, and production plugs
in the customer's Azure OpenAI — the Data Agent is a CONSUMER of these
descriptions, never the generator.

Grounding rule: a step's prompt contains its OWN sql fragment plus only the
names+descriptions of its direct dependencies (context, not content), so a
bad description cannot cascade up the chain.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Callable

from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.models import EdgeType, NodeLayer

# Bump when a prompt changes: the version is part of every cache key,
# so a prompt upgrade automatically regenerates every description on
# the next 07 run — no flags, no manual cache wipe (live find
# 2026-08-13: vague descriptions survived a rerun because the cache
# key knew only the SQL, not the prompt that read it).
# v3 (live find 2026-08-14): v2 kept actual values but also kept raw
# warehouse identifiers — the fix is grounded translation material
# (the data dictionary the graph already holds) plus a ban on raw
# identifiers in the output.
# v4 hardened the SQL-reading prompt after the fabrication trace.
# v5 (ADR 0044 phase 2, clauses 2+5): the SQL-reading step prompt is
# DELETED — the step path translates typed tree facts via
# src/tree/translate.py; the LLM never sees a SQL statement again.
# TREE_CONTRACT_VERSION rides in the version so tightening the tree
# contract regenerates everything it governs.
from src.tree import TREE_CONTRACT_VERSION
from src.tree.extract import build_decision_tree

# v6 (2026-08-21, walk find 2): the metric-grain scope rule — the
# bump invalidates every cached description so poisoned "without
# applying any filtering decisions" text cannot survive the next run.
# 7: the ADR 0074 wiring — skeleton-floor acceptance replaced the
# translate/enforce path in the step loop; every description
# regenerates under the ratified architecture (0044 version binding).
# 8: DESC-LEAF-1 + the 09-03 estate-scale fixes (subject-phrase
# meanings, elision-count exemption, claim-shaped placeholder ban).
# 9: the digit-boundary camel fix ('hba1 c' — the answer key's first
# catch); composition changed, every governed description regenerates
# 10: the 09-04 overnight queue — §5.3a-1 sentence-grain kill (what
# ships changed), the derived-values lead (3a), EXISTS naming the
# missing record via the inner table's meaning (3b, rides t4)
PROMPT_VERSION = f"10.t{TREE_CONTRACT_VERSION}"

# ADR 0074 call 2 (ratified 2026-09-02): the provenance vocabulary for
# stored descriptions — spec:B2's closed set, code home. gate_passed =
# smoothed prose that cleared the gate; skeleton_floor = deterministic
# composition (unfalsifiable); flagged = kept but marked. Emptied
# descriptions are ABSENT rows (the empties-(a) ruling): counted,
# never stored, never silent.
PROVENANCE = ("gate_passed", "skeleton_floor", "flagged")

MEASURE_PROMPT = (
    "You are documenting a Power BI DAX {expression_type} for a business "
    "audience of clinicians and executives.\n"
    "Measure name: {name}\n"
    "Defined in report: {report_name}\n"
    "{dict_block}"
    "DAX expression:\n{expression}\n\n"
    "Write ONE sentence (max 30 words) stating what this calculates in "
    "business terms. Then, if the DAX makes decisions, add one line per "
    "decision, each starting with '- ': filters, thresholds, time "
    "windows, and conditions. Keep the literal VALUES that define each "
    "decision — codes, numbers, statuses — with the business meaning "
    "beside each when the data dictionary above provides one. NEVER "
    "show raw table or column identifiers in the output — use the "
    "dictionary description or a plain phrase instead. Never write "
    "vague fillers such as 'specific', 'specified', 'certain', or "
    "'various' in place of a value. Ground every line in the DAX above. "
    "No patient identifiers, no preamble."
)

METRIC_PROMPT = (
    "You are documenting the certified business metric {metric_name}.\n"
    "Its calculation is assembled from these final steps (each already "
    "described in business terms):\n{roots_block}\n"
    "It draws on {step_count} calculation steps in total, whose "
    "conditions comprise {decision_count} filtering/branching decision "
    "sites.\n\n"
    "Write a concise business description: first, one sentence stating "
    "what this metric reports or measures, grounded strictly in the step "
    "descriptions and the metric name. Then a blank line, then "
    "'Business logic:' followed by 3-6 bullets covering the population "
    "included, time windows, clinical criteria or thresholds, and how the "
    "outcome is calculated — in business terms, grounded ONLY in the step "
    "descriptions above. Bullets must keep the actual values, codes, "
    "thresholds, and time windows the step descriptions name — never "
    "generalize them away, and never write vague fillers such as "
    "'specific', 'specified', 'certain', or 'various' in place of a "
    "value. Do not state purposes, benefits, or decisions "
    "the metric supports unless a step description states them — no "
    "filler like 'supports decision-making' or 'improves outcomes'. "
    "If the decision-site count above is greater than zero, NEVER "
    "claim the metric applies no filters or no filtering criteria — "
    "such absence claims are true only of a single step, never of the "
    "metric; instead say the detailed criteria live in its "
    "{decision_count} decision sites. "
    "Plain text only: no greetings, no markdown headers, no bold, no "
    "trailing spaces, no invented details."
)

# Observation only (never a retry loop): generated text that hides a
# value behind a filler word is flagged for the run report / dashboard.
_VAGUE_FILLERS = re.compile(
    r"\b(specific|specified|certain|various)\b", re.IGNORECASE)

# Raw-identifier smell in OUTPUT text: SNAKE_CASE_CAPS columns,
# #temp tables, backticked/dotted code refs (live find 2026-08-14:
# ADT_DEPARTMENT_ID / #SDX / `pd.PatEncCSNID` all over the workbench).
_RAW_IDENTIFIERS = re.compile(
    r"(#\w+|`[^`]+`|\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b)")




# --- The grounding gate (2026-08-19, TRACE_USP_ED_SEPSIS) -------------
# Field-proven failure modes in production descriptions: (1) SELECTed
# columns hallucinated into filters ("excludes pending or cancelled"
# with no such condition anywhere), (2) invented literal codes
# ("flowsheet IDs 123 and 456" vs the real 900112/900111). The prompt
# already forbade both; prompt instructions are intent — only
# mechanical verification survives (the notebook-contract lesson).

_OUT_NUMBERS = re.compile(r"\d{2,}")
_OUT_QUOTED = re.compile(r"'([^']{1,40})'")
_FILTER_CLAIM = re.compile(
    r"(?i)\b(exclud\w*|includes? only|only includ\w*|filters?\b|"
    r"requir\w+|must have|limited to|restrict\w*)\b")
_CLAIM_STOPWORDS = frozenset(
    "encounters includes include included excludes exclude excluded "
    "filters filter filtered records results patients patient orders "
    "information department departments emergency hospital associated "
    "between during where which their those based table tables step "
    "steps only that this with from have been were each every there "
    "measurements medications details specific specified certain "
    "various".split())


# --- P0-a (DESC-GATE-2, ordered 2026-08-31): TABLE + GRAIN claims --
# The two classes the value/filter checks cannot see. A wrong GRAIN
# claim is the most dangerous description error we can ship: it
# reads fluent and it is false ("counts patients" over a visit-grain
# query). A wrong TABLE claim invents provenance.

# FROM/JOIN/UPDATE/INTO targets — the tables a fragment actually
# touches. Aliases and schema prefixes are stripped to the bare name
# (the alias-never-faces-the-steward rule from CONSOLE-4c).
# real estates read TEMP TABLES (#Staging) and bracketed identifiers
# as often as plain names (P0-c corpus find on Clarity-shaped SQL)
# READS only. INTO/UPDATE name a WRITE TARGET, not a source — a
# SELECT…INTO #X does not read #X, and listing it made a step
# appear to read itself (DESC-TEMP-1 live find).
# the entity words a description may claim to count, and the column
# tokens that evidence each. Word-grain, never question shapes.
_GRAIN_WORDS = {
    "patient": ("patient", "member", "person", "mrn"),
    "visit": ("visit", "encounter", "enc_", "_enc", "admission",
              "appointment", "appt", "stay"),
    "order": ("order", "prescription", "med_order"),
    "claim": ("claim", "billing", "cpt", "charge"),
    "result": ("result", "lab", "observation"),
}
_GRAIN_CLAIM = re.compile(
    r"(?i)\b(?:counts?|per|one row per|number of|distinct)\s+"
    r"(?:the\s+)?([a-z]+?)s?\b")


def _bare(name: str) -> str:
    """The comparable table name: schema and brackets stripped, the
    temp-table marker KEPT (#Staging and Staging are different
    objects to a reader, and both must be recognisable)."""
    last = name.split(".")[-1].strip()
    return last.strip("[]").lower()


def parsed_tables(fragment: str) -> "set[str]":
    """The base tables a fragment reads — named references minus the
    CTE names it defines itself. PARSER-NATIVE since the gate recut
    (2026-09-02, spec:G4 ancestry: DESC-SKELETON-3's tree
    consumption). parse_ok False => empty set: the closed-outcome
    law — no evidence refuses no claim; no regex fallback exists."""
    from src.tree.extract import query_shape
    return {_bare(x) for x in query_shape(fragment or "").base_tables}


def parsed_grain(fragment: str) -> "set[str]":
    """The entity grain(s) the fragment's KEY columns evidence.

    Precedence, strongest evidence first (the parser decides which
    columns define a row, not prose):
      1. DISTINCT / GROUP BY columns — they DEFINE the row;
      2. otherwise the SELECT list's *_ID columns — the row's keys;
      3. otherwise nothing: an unknown grain refuses no claim
         (absence of evidence is not evidence).
    When (1) or (2) yields any entity, that set is the grain — a
    PATIENT_ID also present in a visit-keyed select does not make
    the query patient-grain."""
    # PARSER-NATIVE since the gate recut (2026-09-02): the docstring
    # said "the parser decides" — now the code agrees. OUTER-scope
    # keys only: a derived table's GROUP BY defines ITS rows, not the
    # step's (the 3a scope law, checker side).
    from src.tree.extract import query_shape
    shape = query_shape(fragment or "")
    source_cols = shape.key_cols or shape.select_cols
    ids = [c.split(".")[-1] for c in source_cols
           if c.upper().endswith(("_ID", "_KEY", "_NO", "_NUM"))]
    keys_low = " ".join(ids).lower()
    found = set()
    for entity, tokens in _GRAIN_WORDS.items():
        if any(tok in keys_low for tok in tokens):
            found.add(entity)
    return found


def _grain_violations(text: str, fragment: str) -> "list[str]":
    evidence = parsed_grain(fragment)
    if not evidence:
        return []          # unknown grain refuses nothing
    out = []
    for claim in set(_GRAIN_CLAIM.findall(text)):
        claimed = claim.lower().rstrip("s")
        if claimed not in _GRAIN_WORDS:
            continue       # not a grain word — other checks own it
        if claimed not in evidence:
            out.append(
                f"grain claim {claim!r} contradicts the parsed grain "
                f"({', '.join(sorted(evidence))})")
    return out


def _table_violations(text: str, fragment: str,
                      dict_lines: "list[str] | None") -> "list[str]":
    reads = parsed_tables(fragment)
    if not reads:
        return []
    # a claim names a table when it uses a TABLE-SHAPED token
    # (UPPER_SNAKE or a known read) — prose nouns are not claims
    dict_blob = " ".join(dict_lines or []).lower()
    out = []
    for token in set(re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b",
                                text)):
        bare = _bare(token)
        if bare in reads:
            continue
        if bare in dict_blob or bare in (fragment or "").lower():
            continue       # named in the source or its dictionary
        out.append(
            f"ungrounded table claim: {token!r} — the fragment reads "
            f"{', '.join(sorted(reads)) or 'no table'}")
    return out


# --- DESC-VOICE-1 (Sunny's grading, 2026-08-31) ---------------------
# Her verdict on ACCURACY was clean; the failures were VOICE. A
# steward's field must not carry a developer's sentence: the source
# objects are already carried by the RELATIONSHIP (landing matrix
# §1a), so the sentence never needs them.

_TECH_WORDS = (
    "temporary table", "temp table", "table", "cte",
    "common table expression", "join", "joins", "joined", "select",
    "subquery", "query", "dataset", "data set", "column", "columns",
    "row", "rows", "schema", "index",
)
# the word must be the SUBJECT, not part of a computation's name:
# "Row_Number" / "row number" describes a real ranking the SQL does,
# while "the rows" is developer voice (P0-c variance find — the
# false positive emptied an otherwise-honest description)
_TECH_SUBJECT = re.compile(
    r"(?i)(?:^|[-\s(])(?:the\s+)?(" + "|".join(_TECH_WORDS)
    + r")\b(?![\s_-]*(?:number|num|count|numbering))")
_HASH_OBJECT = re.compile(r"#\w+")
# "X (ACRONYM)" or "ACRONYM (expansion)" — the model teaching us
# medicine from its own knowledge rather than from the source
_ACRONYM_GLOSS = re.compile(
    r"([A-Za-z][A-Za-z\s/-]{3,40}?)\s*\(([A-Z]{2,6})\)"
    r"|\b([A-Z]{2,6})\s*\(([A-Za-z][A-Za-z\s/-]{3,40}?)\)")


# DESC-LEAF-1 part 2 — the composer's own fallback strings, frontier
# AS DATA (spec:G4 clause 1): pattern -> injection exemplar, each
# proven to fire in TestPlaceholderBan (clause 2). The pattern matches
# the placeholder CLAIM, not its words anywhere — '\bthe value\b'
# alone false-positived on the customer's own 'the value set' and
# emptied a true description (09-03 estate find). A placeholder in
# prose means a leaf went unvoiced; the ruled outcome (empties-(a)
# precedence) is a COUNTED empty, never shipped mush.
_COMPOSER_PLACEHOLDERS = {
    r"condition holds:": "condition holds: `X > 1`",
    r"\bthe value\b\s+(?:is|falls|does|exceeds|matches|contains"
    r"|starts|ends)": "the value is at least 4",
}


def voice_violations(text: str, fragment: str,
                     dict_lines: "list[str] | None" = None
                     ) -> "list[str]":
    """The business-voice rules. Not accuracy — AUDIENCE."""
    out: "list[str]" = []
    ground = ((fragment or "") + "\n"
              + "\n".join(dict_lines or [])).lower()
    for pat in _COMPOSER_PLACEHOLDERS:
        if re.search(pat, text, re.IGNORECASE):
            out.append(
                f"composer placeholder in a business description: "
                f"{pat!r} — an unvoiced leaf must become a counted "
                "empty, not shipped mush")
    for obj in set(_HASH_OBJECT.findall(text)):
        out.append(
            f"technical object in a business description: {obj!r} — "
            "the source object is carried by the relationship, not "
            "the sentence")
    for m in _TECH_SUBJECT.finditer(text):
        out.append(
            f"technical vocabulary in a business description: "
            f"{m.group(1)!r} — say what is included, not how the "
            "SQL assembles it")
    # an acronym may be EXPANDED only from the source or dictionary
    for m in _ACRONYM_GLOSS.finditer(text):
        expansion = (m.group(1) or m.group(4) or "").strip()
        acronym = (m.group(2) or m.group(3) or "").strip()
        if not expansion or not acronym:
            continue
        head = expansion.split()[0].lower().rstrip("s")
        if len(head) >= 4 and head not in ground:
            out.append(
                f"ungrounded acronym expansion: {acronym!r} expanded "
                f"as {expansion!r}, which appears nowhere in the "
                "source or dictionary — print the acronym as written")
    return out


# DESC-VOICE-2 (Sunny's second read): the gate stops LIES, it does
# not stop EMPTINESS. A description that says "Encounters are
# included when… critical for tracking treatment protocols" is
# unfalsifiable purpose-speak. The rule: say WHAT is included and
# on WHAT VALUES; never say WHY the business does it — purpose is
# the steward's contribution, and claiming it is how a
# machine-written field starts lying politely.
_PURPOSE_TAIL = re.compile(
    r"(?i)\b(?:"
    r"critical (?:for|to)|essential (?:for|to)|important (?:for|to)|"
    r"key (?:for|to)|vital (?:for|to)|"
    r"ensur\w+|allow\w+ (?:for|us|them)|enabl\w+|facilitat\w+|"
    r"align\w+ with|help\w* (?:to )?(?:identify|ensure|track|"
    r"capture|target)|"
    r"support\w* (?:the )?(?:analysis|tracking|monitoring|quality)|"
    r"provid\w+ (?:a )?(?:clear|comprehensive|insight)|"
    r"for (?:quality|reporting|analysis|tracking) (?:metrics|"
    r"purposes)|"
    r"so that|in order to|which is useful|thereby|"
    r"relevant (?:cases|records|data) are (?:captured|considered)|"
    r"comprehensive view|effective\w* (?:tracking|monitoring)"
    r")\b")


# a prompt placeholder echoed into the output is the instruction
# leaking through as data (P0-c find: "(first: <first_value>, last:
# <last_value>)" reached a steward-facing description)
_PLACEHOLDER = re.compile(r"<[a-z_]{3,24}>")


def placeholder_violations(text: str) -> "list[str]":
    return [f"prompt placeholder echoed: {m!r} — the instruction "
            "leaked into the description as data"
            for m in set(_PLACEHOLDER.findall(text))]


def purpose_violations(text: str, fragment: str) -> "list[str]":
    """DESC-VOICE-2 item 3: purpose speculation is banned unless the
    SOURCE states it (a comment we can quote)."""
    ground = (fragment or "").lower()
    out: "list[str]" = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _PURPOSE_TAIL.search(line)
        if not m:
            continue
        phrase = m.group(0).lower()
        if phrase in ground:          # the source says it; quote ok
            continue
        out.append(
            f"purpose speculation: {m.group(0)!r} in {line[:60]!r} — "
            "say WHAT is included and on WHAT VALUES; why is the "
            "steward's to write")
    return out


_GRAIN_SUBJECT = {
    "patient": "patients", "visit": "encounters",
    "order": "medication orders", "claim": "billing records",
    "result": "lab results",
}


def subject_for(fragment: str) -> str:
    """The SUBJECT a description should name, from the parsed grain
    (DESC-VOICE-1 item 2). 'records' only when grain is unknown —
    and that fallback is a signal worth logging."""
    grain = parsed_grain(fragment)
    for key in ("patient", "visit", "order", "claim", "result"):
        if key in grain:
            return _GRAIN_SUBJECT[key]
    return "records"


# --- DESC-VOICE-3.1 (ordered 08-31, specimen USP_ED_SEPSIS · #BPA) --
# THE MISATTRIBUTED PREDICATE: right values, wrong subject. The
# description said "Encounter IDs must match the ADT_ARRIVAL_TIME and
# ED_DEPARTURE_TIME" where the SQL constrains ALT_ACTION_INST BETWEEN
# those two. Every value was present, so a presence check passes it.
# A description can be entirely built of true tokens and still assert
# something the SQL never says — grounding must therefore check what
# a claim is PREDICATED OF, not merely that its parts occur.
_PREDICATES = re.compile(
    r"(?is)([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\s*"
    r"(?:(BETWEEN)\s+([A-Za-z_][\w.]*)\s+AND\s+([A-Za-z_][\w.]*)"
    r"|(=|<>|!=|>=|<=|>|<)\s*([A-Za-z_][\w.]*))")


# A misattribution can ride on any condition verb, and the shared
# _FILTER_CLAIM pattern is deliberately narrow (it gates the
# selected-not-filtered heuristic, where a false positive empties an
# honest description). The #BPA lie used "must match", which that
# pattern does not carry — so this class gets its OWN, wider trigger
# rather than widening a pattern tuned for a different job.
_CONDITION_VERB = re.compile(
    r"(?i)\b(must|has to|have to|need(?:s)? to|should|only|between|"
    r"within|matches?|match|falls?|fall|requir\w+|restrict\w*|"
    r"limited to|exclud\w*|includ\w*)\b")


def _column_words(col: str) -> "set[str]":
    """The words a steward-facing sentence would use for a column.
    ALT_ACTION_INST → {alt, action, inst}. Attribution is checked at
    WORD grain because the description must NOT contain the raw token
    (rule 2 of the same order bans column names outright)."""
    return {w for w in re.split(r"[_\W]+", col.lower()) if len(w) > 2}


# --- DESC-VOICE-3.2: NO COLUMN NAMES in a steward's field ---------
# The table rule at COLUMN grain. BPA_LOCATOR_ID / ADT_ARRIVAL_TIME /
# ALT_ACTION_INST are developer tokens; a steward reads them as
# noise. The fix is not "strip them" but "write from the column's
# DICTIONARY DESCRIPTION" — dictionary_for_step() already selects
# exactly the referenced columns' entries, so this is wiring + a ban.
# Where a column has NO entry: a readable form of the name AND the
# column is REPORTED as a coverage gap (Sunny's fallback ruling) —
# missing dictionary entries become a Tier-1 asset ("N columns your
# catalog never documented"), never a silent degradation.

def parsed_columns(fragment: str) -> "set[str]":
    """Every column the fragment's OUTER scope evidences — select
    list + deciding sites + keys. Parser-native since the gate
    recut; same closed-outcome law as parsed_tables."""
    from src.tree.extract import query_shape
    shape = query_shape(fragment or "")
    cols = {c.split(".")[-1].upper() for c in shape.select_cols}
    cols |= set(shape.deciding_cols)
    cols |= {c.split(".")[-1].upper() for c in shape.key_cols}
    return {c for c in cols if "_" in c}


def _documented(dict_lines: "list[str] | None") -> "set[str]":
    out: "set[str]" = set()
    for line in dict_lines or []:
        head = line.strip().lstrip("- ").split(":", 1)[0].strip()
        if head:
            out.add(head.upper())
    return out


def undocumented_columns(
    fragment: str, dict_lines: "list[str] | None" = None,
) -> "list[str]":
    """Columns the step references that the customer's dictionary does
    NOT describe. Returned so callers can REPORT the gap."""
    return sorted(parsed_columns(fragment) - _documented(dict_lines))


def readable_column(col: str) -> str:
    """The fallback wording when a column has no dictionary entry:
    minimally transformed, never invented. ALT_ACTION_INST stays
    honest as 'alt action inst' — deliberately plain, so a thin
    description reads as thin rather than as confident prose.
    CamelCase splits too ('@StartDate' voiced as 'dstartdate' was the
    recorded 741bef2 find; parameters and TMDL names camel-case).
    Lowercase-to-uppercase boundaries ONLY: a digit boundary split
    'HBA1C' into 'hba1 c' (caught by the corpus answer key on its
    first run — the LLM had been silently smoothing the mangle)."""
    col = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", col)
    return re.sub(r"[_\W]+", " ", col).strip().lower()


def column_name_violations(text: str, fragment: str) -> "list[str]":
    """Raw column names in steward-facing text. Only columns the
    fragment actually references are flagged, so an ordinary
    capitalised word can never trip this."""
    cols = parsed_columns(fragment)
    out: "list[str]" = []
    for col in sorted(cols):
        # ONLY developer-shaped tokens. A single ordinary word that
        # happens to be a column (RESULT, NAME, DEPARTMENT) is not a
        # developer token, and banning it would push descriptions
        # away from plain English — the opposite of this order's
        # intent. Caught by an existing steward-voice test that this
        # rule broke on first draft.
        if "_" not in col:
            continue
        # match the developer casing, not the English word: the
        # offence is BPA_LOCATOR_ID appearing verbatim
        if re.search(r"\b" + re.escape(col) + r"\b", text):
            out.append(
                f"column name in a business description: {col!r} — "
                f"write from its dictionary description, or say "
                f"{readable_column(col)!r}")
    return out


def _stem(word: str) -> str:
    """Crude, deliberate stem so 'acted'/'action', 'alert'/'alt' and
    'arrival'/'arrive' collapse. Rule 2 of this same order BANS raw
    column names in descriptions, so the subject can only ever appear
    in business words — demanding a literal token match would demand
    the very thing the order forbids. Prefix comparison is the
    weakest test that still distinguishes 'the time the alert was
    acted on' (right subject) from 'Encounter IDs' (wrong one)."""
    w = re.sub(r"(?:ing|ed|es|s|ion|al)$", "", word.lower())
    return w[:4]


def _names_subject(line_words: "set[str]", subject: "set[str]") -> bool:
    """True when the sentence names the predicate's subject in ANY
    form — exact token, or a shared stem with any subject word."""
    if subject & line_words:
        return True
    stems = {_stem(s) for s in subject if len(s) > 2}
    return bool(stems & {_stem(w) for w in line_words})


def _dict_meanings(dict_lines: "list[str] | None") -> "dict[str, str]":
    """dict_lines ('- NAME: description') -> {NAME_upper: description}.
    The checkers' bridge to the meanings reframe: a claim voiced via a
    column's dictionary words must be recognizable as naming it."""
    out: "dict[str, str]" = {}
    for line in dict_lines or []:
        m = re.match(r"^-\s*([^:]+):\s*(.+)$", line.strip())
        if m:
            out[m.group(1).strip().split(".")[-1].upper()] = m.group(2)
    return out


def misattribution_violations(
    text: str, fragment: str,
    dict_lines: "list[str] | None" = None,
) -> "list[str]":
    """A sentence that names the OPERANDS of a predicate must also name
    its SUBJECT (the left-hand side). Only fires when a sentence
    carries a condition claim AND names >=2 operand words while naming
    NO word of the subject — an asymmetry that cannot happen by
    accident and is exactly the #BPA failure.

    Meanings bridge (09-03 estate find, ~15 true claims killed): the
    subject may be named by its DICTIONARY words, not only its column
    words — the composer voices meanings, and a checker that cannot
    read them kills the truth."""
    out: "list[str]" = []
    preds = _PREDICATES.findall(fragment or "")
    if not preds:
        return out
    docs = _dict_meanings(dict_lines)
    for line in text.splitlines():
        low = line.strip().lower()
        if not low or not _CONDITION_VERB.search(low):
            continue
        for _tbl, lhs, is_btw, lo, hi, _op, rhs in preds:
            operands = [x for x in ((lo, hi) if is_btw else (rhs,)) if x]
            op_words: "set[str]" = set()
            for o in operands:
                op_words |= _column_words(o.split(".")[-1])
            if len(op_words) < 2:
                continue
            named = {w for w in op_words if w in low}
            subject = _column_words(lhs)
            line_words = set(re.findall(r"[a-z]{3,}", low))
            if len(named) >= 2 and not _names_subject(line_words, subject):
                doc = docs.get(lhs.split(".")[-1].upper(), "")
                doc_words = {w for w in re.findall(
                    r"[a-z]{3,}", doc.lower().split(". ")[0])
                    if w not in ("the", "this", "that", "with", "for",
                                 "was", "which", "are")}
                if doc_words and len(doc_words & line_words) >= min(
                        2, len(doc_words)):
                    continue        # subject named via its meaning
                out.append(
                    f"misattributed predicate: {line.strip()!r} — names "
                    f"the values of the {lhs} condition but not what "
                    f"they constrain")
                break
    return out


# --- DESC-MEANING-1 (THE REFRAME, ordered 08-31) ------------------
# We were generating from SQL and then CENSORING forbidden words.
# The right frame: the SQL is a SKELETON OF RELATIONSHIPS, the
# dictionary supplies MEANING, and the description is their
# COMPOSITION. Every symptom of the old frame — 74 column-name
# violations, most empties, the 'table' ban — came from removing the
# only vocabulary the model had. Fix by construction, not
# prohibition.
#
# The skeleton is UNFALSIFIABLE BY CONSTRUCTION: every element comes
# from the parse or the dictionary, so it cannot invent a value, a
# subject, or a filter. That property is what lets it be the
# FALLBACK when model smoothing violates the gate — and why nothing
# is ever empty again.

_MAX_LISTED_VALUES = 6


def meaning_of(column: str, meanings: "dict[str, str] | None") -> str:
    """A column's documented business meaning, or the minimally
    transformed name (Sunny's fallback ruling). Never the raw
    identifier — that is the whole point of the reframe."""
    bare = (column or "").split(".")[-1]
    key = bare.upper()
    doc = (meanings or {}).get(key) or (meanings or {}).get(bare)
    if doc and doc.strip():
        # Steward dictionaries hold SENTENCES; a subject must be the
        # FIRST sentence, unterminated — splicing the full text
        # produced 'took place. is recorded' and defeated the
        # misattribution checker (09-03 estate-scale find)
        return doc.strip().split(". ")[0].rstrip(".").strip()
    # fallback gets the ORIGINAL casing — upper-casing first would
    # destroy the camel boundaries readable_column splits on
    return readable_column(bare)


def _values_from(operands: "list[str]") -> str:
    """Concrete values, elided past ~6 with a count naming this list's
    OWN first and last — never invented, never an example."""
    vals = [str(v).strip().strip("'\"") for v in operands if str(v).strip()]
    if len(vals) <= _MAX_LISTED_VALUES:
        return ", ".join(f"'{v}'" for v in vals)
    return f"one of {len(vals)} values from '{vals[0]}' to '{vals[-1]}'"


# The elision idiom's count, recognized by the value gate as composed-
# by-construction (it is len() of the SQL's own list, never a literal)
_ELISION_COUNT = re.compile(r"\bone of (\d+) values from\b")

# The subquery-IN idiom (the 3a-safe voicing: no inner value is ever
# named), recognized by the filter-claim check as composed-by-
# construction WHEN a subquery decides the step — 09-04 estate find
# (HRC6/HRC98 emptied over the composer's own phrase), the echo of
# the elision-count class; injection twin pinned in
# TestEstateScaleCorpses (a fragment with no subquery still refuses
# the fabricated idiom).
_SUBQUERY_IDIOM = re.compile(
    r"\bis (?:restricted to|excluded from) a separately selected set\b")


_OP_WORDS = {"EQ": "is", "NEQ": "is not", "GT": "is more than",
             "LT": "is less than", "GTE": "is at least",
             "LTE": "is at most"}

# OP-FRONTIER-1 (spec:G4): the composer side of the seam, as data.
# test_op_frontier holds EMITTED_OPS == VOICED_OPS ⊎ UNVOICED_OPS and
# proves every VOICED op fires on a synthetic node — membership is
# earned, not declared. An op entering the extractor without entering
# a list here is a red build, not a corpus discovery.
VOICED_OPS = frozenset({
    "EQ", "NEQ", "GT", "LT", "GTE", "LTE",
    "IN", "NOT_IN", "BETWEEN", "NOT_BETWEEN", "LIKE", "NOT_LIKE",
    "IS", "IS_NOT", "EXISTS", "PARAMETER_DEFAULT",
})
UNVOICED_OPS: "dict[str, str]" = {}   # op -> recorded reason; empty is earned


# DESC-LEAF-1: aggregate subjects, voiced from the parse's func fact.
# Wrappers that do not change what a value MEANS pass the column's own
# meaning through; anything outside these frontiers is unvoicable and
# falls to the raw echo (which the gate refuses — a counted empty).
_AGG_WORDS = {"SUM": "the total", "AVG": "the average",
              "MIN": "the lowest", "MAX": "the highest"}
_MEANING_PRESERVING = {"UPPER", "LOWER", "TRIM", "LTRIM", "RTRIM"}


# --- EXPR-IR-1 (ruled 09-03): compositional interpretation ---------
# One rule per captured GRAMMAR kind — recursion handles depth, so no
# expression shape is ever enumerated. Coverage comes from the
# generic rules; per-function phrasing is an EVIDENCE-ORDERED overlay
# (DATEDIFF earned its phrase via 36 counted empties on the estate).
# The kind frontier is data: RENDERED ⊎ UNRENDERED == EXPR_KINDS.
RENDERED_KINDS = ("column", "literal", "variable", "function",
                  "arithmetic", "unary", "cast")
UNRENDERED_KINDS = {
    "case": "a projection choice embedded in a predicate — no "
            "faithful one-phrase reading; counted, never guessed",
    "subquery": "its meaning is the inner selection's own "
                "description — naming it here is the 3a leak",
    "unknown": "outside the captured grammar — counted, never guessed",
}

_ARITH_WORDS = {"+": "plus", "-": "minus", "*": "times",
                "/": "divided by", "%": "modulo"}
_DATEPART_WORDS = {
    "YY": "years", "YYYY": "years", "YEAR": "years",
    "QQ": "quarters", "QUARTER": "quarters",
    "MM": "months", "MONTH": "months", "WK": "weeks", "WW": "weeks",
    "WEEK": "weeks", "DD": "days", "DY": "days", "DAY": "days",
    "HH": "hours", "HOUR": "hours",
    "MI": "minutes", "N": "minutes", "MINUTE": "minutes",
    "SS": "seconds", "S": "seconds", "SECOND": "seconds"}


def _expr_phrase(x, meanings) -> "str | None":
    """Interpret one captured expression node. None = unrenderable —
    the caller falls to the raw echo, which the gate refuses: the
    counted outcome, never a guess."""
    kind = x.kind
    if kind == "column":
        return meaning_of(x.name, meanings)
    if kind == "literal":
        return x.name
    if kind == "variable":
        return meaning_of(x.name.lstrip("@"), meanings)
    if kind == "unary":
        inner = (_expr_phrase(x.children[0], meanings)
                 if x.children else None)
        if inner is None:
            return None
        return f"negative {inner}" if x.name == "-" else inner
    if kind == "cast":
        # a cast changes representation, not meaning — pass through
        return (_expr_phrase(x.children[0], meanings)
                if x.children else None)
    if kind == "arithmetic":
        if len(x.children) != 2:
            return None
        left = _expr_phrase(x.children[0], meanings)
        right = _expr_phrase(x.children[1], meanings)
        if left is None or right is None:
            return None
        sep = (", " if x.children[0].kind in ("function", "arithmetic")
               else " ")
        return f"{left}{sep}{_ARITH_WORDS.get(x.name, x.name)} {right}"
    if kind == "function":
        return _function_phrase(x, meanings)
    return None                       # case / subquery / unknown


def _function_phrase(x, meanings) -> "str | None":
    name = (x.name or "").upper()
    kids = x.children

    def ph(i):
        return (_expr_phrase(kids[i], meanings)
                if i < len(kids) else None)

    if name in ("COUNT", "COUNT_BIG"):
        d = "distinct " if x.distinct else ""
        inner = ph(0) if kids and kids[0].kind == "column" else None
        return (f"the number of {d}{inner} values" if inner
                else f"the number of {d}records")
    if name in _AGG_WORDS:
        inner = ph(0)
        return None if inner is None else f"{_AGG_WORDS[name]} {inner}"
    if name in _MEANING_PRESERVING:
        return ph(0)
    if name == "DATEDIFF" and len(kids) == 3:
        unit = _DATEPART_WORDS.get(
            (kids[0].name or "").strip("'").upper())
        a, b = ph(1), ph(2)
        if unit and a and b:
            return f"the {unit} between {a} and {b}"
        return None
    if name == "ABS":
        inner = ph(0)
        return None if inner is None else f"the absolute value of {inner}"
    # The GENERIC rule: grounded coverage for every function, at any
    # depth — quality overlays are added only on estate evidence.
    parts = [ph(i) for i in range(len(kids))]
    if any(p is None for p in parts):
        return None
    if not parts:
        return f"the {name.lower()} value"
    joined = (" and ".join(parts) if len(parts) == 2
              else ", ".join(parts))
    return f"the {name.lower()} of {joined}"


def _subject_phrase(n, meanings) -> "str | None":
    """The grounded SUBJECT of a predicate leaf, or None when the
    parse offers no voicable subject. Never a placeholder — 'the
    value is at least 4' shipped as mush (the High_Utilizer grade);
    the closed outcomes are voice-fully or counted-unvoiced.

    EXPR-IR-1: when the leaf carries a captured expression record,
    the compositional interpreter IS the subject rule — any depth,
    no shape enumeration. The flat-field path survives only as the
    fallback for leaves with no capture."""
    exprs = getattr(n, "exprs", None) or []
    if exprs:
        return _expr_phrase(exprs[0], meanings)
    if n.column:
        return meaning_of(n.column, meanings)
    func = (getattr(n, "func", None) or "").upper()
    inner_cols = [c for c in n.columns if c]
    inner = inner_cols[0] if len(inner_cols) == 1 else None
    if func in ("COUNT", "COUNT_BIG"):
        d = "distinct " if getattr(n, "func_distinct", False) else ""
        if inner:
            return f"the number of {d}{meaning_of(inner, meanings)} values"
        return f"the number of {d}records"
    if func in _AGG_WORDS and inner:
        return f"{_AGG_WORDS[func]} {meaning_of(inner, meanings)}"
    if func in _MEANING_PRESERVING and inner:
        return meaning_of(inner, meanings)
    return None


def _pattern_phrase(raw: str, negated: bool) -> str:
    """A LIKE pattern -> a business verb, ONLY where the pattern shape
    proves the verb (prefix/suffix/infix with no other wildcards);
    anything irregular stays verbatim as 'matches the pattern' —
    never simplified into a claim the SQL does not make."""
    p = str(raw).strip().strip("'\"")
    wild = set("%_[")
    if p.endswith("%") and len(p) > 1 and not (set(p[:-1]) & wild):
        verb, core = "starts with", p[:-1]
    elif (p.startswith("%") and p.endswith("%") and len(p) > 2
            and not (set(p[1:-1]) & wild)):
        verb, core = "contains", p[1:-1]
    elif p.startswith("%") and len(p) > 1 and not (set(p[1:]) & wild):
        verb, core = "ends with", p[1:]
    else:
        verb, core = "matches the pattern", p
    if negated:
        verb = "does not " + {"starts with": "start with",
                              "contains": "contain",
                              "ends with": "end with",
                              "matches the pattern": "match the pattern",
                              }[verb]
    return f"{verb} '{core}'"


def _operand_phrase(v, meanings) -> str:
    """A comparison operand: @parameters voice as their documented
    meaning; literals stay VERBATIM. (Routing literals through
    meaning_of split '5.6' at the dot and claimed 'between 4 and 6' —
    a false claim found red-first by the NOT_BETWEEN exit test.)"""
    s = str(v).strip()
    if s.startswith("@"):
        return meaning_of(s.lstrip("@"), meanings)
    return s


def _raw_echo(n) -> str:
    # The honest last resort: verbatim, grounded, and UNSHIPPABLE —
    # the gate's placeholder ban refuses it, so an unvoicable leaf
    # becomes a counted empty, never silent mush (DESC-LEAF-1's
    # closed-outcomes ruling).
    return f"condition holds: `{n.expression_sql[:160]}`"


def _leaf_phrase(n, meanings) -> "str | None":
    """One predicate leaf -> one grounded phrase (no trailing period).
    None = deliberately unvoiced here (join keys wire, they decide
    nothing; case_when is a projection choice, not membership)."""
    op = n.op or ""
    subj = _subject_phrase(n, meanings)
    exprs = getattr(n, "exprs", None) or []
    if op in _OP_WORDS:
        if (op == "EQ" and len(exprs) == 2
                and all(x.kind == "column" for x in exprs)):
            return None                      # column = column: a join key
        if len(exprs) == 2:
            # EXPR-IR-1: role-exact comparand (the flat operand list
            # once put the DIVISOR where the threshold belongs)
            comp = _expr_phrase(exprs[1], meanings)
            if subj is None or comp is None:
                return _raw_echo(n)
            return f"{subj} {_OP_WORDS[op]} {comp}"
        if n.operands:
            if subj is None:
                return _raw_echo(n)
            return f"{subj} {_OP_WORDS[op]} {n.operands[0]}"
        cols = [c for c in n.columns if c]
        if op == "EQ" and len(cols) >= 2:
            return None                      # column = column: a join key
        if len(cols) >= 2:
            return (f"{meaning_of(cols[0], meanings)} {_OP_WORDS[op]} "
                    f"{meaning_of(cols[1], meanings)}")
    if op in ("IN", "NOT_IN"):
        neg = op == "NOT_IN"
        if subj is None:
            return _raw_echo(n)
        if "SELECT" in (n.expression_sql or "").upper():
            # subquery IN: its literals belong to the INNER scope —
            # naming them here is the 3a leak by value
            return (f"{subj} is {'excluded from' if neg else 'restricted to'}"
                    f" a separately selected set")
        if n.operands:
            return f"{subj} is {'not ' if neg else ''}{_values_from(n.operands)}"
    if op in ("BETWEEN", "NOT_BETWEEN"):
        falls = "does not fall" if op == "NOT_BETWEEN" else "falls"
        if len(exprs) >= 3:
            lo = _expr_phrase(exprs[1], meanings)
            hi = _expr_phrase(exprs[2], meanings)
            if subj is None or lo is None or hi is None:
                return _raw_echo(n)
            return f"{subj} {falls} between {lo} and {hi}"
        if len(n.operands) >= 2:
            if subj is None:
                return _raw_echo(n)
            return (f"{subj} {falls} between "
                    f"{_operand_phrase(n.operands[0], meanings)} and "
                    f"{_operand_phrase(n.operands[1], meanings)}")
        cols = [c for c in n.columns if c]
        if len(cols) >= 3:
            return (f"{meaning_of(cols[0], meanings)} {falls} between "
                    f"{meaning_of(cols[1], meanings)} and "
                    f"{meaning_of(cols[2], meanings)}")
    if op in ("LIKE", "NOT_LIKE"):
        if subj is None or not n.operands:
            return _raw_echo(n)
        return f"{subj} {_pattern_phrase(n.operands[0], op == 'NOT_LIKE')}"
    if op in ("IS", "IS_NOT"):
        if subj is None:
            return _raw_echo(n)
        return (f"{subj} is "
                f"{'recorded' if op == 'IS_NOT' else 'not recorded'}")
    if op == "EXISTS":
        # dict.fromkeys: both sides of a correlation key usually carry
        # the SAME meaning — '(patient id, patient id)' is a stutter
        what = ", ".join(dict.fromkeys(
            meaning_of(c, meanings)
            for c in n.columns[:2])) or "the linked records"
        # 3b (09-04): name the record by the inner table's DICTIONARY
        # meaning where one exists ('a primary-care assignment record
        # exists for the patient'); the dictionary-less fallback
        # keeps the generic phrasing. Documented meanings only — the
        # readable-name fallback would splice a raw-ish table name
        # into steward prose.
        inner = getattr(n, "inner_table", None) or ""
        tm = (meanings or {}).get(inner.upper()) or (
            meanings or {}).get(inner)
        if tm and tm.strip():
            record = tm.strip().split(". ")[0].rstrip(".").strip()
            return f"a {record} record exists for {what}"
        return f"a matching record exists ({what})"
    if op == "PARAMETER_DEFAULT":
        # Sunny's 08-19 ruling: parameter-defaulting IF blocks exist
        # so descriptions can voice them. Operands hold the @variable
        # and the default literal(s) from the walked SET branches.
        params = list(dict.fromkeys(
            str(o).lstrip("@") for o in n.operands
            if str(o).startswith("@")))
        values = [str(o) for o in n.operands
                  if not str(o).startswith("@")]
        if params and values:
            return (f"{meaning_of(params[0], meanings)} defaults to "
                    f"{values[0]} when no value is supplied")
        if params:
            return (f"a default value is applied to "
                    f"{meaning_of(params[0], meanings)} when none "
                    f"is supplied")
        return _raw_echo(n)
    # Unknown shape: the verbatim expression IS grounded — quote it.
    return _raw_echo(n)


def _render(n, meanings) -> "list[str]":
    """A boolean subtree -> bullet phrases, SHAPE-PRESERVING: an OR is
    ONE phrase (splitting it into bullets silently turns it into an
    AND — the LDA lesson at composer grain)."""
    if n.kind == "predicate":
        if not n.must_voice:
            # WHERE 1=1 scaffolding: extracted and counted, decides
            # nothing — voicing it would raw-echo into a gate kill
            # that empties the whole step (OP-FRONTIER-1 live find)
            return []
        ph = _leaf_phrase(n, meanings)
        return [ph] if ph else []
    if n.kind == "and":
        out: "list[str]" = []
        for c in n.children:
            out.extend(_render(c, meanings))
        return out
    if n.kind == "or":
        parts: "list[str]" = []
        for c in n.children:
            parts.extend(_render(c, meanings))
        return [" or ".join(parts)] if parts else []
    if n.kind == "not":
        inner = [p for c in n.children for p in _render(c, meanings)]
        if (len(n.children) == 1 and n.children[0].kind == "predicate"
                and n.children[0].op == "EXISTS"):
            # every EXISTS phrase starts 'a … exists' by construction
            # (generic or dictionary-named), so negation is uniform:
            # 'a X record exists…' -> 'no X record exists…'
            if inner and inner[0].startswith("a "):
                return ["no " + inner[0][2:]]
            return inner
        return [f"it is not the case that {p}" for p in inner]
    return []


def compose_skeleton(fragment: str,
                     meanings: "dict[str, str] | None" = None) -> str:
    """DESC-SKELETON-3 (the ruled re-cut, ADR 0074): the deterministic
    composition, AST-FIRST — the composer consumes the faithful
    decision tree (ScriptDom, scope-aware), never regex over SQL text
    (GATE-REGEX-1; the regex composer's four decoy-class defects and
    the derived-table leak are pinned in test_skeleton_composer).

    Scope law (DESC-SKELETON-3a): only OUTER-scope sites are this
    step's claims — a filter inside a derived table or subquery is
    THAT selection's decision, not this step's. case_when sites are
    projection choices, never membership conditions (decoy 4); the
    translate path's ledger still voices them (0044 clause 5)."""
    from src.tree.extract import query_shape
    shape = query_shape(fragment or "")
    # Report-review 3a (09-04): a no-table step must not open with
    # 'This is a selection of records' — the lead IS the
    # derived-values fact, instead of contradicting it one bullet
    # later ('Constant' corpus find).
    if shape.parse_ok and not shape.base_tables:
        lines = ["This step produces derived values; no source "
                 "records are read."]
    else:
        lines = [f"This is a selection of {subject_for(fragment or '')}."]
    try:
        tree = build_decision_tree(fragment or "")
    except Exception:  # noqa: BLE001 — no parse, no claims: the lead
        return "\n".join(lines)  # line alone is still grounded & true
    seen: "set[str]" = set()
    for site in tree.sites:
        if site.scope != "outer" or site.context == "case_when":
            continue
        for ph in _render(site.root, meanings):
            text = f"- {ph}."
            if text not in seen:
                seen.add(text)
                lines.append(text)
    if not tree.sites and not tree.unextracted:
        # DESC-LEAF-1 (the Passthrough grade): ZERO decision sites at
        # ANY scope is itself a voicable, grounded fact — 'a
        # collection of records' said nothing. Any-scope on purpose:
        # a filter in a derived table would make 'no filtering
        # conditions' read as a lie to a human, whoever's claim it is.
        # (The no-table fact now lives in the LEAD — 3a — so only
        # table-reading steps need the bullet.)
        if shape.parse_ok and shape.base_tables:
            lines.append(
                "- No filtering conditions are applied in this step.")
    return "\n".join(lines)


_SMOOTH_PROMPT = """Rewrite the statement below as fluent English
for a business steward.

RULES — this is a REPHRASING, not a rewrite:
- Keep every value, condition and subject EXACTLY as given.
- Add NOTHING: no new conditions, no values not listed, no purpose
  or benefit, no explanation of why it matters.
- Drop nothing: every bullet must survive as a statement.
- Do not name tables, columns, temp tables, joins or queries.

STATEMENT:
{skeleton}"""


@dataclass
class StepDescription:
    text: str = ""
    source: str = "skeleton"      # "smoothed" | "skeleton"
    undocumented: "list[str]" = field(default_factory=list)
    violations: "list[str]" = field(default_factory=list)


def describe_step(
    fragment: str, meanings: "dict[str, str] | None" = None,
    smooth: "Callable[[str], str] | None" = None,
) -> StepDescription:
    """DESC-MEANING-1 steps 3-5: compose the skeleton
    deterministically, let the model SMOOTH it, and keep the smoothed
    text only if it still passes the accuracy gate. Otherwise THE
    SKELETON SHIPS — plain but true.

    The skeleton is the floor, so this never returns empty. That is
    the constructive answer to the empties ruling: absence was only
    ever the least-bad option when the alternative was fabrication;
    with a grounded skeleton available, neither is needed."""
    skeleton = compose_skeleton(fragment, meanings)
    undoc = undocumented_columns_from(fragment, meanings)
    if smooth is None:
        return StepDescription(skeleton, "skeleton", undoc, [])
    try:
        candidate = str(smooth(_SMOOTH_PROMPT.format(
            skeleton=skeleton)) or "").strip()
    except Exception:  # noqa: BLE001 - deliberate: see below
        # BROAD ON PURPOSE. Any failure in the smoothing call —
        # timeout, auth, rate limit, malformed response — must
        # degrade to the grounded skeleton, never cost the
        # description. Narrowing this would trade a guaranteed floor
        # for an unhandled class of outage.
        return StepDescription(skeleton, "skeleton", undoc, [])
    if not candidate:
        return StepDescription(skeleton, "skeleton", undoc, [])
    violations = grounding_violations(candidate, fragment)
    if violations:
        return StepDescription(skeleton, "skeleton", undoc, violations)
    return StepDescription(candidate, "smoothed", undoc, [])


def undocumented_columns_from(
    fragment: str, meanings: "dict[str, str] | None" = None,
) -> "list[str]":
    """Referenced columns with no documented meaning — the reported
    coverage gap (Sunny's fallback ruling), now keyed off the
    meanings map rather than dictionary text lines."""
    have = {k.upper() for k in (meanings or {})}
    return sorted(parsed_columns(fragment) - have)


def grounding_violations(
    text: str, fragment: str, dict_lines: "list[str] | None" = None,
    dialect: str = "sql", voice: bool = True,
) -> "list[str]":
    """Deterministic checks of a generated description against the ONE
    source it claims to describe. Returns human-readable violations;
    empty list = grounded.

    dialect: "sql" applies the full check set. "dax"/"prose" skip the
    selected-not-filtered heuristic — it reads SQL structure (WHERE/ON
    windows vs SELECT list), which does not exist in a DAX expression
    or in composed prose (field find, tenant 600 run 2026-08-20: a
    legitimate CALCULATE filter was stripped as 'selected-not-
    filtered' until the whole description emptied). Value grounding
    (checks 1) applies to every dialect."""
    violations: "list[str]" = []
    ground = (fragment or "") + "\n" + "\n".join(dict_lines or [])
    ground_low = ground.lower()
    if dialect != "sql":
        conditions = ground_low
    else:
        # OUTER-scope deciding facts from the tree (the gate recut):
        # the 240-char keyword windows are gone, and a derived
        # table's text no longer counts as this step's deciding
        # evidence — the 3a scope law on the checker side.
        from src.tree.extract import query_shape
        conditions = " ".join(
            query_shape(fragment or "").deciding_exprs).lower()
        # Meanings bridge (09-03): a DECIDING column's dictionary
        # words count as condition vocabulary — the composer voices
        # meanings, so the checker must read them. A SELECT-only
        # column's meaning is deliberately NOT added: claiming it
        # filters stays a violation (role-faithful, not a loosening).
        for name, desc in _dict_meanings(dict_lines).items():
            if name.lower() in conditions:
                conditions += " " + desc.lower()

    # 1) every literal value in the output must exist in the source.
    # The composer's own elision idiom is exempt: in 'one of 25 values
    # from X to Y' the 25 is COUNTED from the SQL's own list, true by
    # construction, not a literal (09-03 estate find: the gate emptied
    # a step over its own composed count).
    elision_counts = set(_ELISION_COUNT.findall(text))
    for num in set(_OUT_NUMBERS.findall(text)):
        if num not in ground and num not in elision_counts:
            violations.append(f"ungrounded value: {num!r} not in the SQL")
    for quoted in set(_OUT_QUOTED.findall(text)):
        toks = _OUT_NUMBERS.findall(quoted)
        probe = toks[0] if toks else quoted
        if probe and probe.lower() not in ground_low:
            violations.append(f"ungrounded value: '{quoted}' not in the SQL")

    # 2) filter-claims need support in the DECIDING part of the SQL
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("- ") or not _FILTER_CLAIM.search(line):
            continue
        if _SUBQUERY_IDIOM.search(line) and "select" in conditions:
            # composed-by-construction: the idiom names no value and
            # is grounded whenever a subquery decides this step (the
            # elision-count exemption's pattern at sentence grain)
            continue
        terms = [w for w in re.findall(r"[a-z]{5,}", line.lower())
                 if w not in _CLAIM_STOPWORDS]
        if not terms:
            continue
        in_fragment = [w for w in terms if w in ground_low]
        in_conditions = [w for w in in_fragment if w in conditions]
        has_literal = any(n in ground for n in _OUT_NUMBERS.findall(line))
        if not in_fragment and not has_literal:
            violations.append(f"ungrounded filter claim: {line!r}")
        elif in_fragment and not in_conditions and not has_literal:
            violations.append(
                f"selected-not-filtered: {line!r} — the concept appears "
                f"only in the SELECT list, never in a condition")

    # 3) TABLE claims (P0-a): only tables the fragment reads
    # 4) GRAIN claims (P0-a): the counted entity must match the keys
    if dialect == "sql":
        violations.extend(_table_violations(text, fragment, dict_lines))
        violations.extend(_grain_violations(text, fragment))
        violations.extend(
            misattribution_violations(text, fragment, dict_lines))
        if voice:
            violations.extend(column_name_violations(text, fragment))
    # 5) VOICE (DESC-VOICE-1): audience, not accuracy — a steward's
    # field must not carry a developer's sentence. Skipped with
    # voice=False for MACHINE-COMPOSED text (the template fallback
    # is stilted truth by design; policing its voice would floor
    # the floor).
    if voice:
        violations.extend(voice_violations(text, fragment, dict_lines))
        violations.extend(purpose_violations(text, fragment))
        violations.extend(placeholder_violations(text))
    return violations


def enforce_grounding(
    text: str, fragment: str, dict_lines: "list[str] | None" = None,
    dialect: str = "sql",
) -> "tuple[str, list[str]]":
    """Surgical fallback after a failed retry: strip the violating
    lines, keep grounded content. If the remaining text still violates
    (bad summary sentence), drop everything — absence over fabrication.
    Returns (clean_text_or_empty, removed_violations)."""
    violations = grounding_violations(text, fragment, dict_lines, dialect)
    if not violations:
        return text, []
    bad_lines = {v.split(": ", 1)[1].split(" — ")[0].strip("'\"")
                 for v in violations if ": '" in v or ": \"" in v}
    kept = []
    for line in text.splitlines():
        if any(repr(line.strip()) == b or line.strip() == b.strip("'")
               for b in bad_lines):
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    if cleaned and not grounding_violations(cleaned, fragment, dict_lines,
                                            dialect):
        return cleaned, violations
    return "", violations


def line_level_kill(
    text: str, fragment: str, dict_lines: "list[str] | None" = None,
) -> "tuple[str, list[str], list[str]]":
    """0074 §5.3a-1 (Sunny, 2026-09-04): the kill unit is the
    SENTENCE. A voice/gate violation kills the violating LINE; the
    surviving true lines ship; every dropped line is counted by the
    caller. Returns (shipped_text, killed_line_texts, violations) —
    shipped_text == text and killed empty when nothing violates;
    shipped_text == "" when the step must empty.

    The step empties when no DECISION line ('- ' bullet) survives: a
    lead line alone is content-free filler (the Passthrough grade by
    another door), and the authored Case_Predicate 'emptied' answer
    stays the right answer. The ban itself never loosens — survivors
    are re-checked whole, and a set that still violates empties."""
    violations = grounding_violations(text, fragment, dict_lines)
    if not violations:
        return text, [], []
    kept: "list[str]" = []
    killed: "list[str]" = []
    for line in text.splitlines():
        if line.strip() and grounding_violations(line, fragment,
                                                 dict_lines):
            killed.append(line.strip())
        else:
            kept.append(line)
    shipped = "\n".join(kept).strip()
    if not any(ln.strip().startswith("- ") for ln in kept):
        return "", killed, violations
    if shipped and not grounding_violations(shipped, fragment,
                                            dict_lines):
        return shipped, killed, violations
    return "", killed, violations


def _cache_entry(entry) -> "tuple[str, str, int]":
    """Normalize a cache value at the boundary: (text, provenance,
    killed_lines) — written as a tuple, but ANY JSON round-trip
    returns a LIST; a v6 cache holds bare strings and a v7-v9 cache
    holds pairs. The generator lesson (second tuple-vs-JSON trap in
    one week): normalize where the data enters, not at each use
    site."""
    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
        killed = 0
        if len(entry) >= 3:
            try:
                killed = int(entry[2])
            except (TypeError, ValueError):
                killed = 0
        return str(entry[0]), str(entry[1]), killed
    return str(entry), "gate_passed", 0


def step_content_hash(fragment: str, dep_names: "list[str]",
                      dict_lines: "list[str] | None" = None) -> str:
    payload = (
        PROMPT_VERSION + "\n" + (fragment or "")
        + "\n--deps--\n" + "\n".join(sorted(dep_names))
        + "\n--dict--\n" + "\n".join(dict_lines or [])
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def measure_content_hash(name: str, expression: str,
                         dict_lines: "list[str] | None" = None) -> str:
    payload = (
        PROMPT_VERSION + "\n--measure--\n" + name + "\n" + (expression or "")
        + "\n--dict--\n" + "\n".join(dict_lines or [])
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def metric_content_hash(metric_name: str, roots: "list[tuple[str, str]]",
                        step_count: int, decision_count: int = 0) -> str:
    payload = (
        PROMPT_VERSION + "\n" + metric_name + f"\n{step_count}\n"
        + f"{decision_count}\n"
        + "\n".join(f"{n}\t{d}" for n, d in sorted(roots))
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


@dataclass
class DescriptionResult:
    descriptions: "dict[str, str]" = field(default_factory=dict)  # node_id -> text
    cache_hits: int = 0
    generated: int = 0
    failed: "list[str]" = field(default_factory=list)
    # (node_id, "reason_code: detail") — the WHY behind every failed
    # node, persisted to ops_fallout by 600 (field find 2026-08-20:
    # four failures whose causes existed only in printed output)
    failed_reasons: "list[tuple[str, str]]" = field(default_factory=list)
    vague: "list[str]" = field(default_factory=list)   # filler-word flags
    jargon: "list[str]" = field(default_factory=list)  # raw-identifier flags
    # grounding gate (2026-08-19): (node_id, violations) that survived a
    # corrective retry — the offending lines were stripped or the whole
    # description dropped; absence over fabrication.
    ungrounded: "list[tuple[str, list[str]]]" = field(default_factory=list)
    # (step_id, count): facts the translator failed to voice — their
    # lines came from the deterministic template floor (clause 5); the
    # text stays complete, the miss stays counted.
    unvoiced: "list[tuple[str, int]]" = field(default_factory=list)
    # ADR 0074 D1: node_id -> PROVENANCE value for every STORED
    # description; total over descriptions, closed vocabulary.
    provenance: "dict[str, str]" = field(default_factory=dict)
    # The empties-(a) ruling (0074 section 5.3a): voice/gate kill >
    # skeleton floor > absent. (step_id, violations) — ABSENT rows,
    # counted, never stored, never silent.
    emptied: "list[tuple[str, list[str]]]" = field(default_factory=list)
    # 0074 §5.3a-1 (kill unit = the SENTENCE, ruled 09-04): partial
    # ships — node_id -> count of dropped lines. Stored beside
    # provenance in the cache so a cached rerun reports the same
    # accounting; the dropped TEXT is never stored (absent lines are
    # counted, never kept). The failed/failed_reasons pattern:
    # killed_reasons carries this run's fresh kill violations for
    # ops_fallout.
    killed_lines: "dict[str, int]" = field(default_factory=dict)
    killed_reasons: "list[tuple[str, list[str]]]" = field(
        default_factory=list)
    # ADR 0074 D3 (DESC-FILE-1): the deliverable is a description per
    # SQL FILE — metric node_id -> text; coverage is measured in
    # files described. Multi-step files compose; single-statement
    # files describe their own block.
    file_descriptions: "dict[str, str]" = field(default_factory=dict)

    def fail(self, node_id: str, reason: str) -> None:
        self.failed.append(node_id)
        self.failed_reasons.append((node_id, reason))


def topological_step_order(nodes: dict, edges: list) -> "list[str]":
    """Transformation node_ids, every direct dependency before its dependent.

    DEPENDS_ON points dependent -> dependency, so emit in DFS post-order.
    Cycles (shouldn't exist; parser output is a DAG) are broken at the
    back-edge — the step is emitted once, grounded in its own fragment.
    """
    dependencies: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TRANSFORM:
            dependencies.setdefault(e.source_id, []).append(e.target_id)

    ordered: "list[str]" = []
    done: "set[str]" = set()
    in_progress: "set[str]" = set()

    def visit(node_id: str) -> None:
        if node_id in done or node_id in in_progress:
            return
        in_progress.add(node_id)
        for dep in dependencies.get(node_id, []):
            visit(dep)
        in_progress.discard(node_id)
        done.add(node_id)
        ordered.append(node_id)

    for node_id, node in sorted(nodes.items()):
        if node.layer == NodeLayer.TRANSFORMATION:
            visit(node_id)
    return ordered


MAX_DICT_LINES = 30


def meanings_for_step(
    step_id: str, nodes: dict, tech_map: "dict[str, list[str]]",
    columns_map: "dict[str, list[str]]", fragment: str,
) -> "dict[str, str]":
    """Column -> business meaning for the columns the fragment
    references — the skeleton composer's vocabulary (same selection
    rule as dictionary_for_step, keyed for composition).

    TABLE descriptions ride in the same map (3b, 09-04): the EXISTS
    phrase names the missing record by the inner TABLE's meaning,
    which the composer can only see if tables are vocabulary too."""
    frag = (fragment or "").lower()
    meanings: "dict[str, str]" = {}
    for table_id in tech_map.get(step_id, []):
        table = nodes.get(table_id)
        if (table is not None and (table.description or "").strip()
                and table.name.lower() in frag):
            meanings[table.name.upper()] = table.description.strip()
        for col_id in columns_map.get(table_id, []):
            col = nodes.get(col_id)
            if col is None or not (col.description or "").strip():
                continue
            if col.name.lower() in frag:
                meanings[col.name.upper()] = col.description.strip()
    return meanings


def dictionary_for_step(
    step_id: str, nodes: dict, tech_map: "dict[str, list[str]]",
    columns_map: "dict[str, list[str]]", fragment: str,
) -> "list[str]":
    """Dictionary lines for the tables a step touches, plus only the
    COLUMNS the fragment actually references (whole-table column lists
    would drown the prompt). Pure selection — the dictionary text
    itself is the customer's own, from graph_nodes."""
    frag = (fragment or "").lower()
    lines: "list[str]" = []
    for table_id in sorted(tech_map.get(step_id, [])):
        table = nodes.get(table_id)
        if table is None:
            continue
        if (table.description or "").strip():
            lines.append(f"- {table.name}: {table.description.strip()}")
        for col_id in sorted(columns_map.get(table_id, [])):
            col = nodes.get(col_id)
            if col is None or not (col.description or "").strip():
                continue
            if col.name.lower() in frag:
                lines.append(f"  - {col.name}: {col.description.strip()}")
    return lines


def build_measure_prompt(
    name: str, expression: str, expression_type: str,
    report_name: str, dict_lines: "list[str] | None" = None,
) -> str:
    if dict_lines:
        entries = "\n".join(dict_lines[:MAX_DICT_LINES])
        dict_block = (
            "Data dictionary for the columns this DAX references "
            f"(translate identifiers using these):\n{entries}\n\n"
        )
    else:
        dict_block = ""
    return MEASURE_PROMPT.format(
        name=name, expression=expression or "(none)",
        expression_type=("calculated column" if expression_type == "calculated_column"
                         else "measure"),
        report_name=report_name or "(unknown)", dict_block=dict_block,
    )


def build_metric_prompt(metric_name: str, roots: "list[tuple[str, str]]",
                        step_count: int, decision_count: int = 0) -> str:
    roots_block = "\n".join(f"- {n}: {d}" for n, d in roots) or "- (no described steps)"
    return METRIC_PROMPT.format(
        metric_name=metric_name, roots_block=roots_block,
        step_count=step_count, decision_count=decision_count,
    )


# Walk corpse (Sunny, 2026-08-21 evening — find 2): metric
# descriptions claimed "without applying any filtering decisions" on
# metrics carrying HUNDREDS of decision sites (427 on
# USP_Severe_Sepsis) — the final_select step's true no-WHERE fact
# over-scoped to the whole metric, and the engine faithfully repeated
# the poisoned text. Sunny's rule: a metric-grain description may not
# make absence-of-filtering claims scoped beyond its step; when
# decision sites exist, the description voices their existence and
# count.
_ABSENCE_OF_FILTERING = re.compile(
    r"(?i)\b(?:without|no|not)\b[^.\n]{0,60}?\bfilter")


def metric_scope_violations(text: str, decision_count: int) -> "list[str]":
    """Deterministic metric-grain scope check (find 2). Empty list =
    no over-scoped absence claim."""
    if decision_count <= 0:
        return []
    out = []
    for line in text.splitlines():
        if _ABSENCE_OF_FILTERING.search(line):
            out.append(
                f"over-scoped absence claim: {line.strip()!r} — this "
                f"metric carries {decision_count} decision sites; an "
                "absence-of-filtering fact is true only of a single "
                "step, never of the metric")
    return out



_RETRY_NOTE = (
    "\n\nYour previous draft was REJECTED by an automatic grounding "
    "check for these violations:\n{violations}\n"
    "Rewrite it. Every value must appear in the SQL above; describe a "
    "column as a filter ONLY if it appears in a WHERE / JOIN ON / "
    "HAVING / CASE WHEN condition; name ONLY tables the SQL reads; "
    "state the counted entity ONLY as the key columns define it "
    "(do not say patients when the row is a visit); write for a "
    "STEWARD, not a developer — never mention tables, temp tables, "
    "joins, columns, queries or datasets, and never expand an "
    "acronym the source does not expand; drop any claim you cannot "
    "ground."
)


def _grounded_describe(
    describe, prompt: str, fragment: str,
    dict_lines: "list[str] | None", dialect: str = "sql",
) -> "tuple[str, list[str]]":
    """describe() + gate + ONE corrective retry + surgical fallback.
    Returns (text_or_empty, violations_removed)."""
    text = describe(prompt).strip()
    if not text:
        return "", []
    violations = grounding_violations(text, fragment, dict_lines, dialect)
    if not violations:
        return text, []
    note = _RETRY_NOTE.format(
        violations="\n".join(f"- {v}" for v in violations))
    try:
        retry = describe(prompt + note).strip()
    except Exception:  # noqa: BLE001 — retry is best-effort
        retry = ""
    if retry:
        text = retry
    return enforce_grounding(text, fragment, dict_lines, dialect)


def generate_descriptions(
    nodes_rows: "list[dict]",
    edges_rows: "list[dict]",
    describe: "Callable[[str], str]",
    cache: "dict[str, str] | None" = None,
) -> DescriptionResult:
    """Walk the DAG bottom-up; describe steps, then compose metrics.

    cache maps content_hash -> description and is mutated in place — the
    caller persists it (Delta table on Fabric, JSON locally). The cache
    is the ONLY regeneration authority: keys include PROMPT_VERSION and
    the exact inputs, so a description regenerates precisely when its
    SQL, its dependencies, or the prompt changed — an existing text on
    the node never blocks an upgrade from reaching it.
    """
    nodes = rows_to_nodes(nodes_rows)
    edges = rows_to_edges(edges_rows)
    cache = cache if cache is not None else {}
    result = DescriptionResult()

    dep_map: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TRANSFORM:
            dep_map.setdefault(e.source_id, []).append(e.target_id)
    roots_map: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.CANONICAL_TO_TRANSFORM:
            roots_map.setdefault(e.source_id, []).append(e.target_id)
    tech_map: "dict[str, list[str]]" = {}       # step -> touched tables
    columns_map: "dict[str, list[str]]" = {}    # table -> its columns
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TECHNICAL:
            tech_map.setdefault(e.source_id, []).append(e.target_id)
        elif e.edge_type == EdgeType.TABLE_TO_COLUMN:
            columns_map.setdefault(e.source_id, []).append(e.target_id)

    described: "dict[str, str]" = {}

    for step_id in topological_step_order(nodes, edges):
        node = nodes[step_id]
        fragment = node.properties.get("sql_fragment", "")
        dep_names = [nodes[d].name for d in dep_map.get(step_id, []) if d in nodes]
        dict_lines = dictionary_for_step(
            step_id, nodes, tech_map, columns_map, fragment)
        key = step_content_hash(fragment, dep_names, dict_lines)
        if key in cache:
            text, prov, killed_n = _cache_entry(cache[key])
            described[step_id] = text
            result.descriptions[step_id] = text
            result.provenance[step_id] = prov
            if killed_n:
                result.killed_lines[step_id] = killed_n
            result.cache_hits += 1
            continue
        try:
            # ADR 0074 acceptance (the ratified field architecture):
            # deterministic skeleton from the tree (translator
            # blindness by construction — the smooth prompt carries
            # ONLY the skeleton, never SQL), one smoothing attempt,
            # gate on the candidate, SKELETON FLOOR on violation.
            meanings = meanings_for_step(
                step_id, nodes, tech_map, columns_map, fragment)
            sd = describe_step(fragment, meanings, smooth=describe)
            text = sd.text
        except Exception as err:  # noqa: BLE001 — one bad step must not kill the batch
            result.fail(step_id, f"generation_error: {type(err).__name__}: {err}"[:300])
            continue
        if sd.source == "skeleton":
            # empties-(a) precedence: voice/gate kill > skeleton >
            # absent — at SENTENCE grain (0074 §5.3a-1): the
            # violating line dies, survivors ship, every drop is
            # counted; the step empties only when no decision line
            # survives.
            shipped, killed, kill = line_level_kill(
                text, fragment, dict_lines)
            if kill and not shipped:
                result.emptied.append((step_id, kill))
                continue
            if killed:
                result.killed_lines[step_id] = len(killed)
                result.killed_reasons.append((step_id, kill))
                text = shipped
            prov = "skeleton_floor"
        else:
            prov = "gate_passed"
        if sd.violations:
            # the smoothing candidate's violations — the skeleton
            # shipped instead; the catch stays counted
            result.ungrounded.append((step_id, sd.violations))
        if _VAGUE_FILLERS.search(text):
            result.vague.append(step_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(step_id)
        cache[key] = (text, prov, result.killed_lines.get(step_id, 0))
        described[step_id] = text
        result.descriptions[step_id] = text
        result.provenance[step_id] = prov
        result.generated += 1

    # Measures (ADR 0040): DAX is business logic — same treatment as SQL
    # steps. Independent of the step DAG; grounded in its own expression
    # plus the dictionary text of the columns it provably references
    # (MEASURE_TO_COLUMN edges — resolved, never guessed).
    measure_cols: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.MEASURE_TO_COLUMN:
            measure_cols.setdefault(e.source_id, []).append(e.target_id)

    for node_id, node in sorted(nodes.items()):
        if node.layer != NodeLayer.MEASURE:
            continue
        expression = node.properties.get("dax_expression", "")
        if not expression:
            result.fail(node_id, "no_dax_expression: measure ingested "
                                 "without an expression")
            continue
        dict_lines = []
        for col_id in sorted(measure_cols.get(node_id, [])):
            col = nodes.get(col_id)
            if col is not None and (col.description or "").strip():
                dict_lines.append(f"- {col.name}: {col.description.strip()}")
        key = measure_content_hash(node.name, expression, dict_lines)
        if key in cache:
            m_text, m_prov, _mk = _cache_entry(cache[key])
            result.descriptions[node_id] = m_text
            result.provenance[node_id] = m_prov
            result.cache_hits += 1
            continue
        prompt = build_measure_prompt(
            node.name, expression,
            node.properties.get("expression_type", "measure"),
            node.properties.get("report_name", ""), dict_lines,
        )
        try:
            text, removed = _grounded_describe(
                describe, prompt, expression, dict_lines, dialect="dax")
        except Exception as err:  # noqa: BLE001 — one bad measure must not kill the batch
            result.fail(node_id, f"generation_error: {type(err).__name__}: {err}"[:300])
            continue
        if removed:
            result.ungrounded.append((node_id, removed))
        if not text:
            result.fail(node_id, "grounded_to_empty: every generated line "
                                 "failed the grounding check")
            continue
        if _VAGUE_FILLERS.search(text):
            result.vague.append(node_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(node_id)
        cache[key] = (text, "gate_passed", 0)
        result.descriptions[node_id] = text
        result.provenance[node_id] = "gate_passed"
        result.generated += 1

    # Metrics: composed from ROOT step descriptions (raw roots-only edges)
    step_count_by_metric: "dict[str, int]" = {}
    decision_count_by_metric: "dict[str, int]" = {}
    for node_id, node in nodes.items():
        if node.layer == NodeLayer.TRANSFORMATION:
            metric_id = node.properties.get("metric_id", "")
            step_count_by_metric[metric_id] = step_count_by_metric.get(metric_id, 0) + 1
        elif node.layer == NodeLayer.DECISION:
            metric_id = node.properties.get("metric_id", "")
            decision_count_by_metric[metric_id] = (
                decision_count_by_metric.get(metric_id, 0) + 1)

    for node_id, node in sorted(nodes.items()):
        if node.layer != NodeLayer.CANONICAL:
            continue
        metric_id = node_id.replace("canonical:", "")
        # ADR 0074 D3: compose from TERMINAL steps — the steps no
        # other step of this metric depends on, CTE or temp alike.
        # 0019's "root CTEs" premise broke on the real estate (23/28
        # procs stage through temp tables). Edge-derived roots remain
        # the fallback where the dep graph is absent.
        metric_steps = [
            sid for sid, n in nodes.items()
            if n.layer == NodeLayer.TRANSFORMATION
            and n.properties.get("metric_id", "") == metric_id
        ]
        depended = {t for s in metric_steps for t in dep_map.get(s, [])}
        terminals = [s for s in metric_steps if s not in depended]
        source_steps = terminals or roots_map.get(node_id, [])
        roots = [
            (nodes[r].name, described.get(r, ""))
            for r in source_steps if r in nodes
        ]
        if not roots:
            # DESC-FILE-1: a no-step file is ONE BLOCK — describe its
            # own statement (minted by 300 onto the canonical node).
            frag = node.properties.get("sql_fragment", "")
            if frag:
                try:
                    sd = describe_step(frag, None, smooth=describe)
                except Exception as err:  # noqa: BLE001 — one bad file, not the batch
                    result.fail(node_id,
                                f"generation_error: {type(err).__name__}: {err}"[:300])
                    continue
                if sd.source == "skeleton":
                    # §5.3a-1 sentence-grain kill, same as the step
                    # loop — the no-roots file path is the same
                    # acceptance
                    shipped, killed, kill = line_level_kill(
                        sd.text, frag)
                    if kill and not shipped:
                        result.emptied.append((node_id, kill))
                        continue
                    if killed:
                        result.killed_lines[node_id] = len(killed)
                        result.killed_reasons.append((node_id, kill))
                        sd.text = shipped
                    prov = "skeleton_floor"
                else:
                    prov = "gate_passed"
                result.descriptions[node_id] = sd.text
                result.provenance[node_id] = prov
                result.file_descriptions[node_id] = sd.text
                result.generated += 1
                continue
            result.fail(node_id, "no_root_steps: metric node has no "
                                 "steps and no stored statement to "
                                 "describe from")
            continue
        step_count = step_count_by_metric.get(metric_id, len(roots))
        decision_count = decision_count_by_metric.get(metric_id, 0)
        key = metric_content_hash(node.name, roots, step_count,
                                  decision_count)
        if key in cache:
            m_text, m_prov, _mk = _cache_entry(cache[key])
            result.descriptions[node_id] = m_text
            result.provenance[node_id] = m_prov
            result.file_descriptions[node_id] = m_text
            result.cache_hits += 1
            continue
        prompt = build_metric_prompt(node.name, roots, step_count,
                                     decision_count)
        roots_ground = "\n".join(d for _, d in roots)
        # Facts WE put in the prompt are grounded by definition — the
        # gate greps only roots_ground, so the step_count it asked the
        # LLM to voice ('computed in 122 steps') must be in the ground
        # (field find, tenant 600 run 2026-08-20).
        prompt_facts = ([node.name, str(step_count), str(decision_count)]
                        + [n for n, _ in roots])
        try:
            text, removed = _grounded_describe(
                describe, prompt, roots_ground, prompt_facts,
                dialect="prose")
        except Exception as err:  # noqa: BLE001
            result.fail(node_id, f"generation_error: {type(err).__name__}: {err}"[:300])
            continue
        if removed:
            result.ungrounded.append((node_id, removed))
        if not text:
            result.fail(node_id, "grounded_to_empty: every generated line "
                                 "failed the grounding check")
            continue
        # Metric-grain scope rule (walk find 2, Sunny 2026-08-21): one
        # corrective retry, then strip the violating lines; if the
        # remainder still over-scopes, drop the description entirely —
        # absence over poisoned certainty.
        scope_v = metric_scope_violations(text, decision_count)
        if scope_v:
            note = ("\n\nYour previous draft was REJECTED: it makes "
                    "absence-of-filtering claims at metric grain:\n"
                    + "\n".join(f"- {v}" for v in scope_v)
                    + "\nRewrite it without any such claim; say the "
                    "detailed criteria live in the "
                    f"{decision_count} decision sites.")
            try:
                retry = describe(prompt + note).strip()
            except Exception:   # noqa: BLE001 — retry is best-effort
                retry = ""
            if retry and not grounding_violations(
                    retry, roots_ground, prompt_facts, "prose"):
                text = retry
            if metric_scope_violations(text, decision_count):
                kept = [ln for ln in text.splitlines()
                        if not _ABSENCE_OF_FILTERING.search(ln)]
                text = "\n".join(kept).strip()
            result.ungrounded.append((node_id, scope_v))
            if not text or metric_scope_violations(text, decision_count):
                result.fail(node_id,
                            "over_scoped_absence: metric-grain "
                            "no-filtering claim survived retry+strip")
                continue
        if _VAGUE_FILLERS.search(text):
            result.vague.append(node_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(node_id)
        cache[key] = (text, "gate_passed", 0)
        result.descriptions[node_id] = text
        result.provenance[node_id] = "gate_passed"
        # the composed metric description IS the file description
        # (DESC-FILE-1: multi-step files compose from steps)
        result.file_descriptions[node_id] = text
        result.generated += 1

    return result
