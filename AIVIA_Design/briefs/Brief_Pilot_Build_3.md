# Brief_Pilot_Build_3 — the three description levels get GOALS: scope = the Business Term sentence · statement = the workflow step wearing its scope's head · file = headline, pipeline, appendix (slices D+E)

**Status: BUILT** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED; PRESENTED 2026-09-20 with the prototype's real output as the worked-examples table; APPROVED 2026-09-20 at Sunny's word: "approved, build brief 3"; BUILT same day — grammar 2.14.0 / metamodel+registries 1.50.0 / wheel 2.4.0, suite 758 green with the one RecordingGap class open on his `AISQL_RECORD=1` run; CLOSED rides his eye on the re-voiced corpus + that run + his Fabric load of the regenerated exports) —
ship-unit 3 of Brief_Pilot_Findings_R1 ruling (7) ("i agree, three
briefs": brief 3 = D+E, its own ratification and load). Opened at
Sunny's goals directive (2026-09-20, from the work pilot: "can you
set goals: what SHOULD the descriptions at each of these 3 levels
look like? use a local example, one of our ED sepsis sql file to
test. until it's proven to be good descriptions."). The worked
examples below compose the goal text BY HAND from stored graph
facts of reporting/USP_IP_SepsisShiftCompliance.sql — the proof
loop runs until his eye says good; then this brief PRESENTS.
Q1–Q5 RULED 2026-09-20 ("agree with all five") — the proof loop's
prototype composer now runs over the sepsis corpus under those
five rulings; APPROVED lands at his eye on its output.

## THE GOALS (each slot filled ONLY from ruled stored sources)

| level | the goal sentence | slot sources |
|---|---|---|
| scope (the Business Term — rulings (1)–(3) already fix the shape) | "One record per <grain>: <population>, carrying <payload>." · grain absent → "<Base source> records: <population>, carrying <payload>." · population empty → the clause drops | grain: GROUP BY / DISTINCT words; the rank-filter partition AFTER slice E (FL17) — until E, grain stays SILENT, never invented (ruling (1)). population: membership first ("matched in X and in Y"), then value restrictions from inner-join ONs + every WHERE (ruling (2)); long value lists compress to counts (ruling (3)). payload: ruling (10)'s ladder — dcol phrases · author alias words · spoken column names |
| statement | the workflow connective KEEPS its R11 form; at RENDER it borrows the built scope's grain-or-base clause — "Builds the base pop selection — one record per <grain> — preparing the datecte selection first." NOTHING new stored (derivable-never-stored: the clause lives once, on the scope; the renderer joins at read). Guard idioms speak as idioms: the OBJECT_ID/DROP dance says "A cleanup step: removes the previous #x when it already exists", never object_id(n'tempdb..#x') raw | the scope's stored sentence head · a new grammar row for the temp-table-existence guard (FL10 family) |
| file (technical definition) | three layers, all derivable: (1) HEADLINE = the delivery scope's sentence wearing "Delivers" — the Business Term of the whole file; (2) THE PIPELINE — the statement chain in build order, one line per step, each wearing its scope's head clause; (3) THE APPENDIX — today's per-selection filters and joins, joins grouped per selection (FL20), value lists compressed (ruling (3)) | the delivery scope's sentence · the R11 statements · the condition/join rows |

## Worked examples — PROVEN BY THE PROTOTYPE (v3, 2026-09-20): every sentence below is the scratchpad composer's ACTUAL OUTPUT over the stored sepsis graph, zero hand-editing

| grain | before (stored today) | after (the composer's real output) |
|---|---|---|
| scope #ODScores | "Drawn from grouper compiled list records." | "Grouper compiled list records: The context (master file) for the records included in the compiled grouper is 'FLO'; The unique identifier (vcg-.1) for the base record associated with the compiled record is one of the values '800006'; carrying the flo id." |
| scope #Base_PopTemp | "Drawn from the mainadmdetails selection defined earlier in this procedure, restricted to records also present in the vaplh selection defined earlier in this procedure, restricted to records also present in config value set records." | "The main adm details selection, matched in the vaplh selection and in config value set records (the value set id is 3031), carrying the in dept date, the out dept date, the in shift date, the in shift, the out shift date, the out shift, the in dept rn, the enc id order, and 14 carried-through columns." — THE PROOF LOOP'S OWN CATCH: the first hand-composed draft put the shift-window betweens in the population; the tree walk showed they are CASE-derivation internals of the computed columns, NOT filters — the mechanical composer is more truthful than the hand |
| scope dateCTE (union, Q2) | "Drawn from the base poptemp selection … the combination of 2 alternative selections (duplicates kept)." | "The base pop temp selection: in 2 alternatives: (1) The department rollup is none of the values 'ER', 'P-ER'; The indeptrn is 1; (2) The 1 day after the expansion date is on or before the expansion end date; carrying the shifts per day, the am denom, the pm denom, the in record, the out record, the expansion date, and 15 carried-through columns." |
| scope #FlwshtLstHuddleODScore | "Drawn from the base pop selection …, restricted to records also present in flowsheet records records, restricted to …" | "The base pop selection, matched in flowsheet records and in flowsheet measurements records: The exact moment when the reading was recorded is between the shift start and the shift end (inclusive); carrying the encounter id, the fsd id, the flo meas id, the recorded time, the meas value, the enc id overall order." |
| scope #FlwshtAlert (pre-E, Q4) | "Drawn from an inline selection." | "An inline selection, matched in clinical alerts records (the bpa locator id is 900400001) and in the base pop selection and in alert history records and in ref alert override reasons records; the first record in its ordered sequence kept; carrying the clinical alerts activated comment, the row num, and 3 carried-through columns." — AFTER slice E the head becomes "One record per <partition>: …" |
| statement (Q5) | "Builds the base poptemp selection, preparing the vaplh selection first." | "Builds the base poptemp selection (the main adm details selection), preparing the vaplh selection first." — the parenthetical is the scope's head clause, joined at render, stored once |
| statement (guard) | "A decision step, taken when the object_id(n'tempdb..#base_poptemp') is recorded." | "A cleanup step: removes the previous #base_poptemp when it already exists." |

Prototype: scratchpad goal_composer.py (session scratchpad; the
real build re-implements inside the renderers under tests). KNOWN
PROTOTYPE LIMITS, all closing in the real build: inline-selection
bases say "An inline selection" (the build resolves through the
derived scope per ruling (10)); ON-clause value conditions are
regex-lifted from the join fragment (the build reads the condition
tree); grain never speaks yet — FL21.

## Open questions — ALL FIVE RULED (Sunny "agree with all five", 2026-09-20); each recommendation below is now the ruled answer

| # | question | recommendation → RULED |
|---|---|---|
| Q1 | payload compression: a 22-member payload cannot all speak — what does? | named business outputs first (the dcols, by name), then "and N carried-through columns"; the full list stays on the nodes (derivable) |
| Q2 | union scopes (combination arms): does the sentence speak per arm or once with the alternatives named? | once, with the shared shape spoken and the arms as alternatives ("in two alternatives: AM …, PM …") — per-arm repeats everything twice |
| Q3 | repeated near-identical conditions (the 8 shift-window betweens): compress mechanically? | join identical subjects' betweens with "or between … and …" (pure structure, no invention); anything smarter waits for evidence |
| Q4 | pre-E interim for rank-filtered scopes: grain silent, or the honest structural clause ("the first record in its ordered sequence kept")? | the structural clause — it is stored fact (the rank condition + the dcol phrase), not invention |
| Q5 | the statement render-join (borrowing the scope's head at read) — approve the derivable display join? | yes — stores nothing twice, and dry_run's statement lines finally say what got built |
| FIND | a file with NO delivery statement stores NO technical_definition at all — silently (USP_IP_SepsisShiftCompliance.sql proves it; the operator's file spoke only because it HAS a delivery) | the headline falls back to the LAST built scope's sentence + "builds N working selections; delivers nothing" — counted, never empty-silent; lands as a row in Contract_Logic_Layer at PRESENTED |
| FIND-2 (FL21) | ALL THREE grain sources are un-captured: GROUP BY lands only as the string "GROUP BY" in scope.structures (columns never kept), DISTINCT is not captured at all, and the window OVER is a flag (FL17) — the proof-loop composer could find no grain to speak anywhere in the corpus | slice E widens from the window capture to the whole grain-source family: GROUP BY column refs + DISTINCT flag + PARTITION BY/ORDER BY contents, ONE capture act; FL21 landed in Contract_Logic_Layer 2026-09-20 |

## Build decisions for Sunny's eye (mechanical calls inside the ruled shapes, declared not silent)

| # | decision | why |
|---|---|---|
| B1 | Presents STAYS in the file definition (inside the appendix, after Pipeline) | the M7 report cherry-pick (RATIFIED, v2.13.0) reads the "Presents: " section to derive report definitions — dropping it would break a ratified consumer; the three ruled levels stand around it (headline · pipeline · appendix = Presents + per-selection filters + per-selection joins) |
| B2 | list-compression threshold = more than 6 members | ruling (3) said "long"; 6 keeps every worked example verbatim and compresses the work pilot's plan-code class; pinned in test_scope_sentence |
| B3 | R14 selection names use the READABLE fold (camel split: "the main adm details selection") | matches the approved worked examples; R11's ratified spoken fold ("basepoptemp") is untouched — the render-join matches the two registers through a separator-blind squash |
| B4 | a no-source scope leads "Derived values (no source records are read)" | the ruled 2.4.0 restoration words wearing the sentence's lead slot; nothing invented |
| B5 | order-only windows (no PARTITION BY) speak "the record's position, ordered by <order>" | the slotted phrase's mechanical reduction; flag-only `over` keeps the slotless phrase |
| B6 | the committed sepsis graph_export predated wheel 2.3.0's resolver fix — this regen carries Brief_Pilot_Build_1's elided-schema recovery too (USP_RPTS_IP_SEPSIS #Base_Pop: 7 join sides + 19 condition resolves appear, "bed id"→"bed record") | verified ref-by-ref against the parquet diff; every other statement-text delta (212) is the guard idiom exactly |

## Closing check (BUILT, 2026-09-20)

Files changed == files declared: BALANCED. Declared-but-untouched,
each reasoned: test_statement_render.py (stored R11 pins unchanged;
the guard idiom pinned in test_scope_sentence.py) ·
test_statement_layer.py (counts unchanged) · test_meaning_smells.py
(its "Drawn from" string is a smells-detector fixture, not a stored
text) · test_registry_mirrors.py (the mirror pin lives in
test_derived_render.py) · AIVIA_Test/test_ed_sepsis_dev_estate.py
(the answer KEY updated instead; every recompute test green) ·
docs SPEC/AXIOM_CROSSWALK/DECISION_LANDING_MATRIX (regen ran,
byte-identical). Suite 758/0 non-RecordingGap · ruff zero new ·
the one OPEN lane is HIS: `AISQL_RECORD=1 python3.11 -m pytest
tests AIVIA_Test -q` records the 450 new spoken sentences (62
tests gap until then), then his Fabric load of the regenerated
graph_export parquet.

## Files declared

(filled at APPROVED per the template law — the build touches the
scope/statement/file renderers, Grammar_Floor R14 + the R11/R12/R13
amendments, slice E's grain-source capture (metamodel 1.50.0), the
sepsis + ed_sepsis_dev re-voice with pins re-based by measurement,
the wheel, and HIS LOAD for the served texts)

    AIVIA_Design/briefs/Brief_Pilot_Build_3.md
    AIVIA_Design/Grammar_Floor.md
    AIVIA_Design/Contract_Logic_Layer.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Manifest_Build.md
    AIVIA_Design/registries/convert_from_xlsx.py
    AIVIA_Design/registries/flows.json
    AIVIA_Design/registries/kg1_technical.json
    AIVIA_Design/registries/kg2_kind_library.json
    AIVIA_Design/registries/kg2_logic.json
    AIVIA_Design/registries/kg3_artifacts.json
    AIVIA_Design/registries/kg4_concepts.json
    AIVIA_Design/registries/lenses.json
    aisql/graph/kg2_mapper/__init__.py
    aisql/flows/produce.py
    aisql/flows/inbound.py
    aisql/fabric_run.py
    pyproject.toml
    CHANGELOG.md
    pilots/work_dryrun/README_Runbook.md
    docs/architecture/SPEC.md (generate_docs regen rider)
    docs/architecture/AXIOM_CROSSWALK.md (regen rider)
    docs/architecture/DECISION_LANDING_MATRIX.md (regen rider)
    docs/architecture/TEST_MAP.md
    tests/aisql/test_grain_capture.py
    tests/aisql/test_scope_sentence.py
    tests/aisql/test_scope_layer.py
    tests/aisql/test_derived_render.py
    tests/aisql/test_file_render.py
    tests/aisql/test_statement_render.py
    tests/aisql/test_statement_layer.py
    tests/aisql/test_fabric_run.py
    tests/aisql/test_sepsis_shakedown.py
    tests/aisql/test_meaning_smells.py
    tests/aisql/test_phase_a_projection.py
    tests/aisql/test_registry_mirrors.py
    tests/aisql/test_metamodel.py
    tests/aisql/test_produce.py
    AIVIA_Design/Design_Graph_Engine.md (registry stamp block, same breath)
    tests/aisql/test_wheel_boot.py
    AIVIA_Test/test_meaning_console.py
    AIVIA_Test/test_ed_sepsis_dev_estate.py
    AIVIA_Product/estates/sepsis/expected_shakedown.json
    AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json
    AIVIA_Product/estates/sepsis/graph_export/ (regen, store texts changed)
    AIVIA_Product/estates/ed_sepsis_dev/graph_export/ (regen, store texts changed)
    dist/ (wheel 2.4.0; 2.3.1 retired per the one-current-wheel law)
