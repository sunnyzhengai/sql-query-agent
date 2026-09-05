# Port Manifest — DRAFT v0.1 (for Sunny's ruling)

*The comparison artifact named by the MVP v1 build approach (ratified
2026-09-05: "new skeleton, ported organs"). Drawn from the 09-04/09-05
audit (the three Code Structure Maps) against the live `src/` tree.
Authored 2026-09-05.*

**Laws of this manifest**

1. Two-sided accounting: every TARGET module of the new skeleton gets
   exactly one verdict — `PORT` (proven organ moves with its tests),
   `REWORK` (organ moves, shape changes to the new metamodel), or
   `NEW` (no organ exists) — and every existing `src/` module gets a
   disposition (ported into / consulted by / not carried). Nothing
   unaccounted on either side.
2. Ported organs bring their test suites; the suite passing in the new
   address IS the porting acceptance. Reworked organs keep their suite
   as the *behavioral floor* — new-shape tests come from fixtures F1–F6.
3. The existing repo keeps running untouched (the demo path). "Not
   carried" means *not copied into the new skeleton* — never deleted.
4. PM-1..PM-4 were flagged, never decided, per the HITL law — then
   RULED 2026-09-05 (Sunny, adopting the draft reads); rulings and
   updated rows are landed in place. Formal ratification of the whole
   manifest rides the registry ratification pass.

---

## Level 1 — `graph/`

| Target | Verdict | Source / donors | Porting acceptance | Notes |
|---|---|---|---|---|
| `graph/store.py` | NEW | consult-only: `src/graph/delta_backend.py`, `src/graph/backend.py` | GV via fixture validator | append-only substrate is foundationally new; old backends assume mutable current-state tables |
| `graph/metamodel.py` | NEW | pattern donor: `src/spec_registry.py` (registry-as-code + stale-doc CI, the proven shape) | binding-mechanism-a stamp tests (new) | loads the ratified L1–L3 registries; code never sees the prose |
| `graph/phi_gate.py` | REWORK | `src/phi_scan.py` | `tests/test_phi_scan.py` (25 tests) as behavioral floor; door-2 fixtures owed to F6 before code | PM-1 RULED 2026-09-05: door 2 (free-typed usage payloads) is unproven territory for the SQL-hardened scan rules — conservative REWORK; signature narrows to pure text → (redacted, count) |
| `graph/kg1_intake.py` | NEW | donors: `src/dictionary.py`, `src/extraction_registry.py` | F1 fixtures + validator (GV-C conservation) | CONTRACT_DATALOAD intake never existed; A1/A2 identity, A14 quarantine, INTAKE-0..10 all new law |
| `graph/kg2_mapper.py` | REWORK | parser adapter PORTS whole: `src/parser/` (scriptdom_loader, sql_parser, identity, error_classifier); IR extraction REWORKS: `src/tree/extract.py`, `src/tree/translate.py` → the KG2 kind library | parser: `tests/parser/` + `tests/test_native_parser_law.py` port as-is; extraction floor: `tests/tree/test_extract.py` (18); new shape: F2 fixtures | ScriptDom authority is the proven organ (99%, 788/790); only the IR it feeds changes |
| `graph/kg3_artifacts.py` | NEW | donors: `src/governance/steward.py` (dispositions), `src/governance/publish_log.py` | F5 fixtures | the spine + lifecycle model changed at the foundation |
| `graph/kg4_concepts.py` | NEW | — | mint checks (CHECK-KG4-1) | human-act-required minting has no precedent organ |
| `graph/read_api.py` | NEW | consult-only: `src/graph/traversal.py` | GV-B3 completeness on every result | the import-law surface; plank-guarded |

## Level 2 — `lenses/` (v1 = the eleven ratified lenses)

| Target | Verdict | Source / donors | Porting acceptance | Notes |
|---|---|---|---|---|
| `lenses/registry.py` | NEW | pattern donor: `src/spec_registry.py` | rule-to-check meta-test | D1 accounting home |
| `lenses/derivation.py` | NEW | — | F3 `staleness_t0` + F5 derived-state answers | small arithmetic over chains; clean-room is cheaper than porting |
| `lenses/decisions.py` | NEW | — | F3 `decisions_membership` + `degenerate` (incl. the 09-05 literal-exclusion rule) | reads KG2 positions; the answer key is the spec — see PM-4 |
| `lenses/compliance.py` | NEW (join_compliance) · DEFERRED (divergence) | consult-only: `src/graph/topology.py` | F3 `join_compliance` (A12 direct-only + declared loophole) | divergence compares against prior state — v1 is first contact |
| `lenses/families.py` | NEW (relatedness) · DEFERRED (correspondence, concept_drift) | consult-only: `src/graph/decomposition_diff.py` | deterministic content-key tests (to author) | S4 rule ships with correspondence, later |
| `lenses/census.py` | NEW | — | F3 `working_set`, `gap_census`; F1 referenced-keys witness | the honesty counters |
| `lenses/usage.py` | DEFERRED (entire) | donors recorded for later: `src/flywheel.py`, `src/governance/funnel.py` | — | reads the deferred ask surface; import law makes the deferral checkable |

## Level 3 — `flows/`

