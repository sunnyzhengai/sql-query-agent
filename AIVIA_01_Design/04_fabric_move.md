04_fabric_move.md

Design description:
- Move phases 02-03 to Fabric: the sheets become lakehouse Delta
  tables, the graph becomes a declared Fabric graph model over them,
  the chat reads from Fabric, and the Fabric Data Agent is compared
  head-to-head against our own chat. Local stays the build-and-truth
  environment (the standing principle: design, plan and develop
  locally, then move code and data to Fabric).
- ALL DECISIONS RATIFIED by Sunny 2026-09-30. Table names confirmed;
  decision 1's archive question RULED: Delta only. Open TBDs remain
  only where named: the Key Vault secret names (decision 5, by M05)
  and stage B's host (decision 7, by M07).

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
   - TBD (Sunny): the secret names (closes the standing TBD in the 02
     and 03 contracts).

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
     TBD (Sunny, the big product ruling): Azure-hosted web app
     reading the lakehouse, or a Fabric-native workload (the deeper
     marketplace story, the heavier lift). Stage B may be ruled into
     this phase or split into its own.

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

M03: The graph model — declared over the node/edge tables; the
    decision-2 validation gate runs and its results land in the doc.

M04: Stage A chat — the engine's asset source becomes a parameter;
    the chat runs locally reading Fabric; the twelve shapes rerun.

M05: Models and keys — Azure OpenAI endpoints, Key Vault, Entra;
    the parity law verified (one known embedding re-computed on the
    Azure model and compared to the stored vector).

M06: The Data Agent comparison — decision 8's head-to-head; the
    scorecard recorded.

M07: Stage B surface — opens only after Sunny's decision-7 ruling.

M08: The kit closes — test_04_* suites green, Sunny's 04 shapes md
    with the run commands, acceptance parity per decision 9.

Standing laws that bind this phase: capacity ops on Sunny's go, one
refresh per batch; no Fabric Data Agent as validator; verdicts land in
docs same-day; paid calls real; tests red before code; Sunny authors
Design/ and Data/, Claude authors Code/ and Test/.
