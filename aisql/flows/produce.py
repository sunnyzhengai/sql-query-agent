"""Outward stage 1: PRODUCE — graph -> layer-3 machine versions.

The floor composer implements the RATIFIED Floor Grammar
(AIVIA_Design/Grammar_Floor.md, FLOOR_GRAMMAR_VERSION) rule by rule; the grammar version
stamps into every run's basis. The staleness lens IS the worklist
(PROD-2) — nobody hand-picks; ECON v1 (aisql/flows/econ_params.json,
ruled 2026-09-05) paces it: batch, budget, usage-weighted priority
(an empty ledger degrades to worklist order — declared, not silent).

Deterministic composition + bounded smoothing + the gate: the model
never adds a fact; on gate failure or no model THE FLOOR SHIPS
(skeleton_floor — plain but true). Per-artifact atomicity (OPS-2):
one append or a counted absence, never a half-write.
"""
import functools
import json
import pathlib
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from aisql.flows import gates, run_events
from aisql.graph import kg3_artifacts
from aisql.graph.read_api import ReadApi
from aisql.lenses import anchors, decisions, derivation

ECON = json.loads((pathlib.Path(__file__).parent / "econ_params.json")
                  .read_text())
# 2.0.0 (Phase C, ADR 0077): the POLICY-WALK major — the spine reads
# the meaning twin (composition sentence from source nodes; the
# voicing ledger); leaf voicings survive verbatim (ruling 4b). The
# 24-hour-window bound gains the DATEADD phrase (ADR 0076's
# evidence-ordered overlay: 12 estate uses ordered it) — the line-83
# raw-token corpse from Sunny's gap-check dies here.
# 2.2.0: the ABX FIRST LEG (Sunny): IN/EXISTS subselections voice
# their aggregate reads + restrictive-spine conditions (nested
# membership; OUTER-APPLY interiors and combination arms excluded).
# 2.1.0: the ABX corpse (Sunny's Phase-C gap-check find) — a UNION
# CTE floored as 'no source records are read': COMBINATION scopes now
# map (arms in order, dedup flag), voice per arm, and an unmapped
# query shape floors as its honest counted state, never a claim.
# 2.3.0: R10 — THE REPORT FLOOR (live find #9): file floors compose
# from scopes — deliveries lead, spine voiced, intermediates counted,
# census closes; file ask-index words = the delivery lead.
# 2.5.0: NOT FOLDS INTO ITS CHILD (Sunny's ruling 2026-09-12) —
# per-kind negations from the closed set (_voice_negated); the
# condition store nodes inherit the fold at condition_render.
# (The 2.4.0 doc bump had missed this constant — 2.3.0 while the
# doc said 2.4.0; caught and closed in the same 2.5.0 breath.)
# 2.6.0: RECORDEDNESS IDENTIFIES (Sunny's go, same day, from "what
# is the best translation for MA.TAKEN_TIME IS NOT NULL"): the
# NULL_CHECK family speaks "is recorded"/"is not recorded" with a
# NAME-WORDS subject (_ident_subject) — identification, never
# definition; the owner-possessive and the business reading are
# recorded deferrals (blessed-vocabulary wiring · the blessing
# path).
# 2.7.0: THE RELATION RULE + the token-link reduction + noted
# annotations (Sunny, same day: cond#8/cond#9 "still not fixed"):
# column-vs-column comparisons speak name words BOTH sides
# (_compare_terms — the mixed-register corpse); '<qualifier>
# <token> associated with <the thing>' subjects speak the thing;
# a predicate's trailing SQL note reaches the store phrase
# ("is 11 (noted 'intravenous')").
# 2.8.0: R5.b THE BLESSED NAME (ratified 2026-09-12, built same
# day — the declared constant deferral closes here, in the
# build's first slice as ruled): blessed_name nodes (kg3@, seeded
# from glossary/blessed_subjects.json, GATE-SUBJ gated, human-
# blessed) win EVERY voicing position for their target — column
# subjects (_Voice.subject), name-words register (name_words:
# recordedness + relation sides), table source phrases
# (_source_phrase) + R2 instance marking. Unblessed = 2.7.0
# verbatim (A1); the proposer batch waits on riders (c)/(d).
# 2.9.0: R5.c THE OWNER-POSSESSIVE (Sunny's "go with your
# recommendations", 2026-09-14 — the v2.6.0 deferral closes):
# recordedness subjects speak the blessed OWNER table
# possessively ("the medication administration's taken time") —
# recordedness only, always-when-blessed, 's on every head, no
# stutter guard (the smell census is the eye). Unblessed owner =
# 2.8.0 verbatim (A1).
# 2.10.0: R12 THE COMPUTED OUTPUT (ratified Sunny 2026-09-16,
# "ratified — go on M4"; the declared constant deferral closes
# here, the M4 build's first slice as ruled): derived_column
# descriptions = name words + the defining phrase, voiced
# inside-out through THE FUNCTION-VOICING LIBRARY
# (kg2_kind_library Function_Voicings — FN_SKELETONS is the
# code mirror, test-locked). Composite kinds by rule: case
# standing phrase · cast TRANSPARENT · unary sign-fold ·
# arithmetic operator words. Unlisted operation = safe fallback
# + counted remainder (voice.function_remainders). The ADR 0076
# value() overlays (COALESCE/LEFT/RIGHT/DATEADD) absorb into
# _fill_overlay — condition-context phrases BYTE-IDENTICAL (A1).
# 2.11.0: R11 THE STATEMENT STEP (ratified Sunny 2026-09-17, the
# 36 gap-checked at the M5 checkpoint): statement_phrase — the
# closed Statement_Voicings library; operational + unlisted
# kinds speak NOTHING (the (b) ruling).
# 2.12.0: R13 THE CATCH-ALL (ratified Sunny 2026-09-17, the real
# USP render gap-checked; "all three" checkpoint rulings):
# inbound._render_technical_definition — Presents (top-level) +
# grouped Population filters (degenerates pruned, recursion
# full) + Inner joins; the file grain's governance field.
# 2.14.0: R14 THE BUSINESS TERM SENTENCE (Brief_Pilot_Build_3,
# Sunny "approved, build brief 3" 2026-09-20; rulings (1)-(3),
# (10) + Q1-Q5 "agree with all five"): the scope's stored
# description becomes ONE sentence — grain-or-base lead (GROUP
# BY / DISTINCT / the rank-filter partition, slice E's capture),
# membership (inner joins, ON residues riding parenthetically),
# population (every WHERE; join keys and degenerates excluded;
# long value lists compress to a count — the full list stays on
# the condition rows; identical-subject betweens merge), payload
# (the dcols by name, then the carried-through count). Replaces
# the from-structure lead FOR SCOPES ONLY. RIDERS: R11 gains the
# temp-table-existence guard idiom (then_kind evidence) + the Q5
# render-join (statement_display — derivable, stored never);
# R12's ROW_NUMBER partition/order deferral CLOSES (the slotted
# phrase, FL17's echo-mandated acceptance).
# v2.15.0 (Brief_Pilot_Build_2 slice C, Sunny "agree with all
# seven recommendations, build it" 2026-09-20): R15 THE VOICING
# REPAIRS — the two-sided relation names both owners (FL9); the
# temporal-window idiom + one-library-two-readers (FL10); the
# pack ladder's convention rung (FL11, ruling (6)); LAG/LEAD slot
# forms (FL14); the pair words (FL18); the noun-phrase gate
# (FL19). The NOT fold and the select_refs skip land in the
# inbound walkers (ruling (9), FL13).
FLOOR_GRAMMAR_VERSION = "2.15.0"
# literal: grammar Grammar_Floor R1
_PREPOSITIONS = ("of", "on", "per", "for", "in", "at", "by", "with")
# rider (c) amended (Sunny 2026-09-13): the dictionary's declared
# type is temporal truth. T-SQL timestamp/rowversion is NOT here —
# it is a version counter, not a moment.
# literal: grammar Grammar_Floor R5.b rider (c)
_TEMPORAL_TYPES = frozenset(("date", "datetime", "datetime2",
                             "smalldatetime", "datetimeoffset",
                             "time"))


# ---- R5: steward words, graph-sourced (v1.3.1 rendering) ----
_BOILERPLATE = re.compile(
    r"(?i)^this\s+(?:column|item|field|table)\s+"
    r"(?:holds|contains|stores|indicates|captures|is)"
    r"(?:\s+details|\s+information)?(?:\s+about)?\s+")
# literal: grammar Grammar_Floor R5
_TOKEN_HEADS = {"id", "code", "number", "identifier", "key", "nbr"}
# R15.g THE NOUN-PHRASE GATE (v2.15.0, FL19 C1): a description
# leading with one of these is not a noun phrase — it falls to
# the identifier tier (through the R15.c ladder), never a broken
# pass-through. Growing this list is a grammar amendment.
# literal: grammar Grammar_Floor R15.g
_NON_NOUN_LEADS = frozenset((
    "stores", "contains", "indicates", "captures", "specifies",
    "denotes", "determines", "identifies", "defines", "describes",
    "displays", "shows", "lists", "links", "holds", "provides",
    "tracks", "records", "flags", "marks", "represents",
    "references", "returns", "reflects", "gives", "allows",
    "enables", "includes", "applies", "associates",
    "you", "your", "this", "these", "it", "if", "whether", "when",
    "used", "use"))


def _cut_outside_parens(s: str) -> str:
    """R15.g: the comma cut never lands inside an open paren."""
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            return s[:i]
    return s


def _noun_phrase(description: str, column: str) -> str:
    """The R5 rendering, v1.3.1 (the ED-sepsis phrasing corpses):
    1. strip meta-boilerplate leads ('This column holds details
       about ...' describes the column, not the thing);
    2. first sentence, comma-truncated (a trailing clause after a
       comma is commentary, not the subject), article stripped;
    3. '<X> of|for the <Y>': when head(X) is a TOKEN word (id, code,
       number...) the subject IS Y — 'The ID number of the unit ...'
       speaks about the unit; reorder to '<Y> <head(X)>' only when
       BOTH sides are short (visit date, appointment status); long
       phrases stand as written — gluing a head onto them made
       '...it became effective id';
    4. backstop: cut a reduced relative clause at a non-initial
       ' this ' and strip dangling prepositions."""
    first = (description or "").strip().split(". ")[0].rstrip(".").strip()
    if not first:
        return re.sub(r"[_\W]+", " ", column).strip().lower()
    phrase = _BOILERPLATE.sub("", first)
    # R15.g (v2.15.0, FL19): the gate — a lead outside noun
    # territory falls to the identifier tier, never a broken
    # pass-through ("the stores the unique category identifier
    # ... is 0" can never print again)
    lead = re.sub(r"^(the|a|an)\s+", "", phrase, flags=re.I)
    if lead.split() and lead.split()[0].lower() in _NON_NOUN_LEADS:
        return re.sub(r"[_\W]+", " ", column).strip().lower()
    phrase = _cut_outside_parens(phrase).strip()
    phrase = re.sub(r"^(the|a|an)\s+", "", phrase, flags=re.I)
    m = re.match(r"(?i)^(.*?)\s+(?:of|for)\s+the\s+(.+)$", phrase)
    if m:
        x, y = m.group(1), m.group(2)
        head = x.split()[0].lower()
        if head in _TOKEN_HEADS:
            phrase = y  # the token names the column; Y names the thing
        elif len(x.split()) <= 3 and len(y.split()) <= 3:
            phrase = f"{y} {head}"
    # 2.7.0: '<qualifier> <token> associated with <the thing>' —
    # dictionary boilerplate shaped around a code/number token
    # speaks THE THING ("category number associated with the route
    # of administration" -> "route of administration"); scoped to
    # these linking verbs so the tuned of/for rule stands untouched
    m = re.match(r"(?i)^(.{0,40}?)\s+(?:associated with|linked to|"
                 r"corresponding to)\s+(?:the|a|an)\s+(.+)$", phrase)
    if m and m.group(1).split() \
            and m.group(1).split()[-1].lower() in _TOKEN_HEADS:
        phrase = m.group(2)
    cut = re.search(r"\s+this\s+", phrase)
    if cut and cut.start() > 0:
        phrase = phrase[:cut.start()]
        phrase = re.sub(
            r"\s+(?:in|on|of|for|to|at|by|with|from)$", "", phrase)
    return phrase.lower()


