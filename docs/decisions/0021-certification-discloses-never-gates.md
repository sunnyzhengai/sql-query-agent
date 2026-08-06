# 0021 — Certification discloses trust; it never gates availability

**Status:** Accepted
**Date:** 2026-08-06

## Context

ADR 0004 defined two-stage certification (developer, then steward) and ADR
0005 defined refusal when no certified path exists. Read together they imply
a gate: an uncertified metric is invisible until two humans sign off. The
ROADMAP's steward backlog flags the missing lifecycle ("biggest remaining
product gap"), and the design input for this pass settles the philosophy:

> Stewards are bottlenecks if made mandatory. All metrics are available
> immediately; certification is a quality signal the agent discloses, never
> a gate that hides metrics. Usage IS governance.

The failure mode we are designing against is real and well documented in
enterprise catalogs: certification-gated systems launch empty, users route
around them, and the steward queue becomes a graveyard. The system must be
useful on day one with zero certified metrics and zero assigned stewards —
and get *better*, not merely bigger, as usage accumulates.

## Decision

**Availability and trust are separate axes. Certification moves trust only.**

1. Every metric that parses into the graph is answerable immediately, in
   `draft` state. No certification state hides, filters, or delays a metric.
2. Every answer **discloses** the trust context of what it used: the
   certification state, the accountable people if assigned (steward,
   developer), definition freshness (ADR 0022), and usage weight (ADR 0023).
   Uncertified is a label, not a lock.
3. **ADR 0005's refusal is reinterpreted about existence, not certification:**
   the agent refuses when no graph path exists at all — it never fabricates.
   When a path exists but is uncertified, the agent answers *with
   disclosure*. ADR 0005 stays in force for what it was actually protecting
   against: invented metrics, invented logic.
4. Stewards still govern — certification remains a first-class state with
   named accountability (ADR 0004 unchanged for *how* certification
   happens) — but nothing in the product is *reliant* on a steward acting.
   Steward inaction degrades trust labels, never availability.

This ADR is the constitution for the governance lifecycle: any future
feature that would make an answer conditional on a human approval step must
either be reframed as disclosure or get its own ADR superseding this one.

## Consequences

- Day-one utility: a fresh install answers from `draft` metrics with honest
  labels; certification coverage grows along the usage-weighted queue
  (ADR 0023) instead of blocking launch.
- The agent's grounding instructions and answer templates must carry the
  disclosure fields — `certification_status` (and companions) join
  `output_metric_logic` so the agent can see them (contract drafts:
  `gov_certification_events`, planned columns in ADR 0022/0023).
- A wrong-but-plausible draft answer is now possible where a gate would
  have refused. Mitigation is layered: disclosure ("draft — not yet
  reviewed"), answer feedback feeding the flywheel (ADR 0023), and
  healthcare deployments can *choose* a stricter posture via configuration
  — but strict mode is a customer override, not the product default.
- Certification-gated competitors' emptiness is our wedge: this composes
  with the usage flywheel to make governance a byproduct of use.
