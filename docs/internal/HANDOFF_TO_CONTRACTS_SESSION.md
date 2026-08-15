# Handoff — items for the contracts/cleanup session

**From:** the code-reading (teaching) session, 2026-08-15. That session is
read-only by agreement and will not implement these. **To:** the session
fixing contract misalignments and creating the contracts. Fold these into
the contract design rather than treating them as separate tasks.

> **Role swap (2026-08-15, later):** the sessions exchanged roles — the
> former teaching session now builds; the former contracts session now
> teaches (read-only). Items 1–3 below all landed (1.6.0–1.7.0). First
> build act after the swap: 1.7.1 — CI had been red since 1.6.0 (fastapi
> imported but undeclared broke collection, masking the whole suite);
> fixed with declared extras + a new imported-vs-declared contract test,
> which also caught undeclared PyJWT in marketplace_host before deploy.
> Note for local runs: tests/golden fallback smoke needs the ScriptDom
> sidecar on localhost:5111 (18 local-only failures when it's down).

## 1. Precondition gates (mirror of `postcondition_gate`)

`src/steps/gates.py` has `postcondition_gate` (proves what a step *wrote*
honors its contract) but no precondition half. Notebook cell 1 reads are
bare — e.g. `03_build_graph` reads `ops_parse_results` and the dictionary
tables with no existence check, so a missing table surfaces as a pyspark
`AnalysisException` stack trace mid-cell.

Wanted: a `precondition_gate` in `src/steps/gates.py`, called at the top of
each numbered notebook, that checks required input tables exist (and are
non-empty where emptiness is invalid) and fails with an operational
message that **names the producing notebook**, e.g.:

    [!] Preconditions failed for 03_build_graph:
        ops_parse_results missing — produced by 02_parse

The producer mapping should come from the same contract registry
(`tables_owned_by`) so gates can't drift from the contracts. The
`tableExists` fallback in 07 for `ops_phi_findings` is the existing
in-repo cousin of this pattern.

Design intent (Sunny): failures have two audiences. State problems
(missing/empty/stale tables) must surface as admin-actionable operational
messages so customer admins self-serve; raw stack traces are reserved for
true product defects, which route to Sunny. Every stack trace a gate could
have prevented is a misfiled support ticket.

## 2. Errors link back to contracts (extends ADR 0026)

ADR 0026 established error → **data** lineage (every error names its
metric/objects; blast-radius query). Sunny's contract philosophy extends
it one hop: every error is a node in the knowledge graph linked back to
the **contract whose failure produced it** (error → contract → data).

Implications for the contract work:

- Each contract in the registry needs a stable ID that error/event rows
  can reference (a `contract_id` column alongside ADR 0026's
  `affected_objects`), including gate failures from item 1 — a
  precondition failure is itself an error event citing the violated
  contract.
- Traceability chain: customer admin sees the operational message; Sunny
  queries the customer's graph for which contracts failed and how often;
  the same error repeating across multiple customers is the signal that
  the product itself needs improving, not the customer's environment.

If this lands, it likely warrants an ADR amendment or a new ADR that
cites 0026.

## 3. Optional inputs: setup incompleteness should be queryable state

Sunny's question (2026-08-15, reading 03 cell 2): are the optional-table
messages tied to documented admin prerequisites? Today: prose only. The
"No gov_steward_assignments table — run manage_stewards" line exists only
in notebook stdout; INSTALLATION_GUIDE lists the table but has no
matching setup step; nothing queryable records that a run proceeded
without the enrichment.

There is a third failure category between "gate error" and "product
defect": **legitimate-but-degraded state** (graph built with 0 stewards,
metrics showing object names only). Suggested contract treatment:

- Registry marks these inputs `optional`, each with a `remediation`
  field (which utility/notebook provides it).
- A pipeline run that proceeds without an optional input emits a
  setup-completeness record (queryable, e.g. feeding `/health`), not
  just a printed line — consistent with item 2: state that matters is a
  node in the graph, never only stdout.
- INSTALLATION_GUIDE's post-install steps should be generated from (or
  at least checked against) the optional-input registry so docs and
  contracts can't drift.
