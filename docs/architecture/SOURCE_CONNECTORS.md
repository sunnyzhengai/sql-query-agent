# Source Connectors & Change Monitoring

**Date:** 2026-08-11 · **Status:** research + modular plan (Sunny's ask:
"we can't assume every customer uploads SQL files like I do")

The shipped acquisition path — SQL files dropped into Lakehouse Files —
reflects one real configuration (Sunny's: PBI on Fabric, databases
on-prem, views/procs called by PBI). This doc enumerates every
configuration where customer SQL/BI logic actually lives, then defines
the modular connector architecture that feeds them all into the SAME
pipeline unchanged.

## Part 1 — Where the logic lives (the full configuration space)

### A. T-SQL relational engines (ScriptDom already parses all of these)

| # | Configuration | What holds the logic | Extraction path | Priority |
|---|---|---|---|---|
| A1 | **File drop** (shipped) | .sql files exported by the customer | Lakehouse Files upload — stays forever as the universal tier-0 fallback (works for EVERY source below) | SHIPPED |
| A2 | **Fabric Warehouse** | procs + views in Fabric | `sys.sql_modules` / `INFORMATION_SCHEMA.ROUTINES` via the warehouse SQL endpoint, straight from a pipeline notebook under the workspace identity — no gateway, no secrets | P1 |
| A3 | **Fabric Lakehouse SQL analytics endpoint** | views only (no procs) | same catalog views as A2 | P1 (same connector) |
| A4 | **Fabric SQL Database** (newer item type) | procs + views | same T-SQL catalog | P1 (same connector) |
| A5 | **Azure SQL Database / Managed Instance** | procs + views | direct TDS from a notebook (pyodbc/JDBC), `sys.sql_modules`; auth via Entra service principal or SQL auth from Key Vault | P2 |
| A6 | **On-prem SQL Server** (Sunny's world) | procs + views | two honest routes: (a) **customer-side extractor script** (a tiny signed PowerShell/Python we ship: dumps `sys.sql_modules` to .sql files + uploads via OneLake API → lands as A1) — zero inbound connectivity, hospital-friendly; (b) on-prem **data gateway** + pipeline copy for orgs that already run one | P2 (script), P3 (gateway doc) |
| A7 | **Synapse dedicated SQL pool** (legacy) | procs + views | same catalog views as A5 | P3 |

### B. The Power BI layer (logic that is NOT views/procs — Sunny's point)

| # | Configuration | What holds the logic | Extraction path | Priority |
|---|---|---|---|---|
| B1 | **Semantic models — M partitions with NATIVE QUERIES** | `Sql.Database(..., [Query="SELECT ..."])` inside partition M expressions — full SQL embedded in M | we already ingest TMDL from DevOps git (shipped for report lineage); extend the TMDL walk to extract partition source expressions → pull the native query string → ScriptDom parses it like any proc | **P1 — biggest gap, most differentiating; the TMDL plumbing exists** |
| B2 | **Semantic models — pure M transformations** | folding/merging logic written in M itself (no SQL string) | requires an M parser (dialect tier of its own). Honest status: ROADMAP; v1 records these partitions as *known-unparsed sources* in ops tracking so coverage is disclosed, never silently missing | P4 |
| B3 | **DAX measures** | measure definitions in TMDL | shipped for lineage; measure-as-metric-node promotion is the dimension-layer follow-on | shipped/partial |
| B4 | **Dataflows (Gen1/Gen2)** | M documents (model.json / dataflow definition via API), often with native queries | same native-query extraction as B1 once the M document is fetched | P3 |
| B5 | **Paginated reports (RDL)** | dataset `<CommandText>` = raw SQL inside report XML | trivial XML walk → ScriptDom | P3 (legacy healthcare estates are full of these) |
| B6 | **Non-git tenants** (no DevOps for TMDL) | same TMDL content | XMLA read-only endpoint export instead of git | P3 |

### C. Orchestration / ETL

| # | Configuration | What holds the logic | Extraction path | Priority |
|---|---|---|---|---|
| C1 | **Fabric Data Factory / ADF pipelines** | SQL inside Script, Stored-Proc-call, and Copy activities (pipeline JSON) | pipeline definitions via git or REST → walk activities → extract SQL | P3 |
| C2 | **SSIS packages (.dtsx)** | SQL in Execute-SQL tasks and sources (XML) | XML walk → ScriptDom | P4 (legacy-heavy verticals) |

### D. Non-Microsoft engines (existing roadmap tiers, unchanged)

dbt (manifest.json: compiled SQL + native DAG — NEXT), Databricks
(Unity Catalog views / GET_DDL-equivalents), Snowflake (GET_DDL),
Oracle PL/SQL. Each is a dialect tier (parser) + a connector (this doc).

**Verify-before-build notes:** exact Dataflow Gen2 definition API shape;
XMLA export format for B6; Fabric SQL Database catalog parity. Each is
a one-hour probe in the tenant before its connector is scheduled.

## Part 2 — Modular connector architecture

One protocol, one landing contract, zero pipeline changes:

```python
class SourceConnector(Protocol):
    def collect(self) -> Iterator[SqlArtifact]: ...

@dataclass(frozen=True)
class SqlArtifact:
    source_system: str      # "fabric_warehouse" | "tmdl_native_query" | ...
    origin_uri: str         # server/db/schema.object, git path, report id
    object_name: str
    dialect: str            # "tsql" (all P1/P2), later "m", "plsql"...
    sql_text: str
    content_hash: str       # ADR 0022 normalization — computed at collect
    origin_metadata: dict   # connector-specific (report name, workspace...)
```

- Every connector writes the SAME rows to `input_sql_sources` (+
  `ops_extraction_tracking`) that file-drop writes today. Stages 02–09
  never know or care where SQL came from — ADR 0009's adapter
  philosophy applied to the input side.
- `org_config.yaml` gains a `sources:` list — each entry {type,
  connection params}; 01_install iterates configured connectors. File
  drop remains the zero-config default.
- Layout: `src/connectors/` — `base.py` (protocol + artifact),
  `files.py` (current behavior, refactored in), then one module per
  configuration, each with fixture-based tests (a canned catalog dump /
  TMDL folder / pipeline JSON — no live services in CI).
- Build order by market coverage per effort: **files (shipped) →
  fabric_sql (A2/A3/A4, one connector) → tmdl_native_query (B1) →
  azure_sql (A5) → onprem extractor script (A6a) → RDL (B5) →
  dataflows/ADF (B4/C1) → dbt**.

## Part 3 — Change monitoring (Sunny's ask: ETL or CI/CD?)

The answer is **both are just triggers; the core is one mechanism we
already own**: re-collect + content-hash diff. ADR 0022 gives every
object a normalized content hash, and connectors compute it at collect
time — so change detection is `collected_hash != stored_hash`, per
object, deterministic, source-agnostic.

**Triggers, layered:**

1. **Scheduled sweep (the universal floor).** A nightly/weekly Fabric
   pipeline runs `collect()` (metadata-cheap for DB connectors —
   `sys.objects.modify_date` prefilters what to re-read), diffs hashes,
   and re-parses ONLY changed objects. Works for every connector
   including file drop; no customer CI required.
2. **CI/CD hook (the fast path where git exists).** For DevOps-managed
   sources (TMDL, dbt, SQL-in-git): a pipeline step on merge calls the
   same collect+diff. Instant freshness for shops that have the
   discipline; never required.
3. **ETL post-hook.** Shops whose procs are deployed by ETL jobs call
   the same endpoint/notebook as a final step. Same mechanism, third
   doorway.

**What a detected change does (the governance payoff):** certification
pins a version (ADR 0022), so a drifted object automatically flips its
dependent metrics to *"definition changed since certification"* —
disclosed in every answer (ADR 0021: disclose, never gate), a
DriftEvent lands in the governance stream, and the steward gets a diff
(the variants kernel renders it). Change monitoring isn't
infrastructure hygiene — it's the certification lifecycle finally
closing its loop.

**Recommendation:** ship trigger 1 (scheduled sweep) as the default in
the next connector milestone; document 2 and 3 as integration recipes.
Decision recorded here; ADR when the build starts.

## Part 4 — Object identity across re-ingests (Sunny's question,
## 2026-08-11: "is there an id that can be reliably used?")

Identity is the fully qualified name DECLARED IN THE SQL
(schema.object, case-folded per ADR 0016) — never the file name.
metric_id (ADR 0015) is that name; the content hash (ADR 0022) is the
VERSION of it. Two levels: name says which object, hash says which
revision. Same name + new hash = drift (the normal case; works).

**The rename gap:** a renamed/re-schema'd object looks like one
disappearance plus one unrelated arrival — certification and usage
history would strand. No universal reliable id exists, so a
deterministic ladder (decisions placed per ADR 0035's taxonomy):

1. **Exact-hash rename** (computable → code): a new name whose content
   hash equals a vanished name's hash auto-maps, disclosed as
   "renamed from X".
2. **Step-overlap similarity** (computable signal, judgment call):
   per-step fragment hashes score candidate rename+edits; the system
   PROPOSES with evidence, the steward CONFIRMS — never auto-merged.
   Confirmed mappings land as append-only alias records that carry
   certification + usage history across.
3. **No match** → genuinely new object; the vanished one is archived.

**Native stable ids, used wherever a connector has one:**

| Source | Stable id? | Use |
|---|---|---|
| SQL Server/Azure SQL object_id | NO — DROP+CREATE deployments mint new ones | declared name only |
| File drop paths | NO — customers reorganize folders | declared name only |
| Power BI artifacts (reports, semantic models) | YES — stable GUIDs | GUID is the identity |
| DevOps git sources | partial — git rename detection | feeds ladder step 1 |
| dbt | YES — unique_id | unique_id is the identity |

Identity transfer is itself a governed event: automatic only when
byte-deterministic, steward-confirmed when fuzzy, append-only always.
