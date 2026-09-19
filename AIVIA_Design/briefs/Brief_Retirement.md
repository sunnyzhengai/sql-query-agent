# Brief_Retirement — era 1 leaves the tree (the first standing act of The Retirement Law)

**Status: PRESENTED** (2026-09-19, drafted at Sunny's word "draft
the retirement brief"; design-first — the census below is MEASURED,
not guessed; every fate is his ruling, row by row)

| field | content |
|---|---|
| class | update — retires DECIDED-then-superseded directions under The Retirement Law (P4, ratified 2026-09-19: "when we developed new code to pivot to a new direction, we need ruling that this new direction is confirmed and the old directions need to be retired … the history is always in git history … to keep the current 'production' free of un-used old code") |
| claims | P4 + P5 (Ruling_Change_Process.md) · his test-count question the same sitting: "are there any stale ones we should remove? do we have a mechanism when code changes we check for tests to remove" — the census below IS that mechanism's first run |
| impacts (computed) | the tree loses the era-1 layer (git history keeps every byte) · the suite loses ~115 of 196 modules (the src/-guarding block — runtime drops by roughly half) · src/zones.py + src/trace_registry.py RELOCATE (living suite infrastructure) with their consumers re-pointed · GOVERNED_ENTRIES shrinks with the tree (same act, the zones law) · pyproject dev extras + CI lines trim in a follow-on slice once green |
| ambiguities | RT1–RT5 below — RT1 BLOCKS the Fabric-folder rows until answered |
| debt declared | the dev-extras/CI trim (pyyaml, pydantic, fastapi, requests…) lands AFTER the deletion goes green — declared here so it cannot be forgotten |
| retirement (the P4 field) | this brief IS the retirement act; supersessions named per row below |
| does this promote? (P5) | YES proposed — this close is the natural first dev → main promotion: production tree = era 2 only |
| Sunny's approval | (pending — rule RT1–RT5) |
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
| RT1 | **is ANY live Fabric workspace still git-synced to this repo?** A synced workspace DELETES its items when their folders leave the branch. His personal capacity serves the M-ladder graph today | Sunny answers from his tenant; if no workspace syncs this repo (loads have been manual parquet uploads since the reset), row 5 proceeds; if one does, disconnect first, then proceed |
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
    AIVIA_Design/INDEX.md

(Code paths — the relocations, the consumer re-points, and the
generated deletion manifest — are appended at APPROVED per RT2/RT4;
nothing beyond these two files changes before his rulings.)
