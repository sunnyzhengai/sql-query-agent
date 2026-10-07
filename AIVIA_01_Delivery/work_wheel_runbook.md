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
- [ ] The runner's LLM API key, stored in an Azure Key Vault
      (Step K below); customer tenants vault-only — the paste
      interim exists solely under Cell 1 Form 2's conditions
- [ ] The DevOps path of the `*.SemanticModel` folders (TMDL) —
      Step T below tells how to find it and how to pull the
      folders (manual zip or the automated notebook cell)
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

## Step T — getting the TMDL (the `*.SemanticModel` folders)

The engine reads TMDL files, not published Power BI items. A
workspace's items are files ONLY if the workspace is connected
to Git — then every Synced item sits in the repo as a
`<name>.SemanticModel` folder.

Find the right workspace and its repo:

1. A Git-connected workspace shows a **Source control** button
   in its toolbar and a **Git status** column (Synced /
   Uncommitted) in the item list. No button, no column = not
   connected (prod workspaces often aren't — use their
   git-connected test twin; the TMDL then describes the TEST
   version of each model, usually identical to prod except
   connection settings).
2. In the connected workspace: **Workspace settings** (button
   top-right of the workspace page, NOT the portal's gear) ->
   **Git integration** -> copy the organization, project,
   repo, and branch into `tenant_intake.md`.
3. Only **Synced** items are in the repo. An **Uncommitted**
   item you want: Source control button -> select it ->
   Commit (needs commit rights on that workspace).

### T-manual — browse and download by hand

1. Go to dev.azure.com, sign in, click the organization ->
   the project.
2. Left menu -> **Repos** -> **Files**; set the repo picker
   and the branch picker (top of the file view) to the values
   from Git integration.
3. Open the folder holding the reports; each model is a
   `<name>.SemanticModel` folder (ignore the `.Report`
   folders — the engine does not read them).
4. Hover a `.SemanticModel` folder -> **...** -> **Download
   as Zip** -> unzip locally -> upload the folder into the
   lakehouse `Files/tmdl/`.

### T-auto — the notebook cell (repeatable; replaces manual)

Needs a DevOps **Personal Access Token (PAT)**: dev.azure.com
-> top-right user-settings icon (person with gear) ->
**Personal access tokens** -> **+ New Token** -> scope **Code:
Read** only, short expiry -> Create -> copy once. A PAT is a
password-equivalent: it rides the SAME rules as the LLM key —
vault, or Cell 1 Form 2's paste-interim conditions and scrub.

    import io, os, shutil, zipfile, requests

    ORG, PROJECT, REPO = "<org>", "<project>", "<repo>"
    BRANCH = "main"
    FOLDERS = ["<repo folder>", "<another folder>"]  # or ["/"]
    #            for the WHOLE repo in one pull
    PAT = "PASTE-PAT-HERE"  # Form 2 rules: scrub after the run
    TMDL = "/lakehouse/default/Files/tmdl"

    url = (f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/git/"
           f"repositories/{REPO}/items")
    os.makedirs(TMDL, exist_ok=True)
    n = 0
    for folder in FOLDERS:
        r = requests.get(url, auth=("", PAT), params={
            "path": folder, "$format": "zip",
            "download": "true",
            "versionDescriptor.version": BRANCH,
            "api-version": "7.1"})
        r.raise_for_status()
        tmp = "/tmp/devops_tmdl"
        shutil.rmtree(tmp, ignore_errors=True)
        zipfile.ZipFile(io.BytesIO(r.content)).extractall(tmp)
        for root, dirs, _ in os.walk(tmp):
            for d in list(dirs):
                if d.endswith(".SemanticModel"):
                    dst = os.path.join(TMDL, d)
                    shutil.rmtree(dst, ignore_errors=True)
                    shutil.copytree(os.path.join(root, d), dst)
                    n += 1
        print(f"{folder}: done")
    print("semantic models landed:", n)

SEVERAL SOURCE WORKSPACES (D11, built 2026-10-07, wheel
0.6.0): run this cell once per workspace, each with that
workspace's ORG / PROJECT / REPO / FOLDERS — and give each
workspace its OWN subfolder by setting TMDL per run, e.g.
`TMDL = "/lakehouse/default/Files/tmdl/WS One"`. The engine
walks tmdl/ recursively; a model in a subfolder is named
"<subfolder>/<model>" everywhere downstream (delivery,
Collibra, blessings). Two workspaces sharing a bare report
name is caught MECHANICALLY: the preflight fails naming the
twins, and deliver() refuses to run until one is renamed or
removed. Flat tmdl/ (no subfolders) stays legal for a
single-workspace estate.

The cell pulls ONLY `.SemanticModel` folders and overwrites
each by name — re-run any time the repo moved; nothing else
in `Files/tmdl/` is touched. The first run: eyeball that the
landed folder names match the reports you meant.

## Step K — the key vault (once; Azure portal, NOT Fabric)

The key lives in an Azure Key Vault; the notebook reads it at
run time under YOUR login. Workspace access does NOT grant
vault access — a workspace colleague who opens or runs the
notebook fetches with their OWN login and gets denied unless
someone grants them a vault role. Record vault name, secret
name, and who granted access in `tenant_intake.md`.

If you cannot create Azure resources at work, hand steps 1-8
to the Azure admin and ask back for the vault name + secret
name + a "Key Vault Secrets User" role for you.

1. Go to portal.azure.com (the Azure portal, not Fabric).
2. Top search bar -> type **Key vaults** -> click **Key vaults**
   -> **+ Create**.
3. Basics tab: pick the Subscription and Resource group (ask
   the admin which to use if unsure), give the vault a name
   (globally unique, e.g. `<team>-ai01-kv`), pick the same
   Region as the Fabric capacity.
4. Access configuration tab: leave **Azure role-based access
   control** selected. **Review + create** -> **Create** ->
   wait -> **Go to resource**.
5. Grant yourself the right to WRITE secrets: left menu
   **Access control (IAM)** -> **+ Add** -> **Add role
   assignment** -> role **Key Vault Secrets Officer** ->
   Members: your account -> **Review + assign**. (Creating the
   vault does not by itself let you create secrets under RBAC.)
6. Store the key: left menu **Objects -> Secrets** ->
   **+ Generate/Import** -> Name: `ai01-openai-key` ->
   Secret value: paste the API key -> **Create**. This is the
   ONLY place the key is ever pasted.
7. Grant READ to everyone who will run the notebook (yourself
   included if you only did step 5's Officer role — Officer
   already includes read): **Access control (IAM)** ->
   **+ Add** -> **Add role assignment** -> role **Key Vault
   Secrets User** -> Members: the runner's account ->
   **Review + assign**.
8. To eyeball a stored secret later: **Objects -> Secrets** ->
   click the secret -> click the current version -> **Show
   Secret Value**. Only vault-role holders can do this.

## Step C — the notebook (fresh session, environment attached)

Cell 1 — the key. Two forms; the vault form is the standard
and the ONLY form allowed on a customer tenant.

Form 1 — vault read (customer tenants, always; fill in the
two quoted names from Step K):

    import os
    from notebookutils import credentials
    os.environ["OPENAI_API_KEY"] = credentials.getSecret(
        "https://<vault-name>.vault.azure.net/",
        "ai01-openai-key")
    print("key loaded:", bool(os.environ["OPENAI_API_KEY"]))

Form 2 — paste interim (RULED 2026-10-06, Sunny): allowed ONLY
when BOTH conditions hold, checked that day — (a) the runner is
the workspace's only member (Workspace settings -> Manage
access) and (b) Git integration is OFF (Workspace settings ->
Git integration). Either condition false -> Form 1 or stop.

    import os
    os.environ["OPENAI_API_KEY"] = "PASTE-KEY-HERE"
    print("key loaded:", bool(os.environ["OPENAI_API_KEY"]))

