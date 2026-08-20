# Handoff — shipped-vs-internal zones, the trace registry, and the admin graph + companion

**From:** review session, 2026-08-20. **To:** dev session.
**Verdicts below are Sunny's, made 2026-08-20 — do not re-litigate the
decisions; scope and mechanics are yours to shape.**

## Verdicts (Sunny, 2026-08-20)

1. **Everything we ship is governed; everything unshipped lives in one
   declared zone.** Carve out a top-level `internal/` and consolidate the
   unshipped material there (docs/internal/, learning/, presentation/,
   private/ are the obvious candidates — dev session proposes the exact
   move list). The repo partitions into governed ⊎ internal: nothing
   unclassified.
2. **The admin co-pilot does not wait for customers.** ADR 0011's
   "no data on what breaks until 3+ customers" reasoning predates the
   contract regime; the contracts now DEFINE what a working system is —
   each step's required inputs, outputs, and escalations are enumerated
   and checked. Build the companion on that. (ADR 0011 needs an amendment:
   trigger changes from "3+ customers" to "admin graph projected." Field
   data still enriches the residue outside the contract frontier —
   environment/tenant quirks — via the existing signature-census channel.)
3. **The Q1 trace lineages (ADR → axiom → module → test → doc) go INTO
   the admin graph**, so the companion can trace any issue to its root:
   symptom → error event → contract → producing notebook → src module →
   ADR → remediation, every hop a real edge.

## Scope (in order)

1. **Zone carve-out.** `git mv` the unshipped trees under top-level
   `internal/` (history-preserving). Declared-zones rule, mechanically
   enforced: every top-level path is either governed (registered, see
   item 2) or under `internal/` — an unclassified path fails CI.
   `scripts/build_deployment_package.py`'s allowlist + leak check remain
   the shipped-boundary enforcement (SHIPPED_DOCS stays the one truth for
   what customers receive); after the move, its verify step should get
   simpler, not looser. Fix internal cross-links (handoffs, ADR
   references to docs/internal/ paths).

