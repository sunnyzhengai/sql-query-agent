# ADR 0059 — The graph topology axioms: connected, sound, complete

**Status:** DRAFT 2026-08-26 — Sunny's directive ("everything is
connected, and connections are sound and complete, should be formal
specifications"); measured before drafted; Sunny ratifies, then the
axioms join Φ_AIVIA (per the amendment rule).

**The measurement (2026-08-26, full local build over the recorded
corpus, current builder incl. the folded sweep):** 6,669 nodes /
14,994 edges across 5 layers; **components = 1; degree-0 nodes = 0;
dangling edges = 0**; all 79 dictionary tables materialized (+3,946
columns). "Everything is connected" is TRUE today, verified by
union-find, not assumed.

## Axiom G1 — Accounted connectivity ("one sphere")

The graph's undirected components are ENUMERATED every build; every
component is either (a) the principal component, or (b) carries a
TYPED isolation reason (e.g., `foundation_unreferenced` — a
sovereign-dictionary table no SQL reads yet, awaiting join topology
or first reader; or a declared exclusion class). Degree-0 nodes are
forbidden outright (an unconnectable node may not be minted — it
must at minimum connect within its own layer, e.g., table→columns).
- Today's asserted state: 1 component, 0 orphans, empty isolation
  list. The axiom's form anticipates sovereign foundation WITHOUT
  weakening today's stronger truth.
- NOT "one component forever": that would make honest foundation
  growth a violation. Conservation over connectivity:
  connected ⊎ isolated-with-reason. Total or lying.

## Axiom G2 — Edge soundness

Every edge: (a) REFERENTIAL — both endpoints exist as nodes
(measured: 0 dangling); (b) PROVENANCED — carries exactly one
provenance class: `parsed` (from ScriptDom/TMDL evidence, source
recoverable), `declared` (dictionary/config), `derived`
(deterministic build computation: closures, clusters, projections —
recomputable byte-identically), or `asserted` (human testimony, ADR
0056 — typed, append-only, never masquerading as the other three).
No edge without a class; no class outside these four.
- Gap to close at build: provenance is currently implicit in
  edge_type; G2 makes it an explicit, CI-checkable column/mapping
  (every edge_type maps to exactly one provenance class in a
  registry — 0052 pattern).

## Axiom G3 — Relative completeness

Completeness is PROVEN relative to declared extractors, never
claimed absolutely: every extraction contract's conservation holds
(refs = minted ⊎ dropped-with-reason; steps ⊎ terminals; sweep's
swept = flagged ⊎ clean ⊎ excluded; cluster/matrix totality;
reachability 0052), and every boundary is disclosed at ask time
(coverage-absent stamps, declared-incomplete legs). A completeness
claim without a conservation equation behind it is forbidden.

## Enforcement (the Echo Law's build-first default applies)

1. **CI leg (local):** the recorded-corpus build asserts G1 numbers
   (components/orphans/dangling + the isolation list), G2 mapping
   totality, G3 conservation sums — the union-find audit becomes a
   permanent test, not a one-off probe.
2. **Live-audit leg (tenant):** reachability_audit gains a topology
   leg computing the same over the store; red on any unaccounted
   island, dangling edge, or unmapped edge_type.
3. **Timing:** dev is currently INSIDE the 300 fold (single writer)
   — G1/G2-referential assertions belong in 300's postconditions
   NOW, in the same order, not as a follow-up (build the mechanism
   at the first opportunity, not after the first failure).

## PARKED for Sunny

1. Ratify G1–G3 as stated (then they join SPEC beside reachability
   and translatability, one ADR-recorded amendment).
2. G2's provenance registry: ratify the four classes.
3. Whether `foundation_unreferenced` islands should ALSO surface as
   a differentiation-queue entry ("tables nobody reads") or stay
   audit-only until sovereign foundation ships.
