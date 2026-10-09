# work_wheel_runbook — deploying the engine on a customer Fabric tenant

Status: FINAL 2026-10-06, amended 2026-10-08 (succinct rewrite +
first-customer-tenant fixes; THE NAMING LAW — setup steps are
lettered, pipeline steps are numbered, a step's number is its
folder's number; tmdl/ -> 03_tmdl, out/ -> 04_run, effective
now).

THE LAWS: metadata boundary (the LLM sees SQL text +
dictionaries, never query results) · the wall (work SQL and
work outputs never come back to the repo) · one wheel (ONE
sqldesc wheel in the environment) · blessed-only (no unblessed
name reaches Collibra).

WHEEL 0.7.0 (ruled + SHIPPED 2026-10-08, the step table in
10_work_wheel_data_contract.md): `<step>_output` file names,
the BUILD/DESCRIBE cell split with the 13-stamp staleness
guard, the key as a blocking preflight row (no degrade, ever),
and the delivery = PAID FILES ONLY with files_described /
files_waiting per report.
UPGRADING A 0.6.x TENANT: publish the new wheel (one wheel,
fresh session) -> rename the folders (Setup C) -> KEEP
04_run/10_corpus_ledger.json and any blessing registry (the
migration reads honor the old names; nothing re-pays) ->
delete the old 05/ 06/ 07/ folders and old output files ->
run the notebook from RUN 2.

## Prereqs (pack before the first session)

- [ ] Newest `ai01_sqldesc-*.whl` from wheel/ (never two versions)
- [ ] `tools/csv_to_json.py` (rides with the wheel)
- [ ] The five extraction queries in dictionary_extraction/
- [ ] The LLM API key, stored in Azure Key Vault (Setup D)
- [ ] DevOps org/project/repo/branch of the TMDL (Step 03)
- [ ] Which procs/views go in (Step 01)

## Setup A — create the Fabric items (once)

Do NOT mirror any other tenant's folders — the engine needs
only the Setup C folders. Record every name/id in
`tenant_intake.md` section 1.

1. Fabric portal -> your workspace -> **+ New item** ->
   **Lakehouse** -> name it -> Create.
2. **+ New item** -> **Environment** -> name it -> Create.
3. **+ New item** -> **Notebook** -> name it; toolbar: set
   **Environment** to yours; Explorer: **Add data items ->
   your lakehouse** (becomes `/lakehouse/default/...`).
4. Workspace/lakehouse ids are in the browser URL with the
   lakehouse open: `.../groups/<ws-id>/lakehouses/<lh-id>`.

## Setup B — the environment (once)

1. Open the ENVIRONMENT item.
2. Libraries -> PUBLIC libraries -> add `openai` pinned 3.19.2
   (the parity pin). Public install resolves dependencies.
   TENANTS WITH EXTERNAL REPOSITORIES ONLY (no public
   libraries): those installs bring ONE package, no
   dependencies. Add THREE, pinned: `openai 3.19.2`,
   `httpx 0.28.1`, `httpcore 1.0.9`. (openai's httpx2 comes
   along; plain httpx does not; the runtime carries the
   rest.) If unsure, probe in a notebook cell —
   `importlib.import_module` over: httpx, httpx2, httpcore,
   h11, anyio, sniffio, idna, certifi, jiter, pydantic,
   typing_extensions — add every miss, ALL IN ONE PUBLISH.
3. Libraries -> CUSTOM libraries -> upload the wheel. One
   sqldesc wheel, ever.
