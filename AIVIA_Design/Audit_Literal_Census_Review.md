# The Literal Census Review — the complete offense inventory

*(2026-09-07, read-only review per Sunny's order; method in
Audit_Literal_Law_Plan.md. Scope: aivia/ (163 scanner hits) + hand review
of prose the scanner cannot see. Verdicts: **OFFENSE** (banned
class — must move to registry/graph), **MIRROR** (stays in code,
gains citation + a mirror-check test asserting equality with its
registry sheet), **INNOCENT** (shape/mechanical/frame/grammar —
gains its marker). NOTHING IS FIXED HERE — this is the worklist.)*

---

## ⚠ CRITICAL INCIDENTAL FIND (live bug, shipped 2026-09-07)

`aivia/console.py` records clarify follow-ups as
`append_usage(action="clarify-picked"/"clarify-retyped")` — but
`kg3_artifacts.USAGE_ACTIONS = ("asked","ran","confirmed")` is
validated at write: **RefusalKG3 raises the first time a user types
after a clarify.** No hermetic test exercises clarify→next-round
through the console; the manifest row (#7) claimed BUILT with code
existence as evidence, not a test — the claims-ledger discipline
failed on precisely the untested row. This bug is ALSO the literal
law's best exhibit: a ruled set lived in code, a second writer
extended its usage elsewhere, nothing forced the homes to agree.
FIX (on GO): the ruled action set moves to the registry
(mirror-checked); the new actions join it BY RULING; a hermetic
clarify→next-round test.

---

## OFFENSES (banned classes — must move; the sweep's core)

| where | what | verdict | destination |
|---|---|---|---|
| flows/ask.py L21 `VALID_KINDS` | the kind list as a code tuple; validates the Interpreter's kind-marks | OFFENSE-ruling | dies entirely with shape-only marking (the pending find package); any residual closed-kind need reads the graph's kind nodes |
| console.py `make_interpreter` prompt | kind enumeration WITH synonym hints ("file (reports/procs/queries/views)…") — the dead Kind_Vocabulary resurrected as prose; also names roles/hints vocabulary | OFFENSE-vocabulary | prompt becomes REGISTRY DATA (Seat_Prompts sheet, versioned); rewritten shape-only (no kind targets, no synonym lists) |
| flows/censuses.py L19 `RULED_ISOLATED_KINDS` | nine kinds ruled edge-less, WITH their ruling reasons, in code | OFFENSE-ruling | registry sheet (Censuses gains Ruled_Isolated rows); code mirror-checks |
| flows/speech.py `DRIFT_SENTENCE` | claim words (the drift speech) authored in code | OFFENSE-vocabulary/speech | the sentence text moves into the Speech_Sources drift row; speak() reads it |
| flows/ask.py render_card drift branch | the long drift card sentence ("READER/WRITER DRIFT: …") + "No description is recorded — a counted documentation gap." — claim words in code | OFFENSE-speech | same home: registry speech text (or grammar rule with ID); render reads |
| graph/kg3_artifacts.py L30 `USAGE_ACTIONS` (+ the console's unregistered extensions) | a ruled action set in code, already drifted (the critical find) | OFFENSE-ruling → MIRROR | the set lands in the kg3 registry sheet; code mirror-checks; clarify-picked/retyped join by ruling |

## MIRRORS (ruled/schema sets that stay in code with a citation + equality test)

| where | what | mirror target |
|---|---|---|
| kg3_artifacts L24,25,28,29,31,32 (STATE/EVENT_CLASSES, DESCRIPTION_STATUS, RULINGS, ASKED_OUTCOMES, OBSERVED_OUTCOMES) | ruled kg3 sets | kg3_artifacts registry (rows exist/added) |
| lenses/decisions.py L11 (COMPARE_* kinds), L49 (operand roles) | kind-library sets | kg2_kind_library registry |
| kg2_translator L63 (operand roles), L232 (expression kinds), L476+L491 (statement classes) | kind-library + statement classes | kg2_kind_library / Operational_Statement_Kinds |
| flows/produce.py L243/245 (comparator families), L464 (Union/Except/Intersect) | kind-library sets | kg2_kind_library |
| kg2_mapper L31 (ScriptDom name → kind map) | VALUES are kind-library kinds (keys are external ScriptDom API = mechanical) | kg2_kind_library (values only) |
| flows/ask.py L17 `DISPLAY_MODES` | the ruled STEER view set | new registry rows (Ask_Console/Views) |
| console.py L295 TIERS label map + ask.py outcome tuples (L710/791/805/818) | engine tier + outcome names (ruled in ADR 0079/0080 but declared nowhere) | NEW registry sheet Grounding_Tiers/Outcomes; labels stay frame |
| flows/connect.py L17 edge kinds | edge-kind names | Ranking_Weights sheet (exists) |
| flows/censuses.py L39 store-kind list | store node kinds | metamodel/kg3 registry |
| flows/speech.py L24 `SHEET_KINDS` | entry-kind → Speech_Sources row mapping | Speech_Sources (every value must be a row) |
| graph/metamodel.py L19 (registry manifest), L137 (lens names) | the registries on disk / lenses registry | directory listing / lenses sheet |
| graph/phi_gate.py L30 (phi classes) | ruled contact-shape classes (ADR 0025 posture) | kg3/contract registry rows |
| lenses/census.py L68 (gap census keys) | counted classes | Gap_Classes sheet |
| lenses/derivation.py L16, L89 | kg3 sets | kg3 registry |
| lenses/registry.py L14 (reading names) | the readings catalog | lenses registry |
| ask.py L197, L312 (kind-branch tuples in renderers) | kind names | Speech_Sources kinds |

~26 mirror sites → ONE mirror-check test module asserting each
cited equality.

## INNOCENT (marked, no move) — the majority (~130)

- **shape** (~100): result/record field-name dicts — every
  `{"yield","completeness","stamp"}` lens envelope, grounding's
  outcome dicts, kg2 node dicts, API payload keys (console L228),
  intake contract fields (kg1_intake L19/21 — cites
  CONTRACT_DATALOAD), run/report shapes.
- **grammar** (~12, each citing its Grammar_Floor rule): produce.py
  prepositions L44 (R1 head-noun), id-tokens L52 (R5 token-head),
  pluralize endings L99 (R1), datepart map L176 (ADR 0076 overlay),
  ordinals L474/523 (R2 instance markers), the R4 voicing phrase
  templates (prose; pinned byte-exact by F4 fixtures).
- **mechanical/external** (~8): ScriptDom class-name lists (mapper
  L79/109/115 — the parser's own API), fold/split literals.
- **frame/process** (~10): intake report headers (inbound
  L113/142), landing CSV headers (land L52 — external contract),
  console door/estate-card guidance lines, trace templates
  (process words per L6-D2 — rendered from trace data only).

## Exempt, noted

- tests/: fixture vocabularies (the seeded earned-vocab VOCAB dict
  simulates a post-cold-start estate) — legitimate as fixtures;
  marked as such in the test file when the census lands.
- src/: the frozen pre-clean-room engine — out of scope.

## Tallies

163 scanner hits + 4 prose items = 167 reviewed.
**OFFENSES: 6** (move) · **MIRRORS: ~26** (cite + equality tests)
· **INNOCENT: ~135** (markers) · exempt: tests/src.
Plus 1 CRITICAL live bug (clarify actions vs USAGE_ACTIONS) and
1 process finding (manifest row #7's evidence was not a test).
