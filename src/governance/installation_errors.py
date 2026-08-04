"""The installation-error knowledge base — one home for error signatures.

Each entry matches the ops_installation_errors contract exactly and powers
the agent's /troubleshoot command (rule 5: supportable at a distance).
Seeded into Delta by 01_install; never author signatures anywhere else.

When a new failure mode is diagnosed, add it here with the signature
(distinctive substring), root cause, fix, and prevention — the next
customer's agent explains it without a support ticket.
"""

ERROR_SEEDS = [
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
        "prevention": "Verify file path during 01_install.",
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
            "Run 01_install first to create all tables. Verify org_config.yaml uses domain-prefixed "
            "names (input_sql_sources, not sql_sources)."
        ),
        "prevention": "Always run 01_install before other notebooks.",
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
        "error_signature": "Set as default lakehouse.*grayed out",
        "error_category": "lakehouse_default_issue",
        "root_cause": "Lakehouse moved from another workspace retains stale metadata.",
        "fix": "Create a new Lakehouse in the current workspace instead of moving one from another workspace.",
        "prevention": "Always create Lakehouses in the target workspace.",
        "first_seen": "2026-07-31",
    },
]