Paste the key between the quotes. THE SCRUB, same sitting: as
soon as the Step C run finishes, put "PASTE-KEY-HERE" back in
the cell and save the notebook before leaving it. The key
never appears in any other cell, file, or commit.

(Both forms print only True/False on purpose — notebook output
is saved with the notebook; never print the key itself.)

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
        dict_dir="/lakehouse/default/Files/02_dictionary",
        max_new=10)  # optional batch cap — see "Adding more
    #                  files later"; omit to take everything new

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

## Adding more files later (D12, built 2026-10-07, wheel 0.6.0)

DESCRIBED = DONE. deliver() keeps a content-hash ledger
(out/10_corpus_ledger.json): a file whose content is unchanged
since it was described is NEVER re-sent to the seat — its card
and terms are reused, free. Upload everything; the run plans
itself (no file names typed, ever).

BATCHES: add `max_new=N` to the deliver call to cap a run at N
new files (name order); the run ends saying what it did —
"10 described (25 already done), 37 remain" — and the next run
takes the next N. A new report tying to an already-described
file re-uses its text for free. `force=True` re-describes
everything (a deliberate full re-pay — rare).

The ledger records only what a run actually described, only
after the paid chain succeeded — a no-key degrade run records
nothing, and a changed file (new content hash) is described
again automatically.

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
key in any file or commit, and in a cell only under Cell 1
Form 2 (solo workspace + Git off), scrubbed the same sitting.
