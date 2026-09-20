# Brief_Anaphor_Clarify — the honest pure-anaphor clarify comes back (FL23) and the connection filter's anchor set gets the ruled band (FL24)

**Status: BUILT** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED) — drafted and presented 2026-09-20 at Sunny's word "draft the brief", from the 4 red pins in his AISQL_RECORD run (4 failed / 816 passed); APPROVED same day at his "agree with all four, build it" — all four ambiguities ruled, quoted below; BUILT same day: suite 823 passed / 0 failed (11:23), the 4 red pins green + 3 new pins; CLOSED at his word

| field | content |
|---|---|
| class | TWO slices. Slice 1 (FL24) proposed as a FIX — the 2026-09-11 matched-graph ruling defines the band as "≥ MATCH_SCORE **and within UNIQUE_MARGIN of the best** — registry thresholds, nothing new minted" (Design_Chatbot, SET FORMATION); ask()'s connection-filter anchor set (ask.py:632) implements only the first clause, so the code returns to the ruled band. Whether that ruling governs this surface is ambiguity (3) — Sunny's reading decides fix vs update. Slice 2 (FL23) is an UNPLANNED ADDITION — no ruled section says what a reference-marked mention that names NOTHING in the estate does when the context table is empty; blocked on ruling (1) |
| claims | Contract_Logic_Layer FL23 + FL24 (landed 2026-09-20, from the first measurement of the Build_3 store on Sunny's recorded vectors) · Design_Chatbot Law 3 (the honest clarify) · Law 4 + the 22:27 corpse rule (a role-mark is a proposal, never a veto — ask.py:531, pinned by test_overmarked_reference_never_vetoes_the_search) · the 2026-09-11 MATCHED-GRAPH ruling's band definition · Echo Law (the honest pure-anaphor clarify has now died TWICE on the 2026-09-09 beat — this brief is the generator-level build, not a third patch) |
| impacts (computed, step-2 query) | ONE WRITER, both slices: aisql/flows/ask.py `ask()` — no other code moves. CONSUMERS: the ask/meaning console surface (aisql/console.py calls ask(), itself unchanged) and the 4 red pins. NO stored node/edge field changes → NO export regen, NO Fabric load, verbatim law untouched. REGISTRIES: no new rows — UNIQUE_MARGIN already lives in lenses.json (today consumed only by grounding.py:309; gains ask()'s anchor set as a second consumer). DOCS same breath: Design_Chatbot gains the ruled text (Law 3's reference-lane rule; the band clause cited at the Law-4 filter), Contract_Logic_Layer FL23/FL24 statuses flip at close, TEST_MAP regen (devtools/suite_map.py), CHANGELOG. TESTS: the 4 red pins ARE the acceptance tests — reality authored the RED; two new distinction pins ride (below). RECORDING: new pins reuse already-recorded query texts, so NO AISQL_RECORD run is expected; if a new text proves unavoidable it lands as a declared RecordingGap for his run (placeholder law). WHEEL: ambiguity (4) |
| ambiguities (ALL FOUR RULED — Sunny "agree with all four, build it", 2026-09-20: (1) Option A the estate-vocabulary gate; (2) the vocabulary boundary confirmed — name tokens + label tokens + blessed acronym names, never speech text; (3) the 2026-09-11 band definition GOVERNS ask()'s anchor set → slice 1 is a FIX; (4) the wheel rides the next release at his word, no churn before his pending 2.4.0 re-run) | **(1) FL23's mechanism — which rule brings the honest clarify back?** OPTION A (recommended): THE ESTATE-VOCABULARY TEST — a reference-marked mention searches as text (the corpse rule stands) ONLY if at least one of its tokens is a NAME or LABEL token somewhere in the estate's ask index, or a blessed acronym; a reference-marked mention with NO estate token and NO context table has nothing to say and nothing to search — the hard "nothing to refer back to" clarify fires. Deterministic, no new threshold, no hand-authored word list — the estate's OWN names decide (Law 4's shape). Measured separation on sepsis: 'it' / 'those' / 'that' / 'them' are in NO name or label; 'ed' / 'iv' / 'ett' / 'sepsis' ARE. The 22:27 corpse pin passes byte-identically ('ED' is an estate word → searches as text → answers). OPTION B: the Law-3 D1 EVIDENCE PROFILE applied to the reference-marked-empty-table lane — clear winner → provisional answer, close cluster → clarify with candidates. Also fixes the 3 tests (for "it" the top two sums gap by 0.0023 — a cluster), but it changes the corpse lane's shape (a lone content-word reference whose hits cluster would clarify instead of answer) and rides on score margins that re-shuffle whenever any stored speech re-voices — the exact instability FL23 names. OPTION C: move MATCH_SCORE — REJECTED as proposed: 'it' vs the name card 'ett' scores 0.6322, so the bar would need to pass 0.63, and the corpse's real matches sit at 0.5005 and would die; a third cliff patch on the same beat. **(2) FL23's vocabulary definition** — vocabulary = the ask index's NAME tokens + LABEL tokens + blessed acronym names, and NEVER speech/description text (stored English sentences contain 'it'; including speech would re-kill the clarify). Confirm this exact boundary. **(3) FL24's class** — does the 2026-09-11 SET-FORMATION band ("≥ MATCH_SCORE and within UNIQUE_MARGIN of the best") govern ask()'s connection-filter anchor set? YES → slice 1 is a fix (code returns to ruled design). NO (that ruling spoke only to the console's steps 3–5) → slice 1 is an update needing its own ruled row. Measured either way: anchors for the fu1 mention fall 409 → 31, the pool keeps reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop, drops reporting/USP_IP_SEPSIS.sql::#Base_Pop — the pin goes green. **(4) the wheel** — ride the next release at his word, or cut 2.4.1 now? His 2.4.0 work re-run is still pending in the queue; no churn before it unless he says so |
| debt declared | none — no placeholders, no deferrals; the 4 red pins stand un-skipped until the build lands (the suite stays honestly red under DRAFT) |
| retirement (pivots only, the 2026-09-19 law) | none — no code retires; the searched-as-text lane, the card-grain MATCH split, and the corpse rule all STAND; slice 2 only adds the vocabulary gate in front of the lane, slice 1 only adds the ruled margin clause to the anchor comprehension |
| does this promote? (the Promotion Gate) | at close, at his word, after the full suite is green — no served data moves, so no load gates it |
| Sunny's approval | (pending — presented 2026-09-20) |
| closing check | BALANCED (2026-09-20): 9 files changed == 9 declared-and-touched + 1 declared no-op reasoned (tests/aisql/test_ask_console.py — its pins fu1/cs1 already existed and went green with no edit); suite 823 passed / 0 failed / 25 skipped / 3 xfailed (11:23); ruff: touched files clean, the 18 remaining pre-exist in untouched files; TEST_MAP regen (only TEST_MAP.md changed under generate_docs.py); no export regen, no load (no stored field changed); the wheel rides the NEXT release per ruling (4) |

## Files declared

    AIVIA_Design/briefs/Brief_Anaphor_Clarify.md
    aisql/flows/ask.py
    tests/aisql/test_search_is_the_answer.py
    tests/aisql/test_ask_console.py
    AIVIA_Design/Design_Chatbot.md
    AIVIA_Design/Contract_Logic_Layer.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Manifest_Build.md
    docs/architecture/TEST_MAP.md
    CHANGELOG.md

## The two findings, measured (2026-09-20, Sunny's recorded vectors — the Build_3 store's first measurement)

Nothing in the search code changed — ask.py and grounding.py are
byte-identical to the last commit. Brief_Pilot_Build_3's R14
sentences re-voiced the scopes' SPEECH cards (292 newly recorded
texts); the new scores re-shuffled the sum-ranked band, and four
pins that were green at 792/0 now measure differently.

| query (searched as text) | identities ≥ 0.25 floor | strongest single card | top-2 sum gap |
|---|---|---|---|
| `it` | 3,467 of ~3,548 | **0.6322** — the NAME card `'ett'` of scope reporting/USP_IP_SepsisDetails.sql::#ETT, riding at rank #16 of the top-48 band | 0.0023 |
| `ED` (the 22:27 corpse's word) | 4,462 | 0.5005 — condition reports/USP_RPTS_ED_Sepsis.sql::#ED2GEN::c0 | 0.0008 |
| `those` | 5,727 | 0.4595 (below MATCH_SCORE) | 0.0000 |

**FL23 (3 of the 4 red pins).** "it" with an empty context table
answers about #ETT instead of clarifying, because one name card
clears MATCH_SCORE inside the band. A pronoun and a three-letter
scope name separate by NO threshold, and band membership shifts
whenever ANY stored description re-voices — the honest clarify is
hostage to unrelated voicing changes. Second death on the
2026-09-09 beat → Echo Law: build the generator-level mechanism.

**FL24 (the 4th red pin).** The mention
`reports/USP_RPTS_ED_Sepsis.sql` yields 409 identities with a card
≥ 0.5 — nearly every pbi_report in the estate — so Law 4's
connection filter's anchor set spans the estate, everything in the
context pool connects to SOMETHING, and the filter cannot filter.

## Slice 1 — FL24: the anchor set gets the ruled band (build first, it is measured green)

The ruled words (Design_Chatbot, the 2026-09-11 MATCHED-GRAPH
ruling, SET FORMATION): "semantic hits form THE BAND (≥
MATCH_SCORE **and within UNIQUE_MARGIN of the best** — registry
thresholds, nothing new minted)." ask.py:632's anchor
comprehension keeps every non-table hit at ≥ MATCH_SCORE and
never applies the margin clause. The change: the anchor set
becomes cards ≥ MATCH_SCORE AND ≥ (best card − UNIQUE_MARGIN).

Measured on the store: anchors 409 → 31; the fu1 pool keeps
`reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop`, drops
`reporting/USP_IP_SEPSIS.sql::#Base_Pop` — pin green. `strong`
(the honest-clarify judgment) is NOT touched by this slice; the
band-of-one case is FL23's territory.

## Slice 2 — FL23: the vocabulary gate (blocked on rulings 1 + 2)

Under Option A: before the searched-as-text lane runs for a
reference-marked mention with an empty table, the mention's tokens
are checked against the estate's own words — the ask index's name
tokens + label tokens + blessed acronym names (never speech text).
No estate token → the mention contributes NO text search; if no
other mention answers strongly, the existing hard clarify
("nothing to refer back to — ask a direct question first") fires
exactly as written. At least one estate token → today's behavior,
unchanged, including the corpse pin.

## Tests (RED first — reality already authored the RED)

1. The 4 red pins are the acceptance tests: test_pure_anaphor_with_empty_table_still_clarifies · test_cs1_context_is_conversation_scoped · test_typing_after_a_clarify_never_crashes · test_fu1_those_filters_by_connection.
2. NEW distinction pin: a reference-marked ESTATE word with an empty table still searches as text and answers (the corpse shape, pinned from the vocabulary side — 'ED' in, 'it' out, both asserted in one test).
3. NEW unit pin on the anchor band: the fu1 mention's anchor set under the margin clause excludes the sub-band pbi_reports (counts asserted at the measured values' SHAPE, not their decimals).
4. test_overmarked_reference_never_vetoes_the_search must pass UNCHANGED — the standing guard that slice 2 never re-grows the veto.
