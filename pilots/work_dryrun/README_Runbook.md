# Work Dry-Run Runbook — work SQL through the engine, descriptions seen

**Brief_Work_Dryrun (approved 2026-09-18). THE WALL: engine-outbound
only. Everything below runs in the WORK clone, on work machines.
The work estate folder is named `work_<name>` and is gitignored —
it can never enter a commit. Nothing work-flavored (paths, names,
SQL, outputs) is ever written into this repo's tracked files.
Findings come back as words about the engine only.**

This file contains PLACEHOLDERS only. Fill values at work, in the
work clone.

## One-time setup (work machine)

1. Clone the repo. Good = `git status` clean.
2. Install python 3.11 (Homebrew or work-approved equivalent) and
   the .NET runtime; set `DOTNET_ROOT` to the runtime folder.
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
