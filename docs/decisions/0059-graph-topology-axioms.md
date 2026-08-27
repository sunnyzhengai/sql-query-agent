# ADR 0059 — The graph topology axioms: connected, sound, complete

**Status:** ACCEPTED 2026-08-26 — G1–G3 RATIFIED by Sunny; the four
provenance classes RATIFIED; item 3 resolved by the FOUNDATION
EXCEPTION (below). The axioms join Φ_AIVIA per the amendment rule;
mechanization (SPEC text + CI legs + 300 postconditions) is dev's.

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

## Rulings (Sunny, 2026-08-26)

1. G1–G3 RATIFIED as stated.
2. The four provenance classes RATIFIED (parsed / declared /
   derived / asserted; future catalog imports = declared unless an
   ADR says otherwise).
3. **THE FOUNDATION EXCEPTION (supersedes the question as asked):**
   the dictionary is a SOURCE OF TRUTH — foundation nodes exist AS
   IS, justified by the dictionary itself, whether or not any
   transformation reads them. G1's principal-component requirement
   applies to the DERIVED layers only (org, canonical, governance —
   where disconnection genuinely signals a defect); foundation is
   exempt: its required connectivity is internal (table→columns
   always; table→table when declared join topology is ingested),
   its islands are LEGITIMATE STATES — enumerated by the audit for
   visibility, never findings, never queue entries, never flags.
   In the real EMR most tables ARE connected; foundation will
   largely be one fabric with legitimate cluster-islands inside.
