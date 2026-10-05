04_fabric_move.md

Design description:

- Move phases 02-03 to Fabric: the sheets become lakehouse Delta
tables, the graph becomes a declared Fabric graph model over them,
the chat reads from Fabric, and the Fabric Data Agent is compared
head-to-head against our own chat. Local stays the build-and-truth
environment (the standing principle: design, plan and develop
locally, then move code and data to Fabric).
- ALL DECISIONS RATIFIED by Sunny 2026-09-30. Table names confirmed;
decision 1's archive question RULED: Delta only. Both named TBDs
have since closed: the Key Vault secret names (RULED at M05 DONE,
2026-10-01: aivia01-kv / aivia01-azure-openai-key) and stage B's
host (RULED 2026-10-01: B1 in-phase as M09, B2 deferred). The one
open TBD: the SaaS offer's timing (decision 7 rider).

The decisions:

1. The sheets become DELTA TABLES (proposed) — one lakehouse table per
  L09 map row kind: tables, columns, joins, values, value
   embeddings, abstracts, terms. Embeddings ride as array columns —
   the 254MB/1.1GB json problem dissolves into Delta. The F11
   precedent (sheet -> lakehouse table, Sunny's eye) extends to all.
   Ids verbatim, nothing minted, same as the sheets.
  - RULED 2026-09-30: DELTA ONLY — the local sheets stay the verbatim
  archive; no json Files in the lakehouse.
2. THE GRAPH MODEL — RULED 2026-09-30. Both layers are built:
  - The node/edge Delta tables (the L09 map) — structurally the
   exact input Fabric Graph requires; a graph model is DECLARED over
   lakehouse tables, so the tables are step one of the real model,
   never a stand-in for it.
  - The Fabric graph model declared over them, with a VALIDATION
  GATE instead of a consumer: GQL probes answered by the model and
  compared against the local engine's known-true answers — the
  connectivity census (one component of 38), per-kind edge counts
  (210 joins_by_fk + 181 joins_by_rule, provenance intact — the
  L08 ruling's "builder writes rule rows into the edge table"
  lands here), and pinned lookups (ZC_STATE's 9 edges with correct
  FK owners).
  - The chat does NOT read the graph model — nothing in the user
  path depends on it yet. It stands validated, ready for the
  future query-writing phase. Standing it up or refreshing it is a
  CAPACITY operation: Sunny's go, one refresh per batch.
3. SEARCH RUNTIME (proposed) — the cosine scan carries over; no
  vector index. Today's corpus is ~17,700 embeddings and the scan
   answers in milliseconds from Delta exactly as it does from json.
   Ruled threshold: a vector index enters when the corpus passes
   100,000 embeddings — a re-ruling here, driven by measurement.
4. MODELS IN PRODUCTION (proposed) — customer Azure OpenAI at launch
  (the standing governance ruling). THE PARITY LAW: the embedding
   model must be IDENTICAL to the one that embedded the stored rows
   (text-embedding-3-large exists on Azure OpenAI). A different model
   = re-embed everything; never mix embeddings across models.
   Segmentation model: the Azure-hosted small model equivalent,
   pinned in the 04 contract.
5. KEYS AND IDENTITY (proposed) — Entra ID sign-in (the phase 01
  browser sign-in precedent); keys in Azure Key Vault.
  - RULED at M05 DONE (2026-10-01): vault aivia01-kv, secret
  aivia01-azure-openai-key (closes the standing TBD in the 02 and
  03 contracts).
6. THE REFRESH STORY (proposed) — local stays the truth: parses,
  dictionary builds, abstract generation, gap-checks and paid-call
   gates all run on Sunny's machine; the Fabric load is a SYNC step
   (the wheel + notebook sync laws from phase 01 carry). A Fabric-side
   rebuild pipeline is NOT this phase.
7. THE CHAT SURFACE, STAGED (proposed):
  - Stage A (this phase): the existing local chat reads its assets
   FROM Fabric — the data plane proven end to end with zero new
   surface. The asset source becomes a parameter (local dir OR
   lakehouse), never a fork.
  - Stage B: the hosted production surface.
  RULED 2026-10-01 (Sunny, in chat; the full costing in
  briefs/Brief_M07_Stage_B_Host.md): stage B splits — B1 (the
  Azure-hosted, Entra-fronted engine) builds in THIS phase as
  M09; B2 (the Fabric workload wrapper) is deferred to its own
  phase, keyed to the marketplace push; the pure frontend-only
  toolkit port is REJECTED (one-engine law). SaaS-offer timing
  still open. (This passage said TBD until 2026-10-04 — the
  ruling had landed only in the M07/M09 milestone lines below;
  aligned in the briefs sweep.)
8. THE FABRIC DATA AGENT COMPARISON — RULED 2026-09-30 (Sunny's ask).
  Stand up the Fabric Data Agent over the same lakehouse tables and
   run the twelve shapes (plus the live session questions) against
   BOTH it and our chat, head to head. The scorecard is recorded in
   this phase's docs (the Round-4 precedent: homegrown 13/13 vs
   Fabric 8/13 — rerun on the new estate).
  - DIRECTION LAW: our chat is the ground truth and the acceptance
  gate; the Data Agent is the SUBJECT of comparison, never the
  validator (the standing rule stands). The comparison informs the
  product story and the competitive record.
  - Capacity + per-question cost: Sunny's go.
9. ACCEPTANCE (proposed) — parity to the digit: the Fabric-backed
  chat passes the same twelve shapes, and its startup census matches
   local exactly (38 / 1,618 / 14,476 / 1,656 / 210 / 181). Headless
   or web-UI eval only.

The move steps (Sunny renumbers as she sees fit):

M01: The data contract: 04_fabric_move_data_contract.md — the Delta
    schemas (one per L09 row kind), the sync inputs/outputs, model
    pins, secret names, authorship, capacity gates.

M02: The Delta loader — the wheel grows a loader that writes the
    sheets to lakehouse tables (F11 pattern extended); counts verified
    against the sheets to the digit; Sunny's eye on the first load.
    DONE 2026-09-30: wheel 0.3.0 published, eight files synced, the
    notebook ran, ALL ELEVEN TABLES at the golden counts — Sunny's run
    and eye. (Two Echo Law builds rode along: publish-watch retry and
    chunk-upload retry, from the live Errno 60.)

M03: The graph model — declared over the node/edge tables; the
    decision-2 validation gate runs and its results land in the doc.
    DONE 2026-09-30: AIVIA_01_GRAPH re-used (SQL_FILE declaration
    retired), Table/Column nodes + hasColumn/joins edges declared over
    the three graph_* tables, and ALL FOUR PROBES PASSED by Sunny's
    hand — 38/1,618 nodes, 210+181 edges by kind + 1,618 hasColumn,
    one component of 38 at radius TWO from PATIENT (rule edges proven
    landed), ZC_STATE's 9 inbound with owners correct and the reverse
    direction empty. Three Fabric GQL dialect laws learned live and
    recorded in the runbook: AS aliases mandatory, grouped aggregation
    refused (filtered counts are the form), quantified paths bounded
    by the real radius. The model stands validated, unconsumed,
    waiting for the query-writing phase.

M04: Stage A chat — the engine's asset source becomes a parameter;
    the chat runs locally reading Fabric; the twelve shapes rerun.
    DONE 2026-10-01: --fabric reads the eight chat tables over OneLake
    (deltalake 1.6.3, schema-enabled Tables/dbo path met live), census
    matched local TO THE DIGIT, and ALL TWELVE SHAPES PASSED
    Fabric-backed by Sunny's hand. The data plane is proven end to
    end; the lakehouse can feed the product.

M05: Models and keys — Azure OpenAI endpoints, Key Vault, Entra;
    the parity law verified (one known embedding re-computed on the
    Azure model and compared to the stored vector).
    DONE 2026-10-01: the aivia resource (East US 2) carries
    text-embedding-3-large + gpt-5.4-mini (ADOPTED over the planned
    gpt-5-mini — newer, no parity constraint on chat); vault
    aivia01-kv / aivia01-azure-openai-key; THE PARITY CHECK PASSED at
    cosine 0.999999 and lives on as a standing suite test; --azure
    composes with --fabric (the full production shape). The
    wrong-resource detour (deployments landing on
    founder-9856-resource via the Foundry project default) is in the
    runbook's troubleshooting.

M06: The Data Agent comparison — decision 8's head-to-head; the
    scorecard recorded.
    DONE 2026-10-01: both rounds run by Sunny's hand, scorecard in her
    04 shapes md. Round A (out-of-box) terminated at 0/2 — structural:
    the agent cannot conceive of data-as-catalog. Round B (instructed,
    briefing recorded verbatim): 5 clean / 5 partial / 1 false-absence
    miss of 11, vs ours 11/11. The three exhibits — census-days,
    payor/payer, disch-disp underscore — are ordinary phrasings that
    defeat string retrieval where the funnel's lanes succeed. The
    Round-4 record (13/13 vs 8/13) is succeeded.

M07: Stage B surface — opens only after Sunny's decision-7 ruling.
    BRIEF READY 2026-10-01 (overnight):
    AIVIA_01_Design/briefs/Brief_M07_Stage_B_Host.md — the 2026
    Extensibility Toolkit finding (workload = your own hosted web app
    + manifest in an iframe; 20-tenant private preview without
    certification), three shapes costed, recommendation: B1 = the
    Azure-hosted engine now (the substrate of every future), B2 = the
    Fabric workload wrapper deferred to the marketplace push. RULED 2026-10-01 (Sunny, in chat): B1 builds in phase 04 as M09; B2 deferred to its own phase; Shape 2 rejected. SaaS-offer timing still open.

M08: The kit closes — test_04_* suites green, Sunny's 04 shapes md

    with the run commands, acceptance parity per decision 9.

    PREPARED 2026-10-01 (overnight): the 04 contract's how-to-test TBD

    closed (all production commands recorded and accepted), suite

    green, docs reconciled.

    CLOSED 2026-10-01 (Sunny, in chat): M07 ruled same day; ruled

    Option 1 — M08 closes against the kit as it stands, the
    stage-B1 build opens as M09.

M09: The Azure-hosted engine — decision-7 stage B1 (opened by the
    M07 ruling, 2026-10-01): the Python engine productionized behind
    an Azure host, Entra ID sign-in in front, serving the existing
    chat page, reading the lakehouse per stage A. Stage B2 (the
    Fabric workload wrapper) is NOT here — deferred to its own
    phase, keyed to the marketplace push. ("B1"/"B2" are decision-7
    stage names only; product phases are Roman — 00_Architecture.md.)



Standing laws that bind this phase: capacity ops on Sunny's go, one
refresh per batch; no Fabric Data Agent as validator; verdicts land in
docs same-day; paid calls real; tests red before code; Sunny authors
Design/ and Data/, Claude authors Code/ and Test/.