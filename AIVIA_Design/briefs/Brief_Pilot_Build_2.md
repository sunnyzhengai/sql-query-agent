# Brief_Pilot_Build_2 — slice C, the voicing repairs (ship-unit 2 of Brief_Pilot_Findings_R1 ruling (7))

**Status: BUILT** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED)
**BUILT 2026-09-20, same day as its draft and rulings. FULL SUITE
793 passed / 0 non-gap failures; the ONE remaining red class is
64 tests blocked on 174 unrecorded embedding sentences (the
re-voiced speech cards) — Sunny's AISQL_RECORD run at the shared
closing run retires them (the Build_3 pattern). Ruff --no-cache
zero new (the two convert_from_xlsx E501s pre-exist). CLOSED
rides the shared closing run: Brief_Description_Levels' build →
one export regen (LOCAL regen already done for the suite gates;
re-run after Q4's compression) → one wheel cut → his
AISQL_RECORD run → his ONE Fabric load → his gap-check eye on
the re-voiced corpus.**
**ALL SEVEN ambiguities RULED at Sunny's "agree with all seven
recommendations, build it" (2026-09-20) — each recommendation
below IS the ruling: C1 FL19 joins · C2 (a) both owners always ·
C3 all five ratified · C4 as refined, measured post-F9 · C5 (a)
the R12 slot form · C6 the investigation runs inside · C7 both
pair words.**

The middle ship-unit of ruling (7) ("i agree, three briefs",
2026-09-19): "brief 2: C (voicing — stored descriptions change,
one Grammar_Floor bump, one regen, ONE load)". Drafted
2026-09-20 at Sunny's "draft the slice C brief". Carries the
slice-C findings born in the two work dry runs (2026-09-19) and
the third (his hand, 2026-09-20): FL9 · FL10 · FL11 · FL12 ·
FL13 · FL14 · FL16 · FL18, plus FL19 pending C1. Two of its
questions are ALREADY RULED in the parent brief — ruling (9)
the NOT fold and ruling (6) the pack naming home — and build
here unchanged.

**THE SEQUENCING LAW OF THIS BRIEF** (Brief_Description_Levels
Q7, ruled "agree with all seven recommendations" 2026-09-20):
slice C's code builds FIRST, Brief_Description_Levels' code
builds immediately after, and then ONE shared closing run: one
export regen · one wheel cut · Sunny's ONE AISQL_RECORD run ·
Sunny's ONE Fabric load. This brief's re-voicing and that
brief's Q4 compression land in the SAME regenerated store — the
one-load economy ruling (7) named.

