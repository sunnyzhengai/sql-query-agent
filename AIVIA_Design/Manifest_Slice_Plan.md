# Manifest_Slice_Plan — the eight-slice build plan

**STATUS: EXECUTED — all 8 slices shipped 2026-09-06 (+ both shakedowns). Kept as the record of the ruled route; superseding ledger: Manifest_Build.md.** (DRAFT header retired 2026-09-09, documentation audit.)

*The ruled route through the build: eight slices in dependency order,
each with entry obligations (what must be ruled/ratified before code),
scope (modules from the Code Structure Maps + verdicts from the Port
Manifest), and exit criteria (which fixtures and checks go green).
Authored 2026-09-05 against the closed design.*

**Laws of this plan**

1. A slice opens only when its entry obligations are met — an entry
   obligation is a RULING or RATIFICATION, never code. Sunny-side
   obligations are marked (Sunny).
2. A slice closes only when its exit criteria are mechanically green:
   the named fixtures byte-exact, the named checks passing, both
   validators (GV + RG) green, ruff + pytest green. No slice closes
   on "mostly."
3. Protocol steps ride every slice: fixtures before code (step 4),
   code never introduces a concept the registry lacks (step 5),
   discoveries flow doc → registry → code (step 6).
4. The import-law plank and the imports-nothing-deferred check run
   from slice 0 onward — deferrals stay checkable the whole build.
5. The existing repo stays untouched and runnable (the demo path)
   through every slice.

---

## Slice 0 — Enforcement bedrock (the machinery that checks everything after it)

**Entry obligations:** the ratification pass (Sunny) — doc sections
stamped, registries flipped `ratified: true` (unblocks RG-A2).

**Scope:** new package skeleton per the Import_Law sheet ·
`graph/metamodel.py` load side (registry loader) · stamp-compare CI
(doc stamp == registry stamp) · build-phase validator (port + grow
`validate_fixtures.py` + `validate_registries.py`) · planks: import
law, parser-only-in-mapper, no-LLM-in-graph/lenses,
store-callable-only-by-lifecycle, imports-nothing-deferred ·
rule-to-check closure meta-test wired into CI.

**Exit:** RG all green including RG-A2 (the standing NOT-RUNNABLE
closes) · plank suite green over the skeleton · CI runs ruff +
pytest + both validators on every push.

## Slice 1 — KG1 intake (the technical layer)

**Entry obligations:** none open — A1/A2/A8/A14 already ruled;
A14's quarantine + count + DBA alert (HITL) is implementation here.

**Scope:** `graph/store.py` (append-only substrate) ·
`graph/metamodel.py` validate side · `graph/kg1_intake.py`
(apply_registration, validate_extract, apply_extract, group_joins,
phrase_extract) · `flows/inbound.py` extract door.

**Exit:** F1 expected_graph reproduced node-by-node ·
INTAKE-0..10 · CHECK-TL-1..5, 6a, 7 · F6 refusal cases (unregistered
db, keyless table, illegal declaration) refuse BY NAME · GV-A..D
green over the built graph, not just the fixture.

## Slice 2 — KG2 mapper (the logic layer)

**Entry obligations:** kind-library fixture families authored before
mapper code (protocol step 4): construct, adversarial (the corpse
catalog — this is where PM-4's clean-room bet is secured), remainder
cases · PM-1's door-2 PHI redaction fixtures authored into F6 (owed
before phi_gate code, even though door 2 exercises at the inward
build).

**Scope:** `graph/phi_gate.py` REWORK (door 1 live: estate text) ·
parser adapter PORT (`src/parser/` + native-parser-law plank, suites
as acceptance) · `graph/kg2_mapper.py` (map_tree to the kind library,
resolve, apply_file; Scope_Identity sheet is the identity law) ·
`flows/inbound.py` estate door.

