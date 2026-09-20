"""The deterministic text gates — pure checkers (PROD-3 / GRND-2's
future consumer). PORTED essence of the proven produce gates (PM-2:
produce family only; the caption/grounding family defers with the
inward flow).

The contract: smoothing is a REPHRASING, not a rewrite. The gate
holds the candidate against the floor it was smoothed from — every
value survives, nothing is added, no raw identifier reaches steward
prose. A violation names itself; the caller's ruled response is to
ship the floor (an outage costs polish, never truth).
"""
import re
from typing import List

_QUOTED = re.compile(r"'[^']*'")
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")


def _values_in(text: str) -> set:
    return set(_QUOTED.findall(text)) | set(_NUMBER.findall(text))


# ---- R5.b THE BLESSED NAME (Grammar_Floor v2.8.0) — the subset
# gate: a blessed candidate may SELECT from the vendor's words
# (description ∪ name), never introduce one. Deterministic; no
# model; a violation names itself and the fallback voices.

# literal: grammar Grammar_Floor R5.b — the closed whitelist
_SUBJ_FUNCTION_WORDS = frozenset((
    "of", "the", "a", "an", "for", "per", "in", "on", "at", "by",
    "to", "with", "and"))
# trailing these = a cut phrase, not a name
# literal: grammar Grammar_Floor R5.b
_SUBJ_PREPOSITIONS = frozenset((
    "of", "for", "per", "in", "on", "at", "by", "to", "with"))
# the closed suffix table, longest-first (no library; reproducible)
# literal: grammar Grammar_Floor R5.b
_SUBJ_SUFFIXES = ("ing", "ion", "es", "ed", "al", "s")
_SUBJ_WORD = re.compile(r"[a-z0-9]+")


def _stems(word: str) -> set:
    """The word plus its closed-table strips — membership is
    checked stem-vs-stem, so plural/inflection either side
    matches; anything subtler is a new word and dies."""
    out = {word}
    for suf in _SUBJ_SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            out.add(word[: -len(suf)])
    return out


def check_blessed_words(candidate: str, description: str,
                        name: str) -> List[str]:
    """Named violations, [] = clean. Deterministic; no model
    consulted (the produce-gate contract)."""
    violations = []
    stripped = (candidate or "").strip()
    if not stripped:
        return ["GATE-SUBJ-4: empty candidate"]
    words = stripped.split()
    # GATE-SUBJ-4 — shape: a short name, not a sentence
    if len(words) > 4:
        violations.append(f"GATE-SUBJ-4: {len(words)} words — a "
                          "blessed name is 1-4")
    if stripped != stripped.lower():
        violations.append("GATE-SUBJ-4: not lowercase")
    # literal: grammar Grammar_Floor R5.b
    if words[0].lower() in ("the", "a", "an"):
        violations.append("GATE-SUBJ-4: leading article")
    if words[-1].lower() in _SUBJ_PREPOSITIONS:
        violations.append("GATE-SUBJ-4: trailing preposition")
    # GATE-SUBJ-3 — no raw identifier: the source identifier
    # verbatim (case-sensitive whole-token, GATE-VOICE-1's law) or
    # any identifier-shaped token (an underscore has no place in
    # steward prose)
    if name and re.search(rf"(?<![\w.]){re.escape(name)}(?![\w.])",
                          candidate):
        violations.append(f"GATE-SUBJ-3: raw identifier '{name}' "
                          "in a blessed name")
    for w in words:
        if "_" in w:
            violations.append(f"GATE-SUBJ-3: identifier-shaped "
                              f"token '{w}'")
    # GATE-SUBJ-2 — no value unless the vendor wrote it
    source_values = _values_in(description) | _values_in(name)
    for value in sorted(_values_in(candidate) - source_values):
        violations.append(f"GATE-SUBJ-2: value {value} not in the "
                          "vendor's words")
    # GATE-SUBJ-1 — the subset law: every content word exists in
    # description ∪ name (stem-matched); selection, never
    # fabrication
    source_stems: set = set()
    for tok in _SUBJ_WORD.findall(
            (description + " " + name).lower()):
        source_stems |= _stems(tok)
    for w in words:
        lw = w.lower()
        if lw in _SUBJ_FUNCTION_WORDS or lw.isdigit() or "_" in lw:
            continue  # digits are SUBJ-2's, identifiers SUBJ-3's
        if not (_stems(lw) & source_stems):
            violations.append(f"GATE-SUBJ-1: word '{w}' absent "
                              "from the vendor's words")
    return violations


def check_text(candidate: str, floor: str,
               forbidden_tokens: List[str]) -> List[str]:
    """Named violations, [] = clean. Deterministic; no model consulted."""
    violations = []
    floor_values = _values_in(floor)
    candidate_values = _values_in(candidate)
    for value in sorted(floor_values - candidate_values):
        violations.append(f"GATE-VALUE-1: value {value} dropped — every "
                          "value must survive smoothing")
    for value in sorted(candidate_values - floor_values):
        violations.append(f"GATE-VALUE-2: value {value} added — the model "
                          "never adds a fact")
    for token in forbidden_tokens:
        # CASE-SENSITIVE whole-token match: the ban is on the raw
        # identifier appearing verbatim ('APPT_STATUS_C'), never on the
        # English word it shares letters with ('encounters' vs ENCOUNTER
        # — caught by the injection cases at first build)
        if re.search(rf"(?<![\w.]){re.escape(token)}(?![\w.])", candidate):
            violations.append(f"GATE-VOICE-1: raw identifier '{token}' in "
                              "steward prose")
    if not candidate.strip():
        violations.append("GATE-SHELL-1: empty candidate")
    return violations
