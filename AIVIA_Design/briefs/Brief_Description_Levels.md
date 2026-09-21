# Brief_Description_Levels — each level answers one question; drill-down replaces repetition

**Status: APPROVED** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED)
**ALL SEVEN ambiguities RULED at Sunny's "agree with all seven
recommendations" (2026-09-20) — each recommendation below IS the
ruling. Per Q7 the build queues AFTER slice C (ruling (7)'s
brief 2): the levels display already-repaired join/condition
text, and Q4's re-voicing rides slice C's single regen + load +
his AISQL_RECORD run.**

Born 2026-09-20 at Sunny's end-user read of the dryrun_sepsis
output (sepsis_descriptions.txt), USP_ED_SEPSIS the ruled focus
proc ("please use USP_ED_SEPSIS only going forward"). His ask:
"read the sql proc description, and tell me if the technical
description is what we expected to show an end user. if not,
what should we design … i want to see descriptions at the
scope, statement and proc level." The assessment's verdict: the
proc-level technical definition shown to an end user is the
full catch-all (~6,500 words for USP_ED_SEPSIS — headline +
pipeline + the appendix restating every scope's filters and
joins); the statement level is too thin ("Builds the allmeds
selection." carries no meaning); the scope level is close to
right. His direction ruling: **"i agree with the level design,
draft the brief. make sure we record it in the design doc"**
(2026-09-20, quoted; recorded in Grammar_Floor.md THE
DRILL-PATH DIRECTION, same breath).

## THE LEVEL DESIGN (the agreed direction)

Each level answers ONE question; drill-down replaces repetition:

| level | the one question it answers | target shape |
|---|---|---|
| file (proc) | "what does this give me?" | purpose sentence · grain + date window (the delivery scope's R14 headline — already exists) · what it reports, grouped by theme · the main source tables, one line. NOT the per-scope filters/joins dump. |
| statement | "what does this step contribute?" | "Builds the \<x\> selection: \<what belongs in it\>" — the clause borrowed from the scope's own R14 sentence (extends the ruled R11 render-join) |
| scope | "exactly what is in this selection?" | the R14 Business Term sentence, with the compression bar amended (Q4) |
| condition / join rows | "every literal value" | already the law — full lists stay on the rows (ruling (3)) |

NOT claimed here (already OPEN rows, slice C's — Brief_Pilot_
Findings_R1 ruling (7) brief 2): FL9 (correlated equality voices
as a tautology — "the encounter id is the encounter id") and
FL12 (joins fall back to raw ON text, embedded whitespace
included). This brief cites them; their fixes land in slice C.

| field | content |
|---|---|
| class | **update** — changes things DECIDED: Grammar_Floor §R13 v2 (the three levels' surface split), §R11 render-join rider (the borrow widens), §R14 ruling-(3) compression clause (the bar moves) |
| claims | Grammar_Floor §R13 v2 rider · §R11 THE RENDER-JOIN (Q5, ruled 2026-09-20) · §R14 ruling (3) compression · Contract_Logic_Layer dc.file.technical_definition row · FINDINGS FL25–FL29 (born in this act) · cites Brief_Pilot_Build_3, Brief_Pilot_Findings_R1 rulings (3)/(7), Brief_Dryrun_Order (the render-only precedent) |
| impacts (computed, step-2 query) | **writers**: dc.file.technical_definition ← file layer R13 (UNTOUCHED under Q1 rec (b)); statement display ← produce.statement_display (render-time — Q3); scope sentence ← R14 composer (Q4 only); dry_run printer ← fabric_run (the file-level block). **consumers**: sc.fabric_export/Collibra (TD field — untouched under (b)); dry_run (Brief_Dryrun_Order's order pins re-base); M7 report cherry-pick (Presents stays its source — untouched under (b)); ask index (scope speech changes ONLY under Q4 → RecordingGaps → Sunny's AISQL_RECORD run; merged with slice C's load under Q7 rec). **tests**: test_fabric_run (dry_run pins) · test_statement_render/_layer (display pins) · test_scope_sentence (compression pins, RED first) · test_file_render (ONLY if Q1 rules (a)/(c)) · test_sepsis_shakedown · speech parity. **served data**: NONE under the recommendations ((b) + render-time + Q4 rides slice C's regen); else ONE load with slice C. **registries**: Grammar_Floor → 2.15.0 at build; no metamodel change expected. **wheel**: the next cut carries. |
| ambiguities | Q1–Q7 below — ALL RULED (Sunny "agree with all seven recommendations", 2026-09-20): Q1 (b) the stored TD stands, end-user surfaces render short · Q2 (a) the Scribe description grows, approved-only · Q3 (b) the scope sentence minus the payload tail, render-time · Q4 (a) noted-label lists compress past 3, bare keep 6 · Q5 (b) the ruled completeness stands · Q6 (b) the finding class queues as its own feature · Q7 (a) builds after slice C, one load |
| debt declared | ONE row (Q6 ruled (b)): the contradiction-detector ("a stored description contradicts its output's name" as a counted finding class) is DEFERRED — recorded reason: no engine defect exists, it is a distinct product feature with its own design questions; landing step: its own queued brief (Echo Law first-occurrence deferral; a second source-defect catch across customers echoes it into a mandatory build) |
| retirement (pivots only) | nothing retires (Q1 ruled (b): the stored TD stands byte-identical; the end-user short block is a render-time projection beside it, never a replacement) |
| does this promote? (the Promotion Gate) | asked at close per the gate |
| Sunny's approval | direction: "i agree with the level design, draft the brief. make sure we record it in the design doc" (2026-09-20). Build approval: **"agree with all seven recommendations"** (2026-09-20, same day). |
| closing check | (filled at CLOSED) |

## The ambiguities — Sunny rules each

**Q1 — the fate of the stored technical_definition.** R13 ruled
the TD "the Collibra-named governance field for serious users
who want accurate filters … complete by construction". The
level design says the END USER should not meet the appendix
first. Options:
- (a) the stored TD re-shapes to the short block; the appendix
  RETIRES from the field (governance users lose the in-field
  filter dump — they would drill the graph instead).
- **(b) RECOMMENDED: two audiences, two projections, one stored
  home.** The stored TD stands byte-identical (R13's ruled
  consumer keeps the complete catch-all in Collibra); the
  END-USER SURFACES (dry_run today; the console later) render
  the short block at display time — headline · window · main
  sources — a derivable projection, never stored twice. The
  Brief_Dryrun_Order precedent exactly: identical bytes, new
  surface shape, no load.
- (c) the TD re-shapes AND a render-on-demand walk serves the
  full detail to governance users.

**Q2 — the purpose sentence and the themed output groups.**
Themes ("scores and timings · cultures · transfers …") are not
stored anywhere and cannot be spoken deterministically. Options:
- **(a) RECOMMENDED: the existing dc.file.description field is
  the home** — the Scribe summary (LLM cage, approved-only,
  receive_descriptions the one writer) grows from one line to
  purpose + themed outputs; Sunny re-approves the new text per
  the standing empty-until-approved law. The deterministic
  surfaces carry NO themes.
- (b) no themes anywhere — the file block is headline + window
  + sources only, purely deterministic.
- (c) themes deferred to M8 governance vocabulary.

**Q3 — how much of the scope's sentence rides the statement
line?** Today (ruled Q5): "Builds the base poptemp selection
(the main adm details selection)" — the head clause only.
Options:
- (a) the full R14 sentence rides (long ones ride whole).
- **(b) RECOMMENDED: the sentence minus the payload tail** —
  grain-or-base + membership + population, stopping before
  "carrying …" (what belongs, without the column inventory).
- (c) stands as is.
Either way RENDER-TIME (produce.statement_display — the ruled
render-join precedent): derivable is never stored; the stored
R11 text is untouched; the clause lives once, on the scope.

**Q4 — the compression bar.** Ruling (3): IN-lists longer than
6 compress to "one of N values". Measured harm: #BasePopBolus's
6-member medication list WITH noted labels prints ~450
characters inside one sentence, while #ADT's 17 units rightly
compress. The harm is rendered length, not member count.
Options:
- **(a) RECOMMENDED: noted-label lists compress past 3 members;
  bare lists keep the ruled 6.** Countable, no character magic;
  full lists stay on the condition rows (unchanged law).
- (b) a rendered-length bar (compress past ~160 chars).
- (c) the bar stands at 6 for all.
This amends ruled R14 text → scope sentences re-voice → speech
re-record + load (rides slice C's under Q7).

**Q5 — the appendix's uncounted repeats** (only live if Q1
rules the appendix survives anywhere). The final selection's
correlated pair prints FOUR times, once per correlated
subquery. R13 ruled "completeness beats tidiness at catch-all
grain" — any dedup is an amendment. Options:
- (a) counted dedup: the group speaks once + "(applies in 4
  places)".
- **(b) RECOMMENDED: the ruled completeness stands** — under Q1
  (b) the end user never meets the appendix, and the governance
  reader gets the ruled completeness.

**Q6 — the finding class born from the source-defect catch.**
The TD faithfully voiced a real defect in the customer's SQL
(FL29: the two "negative" columns computed from the POSITIVE
score time — USP_ED_SEPSIS.sql:3179/3187). Question: does "a
stored description contradicts its output's name" become a
COUNTED finding class (the error-contract philosophy: repeats
across customers = product signal)? Options:
- (a) build the counted class in this brief.
- **(b) RECOMMENDED: queue it as its own feature row** —
  recorded reason: no engine defect exists; a
  contradiction-detector is a distinct product feature with its
  own design questions (what counts as contradiction?); landing
  step: its own brief, queued.

**Q7 — sequencing against slice C** (brief 2 of ruling (7):
FL9/FL12/FL16/FL18/FL19 voicing repairs — stored text changes,
one regen, ONE load). Options:
- **(a) RECOMMENDED: this brief builds AFTER slice C** — the
  levels then display already-repaired join/condition text, and
  Q4's re-voicing rides slice C's single regen + load + his
  AISQL_RECORD run (the one-load economy of ruling (7)).
- (b) before slice C (render-side lands sooner; Q4 defers).
- (c) merge into slice C as a rider.

## FINDINGS born in this act (rows FL25–FL29, Contract_Logic_Layer)

FL25 the altitude finding · FL26 the thin statement line ·
FL27 the compression bar's noted-label gap · FL28 the appendix's
uncounted repeats · FL29 the source-defect catch. FL9/FL12
cited, not re-claimed.

## Files declared

    aisql/fabric_run.py
    aisql/flows/produce.py
    aisql/flows/describe.py
    AIVIA_Design/Grammar_Floor.md
    AIVIA_Design/Contract_Logic_Layer.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Manifest_Build.md
    AIVIA_Design/briefs/Brief_Description_Levels.md
    tests/aisql/test_fabric_run.py
    tests/aisql/test_statement_render.py
    tests/aisql/test_scope_sentence.py
    tests/aisql/test_sepsis_shakedown.py
    docs/architecture/TEST_MAP.md

    AIVIA_Design/registries/convert_from_xlsx.py
    AIVIA_Design/registries/flows.json
    AIVIA_Design/registries/kg1_technical.json
    AIVIA_Design/registries/kg2_kind_library.json
    AIVIA_Design/registries/kg2_logic.json
    AIVIA_Design/registries/kg3_artifacts.json
    AIVIA_Design/registries/kg4_concepts.json
    AIVIA_Design/registries/lenses.json
    AIVIA_Design/Design_Graph_Engine.md
    AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json
    tests/aisql/test_metamodel.py

    (narrowed AT the rulings, per this section's own drafted
    clause: test_file_render.py dropped — Q1 ruled (b), the
    stored TD is untouched and its hash pin PROVED unmoved at
    build; convert_from_xlsx.py RETURNED at Sunny's "Amend
    (Recommended)": the Scribe prompt is a lenses Seat_Prompts
    registry row — the edit is a versioned regeneration, one
    stamp 1.52.0 across the seven JSONs + the Design_Graph_Engine
    stamp block same breath; describe.py stays declared and
    closes NO-OP, reasoned — it reads the prompt FROM the
    registry. The two stamp-consumer pins amended at his "agree,
    amend the version pins": expected_m_gates.json's twin-key
    basis + test_metamodel.py's version pin, both 1.52.0.)
