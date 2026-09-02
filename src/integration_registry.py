"""INTEGRATION_REGISTRY — the tool/connector landscape as data.

The TABLE_REGISTRY pattern applied to integrations (handoff 2026-08-16):
one record per connector between the product core and an external tool, single
source of truth for what ships, what's next, and what's on watch. The
generated projection is docs/architecture/INTEGRATION_MAP.md
(scripts/generate_docs.py); a freshness test pins it. This registry
supersedes the ROADMAP connector table (2026-08-07) and the
REFERENCE_ARCHITECTURE tier table as source of truth.

Explicitly rejected alternatives: hand-maintained markdown (rots),
runtime DB table (wrong lifecycle), knowledge graph (that's the runtime
product for customer metadata, not a design-time list of ~30 edges).

Customer-runtime state — which connectors an installation actually has
configured — is ops_setup_completeness / adapters config, NOT this.

Fields:
  from_tool / to_tool  — edge direction is dataflow, "core" in the middle
  artifact_parsed      — the native artifact the connector consumes/emits
  mechanism            — parser or adapter that does the work
  status               — shipped | planned | watchlist
  tier                 — Basic | Pro
  direction            — ingest | publish
  notes                — decisions, scope limits, open questions
"""

from __future__ import annotations

STATUSES = ("shipped", "planned", "watchlist")
DIRECTIONS = ("ingest", "publish")
TIERS = ("Basic", "Pro")

