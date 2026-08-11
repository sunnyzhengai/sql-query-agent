# Connectivity & Change Management

How your SQL logic gets into AIVIA, how the product tracks changes to
it, and the one rule your development teams must know before go-live.

## How your SQL gets in

**Shipped today: file upload.** Export your procedures and views as
`.sql` files and upload them to the Lakehouse (Installation Guide,
step 3d). This path works for EVERY source system — on-prem SQL
Server, Azure SQL, Fabric — because every one of them can export its
objects as files. It is deliberately the universal baseline.

**Connectors on the roadmap** (in delivery order): direct extraction
from Fabric Warehouse / Lakehouse SQL endpoint / Fabric SQL Database;
SQL embedded in Power BI semantic models (native queries inside
Power Query partitions); Azure SQL Database / Managed Instance; an
extractor script for on-prem SQL Server (no inbound connectivity
needed — it exports and uploads from your side); paginated-report
(RDL) datasets; Data Factory pipelines; dbt projects. Each connector
feeds the same pipeline — nothing about your deployment changes when
you adopt one.

## How identity and change tracking work

- A metric's identity is the **`[schema].[object]` name declared
  inside the SQL** — never the filename. Rename files freely.
- Every object's content is **hashed on ingestion**. Re-uploading (or
  a future connector's scheduled sweep) compares hashes: unchanged
  objects are untouched; **edited objects are re-processed and their
  dependent metrics are flagged "definition changed since
  certification"** for steward review. Editing a procedure in place is
  a fully supported, governed event.

## 🔴 CRITICAL — the rename rule (tell your developers)

**Renaming a procedure or view — or moving it to another schema —
resets its governance history.** The system sees the old name as
deleted and the new name as a brand-new metric. Certification,
steward assignments, usage history, endorsements, and business-term
links do **not** transfer, and there is currently no automatic
carry-over. (SQL Server itself offers no rename-stable identifier
across the DROP-and-CREATE deployments most teams use — this is a
property of the platform, not a defect of the product.)

**Policy we recommend you adopt at go-live:**
1. Treat renames of governed procedures/views as a **change-controlled
   event**, not a refactor.
2. If a rename is unavoidable: rename, re-ingest, then have the
   steward re-certify the new name and retire the old one.
3. Prefer in-place edits (`ALTER` / `CREATE OR ALTER`) — those are
   versioned and steward-flagged automatically.

## Keeping the graph fresh

Re-run the ingestion pipeline whenever your SQL estate changes — on a
schedule (recommended: weekly), as a step in your CI/CD release
pipeline, or as a post-step of your ETL deployment job. All three call
the same pipeline; hash comparison makes re-runs cheap and idempotent.
