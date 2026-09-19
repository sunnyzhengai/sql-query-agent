# Brief_Fabric_Resident — the engine runs INSIDE Fabric: one wheel, one upload

**Status: BUILT** (2026-09-19 same sitting: the FR7 pin RED→GREEN
— its first red caught the stale egg-info feeding src/ into fresh
wheels; the 2.0.0 wheel in dist/ (sha256 c152919b…, 2.1 MB); the
era-collision set closed at his "approved" (the five reds: the
zones echo → the generator fix; two era-1 laws re-based; the
literal-census markers); FULL SUITE 2232/0 (12:07); ruff zero new
offenses; CLOSED at his Fabric run — the wheel into his
Environment, the three cells speaking. Does this promote? →
proposed WITH Brief_Retirement (RT5), not alone. APPROVED earlier
the same day: "all eight as proposed,
build it" — FR1 all-in-one wheel · FR2 dist/, one current wheel,
old wheels retired · FR3 registries inside the wheel, env-var
override · FR4 explicit estate path · FR5 thin-shell notebook,
logic in aivia/fabric_run.py · FR6 version 2.0.0, pythonnet-only
deps · FR7 the no-repo boot pin · FR8 the manual-work census
ratified. Drafted PRESENTED earlier the same sitting.)

| field | content |
|---|---|
| class | planned addition — the run-in-Fabric lane, queued since the M7 wall ruling; forced open by THE ENVIRONMENT VERDICT (below) |
| claims | Sunny's words (2026-09-19): "yes, draft the fabric-resident brief. where can we record these findings, and make it a prereq so next time we don't go through making these decisions again" · "for fabric build, can you design the .wheel like before? that was the easiest for me to synch up." · THE TURN-KEY RULING, same sitting: "treat this Fabric build as a test run for any future microsoft marketplace customers. what we build today, should be turn-key to future customers. all that can be packaged into .wheel, must be packaged. reduce the manual work to the maximum" |
| impacts (computed) | pyproject.toml RE-BASED (today it still packages the RETIRED src/ tree — the current engine has never been in any wheel; deps carry pyyaml/pydantic that aivia/ never imports) · aivia/graph/metamodel.py (registry path must resolve INSIDE a wheel — F-P1 lands) · aivia/graph/kg2_mapper/scriptdom_loader.py (finds the DLL as package data — F-P4 lands) · estate root becomes configurable (F-P3 lands) · a driver notebook (the console's stand-in in Fabric) · the ship-surface test (dist handling) · SOP fast-gate section (landed with this draft) · tests first for every mechanism |
| ambiguities | FR1–FR7 below — each blocks code until ruled |
| debt declared | F10 (OpenAI egress from Fabric) DEFERRED by Sunny's word — ask-the-graph and Scribe drafts inside Fabric stay CONTINGENT on it; deterministic descriptions, parsing, and the graph build need no egress and are unaffected. F-P2 (pbi_extract in devtools) stays queued |
| Sunny's approval | "all eight as proposed, build it" (2026-09-19) |
| closing check | (filled at CLOSED) |

## THE ENVIRONMENT VERDICT (recorded here so it is never re-derived; the reusable form = the SOP's fast-gate table)

| route | verdict (live run, 2026-09-19, Sunny's hand) | evidence rows |
|---|---|---|
| Windows laptop | BLOCKED — no admin, no sanctioned Python | P3.a: admin credential prompt · P3.c: no Python in the company app portal |
| Fabric workspace | GREEN through F9, zero installs needed | F1–F9 good: role + capacity + notebook + built-in pythonnet 3.0.1 + coreclr + lakehouse upload · F10 deferred by his word |
| **ruled route** | **FABRIC** — this brief | |

## The design (proposal — Sunny rules each FR)

ONE wheel carries the whole engine; his sync becomes: download one
`.whl` from GitHub → upload to the Fabric Environment's custom
libraries → publish → every notebook can `import aivia`.

| id | question | proposal (Sunny may overrule) |
|---|---|---|
| FR1 | what the wheel CONTAINS: engine only (DLL + registries uploaded separately, the August shape) vs ALL-IN-ONE (aivia/ + the 7 registry JSONs + the ScriptDom DLL as package data) | ALL-IN-ONE — one file to move, nothing to forget; ~7 MB, well under Environment library limits; the lakehouse DLL upload step disappears |
| FR2 | where he downloads the wheel: tracked in `dist/` (his old flow — "replace the .wheel file"; raw-file download from GitHub, export-ignored so the source zip stays 2 MB) vs GitHub Releases | tracked in `dist/` — matches his muscle memory; ONE current wheel kept, old wheels retired from the tree at his word (history keeps them) |
| FR3 | registry path when the engine lives in site-packages (F-P1's landing): `importlib.resources` reading the JSONs as package data, with an env-var override for the repo layout | yes — metamodel.py stays the ONE reader; repo layout keeps working unchanged (the override defaults to the existing folder when present) |
| FR4 | estate root in Fabric (F-P3's landing): the boot takes an estate PATH (lakehouse `Files/...`) instead of assuming the repo folder | an explicit argument with the repo default — laptop calls stay identical |
| FR5 | the console's stand-in in Fabric: what does he SEE? | UNDER THE TURN-KEY RULING: the notebook is a THIN SHELL — every line of logic lives in the wheel (a new `aivia/fabric_run.py`, tested like any module; the no-orphan-notebook law). The whole notebook is three one-line cells: `import aivia.fabric_run as f` + `f.dry_run("<Files path to the estate>")` (boot → census counts → every description printed, technical definitions + the AI-generated file/report descriptions) + `f.scribe("<path>")` LAST, contingent-on-F10, runs only at his hand with his key |
| FR6 | pyproject re-base: name/version/deps for the era-2 wheel | name stays `sql-query-agent`; version 2.0.0 (the aivia engine's first wheel — the 1.x line packaged the retired src/); dependencies = `pythonnet>=3.0.1` ONLY (verified: the engine's sole third-party import); `src/` leaves the package config |
| FR7 | wheel build + verification posture | built by `python -m build` at BUILD step, test-first: a pin that installs the wheel into a scratch venv and boots a synthetic estate from it (registries + DLL found INSIDE the wheel, no repo present) — red before the packaging lands, green after; wheel sha256 recorded in the brief at close |
| FR8 | THE MANUAL-WORK CENSUS (the turn-key ruling made mechanical): the census below lists EVERY human step of a customer deployment, each with WHY it cannot live in the wheel. Acceptance at close = the deployment runs with NO step outside the census; any newcomer step is a defect | ratify the census as the turn-key contract; it reprints in the customer-facing deployment doc at the marketplace slice |

## THE MANUAL-WORK CENSUS (FR8 — everything a customer's hands ever do; all else is in the wheel or it is a defect)

| # | manual step | why it cannot be in the wheel | minimized to |
|---|---|---|---|
| 1 | create an Environment, upload the wheel, publish, set it as workspace default | acts on the tenant — Fabric UI/API only | once per workspace; the future marketplace installer automates it via the Fabric REST API (that slice, not this one) |
| 2 | create a lakehouse | same | once, two clicks |
| 3 | upload the estate inputs (the customer's SQL + the dictionary extract + registration.json) | customer data — NEVER ships with the product | one folder upload |
| 4 | create the driver notebook and paste its three one-line cells | a notebook is a Fabric item, not a python file | copy-paste from the deployment doc; zero logic in it |
| 5 | enter the OpenAI key | a secret — never packaged | one setting |

Five steps, once each. Everything else — boot, paths, census,
rendering, drafting, error contracts — lives in the wheel, tested.

## What Fabric runs vs what stays contingent

| capability | needs | status after this brief |
|---|---|---|
| parse work SQL, build the graph, deterministic descriptions | wheel + estate files in the lakehouse | RUNS — no egress, no key |
| ask-the-graph, Scribe drafts | outbound to api.openai.com (F10) + his work key | CONTINGENT — waits on his F10 test |

## Files declared

    AIVIA_Design/briefs/Brief_Fabric_Resident.md
    AIVIA_Design/INDEX.md
    pilots/SOP_Environment_Preflight.md
    pyproject.toml
    aivia/graph/metamodel.py
    aivia/graph/kg2_mapper/scriptdom_loader.py
    aivia/fabric_run.py
    tests/aivia/test_fabric_run.py
    tests/aivia/test_wheel_boot.py
    tests/aivia/test_ship_surface.py
    pilots/work_dryrun/README_Runbook.md
    docs/architecture/TEST_MAP.md

    aivia/console.py
    devtools/scribe_draft.py
    devtools/build_wheel.py
    .gitignore
    dist/sql_query_agent-2.0.0-py3-none-any.whl
    src/zones.py
    tests/test_zones.py
    tests/test_trace_registry.py
    tests/test_release_consistency.py
    tests/test_build_deployment_package.py
    AIVIA_Design/Ruling_Change_Process.md
    AIVIA_Design/briefs/Brief_TEMPLATE.md

(Exact paths added AT APPROVED per this brief's own clause ("add
their exact paths at APPROVED") + the approved FRs that name the
mechanics: console.py = FR4's estate-path landing (build_store is
the ONE boot writer); scribe_draft.py becomes a thin shim — the
scribe driver core moves INTO the wheel per THE TURN-KEY RULING
("all that can be packaged into .wheel, must be packaged");
build_wheel.py = FR7's "built by python -m build" step (copies the
registry JSONs + DLL into the package for the build, cleans after;
.gitignore covers the transient copies); the dist/ wheel = FR2.
ALSO PER FR2 ("old wheels retired from the tree at his word", the
word = "all eight as proposed"): the 48 old-era wheels
(1.56.2–1.83.0) DELETE from the tree — git history keeps every
byte; the 3 deployment zips beside them were never tracked and
left the disk only. The stale 1.x build artifacts (build/,
sql_query_agent.egg-info — untracked) removed: the egg-info's old
SOURCES manifest was feeding src/ into fresh wheels, caught RED by
the FR7 pin.

THE 2.0.0 WHEEL (built at close): sha256
c152919bab9198023ff31709105f0a9071867c351bbcb02e9a83904020525b95
· 2.1 MB · 62 engine files + 7 registry JSONs + the DLL.

THE ERA-COLLISION SET, added at Sunny's "approved" (2026-09-19,
his root-cause ruling — The Retirement Law + The Promotion Gate,
landed in Ruling_Change_Process.md P4/P5 the same breath): the
close's full suite fired FIVE reds — .gitattributes unclassified
(the SECOND echo of the zones class → src/zones.py gains the line
AND the two zone tests gain the Echo-Law generator fix: enumerate
tracked + about-to-be-tracked, so the latch fires BEFORE commit)
+ two ERA-1 LAWS colliding with the ruled era-2 wheel:
test_devtools_can_never_ship pinned "the wheel packages src/*"
(re-based: packages aivia/*, devtools still never ships) and
test_release_consistency demanded the pyproject wheel inside
sql-logic-env.Environment (re-based: pyproject ↔ dist/ is the
living law; sql-logic-env is FROZEN era-1 residue at 1.83.0,
dated retirement slot = the RETIREMENT BRIEF, queued next).)

## RETIREMENT (the 2026-09-19 law, applied retroactively to this pivot)

| supersedes | fate |
|---|---|
| the era-1 wheel line (src/-packaged 1.56.2–1.83.0) | 48 wheels RETIRED from the tree this act (history keeps them); pyproject packages aivia/* |
| the era-1 packaging laws (the two tests above) | RE-BASED to era-2 in this act |
| sql-logic-env.Environment (the era-1 Fabric item) | FROZEN at its 1.83.0 wheel; retirement slot = the Retirement Brief (queued, with src/ + its tests + the era-1 notebooks + the Fabric item folders; the test-census table as worksheet) |

## Build order (after APPROVED)

1. tests first: the wheel-boot pin (FR7) red.
2. pyproject re-base (FR6) + package-data wiring (FR1/FR3) +
   loader route (F-P4) + estate-root argument (FR4).
3. wheel built; pin green; ship-surface test amended for dist.
4. driver notebook (FR5) with its own import-safe test.
5. full suite + ruff; the wheel's sha256 into this brief.
6. commit + push at Sunny's word → his sync: download the .whl,
   upload to the Environment, publish, run the driver notebook.