def _pluralize(grain: str) -> str:
    words = grain.split()
    head_idx = len(words) - 1
    for i, w in enumerate(words):
        if w.lower() in _PREPOSITIONS and i > 0:
            head_idx = i - 1
            break
    head = words[head_idx]
    # literal: grammar Grammar_Floor R1
    plural = head + ("es" if head.endswith(("s", "x", "ch", "sh"))
                     else "s")
    if head.endswith("sis"):
        plural = head[:-3] + "ses"  # diagnosis -> diagnoses
    words[head_idx] = plural
    return " ".join(words)


# ---- R12: THE FUNCTION-VOICING LIBRARY (v2.10.0) ----
# The datepart words (ADR 0076's overlay map, re-homed verbatim —
# byte parity guards the M3 stored texts; keys stay EXACTLY the
# overlay's set).
# literal: grammar ADR-0076 datepart overlay
_UNIT_WORDS = {"HH": "hour", "HOUR": "hour", "DD": "day",
               "D": "day", "DAY": "day", "MI": "minute",
               "MINUTE": "minute", "SS": "second",
               "WK": "week", "MM": "month", "MONTH": "month",
               "YY": "year", "YEAR": "year"}
# The phrase skeletons — the CODE MIRROR of the registry's
# Function_Voicings sheet (the sheet is the authority;
# test_derived_render's mirror pin holds these equal).
# literal: schema-mirror kg2_kind_library Function_Voicings
FN_SKELETONS = {
    "DATEDIFF": "the number of <unit>s between <from> and <to>",
    "ROW_NUMBER": "the record's position in its ordered sequence",
    "DATEADD": "<n> <unit>s after <base>",
    "CHARINDEX": "the position of <find> within <in>",
    "LEFT": "the first <n> characters of <s>",
    "RIGHT": "the last <n> characters of <s>",
    "MIN": "the smallest <arg>",
    "FLOOR": "<arg>, rounded down to a whole number",
    "COALESCE": "the first recorded of <args>",
    "DATENAME": "the name of the <part> of <d>",
    "DATEPART": "the <part> of <d>",
    "STUFF": "<s> with a segment replaced by <r>",
    "ISNULL": "<a>, or <b> when <a> is not recorded",
    "ROUND": "<a> rounded to <n> decimal places",
    "STRING_AGG": "every <a> joined into one list",
    "STUFF + FOR XML PATH('')": "every <a> joined into one list",
    # v2.15.0 (Brief_Pilot_Build_2 slice C, registries 1.51.0)
    "GETDATE": "the current date and time",
    "LAG": "the previous record's <x> in its ordered sequence",
    "LEAD": "the next record's <x> in its ordered sequence",
}
# R15.b (v2.15.0): the far-future ISNULL sentinel — a date literal
# at or past this year is the author's open-ended idiom
# literal: grammar Grammar_Floor R15.b
_OPEN_ENDED_YEAR = 2900
# literal: grammar Grammar_Floor R12 (arithmetic operator words)
_ARITH_WORDS = {"Add": "plus", "Subtract": "minus",
                "Multiply": "times", "Divide": "divided by",
                "Modulo": "modulo"}
# R12 v2.14.0 — the slotted ROW_NUMBER (the deferral closes;
# FL17's acceptance: partition AND ordering named)
# literal: schema-mirror kg2_kind_library Function_Voicings
ROW_NUMBER_SLOTTED = ("the record's position within each "
                      "<partition>, ordered by <order>")


