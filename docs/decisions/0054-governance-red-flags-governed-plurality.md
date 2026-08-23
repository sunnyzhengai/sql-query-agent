# ADR 0054 — Governance red flags and governed plurality

**Status:** ACCEPTED 2026-08-23 — all four ratification items ruled
by Sunny; build authorized, sequenced BEFORE the demo recording.
**Origin:** Walk 1562 (WALK_VERDICTS_1562.md Q5/Q6 corpses, find W8);
Sunny's directive: governance over thousands of SQL files must check
misnomers and conflicting/duplicated definitions SYSTEMATICALLY.
**Rulings already made (Sunny, 2026-08-23, recorded here):**
plurality of definitions is legitimate (citizen stewardship);
official status is steward-certified; variant LABELING ships in the
enterprise layer now, personal-scoped variants stay behind the
ADR 0038 access-control gate.
**Ratifications (Sunny, 2026-08-23, second session):** (a) taxonomy +
severity boundary table APPROVED as enumerated below; (b) certify
authority = STEWARDS (steward role via Entra ID ownership); (c)
reason string MANDATORY on accept/retire dispositions; (d)
sequencing = BUILD BEFORE THE DEMO RECORDING (the estate-wide
red-flags moment goes on camera).

## First principles

1. **Names are claims; parsed logic is truth.** A red flag is a
   machine-detected contradiction between an identity claim (name)
   and the normalized parsed logic (content hash). Native-parser law
   applies; no text heuristics.
2. **Plurality is legitimate; ambiguity is the debt.** The sweep's
   goal is NOT one-definition-per-concept. The debt is UNLABELED
   divergence: name collisions nobody knows about, "the" definition
   answered arbitrarily, duplicates living unlinked.
   **KPI: unlabeled divergences → 0** (never "definitions merged").
3. **Scope determines severity.** A name's flag class depends on the
   scope where it claims identity: local temp-table reuse
   (#Base_Pop) = INFO ambiguity hazard (cross-proc reasoning needs
   compare); shared-scope divergence (schema objects, business
   names, certified metrics) = conflict class. (RATIFIED 2026-08-23.)
4. **A flag is a verdict, not an opinion.** Deterministic content-hash
   computation over ScriptDom-normalized fragments; replayable
   (spec:E2); NO LLM in the decision path (LLM may narrate flags,
   never decide them).
5. **A flag carries its receipts.** Members, hashes, and the drill
   query on every row (error-contract philosophy — steward
   self-serves from flag to offending SQL).
6. **Flags disclose, never gate.** No flag blocks certification, use,
   or query answering. Variants remain first-class and queryable.
