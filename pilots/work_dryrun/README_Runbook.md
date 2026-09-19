# Work Dry-Run Runbook — work SQL through the engine, descriptions seen

**Brief_Work_Dryrun (approved 2026-09-18). THE WALL: engine-outbound
only. Everything below runs in the WORK clone, on work machines.
The work estate folder is named `work_<name>` and is gitignored —
it can never enter a commit. Nothing work-flavored (paths, names,
SQL, outputs) is ever written into this repo's tracked files.
Findings come back as words about the engine only.**

This file contains PLACEHOLDERS only. Fill values at work, in the
work clone.

## Prerequisites — everything AIVIA needs to run

| prerequisite | Windows laptop | Fabric (notebook route) |
|---|---|---|
| the engine files | the GitHub ship zip (~7.5 MB), extracted | ONE wheel — `dist/sql_query_agent-2.0.0-py3-none-any.whl` from GitHub; engine + registries + DLL all inside (Brief_Fabric_Resident) |
| Python 3.11 (3.10–3.12 fine; dev = 3.11.15) | per-user install, no admin (P3) | comes WITH the runtime — pick the Environment runtime whose Python is 3.11 (Runtime 1.3 today); never a library install |
| pythonnet — 3.0.1 exact (Fabric-proven 2026-08; floor ≥3.0.1; dev = 3.1.0) | `pip install pythonnet` (P4) | already in the built-in libraries; pin 3.0.1 under Public libraries only if absent |
| .NET runtime 8 (6+ works) | often preinstalled; else per-user (P6) | built into the Fabric runtime — the SOP's F8 probe proves it |
| ScriptDom DLL — 18.0.78.1 (6.9 MB, sha256 `400a457a…`) | ships inside the zip (`libs/`) | inside the wheel — nothing separate to upload |
| the 7 registry JSONs | ship inside the zip (`AIVIA_Design/registries/`) | inside the wheel — nothing separate |
| OpenAI API key | `.env` file at the repo root | notebook secret / environment setting |
| outbound HTTPS to api.openai.com | for asking questions + Scribe drafts only (deterministic descriptions need no network) | same |
| outbound HTTPS to pypi.org | install-time only; proxy fallback in P4 | Fabric reaches pypi natively |
| a web browser | the console at localhost:8377 | none — no console; outputs land in notebook cells |
| admin rights | NOT required — every install is per-user | not applicable |
| git | NOT required (the zip route) | not required |

## The Fabric route (Brief_Fabric_Resident, the turn-key form)

The whole deployment is the FIVE-STEP CENSUS (the brief's FR8 —
any step beyond these five is a defect):

1. Environment: "+ New item" → Environment → runtime with Python
   3.11 → Custom libraries → upload the wheel (download it first:
   `https://github.com/sunnyzhengai/sql-query-agent/raw/dev/dist/sql_query_agent-2.0.0-py3-none-any.whl`)
   → Publish → attach to the notebook (or set as workspace
   default). Good = publish completes; takes minutes.
2. Lakehouse: "+ New item" → Lakehouse. Good = it opens.
3. Estate upload: one folder into the lakehouse Files —
   `registration.json` (from `pilots/work_dryrun/registration_template.json`,
   values filled) + `<source>_snapshot/` (the dictionary extract)
   + `estate_snapshot/` (the SQL batch). Estate data lives in the
   tenant only — the wall.
4. Notebook: "+ New item" → Notebook → attach the Environment →
   paste the three one-line cells:
       import aivia.fabric_run as f
       f.dry_run("/lakehouse/default/Files/<estate folder>")
       f.scribe("/lakehouse/default/Files/<estate folder>")
   Good = cell 2 prints the node census and every description.
   Cell 3 is the PAID seat — run last, your hand, your key,
   contingent on the F10 egress test.
5. The key (only for cell 3 / asking): the OpenAI key as an
   environment setting or notebook secret.

## Preflight — run FIRST

The full preflight battery (Windows P-steps AND Fabric F-steps,
plus the verdict table naming which environment to use) lives in
ONE home: `pilots/SOP_Environment_Preflight.md`. Run Part A
there; proceed below only on a LAPTOP-green verdict.

## One-time setup (work machine)

1. Get the engine — either route:
   - the ship zip (no git needed):
     `https://github.com/sunnyzhengai/sql-query-agent/archive/refs/heads/dev.zip`
     (or pin an exact commit: `.../archive/<sha>.zip`); extract.
     Good = ~7.5 MB, unzips in seconds, contains `aivia/`,
     `libs/`, `pilots/`, `devtools/`, `AIVIA_Design/registries/`,
     `AIVIA_Product/` and nothing else.
   - or clone the repo. Good = `git status` clean.
2. Python 3.11, pythonnet, and the .NET runtime are present —
   the preflight proves all three. Set `DOTNET_ROOT` to the
   runtime folder (the SOP's P6 shows the per-user form).
3. Check the parser loads:
   `python3.11 -c "from aivia.graph.kg2_mapper import scriptdom_loader; scriptdom_loader.load()"`
   Good = no output, exit 0. (The ScriptDom DLL ships in `libs/`.)
4. Put the work OpenAI key in `.env` at the repo root:
   `OPENAI_API_KEY=<work key>`. The engine reads it itself.

## The dictionary extract (W1 — the full source-pack run)

5. Follow `AIVIA_Product/SOP_Extract_Runbook.md` to run the
   source-pack extraction against the work Clarity database.
   Good = `columns.csv`, `joins.csv`, and a `manifest.json`
   carrying `source_pack_version`.

## The estate scaffold

6. Create the estate folder in the WORK clone:

        AIVIA_Product/estates/work_pilot/
            registration.json          <- from registration_template.json, values filled
                                          (db_name/server OPTIONAL — MR1a: absent, the
                                          graph roots at db:<your single source>)
            <source>_snapshot/         <- the step-5 extract (folder name = "<source>_snapshot", e.g. clarity_snapshot)
            estate_snapshot/           <- the small batch of work .sql files

   Good = `git status` shows NOTHING (the work_* guard holds).

## Boot and see the descriptions (W2 — both kinds)

7. `python3.11 -m aivia.console work_pilot`
   then open http://localhost:8377. Good = the estate answers;
   technical definitions and scope/statement renders (the
   deterministic descriptions) are already speaking — they land
   at boot, no key involved.
8. Scribe drafts (the paid run, your hand):
   `python3.11 devtools/scribe_draft.py work_pilot`
   Good = `descriptions_draft.json` appears in the estate folder
   and the drafts print to the terminal.
9. Review the drafts sentence by sentence (the cage discipline:
   no words the technical definition and the file's own name
   cannot account for; purpose clauses are the known inference —
   accept by eye, the FG2 posture).
10. Approve: merge the texts you accept into the estate's
    `descriptions.json` under `"descriptions"`, with
    `"status": "approved"` (or per-identity `"statuses"`), plus
    `"basis"` and `"created_at"` (copy the shape from any estate
    here). Reboot the console. Good = every approved file
    description speaks, each starting **"AI-generated: "**.

## What comes back to AIVIA

Words only: parse rates, unresolved counts, render quality notes,
engine gaps — as FINDINGS rows in the brief. Never a file name,
never a query, never an output.
