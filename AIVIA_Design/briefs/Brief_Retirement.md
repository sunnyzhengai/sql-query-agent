# Brief_Retirement — era 1 leaves the tree (the first standing act of The Retirement Law)

**Status: BUILT** (2026-09-19, the same sitting: 831 files retired
by manifest · src/ 134 → 15 (the measured living closure; RT2's
relocation deferred with recorded reason — the docs-untangle
slice) · THE RECONCILE at his "B, reconcile it" (the 20
record-consistency reds: 42 SPEC rows re-based to RETIRED with
retired_checks history, the row-audit catching one mis-copied row;
history checks consult the manifest; seven era-1 laws retired with
their subjects; the parse-door law re-pointed era-2) · FULL SUITE
743/0 (11:01) · ruff clean · CLOSED at the push + his RT5
promotion word. APPROVED earlier same day: RT1 "no workspace is
git-synced, my loads have been manual uploads" → RT2–RT5 "all four
as proposed, build it".)

| field | content |
|---|---|
| class | update — retires DECIDED-then-superseded directions under The Retirement Law (P4, ratified 2026-09-19: "when we developed new code to pivot to a new direction, we need ruling that this new direction is confirmed and the old directions need to be retired … the history is always in git history … to keep the current 'production' free of un-used old code") |
| claims | P4 + P5 (Ruling_Change_Process.md) · his test-count question the same sitting: "are there any stale ones we should remove? do we have a mechanism when code changes we check for tests to remove" — the census below IS that mechanism's first run |
| impacts (computed) | the tree loses the era-1 layer (git history keeps every byte) · the suite loses ~115 of 196 modules (the src/-guarding block — runtime drops by roughly half) · src/zones.py + src/trace_registry.py RELOCATE (living suite infrastructure) with their consumers re-pointed · GOVERNED_ENTRIES shrinks with the tree (same act, the zones law) · pyproject dev extras + CI lines trim in a follow-on slice once green |
| ambiguities | RT1–RT5 below — RT1 BLOCKS the Fabric-folder rows until answered |
| debt declared | the dev-extras/CI trim (pyyaml, pydantic, fastapi, requests…) lands AFTER the deletion goes green — declared here so it cannot be forgotten |
| retirement (the P4 field) | this brief IS the retirement act; supersessions named per row below |
| does this promote? (P5) | YES proposed — this close is the natural first dev → main promotion: production tree = era 2 only |
| Sunny's approval | RT1: "no workspace is git-synced, my loads have been manual uploads" · RT2–RT5: "all four as proposed, build it" (2026-09-19) |
| closing check | (filled at CLOSED) |

## THE RETIREMENT CENSUS (measured 2026-09-19)

| # | entry | tracked files | guarded by | proposed fate |
|---|---|---|---|---|
| 1 | `src/` (the era-1 engine) | 134 | 115 of 196 test modules | RETIRE — except row 2 |
| 2 | `src/zones.py` + `src/trace_registry.py` | 2 | test_zones · test_trace_registry · scripts/generate_docs.py · devtools/suite_map.py — LIVING suite infrastructure | RELOCATE (RT2), consumers re-pointed same act |
| 3 | the ~115 src-guarding test modules | ~115 | — | RETIRE WITH THEIR CODE (the law: old tests retire with the old direction) |
| 4 | the 21 root `*.Notebook` folders (010–950) | ~21 | none current | RETIRE |
| 5 | the Fabric item folders (`*.SemanticModel`, `*.SQLDatabase`, `*.Report`, `*.Lakehouse`, `*.GraphModel`, `*.Eventhouse`, `sql-logic-env.Environment`, telemetry) | ~330 | the sql-logic-env freeze pin | RETIRE — **BLOCKED ON RT1** |
| 6 | `data/` (era-1 demo/synthetic corpora, 17.1 MB) | 94 | era-1 tests only | RETIRE |
| 7 | `notebooks/` (era-1 utilities) | 17 | none | RETIRE |
| 8 | `scripts/` | 23 | CI runs generate_docs.py + detect_dead_code.py | SPLIT: the CI-living scripts KEEP; the 10 src-importing pipeline scripts RETIRE |
| 9 | `devtools/` era-1 members (29 import src) | ~29 | — | SPLIT: living tools KEEP (suite_map, change_gate, build_wheel, scribe_draft, graph_visual, pbi_extract); the src-importers RETIRE |
| 10 | `marketplace_host/` (SaaS fulfillment webhook) | 4 | its tests | FREEZE (RT3) — era-1 built, marketplace-future relevant (ADR 0063) |
| 11 | `website/` | 3 | none | RETIRE (RT3) |
| 12 | `environment/` | 2 | **CI installs with `-c environment/requirements.txt`** — living | KEEP until the CI trim slice re-rules it |
| 13 | `docs/` (127) + `internal/` (12) | 139 | suite_map reads the trace claims | KEEP — records and law, never retired |
| 14 | `dist/` (the 2.0.0 wheel) · `aivia/` · `AIVIA_*` · `libs/` · `pilots/` · `tests/` (current-era) | — | the era-2 pins | KEEP — this IS production |

## The ambiguities — Sunny rules each

| id | question | proposal (Sunny may overrule) |
|---|---|---|
| RT1 | **is ANY live Fabric workspace still git-synced to this repo?** A synced workspace DELETES its items when their folders leave the branch. His personal capacity serves the M-ladder graph today | **RULED (Sunny, 2026-09-19): "no workspace is git-synced, my loads have been manual uploads"** — row 5 UNBLOCKED; deleting the item folders touches no live tenant item |
| RT2 | the relocation home for zones.py + trace_registry.py | `devtools/` — suite infrastructure beside the gate and the map; imports re-pointed in the four consumers, a rename-only act |
| RT3 | marketplace_host / website | freeze marketplace_host (its slot = the marketplace slice) · retire website |
| RT4 | the mass-deletion declaration form: the hard gate wants exact paths, and row-level deletion is ~600 files | at APPROVED, a generated appendix (`Brief_Retirement_manifest.txt`, one exact path per line) becomes the declared deletion set; the closing check diffs against it mechanically |
| RT5 | the promotion (P5): merge dev → main when this closes green? | YES — the first promotion: production = era 2 only, and the main-branch zip his work side downloads becomes the clean tree he asked for on day one |

## Build order (after APPROVED)

1. RT1 answered; manifest generated + appended (RT4).
2. Relocations (RT2) with consumer re-points; suite green proves them.
3. The deletion in census order, rows 1→11; GOVERNED_ENTRIES and
   the freeze pin retire in the same act as their subjects.
4. TEST_MAP regenerated (module count drops ~115); full suite +
   ruff; expected runtime roughly halves.
5. Closing check against the manifest; commit + push at Sunny's
   word; promotion (RT5) at his separate word.

## Files declared

    AIVIA_Design/briefs/Brief_Retirement.md
    AIVIA_Design/briefs/Brief_Retirement_manifest.txt
    AIVIA_Design/INDEX.md
    src/zones.py
    tests/test_release_consistency.py
    docs/architecture/TEST_MAP.md
    docs/architecture/SPEC.md
    docs/architecture/AXIOM_CROSSWALK.md
    docs/architecture/DECISION_LANDING_MATRIX.md
    src/spec_registry.py
    tests/test_spec_registry.py
    tests/test_trace_registry.py
    tests/test_docs_consistency.py
    tests/test_zones.py
    tests/test_native_parser_law.py
    tests/test_table_contracts.py
    devtools/suite_map.py

(+ the deletions, each named in the manifest — RT4's form. The
second block of declared files = THE RECONCILE, Sunny's "B,
reconcile it" (2026-09-19): the 20 record-consistency reds ruled
class by class — era-1 laws retire with their subjects
(notebook contract · internal-zone-ship · install-guide coverage ·
shapes seed · boundary-ops · the suite-map tags live-probe and
boundary-echo); LIVING records re-base to the truth (SPEC rows
whose every check retired flip to the new RETIRED status, dead
check paths preserved in retired_checks; the parse-door law
re-points to the era-2 door aivia/…/scriptdom_loader.py; the
writers ground-truth test retires with the notebooks that were
its ground); HISTORY citations (trace registry rows, doc links)
stay verbatim — their existence checks consult the committed
retirement manifest: a cited path must exist OR be recorded
retired.)

## BUILD DELTAS (measured during the build, the census corrected)

1. THE LIVING CLOSURE IS 14 MODULES, NOT 2: scripts/generate_docs.py
   (CI's docs generator) consumes SEVEN src registries (integration,
   notebook, schemas, trace, spec, branding, landing), trace imports
   spec, schemas imports models, and rescued devtools tools pull in
   agent_backend/config/llm_client/secrets_vault. src/ therefore
   SURVIVES TRIMMED to __init__ + 14 living modules (134 → 15 files).
   **RT2's relocation is DEFERRED with recorded reason (Echo Law):
   the docs generator braids living design machinery (SPEC, axioms,
   TEST_MAP) with era-1 content registries; moving 2 of 14 buys
   nothing. Landing step: the DOCS-UNTANGLE slice (its own brief),
   where the whole family moves and src/ dies.**
2. SECOND-PASS RETIREMENTS: eight era-1 test modules imported dead
   TOOLS (not src) and slipped the first cut — retired with their
   subjects per the law, plus three orphaned audit tools whose only
   consumers they were.
3. ONE FALSE DELETION CAUGHT: src/models.py briefly retired by a
   consumer-scan that skipped src-internal imports; schemas.py's
   import broke collection immediately — restored, the scan's blind
   spot noted here so the docs-untangle slice re-measures fresh.
4. The living pin test_devtools_can_never_ship MOVED to
   tests/test_release_consistency.py before its era-1 module
   retired; the freeze pin became the stays-retired pin
   (sql-logic-env may never reappear).
5. tests/ dropped from 196 to ~90 modules, 2232 → ~800 tests —
   the era-1 block held the giant parser/extractor suites.
