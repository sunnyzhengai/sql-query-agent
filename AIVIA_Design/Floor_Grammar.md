# The Floor Grammar — v1.2.0 (RATIFIED, Sunny, 2026-09-05; amended 2026-09-06 ×2)

*v1.2.0 (Sunny's ED-sepsis gap-check, finding 1 — tier 3 of the
meaning ruling): R8 added — developer comments captured as EVIDENCE
and voiced WITH ATTRIBUTION, never as bare fact.*

*v1.1.0 (Sunny's ED-sepsis gap-check, finding 2): R2's dedup ran at
RENDERED-STRING grain and merged two distinct decisions — the same
table read under two aliases (transfer-out event vs transfer-in
event), each filtered `EVENT_SUBTYPE_CODE <> 2`, voiced once. Dedup
now runs at PREDICATE IDENTITY grain, and multi-instance reads carry
an instance marker. A version bump makes every floor-derived artifact
stale — the standing mechanism regenerates them.*

*A13 CLOSED: ratified by Sunny 2026-09-05 at slice-5 entry, per the
ruling's own schedule. This version stamps into every produce run's
basis; a grammar change is a version bump that makes every
floor-derived artifact stale. Seed: the field-proven
skeleton composer (`src/descriptions.py`, DESC-SKELETON-3 / ADR 0074,
38-test suite) — its corpus-hardened rules restated as total mappings
over the ratified kind library. Companion payload (code-consumed):
`AIVIA_Product/fixtures/F4_produce/floor_texts.json` — the exact floor
text per F4 target; on ratification F4 upgrades from interim
substring-grade to byte-exact against that payload.*

**Laws.** Every rule is a TOTAL mapping (disambiguation clause pt 1):
every input case covered, partiality only as an explicit counted
branch. One deciding example per rule — the example TESTS the model
(pt 2); each is a fixture at build. The floor's inputs come from the
GRAPH ONLY: grain (KG1), dictionary descriptions (KG1), values maps
(KG1), membership decisions (the decisions lens), parameter nodes
(KG2). The model never adds a fact; on smoothing failure THE FLOOR
SHIPS — an outage costs polish, never truth.

---

## R1 — the lead sentence

lead(scope) :=
  "This step produces derived values; no source records are read."
      if the scope reads no tables ·
  "This is a selection of {pluralize(grain(t))}." for t = the FIRST
      grain-bearing FROM ref in declaration order ·
  "This is a selection of records." if tables are read but none
      carries a grain (the grain gap is already counted in gap-census).

pluralize(phrase) := pluralize the HEAD NOUN — the word before the
first preposition (of|on|per|for|in|at|by|with), else the last word.

Deciding examples: "patient encounter" → "patient encounters" (no
preposition, last word); "diagnosis on an encounter" → "diagnoses on
an encounter" (head before "on"). The no-table branch is the
'Constant' corpus find: the lead IS the derived-values fact, never a
selection claim contradicted one bullet later.

## R2 — one bullet per membership decision

bullets(scope) := one line per decision in the scope's MEMBERSHIP set
(the decisions lens's yield — outer scope only, position order).
Dedup runs at PREDICATE IDENTITY grain, never at rendered-string
grain (v1.1.0: two predicates that render alike are still two
decisions — the ED-sepsis two-alias corpse). A filter inside a
derived table or subquery is THAT selection's decision, never this
one's (the derived-table leak corpse). Join keys never appear (they
are join_on structures, outside the membership set by construction).

Instance marking (v1.1.0): when a scope reads ONE table under
MULTIPLE aliases, each bullet whose subject binds to that table is
prefixed "For the {first|second|...} {table words} record read:" —
the instance index is the alias's declaration order among that
table's reads. Deciding example: ADT01 (transfer-out) and ADT02
(transfer-in) both filter the event subtype; the floor voices BOTH,
distinguished by instance, never merged.

## R3 — shape preservation

An OR is ONE phrase, its arms joined by " or " — splitting an OR into
bullets silently turns it into an AND (the LDA lesson). NOT voices as
"it is not the case that {inner}", except NOT EXISTS, which voices
uniformly as "no {…} exists" (every EXISTS phrase starts "a …" by
construction).

## R4 — predicate voicings (total over the kind-library closed set)

- COMPARE_EQ    → "The {subject} is {value}."
- COMPARE_NEQ   → "The {subject} is not {value}."
- COMPARE_GTE/GT/LTE/LT → temporal voicing when the subject's steward
  words contain "date" or "time": "is on or after / is after / is on
  or before / is before"; numeric voicing otherwise: "is at least /
  exceeds / is at most / is below". (Total: the word test decides
  every case; no type metadata is consulted.)
- PATTERN_MATCH → by wildcard shape of a literal pattern: trailing %
  only → "starts with '{stem}'"; leading % only → "ends with
  '{stem}'"; both → "contains '{stem}'"; anything else (incl.
  non-literal patterns) → "matches the pattern {pattern}".
