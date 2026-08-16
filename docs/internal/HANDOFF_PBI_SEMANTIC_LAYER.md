# Handoff — PBI / semantic-model layer: from prototype constellation to product

**From:** learning/review session, 2026-08-16. **To:** dev session.
**Origin:** Sunny's turn-key review — "PBI calls these procs, adds formulas
and visuals; in the cloud there will be semantic models. We did some work,
never tested. Turn-key or hodge-podge?" Answer: hodge-podge with one
library-grade core.

## Inventory (verified 2026-08-16)

- src/extractor/devops_tmdl.py — TMDL parser: partition M-expressions
  (deterministic report→proc/view lineage), DAX measures, calc columns.
  13 tests, byte-exact fixtures. LIBRARY-GRADE. The asset.
- notebooks/utilities/devops_lineage.py — manual driver; PAT="" TODO;
  prints summaries; writes NOTHING to pipeline tables.
- src/adapters/fabric_pbi.py — description write-back onto PBI reports via
  Fabric REST. 246 lines, ZERO callers (audit ghost list). Wire or delete.
- collibra_lineage_match + notebook 08 — _PBI-suffix metric ↔ Collibra
  report asset matching. LIVE, 21 tests, but Collibra-specific.
- input_metric_names — registry status "planned"; 03 reads it optionally;
  nothing has ever written it. The intended landing spot for report names.

Nothing above is wired into the numbered pipeline; never run end-to-end.

## Architectural framing (agreed with Sunny)

Business logic splits across TWO layers in every environment: SQL
(procs/views — on-prem heavy) and DAX (measures/calc columns —
Fabric-native heavy). Both native parsers already exist (ScriptDom, TMDL
parser). What is missing is a HOME: the graph has no report/measure node
types, so the DAX half is extracted and discarded.

## Wanted

1. **ADR: graph model extension** — report + measure node types; edges
   report→canonical (partition lineage), measure→columns (DAX refs);
   exports + agent instructions follow. Same scale of decision as
   graph-vs-delta; do NOT bolt on without the ADR. Consider whether the
   ghost DIMENSION layer's removal/repurposing folds into the same ADR.
2. **Semantic-model source profiles** (mirror of extractor handoff item 6):
   (a) DevOps git repo w/ PAT (today — PAT must move to Key Vault, not the
   hardcoded TODO); (b) Fabric-native: semantic-model definitions read from
   workspace items / git-synced .SemanticModel folders — no DevOps
   dependency.
3. **Activate input_metric_names**: a numbered (or 00-family) notebook that
   runs the TMDL extraction and writes the table 03 already knows how to
   consume; registry status planned→active; precondition/optional-input
   wiring follows automatically from the contracts.
4. **fabric_pbi.py verdict**: wire it (description write-back = the
   enrichment-out story, "answer is a caption" applied to PBI) or delete it
   per the ghost rule. Zero-caller code may not keep existing by default.
5. **End-to-end test** with recorded TMDL fixtures through whatever
   pipeline shape 1–3 produce.

## Scoping question — SUNNY'S CALL, do not guess

Is the PBI/semantic layer IN the Marketplace v1 scope, or is v1 "SQL layer
complete, PBI layer next release"? Items 1–5 are sequenced work either
way; the answer decides whether they precede or follow launch hardening.
