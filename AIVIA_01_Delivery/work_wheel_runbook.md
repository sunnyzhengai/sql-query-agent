# work_wheel_runbook — deploying the engine on a customer Fabric tenant

Status: FINAL 2026-10-06 — the rehearsal CLOSED same day (Step 1
of the TEMP checklist, blessed: 1 on Fabric); every cell below
is rehearsal-proven. The permanent home for the work-side
instructions — the TEMP checklist points here and dies at the
end of the road; this doc stays.

THE LAWS RIDING EVERY STEP: metadata boundary (the LLM sees
SQL text + dictionaries, never query results — work's approval
condition) · the wall (work SQL and work outputs NEVER come
back to the repo) · the one-wheel law (ONE sqldesc wheel in
the environment; stop the session after every publish) ·
blessed-only (no unblessed name reaches Collibra).

## Prereqs (pack before the first session — checklist Step 2)

- [ ] the NEWEST `ai01_sqldesc-*.whl` from wheel/ in this folder (the
      version ladder law — never two versions installed)
- [ ] The dictionary (the full-dictionary ruling, 2026-10-06):
      run the four SHAPE-MATCHED queries in
      dictionary_extraction/ against the tenant's Clarity
      dictionary tables (metadata only), unscoped:
      1. dict_extract_table.sql   -> dict_extract_table.csv
      2. dict_extract_column.sql  -> dict_extract_column.csv
         (primary keys + ini/item already folded in)
      3. dict_extract_join.sql    -> dict_extract_join.csv
      4. dict_extract_value.sql   -> dict_extract_value.csv,
         then APPEND the result of the query ASSEMBLED by
         dict_extract_value_generator.sql (the ZC universe —
         eyeball the generated SQL before running it)
      Then: `python tools/csv_to_json.py <csv_dir> <json_dir>`
      (zero logic — the SQL already speaks the engine's shape)
      and upload the four json files. Raw extraction carries
      no embeddings — full Clarity lands in the low hundreds
      of MB, fine for Fabric Files.
- [ ] The runner's LLM API key, entered as a workspace/notebook
      SECRET — never pasted into a committed cell
- [ ] The DevOps path of the `*.SemanticModel` folders (TMDL)
- [ ] Which SQL files go in (and that their names end `.sql` —
      the rehearsal's bare-name lesson: portal uploads can
      drop extensions; the run sweeps `*.sql` only)

## Step 0 — create the Fabric items (once; skip any that exist)

DO NOT mirror any other tenant's folder estate — the engine
needs ONLY the Step B folders below. Record every name/id you
create in `tenant_intake.md` section 1.

1. Fabric portal -> your workspace -> **+ New item** ->
   **Lakehouse** -> name it (your convention) -> Create.
2. **+ New item** -> **Environment** -> name it -> Create.
3. **+ New item** -> **Notebook** -> name it; in the notebook
   toolbar set **Environment** to the one you created, and in
   the Explorer pane **Add data items -> your lakehouse** (it
   becomes `/lakehouse/default/...` in the cells).
4. The workspace/lakehouse ids live in the browser URL when
   the lakehouse is open: `.../groups/<workspace-id>/
   lakehouses/<lakehouse-id>` — copy both into the intake.

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
    Files/02_dictionary/     <- the FOUR extraction files
                                (column, value, table, join)
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

Cell 3 — THE RUN (the runner's hand; quiet minutes = paid calls
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

## Step D — gap-check and bless (the data owner's hand)

1. Read the official txt; check cards + technical definitions
   against the SQL the reviewer knows.
2. Bless the keeper names:

    import business_terms as bt
    bt.bless("/lakehouse/default/Files/out",
             "/lakehouse/default/Files/out/07",
             "<node_id>", "<report name>",
             "RULED <date> (<the blesser>): <the ruling>")

3. The artifact for Collibra: `Files/out/ai_delivery.json` —
   her publish notebook reads it, filters blessed itself,
   maps names to Collibra ids at push time.

## If a run is canceled or the seat was broken mid-run

build07 checkpoints per node (07_live_checkpoint.json in
<out>/07/). A canceled or broken run leaves its failed nodes
checkpointed as floors, and a later resume SKIPS them (rehearsal
find #7: eight file cards stayed floored after the seat was
fixed). After fixing any seat problem: delete
<out>/07/07_live_checkpoint.json if present, keep the blessing
registry, and re-run the chain clean in the SAME session.

## What never happens here

No work file, output, or blessing comes back to the repo (the
wall). No pytest suites at work (locks live at home; the
preflight is the shipped check). No second sqldesc wheel. No
key in any cell, file, or commit.