- IN_LIST       → "The {subject} is one of the values {v1 ('m1'),
  v2 ('m2'), …}" — meanings from the values map where mapped, bare
  value where not; member order = declared position order.
- RANGE         → "The {subject} is between {lower} and {upper}
  (inclusive)."
- NULL_CHECK    → "The {subject} has no recorded value."
- EXISTS_SELECTION → "A matching record exists in a separately
  defined selection."
- IN_SELECTION  → "The {subject} is one of the values defined by
  another selection." (the value-set pattern: the decision's content
  lives in data — the floor says so, never enumerates it)
- QUANTIFIED_COMPARE → the comparison voicing against "every row of"
  (ALL) or "any row of" (ANY/SOME) "another selection".

Deciding example: `D.DX_CODE LIKE 'E11%'` → "The diagnosis code
starts with 'E11'."

## R5 — operand words (steward voice, graph-sourced)

- subject words := the column's DICTIONARY DESCRIPTION rendered as a
  noun phrase; raw column tokens NEVER reach prose (DESC-VOICE-3.2).
  Rendering algorithm (entailed by the ratified payload; landed at
  build per protocol step 6): take the description's FIRST sentence,
  strip the article and terminal period; if it has the shape
  "<X> of|for the <Y>", reorder to "<Y> <head(X)>" with head(X) = the
  first word of X — "date of the visit" → "visit date", "status
  category for the appointment" → "appointment status"; otherwise the
  phrase stands as written — "diagnosis code". Total; ill-fitting
  descriptions produce awkward-but-grounded words, never raw tokens.
  A column with no dictionary entry voices as the readable form of
  its name AND lands as a counted coverage gap — never silent.
- parameter := "the {name words} parameter (default {literal} when
  none is supplied)" when the file declares a default (the structural
  IF+NULL_CHECK+SET pattern); "the {name words} parameter" otherwise.
- category value := "{value} ('{meaning}')" when the subject column
  carries a values map; the bare value otherwise. Meanings resolve at
  voice time from KG1 — never stored into the sentence's basis.

Deciding example: `E.APPT_STATUS_C = 2` → "The appointment status is
2 ('Completed')."

## R6 — degenerate predicates are never voiced

A predicate in the DEGENERATE lens's yield (both-sides-literal) emits
NOTHING. The mapper captured it faithfully; the lens judged it; the
floor stays silent (voicing it raw-echoes into a gate kill that
empties the step — the OP-FRONTIER-1 live find). Deciding example:
`WHERE 1 = 1 AND …` → the 1 = 1 contributes no bullet; the floor
never contains "1 = 1" or "1=1".

## R7 — the honest no-conditions fact

A scope that reads tables and has an EMPTY membership set voices:
"- No membership conditions are applied in this selection." — zero
decisions is itself a voicable, grounded fact ("a collection of
records" said nothing). Unresolved refs never surface as prose; they
live in gap-census. Deciding example: `usp_odd_join.sql::delivery`.

## R8 — source annotations (v1.2.0; evidence, never fact)

The mapper captures a TRAILING SAME-LINE comment as the predicate's
(or IN-list member's) ANNOTATION — it is verbatim estate text, so
citing it is grounded (B1); it is an unverified developer claim, so
it never voices as bare fact. Voicing:

- predicate-level: the bullet gains " (annotated '<text>' in the
  source)". Deciding example: `EVENT_TYPE_CODE = 4  --TRANSFER OUT`
  → "The event record category is 4 (annotated 'TRANSFER OUT' in
  the source)."
- IN-list member-level: the value renders "<value> (noted '<text>')".
  Deciding example: `200108015 --MAIN 95 TOWER EAST` → "200108015
  (noted 'MAIN 95 TOWER EAST')".

Precedence: a DECLARED meaning (tier 1 values map; tier 2 confirmed
pairs) always wins the voicing; when a declared meaning and an
annotation BOTH exist and disagree, the floor voices the declared
meaning and the disagreement is COUNTED — a stale comment or a wrong
lookup, either way a steward's finding. Only trailing same-line
comments annotate (a block comment above a WHERE belongs to nothing,
deterministically); annotations cap at 60 characters, whitespace
collapsed. Annotations ride door-1-redacted text (H6) and pass
egress redaction at land like all outbound prose.

---

## Ratification effects (the A13 flip)

1. This file drops `_DRAFT`, gains `ratified: 2026-09-…`, and the
   version stamps into every produce run's basis (the run event cites
   floor-grammar v1.0.0 alongside model/prompt/lens/metamodel).
2. F4 upgrades: the interim expect/forbid substrings retire and the
   acceptance becomes byte-exact against `floor_texts.json`.
3. Any future grammar change is a VERSION change — a bump makes every
   floor-derived artifact stale (the standing staleness mechanism,
   H8's budgeted queue pacing the regeneration).
