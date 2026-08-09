# 0032 — Deterministic Core, LLM Edges

**Status:** Accepted
**Date:** 2026-08-09

> The LLM translates. The data answers. The human decides.

## Context

Both agents failed the same first-principles test on 2026-08-09, in
opposite directions: asked a topic-grain question ("how is our sepsis
population defined?"), the Delta agent **blended** 28 different
certified definitions into one authoritative-sounding answer, and the
Graph agent **cherry-picked** one of three resolved candidates (a
compliance tracker, arguably the worst fit) and crowned it — then, on a
one-word rephrase, changed its pipeline shape entirely. A week of
instruction fixes (two collisions with the 15,000-char cap) confirmed
the whack-a-mole diagnosis: the stochastic generator still owned the
three decisions that define the product — what to retrieve, how to
rank, how to present.

The architecture that resolves this was not invented here: Sunny
arrived at it through months of tier-2 trial and error before this
repo existed — LLM strictly as translator, vector search over all
layers' descriptions, threshold + rank, and **the human picks**. This
ADR writes that model into the record as the product architecture.

## Decision

**The boundary is defined by three typed LLM touchpoints; everything
between them is replayable code.**

1. **`translate(question) → search_phrase`** (entry edge): the LLM's
   entire output is one string. It never sees schema, catalog, or
   threshold. A poor translation degrades ranking, never correctness.
2. **The deterministic core** — no LLM tokens inside:
   - `embed(phrase)`: pinned embedding model, no sampling;
   - similarity over the semantic catalog spanning **all three
     layers** (metrics, calculation steps, technical tables — plus
     business terms when present);
   - threshold θ from config, never from a prompt;
   - rank by closeness, ties broken deterministically (node_id);
   - **present ALL candidates** through a fixed render template —
     names, descriptions, closeness (relative, never a probability),
     certification status, weight when the flywheel captures;
   - **the human picks — no bypass.** One candidate is presented for
     a pick exactly like ten (Sunny, 2026-08-09: "one candidate is
     treated the same as multiple; no LLM decision whatsoever").
     Uniformity eliminates every conditional path a heuristic could
     hide in;
   - pick validation is structural: the choice must be one of the K
     shown, enforced by code;
   - `assemble(ref)`: fixed lookups per kind — metric → its
     output_metric_logic row; step → its node + parent metric;
     table → dictionary entry + closure-table readers. No free query
     exists in the core.
3. **`interpret_pick(reply, candidates) → index`** (chat surfaces
   only; a click in a real UI): LLM output validated against the
   candidate set — it can produce one of K or "none", nothing else.
4. **`narrate(fact_set) → prose`** (exit edge): the LLM receives only
   assembled facts and may add only language. **Provenance (the Basis
   line) is stamped by the orchestrator, never written by the LLM** —
   closing the lying-footer defect class permanently.

**The testable definition of deterministic:** same phrase + same
catalog state ⇒ byte-identical candidate set, order, and facts. This
replay property goes into CI; "battle-tested" becomes mechanical
(5-rule gate).

**Resolution IS the flywheel's capture surface:** the human's pick is
simultaneously disambiguation and an endorsement signal
(ADR 0023/0031). Plurality is never collapsed by a machine — it is
presented, and usage ranks it over time (ADR 0021/0024).

## Consequences

- **Runtime implication (the honest one):** the Fabric Data Agent's
  query generator is an LLM making retrieval decisions by
  construction — on that surface the line is DOTTED (shrinkable via
  function-only schemas and fixed lookups; enforceable only
  statistically, measured by the paraphrase-robustness suite). The
  line is SOLID only in AIVIA's own orchestration surface (MCP
  client + agent harness + llm_client + resolve function — largely
  already built), where the LLM has no tools beyond the three
  touchpoints. The Fabric agent becomes a consumer surface and
  distribution channel, not the product's spine. Runtime pivot
  pending Sunny's explicit confirmation.
- The instruction files shrink to invariants + touchpoint guidance;
  the question-template casebook (the whack-a-mole surface) is
  deleted where the orchestrator runs.
- The demo's "surprise question" beat (a third party generates a
  question live on camera) becomes safe by design: the robustness
  suite is the same distribution at scale, offline, passed before
  recording. Either outcome — certified answer or honest refusal —
  demonstrates the architecture.
- Readiness gate (hard rule, 2026-08-09) sequences everything:
  answer contracts → instruction diet → robustness suite pass →
  demo (with deliberate on-camera deviation) → listing.