INTEGRATION_REGISTRY = [
    {
        "from_tool": "SQL Server (on-prem)",
        "to_tool": "core",
        "artifact_parsed": "sys.sql_modules definitions (procs + views)",
        "mechanism": "extractor: onprem_gateway profile (JDBC via On-premises Data Gateway) -> ScriptDom",
        "status": "shipped",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "1.8.0 — turn-key front door; definitions stored as extracted",
    },
    {
        "from_tool": "Azure SQL / Managed Instance",
        "to_tool": "core",
        "artifact_parsed": "sys.sql_modules definitions (procs + views)",
        "mechanism": "extractor: azure_direct profile (AAD-token pyodbc) -> ScriptDom",
        "status": "shipped",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "1.8.0",
    },
    {
        "from_tool": "Fabric Warehouse / SQL DB / mirrored DB",
        "to_tool": "core",
        "artifact_parsed": "sys.sql_modules definitions (procs + views)",
        "mechanism": "extractor: fabric_native profile (AAD-token pyodbc) -> ScriptDom",
        "status": "shipped",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "1.8.0",
    },
    {
        "from_tool": "Power BI (DevOps git repos)",
        "to_tool": "core",
        "artifact_parsed": "TMDL (.SemanticModel: partitions, DAX measures, calc columns)",
        "mechanism": "TMDL parser via devops_git profile (PAT from Key Vault)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "1.9.0 — consumption layer (ADR 0040); v1 scope per Sunny 2026-08-16",
    },
    {
        "from_tool": "Power BI (Fabric workspace, git or not)",
        "to_tool": "core",
        "artifact_parsed": "TMDL incl. DirectLake partitions (entityName)",
        "mechanism": (
            "TMDL parser via workspace profile (REST getDefinition, no git "
            "needed) or folder profile (git-synced); DirectLake = pattern 5, "
            "report->technical edges"
        ),
        "status": "shipped",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "workspace profile 1.11.0 — verify Fabric-WH-endpoint M shapes with a real fixture",
    },
    {
        "from_tool": "core",
        "to_tool": "Power BI reports",
        "artifact_parsed": "report descriptions (Fabric REST PATCH)",
        "mechanism": "fabric_pbi adapter, lineage-exact matching (920_publish_pbi)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "publish",
        "notes": "1.9.0 — pushes logged to gov_publish_log",
    },
    {
        "from_tool": "core",
        "to_tool": "Collibra",
        "artifact_parsed": "assets + descriptions + glossary terms (REST)",
        "mechanism": "collibra adapter (900_publish_collibra)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "publish",
        "notes": "",
    },
    {
        "from_tool": "core",
        "to_tool": "Microsoft Purview",
        "artifact_parsed": "assets + descriptions (REST)",
        "mechanism": "purview adapter (910_publish_purview)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "publish",
        "notes": "",
    },
    {
        "from_tool": "dbt",
        "to_tool": "core",
        "artifact_parsed": "manifest.json (DAG from ref() edges) + compiled T-SQL",
        "mechanism": "manifest reader (native JSON) -> ScriptDom on compiled SQL",
        "status": "planned",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "NEXT — cheapest connector; out of v1 unless a design partner needs it",
    },
    {
        "from_tool": "Databricks",
        "to_tool": "core",
        "artifact_parsed": "SQL views + Unity Catalog DDL ONLY (PySpark/DLT notebook logic out of scope)",
        "mechanism": "PARSER TBD at build time: Spark Catalyst in-runtime vs documented doctrine exception",
        "status": "watchlist",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "post-v1; 2026-08-07 parser note updated 2026-09-02: ADR 0001 total, ANTLR grammar when built",
    },
    {
        "from_tool": "Snowflake",
        "to_tool": "core",
        "artifact_parsed": "GET_DDL() over views / materialized views / tasks / dynamic tables",
        "mechanism": "native parser per ADR 0001 (ANTLR grammar); "
                     "sqlglot is banned repo-wide (spec:G2)",
        "status": "watchlist",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "post-v1; same stale-parser caveat as Databricks — record decision here when made",
    },
    {
        "from_tool": "Synapse dedicated SQL pool",
        "to_tool": "core",
        "artifact_parsed": "procs + views (sys.sql_modules, legacy estates)",
        "mechanism": "same T-SQL catalog as Azure SQL -> ScriptDom",
        "status": "planned",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS A7 (P3); legacy healthcare estates",
    },
    {
        "from_tool": "Power BI paginated reports (RDL)",
        "to_tool": "core",
        "artifact_parsed": "dataset CommandText = raw SQL inside report XML",
        "mechanism": "XML walk -> ScriptDom",
        "status": "planned",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS B5 (P3); trivial walk, legacy-heavy verticals",
    },
    {
        "from_tool": "Power BI dataflows (Gen1/Gen2)",
        "to_tool": "core",
        "artifact_parsed": "M documents (model.json / definition API), often with native queries",
        "mechanism": "fetch document -> native-query extraction -> ScriptDom",
        "status": "planned",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS B4 (P3); verify definition API shape before build",
    },
    {
        "from_tool": "Power BI (non-git tenants, XMLA)",
        "to_tool": "core",
        "artifact_parsed": "same TMDL content as the git route",
        "mechanism": "XMLA read-only endpoint export instead of DevOps git",
        "status": "planned",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS B6 (P3); verify export format before build",
    },
    {
        "from_tool": "Fabric Data Factory / ADF pipelines",
        "to_tool": "core",
        "artifact_parsed": "SQL inside Script / Stored-Proc-call / Copy activities (pipeline JSON)",
        "mechanism": "definitions via git or REST -> walk activities -> ScriptDom",
        "status": "planned",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS C1 (P3)",
    },
    {
        "from_tool": "SSIS packages (.dtsx)",
        "to_tool": "core",
        "artifact_parsed": "SQL in Execute-SQL tasks and sources (XML)",
        "mechanism": "XML walk -> ScriptDom",
        "status": "watchlist",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS C2 (P4); legacy-heavy verticals only",
    },
    {
        "from_tool": "Power BI pure-M transformations",
        "to_tool": "core",
        "artifact_parsed": "folding/merging logic written in M itself (no SQL string)",
        "mechanism": "needs the M dialect tier beyond the ADR 0041 mini-parser",
        "status": "watchlist",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS B2 (P4); until built these partitions are "
                 "counted as known-unparsed in ops tracking — disclosed, never silent",
    },
    {
        "from_tool": "Oracle (PL/SQL)",
        "to_tool": "core",
        "artifact_parsed": "packages / procedures / views",
        "mechanism": "native parser per ADR 0001 (ANTLR PL/SQL grammar)",
        "status": "watchlist",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "ex-SOURCE_CONNECTORS part D; dialect tier + connector when demanded",
    },
]