4. **Publish all** -> wait for publish **Success** (10-20 min;
   a library row's own "Success" is only the upload) -> THEN
   stop any open notebook session and start fresh. A session
   started while the publish bakes is stale too.

## Setup C — the lakehouse folders (once)

    Files/01_sql_input/      <- work SQL files (*.sql), Step 01
    Files/02_dictionary/     <- the four extraction json, Step 02
    Files/03_tmdl/           <- *.SemanticModel folders, Step 03
    Files/04_run/            <- the engine writes here (Step 04)

The split: 01–03 are YOURS to fill; 04_run is the ENGINE's.
A from-scratch rerun = delete 04_run, inputs untouched.
(RENAMED 2026-10-08 from tmdl/ and out/ — on an existing
tenant, rename the two folders in the lakehouse and use the
new paths below; the engine takes paths as parameters, any
wheel.)

## Setup D — the key vault (once; Azure portal, NOT Fabric)

The notebook reads the key at run time under YOUR login;
workspace access does not grant vault access. Record vault
name, secret name, who granted what in `tenant_intake.md`. No
Azure rights at work? Hand steps 1-6 to the Azure admin; ask
back for vault name + secret name + a Secrets User role.

1. portal.azure.com -> search **Key vaults** -> **+ Create**.
2. Basics: Subscription + Resource group (ask the admin),
   globally-unique name (e.g. `<team>-ai01-kv`), same Region
   as the Fabric capacity.
3. Access configuration: keep **Azure role-based access
   control** -> **Review + create** -> **Create** -> **Go to
   resource**.
4. Let yourself WRITE secrets: **Access control (IAM)** ->
   **+ Add -> Add role assignment** -> **Key Vault Secrets
   Officer** -> your account -> **Review + assign**.
5. Store the key: **Objects -> Secrets -> + Generate/Import**
   -> Name `ai01-openai-key` -> Value: paste the key ->
   **Create**. The ONLY place the key is ever pasted.
6. Grant READ to every runner: **IAM -> + Add -> Add role
   assignment** -> **Key Vault Secrets User** -> the runner
   -> **Review + assign**. (Officer already includes read.)
7. To eyeball later: **Objects -> Secrets** -> the secret ->
   current version -> **Show Secret Value**.

## Step 01 — the SQL input files (fills 01_sql_input)

1. SSMS: right-click the database -> **Tasks -> Generate
   Scripts** -> **Select specific database objects** -> tick
   the procs/views -> Output: **Save scripts to a specific
   location** + **One script file per object** -> pick the
   mapped laptop drive -> AND set **Save as: ANSI text**
   (or UTF-8 where offered) — the default "Unicode" is
   UTF-16, which the engine refuses (found 2026-10-07:
   deliver dies on `UnicodeDecodeError ... byte 0xff in
   position 0`; the preflight only counts files, so it
   passes) -> Finish.
2. Upload the `.sql` files to `Files/01_sql_input/`
   (multi-select works; names MUST end `.sql` — the sweep
   reads `*.sql` only).
   NON-UTF-8 FILES ALREADY UPLOADED (`0xff in position 0` =
   UTF-16; `0xa0`/other mid-file = ANSI with special chars —
   both seen on the first tenant): convert in place with this
   cell, then re-run — safe to re-run, clean files skipped:

    import codecs, os
    folder = "/lakehouse/default/Files/01_sql_input/"
    fixed = 0
    for n in sorted(os.listdir(folder)):
        if not n.endswith(".sql"):
            continue
        with open(folder + n, "rb") as f:
            raw = f.read()
        if raw.startswith(codecs.BOM_UTF16_LE) \
                or raw.startswith(codecs.BOM_UTF16_BE):
            text = raw.decode("utf-16")
        elif raw.startswith(codecs.BOM_UTF8):
            text = raw.decode("utf-8-sig")
        else:
            try:
                raw.decode("utf-8")
                continue                    # already clean
            except UnicodeDecodeError:
                text = raw.decode("cp1252")  # Windows ANSI
        with open(folder + n, "w", encoding="utf-8") as f:
            f.write(text)
        fixed += 1
    print("converted:", fixed, "files")
3. CLEAN THE NAMES BEFORE A FILE'S FIRST RUN — the file name
   minus `.sql` is the identity everywhere downstream
   (outputs, ledger, Collibra), and renaming later makes the
   ledger forget what was done. Generate Scripts names files
   `Schema.Object.ObjectType.sql`; this cell strips the
   schema prefix and the ObjectType tail, keeps dots INSIDE
   the object name (the 2026-10-07 `V2.1` lesson), and only
   touches fresh Generate Scripts output — SAFE TO RE-RUN
   after each new export, already-clean files untouched:

    import os
    folder = "/lakehouse/default/Files/01_sql_input/"
    TAILS = (".StoredProcedure.sql", ".View.sql")
    renamed = 0
    for n in sorted(os.listdir(folder)):
        tail = next((t for t in TAILS if n.endswith(t)), None)
        if tail is None:
            continue  # not fresh wizard output — leave alone
        core = n[: -len(tail)]
        new = (core.split(".", 1)[1] if "." in core
               else core) + ".sql"
        assert not os.path.exists(folder + new), \
            f"would collide: {n} -> {new}"
        os.rename(folder + n, folder + new)
        renamed += 1
    print("renamed", renamed, "file(s)")

## Step 02 — the dictionary (fills 02_dictionary)

Run in SSMS against the tenant's Clarity dictionary tables
(metadata only, unscoped). FIRST, once per SSMS session (the
setting does not survive non-persistent remote desktops):
Tools -> Options -> Query Results -> SQL Server -> Results to
Grid -> check **Include column headers when copying or saving
results**.

On a Citrix/remote SSMS, save to the mapped laptop drive
(**This PC -> "C on <your laptop>"**) — the remote profile's
own folders are invisible to your laptop.

1. Run dict_extract_table / _column / _join / _value .sql ->
   save each grid as `<same name>.csv`.
2. The ZC universe: run `dict_extract_value_generator.sql`.
   Its OUTPUT IS SQL, not data — copy the whole result column
   into a new query window, delete the trailing `UNION ALL`
   on the last line, EYEBALL it, run it. Save the result as
   `dict_extract_value_zc.csv` (too long for one run? save
   batches `_zc_1.csv`, `_zc_2.csv`, ... — the merge cell
   takes them all, headers or not).
3. Upload all csv files + `tools/csv_to_json.py` to
   `Files/02_dictionary/`.
4. In the notebook, merge + convert (run ONCE — a rerun
   doubles the zc rows):

    import csv, glob, sys

    folder = "/lakehouse/default/Files/02_dictionary/"
    def rd(p):
        with open(p, newline="", encoding="utf-8-sig") as f:
            return list(csv.reader(f))
    value = rd(folder + "dict_extract_value.csv")
    added = 0
    for p in sorted(glob.glob(folder + "dict_extract_value_zc*.csv")):
        rows = rd(p)
        if rows and rows[0] == value[0]:
            rows = rows[1:]
        assert all(len(r) == 3 for r in rows), f"bad rows in {p}"
        value += rows
        added += len(rows)
    with open(folder + "dict_extract_value.csv", "w",
              newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(value)
    print("zc rows folded in:", added)
    sys.path.append(folder)
    import csv_to_json
    csv_to_json.convert(folder, folder)

The four json files land next to the csvs; the value row count
printed by convert must equal value + zc.

## Step 03 — the TMDL (fills 03_tmdl)

The engine reads TMDL files from the workspace's Git repo, not
published items. Git-connected workspaces show a **Source
control** button and a **Git status** column (prod often
isn't connected — use its git-connected test twin). Only
**Synced** items are in the repo; commit Uncommitted ones via
Source control. Find the repo: **Workspace settings -> Git
integration** -> copy org/project/repo/branch into the intake.

Pull with the notebook cell (repeatable; manual alternative:
dev.azure.com -> Repos -> Files -> hover the `.SemanticModel`
folder -> ... -> Download as Zip -> unzip -> upload to
03_tmdl/).

Needs a DevOps PAT: dev.azure.com -> user-settings icon ->
**Personal access tokens** -> **+ New Token** -> scope **Code:
Read**, short expiry -> copy once. A PAT is a password: vault,
or Step 04 Cell 1 Form 2's paste conditions and same-sitting
scrub.

    import io, os, shutil, zipfile, requests

    ORG, PROJECT, REPO = "<org>", "<project>", "<repo>"
    BRANCH = "main"
    FOLDERS = ["<repo folder>", "<another>"]  # or ["/"] = whole repo
    PAT = "PASTE-PAT-HERE"  # scrub after the run
    TMDL = "/lakehouse/default/Files/03_tmdl"

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

SEVERAL SOURCE WORKSPACES: run the cell once per workspace,
each into its own subfolder (`TMDL = ".../03_tmdl/WS One"`).
The engine walks 03_tmdl/ recursively; subfolder models are
named "<subfolder>/<model>" downstream. Bare-name twins across
workspaces fail the preflight by name until resolved. Flat
03_tmdl/ stays legal for one workspace. Re-run any time — the
cell overwrites by name and touches nothing else.

## Step 04 — the run (fresh session, environment attached; writes 04_run)

THE NOTEBOOK IS A VERSIONED FILE — do not hand-edit cells:
`notebook_work_wheel.py`, shipped beside this runbook (SETUP
A-E once, RUN 1-6 per batch, BLESS at the end). Push it to the
Fabric notebook item with one command from the home repo's
sync tool (browser sign-in; lakehouse/environment attachments
preserved; ALL code cells replaced):

    python3.11 sync_notebook.py \
        --workspace <workspace-id> --notebook <notebook-item-id> \
        --source notebook_work_wheel.py

THE SEQUENCE LAW (ruled 2026-10-08): cells run in order; any
FAIL stops the session — fix it, re-run that cell, only then
proceed. The key is a blocking row like every other.

RUN 1 — the key (vault form; Form 2 paste-interim rules stand
    as ruled 2026-10-06, scrub the same sitting).
RUN 2 — the preflight: must end `/ 0 fail`.
RUN 3 — the sweep (free): K > 0 -> send
    `04_run/11_construct_census_output.json` home, a new wheel
    rules the constructs in, then continue.
RUN 4 — BUILD (free, whole corpus): graph + technical + report
    links + the 13 stamp. Run when the input folders change.
RUN 5 — DESCRIBE (paid): the next `max_new` files -> cards,
    terms, the ledger, the delivery. Refuses a stale build:
    "run the build cell first" = re-run RUN 4. Repeat RUN 5
    until "0 remain".
RUN 6 — the eye: prints `04_run/12_ai_delivery_output.txt`.
    Delivery entries are PAID FILES ONLY; each report lists
    files_described / files_waiting — the publish notebook
    skips any report still waiting.

## Step 07 — gap-check and bless (the data owner's hand)

1. Read the official txt; check cards + technical definitions
   against the SQL the reviewer knows.
2. Bless keeper names:

    import business_terms as bt
    bt.bless("/lakehouse/default/Files/04_run",
             "/lakehouse/default/Files/04_run/07_business_descriptions",
             "<node_id>", "<report name>",
             "RULED <date> (<the blesser>): <the ruling>")

3. Collibra reads `Files/04_run/12_ai_delivery_output.json` — her
   publish notebook filters blessed itself.

## Later runs — DESCRIBED = DONE

deliver() keeps a content-hash ledger
(04_run/10_corpus_ledger_output.json; a pre-rename tenant's old-name ledger is honored — the migration read): an unchanged described file is
never re-sent — its text is reused free; a changed file is
described again automatically. Upload everything; the run
plans itself. `max_new=N` caps a run at N new files (name
order) and reports "N described (M already done), K remain".
`force=True` re-describes everything — a deliberate full
re-pay, rare. The ledger records only what a paid run actually
described.

## If a run was canceled or the seat broke mid-run

Failed nodes stay checkpointed as floors and a resume would
skip them. After fixing the seat: delete
`<04_run>/07_business_descriptions/07_business_descriptions_checkpoint_output.json` if present, keep the
blessing registry, re-run the chain clean in the SAME session.

## What never happens here

No work file, output, or blessing comes back to the repo. No
pytest at work (the preflight is the shipped check). No second
sqldesc wheel. No key in any file or commit — in a cell only
under Form 2's conditions, scrubbed the same sitting.