| Target | Verdict | Source / donors | Porting acceptance | Notes |
|---|---|---|---|---|
| `flows/inbound.py` | NEW | thin: wraps kg1_intake + kg2_mapper | F1/F2 fixtures + F6 refusals | the two doors; refusal-names-the-rule is the error contract |
| `flows/produce.py` | REWORK | `src/descriptions.py` produce machinery incl. the skeleton composer (A13's ratified floor-grammar SEED) + `src/steps/agent_descriptions.py` | floor: `tests/test_descriptions.py` (29) + `tests/test_skeleton_composer.py` (38); new shape: F4 (interim substring-grade until A13 lands at this slice) | worklist becomes the staleness lens output (PROD-2); per-artifact atomicity (H10) is new |
| `flows/gates.py` | PORT | `src/steps/gates.py` (produce text gates) + injection fixtures; caption gate (`src/orchestrator/caption_gate.py`, `src/governance/leaf_grounding.py`) DEFERS with the inward flow | `tests/test_gate_recut.py`, injection cases in `tests/test_skeleton_composer.py`; grounding-gate suite defers with its flow | PM-2 RULED 2026-09-05: v1 ports only what v1 runs — a ported-but-unused gate family muddies the imports-nothing-deferred check for zero v1 value; GRND-2 sharing lands at the inward slice |
| `flows/approve.py` | NEW | donor: `src/governance/steward.py` | F5 approve scripts | dispositions-only write path (APPR-1, LC3-C3) |
| `flows/land.py` | REWORK | `src/adapters/file_export.py` (+ flow shape from `src/adapters/publisher.py`) | `tests/adapters/test_file_export.py` (9); new shape: F5 land scripts | v1 file-first ONLY; A15 export headers bind at THIS slice; render/confirm/send/observe staging is new; API adapters (collibra, purview) stay behind for the transport phase |
| `flows/materialize.py` | NEW | — | OPS-1 stamped-report tests (to author) | |
| `flows/run_events.py` | REWORK | `src/run_layer.py` (ADR 0061) | `tests/test_run_layer.py` (25) | gains outcome + abort accounting (H10) |
| `flows/match.py`, `flows/ground.py`, `flows/generate.py` | DEFERRED (inward flow entire) | donors recorded for later: `src/orchestrator/` (turn_engine, agent, core), `src/discovery/`, `src/replan.py`, `src/reachability.py` | one-mind suite stays green in the old repo | cleanest seam per the MVP ruling |

## Cross-cutting

| Target | Verdict | Source / donors | Porting acceptance | Notes |
|---|---|---|---|---|
| build-phase validator | PORT + grow | `AIVIA_Product/fixtures/validate_fixtures.py` (31 GV rules, green) | itself — it IS the acceptance | ruled "likely the FIRST real code of the build" |
| import-law + banned-construct planks | PORT (pattern) | `tests/test_native_parser_law.py`, `tests/test_spec_gates.py` (the proven plank shape) | plank suite green over the new packages | new scope: parser-only-in-mapper, no-LLM-in-graph/lenses, store-callable-only-by-lifecycle |

## Not-carried census (stays in the demo path, untouched)

- **Inward/demo surfaces:** `src/orchestrator/`, `src/webapp/`,
  `src/console.py`, `src/companion.py`, `src/agent_backend.py`,
  `src/xray.py` — deferred with the inward flow or demo-only.
- **Graph backend experiment:** `src/graph/fabric_graph_backend.py`,
  `src/graph/gql_client.py` — the hybrid verdict stands; not a v1 organ.
- **Old-law registries:** `src/spec_registry.py`, `src/trace_registry.py`,
  `src/invariants.py` — remain the OLD repo's law (pattern donors only);
  the new build's law lives in the metamodel/lens registries.
- **Everything else** (`src/marketplace/`, `src/mquery/`, `src/shapes/`,
  `src/steps/` remainder, `src/governance/` remainder, `src/adapters/`
  API transports, `src/extractor/` — see PM-3, `src/flywheel.py`,
  misc. single-file modules) — not carried; each stays runnable where
  it is.

## Flag rulings (all four RULED 2026-09-05, Sunny — adopting the draft reads)

- **PM-1 RULED — REWORK.** `phi_gate` gains door 2 (free-typed usage
  payloads), which the SQL-hardened scan rules have never seen; the
  conservative verdict is rework, old suite as behavioral floor,
  door-2 redaction fixtures owed to F6 before code. Row updated above.
- **PM-2 RULED — split.** Produce text gates + injection fixtures port
  now; the caption/grounding gate family DEFERS with the inward flow.
  v1 ports only what v1 runs — the imports-nothing-deferred check
  stays clean. Row updated above.
- **PM-3 RULED — extractor retires.** File-first covers intake as
  absolutely as landing: v1 receives DBA-delivered snapshots per the
  SOP runbook; no direct-connection scenario exists in a v1
  engagement. `devops_tmdl.py` stays parked as the H4 donor.
- **PM-4 RULED — clean-room stands.** The corpse catalog transfers
  through the kind library's adversarial fixture families (authored
  before mapper code, per protocol step 4), not through salvaged
  tree-walk code. `lenses/decisions.py` is written NEW against the F3
  answer key.