def _validate() -> None:
    for row in INTEGRATION_REGISTRY:
        assert row["status"] in STATUSES, f"bad status: {row}"
        assert row["direction"] in DIRECTIONS, f"bad direction: {row}"
        assert row["tier"] in TIERS, f"bad tier: {row}"
        assert "core" in (row["from_tool"], row["to_tool"]), f"core not an endpoint: {row}"


_validate()


# ---------------------------------------------------------------------
# Connector doctrine (ADR 0069: SOURCE_CONNECTORS.md retired into this
# registry — the configurations became rows above; the standing
# doctrine of change detection and object identity lives here).
# ---------------------------------------------------------------------

# Change monitoring: ETL and CI/CD are just TRIGGERS; the core is one
# shipped mechanism — re-collect + content-hash diff (ADR 0022 hashes,
# src/extractor/tracker.py). Detection is deterministic per object.
CHANGE_TRIGGERS = (
    ("scheduled_sweep", "the universal floor",
     "nightly/weekly pipeline re-collects (modify_date prefilters), "
     "diffs hashes, re-parses only changed objects; works for every "
     "connector incl. file drop, no customer CI required"),
    ("cicd_hook", "the fast path where git exists",
     "a pipeline step on merge calls the same collect+diff; instant "
     "freshness for DevOps-managed sources; never required"),
    ("etl_posthook", "the third doorway",
     "shops whose procs deploy via ETL call the same entry as a final "
     "step; same mechanism"),
)
CHANGE_PAYOFF = (
    "certification pins a version (ADR 0022), so a drifted object "
    "flips its dependents to 'definition changed since certification' "
    "— disclosed in every answer (ADR 0021), a DriftEvent lands, the "
    "steward gets a diff. The certification lifecycle closing its loop.")

# Object identity across re-ingests (Sunny's question, 2026-08-11):
# name says WHICH object, hash says WHICH REVISION.
IDENTITY_RULE = (
    "identity is the fully qualified name DECLARED IN THE SQL "
    "(schema.object, case-folded per ADR 0016) — never the file name; "
    "metric_id (ADR 0015) is that name; the content hash (ADR 0022) "
    "is its version. Same name + new hash = drift (the normal case).")
# The rename ladder: each step typed per the decision-typing rule
# (spec:E3) — computable steps are code's, judgment steps are the
# steward's, never auto-merged.
IDENTITY_LADDER = (
    ("exact_hash_rename", "computable",
     "a new name whose content hash equals a vanished name's hash "
     "auto-maps, disclosed as 'renamed from X'"),
    ("step_overlap_similarity", "judgment",
     "per-step fragment hashes score candidate rename+edits; the "
     "system PROPOSES with evidence, the steward CONFIRMS; confirmed "
     "mappings land as append-only alias records carrying history"),
    ("no_match", "computable",
     "genuinely new object; the vanished one is archived"),
)
NATIVE_STABLE_IDS = (
    ("SQL Server / Azure SQL object_id", False,
     "DROP+CREATE deployments mint new ones — declared name only"),
    ("file drop paths", False,
     "customers reorganize folders — declared name only"),
    ("Power BI artifacts", True, "stable GUIDs are the identity"),
    ("DevOps git sources", None,
     "partial — git rename detection feeds ladder step 1"),
    ("dbt", True, "unique_id is the identity"),
)
# Sunny's shipping decision, 2026-08-11: v1 ships the LIMITATION,
# loudly — renames reset governance history; the install guide and the
# packaged CONNECTIVITY_AND_CHANGE_MANAGEMENT.md warn admins. Ladder
# steps 1-2 are built ONLY if rename-loss blocks more than a one-off
# customer.
IDENTITY_SHIPPING_DECISION = "v1 ships the limitation, loudly"
