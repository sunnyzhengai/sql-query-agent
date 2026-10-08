# work_wheel_runbook — deploying the engine on a customer Fabric tenant

Status: FINAL 2026-10-06, amended 2026-10-08 (succinct rewrite +
first-customer-tenant fixes). Every cell below is proven on a
real tenant.

THE LAWS: metadata boundary (the LLM sees SQL text +
dictionaries, never query results) · the wall (work SQL and
work outputs never come back to the repo) · one wheel (ONE
sqldesc wheel in the environment) · blessed-only (no unblessed
name reaches Collibra).

## Prereqs (pack before the first session)

- [ ] Newest `ai01_sqldesc-*.whl` from wheel/ (never two versions)
- [ ] `tools/csv_to_json.py` (rides with the wheel)
- [ ] The five extraction queries in dictionary_extraction/
- [ ] The LLM API key, stored in Azure Key Vault (Step K)
- [ ] DevOps org/project/repo/branch of the TMDL (Step T)
- [ ] Which procs/views go in (Step S)

## Step 0 — create the Fabric items (once)

Do NOT mirror any other tenant's folders — the engine needs
only the Step B folders. Record every name/id in
`tenant_intake.md` section 1.

1. Fabric portal -> your workspace -> **+ New item** ->
   **Lakehouse** -> name it -> Create.
2. **+ New item** -> **Environment** -> name it -> Create.
3. **+ New item** -> **Notebook** -> name it; toolbar: set
   **Environment** to yours; Explorer: **Add data items ->
   your lakehouse** (becomes `/lakehouse/default/...`).
4. Workspace/lakehouse ids are in the browser URL with the
   lakehouse open: `.../groups/<ws-id>/lakehouses/<lh-id>`.

## Step A — the environment (once)

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

## Step B — the lakehouse folders (once)

    Files/01_sql_input/      <- work SQL files (*.sql), Step S
    Files/02_dictionary/     <- the four extraction json, Step E
    Files/tmdl/              <- *.SemanticModel folders, Step T
    Files/out/               <- the run writes here

## Step T — the TMDL (`*.SemanticModel` folders)