**Exit:** F2 expected_trees byte-exact (::delivery keys per A11) ·
GV-E evidence tiling becomes RUNNABLE and green (the fixture
validator's honest NOT-RUNNABLE closes) · CHECK-KG2-1..8 · kind
library construct/adversarial/remainder families green · ported
parser suites green in their new address.

## Slice 3 — Read API + the v1 lenses

**Entry obligations:** none — the catalog's v1 flag column is the
scope authority.

**Scope:** `graph/read_api.py` · `lenses/registry.py` · the 13
v1-flagged rows across derivation, decisions, compliance
(join_compliance only), families (relatedness only), census.

**Exit:** F3 expected_lenses byte-exact (structured compliant paths,
enumerated staleness, degenerate literals excluded from membership —
all per the 09-05 rulings) · CHECK-LENS-D1 reachability accounting ·
lens purity plank (read_api is the only import).

## Slice 4 — KG3 artifacts + KG4 concepts (the ledger)

**Entry obligations:** none open.

**Scope:** `graph/kg3_artifacts.py` (spine, per-class appends,
supersede, redaction_act — the ONE destruction path) ·
`graph/kg4_concepts.py` (mint).

**Exit:** LC3 lifecycle tests (ownership flip, proposed-never-current,
no-retire-path structural) · fixture families: ownership flip,
disagreement, succession, conservation · CHECK-KG3-1..7, KG4-1..3 ·
derivation lenses (slice 3) now read real chains.

## Slice 5 — Produce (outward stage 1)

**Entry obligations (Sunny):** A13 — the floor grammar becomes a
RATIFIED versioned design artifact, seeded by the ported skeleton
composer; F4 upgrades from interim substring-grade to exact floor
text · ECON params ruled (H8's budgeted queue: batch size, budget,
usage-weighted priority — v1 values can be trivial, but they must be
declared data, not code defaults).

**Scope:** `flows/run_events.py` REWORK (`src/run_layer.py` + H10
outcome/abort) · `flows/gates.py` PORT (produce text gates +
injection fixtures per PM-2; caption family stays behind) ·
`flows/produce.py` REWORK (produce machinery + composer; staleness
lens IS the worklist).

**Exit:** F4 exact-match under the ratified grammar · PROD-1..5 ·
OPS-2/3 (per-artifact atomicity, abort accounting) · gate suites +
injection fixtures green · replay determinism demonstrated (same
graph + versions run twice → identical skeletons and verdicts).

## Slice 6 — Approve + Land + Materialize (outward stages 2–3)

**Entry obligations (Sunny):** A15 — per-target export column
headers bind HERE, from the term-propose precedent (this slice, not
slice 0: "the build slice" in that ruling means the slice that
builds the exports).

**Scope:** `flows/approve.py` (dispositions-only surface) ·
`flows/land.py` REWORK (file_export donor; render → confirm → send →
observe; file-first only) · `flows/materialize.py`.

**Exit:** F5 approve/land scripts byte-exact · APPR-1 · LAND-1..5
(B4 confirmation, anti-repeat, sent-before-transport, zero custom
attributes, append-only observations) · OPS-1 stamped reports · the
X-Ray export bundle renders with the bound headers.

## Slice 7 — Full circle (no new modules)

**Entry obligations:** none — this slice exists to prove the others.

**Scope:** the CrossLayer_Acceptance families: end-to-end (synthetic
extract + estate → layers built → produce → approve → land → files
match authored expectations) · the complete F6 refusal sweep — every
refusal names its rule · the two-denominator coverage metric computed
from working-set + L1 · the SOP intake report rendered as the DBA
would receive it.

**Exit:** all of F1–F6 green in one run from empty · both validators
green · demo path still untouched and passing its own suite. This is
the moment the new architecture can run a real X-Ray engagement.

---

## What is in NO slice (the deferral ledger, restated)

Inward flow (match/ground/generate + caption gates + door-2 PHI
live), usage/expertise/blast-radius/demand lenses, divergence/
concept-drift/correspondence, API transport, TMDL/Snowflake
dialects. Each has its donors recorded in the Port Manifest; the
imports-nothing-deferred plank keeps all of it structurally absent
from v1.

## Sunny-side obligations, collected

- Before slice 0: the ratification pass (doc stamps + registry flips).
- Before slice 5: A13 floor-grammar ratification · ECON param values.
- Before slice 6: A15 export header binding per target.
- Anytime: A11's ::delivery ruling currently lives only in the
  register + fixtures — a one-line landing in the doc's
  Disambiguation list would close the loop.
