# Brief_Packaging — slice 1: the ship surface (the GitHub zip carries the minimum engine, nothing else)

**Status: BUILT** (2026-09-19 same sitting: pins RED→GREEN, archive 62 files ≈2.2 MB zipped, FULL SUITE 2225/0 (11:57), ruff zero new offenses; two his-word additions mid-build — the preflight SOP and the zones/README fixes; CLOSED follows the push + his acceptance download. APPROVED earlier the same day: "all four as proposed, build it" — PK1 gitattributes route · PK2 the 7 registry JSONs only · PK3 no pyproject, the pip line instead · PK4 runbook amendments; same message added the PREREQUISITES table ask: "can you add a table to the runbook: list all prerequisites for AIVIA to work. if different, list a column for windows, a column for fabric … all software, not just python … just prereqs")

| field | content |
|---|---|
| class | planned addition — fills the declared slot: Brief_Work_Dryrun's debt row named "the ALLOWLIST SHIPMENT MANIFEST (his 'never mix' rule made mechanical) is Brief_Packaging's work"; the M7 close queued Brief_Packaging next after the dry run |
| claims | Sunny's words (2026-09-19): "the zip is large and it's taking a long time to unzip" · "is it possible to at least make the main branch clean, so next time, i just download the main branch" · "i don't need to download any sql files. i will use my work's" · "i don't want any design docs to go to work. i only want the minimum set of files for the engine to work." · "go ahead, write the brief" · (post-presentation, same day) "i might not be able to install python … in the runbook, can you add commands for me to: test if python is already installed on my laptop, what version, how to install it" — the preflight section, landed in the runbook at his word |
| impacts (computed) | NO engine code changes; NO registry changes; NO served data (no load). NEW: `.gitattributes` (export-ignore allowlist — GitHub builds its download zips with `git archive`, which skips every path marked export-ignore; nothing is deleted from the repo, only the zip surface shrinks) · a ship-surface test (test-first: archives the tree, asserts the allowlist holds) · the work runbook gains the zip-download route + the `pip install pythonnet` line (its dependency step was missing — found during this brief's step-2 query) · INDEX brief-count line |
| ambiguities | PK1–PK4 below |
| debt declared | SLICE 2 (queued, not this brief): the M7 ship-vs-keep audit findings stay open — F-P1 registries live inside Sunny-only AIVIA_Design (the real fix moves them out; until then the 7 JSONs ship from their current path, see PK2) · F-P2 pbi_extract in devtools · F-P3 estate root hardcoded · F-P4 the DLL loader's two routes. Landing step: the marketplace-grade packaging brief. Tripwire: the ship-surface test pins that NOTHING outside the allowlist ships — any slice-2 relocation that moves a shipped file fails the pin and forces the declaration |
| Sunny's approval | "all four as proposed, build it" (2026-09-19) |
| closing check | (filled at CLOSED) |

## THE SHIP SET (the allowlist — verified against the code, 2026-09-19)

| path | files | why |
|---|---|---|
| `aivia/` | 44 | the engine (imports verified stdlib-only + pythonnet) |
| `libs/` | 3 | `Microsoft.SqlServer.TransactSql.ScriptDom.dll` — the parser |
| `AIVIA_Design/registries/*.json` | 7 | `metamodel.py` hard-codes the path; boot refuses without all seven (kg1_technical, kg2_kind_library, kg2_logic, kg3_artifacts, kg4_concepts, lenses, flows) |
| `pilots/` | 3 | the work runbook + registration template + the environment-preflight SOP |
| `devtools/scribe_draft.py` | 1 | the Scribe driver |
| `AIVIA_Product/SOP_Extract_Runbook.md` + `AIVIA_Product/source_packs/` | 4 | the dictionary-extract machinery |

≈ 61 files, ≈ 7.5 MB (vs today's 1,536 files, 89.2 MB). ZERO `.sql`
files, ZERO design `.md` docs, ZERO estates/fixtures/wheels/data —
each asserted by the test, not by hope.

Everything else is export-ignored: dist (19.0 MB wheels) · data
(17.1 MB) · AIVIA_Product/fixtures (28.7 MB recorded vectors) ·
AIVIA_Product/estates (6.6 MB) · tests + AIVIA_Test · src ·
notebooks + the 21 root *.Notebook folders · the Fabric item
folders (*.SemanticModel, *.SQLDatabase, *.Report, *.Lakehouse,
*.GraphModel, *.Eventhouse, *.Environment) · docs · internal ·
scripts · AIVIA_Design (all but the 7 registry JSONs) · every
root file (README, CHANGELOG, CLAUDE.md, pyproject.toml, configs).

## The ambiguities — Sunny rules each

| id | question | proposal (Sunny may overrule) |
|---|---|---|
| PK1 | the route: he asked "make the main branch clean". A cleaned main means real deletions on main plus a manual sync chore from dev at every release. The `.gitattributes` export-ignore route deletes nothing, has no recurring chore, and makes EVERY zip URL clean — main and dev both | `.gitattributes` — and then downloading dev directly always gives the newest work; a separate clean main becomes unnecessary |
| PK2 | his ruling "i don't want any design docs to go to work" vs the loader's hard requirement: the 7 registry JSONs live INSIDE AIVIA_Design/registries/ and the engine refuses to boot without them. They are generated data tables (code-consumed), not design prose | ship exactly the 7 JSONs at their existing path; every .md, the converter, the validator, and all other AIVIA_Design content stays home. Moving registries OUT of AIVIA_Design = F-P1's real fix, slice 2 |
| PK3 | pyproject.toml: ship it (the formal dependency list) or keep the zip minimal and put the one real dependency in the runbook? (verified: the engine's only third-party import is pythonnet; pyproject's pyyaml/pydantic rows are not imported anywhere in aivia/) | do not ship it; the runbook gains one line: `python3.11 -m pip install pythonnet` |
| PK4 | the runbook still says "clone the repo" (step 1) and never names the zip route he actually uses, nor the pip install | amend `pilots/work_dryrun/README_Runbook.md` in this brief's build: step 1 offers the zip route (the commit-pinned archive URL), setup gains the pip line — a .md edit, placeholders only, the wall untouched. **PARTIALLY LANDED EARLY at Sunny's direct word (2026-09-19, "can you add commands for me to: test if python is already installed…"): the PREFLIGHT section (P1–P7 — python present/version/no-admin install routes, pythonnet via pip + proxy fallback, .NET check + per-user dotnet-install) is in the runbook now, before his weekend; the zip-route line still waits for the build** |

## The test (written FIRST, red then green)

`tests/aivia/test_ship_surface.py` — runs
`git archive --worktree-attributes HEAD`, lists the paths, asserts:

1. every path sits under an allowlisted root (the table above);
2. zero paths end `.sql`;
3. zero `.md` under `AIVIA_Design/`;
4. the required files are PRESENT: `aivia/console.py`, the
   ScriptDom DLL, all 7 registry JSONs, the runbook, the SOP,
   `devtools/scribe_draft.py`;
5. nothing from `dist/`, `data/`, `AIVIA_Product/fixtures/`,
   `AIVIA_Product/estates/`.

Red before `.gitattributes` exists (today's archive carries dist/),
green after. This test IS the mechanical form of the allowlist law.

## Acceptance (Sunny's hand, after push)

Download the dev zip fresh from GitHub. Good = the zip is ~7–8 MB,
~61 files, unzips in seconds, and contains no folder you ruled out.

## Files declared

    AIVIA_Design/briefs/Brief_Packaging.md
    AIVIA_Design/INDEX.md
    .gitattributes
    tests/aivia/test_ship_surface.py
    pilots/work_dryrun/README_Runbook.md
    pilots/SOP_Environment_Preflight.md
    docs/architecture/TEST_MAP.md
    src/zones.py
    libs/README.md

(pilots/SOP_Environment_Preflight.md added mid-build at Sunny's
word, 2026-09-19: "let's create an SOP for pre-flights. instead
of trial and errors. for these two environments: windows and
fabric, create a document if necessary" — the P-steps moved
there from the runbook (one home), a Fabric F-step battery and
the environment verdict table born with it; the runbook keeps a
pointer. The SOP sits under pilots/ so it ships inside the
existing allowlist — no .gitattributes change, ship set 62 files.

src/zones.py added at Sunny's word "add it", 2026-09-19: the
FIRST POST-COMMIT FULL SUITE caught a LATENT M7 finding — pilots/
became tracked at the M7 closing commit but was never declared in
GOVERNED_ENTRIES; every M7-arc suite run predated the commit, so
the declared-zones latch (test_zones + test_trace_registry, the
2026-08-20 law) only fired today. Class FIX: one line, "pilots"
declared governed — it is runbook content that SHIPS.

libs/README.md added at Sunny's word "fix the libs readme",
2026-09-19: the old-era text claimed the DLL is gitignored and
manually downloaded — false since the DLL became tracked (the
.gitignore beside it was already truthful). Rewritten to the
current facts: tracked, ships in the zip, version 18.0.78.1 +
sha256 pinned, laptop route vs lakehouse route named.)

## Build order (after APPROVED)

1. test_ship_surface.py authored, run, RED (dist/ in the archive).
2. `.gitattributes` written (allowlist form: `/* export-ignore`,
   then `-export-ignore` per ship row). Test GREEN.
3. Runbook amendments (PK4): zip route + pip line.
4. TEST_MAP + INDEX count-line, same breath.
5. Full suite + ruff.
6. Commit + push at Sunny's word → his acceptance download.
