# 0048 — Declared zones, the trace registry, the admin graph, and the admin companion

**Status:** Accepted (Sunny's verdicts, 2026-08-20 — HANDOFF_TRACE_AND_ADMIN_GRAPH)
**Date:** 2026-08-20

## Context

Two of Sunny's requirements converged: the closed-system requirement
("everything we ship is governed; everything unshipped lives in one
declared zone") and "we should know what a working system should be
like." The contract regime already answers the second in pieces — table
contracts, notebook gates, the capability registry, the spec's axioms —
but the pieces were not walkable as one structure, and the repo carried
unclassified material (docs/internal/, learning/, presentation/,
private/) outside any declared boundary.

Separately, ADR 0011 deferred the installation co-pilot until "3+
customers reveal real support patterns." That reasoning predates the
contract regime: the contracts now DEFINE what a working system is, so
the data the co-pilot was waiting for already exists — as registries.

## Decision

1. **Declared zones** (shipped 1.34.0). The repo partitions into
   governed ⊎ internal. All unshipped material lives under top-level
   `internal/`; every top-level tracked path must classify
   (src/zones.py, tests/test_zones.py) — an unclassified path fails
   CI. The deployment package's allowlist + FORBIDDEN scan remain the
   shipped-boundary enforcement.

2. **TRACE_REGISTRY** (src/trace_registry.py) — the seventh peer
   registry, truth-as-data. One entry per ADR: category (architecture
   | product — business ADRs legitimately have no code), spec axioms
   grounded, implementing src/ modules, enforcing tests, summarizing
   docs. Three closure checks in CI (tests/test_trace_registry.py):
   - **totality**: every src/ module is cited by ≥1 decision — the
     ghost rule mechanized; an uncited module is a finding;
   - **existence**: every cited path, test, and ADR file exists — the
     failure class the spec audit caught by hand (a cited test that
     didn't exist);
   - **single classification**: governed ⊎ internal covers the repo
     (with tests/test_zones.py).
   `docs/architecture/TRACE_MAP.md` is a generated projection
   (scripts/generate_docs.py, the NOTEBOOK_MAP pattern): open any ADR,
   see its axioms, code, tests.

3. **The admin graph** — executes ADR 0039's planned follow-up
   ("project contracts as graph nodes so error → contract → data is
   walkable") and extends it with the trace lineage. Node kinds:
   contract, notebook, src module, ADR, spec axiom, error event,
   checklist item. Edges, all deterministic from registries and event
   tables (the witness rule spec:B1 applies here too): notebook
   —produces→ contract; contract —enforced_by→ gate/test; module
   —implements→ ADR; ADR —grounds→ axiom; decision —traced_by→
   module/test; error —violates→ contract. The admin graph is a
   PROJECTION (spec:D3): rebuilt from registries + event tables each
   run, never a second truth. Its source kinds are the registries
   themselves — spec:C1 applies reflexively, via EXTRACTION_REGISTRY
   rows.

4. **The admin companion.** The LLM layer over the admin graph,
   explaining installation steps and diagnosing failures. Constraints,
   all existing law: ONE engine (ADR 0046's anchor → traverse →
   present, pointed at the admin graph — never a second engine); E3
   discipline (every check is code; the LLM anchors admin language to
   graph nodes, walks real edges, and narrates — a diagnosis is a path
   in the graph, captioned); grounding corpus = contracts, ADRs, spec
   axioms, escalated checklist rows, installation-error signatures;
   BYOT (runs on the customer's Azure OpenAI). Sequencing: graph
   projection first, then the deterministic step-explainer, then the
   diagnostic conversation surface.

5. **ADR 0011 amended**: the co-pilot trigger changes from "3+
   customers" to "admin graph projected." Customer field data still
   enriches the residue outside the contract frontier
   (environment/tenant quirks) via the signature census — it is no
   longer the gate.

## Consequences

- "What does a working system look like" has one answer: the admin
  graph, projected from the same registries the gates execute. Support
  and diagnosis walk the same edges CI enforces.
- The ghost rule is mechanical: code that no decision claims fails CI,
  so the registry stays total by construction.
- The spec gains the admin graph as a second Σ-structure over the same
  axiom groups (soundness, projection correctness, escalation) —
  amendment recorded in SPEC.md's changelog, version-bumped.
