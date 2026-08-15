# Handoff — items for the contracts/cleanup session

**From:** the code-reading (teaching) session, 2026-08-15. That session is
read-only by agreement and will not implement these. **To:** the session
fixing contract misalignments and creating the contracts. Fold these into
the contract design rather than treating them as separate tasks.

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