def _readable_name(name: str) -> str:
    """Output-name words: the author's own identifier folded to
    readable words (AGE_IN_DAYS / EncWeight -> 'age in days' /
    'enc weight') — the R5.b line for author-named things: the
    author's words, no blessing gate, no raw identifier spoken."""
    s = (name or "").replace("_", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    return " ".join(s.split()).lower()


def _bare(phrase: str) -> str:
    return phrase[4:] if phrase.startswith("the ") else phrase


def _fill_overlay(name, args, sub) -> Optional[str]:
    """COALESCE / LEFT / RIGHT / DATEADD — the absorbed ADR 0076
    overlays, one fill for both contexts (value() operands + R12
    defining phrases). Guards identical to the overlays so the M3
    condition texts stay byte-exact (A1)."""
    if name == "COALESCE":
        return FN_SKELETONS["COALESCE"].replace(
            "<args>", ", ".join(sub(a) for a in args))
    if name in ("LEFT", "RIGHT") and len(args) == 2:
        n = args[1].get("value")
        return (FN_SKELETONS[name]
                .replace("<n>", str(n) if n is not None
                         else sub(args[1]))
                .replace("<s>", sub(args[0])))
    if name == "DATEADD" and len(args) == 3:
        first = args[0]
        unit = str(first.get("value") or first.get("ref", "")
                   ).split(".")[-1].upper()
        n, neg = _offset_value(args[1])
        if unit in _UNIT_WORDS and n is not None:
            word = _UNIT_WORDS[unit] + ("" if str(n) == "1" else "s")
            if neg:
                # R15.b (v2.15.0, FL10 C3): the guard reads THROUGH
                # the unary-minus wrapper — a negative offset voices
                # "before"; the raw fragment can never print again
                return f"{n} {word} before {sub(args[2])}"
            return (FN_SKELETONS["DATEADD"]
                    .replace("<n>", str(n))
                    .replace("<unit>s", word)
                    .replace("<base>", sub(args[2])))
    return None


def _offset_value(expr):
    """The DATEADD offset through its wrapper: a unary minus (the
    ScriptDom shape for -60) or a minus-signed literal both read as
    a negative offset. Returns (magnitude, is_negative)."""
    if expr.get("kind") == "unary" and expr.get("op") == "Negative":
        inner = (expr.get("args") or [{}])[0]
        v = inner.get("value")
        return (v, True) if v is not None else (None, False)
    v = expr.get("value")
    if v is not None and str(v).startswith("-"):
        return str(v)[1:], True
    return v, False


def _part_word(expr) -> str:
    token = str(expr.get("value") or expr.get("ref", "")
                ).split(".")[-1]
    return _UNIT_WORDS.get(token.upper(), token.lower())


def _partition_words(expr, voice) -> str:
    if expr.get("kind") == "column_ref":
        return voice.name_words(expr)
    return _bare(_defining_phrase(expr, voice))


def _order_words(element, voice) -> str:
    e = element.get("expr") or {}
    if e.get("kind") == "column_ref":
        words = "the " + voice.name_words(e)
    else:
        words = _defining_phrase(e, voice)
    return words + (" (descending)" if element.get("descending")
                    else "")


def _fill_library(name, args, voice, sub, expr=None) -> Optional[str]:
    """The named-function rows beyond the absorbed overlays. None =
    no row or a guard failed — the caller counts the remainder."""
    skel = FN_SKELETONS.get(name)
    if skel is None:
        return None
    if name == "DATEDIFF" and len(args) == 3:
        return (skel.replace("<unit>", _part_word(args[0]))
                .replace("<from>", sub(args[1]))
                .replace("<to>", sub(args[2])))
    if name == "ROW_NUMBER":
        # THE DEFERRAL CLOSES (v2.14.0, Brief_Pilot_Build_3 — FL17's
        # echo): captured over contents fill the slots; a flag-only
        # `over` (or empty contents) keeps the ratified slotless
        # phrase — never an empty slot in prose
        over = (expr or {}).get("over")
        if isinstance(over, dict):
            parts = " and ".join(_partition_words(p, voice)
                                 for p in over.get("partition_by")
                                 or [])
            order = ", ".join(_order_words(o, voice)
                              for o in over.get("order_by") or [])
            if parts and order:
                return (ROW_NUMBER_SLOTTED
                        .replace("<partition>", parts)
                        .replace("<order>", order))
            if order:
                return f"the record's position, ordered by {order}"
        return skel
    if name == "MIN" and args:
        phrase = sub(args[0])
        if voice.is_temporal(args[0], phrase):
            # literal: grammar Grammar_Floor R12 (MIN temporal,
            # Sunny 2026-09-16: "yes, say earliest for dates")
            return f"the earliest {_bare(phrase)}"
        return skel.replace("<arg>", _bare(phrase))
    if name == "CHARINDEX" and len(args) >= 2:
        return (skel.replace("<find>", sub(args[0]))
                .replace("<in>", sub(args[1])))
    if name == "FLOOR" and args:
        return skel.replace("<arg>", sub(args[0]))
    if name in ("DATENAME", "DATEPART") and len(args) == 2:
        return (skel.replace("<part>", _part_word(args[0]))
                .replace("<d>", sub(args[1])))
    if name == "ISNULL" and len(args) == 2:
        # R15.b (v2.15.0, FL10 C3): the far-future sentinel is the
        # author's open-ended idiom, never a real date
        if _is_open_ended_sentinel(args[1]):
            return (f"{sub(args[0])} (treating a missing date as "
                    "open-ended)")
        return (skel.replace("<a>", sub(args[0]))
                .replace("<b>", sub(args[1])))
    if name == "GETDATE":
        return skel
    if name in ("LAG", "LEAD") and args:
        # R15.f (v2.15.0, FL14 C5 (a)): the R12 slot form — slice
        # E's captured over contents fill the slots; never an
        # empty slot in prose
        who = "previous" if name == "LAG" else "next"
        x = _bare(sub(args[0]))
        over = (expr or {}).get("over")
        if isinstance(over, dict):
            parts = " and ".join(_partition_words(p, voice)
                                 for p in over.get("partition_by")
                                 or [])
            order = ", ".join(_order_words(o, voice)
                              for o in over.get("order_by") or [])
            if parts and order:
                return (f"the {who} record's {x} within each "
                        f"{parts}, ordered by {order}")
            if order:
                return f"the {who} record's {x}, ordered by {order}"
        return skel.replace("<x>", x)
    if name == "ROUND" and len(args) >= 2:
        n = args[1].get("value")
        return (skel.replace("<a>", sub(args[0]))
                .replace("<n>", str(n) if n is not None
                         else sub(args[1])))
    if name == "STRING_AGG" and args:
        return skel.replace("<a>", _bare(sub(args[0])))
    if name == "STUFF" and len(args) == 4:
        r = args[3].get("value")
        return (skel.replace("<s>", sub(args[0]))
                .replace("<r>", str(r) if r is not None
                         else sub(args[3])))
    return None


def _is_open_ended_sentinel(expr) -> bool:
    """R15.b: a date literal whose year is 2900+ ('2999-12-31')."""
    if expr.get("kind") != "literal":
        return False
    m = re.match(r"^'?(\d{4})-\d{2}-\d{2}", str(expr.get("value", "")))
    return bool(m) and int(m.group(1)) >= _OPEN_ENDED_YEAR


def _stuff_idiom(subq, voice) -> str:
    """THE STUFF LIST IDIOM (Sunny 2026-09-16, 'rule the idiom'):
    STUFF over a FOR-XML subquery is the pre-2017 list-join —
    voiced as STRING_AGG's meaning; the separator literal is
    stripped (the STUFF only trims it). The <order> slot is
    DEFERRED with ROW_NUMBER's recorded reason (ORDER BY contents
    are a structure flag, not contents)."""
    members = (subq.get("scope") or {}).get("projection") or []
    expr = (members[0].get("expression") or {}) if members else {}
    if expr.get("kind") == "arithmetic":
        args = expr.get("args") or []
        non_lit = [a for a in args if a.get("kind") != "literal"]
        if len(non_lit) == 1:
            expr = non_lit[0]
    inner = _defining_phrase(expr, voice) if expr \
        else "the selected value"
    return FN_SKELETONS["STUFF + FOR XML PATH('')"].replace(
        "<a>", _bare(inner))


def _defining_phrase(expr, voice) -> str:
    """R12's recursive walk: nesting voices inside-out; a
    composite's slot words are its children's finished phrases."""
    kind = expr.get("kind")
    if kind == "function":
        name = (expr.get("name") or "").upper()
        args = expr.get("args") or []
        if name == "STUFF" and args \
                and args[0].get("kind") == "subquery_ref":
            return _stuff_idiom(args[0], voice)

        def sub(a):
            return _defining_phrase(a, voice)
        got = _fill_overlay(name, args, sub)
        if got is None:
            got = _fill_library(name, args, voice, sub, expr)
        if got is not None:
            return got
        voice.function_remainders[name] = \
            voice.function_remainders.get(name, 0) + 1
        parts = [sub(a) for a in args]
        # literal: grammar Grammar_Floor R12 (the counted fallback)
        return "a value computed from " + \
            (", ".join(parts) if parts else "its inputs")
    if kind == "cast":
        # TRANSPARENT: representation change, not meaning change
        args = expr.get("args") or []
        return (_defining_phrase(args[0], voice) if args
                else "a recast value")
    if kind == "case":
        # literal: grammar Grammar_Floor R12 (the standing phrase)
        return "a value derived by rule"
    if kind == "unary":
        args = expr.get("args") or []
        inner = _defining_phrase(args[0], voice) if args else "a value"
        return ("negative " + inner
                if expr.get("op") == "Negative" else inner)
    if kind == "arithmetic":
        args = expr.get("args") or []
        if len(args) == 2:
            word = _ARITH_WORDS.get(expr.get("op"), "combined with")
            return (f"{_defining_phrase(args[0], voice)} {word} "
                    f"{_defining_phrase(args[1], voice)}")
        return "a computed combination"
    if kind == "subquery_ref":
        # literal: grammar Grammar_Floor R12
        return "a value from a nested selection"
    return voice.value(expr, expr)


def derived_phrase(member, voice) -> str:
    """The derived_column node's stored description — R12's phrase
    shape: name words + the defining phrase; a nameless member
    speaks the phrase alone. The verbatim law holds stored == this
    recompute."""
    expr = member.get("expression") or {}
    if expr.get("kind") == "literal":
        # literal: grammar Grammar_Floor R12 (the named constant)
        phrase = f"the constant {expr.get('value')}"
    else:
        phrase = _defining_phrase(expr, voice)
    words = _readable_name(member.get("name") or "")
    if words:
        return f"{words[0].upper()}{words[1:]}: {phrase}."
    return f"{phrase[:1].upper()}{phrase[1:]}."


@functools.lru_cache(maxsize=None)
def _pack_conventions(vendor: str) -> tuple:
    """R15.c (v2.15.0, ruling (6)): the packaged pack.json's
    naming_conventions for one vendor — (suffix, rule) pairs,
    longest suffix first. The wheel's aisql/_source_packs/<vendor>
    wins; the repo's AIVIA_Product/source_packs/<vendor> is the
    dev fallback (the fabric_run._pack_dir pattern). No pack, no
    conventions — estates without one stay untouched."""
    if not vendor:
        return ()
    here = pathlib.Path(__file__).resolve()
    for base in (here.parents[1] / "_source_packs",
                 here.parents[2] / "AIVIA_Product" / "source_packs"):
        path = base / vendor / "pack.json"
        if path.is_file():
            try:
                rows = json.loads(path.read_text(encoding="utf-8-sig")
                                  ).get("naming_conventions") or []
            except (OSError, json.JSONDecodeError):
                return ()
            pairs = [(str(r.get("suffix") or ""), str(r.get("rule")
                                                      or ""))
                     for r in rows if r.get("suffix")]
            return tuple(sorted(pairs, key=lambda t: -len(t[0])))
    return ()


class _Voice:
    """Graph-backed voicing context for one scope."""

    def __init__(self, read: ReadApi, tree: Dict[str, Any]):
        self._columns = {n.identity: n.properties
                         for n in read.nodes("column")}
        # R15.c (v2.15.0, ruling (6)): each column's VENDOR from
        # its dictionary extract's pack id ("emr@…#clarity-pack-1.2"
        # → "clarity"); the packaged pack.json's naming_conventions
        # are the ladder's middle rung — estates with no pack get
        # an empty tuple and stay untouched
        self._vendor_of = {}
        for n in read.nodes("column"):
            x = getattr(n, "extract_id", "") or ""
            pack = x.split("#")[-1] if "#" in x else ""
            self._vendor_of[n.identity] = (
                pack.split("-pack-")[0] if "-pack-" in pack else "")
        self._tables = {n.identity: n.properties
                        for n in read.nodes("table")}
        self._params = {p["name"]: p for p in tree.get("parameters", [])}
        # R5.b (v2.8.0): blessed names — one map, both grains
        # (4-part = column, 3-part = table); a blessed name wins
        # EVERY position its target is voiced; absent = fallback
        self.blessed = {n.properties["target"]: n.properties["words"]
                        for n in read.nodes("blessed_name")}
        self.disagreements: List[str] = []  # declared vs annotation (R8)
        # R12: unlisted operations land here — the counted remainder
        self.function_remainders: Dict[str, int] = {}

    def subject(self, expr) -> str:
        if expr.get("kind") == "column_ref":
            col_id = expr.get("resolves_to") or ""
            if col_id in self.blessed:  # R5.b tier 1
                return self.blessed[col_id]
            col_name = expr["ref"].split(".")[-1]
            desc = self._columns.get(col_id, {}).get("description", "")
            if desc:
                phrase = _noun_phrase(desc, col_name)
                fold = re.sub(r"[_\W]+", " ", col_name).strip().lower()
                if phrase != fold:
                    return phrase  # the dictionary tier spoke
            # R15.c: the identifier tier walks the ladder — pack
            # convention before the readable fold
            return (self._convention_words(expr)
                    or _noun_phrase("", col_name))
        # a computed subject voices through the value path (DATEADD
        # overlay, steward words) — raw tokens never face the steward
        phrase = self.value(expr, expr)
        return phrase[4:] if phrase.startswith("the ") else phrase

    def _convention_words(self, expr) -> Optional[str]:
        """R15.c (v2.15.0, ruling (6)): the pack-convention rung —
        vendor suffix rules from the packaged pack.json, longest
        suffix first; None when no pack or no suffix matches."""
        target = expr.get("resolves_to") or ""
        vendor = self._vendor_of.get(target, "")
        ident = str(expr.get("ref", "")).split(".")[-1]
        for suffix, rule in _pack_conventions(vendor):
            if len(ident) > len(suffix) \
                    and ident.upper().endswith(suffix.upper()):
                stem = _noun_phrase("", ident[:-len(suffix)])
                # literal: shape (pack.json naming_conventions rules)
                if rule == "yes_no_flag":
                    return stem + " yes/no flag"
                if rule == "datetime_words":
                    return stem + " date and time"
                if rule == "internal_date":
                    return stem + " date (internal decimal form)"
                return stem  # category_code: the suffix drops
        return None

    def name_words(self, expr) -> str:
        """The name-words register (v2.6.0/v2.7.0 subjects), R5.b
        tier ladder since v2.15.0 (ruling (6)): blessed name → pack
        convention → readable identifier form."""
        target = expr.get("resolves_to") or ""
        return (self.blessed.get(target)
                or self._convention_words(expr) or _name_words(expr))

    def owner_words(self, expr) -> str:
        """R5.c (v2.9.0): the blessed OWNER name for a column_ref's
        table — EMPTY when the table is unblessed. The possessive
        never speaks raw table names; that was the v2.6.0
        deferral's whole reason (premature wiring bakes jargon
        into every phrase)."""
        col_id = expr.get("resolves_to") or ""
        if col_id.count("|") < 3:
            return ""
        return self.blessed.get(col_id.rsplit("|", 1)[0], "")

    def temporal_evidence(self, expr, spoken: str) -> str:
        """Rider (c) RULED — THE TEMPORAL UNION: blessing may only
        ADD temporal evidence, never remove it. When a blessed
        name spoke, the words the fallback tiers would have spoken
        (name words + the dictionary phrase) join the R4 test;
        unblessed subjects test their spoken words alone —
        byte-identical to v2.7.0 (A1)."""
        target = (expr.get("resolves_to") or "") \
            if expr.get("kind") == "column_ref" else ""
        if not target or target not in self.blessed:
            return spoken
        desc = self._columns.get(target, {}).get("description", "")
        return " ".join((spoken, _name_words(expr),
                         _noun_phrase(desc,
                                      expr["ref"].split(".")[-1])))

    def is_temporal(self, expr, spoken: str) -> bool:
        """R4 verb choice — EVIDENCE ONLY ADDS, three sources in
        a ladder: (1) the DECLARED data_type (rider (c) amended,
        Sunny 2026-09-13: the EMR dictionary carries types) — a
        temporal type decides YES outright; a non-temporal type
        never decides NO (VARCHAR dates are an EMR fact of life)
        — it falls through to (2)+(3), the temporal union of
        blessed words and the fallback tier's words."""
        target = (expr.get("resolves_to") or "") \
            if expr.get("kind") == "column_ref" else ""
        declared = self._columns.get(target, {}).get("data_type", "")
        if declared.split("(")[0].strip().lower() in _TEMPORAL_TYPES:
            return True
        # R15.b corollary (v2.15.0): a count phrase — "the number
        # of minutes between …" — is a NUMBER, never a moment; the
        # word "time" inside its slots is not temporal evidence
        if spoken.lstrip().startswith(("number of", "the number of")):
            return False
        ev = self.temporal_evidence(expr, spoken)
        return "date" in ev or "time" in ev

    def value(self, expr, subject_expr) -> str:
        kind = expr.get("kind")
        if kind == "parameter_ref":
            name = expr["ref"].lstrip("@")
            words = re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()
            param = self._params.get(name)
            if param:
                return (f"the {words} parameter (default "
                        f"{param['default_logic']} when none is supplied)")
            return f"the {words} parameter"
        if kind == "literal":
            raw = str(expr["value"])
            col_id = subject_expr.get("resolves_to") or ""
            values_map = self._columns.get(col_id, {}).get("values") or {}
            meaning = values_map.get(raw.strip("'"))
            note = expr.get("annotation")
            if meaning:  # R8 precedence: the DECLARED meaning wins
                if note and note.lower() != meaning.lower():
                    self.disagreements.append(
                        f"{raw}: declared '{meaning}' vs source note "
                        f"'{note}'")
                return f"{raw} ('{meaning}')"
            if note:
                return f"{raw} (noted '{note}')"
            return raw
        if kind == "column_ref":
            # a column as a VALUE voices by its steward words too —
            # raw identifiers never face the steward (R5; the line-83
            # corpse: '[#base_pop].ed_departure_time' in prose)
            return f"the {self.subject(expr)}"
        if kind == "case":
            return "a value derived by rule"
        if kind == "cast":
            # R15.b (v2.15.0): TRANSPARENT on the WHERE path too —
            # CONVERT(numeric, sig) never prints raw again; the
            # cast kind's R12 rule, now one rule on both paths
            args = expr.get("args") or []
            if args:
                return self.value(args[0], subject_expr)
        if kind == "function":
            # the ADR 0076 overlays, ABSORBED into the shared fills
            # (R12 v2.10.0) — guards identical, phrases byte-exact
            got = _fill_overlay((expr.get("name") or "").upper(),
                                expr.get("args") or [],
                                lambda a: self.value(a, a))
            if got is None:
                # R15.b ONE LIBRARY, TWO READERS (v2.15.0, FL10 C3):
                # the WHERE path fills from the same Function_
                # Voicings rows the derived path reads
                got = _fill_library((expr.get("name") or "").upper(),
                                    expr.get("args") or [], self,
                                    lambda a: self.value(a, a), expr)
            if got is not None:
                return got
        return decisions.render_expr(expr).lower()

    def forbidden_tokens(self, scope) -> List[str]:
        tokens = []
        for ref in scope.get("from_refs", []):
            name = ref.get("table_ref")
            if name:
                tokens.append(name.split(".")[-1])
        for col in decisions.flatten_where(scope.get("where")):
            # literal: schema-mirror kg2_kind_library
            for role in ("subject", "comparand", "pattern"):
                e = col.get(role)
                if e and e.get("kind") == "column_ref":
                    tokens.append(e["ref"].split(".")[-1])
                    tokens.append(e["ref"])
        return tokens


def _nested_selection_phrase(selection, voice: "_Voice") -> str:
    """Grammar 2.2.0: an IN/EXISTS subselection voices its aggregate
    reads + restrictive-spine conditions in one phrase. Returns ''
    when there is no mapped interior (the pre-sweep pointer wording
    stands) or when the interior is a combination (alternatives
    cannot flatten; the pointer wording stays honest)."""
    scope = (selection or {}).get("scope")
    if not scope or "combination_arms" in scope:
        return ""
    sources = decisions.nested_sources(scope)
    if not sources:
        return ""
    phrases = []
    for ref in sources:
        p = _source_phrase(ref.get("table_ref"),
                           ref.get("resolves_to"), [],
                           blessed=voice.blessed)
        if p not in phrases:
            phrases.append(p)
    conds = []
    for pred in decisions.nested_membership(scope):
        if decisions.is_degenerate(pred):
            continue
        phrase = _voice_predicate(pred, voice)
        if phrase and phrase not in conds:
            conds.append(phrase)
    out = "a nested selection reading " + ", ".join(phrases)
    if conds:
        joined = "; and ".join(p.rstrip(".")[0].lower() + p.rstrip(".")[1:]
                               for p in conds)
        out += f", where {joined}"
    return out


def _name_words(expr) -> str:
    return _noun_phrase("", str(expr.get("ref", "")).split(".")[-1])


# literal: shape (inbound.SAME_TREE — the resolver's same-tree
# scope marker; one spelling, two readers)
_SAME_TREE_MARK = "SAME-TREE scope "


def _relation_owner(expr, voice: _Voice) -> str:
    """R15.a (v2.15.0, FL9 C2 (a)): the owner's possessive for one
    side of a column-to-column relation. A table side speaks its
    BLESSED name, else '<readable table words> record's' (C2 ruled
    the readable fallback INTO this position; R5.c's blessed-only
    law stands for the recordedness pointer). A SAME-TREE side
    speaks 'the <words> selection's'. Unresolved → '' (bare name
    words — honesty over invention)."""
    r = expr.get("resolves_to") or ""
    if not isinstance(r, str):
        return ""
    if r.count("|") == 3:
        table_id = r.rsplit("|", 1)[0]
        words = voice.blessed.get(table_id)
        if words:
            return f"{words}'s "
        t = _readable_name(table_id.rsplit("|", 1)[-1])
        if not t:
            return ""
        if t.endswith("records"):
            # the records-records guard (the 2026-09-15 class,
            # echo-mandated): MED_ADMIN_RECORDS speaks "the med
            # admin record's", never "records record's"
            return f"{t[:-1]}'s "
        return f"{t} record's "
    if r.startswith(_SAME_TREE_MARK):
        key = r[len(_SAME_TREE_MARK):]
        sel = _spoken_selection(key.rsplit("::", 1)[-1])
        return f"{sel} selection's " if sel else ""
    return ""


def _compare_terms(pred, voice: _Voice) -> Tuple[str, str]:
    """GRAMMAR 2.7.0 — THE RELATION RULE (Sunny, 2026-09-12: the
    mixed-register corpse 'the time designated by the user when
    the action occurred is before the ed departure time'): a
    comparison BETWEEN TWO COLUMNS is a relation between two named
    things — both sides speak NAME WORDS; a comparison against a
    VALUE keeps the dictionary-definition subject, because there
    the meaning IS the sentence. R15.a (v2.15.0, FL9 C2 (a)):
    both sides carry their OWNERS — 'The x is the x' can never
    print again for resolved sides."""
    subj_expr = pred.get("subject", {})
    comp_expr = pred.get("comparand")
    if subj_expr.get("kind") == "column_ref" \
            and isinstance(comp_expr, dict) \
            and comp_expr.get("kind") == "column_ref":
        return (_relation_owner(subj_expr, voice)
                + voice.name_words(subj_expr),
                "the " + _relation_owner(comp_expr, voice)
                + voice.name_words(comp_expr))
    return (voice.subject(subj_expr),
            voice.value(comp_expr, subj_expr))


def _temporal_window(pred, voice: _Voice) -> Optional[str]:
    """R15.b (v2.15.0, FL10 C3) — THE TEMPORAL-WINDOW IDIOM: a
    comparison against DATEADD(unit, ±N, now) speaks the window —
    subject >= now-minus-N is 'within the last N <unit>s',
    subject <= now-plus-N is 'within the next N <unit>s'; n==1
    drops the count ('within the last year'). Every other DATEADD
    keeps the compositional voice."""
    comp = pred.get("comparand")
    if not isinstance(comp, dict) or comp.get("kind") != "function" \
            or (comp.get("name") or "").upper() != "DATEADD":
        return None
    args = comp.get("args") or []
    if len(args) != 3 or not _is_now(args[2]):
        return None
    unit = str(args[0].get("value") or args[0].get("ref", "")
               ).split(".")[-1].upper()
    if unit not in _UNIT_WORDS:
        return None
    n, neg = _offset_value(args[1])
    if n is None:
        return None
    kind = pred["kind"]
    if neg and kind in ("COMPARE_GTE", "COMPARE_GT"):
        way = "last"
    elif not neg and kind in ("COMPARE_LTE", "COMPARE_LT"):
        way = "next"
    else:
        return None
    subj = voice.subject(pred.get("subject", {}))
    word = _UNIT_WORDS[unit]
    if str(n) == "1":
        return f"The {subj} is within the {way} {word}."
    return f"The {subj} is within the {way} {n} {word}s."


def _is_now(expr) -> bool:
    """GETDATE(), or a cast of it (CONVERT(date, GETDATE()))."""
    if expr.get("kind") == "function" \
            and (expr.get("name") or "").upper() == "GETDATE":
        return True
    if expr.get("kind") == "cast":
        args = expr.get("args") or []
        return bool(args) and _is_now(args[0])
    return False


def _voice_predicate(pred, voice: _Voice) -> str:
    kind = pred["kind"]
    subj_expr = pred.get("subject", {})
    subj = voice.subject(subj_expr)
    # literal: schema-mirror kg2_kind_library
    if kind in ("COMPARE_GTE", "COMPARE_GT", "COMPARE_LTE", "COMPARE_LT"):
        window = _temporal_window(pred, voice)
        if window:
            return window
        subj, comp = _compare_terms(pred, voice)
        # rider (c): declared type first, then the temporal union
        # — evidence only adds; unblessed untyped columns test
        # their spoken words alone (A1)
        temporal = voice.is_temporal(subj_expr, subj)
        # literal: grammar Grammar_Floor R4 verbs
        verb = {"COMPARE_GTE": "is on or after" if temporal else "is at least",
                "COMPARE_GT": "is after" if temporal else "exceeds",
                "COMPARE_LTE": "is on or before" if temporal else "is at most",
                "COMPARE_LT": "is before" if temporal else "is below"}[kind]
        return f"The {subj} {verb} {comp}."
    if kind == "COMPARE_EQ":
        subj, comp = _compare_terms(pred, voice)
        return f"The {subj} is {comp}."
    if kind == "COMPARE_NEQ":
        subj, comp = _compare_terms(pred, voice)
        return f"The {subj} is not {comp}."
    if kind == "PATTERN_MATCH":
        pattern = str(pred["pattern"].get("value", "")).strip("'")
        if pattern.endswith("%") and "%" not in pattern[:-1] \
                and "_" not in pattern:
            return f"The {subj} starts with '{pattern[:-1]}'."
        if pattern.startswith("%") and "%" not in pattern[1:] \
                and "_" not in pattern:
            return f"The {subj} ends with '{pattern[1:]}'."
        if pattern.startswith("%") and pattern.endswith("%") \
                and "%" not in pattern[1:-1]:
            return f"The {subj} contains '{pattern[1:-1]}'."
        return f"The {subj} matches the pattern '{pattern}'."
    if kind == "IN_LIST":
        members = ", ".join(voice.value(m, subj_expr)
                            for m in pred["comparand_list"])
        return f"The {subj} is one of the values {members}."
    if kind == "RANGE":
        return (f"The {subj} is between "
                f"{voice.value(pred['lower_bound'], subj_expr)} and "
                f"{voice.value(pred['upper_bound'], subj_expr)} (inclusive).")
    if kind == "NULL_CHECK":
        # GRAMMAR 2.6.0 (Sunny's go, 2026-09-12): recordedness
        # predicates IDENTIFY their subject — name words point,
        # dictionary words teach; "is recorded" needs pointing only
        return f"The {_ident_subject(pred, voice)} is not recorded."
    if kind == "EXISTS_SELECTION":
        detail = _nested_selection_phrase(pred.get("selection"), voice)
        if detail:
            return f"A matching record exists in {detail}."
        return "A matching record exists in a separately defined selection."
    if kind == "IN_SELECTION":
        # grammar 2.2.0 (Sunny's ABX first-leg find): the value-set
        # pointer gains its CONTENT now that subquery interiors are
        # mapped — the nested selection's reads and its restrictive-
        # spine conditions; OUTER-APPLY interiors stay excluded (an
        # optional lookup never restricts the producing rows)
        detail = _nested_selection_phrase(pred.get("selection"), voice)
        if detail:
            return f"The {subj} is one of the values from {detail}."
        return (f"The {subj} is one of the values defined by another "
                "selection.")
    if kind == "QUANTIFIED_COMPARE":
        quant = ("every row of" if pred.get("quantifier") == "All"
                 else "any row of")
        return (f"The {subj} compares against {quant} another selection.")
    if kind == "OR":
        arms = [_voice_predicate(c, voice).rstrip(".")
                for c in pred["children"]]
        return " or ".join(arms) + "."
    if kind == "NOT":
        # GRAMMAR 2.5.0 (Sunny's ruling 2026-09-12): NOT FOLDS INTO
        # ITS CHILD — one meaning, one phrase, per-kind negation
        # from the closed set; the wrapper sentence is the fallback
        return _voice_negated(pred["children"][0], voice)
    return ""  # remainder predicates voice nothing; they are counted


# NOT's comparison flips (2.5.0): the negation of an order
# comparison IS the opposite comparison
# literal: grammar
_NEGATED_COMPARE = {"COMPARE_GTE": "COMPARE_LT",
                    "COMPARE_GT": "COMPARE_LTE",
                    "COMPARE_LTE": "COMPARE_GT",
                    "COMPARE_LT": "COMPARE_GTE",
                    "COMPARE_EQ": "COMPARE_NEQ",
                    "COMPARE_NEQ": "COMPARE_EQ"}


def _ident_subject(pred, voice: _Voice) -> str:
    """GRAMMAR 2.6.0 — recordedness predicates IDENTIFY their
    subject (the column's name words) where value predicates
    DEFINE it (dictionary words): 'the taken time is recorded'
    needs to point at the column, not to teach its meaning.
    GRAMMAR 2.9.0 (R5.c, ruled 2026-09-14) — the v2.6.0 deferral
    closes: when the OWNER table has a blessed name, the pointer
    gains its missing half ('the medication administration's
    taken time'). Recordedness positions ONLY; always-when-
    blessed (text stays a pure function of node + registry, so
    delta-by-name holds); 's unchanged on s-ending heads; a
    stutter is the smell census's to flag, never suppressed
    here."""
    expr = pred.get("subject", {})
    if expr.get("kind") == "column_ref" and expr.get("ref"):
        words = voice.name_words(expr)
        owner = voice.owner_words(expr)
        return f"{owner}'s {words}" if owner else words
    return voice.subject(expr)


def _voice_negated(pred, voice: _Voice) -> str:
    """GRAMMAR 2.5.0 — the negated voice of a leaf predicate (the
    closed kind set, R4 family): NOT(NULL_CHECK) speaks the
    positive fact; order comparisons flip to their opposites;
    membership and pattern kinds negate their verb; anything
    without a ruled negation keeps the honest wrapper sentence."""
    kind = pred.get("kind", "")
    if kind == "NULL_CHECK":
        # 2.6.0: the positive recordedness fact, name-words subject
        return f"The {_ident_subject(pred, voice)} is recorded."
    if kind in _NEGATED_COMPARE:
        return _voice_predicate({**pred, "kind":
                                 _NEGATED_COMPARE[kind]}, voice)
    if kind == "IN_LIST":
        subj_expr = pred.get("subject", {})
        subj = voice.subject(subj_expr)
        members = ", ".join(voice.value(m, subj_expr)
                            for m in pred["comparand_list"])
        return f"The {subj} is none of the values {members}."
    if kind == "IN_SELECTION":
        subj = voice.subject(pred.get("subject", {}))
        detail = _nested_selection_phrase(pred.get("selection"),
                                          voice)
        if detail:
            return (f"The {subj} is not one of the values from "
                    f"{detail}.")
        return (f"The {subj} is not one of the values defined by "
                "another selection.")
    if kind == "EXISTS_SELECTION":
        detail = _nested_selection_phrase(pred.get("selection"),
                                          voice)
        if detail:
            return f"No matching record exists in {detail}."
        return ("No matching record exists in a separately "
                "defined selection.")
    if kind == "PATTERN_MATCH":
        positive = _voice_predicate(pred, voice)
        # literal: grammar — the R4 pattern verbs and their negations
        negated_verb = {"starts with": "does not start with",
                        "ends with": "does not end with",
                        "contains": "does not contain",
                        "matches the pattern":
                        "does not match the pattern"}
        for verb, neg in negated_verb.items():
            if f" {verb} " in positive:
                return positive.replace(f" {verb} ", f" {neg} ", 1)
    inner = _voice_predicate(pred, voice).rstrip(".")
    if not inner:
        return "The inner condition does not hold."
    return f"It is not the case that {inner[0].lower()}{inner[1:]}."


def _twin_selection(read: ReadApi, tree, scope):
    """The scope's selection node in the stored meaning twin (KG2b) —
    the spine the policy walk reads since grammar 2.0.0."""
    want = scope.get("name") or scope.get("name_key")
    for n in read.nodes("meaning_twin"):
        twin = n.properties.get("twin", {})
        if twin.get("file") != tree.get("name"):
            continue
        for node in twin["nodes"]:
            if node["kind"] == "selection" \
                    and node["content"].get("selection") == want:
                return twin, node
    return None, None


def _spoken_selection(name: str) -> str:
    """The author's selection name, spoken — # stripped, separators
    to spaces, lowercased (R5.b standing: the author's own words, no
    blessing gate). ONE home: _source_phrase and R11 both fold
    through here."""
    return re.sub(r"[_\W]+", " ",
                  (name or "").lstrip("#")).strip().lower()


# literal: schema-mirror kg2_kind_library Statement_Voicings
_STATEMENT_VOICED = frozenset({"SELECT INTO", "IF", "SELECT"})


def statement_phrase(stmt, predicate_phrase: Optional[str] = None
                     ) -> Optional[str]:
    """R11 — THE STATEMENT STEP (DRAFT, Brief_M5_Statement_Layer
    approved 2026-09-17; Sunny gap-checks the rendered 36 before
    ratification). What THIS STEP does, naming its selections —
    never its scopes' floors (the speech contract). Returns None
    for the silent kinds: T-2 operational and unlisted (the
    builder COUNTS those; this function never invents a phrase)."""
    kind = stmt.get("statement_kind", "")
    if kind not in _STATEMENT_VOICED:
        return None
    scope = stmt.get("scope") or {}
    sel = _spoken_selection(scope.get("name")
                            or (scope.get("name_key") or ""
                                ).rsplit("::", 1)[-1])
    if kind == "SELECT INTO" and sel:
        helpers = [f"the {_spoken_selection(c.get('name') or (c.get('name_key') or '').rsplit('::', 1)[-1])} selection"
                   for c in stmt.get("ctes") or []]
        if helpers:
            listed = (helpers[0] if len(helpers) == 1
                      else ", ".join(helpers[:-1])
                      + " and " + helpers[-1])
            return (f"Builds the {sel} selection, preparing "
                    f"{listed} first.")
        return f"Builds the {sel} selection."
    if kind == "IF":
        # THE GUARD IDIOM (R11 amendment, v2.14.0 — FL10 family,
        # Brief_Pilot_Build_3): the OBJECT_ID/DROP dance speaks as
        # the idiom it is — ONLY when the tree shows BOTH halves
        # (the recordedness guard AND the drop); anything else
        # keeps the decision-step voice, never a guess
        if stmt.get("then_kind") == "DropTableStatement" \
                and stmt.get("then_drops") \
                and _is_objectid_guard(stmt.get("predicate")):
            return (f"A cleanup step: removes the previous "
                    f"{stmt['then_drops'][0]} when it already "
                    "exists.")
        if predicate_phrase:
            p = predicate_phrase.strip().rstrip(".")
            return (f"A decision step, taken when "
                    f"{p[0].lower()}{p[1:]}.")
        return None
    if kind == "SELECT" and stmt.get("emits"):
        return "Delivers the procedure's result set."
    return None


def _is_objectid_guard(pred) -> bool:
    """The temp-table-existence guard's predicate half:
    NOT(NULL_CHECK(OBJECT_ID(...))) — read from the tree, never
    from rendered text."""
    if not pred or pred.get("kind") != "NOT":
        return False
    kids = pred.get("children") or []
    if len(kids) != 1 or kids[0].get("kind") != "NULL_CHECK":
        return False
    subject = kids[0].get("subject") or {}
    return (subject.get("kind") == "function"
            and str(subject.get("name") or "").upper() == "OBJECT_ID")


def _source_phrase(name: str, resolved, depth2_counter: List[int],
                   blessed=None) -> str:
    if resolved and str(resolved).startswith("SAME-TREE"):
        # named scope refs stay OUT of R5.b — the author's own
        # words, no vendor dictionary row
        words = _spoken_selection(name)
        return (f"the {words} selection defined earlier in this "
                "procedure")
    if name is None:  # an anonymous derived table — depth-1 inline
        return "an inline selection"
    if blessed and resolved in blessed:  # R5.b tier 1, table grain
        return f"{blessed[resolved]} records"
    words = re.sub(r"[_\W]+", " ", name.split(".")[-1]).strip().lower()
    return f"{words} records"


def _composition_sentence(read: ReadApi, tree, scope,
                          ledger: Dict[str, int],
                          blessed=None) -> Optional[str]:
    """The composition sentence (the finding-4 heir; ruling 4c): what
    this selection READS and how the joins compose the population —
    INNER voices as restriction; any OUTER present demotes the wording
    to 'combined with' (voicing an optional match as a restriction
    would lie the other way — the v1.3.0 posture)."""
    refs = scope.get("from_refs", [])
    if not refs:
        return None
    join_kinds = {str(on.get("join_type"))
                  for on in scope.get("join_on", [])}
    # restriction wording needs a LINK: an ON clause, or comma-join
    # keys (col=col) in the WHERE; linkless multi-source = cartesian,
    # voiced neutrally ("combined with") — never a false restriction
    linked = bool(scope.get("join_on")) or any(
        decisions.is_join_key(leaf)
        for leaf in decisions.flatten_where(scope.get("where")))
    inner_only = join_kinds <= {"Inner"} and linked
    phrases = []
    for ref in refs:
        if "derived_scope" in ref:
            phrases.append("an inline selection")
            # depth-2 nesting: translated in full (the twin is total);
            # PROSE inlines depth 1 only — deeper is counted with the
            # revisit trigger (ruled 2026-09-06, the depth cap)
            inner_refs = ref["derived_scope"].get("from_refs", [])
            if any("derived_scope" in r for r in inner_refs):
                ledger["deep_nesting_counted"] = \
                    ledger.get("deep_nesting_counted", 0) + 1
            continue
        phrases.append(_source_phrase(ref.get("table_ref"),
                                      ref.get("resolves_to"), [],
                                      blessed=blessed))
    if not phrases:
        return None
    # 2.3.0 phrasing (truth unchanged, count visible): a RUN of
    # identical source phrases aggregates — "combined with an inline
    # selection" seven times is mechanics, "7 inline selections" is
    # the same fact spoken once
    compressed = []
    i = 0
    while i < len(phrases):
        j = i
        while j < len(phrases) and phrases[j] == phrases[i]:
            j += 1
        n = j - i
        if n == 1:
            compressed.append(phrases[i])
        elif phrases[i] == "an inline selection":
            compressed.append(f"{n} inline selections")
        else:
            compressed.append(f"{phrases[i]} ({n} reads)")
        i = j
    phrases = compressed
    sentence = f"Drawn from {phrases[0]}"
    connector = (", restricted to records also present in "
                 if inner_only and len(join_kinds) > 0
                 else ", combined with ")
    for p in phrases[1:]:
        sentence += connector + p
    return sentence + "."


# ---- R14: THE BUSINESS TERM SENTENCE (v2.14.0) ----
# Brief_Pilot_Build_3 (Sunny "approved, build brief 3" 2026-09-20;
# rulings (1)-(3), (10) + Q1-Q5 "agree with all five"). One sentence
# per scope, composed from the TREE at compose time (ruling (10) —
# no new nodes; the verbatim law holds because the recompute walks
# the same tree). Replaces the from-structure lead FOR SCOPES ONLY.

# literal: grammar Grammar_Floor R14 (ruling (3) list compression)
_LIST_COMPRESS_OVER = 6
# Q4 (a) (Brief_Description_Levels, "agree with all seven
# recommendations" 2026-09-20; FL27): a list whose members carry
# noted labels compresses past 3 — the harm is rendered length
# literal: grammar Grammar_Floor R14 (the amended compression)
_NOTED_COMPRESS_OVER = 3


def _squash(name) -> str:
    """The name-matching fold shared by the render-join and the
    head map: separators dropped, lowered, leading # stripped."""
    return re.sub(r"[\s_\W]+", "", str(name or "")).lower()


def _bt_target_phrase(target, blessed) -> str:
    """The R14 source register: a same-tree scope speaks 'the
    <author words> selection' (no 'defined earlier' tail — the
    sentence IS the definition, not a narration); a table speaks
    '<words> records', blessed name first."""
    t = str(target or "")
    if "::" in t:
        # the readable fold (camel split — the worked examples'
        # register: 'the main adm details selection'), not R11's
        # spoken fold; the render-join matches through _squash so
        # the two registers never collide
        words = _readable_name(t.rsplit("::", 1)[-1].lstrip("#"))
        return f"the {words} selection"
    if blessed and t in blessed:
        words = blessed[t]
    else:
        raw = t.rsplit("|", 1)[-1] if "|" in t else t.split(".")[-1]
        words = re.sub(r"[_\W]+", " ",
                       raw.lstrip("#")).strip().lower()
    if not words:
        return "an inline selection"
    return words if words.endswith("records") else f"{words} records"


def _bt_base(shape):
    """The base source: from_refs[0], resolved THROUGH derived
    scopes (ruling (10) — the composer reads the tree; the
    prototype's 'An inline selection' limit closes here). Returns
    a target: a table identity, a same-tree scope key, a raw
    table_ref name, or None."""
    refs = shape.get("from_refs") or []
    if not refs:
        return None
    ref = refs[0]
    for _ in range(5):
        if "derived_scope" not in ref:
            break
        inner = ref["derived_scope"]
        if "combination_arms" in inner:
            inner = inner["combination_arms"][0]
        inner_refs = inner.get("from_refs") or []
        if not inner_refs:
            return None
        ref = inner_refs[0]
    if "derived_scope" in ref:
        return None
    resolved = ref.get("resolves_to")
    if resolved and str(resolved).startswith("SAME-TREE"):
        return str(resolved).replace("SAME-TREE scope ", "")
    return resolved or ref.get("table_ref")


def _bt_membership(shape, base_target, voice):
    """Ruling (2): inner joins spoken as MEMBERSHIP, their non-key
    ON residues riding the member parenthetically; a residue whose
    sides are all already spoken falls to the population items —
    counted into the sentence, never dropped. Outer joins and
    outer-apply lookups never enter (they do not restrict)."""
    from aisql.flows import inbound
    known = {str(base_target)} if base_target else set()
    members: List[str] = []
    loose: List[str] = []
    joined_targets = set()
    for pred in inbound._join_entries(shape):
        targets = inbound._join_targets(pred)
        joined_targets.update(str(t) for t in targets)
        if str(pred.get("join_type") or "Inner") != "Inner":
            continue
        vals = []
        for leaf in decisions.flatten_where(pred):
            if decisions.is_join_key(leaf) \
                    or decisions.is_degenerate(leaf):
                continue
            txt = _bt_condition(leaf, voice)
            if txt:
                vals.append(txt[0].lower() + txt[1:])
        placed = False
        for target in targets:
            t = str(target)
            if t in known:
                continue
            known.add(t)
            phrase = _bt_target_phrase(target, voice.blessed)
            if vals and not placed:
                phrase += " (" + "; ".join(vals) + ")"
                placed = True
            members.append(phrase)
        if vals and not placed:
            loose.extend(v[0].upper() + v[1:] for v in vals)
    # leftover FROM sources (comma joins): linked sources join the
    # membership; linkless ones voice neutrally (the v1.3.0 posture)
    linked = any(decisions.is_join_key(leaf)
                 for leaf in decisions.flatten_where(
                     shape.get("where")))
    combined: List[str] = []
    for ref in (shape.get("from_refs") or [])[1:]:
        if ref.get("outer_apply") or "derived_scope" in ref:
            continue
        resolved = ref.get("resolves_to")
        if resolved and str(resolved).startswith("SAME-TREE"):
            t = str(resolved).replace("SAME-TREE scope ", "")
        else:
            t = str(resolved or ref.get("table_ref") or "")
        if not t or t in known or t in joined_targets:
            continue
        known.add(t)
        phrase = _bt_target_phrase(t, voice.blessed)
        (members if linked else combined).append(phrase)
    return members, combined, loose


def _compressed_list(pred, voice, negated=False) -> Optional[str]:
    """Ruling (3): value lists longer than the threshold speak a
    COUNT in the sentence; the full list stays on the condition
    row (condition_render is untouched — derivable, never lost)."""
    if pred.get("kind") != "IN_LIST":
        return None
    members = pred.get("comparand_list") or []
    n = len(members)
    subj_expr = pred.get("subject", {})
    # Q4 (a): noted-label members (an annotation or a values-map
    # meaning) compress sooner — their labels are the length
    noted = any(_member_noted(m, subj_expr, voice) for m in members)
    over = _NOTED_COMPRESS_OVER if noted else _LIST_COMPRESS_OVER
    if n <= over:
        return None
    subj = voice.subject(subj_expr)
    word = "none" if negated else "one"
    return f"The {subj} is {word} of {n} values"


def _member_noted(m, subj_expr, voice) -> bool:
    if m.get("annotation"):
        return True
    col_id = subj_expr.get("resolves_to") or ""
    values = voice._columns.get(col_id, {}).get("values") or {}
    return str(m.get("value", "")).strip("'") in values


def _bt_condition(pred, voice) -> str:
    """The R14 condition voice: the ratified renders (one home —
    condition_render), fully recursive, degenerates pruned, long
    lists compressed at compose time only."""
    from aisql.flows import inbound

    def phrase(p, top):
        kind = p.get("kind", "")
        kids = p.get("children") or []
        if kind == "NOT" and kids:
            compressed = _compressed_list(kids[0], voice,
                                          negated=True)
            if compressed:
                return compressed
        if p.get("node") == "predicate":
            if decisions.is_degenerate(p):
                return ""
            compressed = _compressed_list(p, voice)
            if compressed:
                return compressed
            return inbound.condition_render(p, voice).rstrip(".")
        if kind not in ("OR", "AND") or not kids:
            return inbound.condition_render(p, voice).rstrip(".")
        sub = [phrase(k, False) for k in kids]
        sub = [s for s in sub if s]
        if not sub:
            return ""
        if len(sub) == 1:
            return sub[0]
        lowered = [s[0].lower() + s[1:] for s in sub]
        if kind == "AND":
            return " and ".join(lowered)
        joined = " or ".join(lowered)
        return joined if top else "either " + joined

    return phrase(pred, True)


_BETWEEN = re.compile(r"^(The .*?) is between (.*)$")


def _merge_betweens(texts: List[str]) -> List[str]:
    """Q3 RULED: identical subjects' betweens join with 'or between'
    — pure structure, no invention."""
    rest: List[str] = []
    by_subject: Dict[str, List[str]] = {}
    order: List[str] = []
    for t in texts:
        m = _BETWEEN.match(t)
        if m:
            if m.group(1) not in by_subject:
                order.append(m.group(1))
            by_subject.setdefault(m.group(1), []).append(m.group(2))
        else:
            rest.append(t)
    merged = [f"{s} is between " + " or between ".join(
        dict.fromkeys(by_subject[s])) for s in order]
    return merged + rest


def _bt_rank_member(shape, scopes_by_key, colname):
    """Ruling (1): the rank filter's ROW_NUMBER member, found in the
    scope's SOURCES (the computing scope) — the partition speaks at
    the scope that APPLIES the filter, never where it is computed."""
    fold = str(colname).upper()
    sources = []
    for ref in shape.get("from_refs") or []:
        if "derived_scope" in ref:
            inner = ref["derived_scope"]
            if "combination_arms" in inner:
                inner = inner["combination_arms"][0]
            sources.append(inner)
            continue
        r = str(ref.get("resolves_to") or "")
        if r.startswith("SAME-TREE"):
            sc = scopes_by_key.get(r.replace("SAME-TREE scope ", ""))
            if sc is not None:
                arms = sc.get("combination_arms")
                sources.append(arms[0] if arms else sc)
    for src in sources:
        for m in src.get("projection") or []:
            if str(m.get("name") or "").upper() != fold:
                continue
            e = m.get("expression") or {}
            if e.get("kind") == "function" \
                    and str(e.get("name") or "").upper() \
                    == "ROW_NUMBER":
                return m
    return None


def _bt_rank_match(pred, shape, scopes_by_key):
    """A leaf of the form <ranking column> = 1 whose column IS a
    source's ROW_NUMBER member — structure, not population."""
    if pred.get("node") != "predicate" \
            or pred.get("kind") != "COMPARE_EQ":
        return None
    subject = pred.get("subject") or {}
    comparand = pred.get("comparand") or {}
    if subject.get("kind") != "column_ref" \
            or comparand.get("kind") != "literal" \
            or str(comparand.get("value")) != "1":
        return None
    colname = str(subject.get("ref") or "").rsplit(".", 1)[-1]
    return _bt_rank_member(shape, scopes_by_key, colname)


def _bt_where_items(shape, voice, scopes_by_key, rank) -> List[str]:
    where = shape.get("where")
    if where is None:
        tops = []
    elif where.get("kind") == "AND":
        tops = list(where.get("children") or [])
    else:
        tops = [where]
    items: List[str] = []
    for t in tops:
        if t.get("node") == "predicate":
            if decisions.is_degenerate(t) or decisions.is_join_key(t):
                continue
            member = _bt_rank_match(t, shape, scopes_by_key)
            if member is not None:
                rank["kept"] = True
                if rank["member"] is None:
                    rank["member"] = member
                continue
        txt = _bt_condition(t, voice)
        if txt:
            items.append(txt[0].upper() + txt[1:])
    return _merge_betweens(list(dict.fromkeys(items)))


def _bt_grain_words(expr, voice) -> str:
    if expr.get("kind") == "column_ref":
        return voice.name_words(expr)
    return _bare(_defining_phrase(expr, voice))


def _bt_grain(shape, voice, rank_member):
    """Ruling (1): grain speaks from definitional sources ONLY —
    GROUP BY, DISTINCT, the rank-filter partition (slice E's
    capture); no source -> no grain clause, never an invention.
    Returns (grain clause, partition_spoken)."""
    group_by = shape.get("group_by")
    if group_by:
        words = " and ".join(_bt_grain_words(g, voice)
                             for g in group_by)
        return f"One record per {words}", False
    if shape.get("distinct"):
        names = [m.get("name") for m in shape.get("projection") or []
                 if m.get("name")]
        if names and len(names) <= 4:
            listed = " and ".join(_readable_name(n) for n in names)
            return f"One record per distinct {listed}", False
        return "One record per distinct combination of its columns", \
            False
    if rank_member is not None:
        over = (rank_member.get("expression") or {}).get("over")
        if isinstance(over, dict) and over.get("partition_by"):
            words = " and ".join(_bt_grain_words(p, voice)
                                 for p in over["partition_by"])
            return f"One record per {words}", True
    return None, False


def _bt_payload(shape, voice) -> str:
    """Q1 RULED: named business outputs first (the dcols, by name),
    then the carried-through count; the full list stays on the
    nodes (derivable)."""
    from aisql.flows import inbound
    projection = [m for m in shape.get("projection") or []
                  if isinstance(m, dict)]
    named = list(dict.fromkeys(
        _readable_name(m["name"]) for m in projection
        if inbound._is_derived_node(m) and m.get("name")))
    if named:
        carried = max(0, len(projection) - len(named))
        head = ", ".join(f"the {w}" for w in named[:8])
        more = (f" and {len(named) - 8} more computed columns"
                if len(named) > 8 else "")
        tail = ""
        if carried:
            word = "column" if carried == 1 else "columns"
            tail = f", and {carried} carried-through {word}"
        return f"carrying {head}{more}{tail}"
    cols = [m.get("name") for m in projection if m.get("name")][:6]
    if not cols:
        return ""
    more = (f" and {len(projection) - len(cols)} more columns"
            if len(projection) > len(cols) else "")
    return ("carrying "
            + ", ".join(f"the {_readable_name(c)}" for c in cols)
            + more)


def scope_sentence(read: ReadApi, tree, scope) -> str:
    """R14 — the scope's ONE stored sentence (the Business Term
    shape, ruling (3)): grain-or-base lead · membership ·
    population · payload. Out-of-class scopes keep their ruled
    sentences (delete = removal; unmapped = the honest counted
    state)."""
    if scope.get("unmapped_shape"):
        return ("The logic of this selection is not yet modeled "
                f"(unmapped query shape: {scope['unmapped_shape']}); "
                "its contents are counted for engineering review, "
                "never described by guess.")
    voice = _Voice(read, tree)
    if scope.get("operation") == "delete":
        ref = scope["from_refs"][0]
        phrase = _source_phrase(ref.get("table_ref"),
                                ref.get("resolves_to"), [],
                                blessed=voice.blessed)
        return f"This step removes records from {phrase}."
    arms = scope.get("combination_arms")
    shape = arms[0] if arms else scope
    scopes_by_key = {s["name_key"]: s
                     for s in decisions.named_scopes(tree)
                     if s.get("name_key")}
    base_target = _bt_base(shape)
    members, combined, loose = _bt_membership(shape, base_target,
                                              voice)
    rank = {"member": None, "kept": False}
    if arms:
        per_arm = [set(_bt_where_items(a, voice, scopes_by_key,
                                       rank))
                   for a in arms]
        shared = set.intersection(*per_arm) if per_arm else set()
        texts = sorted(shared)
        diffs = [sorted(p - shared) for p in per_arm]
        if any(diffs):
            alt = "; ".join(
                (f"({i + 1}) " + "; ".join(d)) if d
                else f"({i + 1}) —"
                for i, d in enumerate(diffs))
            texts.append(f"in {len(arms)} alternatives: {alt}")
    else:
        texts = _bt_where_items(shape, voice, scopes_by_key, rank)
    texts = loose + texts
    grain, partition_spoken = _bt_grain(shape, voice, rank["member"])
    if grain:
        lead = grain
    elif base_target:
        lead = _bt_target_phrase(base_target, voice.blessed)
    elif shape.get("from_refs"):
        lead = "an inline selection"
    else:
        # the no-source scope (the 2.4.0 restoration's class) —
        # the ruled words wear the sentence's lead slot
        lead = "derived values (no source records are read)"
    sentence = lead[0].upper() + lead[1:]
    if members:
        sentence += ", matched in " + " and in ".join(members)
    if combined:
        sentence += ", combined with " + " and ".join(combined)
    population = "; ".join(texts)
    if population:
        sentence += ": " + population
    kept = rank["kept"] and not partition_spoken
    if kept:
        sentence += "; the first record in its ordered sequence kept"
    payload = _bt_payload(shape, voice)
    if payload:
        sentence += (("; " if population or kept else ", ")
                     + payload)
    return sentence + "."


def scope_head(sentence) -> Optional[str]:
    """The sentence's grain-or-base HEAD CLAUSE — what the Q5
    render-join borrows. Derivable from the stored sentence; None
    when the head says nothing ('An inline selection')."""
    head = str(sentence or "").split(":")[0].split(";")[0]
    head = head.split(", matched in")[0]
    head = head.split(", combined with")[0]
    head = head.split(", carrying")[0]
    head = head.rstrip(".").strip()
    if not head or head.lower() == "an inline selection":
        return None
    return head


def scope_meaning(sentence) -> Optional[str]:
    """Q3 (b) (Brief_Description_Levels, built 2026-09-20): the
    scope's sentence MINUS the payload tail — what the END-USER
    statement line wears. Derivable from the stored sentence;
    None when nothing meaningful remains (scope_head's rule)."""
    s = str(sentence or "").rstrip(".")
    for sep in ("; carrying ", ", carrying "):
        i = s.find(sep)
        if i >= 0:
            s = s[:i]
            break
    s = s.strip().rstrip(";").strip()
    if not s or s.lower() == "an inline selection":
        return None
    return s


_BUILDS_LINE = re.compile(r"^Builds the ([\w ]+) selection")


def statement_display(text, heads) -> str:
    """Q5 RULED ("agree with all five"): at RENDER the statement
    borrows the built scope's head clause — a derivable display
    join; NOTHING new stored (the clause lives once, on the
    scope). `heads` maps _squash(scope name) -> head clause."""
    m = _BUILDS_LINE.match(text or "")
    if not m:
        return text
    head = (heads or {}).get(_squash(m.group(1)))
    if not head:
        return text
    borrowed = head[0].lower() + head[1:]
    return text.replace(
        f"Builds the {m.group(1)} selection",
        f"Builds the {m.group(1)} selection ({borrowed})", 1)


def statement_enduser(text, meanings) -> str:
    """Q3 (b) (Brief_Description_Levels, built 2026-09-20): the
    END-USER statement line — 'Builds the <x> selection: <what
    belongs in it>', the scope's sentence minus the payload tail,
    colon-joined. Render-time only (dry_run); R13's pipeline keeps
    statement_display's head clause so the stored TD stands
    byte-identical (Q1 (b)). `meanings` maps _squash(scope name)
    -> scope_meaning(sentence)."""
    m = _BUILDS_LINE.match(text or "")
    if not m:
        return text
    meaning = (meanings or {}).get(_squash(m.group(1)))
    if not meaning:
        return text
    lowered = meaning[0].lower() + meaning[1:]
    return text.replace(
        f"Builds the {m.group(1)} selection",
        f"Builds the {m.group(1)} selection: {lowered}", 1)


def voicing_ledger(read: ReadApi, target: str) -> Dict[str, int]:
    """THE VOICING LEDGER (ruling 4a; ADR 0044 clause 5 generalized):
    every membership-grain decision in the scope is VOICED or COUNTED
    — voiced + counted == total, disjoint, queryable. Silent omission
    has no constructible path."""
    tree, scope = None, None
    for t in read.trees().values():
        for s in decisions.named_scopes(t):
            if s["name_key"] == target:
                tree, scope = t, s
    if scope is None:
        raise KeyError(target)
    voice = _Voice(read, tree)
    voiced = counted = 0
    detail: Dict[str, int] = {}
    for pred in decisions.membership_predicates(scope):
        if decisions.is_degenerate(pred):
            counted += 1
            detail["degenerate_policy_silent"] = \
                detail.get("degenerate_policy_silent", 0) + 1
        elif _voice_predicate(pred, voice):
            voiced += 1
        else:
            counted += 1
            detail["remainder_unvoiced"] = \
                detail.get("remainder_unvoiced", 0) + 1
    arms = [scope] + scope.get("combination_arms", [])
    outer = sum(1 for s in arms for on in s.get("join_on", [])
                if str(on.get("join_type")) != "Inner")
    counted += outer
    if outer:
        detail["outer_match_conditions"] = outer
    total = voiced + counted
    # literal: shape
    return {"voiced": voiced, "counted": counted, "total": total,
            "detail": detail}


def compose_floor(read: ReadApi, target: str) -> str:
    """The ratified grammar, rule by rule, over the graph's facts."""
    tree, scope = None, None
    for t in read.trees().values():
        for s in decisions.named_scopes(t):
            if s["name_key"] == target:
                tree, scope = t, s
    if scope is None:
        raise KeyError(f"no scope {target} in the parsed estate")
    return _compose_scope(read, tree, scope)


def _compose_scope(read: ReadApi, tree, scope,
                   include_lead: bool = True) -> str:
    # An unmapped query shape NEVER floors as a claim — the old walk
    # laundered the counted gap into 'no source records are read'
    # (Sunny's ABX corpse). Absence over fabrication.
    if scope.get("unmapped_shape"):
        return ("The logic of this selection is not yet modeled "
                f"(unmapped query shape: {scope['unmapped_shape']}); "
                "its contents are counted for engineering review, "
                "never described by guess.")
    # COMBINATION (grammar 2.1.0, the ABX corpse): lead from the first
    # arm, the combination fact voiced, each arm's composition and
    # conditions voiced in arm order (arm order is meaning)
    if "combination_arms" in scope:
        arms = scope["combination_arms"]
        dupes = ("duplicates kept" if scope.get("combination_all")
                 else "duplicates removed")
        # literal: schema-mirror kg2_kind_library
        kind_words = {"Union": "combination",
                      "Except": "difference",
                      "Intersect": "intersection"}
        word = kind_words.get(str(scope.get("combination")),
                              "combination")
        first_arm_lines = _compose_scope(read, tree, arms[0],
                                         include_lead=True).split("\n")
        lines = [first_arm_lines[0],
                 f"This selection is the {word} of {len(arms)} "
                 f"alternative selections ({dupes})."]
        # literal: grammar Grammar_Floor R2
        ordinals = ("first", "second", "third", "fourth", "fifth")
        for i, arm in enumerate(arms):
            marker = ordinals[i] if i < len(ordinals) else f"#{i + 1}"
            body = _compose_scope(read, tree, arm, include_lead=False)
            lines.append(f"The {marker} alternative:")
            lines.extend(body.split("\n"))
        return "\n".join(line for line in lines if line)
    voice = _Voice(read, tree)
    tables = {n.identity: n.properties for n in read.nodes("table")}
    # R1 — the lead
    reads_tables, lead_grain = False, None
    for ref in scope.get("from_refs", []):
        rt = ref.get("resolves_to") or ""
        if rt in tables:
            reads_tables = True
            if lead_grain is None and tables[rt].get("grain"):
                lead_grain = tables[rt]["grain"]
    if not include_lead:
        lines = []
    elif scope.get("operation") == "delete":
        # a DELETE shapes a population by REMOVAL — 'a selection'
        # would misstate the act (ledger-close, 2026-09-06)
        ref = scope["from_refs"][0]
        phrase = _source_phrase(ref.get("table_ref"),
                                ref.get("resolves_to"), [],
                                blessed=voice.blessed)
        lines = [f"This step removes records from {phrase}."]
    elif not reads_tables and not scope.get("from_refs"):
        # THE RESTORATION (grammar 2.4.0): this elif was REPLACED
        # by the delete branch at the ledger-close (e8dd8a9) —
        # DELETE floors lied 'derived values' and no-source floors
        # fell to the fallback (the 'Constant' corpse) ever since
        lines = ["This step produces derived values; no source records "
                 "are read."]
    elif lead_grain:
        lines = [f"This is a selection of {_pluralize(lead_grain)}."]
    else:
        # Grammar 2.4.0 (Sunny's ruling 2026-09-11): the constant
        # no-grain opener is DEAD — the composition sentence LEADS;
        # the degenerate guard below keeps the minimal sentence
        # only when the floor would otherwise be empty
        lines = []
    # Grammar 2.0.0 — the composition sentence (the finding-4 heir):
    # sources + join composition, from the same facts the twin's
    # source nodes hold; reference phrases, never raw temp names
    ledger_counts: Dict[str, int] = {}
    composition = _composition_sentence(read, tree, scope, ledger_counts,
                                        blessed=voice.blessed)
    if composition:
        lines.append(composition)
    # R2 + R6 — one bullet per membership decision (dedup at PREDICATE
    # IDENTITY grain, v1.1.0 — the ED-sepsis two-alias corpse: two
    # predicates that render alike are still two decisions), degenerate
    # silent. Multi-instance reads carry the instance marker.
    alias_instance: Dict[str, str] = {}
    reads_per_table: Dict[str, List[str]] = {}
    for ref in scope.get("from_refs", []):
        rt = ref.get("resolves_to") or ""
        if rt in tables and ref.get("alias"):
            reads_per_table.setdefault(rt, []).append(ref["alias"])
    # literal: grammar Grammar_Floor R2
    ordinals = ("first", "second", "third", "fourth", "fifth", "sixth")
    for rt, aliases in reads_per_table.items():
        if len(aliases) < 2:
            continue
        words = voice.blessed.get(rt) or re.sub(
            r"[_\W]+", " ", rt.rsplit("|", 1)[-1]).strip().lower()
        for i, alias in enumerate(aliases):
            marker = ordinals[i] if i < len(ordinals) else f"#{i + 1}"
            alias_instance[alias] = f"For the {marker} {words} record read: "
    bullets = []
    for pred in decisions.membership_predicates(scope):
        if decisions.is_degenerate(pred):
            continue
        phrase = _voice_predicate(pred, voice)
        if not phrase:
            continue
        note = pred.get("annotation")
        if note:  # R8: attributed, never bare fact
            phrase = (phrase.rstrip(".")
                      + f" (annotated '{note}' in the source).")
        subject_ref = pred.get("subject", {}).get("ref", "")
        alias = subject_ref.split(".")[0] if "." in subject_ref else None
        prefix = alias_instance.get(alias, "")
        if prefix:
            phrase = prefix + phrase[0].lower() + phrase[1:]
        bullets.append(f"- {phrase}")
    # R7 — the honest no-conditions fact
    if not bullets and reads_tables:
        bullets = ["- No membership conditions are applied in this "
                   "selection."]
    if include_lead and not lines:
        # the degenerate guard (2.4.0): only when NO lead and NO
        # composition exist does the minimal sentence survive — a
        # floor never opens with a bare bullet
        lines = ["This is a selection of records."]
    return "\n".join(lines + bullets)


def _scope_lead(read: ReadApi, tree, scope) -> str:
    """A scope's lead + composition sentence — the non-bullet head of
    its floor (R10 voices scopes at file grain through this)."""
    lead = []
    for line in _compose_scope(read, tree, scope).split("\n"):
        if line.startswith("- ") or line.endswith("alternative:"):
            break
        lead.append(line)
        if len(lead) == 2:
            break
    return " ".join(lead)


def compose_file_floor(read: ReadApi, target: str) -> str:
    """R10 — THE REPORT FLOOR (grammar 2.3.0, live find #9): a file's
    floor composes from its scopes. Deliveries LEAD, the spine walks
    back to base selections (voiced), intermediates are COUNTED
    (voiced + counted == total extends to file grain), the census
    closes — honest mechanics, never the lead. Deterministic; the
    model adds nothing."""
    tree = None
    for k, t in read.trees().items():
        if k == target or t["name"] == target:
            tree = t
    if tree is None:
        raise KeyError(f"no file {target} in the parsed estate")
    scopes = {sc["name_key"]: sc
              for sc in decisions.named_scopes(tree)}
    deliveries = [st["scope"] for st in tree["statements"]
                  if st.get("emits") and st.get("scope")
                  and st["scope"].get("name_key")]

    lines: List[str] = []
    if not deliveries:
        lines.append("This procedure emits no result set — a "
                     "setup/maintenance script; nothing is delivered "
                     "to a reader.")
    for i, d in enumerate(deliveries):
        prefix = ("This report delivers: " if len(deliveries) == 1
                  else f"This report delivers ({i + 1} of "
                       f"{len(deliveries)}): ")
        lines.append(prefix + _scope_lead(read, tree, d))

    # the spine: every named selection the deliveries draw from,
    # transitively (arms and derived interiors included — a read is
    # a read)
    on_chain: List[str] = []

    def walk(scope):
        for ref in decisions.nested_sources(scope):
            rt = str(ref.get("resolves_to") or "")
            if rt.startswith("SAME-TREE scope "):
                nk = rt.replace("SAME-TREE scope ", "")
                if nk in scopes and nk not in on_chain:
                    on_chain.append(nk)
                    walk(scopes[nk])
    for d in deliveries:
        walk(d)

    def is_base(scope) -> bool:
        refs = decisions.nested_sources(scope)
        return bool(refs) and not any(
            str(r.get("resolves_to") or "").startswith("SAME-TREE")
            for r in refs)
    delivery_keys = {d["name_key"] for d in deliveries}
    chain = [nk for nk in scopes if nk in on_chain]  # tree order
    bases = [nk for nk in chain if is_base(scopes[nk])]
    intermediates = [nk for nk in chain if nk not in bases]
    off_chain = [nk for nk in scopes
                 if nk not in on_chain and nk not in delivery_keys]

    BASE_CAP = 5
    if bases:
        lines.append(f"Built from {len(bases)} base selection(s) "
                     "reading source tables:")
        for nk in bases[:BASE_CAP]:
            name = nk.split("::")[-1]
            lines.append(f"- {name}: "
                         + _scope_lead(read, tree, scopes[nk]))
        if len(bases) > BASE_CAP:
            lines.append(f"- … and {len(bases) - BASE_CAP} more base "
                         "selection(s) — each speaks its own floor.")
    if intermediates:
        lines.append(f"Refined through {len(intermediates)} "
                     "intermediate selection(s) — each speaks its "
                     "own floor.")
    if off_chain:
        lines.append(f"{len(off_chain)} named selection(s) sit "
                     "outside the delivery chain (counted).")
    voiced = len(delivery_keys) + min(len(bases), BASE_CAP)
    counted = (len(intermediates) + len(off_chain)
               + max(0, len(bases) - BASE_CAP))
    lines.append(f"Voicing: {voiced} voiced, {counted} counted, of "
                 f"{len(scopes)} named selections.")

    # the census closes — honest mechanics, never the lead
    names = [nk.split("::")[-1] for nk in scopes]
    lines.append(f"A procedure of {len(tree['statements'])} steps; "
                 f"named selections: "
                 f"{', '.join(names[:12]) or '(none)'}"
                 + (f" … ({len(names) - 12} more)"
                    if len(names) > 12 else "") + ".")
    return "\n".join(lines)


def file_words(read: ReadApi, target: str) -> str:
    """The file's delivery lead — a GRAMMAR RENDER (R10). Under ADR
    0080 the composed subject is the TRANSLATOR'S stored work; this
    render is only the delivery half. Total: never raises."""
    tree = None
    for k, t in read.trees().items():
        if k == target or t["name"] == target:
            tree = t
    if tree is None:
        return ""
    deliveries = [st["scope"] for st in tree["statements"]
                  if st.get("emits") and st.get("scope")
                  and st["scope"].get("name_key")]
    if not deliveries:
        return ("emits no result set; a setup or maintenance "
                "script")
    return " ".join(_scope_lead(read, tree, d)
                    for d in deliveries).lower()


def _priority(read: ReadApi, worklist: List[str]) -> List[str]:
    """ECON: usage-weighted — touch counts from the ledger; first
    contact (empty ledger) degrades to worklist order, declared."""
    touches: Dict[str, int] = {}
    for e in read.nodes("usage"):
        about = e.properties.get("about")
        if about:
            touches[about] = touches.get(about, 0) + 1
    return sorted(worklist, key=lambda t: -touches.get(t, 0))


def run(store, occurred_at: str,
        smooth: Optional[Callable[[str], str]] = None):
    """One produce run. Returns the run event node (PROD-1: the only
    production ledger)."""
    read = ReadApi(store)
    worklist = derivation.lens_staleness(read, None)["yield"]  # PROD-2
    batch = _priority(read, worklist)[:min(ECON["batch_size"],
                                           ECON["run_budget"])]
    run = run_events.open_run(
        author="agent:produce",
        # literal: shape
        basis={"floor_grammar": FLOOR_GRAMMAR_VERSION,
               "econ": ECON["version"], "metamodel": "1.0.0",
               "worklist": list(batch)},
        occurred_at=occurred_at)
    shipped, absent, killed = 0, [], 0
    # Phase D: every new machine description anchors to its scope's
    # MEANING identity at write time (the anchor rule, ruling 2f)
    keys = anchors.selection_keys(read)
    for target in batch:
        try:  # OPS-2: one append or a counted absence, never half
            floor = compose_floor(read, target)
            text, status = floor, "skeleton_floor"
            if smooth is not None:
                candidate = smooth(floor)
                tree = next(t for t in read.trees().values()
                            for s in decisions.named_scopes(t)
                            if s["name_key"] == target)
                scope = next(s for s in decisions.named_scopes(tree)
                             if s["name_key"] == target)
                violations = gates.check_text(
                    candidate, floor,
                    _Voice(read, tree).forbidden_tokens(scope))
                if not violations:
                    text, status = candidate, "gate_passed"
                else:
                    killed += len(violations)  # counted, never silent
            anchor = ({"scope": target, "content_key": keys[target]}
                      if target in keys else None)
            kg3_artifacts.append_description(
                store, artifact_id=f"description:{target}", about=[target],
                text=text, status=status, author="agent:produce",
                basis=run.basis, created_at=occurred_at, anchor=anchor)
            shipped += 1
        except Exception as err:  # noqa: BLE001 — OPS-2: absence counted w/ reason, run continues
            absent.append({"target": target, "reason": str(err)})
    # literal: shape
    run.accounting["descriptions"] = {
        "attempted": len(batch), "shipped": shipped,
        "absent": len(absent), "absent_detail": absent,
        "killed_lines": killed}
    run.accounting["terms"] = {"attempted": 0}
    return run_events.close_run(store, run, outcome="completed")
