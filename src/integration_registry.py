"""INTEGRATION_REGISTRY — the tool/connector landscape as data.

The TABLE_REGISTRY pattern applied to integrations (handoff 2026-08-16):
one record per connector between AIVIA and an external tool, single
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
  from_tool / to_tool  — edge direction is dataflow, AIVIA in the middle
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
        "to_tool": "AIVIA",
        "artifact_parsed": "sys.sql_modules definitions (procs + views)",
        "mechanism": "extractor: onprem_gateway profile (JDBC via On-premises Data Gateway) -> ScriptDom",
        "status": "shipped",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "1.8.0 — turn-key front door; definitions stored as extracted",
    },
    {
        "from_tool": "Azure SQL / Managed Instance",
        "to_tool": "AIVIA",
        "artifact_parsed": "sys.sql_modules definitions (procs + views)",
        "mechanism": "extractor: azure_direct profile (AAD-token pyodbc) -> ScriptDom",
        "status": "shipped",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "1.8.0",
    },
    {
        "from_tool": "Fabric Warehouse / SQL DB / mirrored DB",
        "to_tool": "AIVIA",
        "artifact_parsed": "sys.sql_modules definitions (procs + views)",
        "mechanism": "extractor: fabric_native profile (AAD-token pyodbc) -> ScriptDom",
        "status": "shipped",
        "tier": "Basic",
        "direction": "ingest",
        "notes": "1.8.0",
    },
    {
        "from_tool": "Power BI (DevOps git repos)",
        "to_tool": "AIVIA",
        "artifact_parsed": "TMDL (.SemanticModel: partitions, DAX measures, calc columns)",
        "mechanism": "TMDL parser via devops_git profile (PAT from Key Vault)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "1.9.0 — consumption layer (ADR 0040); v1 scope per Sunny 2026-08-16",
    },
    {
        "from_tool": "Power BI (Fabric workspace, git or not)",
        "to_tool": "AIVIA",
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
        "from_tool": "AIVIA",
        "to_tool": "Power BI reports",
        "artifact_parsed": "report descriptions (Fabric REST PATCH)",
        "mechanism": "fabric_pbi adapter, lineage-exact matching (13_publish_pbi)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "publish",
        "notes": "1.9.0 — pushes logged to gov_publish_log",
    },
    {
        "from_tool": "AIVIA",
        "to_tool": "Collibra",
        "artifact_parsed": "assets + descriptions + glossary terms (REST)",
        "mechanism": "collibra adapter (08_publish_collibra)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "publish",
        "notes": "",
    },
    {
        "from_tool": "AIVIA",
        "to_tool": "Microsoft Purview",
        "artifact_parsed": "assets + descriptions (REST)",
        "mechanism": "purview adapter (09_publish_purview)",
        "status": "shipped",
        "tier": "Pro",
        "direction": "publish",
        "notes": "",
    },
    {
        "from_tool": "dbt",
        "to_tool": "AIVIA",
        "artifact_parsed": "manifest.json (DAG from ref() edges) + compiled T-SQL",
        "mechanism": "manifest reader (native JSON) -> ScriptDom on compiled SQL",
        "status": "planned",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "NEXT — cheapest connector; out of v1 unless a design partner needs it",
    },
    {
        "from_tool": "Databricks",
        "to_tool": "AIVIA",
        "artifact_parsed": "SQL views + Unity Catalog DDL ONLY (PySpark/DLT notebook logic out of scope)",
        "mechanism": "PARSER TBD at build time: Spark Catalyst in-runtime vs documented doctrine exception",
        "status": "watchlist",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "post-v1; 2026-08-07 'sqlglot dialect' note predates sqlglot retirement — re-decide",
    },
    {
        "from_tool": "Snowflake",
        "to_tool": "AIVIA",
        "artifact_parsed": "GET_DDL() over views / materialized views / tasks / dynamic tables",
        "mechanism": "PARSER TBD at build time: documented doctrine exception (sqlglot dialect) vs ANTLR grammar",
        "status": "watchlist",
        "tier": "Pro",
        "direction": "ingest",
        "notes": "post-v1; same stale-parser caveat as Databricks — record decision here when made",
    },
]


def _validate() -> None:
    for row in INTEGRATION_REGISTRY:
        assert row["status"] in STATUSES, f"bad status: {row}"
        assert row["direction"] in DIRECTIONS, f"bad direction: {row}"
        assert row["tier"] in TIERS, f"bad tier: {row}"
        assert "AIVIA" in (row["from_tool"], row["to_tool"]), f"AIVIA not an endpoint: {row}"


_validate()