| field | content |
|---|---|
| class | **planned addition** (fills ruling (7)'s declared slice-C slot) carrying **grammar amendments** (the phrase texts C2–C7 need ratification — R-numbered into Grammar_Floor at build, the ruling-(3) precedent) + **two already-ruled builds** (ruling (9) the NOT fold · ruling (6) the pack naming ladder) + **one fix-after-investigation** (FL13, generator clause) |
| claims | Brief_Pilot_Findings_R1 rulings (6) · (7) · (9); FINDINGS FL9 FL10 FL11 FL12 FL13 FL14 FL16 FL18 (+ FL19 per C1); Grammar_Floor → 2.15.0 at build; clarity pack → clarity-pack-1.2; Contract_Source_Packs (the naming-conventions rows); cites Brief_Description_Levels Q7 (the shared load) and Q4 (rides this regen) |
| impacts (computed, step-2 query) | **writers**: dc.condition.description ← the condition renderer, R1–R7 + overlays (produce.py; FL9 owners · FL10 phrases · FL18 pair words); dc.join.description ← the join renderer (inbound.py; FL12); dc.derived_column.description ← R12 renderer (produce.py; FL14); the condition walker ← inbound.py (FL16 fold: the child row never minted, the folded row absorbs the child's column-resolution links; FL13 after investigation); the voicing ladder ← blessed name → pack convention → readable identifier (ruling (6); pack.json 1.2 the vendor-facts home); scope sentences + file TDs recompute (they cite the condition/join renders — one home, the walk re-renders). **consumers**: ask index speech (condition · scope · derived_column · file description cards re-voice → RecordingGaps → his ONE AISQL_RECORD run, shared); sc.fabric_export → his ONE load (shared); Collibra TD; dry_run; M7 report cherry-pick (re-derives from the TD). **census**: condition rows DROP (FL16 children unminted · FL13 dupes dead) → re-base BY MEASUREMENT reaching EVERY coverage string (the FL7 lesson): expected_shakedown.json · expected_m_gates.json · GQL_Gates.md. **registries**: kg2 function library rows (CONVERT · GETDATE · the WHERE-path skeleton fills) via convert_from_xlsx.py, registries → 1.51.0; Grammar_Floor 2.15.0. **tests**: verbatim suites (test_verbatim_census · condition render pins) · test_scope_sentence · test_file_render (hash re-base) · test_sepsis_shakedown + test_shapes_shakedown (census re-base) · test_kg2_mapper (the fold's walker) · test_clarity_source_pack (pack 1.2) · test_derived_render (FL14) · speech parity · estate batteries; new pins RED-first per finding. **wheel**: ONE cut after BOTH briefs (the one-current-wheel law). |
| ambiguities | C1–C7 ALL RULED (Sunny "agree with all seven recommendations, build it", 2026-09-20): C1 FL19 joins the brief · C2 (a) every column-to-column predicate names both owners · C3 all five ratified (the two phrases, the two skeleton rows, the WHERE-path fill, the unary-minus guard) · C4 the fallback names both sides + whitespace normalized + comments "(noted …)", measured post-F9 · C5 (a) the R12 slot form for LAG/LEAD · C6 the FL13 investigation runs inside this brief · C7 "Both of its parts hold." / "Either of its parts holds."; rulings (6) and (9) QUOTED law |
| debt declared | FL13 is INVESTIGATION-FIRST (the generator clause, ruled 08-29): if the double-walk's true home exceeds this brief's declared files, the investigation's finding lands as a NEW FL row and the fix returns via its own brief — the deferral's recorded reason would be "the generator lives outside the slice", landing step named in that row. No other debt. |
| retirement (pivots only) | the NOT child rows RETIRE from the store (ruling (9): never minted again; existing stores re-derive at regen — nothing hand-deleted); no code direction retires |
| does this promote? (the Promotion Gate) | asked at close, AFTER the shared closing run with Brief_Description_Levels |
| Sunny's approval | **"agree with all seven recommendations, build it"** (2026-09-20) |
| closing check | AT BUILT (2026-09-20): 40 declared paths (after the two ruled amendments — "Amend the list" · "Amend all seven"). CHANGED-AND-DECLARED: 35 (code 3 · registries 8 · pack 8 · design docs 6 incl. Design_Graph_Engine's stamp block · tests 10 incl. AIVIA_Test · expected files 3 · both graph_export dirs · TEST_MAP). DECLARED NO-OP, reasoned: aisql/flows/speech.py (speech cards read stored descriptions — nothing to change) · AIVIA_Product/estates/sepsis/expected_shakedown.json (it pins resolution, not condition counts) · tests/aisql/test_shapes_shakedown.py + tests/aisql/test_verbatim_census.py (their pins never moved; ran green). CHANGED BEYOND DECLARATION, flagged for Sunny's word: tests/test_ci_lint_paths.py (ONE docstring line — the missing "Proves:" claim, Brief_CI_Lint's close miss, red on the suite-map gate since its birth; marked in the file). NOT THIS BRIEF'S: Brief_Description_Levels.md + its rows (its own brief) · USP_ED_SEPSIS_descriptions.txt (the untracked loop file, declared in zones) · ci.yml/CHANGELOG/CLAUDE.md/devtools deletions/Brief_CI_Lint.md/sepsis_descriptions.txt/Contract_Technical_Layer.md (pre-existing uncommitted work of prior briefs). BALANCED subject to the one flagged line. |

## The already-ruled builds (no questions — his words quoted)

**The NOT fold — ruling (9)** ("i agree, fold entirely",
2026-09-19): one NOT predicate, ONE condition row, the folded
voice ("The x is none of the values …"); the child row is never
minted; the folded row ABSORBS the child's column-resolution
links (verified: today the child carries them — _condition_refs
stops at child predicates); the tree shape survives in the
parse record; a future ask for the un-negated form DERIVES it
at ask time, never stores it; the condition census re-bases and
the re-base must reach EVERY coverage string (the FL7 lesson).
Closes FL16.

**The pack naming ladder — ruling (6)** ("i agree with option
a", 2026-09-19): per-vendor naming knowledge lives IN THE
SOURCE PACK — the clarity pack gains a naming-conventions table
(suffix → voicing rule: _C drops the suffix and expects a
category values map; _YN speaks as a yes/no flag; the exact
list authored AT BUILD from Epic's documented conventions,
presented at his gap-check); pack version → clarity-pack-1.2;
the voicing ladder: blessed name → pack convention →
readable-identifier fallback; the grammar floor stays
vendor-free; estates with no pack untouched; FL11's values-map
half rides under the ruled R8 precedence. Closes FL11.

## The ambiguities — Sunny rules each

**C1 — does FL19 join this brief?** The noun-phrase gate: Epic
dictionary descriptions that are verb-led ("Stores the unique
category identifier …" → "the stores the … is 0"),
second-person ("You have the ability …"), or comma-truncated
inside a parenthetical, pass through as broken subjects — the
F12 generator class in the grammar domain. Its row says
"Sunny's word adds it to that brief's scope."
- **RECOMMENDED: yes, it joins** — same class (voicing repair),
  same re-voicing, same load; leaving it out means these broken
  subjects ride the regenerated store until a fourth brief. The
  remedy as the row proposes: a noun-phrase gate on the
  dictionary-phrase tier — a description failing it FALLS to
  the readable-identifier tier (never a broken pass-through),
  and truncation respects parenthesis balance.

**C2 — FL9, the two-sided phrase.** `T1.X = T2.X` voices "The x
is the x". Options:
- **(a) RECOMMENDED: every column-to-column predicate names
  BOTH owners** — "the abx selection's encounter id is the base
  pop selection's encounter id" — one enumerable rule, no
  tautology can survive it, and near-identical names (`T1.X =
  T2.Y`) separate too (the enumerate-all-cases law: fix the
  class, not the instance).
- (b) owners speak only when the bare render would repeat the
  same words (the minimal patch — near-identical names stay
  confusable).
- (c) only the right side names its owner.
The owner words ride the same readable-name fold the rest of
the grammar uses; where a side is a scope, "the \<scope words\>
selection's"; where a table, the blessed/readable table words.

**C3 — FL10, the function phrases + the two mechanism fixes.**
Ratify the phrases proposed in the row, and close the two
verified entry-point gaps:
- DATEADD relative to GETDATE → **"within the last N \<units\>"**
  (and the future-facing twin "within the next N \<units\>").
- ISNULL(\<date\>, far-future sentinel) → **"treating a missing
  \<date words\> as open-ended"**.
- CONVERT and GETDATE get their FN_SKELETONS rows (the R12
  remainder — registries 1.51.0 via the converter).
- MECHANISM 1: the WHERE path gains the library fill —
  condition subjects today reach only the four absorbed
  overlays; the skeleton rows must fill on BOTH paths (one
  library, two readers).
- MECHANISM 2: the DATEADD overlay's negative-offset guard
  reads args[1].value and a unary minus parses to None — the
  guard reads through the unary wrapper (a fix; the raw
  fragment can never print for a negative offset again).
- **RECOMMENDED: ratify all five as written.**

**C4 — FL12, the join fallback's voice.** The refined row: the
real trigger was UNRESOLVED SIDES (F9's class, since fixed in
Brief_Pilot_Build_1) — so first MEASURE the residual raw-
fallback class on the re-based sepsis store, then the voice:
the fallback names both sides always, whitespace normalizes
(the TD's embedded newlines/tabs die), inline comments surface
as "(noted …)" as condition prose already does.
- **RECOMMENDED: as the row proposes**, with the measurement
  recorded in this brief at build (the count before and after —
  if the residual class is zero after F9, the fragment voice
  still lands as the honest fallback for foreign estates).
- **MEASURED at build (2026-09-20, both estates, post-F9 +
  R15.d)**: ed_sepsis_dev — 95 joins, 0 no-side fallbacks, 8
  one-sided, 0 embedded newlines/tabs. sepsis (28 files) — 724
  joins, 1 no-side fallback residual, 30 one-sided, 12 join
  descriptions now carry "(noted '…')" from inline comments,
  0 embedded newlines/tabs (the class the TD showed is dead).

**C5 — FL14, the LAG/LEAD phrase — old proposal or the R12 slot
form?** The row (written 2026-09-19) proposed "the previous/next
record's x in its ordered sequence". Slice E has SINCE captured
OVER contents (partition_by/order_by, metamodel 1.50.0), and
R12's slots-close rider speaks them.
- **(a) RECOMMENDED: the R12 slot form** — "the previous
  record's \<x\> within each \<partition\>, ordered by \<order\>"
  (LEAD: "the next record's …"; captured-empty slots fall back
  to the row's slotless phrase — never an empty slot in prose,
  the R12 law).
- (b) the row's original slotless phrase everywhere.

**C6 — FL13, the double-visit CASE — disposition.** The
generator clause commands: locate the double-walk one level up
BEFORE any patch.
- **RECOMMENDED: the investigation runs INSIDE this brief**
  (reproduce with a searched CASE on the sepsis corpus, walk
  the walker); if the true home sits within this brief's
  declared files, the fix lands here with its RED-first pin; if
  it sits outside, the finding row updates with the located
  generator and the fix returns via its own brief (the debt row
  above).

**C7 — FL18, the pair words — and the OR twin.** The row rules
AND's n==2: "Both of its parts hold." The same counting error
lives on the OR side ("Any of its 2 parts holds") — the
enumerate-all-cases law says fix the class:
- **RECOMMENDED: both pair words in one act** — AND n==2 →
  "Both of its parts hold."; OR n==2 → "Either of its parts
  holds."; n≥3 keeps the counted forms.

## Build order (the fixed order, after the rulings)

1. Registry/contract rows via the converter (function library →
   registries 1.51.0; pack.json → clarity-pack-1.2; the
   naming-conventions rows into Contract_Source_Packs).
2. Grammar_Floor 2.15.0 — the ratified phrases R-numbered in.
3. Tests FIRST, RED: one pin per finding (the tautology dies ·
   the within-the-last phrase · the ladder's three rungs · the
   fallback names both sides · the slot form · the fold's
   one-row census · both pair words · the noun-phrase gate if
   C1 rules in).
4. Code: produce.py · inbound.py · speech.py as declared.
5. FL13 investigation (C6's path).
6. Full suite + ruff --no-cache; census re-base BY MEASUREMENT
   into every coverage string.
7. THEN Brief_Description_Levels builds; the shared closing run
   follows (one regen · one wheel · his AISQL_RECORD run · his
   ONE load).

## Files declared

    aisql/flows/produce.py
    aisql/flows/inbound.py
    aisql/flows/speech.py
    AIVIA_Design/registries/convert_from_xlsx.py
    AIVIA_Design/registries/kg2_kind_library.json
    AIVIA_Design/registries/kg2_logic.json
    AIVIA_Design/registries/flows.json
    AIVIA_Design/registries/kg1_technical.json
    AIVIA_Design/registries/kg3_artifacts.json
    AIVIA_Design/registries/kg4_concepts.json
    AIVIA_Design/registries/lenses.json
    AIVIA_Product/source_packs/clarity/01_tables.sql
    AIVIA_Product/source_packs/clarity/02_columns.sql
    AIVIA_Product/source_packs/clarity/03_pk.sql
    AIVIA_Product/source_packs/clarity/04_joins.sql
    AIVIA_Product/source_packs/clarity/05_values.sql
    AIVIA_Product/source_packs/clarity/06_manifest.sql
    AIVIA_Product/source_packs/clarity/README.md
    AIVIA_Design/Grammar_Floor.md
    AIVIA_Design/Contract_Logic_Layer.md
    AIVIA_Design/Contract_Source_Packs.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Manifest_Build.md
    AIVIA_Design/briefs/Brief_Pilot_Build_2.md
    AIVIA_Product/source_packs/clarity/pack.json
    AIVIA_Product/estates/sepsis/expected_shakedown.json
    AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json
    AIVIA_Test/GQL_Gates.md
    tests/aisql/test_scope_sentence.py
    tests/aisql/test_file_render.py
    tests/aisql/test_sepsis_shakedown.py
    tests/aisql/test_shapes_shakedown.py
    tests/aisql/test_verbatim_census.py
    tests/aisql/test_kg2_mapper.py
    tests/aisql/test_derived_render.py
    AIVIA_Test/test_clarity_source_pack.py
    docs/architecture/TEST_MAP.md

    tests/aisql/test_blessings.py
    tests/aisql/test_produce.py
    tests/aisql/test_metamodel.py
    AIVIA_Test/test_meaning_console.py
    src/zones.py
    AIVIA_Design/Design_Graph_Engine.md
    AIVIA_Product/estates/ed_sepsis_dev/graph_export/
    AIVIA_Product/estates/sepsis/graph_export/

    (AMENDED at build with Sunny's word ("Amend the list",
    2026-09-20): +5 registry JSONs — the converter stamps ONE
    version across all seven, a regen restamps them all; +7
    clarity pack files — ruling (6)'s 1.2 bump lives in the six
    script headers and the README, comment lines only, the
    ScriptDom parse pins unaffected.)

    THE SHARED CLOSING RUN's artifacts (declared at execution per
    this list's own note; Sunny's "push and promote" is the act's
    word, 2026-09-20):
    pyproject.toml
    dist/sql_query_agent-2.5.0-py3-none-any.whl
    tests/aisql/test_wheel_boot.py
    pilots/work_dryrun/README_Runbook.md
    CHANGELOG.md
    (2.4.0 retired from dist/ per the one-current-wheel law; the
    runbook's wheel URL + the step-6 "Good" line follow the new
    dry_run shape — the Brief_Dryrun_Order precedent.)

    (AMENDED AGAIN at his "Amend all seven" (2026-09-20): the
    consumer pins the full suite surfaced — test_blessings' three
    relation pins re-base to the R15.a two-owner voice ·
    test_produce's grammar-version pin · test_metamodel's
    registry-version pin · test_meaning_console's condition
    numbering (the NOT fold) · src/zones.py declares the two
    repo-root description .txt files (sepsis_descriptions.txt
    pre-dated this build unclassified) · Design_Graph_Engine's
    registry-stamp block 1.51.0 (the same-breath law, RG-A2
    caught it) · both estates' graph_export parquets — LOCAL
    regen only; Sunny's ONE Fabric load stays at the shared
    closing run.)

    (drafted before the rulings — narrows or grows WITH C1–C7:
    the FL19 gate rides only C1 "yes"; the registry JSONs move
    only via the converter, never by hand; the graph_export
    regen files and the wheel land in the SHARED closing run
    and are declared there when it executes. Amending after
    approval needs Sunny's word.)
