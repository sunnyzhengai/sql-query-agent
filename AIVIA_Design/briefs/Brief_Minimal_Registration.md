# Brief_Minimal_Registration — db_name and server become optional

**Status: BUILT** (2026-09-19 same sitting: pins RED→GREEN 6/6
(absent-db roots at db:<source> · present-db byte-identical ·
INTAKE-10 two-source refusal · minimal manifest passes · the
cross-check armed both-sided, waived one-sided); FULL SUITE 757/0
(11:02); ruff clean; templates + pack docs carry the minimal form.
THE WHEEL CARRY DEFERRED at his "option 1": the 2.0.0 wheel at
work predates this change — his pilot runs with the one-word
db_name/server filler (identities identical either way: db:clarity);
the 2.1.0 wheel rides the next release word. CLOSED at his minimal
boot. APPROVED: MR1 ruled "a" — absent db_name,
the graph roots at `db:<the single registered source>`; two
sources with no db_name = a named refusal. Presented the same
sitting at "keep db name and server names optional".)

| field | content |
|---|---|
| class | update — amends DECIDED intake law (MANIFEST_FIELDS requires db_name/server non-empty; INTAKE-8/9 compare declared vs captured db; L1_KG1_CONTRACT_DATALOAD governs) |
| claims | Sunny's words (2026-09-19): "this is overlapping with the registrations file" · "why do we need all this info? we are reading sql files. in those sql files, no database name, only schema name, and tables and columns" · "keep it minimal for this pilot run" · "keep db name and server names optional" |
| impacts (computed) | aivia/graph/kg1_intake.py: MANIFEST_FIELDS drops db_name/server from the required tuple; the INTAKE-8/9 wrong-database cross-check runs ONLY when both files provide db_name (providing it OPTS IN to the check — the check itself stays law); the db root node needs an anchor when db_name is absent (MR1); inbound.py's boot prose tolerates absence · registration_template.json + the runbook's minimal forms · tests FIRST: absent-db boot green, present-db behavior byte-identical (every existing estate provides db_name — zero behavior change for them), the opt-in cross-check still refuses on mismatch |
| ambiguities | MR1 below |
| debt declared | none — the cross-check survives as opt-in; the SOP/runbook name the trade plainly (no db_name = no wrong-database refusal) |
| retirement (P4) | nothing retires; INTAKE-8/9 narrow from mandatory to opt-in |
| does this promote? (P5) | with the next promotion after CLOSED |
| Sunny's approval | MR1: "a" (2026-09-19) |
| closing check | (filled at CLOSED) |

## MR1 — the one design question: what anchors the graph when db_name is absent?

Every identity in the graph roots at `db:<db_name>` today. Absent
db_name needs a deterministic anchor.

| option | root when absent | trade |
|---|---|---|
| a (proposed) | `db:<source>` (the estate's single registered source, e.g. `db:clarity`) | reads naturally ("the clarity estate"); collides only if one estate ever registers two sources with no db_name — refused with a named message at that moment |
| b | `db:local` (a constant) | simplest; reads generically |
| c | `db:<estate folder name>` | unique per estate; but bakes a folder name into every identity |

## Files declared

    AIVIA_Design/briefs/Brief_Minimal_Registration.md
    AIVIA_Design/INDEX.md
    aivia/graph/kg1_intake.py
    aivia/flows/inbound.py
    tests/aivia/test_minimal_registration.py
    pilots/work_dryrun/registration_template.json
    pilots/work_dryrun/README_Runbook.md
    AIVIA_Product/source_packs/clarity/06_manifest.sql
    AIVIA_Product/source_packs/clarity/README.md
    docs/architecture/TEST_MAP.md

## Build order (after MR1 ruled)

1. Tests first, RED: absent-db boot · present-db byte-identity ·
   the opt-in mismatch refusal.
2. kg1_intake + inbound; templates + runbook minimal forms;
   06_manifest.sql marks db_name/server optional.
3. Full suite + ruff; close at his next boot.
