# 10_work_wheel_production_steps — the WORK Fabric runbook

Status: DRAFT 2026-10-06, written from the personal-Fabric
rehearsal (Step 1 of the TEMP checklist); FINALIZED when the
rehearsal closes. The permanent home for the work-side
instructions — the TEMP checklist points here and dies at the
end of the road; this doc stays.

THE LAWS RIDING EVERY STEP: metadata boundary (the LLM sees
SQL text + dictionaries, never query results — work's approval
condition) · the wall (work SQL and work outputs NEVER come
back to the repo) · the one-wheel law (ONE sqldesc wheel in
the environment; stop the session after every publish) ·
blessed-only (no unblessed name reaches Collibra).

## Prereqs (pack before the first session — checklist Step 2)

- [ ] `ai01_sqldesc-0.5.6-py3-none-any.whl` (or newer; the
      version ladder law — never two versions installed)
- [ ] The three dictionary files ONLY:
      `02_emr_data_dictionary_extraction_column.json`,
      `..._extraction_value.json`, `..._extraction_table.json`
- [ ] Her OpenAI key, entered as a workspace/notebook SECRET —
      never pasted into a committed cell
- [ ] The DevOps path of the `*.SemanticModel` folders (TMDL)
- [ ] Which SQL files go in (and that their names end `.sql` —
      the rehearsal's bare-name lesson: portal uploads can
      drop extensions; the run sweeps `*.sql` only)

## Step A — the environment (once)

1. Work Fabric portal -> the workspace -> New/open the
   ENVIRONMENT item.
2. Libraries -> PUBLIC libraries -> add `openai` pinned
   (3.19.2 — the parity pin) — THIS is what installs the
   seat's dependency tree (the rehearsal's httpx lesson;
   custom wheels alone do not resolve it).
3. Libraries -> CUSTOM libraries -> upload the wheel. ONE
   sqldesc wheel, ever.
4. Publish all -> wait for Success -> any open notebook
   session is now STALE: stop it.

## Step B — the lakehouse folders (once)

    Files/01_sql_input/      <- the work SQL files (*.sql)
    Files/02_dictionary/     <- the three extraction files
    Files/tmdl/              <- the *.SemanticModel folders
    Files/out/               <- the run writes here

Upload the inputs; eyeball that sql names end `.sql`.

## Step C — the notebook (fresh session, environment attached)

Cell 1 — the key (from the workspace secret; adjust to however
the secret is stored at work — vault getSecret or a pipeline/
notebook secret; NEVER a literal in the cell):

    import os
    os.environ["OPENAI_API_KEY"] = <the secret read>
    print("key loaded:", bool(os.environ["OPENAI_API_KEY"]))

Cell 2 — THE PREFLIGHT (the same shipped check as the
rehearsal — tenant-blind; must end `/ 0 fail`; every FAIL
line names its own fix):

    import sqldesc_cli
    sqldesc_cli.preflight(
        "/lakehouse/default/Files/tmdl",
        "/lakehouse/default/Files/01_sql_input",
        "/lakehouse/default/Files/out",
        dict_dir="/lakehouse/default/Files/02_dictionary")

Expected work-side differences from the rehearsal board: the
names asset is absent (no 03 folder at work) — that is the
ruled honest fallback, not a failure; the blessing registry
starts empty — blessings are made here and STAY here.

Cell 3 — THE RUN (her hand; quiet minutes = paid calls
working; deliver re-runs the preflight itself and refuses on
any failure except a missing key):

    sqldesc_cli.deliver(
        "/lakehouse/default/Files/tmdl",
        "/lakehouse/default/Files/01_sql_input",
        "/lakehouse/default/Files/out",
        dict_dir="/lakehouse/default/Files/02_dictionary")

Cell 4 — the eye:

    print(open("/lakehouse/default/Files/out/"
               "08_report_descriptions.txt").read()[:4000])

## Step D — gap-check and bless (her hand)

1. Read the official txt; check cards + technical definitions
   against the SQL she knows.
2. Bless the keeper names:

    import business_terms as bt
    bt.bless("/lakehouse/default/Files/out",
             "/lakehouse/default/Files/out/07",
             "<node_id>", "<report name>",
             "RULED <date> (Sunny): <her words>")

3. The artifact for Collibra: `Files/out/ai_delivery.json` —
   her publish notebook reads it, filters blessed itself,
   maps names to Collibra ids at push time.

## What never happens here

No work file, output, or blessing comes back to the repo (the
wall). No pytest suites at work (locks live at home; the
preflight is the shipped check). No second sqldesc wheel. No
key in any cell, file, or commit.
