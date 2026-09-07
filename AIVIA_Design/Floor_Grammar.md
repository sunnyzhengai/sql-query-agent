# The Floor Grammar — v2.3.0 (the REPORT FLOOR, 2026-09-07;
# v2.0.0 POLICY-WALK major 2026-09-06; v1.3.1 RATIFIED Sunny
# 2026-09-05)

*v2.3.0 (live find #9 — Sunny: "the answer is mechanical. i was
looking for a meaning at the report level. do we not translate the
report description based on the descriptions of the steps
contained?"): R10 — THE REPORT FLOOR. The grammar composed floors
at SCOPE grain only; the FILE card was a census placeholder ("A
procedure of 67 steps; named selections: ..."). Same disease class
as the flat-set finding: one level left mechanical while every
level below it speaks. R10 composes the file's floor from its
scopes — deliveries lead, the spine follows, intermediates are
COUNTED, the census closes. Corollary (find #8's second layer): the
report floor's lead becomes the file's ask-index words, so file
embeddings embed MEANING, not name-noise. Phrasing rider (truth
unchanged): a RUN of identical source phrases in the composition
sentence aggregates with a visible count ("7 inline selections",
"x records (2 reads)") — repetition is mechanics, the count is the
fact.*

*v2.2.0 (the ABX first leg, 2026-09-06 — note landed late, with
v2.3.0): IN/EXISTS subselections voice their aggregate reads and
restrictive-spine conditions (nested_membership/nested_sources);
OUTER APPLY interiors and combination arms excluded.*

*v2.1.0 (the ABX corpse, 2026-09-06 — note landed late, with
v2.3.0): COMBINATION scopes (UNION ctes) voice per arm; a counted
gap never launders into "no source records read".*

*v2.0.0 (Phase C, ADR 0077 — awaiting Sunny's gap-check verdict):
the grammar becomes the VOICING POLICY over the meaning twin
(ruling piece 4). NEW: the COMPOSITION SENTENCE after the lead —
sources + join composition ("Drawn from X, restricted to records
also present in Y"; any OUTER join demotes to "combined with" —
voicing an optional match as restriction would lie the other way);
named scope refs voice as reference phrases, never raw temp names;
anonymous derived tables inline at depth 1, deeper counted (the
depth-cap ruling). THE VOICING LEDGER: voiced + counted == total
per scope, queryable (produce.voicing_ledger). Leaf voicings
survive verbatim (R3-R8 below) plus: a column-as-VALUE voices by
steward words, and DATEADD earned its phrase (ADR 0076
evidence-ordered overlay; 12 estate uses) — the line-83 raw-token
corpse dies. R1 lead amendment: a scope reading ONLY earlier
selections is still "a selection of records", never "derived
values; no source records are read" (that lead now means literally
no sources). Rules below stand as the ratified leaf record.*

*v1.3.1 (phrasing only, no truth change — the R5 artifact corpses):
the noun-phrase rendering gains meta-boilerplate stripping ('This
column holds details about...'), comma truncation, the token-head
drop ('The ID number of the unit...' speaks about the UNIT), a
short-both-sides guard on the of/for reorder, and the reduced
relative-clause backstop. Deciding corpses: '...it became effective
id' and 'the best practice alert this'. Residual awkwardness is the
smoothing seat's job — an outage costs polish, never truth.*

*v1.3.0 (Sunny's ED-sepsis gap-check, finding 3 — the #BPA corpse):
ON-clause FILTERS of INNER joins are membership. The old build
over-applied the join-key exclusion to the whole ON clause; but only
`col = col` pairs are structure — `ALT.BPA_LOCATOR_ID = '900130001'`
riding an INNER JOIN's ON is a row filter wherever the developer
parked it (kinds name meanings, never syntax placement). OUTER-join
ON residues are NOT membership (rows survive without a match) — they
are COUNTED, never voiced as filters; the revisit trigger is a
gap-check finding that needs them voiced.*

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

## R9 — population composition (RETIRED 2026-09-06 — the
## twin-graph ruling RATIFIED)

*The twin-graph ruling ratified 2026-09-06 (see
`Twin_Graph_KG_RULING.md`, piece 4): R9 retires — the composition
sentence is the voicing-policy walk over SOURCE nodes of the
meaning tree (ruling 4c), and the depth-1 ruling below carries
forward as voicing policy. This grammar's next MAJOR version is
the policy-walk port (ruling piece 4, phased per ruling 5d).*

Discussion state (Sunny's ED-sepsis gap-check, finding 4 — the
readmit corpse): each scope gains a composition sentence voicing what
it reads — INNER joins as restriction, OUTER joins as optional match.
Architecture: composition is a LENS yield (candidate: a fourth
decisions yield beside membership|grain|value|path; registry entry
pending); R9 only voices it. No metamodel change — table_ref already
resolves to a KG1 table OR a same-tree scope. Named scope refs voice
as REFERENCE PHRASES (readable name + grain, counted naming gap),
never inlined summaries — candidate, unruled.

RULED (Sunny, 2026-09-06): anonymous derived-table scopes render
INLINE at depth 1 only; deeper nesting is COUNTED in gap-census with
the revisit trigger declared (the v1.3.0 posture).

---

## R10 — THE REPORT FLOOR (v2.3.0, file grain)

A FILE's floor composes from its scopes — deterministic, no model:

1. **The delivery lead.** Every emitting statement is a delivery
   scope (`file::delivery`, mapper A11). The report floor leads with
   what the report DELIVERS: each delivery scope's floor lead — its
   grain sentence and composition sentence. Multiple deliveries
   enumerate in statement order. A file with no delivery scope
   (setup-only scripts) says so honestly.
2. **The spine.** Walk each delivery's read chain (from_refs to
   earlier named selections, transitively) back to the base
   selections that read only real sources. Voice the base
   selection(s) by name and restriction lead; COUNT the
   intermediate steps: "built through N intermediate selections —
   each speaks its own floor." Voiced ⊎ counted == total holds at
   file grain: every named scope is either voiced (delivery, base)
   or counted (intermediate) — the voicing ledger extends.
3. **The census closes.** The step count and named-selection list
   remain as the final line — honest mechanics, never the lead.

Corollary (the ask index): a file's `words` = its report floor's
delivery lead. Files embed MEANING; the name-noise ranking of live
find #8 (a 0.05-band score spread with the true file last) becomes
structurally impossible for described files.

## Ratification effects (the A13 flip)

1. This file drops `_DRAFT`, gains `ratified: 2026-09-…`, and the
   version stamps into every produce run's basis (the run event cites
   floor-grammar v1.0.0 alongside model/prompt/lens/metamodel).
2. F4 upgrades: the interim expect/forbid substrings retire and the
   acceptance becomes byte-exact against `floor_texts.json`.
3. Any future grammar change is a VERSION change — a bump makes every
   floor-derived artifact stale (the standing staleness mechanism,
   H8's budgeted queue pacing the regeneration).
