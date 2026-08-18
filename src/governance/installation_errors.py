"""The installation-error knowledge base — one home for error signatures.

Each entry matches the ops_installation_errors contract exactly and powers
the agent's /troubleshoot command (rule 5: supportable at a distance).
Seeded into Delta by 100_install; never author signatures anywhere else.

When a new failure mode is diagnosed, add it here with the signature
(distinctive substring), root cause, fix, and prevention — the next
customer's agent explains it without a support ticket.
"""

ERROR_SEEDS = [
    {
        "error_signature": "Invalid object name",
        "error_category": "missing_source_object",
        "root_cause": (
            "SQL references a table/view that does not exist in the target "
            "database. Two usual causes: (1) a setup/seed script was "
            "PARTIALLY applied — without GO separators, the first failed "
            "statement silently kills every statement after it in the same "
            "batch, so the script 'ran' but the database is incomplete; "
            "(2) the object list was built from read-lineage only and "
            "missed write-target tables (INSERT INTO/UPDATE/MERGE)."
        ),
        "fix": (
            "Re-run the seed scripts top to bottom (they are idempotent), "
            "then run the VERIFICATION query at the end of "
            "seed_demo_tables_supplement.sql — it lists every referenced "
            "object still missing; expect an empty result before retrying."
        ),
        "prevention": (
            "Author seed scripts with GO after every statement (one failure "
            "can never silently kill the rest) and end them with a "
            "verification query that names anything missing."
        ),
        "first_seen": "2026-08-18",
    },
    {
        "error_signature": "Invalid column name",
        "error_category": "missing_source_column",
        "root_cause": (
            "SQL references a column that exists in the code but not in "
            "the table — when tables are stubbed or migrated from a data "
            "dictionary, the dictionary lags the code (428 such columns "
            "across 27 tables at first demo-seed execution)."
        ),
        "fix": (
            "Run seed_demo_columns_patch.sql (idempotent ALTER TABLE ADD "
            "per column), then its verification query — expect an empty "
            "result before retrying."
        ),
        "prevention": (
            "Derive stub columns from the CODE's references (alias-scoped "
            "scan), not from the dictionary alone; keep the verification "
            "tail in every seed."
        ),
        "first_seen": "2026-08-18",
    },
    {
        "error_signature": "Cannot find either column \"dbo\" or the user-defined function",
        "error_category": "missing_function",
        "root_cause": (
            "A stored procedure calls a scalar UDF (e.g. dbo.fn_parse_date) "
            "that was never created — table seeds cover tables, not "
            "functions, and nothing exercises functions until a proc "
            "actually EXECUTEs (extraction only reads definitions)."
        ),
        "fix": "Run seed_demo_functions.sql (or create the named function), then retry.",
        "prevention": (
            "Enumerate function dependencies alongside tables when seeding "
            "a source database; execute one proc end-to-end as the seed's "
            "acceptance check."
        ),
        "first_seen": "2026-08-18",
    },
    {
        "error_signature": "PyToIPynbFailure",
        "error_category": "notebook_format",
        "root_cause": (
            "A notebook-content.py in git is not convertible by Fabric's "
            "py-to-ipynb importer (dangling '# CELL' marker at EOF or a "
            "malformed '# META' JSON block). One bad item blocks the whole "
            "git update batch for the workspace."
        ),
        "fix": (
            "Pull the latest release (the repo enforces Fabric format "
            "integrity in CI), refresh Source control, and Update all again."
        ),
        "prevention": (
            "Notebook contract plank: tests/test_notebook_contract.py "
            "validates header, META JSON, and cell-marker structure on "
            "every commit."
        ),
        "first_seen": "2026-08-18",
    },
    {
        "error_signature": "Additional text encountered after finished reading JSON",
        "error_category": "notebook_format",
        "root_cause": (
            "Inner message of PyToIPynbFailure: Fabric's converter hit "
            "unexpected trailing content while parsing a notebook's "
            "structure (usually a dangling '# CELL' marker at end of file)."
        ),
        "fix": (
            "Same as PyToIPynbFailure: pull the latest release and re-run "
            "the Source control update."
        ),
        "prevention": "Covered by the notebook-format CI guard.",
        "first_seen": "2026-08-18",
    },

    {
        "error_signature": "This property must be set before runtime is initialized",
        "error_category": "pythonnet_initialization",
        "root_cause": "%pip install restarts the kernel, breaking pythonnet CLR init.",
        "fix": "Use Fabric Environment with pre-installed packages instead of %pip install.",
        "prevention": "Never use %pip install in notebooks that use pythonnet/ScriptDom.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "No module named 'Microsoft.SqlServer'",
        "error_category": "dll_not_found",
        "root_cause": "ScriptDom DLL missing from libs/ folder or wrong filename.",
        "fix": (
            "Upload Microsoft.SqlServer.TransactSql.ScriptDom.dll to Files/sql-query-agent/libs/. Use "
            "lib/netstandard2.0/ version from NuGet."
        ),
        "prevention": "Verify DLL path during deployment.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "Could not load file or assembly",
        "error_category": "dll_load_failure",
        "root_cause": "Wrong DLL version (e.g., net462 instead of netstandard2.0) or corrupted file.",
        "fix": "Re-download from NuGet, use lib/netstandard2.0/ version only.",
        "prevention": "Always use netstandard2.0 build.",
        "first_seen": "2026-07-26",
    },
    {
        "error_signature": "Config not found at",
        "error_category": "config_not_found",
        "root_cause": "org_config.yaml is missing or in the wrong location.",
        "fix": "Upload org_config.yaml to Files/sql-query-agent/ (NOT in a config/ subfolder).",
        "prevention": "Verify file path during 100_install.",
        "first_seen": "2026-07-30",
    },
    {
        "error_signature": "Bad Request.*400.*csv",
        "error_category": "spark_csv_read_failure",
        "root_cause": "Spark CSV reader fails with OneLake HTTP path in some Fabric configurations.",
        "fix": "Add file:// prefix to CSV paths: spark.read.csv('file://' + path).",
        "prevention": "Use file:// prefix for all local CSV reads.",
        "first_seen": "2026-07-31",
    },
    {
        "error_signature": "CapacityLimitExceeded",
        "error_category": "capacity_throttled",
        "root_cause": (
            "Sustained usage above the capacity SKU triggered Fabric smoothing/throttling — "
            "interactive operations (agent queries, publishes) are rejected until the "
            "carried-forward overage burns down. Agent Q&A is CU-intensive on small SKUs."
        ),
        "fix": (
            "Fastest: pause then resume the Fabric capacity in the Azure portal — pausing "
            "settles the smoothed debt immediately. Otherwise stop idle Spark sessions and "
            "wait for the overage to burn down (minutes to hours). For sustained agent "
            "testing, temporarily resize to a larger SKU (e.g. F2 -> F4) for the session."
        ),
        "prevention": (
            "Batch heavy operations with gaps on small SKUs; stop Spark sessions when done; "
            "size capacity to the workload during test sessions."
        ),
        "first_seen": "2026-08-04",
    },
    {
        "error_signature": "TooManyRequestsForCapacity.*430",
        "error_category": "capacity_limit",
        "root_cause": "F2 capacity only supports one Spark session at a time.",
        "fix": (
            "Wait 2-3 minutes for the previous session to release, then retry. Check Monitoring hub for "
            "active sessions."
        ),
        "prevention": "Cancel unused sessions. Consider F4 capacity for concurrent workloads.",
        "first_seen": "2026-07-30",
    },
    {
        "error_signature": "TABLE_OR_VIEW_NOT_FOUND",
        "error_category": "table_not_found",
        "root_cause": "Delta table doesn't exist yet, or org_config.yaml has old table names.",
        "fix": (
            "Run 100_install first to create all tables. Verify org_config.yaml uses domain-prefixed "
            "names (input_sql_sources, not sql_sources)."
        ),
        "prevention": "Always run 100_install before other notebooks.",
        "first_seen": "2026-07-30",
    },
    {
        "error_signature": "User Aad Token is expired",
        "error_category": "token_expired",
        "root_cause": (
            "AAD token expires after ~1 hour. mssparkutils caches the token and won't refresh within "
            "the same session."
        ),
        "fix": (
            "Restart the kernel and re-run. For long batch runs, results are saved incrementally so you "
            "pick up where you left off."
        ),
        "prevention": "Design batch operations to save progress incrementally.",
        "first_seen": "2026-07-30",
    },
    {
        "error_signature": "Git_GitProviderCredentialsNotAuthorizedError",
        "error_category": "git_auth_failure",
        "root_cause": "Fabric GitHub OAuth doesn't have write access to the repository.",
        "fix": (
            "Revoke and re-authorize: GitHub Settings -> Applications -> find Microsoft Fabric -> grant "
            "repo access. Or use a GitHub Personal Access Token with repo scope."
        ),
        "prevention": "Verify Git write access before connecting workspace.",
        "first_seen": "2026-07-31",
    },
    {
        "error_signature": "duplicate filenames",
        "error_category": "duplicate_sql_files",
        "root_cause": (
            "SQL files from different schemas have the same filename, causing overwrites in flat upload "
            "folder."
        ),
        "fix": (
            "Add a prefix to distinguish files from different schemas (e.g., RPT_USP_xxx.sql, "
            "ETL_USP_xxx.sql). Or use subfolders."
        ),
        "prevention": "Check for duplicate filenames before uploading.",
        "first_seen": "2026-07-30",
    },
    {
        "error_signature": "duplicate metric identities",
        "error_category": "duplicate_metric_identity",
        "root_cause": (
            "Two or more SQL files define the same [schema].[object]. The installer blocks because each "
            "metric must have exactly one certified definition."
        ),
        "fix": (
            "Remove or rename the extra file(s) listed in the installer output. If both versions are "
            "genuinely needed, they are different metrics and need different object names."
        ),
        "prevention": "Ensure each [schema].[procedure or view] is defined by exactly one file before uploading.",
        "first_seen": "2026-08-02",
    },
    {
        "error_signature": "Cannot import 'src' package",
        "error_category": "wheel_not_installed",
        "root_cause": "The .whl file is not uploaded to the Fabric Environment, or Environment not published.",
        "fix": "Upload the sql_query_agent wheel to Environment -> Custom libraries -> Publish.",
        "prevention": "Verify Environment has .whl and is published before running notebooks.",
        "first_seen": "2026-07-31",
    },
    {
        "error_signature": "No module named 'src.",
        "error_category": "stale_wheel_version",
        "root_cause": (
            "The Spark session is running an older product wheel: either an old .whl is still in the "
            "Environment, the notebook is attached to a different Environment, or the session started "
            "before the new wheel finished publishing. (src imports but a newer submodule is missing.)"
        ),
        "fix": (
            "Verify the Environment's Custom libraries show exactly one sql_query_agent wheel at the "
            "expected version and status is Published; verify the notebook's Environment dropdown "
            "selects it; then STOP the Spark session and re-run — sessions bind the Environment at "
            "start. Check with: importlib.metadata.version('sql-query-agent')."
        ),
        "prevention": (
            "After every wheel update: remove the old wheel, publish, confirm the version, and restart "
            "any running sessions before re-running notebooks."
        ),
        "first_seen": "2026-08-02",
    },
    {
        "error_signature": "A schema mismatch detected when writing to the Delta table",
        "error_category": "delta_schema_mismatch_on_upgrade",
        "root_cause": (
            "A product upgrade evolved a table contract (e.g. 1.2.2 added metricId to "
            "graph_canonical), but the existing Delta table still has the old schema and "
            "the notebook write lacked overwriteSchema."
        ),
        "fix": (
            "Snapshot tables are fully regenerated each run, so schema follows the contract: "
            "add .option('overwriteSchema', 'true') to the overwrite write and re-run the "
            "notebook (fixed in all pipeline notebooks as of 1.2.2)."
        ),
        "prevention": (
            "Every mode('overwrite') write of a registry-schema'd table carries "
            "overwriteSchema so contract evolution applies cleanly on upgrade."
        ),
        "first_seen": "2026-08-04",
    },
    {
        "error_signature": "Set as default lakehouse.*grayed out",
        "error_category": "lakehouse_default_issue",
        "root_cause": "Lakehouse moved from another workspace retains stale metadata.",
        "fix": "Create a new Lakehouse in the current workspace instead of moving one from another workspace.",
        "prevention": "Always create Lakehouses in the target workspace.",
        "first_seen": "2026-07-31",
    },
]