The engine reads TMDL files from the workspace's Git repo, not
published items. Git-connected workspaces show a **Source
control** button and a **Git status** column (prod often
isn't connected — use its git-connected test twin). Only
**Synced** items are in the repo; commit Uncommitted ones via
Source control. Find the repo: **Workspace settings -> Git
integration** -> copy org/project/repo/branch into the intake.

Pull with the notebook cell (repeatable; manual alternative:
dev.azure.com -> Repos -> Files -> hover the `.SemanticModel`
folder -> ... -> Download as Zip -> unzip -> upload to tmdl/).

Needs a DevOps PAT: dev.azure.com -> user-settings icon ->
**Personal access tokens** -> **+ New Token** -> scope **Code:
Read**, short expiry -> copy once. A PAT is a password: vault,
or Cell 1 Form 2's paste conditions and same-sitting scrub.

    import io, os, shutil, zipfile, requests

    ORG, PROJECT, REPO = "<org>", "<project>", "<repo>"
    BRANCH = "main"
    FOLDERS = ["<repo folder>", "<another>"]  # or ["/"] = whole repo
    PAT = "PASTE-PAT-HERE"  # scrub after the run
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

SEVERAL SOURCE WORKSPACES: run the cell once per workspace,
each into its own subfolder (`TMDL = ".../tmdl/WS One"`). The
engine walks tmdl/ recursively; subfolder models are named
"<subfolder>/<model>" downstream. Bare-name twins across
workspaces fail the preflight by name until resolved. Flat
tmdl/ stays legal for one workspace. Re-run any time — the
cell overwrites by name and touches nothing else.

## Step E — the dictionary (four json files)

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

## Step S — the SQL input files

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
   UTF-16 FILES ALREADY UPLOADED (the 0xff error above):
   convert in place with this cell, then re-run deliver —
   safe to re-run, plain utf-8 files are skipped:

    import codecs, os
    folder = "/lakehouse/default/Files/01_sql_input/"
    fixed = 0
    for n in os.listdir(folder):
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
            continue
        with open(folder + n, "w", encoding="utf-8") as f:
            f.write(text)
        fixed += 1
    print("converted:", fixed, "files")
3. CLEAN THE NAMES BEFORE THE FIRST RUN — the file name minus
   `.sql` is the identity everywhere downstream (outputs,
   ledger, Collibra), and renaming later makes the ledger
   forget what was done. Generate Scripts names files
   `Schema.Object.ObjectType.sql`; strip to `Object.sql`:

    import os
    folder = "/lakehouse/default/Files/01_sql_input/"
    names = [n for n in os.listdir(folder) if n.endswith(".sql")]
    def clean(n):
        core = n[:-4]
        for t in (".StoredProcedure", ".View"):
            if core.endswith(t):
                core = core[: -len(t)]
        return core.split(".")[-1] + ".sql"
    m = {n: clean(n) for n in names}
    t = list(m.values())
    dups = sorted({x for x in t if t.count(x) > 1})
    assert not dups, f"collisions: {dups}"  # keep schema prefix
    #                                          for just these
    for old, new in m.items():
        if old != new:
            os.rename(folder + old, folder + new)
    print("renamed", sum(o != n for o, n in m.items()),
          "of", len(names))

## Step K — the key vault (once; Azure portal, NOT Fabric)

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

## Step C — the run (fresh session, environment attached)

Cell 1 — the key. Vault form, the only form on a customer
tenant:

    import os
    from notebookutils import credentials
    os.environ["OPENAI_API_KEY"] = credentials.getSecret(
        "https://<vault-name>.vault.azure.net/",
        "ai01-openai-key")
    print("key loaded:", bool(os.environ["OPENAI_API_KEY"]))

Form 2 — paste interim (RULED 2026-10-06): allowed ONLY if,
checked that day, (a) the runner is the workspace's only
member AND (b) Git integration is OFF. Paste between the
quotes; THE SCRUB: the moment the run finishes, put
"PASTE-KEY-HERE" back and save the notebook. Never print the
key.

    import os
    os.environ["OPENAI_API_KEY"] = "PASTE-KEY-HERE"
    print("key loaded:", bool(os.environ["OPENAI_API_KEY"]))

Cell 2 — the preflight. Must end `/ 0 fail`; every FAIL line
names its own fix. (Work-side expected: no names asset — the
ruled fallback; blessing registry starts empty.)

    import sqldesc_cli
    sqldesc_cli.preflight(
        "/lakehouse/default/Files/tmdl",
        "/lakehouse/default/Files/01_sql_input",
        "/lakehouse/default/Files/out",
        dict_dir="/lakehouse/default/Files/02_dictionary")

Cell 2b — THE SWEEP (wheel 0.6.1+; run before the FIRST paid
run on any new corpus, and again after adding files). A free
parse-only pass: finds EVERY T-SQL construct the engine does
not map yet, across all files at once, zero LLM calls. Rule
them in as one batch (one wheel update), then pay once —
instead of a paid run stopping on each surprise.

    census = sqldesc_cli.sweep(
        "/lakehouse/default/Files/01_sql_input",
        "/lakehouse/default/Files/out",
        dict_dir="/lakehouse/default/Files/02_dictionary")

Ends "N file(s), M with unmapped constructs, K distinct
construct(s)" and writes out/11_construct_census.json. K = 0:
go to Cell 3. K > 0: send the census output home; the
constructs get ruled into the engine, a new wheel lands, then
Cell 3. deliver() still stops hard on an unmapped construct —
the sweep exists so it never has to.

Cell 3 — the run. Quiet minutes = paid calls working; deliver
re-runs the preflight and refuses on any failure.

    sqldesc_cli.deliver(
        "/lakehouse/default/Files/tmdl",
        "/lakehouse/default/Files/01_sql_input",
        "/lakehouse/default/Files/out",
        dict_dir="/lakehouse/default/Files/02_dictionary",
        max_new=10)  # batch cap; omit to take everything new

Cell 4 — the eye:

    print(open("/lakehouse/default/Files/out/"
               "08_report_descriptions.txt").read()[:4000])

## Step D — gap-check and bless (the data owner's hand)

1. Read the official txt; check cards + technical definitions
   against the SQL the reviewer knows.
2. Bless keeper names:

    import business_terms as bt
    bt.bless("/lakehouse/default/Files/out",
             "/lakehouse/default/Files/out/07",
             "<node_id>", "<report name>",
             "RULED <date> (<the blesser>): <the ruling>")

3. Collibra reads `Files/out/ai_delivery.json` — her publish
   notebook filters blessed itself.

## Later runs — DESCRIBED = DONE

deliver() keeps a content-hash ledger
(out/10_corpus_ledger.json): an unchanged described file is
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
`<out>/07/07_live_checkpoint.json` if present, keep the
blessing registry, re-run the chain clean in the SAME session.

## What never happens here

No work file, output, or blessing comes back to the repo. No
pytest at work (the preflight is the shipped check). No second
sqldesc wheel. No key in any file or commit — in a cell only
under Form 2's conditions, scrubbed the same sitting.