7. **Total or lying.** Every swept item is clean ⊎ flagged ⊎
   excluded-with-reason; conservation asserted (ADR 0052 pattern).
   The universe is CATALOG grain (certified estate; Base_Pop = 12 at
   catalog grain, not 9 at file grain — dev's 2026-08-23 finding).

## Flag taxonomy (RATIFIED 2026-08-23)

| class | shape | example |
|---|---|---|
| misnomer | one claim, many truths — same name, divergent hashes | Base_Pop: 12 catalog steps, N distinct logics |
| duplicate | many claims, one truth — different names, same hash | copy-paste procs under new names |
| cousin conflict | near-claims, divergent truths — name-family, divergent hashes | Inpatient Sepsis Details vs (Legacy v1) vs cousins |

Severity per principle 3: INFO (local scope) vs CONFLICT (shared
scope). Dev's boundary enumeration (2026-08-23, RATIFIED):

| artifact class | identity scope | divergent hashes → |
|---|---|---|
| temp-table / CTE step name (#Base_Pop) | proc-local | INFO — ambiguity hazard; cross-proc reasoning must compare |
| schema object name (table/view/proc) | shared (schema) | CONFLICT |
| business name (canonical layer) | shared (catalog) | CONFLICT |
| certified metric name | shared (catalog) | CONFLICT |
| near-name family (cousins, token-overlap) | shared | CONFLICT when hashes diverge; INFO when aligned (naming-hygiene only) |

Duplicates (same hash, different names) are INFO at every scope —
nothing contradicts; the debt is the missing `duplicate_of` link.

## Disposition model — the citizen-stewardship workflow (RATIFIED 2026-08-23)

A flag persists until logic changes (rerun) or a disposition is
recorded. Dispositions are APPEND-ONLY events (ADR 0023 discipline):

- **certify** — steward marks one variant OFFICIAL for a scope.
  Authority: STEWARDS — steward role via Entra ID ownership
  (RATIFIED 2026-08-23).
- **label-variant** — divergence is intentional: gains owner, scope
  (team/purpose; PERSONAL scope deferred to 0038), and a typed
  `variant_of` link to the official.
- **retire** — true duplicate/dead copy: `supersedes` /
  `duplicate_of` link, superseded status.
- **accept** — flagged, ruled intentional, closed; never re-flagged
  (precedent: the Screening Trend URL ruling). Reason string
  MANDATORY on accept/retire (RATIFIED 2026-08-23).

The flag queue IS the stewardship inbox — ranked by blast radius
(readers + reports from existing lineage) now; usage weight later
(flywheel application half, out of scope here).

## Graph & store additions

- Typed edges: `variant_of`, `supersedes`, `duplicate_of`.
- Node property: official-for-scope (steward, timestamp, scope).
- `gov_red_flags` table: flag id, class, severity, scope, members
  (refs + hashes), blast radius, drill query, disposition state.
- Reachability rows (ADR 0052) for every new payload; totality test
  will force them before CI passes.

## §3b answers (dev, 2026-08-23)

1. **Inventory.** v1 sweeps two artifact classes at catalog grain:
   (a) transformation steps — every `transform:` node, grouped by
   case-folded, underscore/space-folded name; (b) canonical metrics —
   every `canonical:` node, grouped by business name and by
   near-name token family (the existing containment tokenization, no
   new lexicon). Hash provenance: the compare kernel's normalized
   content key (`_content_key`, ADR 0036 — ScriptDom-normalized
   fragment) IMPORTED, never re-implemented; a step with no stored
   fragment is excluded-with-reason `no_fragment`. The sweep is a
   pure read over graph_nodes — no new parse.
2. **Conservation.** swept_total = transform census + metric census
   (the ADR 0052 count oracles); every swept item lands in exactly
   one of clean ⊎ flagged ⊎ excluded(reason ∈ {no_fragment,
   unparsed}); the notebook asserts the partition sums and the live
   audit re-asserts it against the store on every run.
3. **Drift.** CI leg: flag-class and disposition-state enums pinned
   by L0 tests (adding a class/state without tests fails CI); the
   generated walk section regenerates from the registry rows. Live
   leg: reachability_audit gains a gov_red_flags leg — totals
   reconcile with the conservation partition, zero dispositions
   referencing absent flags, zero flags whose member node_ids have
   vanished from graph_nodes.

## Surfaces

1. Pipeline: numbered notebook per the contract; deterministic;
   PHI gate on any surfaced expression text.
2. Agent: flags readable via named ops (census kind 'flag', retrieve
   flag record); sameness/identity answers become single-row verdict
   reads (ADR 0020 — the systematic close of walk find W6);
   "how is X defined" answers official-first with a variants-exist
   stamp.
3. Admin dashboard: red-flags tile with trend (unlabeled → 0).
4. Fabric agent export: flag surface per ADR 0020 doctrine.

## Acceptance (project law)

- Real ED-sepsis-corpus flag output for Sunny's gap-check BEFORE any
  surface ships.
- Suite: sameness family reads flag verdicts; new `flags` family
  (store-derived oracles).
- Walk: a flags section (SMARTNESS_WALK addition).
- Demo: one QA-gate question ("what governance red flags exist?") —
  candidate estate-wide upgrade of the VO-4 drift beat.

## Out of scope (recorded, not decided)

- Personal-scope variants and per-user certified definitions
  (ADR 0038, build-gated).
- Usage-weighted flag ranking (flywheel application half).
- Any merge/consolidation tooling — this ADR labels; it never merges.
- Write-back of dispositions to Purview/Collibra (future; the
  gov_usage_events transport-swap pattern applies).

## Ratification checklist — ALL RESOLVED (Sunny, 2026-08-23)

1. Taxonomy + severity boundary table — APPROVED as enumerated.
2. Certify authority — STEWARDS (steward role, Entra ID ownership).
3. Disposition closing rules — reason string MANDATORY on
   accept/retire.
4. Sequencing — BUILD BEFORE THE DEMO RECORDING.