2. **TRACE_REGISTRY** (seventh peer registry, truth-as-data). One entry
   per decision: ADR id → spec axioms grounded → implementing src/
   modules → enforcing tests → summarizing docs. Category field per ADR
   (architecture | product/business — business ADRs legitimately have no
   code). Three closure checks in CI:
   - totality: every governed artifact traces to ≥1 decision (the ghost
     rule mechanized — an uncited src/ module is a finding);
   - existence: every cited path/test exists (the failure class the
     spec audit caught by hand in A1 — a cited test that didn't exist);
   - single classification: governed ⊎ internal covers the repo.
   `docs/architecture/TRACE_MAP.md` is a generated projection (the
   NOTEBOOK_MAP pattern): open any ADR, see its axioms, code, tests.

3. **The admin graph** — executes ADR 0039's planned follow-up
   ("project contracts as graph nodes so error → contract → data is
   walkable") and extends it with the trace lineage. Node kinds:
   contract, notebook, src module, ADR, spec axiom, error event,
   checklist item. Edges (all deterministic, from registries and event
   tables — witness rule spec:B1 applies to the admin graph too):
   notebook —produces→ contract; contract —enforced_by→ gate/test;
   module —implements→ ADR/axiom; error —violates→ contract (the 0039
   citation, now an edge); ADR —grounds→ axiom; decision —traced_by→
   module/test (from TRACE_REGISTRY). The admin graph is a PROJECTION
   (spec:D3): rebuilt from registries + event tables each run, never a
   second truth. Give it EXTRACTION_REGISTRY rows (its source kinds are
   the registries themselves — C1 applies reflexively).

4. **The admin companion.** The LLM layer over the admin graph,
   explaining installation steps and diagnosing failures like a human
   companion. Architectural constraints, all existing law:
   - **One engine** (ADR 0046: two paths for one goal — banned): the
     companion is the product's anchor → traverse → present engine
     pointed at the admin graph, not a second engine.
   - **E3 discipline**: every check is code (the gates already ship);
     the LLM anchors admin language to admin-graph nodes, walks real
     edges, and narrates. It never diagnoses by vibe — a diagnosis is a
     path in the graph, captioned.
   - **Grounding corpus**: contracts, ADRs (recorded since 0011
     precisely for this), spec axioms, escalated checklist rows,
     ops_installation_errors signatures.
   - BYOT: runs on the customer's Azure OpenAI like everything else.
   Sequencing inside this item: graph projection first (item 3), then
   the step-explainer ("what does 300 need and produce" — a registry
   projection, no LLM needed for the facts), then the diagnostic
   conversation surface.

5. **ADR duties**: amend ADR 0011 (trigger change, verdict 2); new ADR
   for the trace registry + admin graph + companion (Context: Sunny's
   closed-system requirement and "we should know what a working system
   should be like"; this handoff is the raw material).

## Current-state audit and move list (review session, 2026-08-20)

Audited after the dev session's zone migration (internal/ now holds
docs+learning+presentation+private; docs/internal is gone). Verified
clean, no action needed: secrets hygiene (llm_api_key.txt / .env /
org_config.yaml all gitignored, never in git history; llm_api_key.txt
is a LIVE mechanism read by scripts/validate_deployment.py and 600 —
not cruft), data/ = demo/sample/synthetic fixtures (governed),
build//egg-info/caches untracked.

Remaining cleanup, ordered — **execute only after the current field
cycle is green** (env publish + 500/600 rerun pending), one
coordinated commit per item:

1. **Delete the three empty husk dirs** at root: learning/,
   presentation/, private/ (git mv left them behind; verified empty).
2. **Prune dist/**: 54 wheels tracked (every release since 1.9.x).
   Keep ONLY the current wheel (the `!dist/*.whl` gitignore exception
   exists for the Fabric env install); wheel history belongs in git
   tags/releases, not the working tree.
3. **Workspace-side retirements** (delete in the Fabric workspace
   FIRST, let git sync remove them — never git rm a live workspace
   item): eh_probe.DataAgent, KustoQueryWorkbench_1/2.KQLQueryset
   (numbered scratch; violates naming discipline). Grep for references
   before each deletion (the probe-eh lesson, item 5).
4. **Data Agent ruling needed (Sunny)**: Delta Agent / Graph Agent are
   the rematch-era comparison pair; SQL Intelligence Agent is
   presumably the keeper as the distribution surface. Which retire?
5. **probe-eh.Eventhouse is PRODUCTION under a probe name** —
   referenced by src/webapp/main.py, src/orchestrator/cli.py, and the
   devtools KQL. Options: rename to a clean production name (house
   naming rule) updating all reference sites + the workspace item in
   one coordinated change; or explicitly accept the name in the trace
   registry. Recommend rename at a quiet point; needs Sunny's go.
6. **Utility notebooks at root** (export_test_fixtures,
   make_golden_snapshot) violate the notebooks-location rule (only
   pipeline notebooks at root). Fabric workspace folders sync as repo
   subfolders — move them into a workspace folder via the workspace
   UI; verify the folder lands correctly in git on next sync.
7. **The lasting fix** (part of scope item 1): the CI zone plank —
   every top-level path is either on the governed allowlist or under
   internal/; an unclassified path fails CI. This prevents the root
   from regrowing weeds.

Root Fabric production items (numbered pipeline notebooks, Lakehouse,
Environment, GraphModel, demo SQLDatabase, telemetry + ED Sepsis demo
SM/reports) STAY — they are the workspace mirror; organizing them into
workspace folders is optional later polish, not cleanup.

## Notes

- (Resolved 2026-08-20: this handoff now lives in internal/docs/ — the
  zone migration it requested was executed same day.)
- The spec (SPEC.md) gains the admin graph as a second Σ-structure over
  the same axiom groups — same soundness/completeness/projection laws,
  new sorts. That amendment rides with the new ADR, version-bumped.
