# ADR 0038: The Interaction Layer — "No" Is Input, Users Enter the Graph

**Status:** Accepted (design approved by Sunny, 2026-08-13); the
user-centric build is GATED on the access-control ADR (below)
**Date:** 2026-08-13

## Context

Two of Sunny's realizations (2026-08-13): every human interaction is
training material and must be recorded IN THE GRAPH, traced from
question through every step to verdict, with errors tied to data
(extending ADR 0026); and the product must not stop at "this is not
what I needed" — it must continue: elicit, guide, and let the user
CREATE, turning rejection into supply. Plus the topology insight: with
user→definition edges as first-class structure, the graph matures from
SQL-centric (an index of code) to human-centric (the organization's
semantic memory with its people in it).

Both are pure SCHEMA growth — new node and edge kinds operated on by
the existing four primitives. The algebra is untouched: first evidence
of its practical completeness.

## Decision

### 1. The usage layer of the graph

New node kinds in a distinct layer (never mixed into certified-content
retrieval): **Conversation**, **Turn** (confirmed plan, ops run,
result refs), **Verdict** (accept/reject, who, when). Edges:
Turn —about→ touched metric/step nodes (derived mechanically from plan
ids); Verdict —on→ Turn; Verdict —implicates→ data or decision shape
(ADR 0026 extended to conversations). Accepts are recorded with equal
weight to rejections and feed usage weights (ADR 0023).

Discipline: the append-only event stream (gov_turn_events /
gov_feedback_events) remains ground truth; ALL graph edges in this
layer are rebuildable projections of events — the graph can never
drift from the record that justifies it.

### 2. The continuation loop — the three-way taxonomy of "no"

Every rejection is exactly one of: (a) translation error → telemetry +
suite fixture; (b) missing knowledge → demand signal (most-wanted
queue, ADR 0023); (c) missing DEFINITION → the creation flow:

1. LLM elicits conversationally — UNSCRIPTED (a predefined question
   tree is pattern predefinition; elicitation is translation, the
   LLM's lane).
2. Capture is an `update` operation, always plan-confirmed: create a
   definition node — content (hash-versioned, ADR 0022), author
   (Entra identity), status `proposed_by_user`, provenance edges to
   the birthing conversation (question, rejected candidates,
   elicitation turns).
3. The kernels midwife the birth: compare the proposal against the
   nearest existing definitions/concept family — "yours differs from
   X in exactly this" — sharpening proposals and catching
   almost-matches before creating duplicates.
4. Existing lifecycle machinery takes over untouched: personal-layer
   visibility at once (ADR 0024), steward queue by demand weight
   (0023), disclosure-never-gating (0021), certification pins a
   version (0022).

This is the flywheel's ignition: new truth enters governance at the
moment of demonstrated need, authored by the person who needed it,
provenance-complete from birth.

### 3. Users and concepts as first-class topology

- **user —PROPOSED→ definition**: authorship as structure, born at
  creation with conversation provenance.
- **user —USES→ definition/metric**: DERIVED, never asserted —
  materialized from accept/endorsement events with properties
  (first_used, last_used, count). Weights become edge properties.
- **definition —DERIVED_FROM→ metric**: ancestry of elicited proposals.
- **concept** nodes ("Sepsis") with **—HAS_MEMBER→** edges to metrics/
  definitions/terms: membership PROPOSED mechanically (embedding
  closeness above a floor, listed exhaustively with scores) and
  CONFIRMED by humans — the methodology applied to ontology; status +
  closeness on every membership edge; disclosure, not gating. Concepts
  buy: comparison entry points (traverse concept → compare partition),
  drift-monitoring scope, demand roll-up, and a smarter elicitation
  midwife. Node-kind ceiling: metric / definition / term / concept —
  four; stewards merge rather than we pre-engineer distinctions.

### 4. THE GATE: access control before any user-centric data

Sunny, 2026-08-13: layer visibility "is the first question any
healthcare buyer would ask." Ruling: **the user-centric layer
(PROPOSED/USES edges, personal definitions, per-user telemetry views)
is NOT BUILT until a dedicated access-control ADR defines**: who sees
whose usage (individuals: own subgraph; stewards: aggregates; admins:
configurable), how personal definitions are scoped (ADR 0024 layering
enforced at the query layer, not by convention), retention/erasure of
per-user events (right-to-be-forgotten vs append-only — resolution
required, e.g. crypto-erasure or pseudonymization at ingest), and how
Entra groups map to layer permissions. This ADR is a prerequisite for
the pro tier connecting to ANY customer data. Access control is
designed before data arrives, never retrofitted.

## Consequences

- Interaction recording (events) already ships; the graph projection,
  creation flow, user/concept topology follow the release-scoping
  rule and the access-control gate.
- The robustness suite gains fixtures automatically from real rejected
  conversations (provenance-linked).
- The whitepaper gains the access-control-by-design story — a selling
  point, not a compliance chore.
