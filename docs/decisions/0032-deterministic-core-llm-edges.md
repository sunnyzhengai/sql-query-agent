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

**The boundary is defined by TWO typed LLM touchpoints; everything
between them is replayable code.** (Amended 2026-08-09 same day: the
pick-interpretation touchpoint is eliminated — picks are structural.)

1. **Entry edge — the LLM produces the search token** (Sunny's term):
   its entire output is one string. It never sees schema, catalog, or
   threshold. A poor token degrades ranking, never correctness.
2. **The deterministic core** — no LLM tokens inside:
   - `embed(phrase)`: pinned embedding model, no sampling;
   - **one fixed command, every time**: semantic_search(<token>) —
     the token is a parameter plugged into an immutable function body;
     no query is ever constructed at ask time. Closeness falls out of
     the vector math — nothing scores at runtime;
   - **Tier-1 search space: metric + transformation descriptions only**
     (+ business terms when present — concept grain). Table/column
     descriptions are deliberately excluded: users ask about concepts,
     not objects; object-grain search joins in Tier 2/Pro (Sunny,
     2026-08-09);
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
3. **Picks are structural, not an LLM touchpoint**: in a UI the click
   IS the pick; in chat, candidates are numbered and a number or exact
   name is parsed by code (regex + case-folded match; re-prompt on
   failure). An OPTIONAL LLM fallback may map a fuzzy reply ("the ED
   one") onto the candidate set, validated so it can only yield one of
   K or none — a UX convenience, never architecture.
4. **Exit edge — the LLM narrates the assembled facts**: it receives
   only the fact set and may add only language. **Provenance (the
   Basis line) is stamped by the orchestrator, never written by the
   LLM** — closing the lying-footer defect class permanently.

**The testable definition of deterministic:** same phrase + same
catalog state ⇒ byte-identical candidate set, order, and facts. This
replay property goes into CI; "battle-tested" becomes mechanical
(5-rule gate).

**Resolution IS the flywheel's capture surface:** the human's pick is
simultaneously disambiguation and an endorsement signal
(ADR 0023/0031) — and capture is ONLY possible on an owned surface:
the Fabric agent is read-only and its conversations are not exposed as
data, so a pick made in Fabric chat evaporates; in the orchestrator it
is one appended row to gov_usage_events / gov_term_endorsements
(writers the contracts have been waiting for). Plurality is never collapsed by a machine — it is
presented, and usage ranks it over time (ADR 0021/0024).

## Consequences

- **Runtime implication (the honest one):** the Fabric Data Agent's
  query generator is an LLM making retrieval decisions by
  construction — on that surface the line is DOTTED (shrinkable via
  function-only schemas and fixed lookups; enforceable only
  statistically, measured by the paraphrase-robustness suite). The
  line is SOLID only in AIVIA's own orchestration surface (MCP
  client + agent harness + llm_client + resolve function — largely
  already built), where the LLM has no tools beyond the two
  touchpoints. The Fabric agent becomes a consumer surface and
  distribution channel, not the product's spine. **Runtime pivot
  CONFIRMED by Sunny 2026-08-09** after the live baseline (hit@5
  96.7%, top1 93.3%, replay stable 7/7, p50 0.71s vs 19-47s on the
  Fabric surface): the orchestrator is the flagship experience.
  Policies set with the confirmation: the threshold is a VOLUME
  CONTROL, not a correctness gate (theta keeps lists reasonable; weak
  matches are shown with visible closeness; the human judges); sibling
  variance across paraphrases is accepted — the readiness metric is
  hit@5, not top1 agreement ("we can't predict which sibling is the
  best answer for different users").
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

## Amendment: stratified plurality (2026-08-10)

Live find: steps outnumber metrics 413:28 and sibling steps cluster in
embedding space, so the flat closeness-ranked top-10 buried every
metric but one under a single proc's branch steps — "how is ED sepsis
screening calculated" showed ED2GEN/ED2ICU/IV/ETT while ED Sepsis
(Regulatory), the second-most-relevant item in the catalog, went
unshown. Irrelevant shown + relevant hidden = a retrieval-policy
defect, not a display nit (Sunny's call).

Ranking policy amended: resolve() fetches a wide slice (top 100, still
the one fixed command) and STRATIFIES by kind in pure code — the
closest metrics (≤5) and the closest steps (≤5, max 2 per proc for
diversity), rendered as labeled groups with continuous numbering.
Closeness order within groups, node_id ties, replay property intact.
This enforces the ROADMAP Phase A "full plurality" contract at the
list level. The "Found N related items" headline is retired — at a
0.35 cosine floor over a same-domain corpus nearly everything clears
(434/441), so the floor count is context, never a relevance claim;
the honest signal is the closeness column.
