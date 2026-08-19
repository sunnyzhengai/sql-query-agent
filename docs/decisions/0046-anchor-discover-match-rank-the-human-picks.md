# 0046 — Query composition: anchor, discover, match, rank — the human picks their reality

**Status:** Accepted (settled in live debate, Sunny + dev session, 2026-08-19)
**Date:** 2026-08-19

## Context

The tree contract ([0044](0044-tree-contract-round-trip-descriptions.md))
reopened the question of how queries get composed from the graph. The
debate arc, compressed: "pre-written templates" was rejected (coverage
by enumeration is impossible — you can't pre-define all shapes of user
questions); "the LLM composes a plan from typed primitives" was
rejected next (Sunny: when you know the anchored nodes, the paths are
facts waiting to be discovered — the technical layer is the vendor
dictionary's complete join map; anything that can be joined is known
by this map). What survived scrutiny: path *generation* is fully
deterministic; the only real choices are (a) which discovered meaning
the user intends, and (b) what filter content means in codes — and
both already have owners. The 2026-08-09 agent failures (ADR
[0032](0032-deterministic-core-llm-edges.md)) remain the boundary
condition: a stochastic generator must never author retrieval logic at
ask time, in SQL, GQL, or any other syntax.

## Decision

### The three realities (provenance is the product)

- **Technical layer = the vendor's reality** (e.g. Epic Clarity's
  dictionary): every table, column, and joinable edge — the complete
  map of what CAN join.
- **Certified shapes = the organization's reality**: transformation
  trees and decision sites that stewards certified
  ([0021](0021-certification-discloses-never-gates.md)).
- **Used-but-uncertified shapes = users' realities**: shapes real
  people chose and ran — citizen stewardship, usage as governance
  ([0023](0023-usage-weighted-governance-flywheel.md),
  [0024](0024-layered-truth-personal-and-enterprise.md)).

### The composition pipeline

1. **LLM anchors** tokens to graph entities — closed vocabulary,
   ranked candidates, the resolve step of
   [0017](0017-resolve-then-traverse-agent-retrieval.md). This is the
   LLM's ONLY structural role. It never authors syntax, never chooses
   a path.
2. **Two deterministic engines ALWAYS both run** over the anchors:
   - **Shape matching**: stored shapes (transformation trees, decision
     sites) that contain the anchor set — partial containment allowed;
     shapes with detour paths are candidates too, presented with their
     evidence, never discarded by default.
   - **Path discovery**: graph search over the technical map. Runs
     unconditionally — if discovery only ran on shape-match miss,
     novelty could never beat history. Direction is meaning: mirror
     paths (Encounter→Referral vs Referral→Encounter) are distinct
     candidates with distinct captions, never deduplicated.
3. **Ranking**: the shape corpus is discovery's cost function — edges
   that certified reports traverse constantly rank cheap; never-used
   edges rank expensive (this tames hub explosion through the
   patient/encounter hubs: absurd-but-real paths surface last, not
   first). Ranking PRESENTS, never prunes; a capped list discloses
   the cap (the funnel doctrine applied to retrieval).
4. **Presentation**: one merged list, grouped by reality layer —
   organization's reality, then users' realities, then
   vendor's-reality novel paths badged "no usage evidence" — with
   plain-language captions describing the POPULATION each path
   means ("patients with diabetes on the active problem list" vs
   "patients ever coded diabetic at an encounter"), not query text.
5. **The human picks. Always.** No auto-pick at rank 1; no bypass
   with a single candidate (reaffirms 0032 in its strongest form —
   even one edge carries two meanings, so no case is unambiguous
   enough for the machine to decide a human's reality).
6. **The pick persists**: a chosen novel shape is written to the
   graph and linked to the picker by an edge — it becomes that user's
   reality (the `gov_personal_definitions` draft gains its precise
   semantics: the pick IS the write) and enters the usage flywheel
   from day one.

### Grounding rules that ride along

- **Filter content** (which codes mean "diabetic") comes ONLY from
  stored decision sites, value-set tables, or the human — never from
  model memory (the 123/456 lesson).
- **Qualifying predicates travel with shapes** (fan-out control:
  line-table `LINE` filters, latest-row window patterns). The schema
  map knows the edge; only real reports' decision sites know the
  qualifier that makes the edge business-correct. A raw-map path
  arrives without qualifiers and is badged as such.

### One engine, both tiers

The metadata tier implements this whole pipeline — its questions are
already shape-ranked, human-picked traversals. The Pro/self-service
tier adds exactly ONE layer: assembling executable SQL from the
certified pieces of the picked shape
([0003](0003-sql-fragments-not-full-sql.md) fragments +
[0044](0044-tree-contract-round-trip-descriptions.md) decision trees).
Building a separate engine for Pro would be two paths for one goal —
banned. Sequencing: tree phase 1b first (decision→column edges are
what shape matching matches against), then this engine lands in the
metadata tier.

## Consequences

- The LLM's blast radius shrinks to translation at the two edges
  (tokens in, captions out) — tighter than
  [0032](0032-deterministic-core-llm-edges.md) itself stated.
- Fabrication has no seat: paths exist in the map or they don't;
  filters come from stored artifacts or a human.
- Governance emerges from use: every pick is provenance, every
  persisted user shape is a certification candidate, and the ranked
  presentation IS the disclosure.
- Cost accepted: always running both engines costs compute on every
  question, and human-picks-always costs a click even on "obvious"
  answers — both are the price of never deciding a user's reality
  for them.
- The canonical worked example for onboarding and docs: "who are the
  diabetic patients?" — anchors patient/diagnosis/diabetic; discovery
  surfaces problem-list vs encounter vs ED paths (all real, all
  different populations); shapes rank them by organizational usage;
  the human picks which population is THEIR question.
