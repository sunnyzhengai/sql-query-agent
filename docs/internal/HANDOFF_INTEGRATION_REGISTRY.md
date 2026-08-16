# Handoff — integration registry: the tool/connector landscape as data

> **Status (2026-08-16, dev session): items 1–3 implemented in 1.9.1.**
> src/integration_registry.py (validated on import), generated
> INTEGRATION_MAP.md + freshness test, shipped-ingest-connector ↔
> INSTALLATION_GUIDE projection test. Databricks/Snowflake parser
> columns carry the TBD-at-build-time note verbatim. Item 4
> (customer-runtime connector state) deliberately not built, per the
> handoff. ROADMAP/REFERENCE_ARCHITECTURE tables should be banner-noted
> as superseded on their next edit.

**From:** learning/review session, 2026-08-16. **To:** dev session.
**Origin:** Sunny: "best way to keep track of all tools (PBI, Fabric, SQL
Server, Collibra, Purview, dbt, Databricks, Snowflake) and the connectors
between them?" Decision: registry-as-data, projections generated, tests
pin freshness — the TABLE_REGISTRY pattern applied to the integration
landscape. Explicitly rejected: hand-maintained md (notebooks/README rot),
runtime DB table (wrong lifecycle), knowledge graph (runtime product for
customer metadata, not a design-time list of ~30 edges).

## Wanted

1. **INTEGRATION_REGISTRY** (Python or YAML in-repo; follow the
   TABLE_REGISTRY single-source-of-truth conventions). One record per
   connector:
   - from_tool, to_tool
   - artifact_parsed (TMDL, sys.sql_modules, manifest.json, REST API, ...)
   - parser/mechanism (ScriptDom, TMDL parser, adapter, connection profile)
   - status: shipped | planned | watchlist
   - tier (Basic/Pro), direction (ingest | publish | both), notes
   Seed rows from the RECORDED roadmap (ROADMAP.md connector roadmap
   2026-08-07 + REFERENCE_ARCHITECTURE.md tier table — the registry
   supersedes both as source of truth once built):
   - SQL Server: shipped (1.8.0, 3 connection profiles)
   - PBI/TMDL via DevOps: shipped→extending (v1 scope per
     HANDOFF_PBI_SEMANTIC_LAYER)
   - Collibra + Purview publish adapters: shipped
   - dbt manifest.json: NEXT (cheapest — JSON + compiled T-SQL → ScriptDom,
     DAG free from ref() edges)
   - Fabric-native semantic models: NEXT (TMDL; DirectLake pattern gap)
   - Databricks: roadmap/post-v1 — SQL views + Unity Catalog DDL ONLY;
     PySpark/DLT notebook logic explicitly out of scope
   - Snowflake: roadmap/post-v1 — GET_DDL() over views/mat views/tasks/
     dynamic tables
   ⚠ PARSER COLUMN STALE for the last two: the 2026-08-07 table says
   "sqlglot dialect", which predates the sqlglot retirement. Re-decide at
   build time: Spark SQL has a native option in-runtime (Catalyst via
   Fabric Spark); Snowflake = documented doctrine-exception (sqlglot
   dialect) vs ANTLR grammar. Record the decision in the registry row.
2. **Generated integration map**: extend scripts/generate_docs.py to emit
   docs/architecture/INTEGRATION_MAP.md (mermaid + table) from the
   registry; add a freshness test mirroring
   test_pipeline_map_is_freshly_generated. Keep it SEPARATE from
   PIPELINE_MAP (different question and audience).
3. **Projections that must cite the registry** (tests where cheap):
   marketplace tier table, INSTALLATION_GUIDE connector prerequisites,
   the pitch/federation diagram (curated visual, but content derived).
4. Later (not now): customer-runtime instance of this — which connectors
   an installation actually has configured — belongs with
   ops_setup_completeness / adapters config, NOT in this registry.
