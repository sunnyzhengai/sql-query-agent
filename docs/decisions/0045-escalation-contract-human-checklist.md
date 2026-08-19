# 0045 — The escalation contract: no silent residue; unresolved outcomes become the human checklist

**Status:** Accepted (contract locked before implementation; gated in `tests/test_escalation_contract.py`)
**Date:** 2026-08-19

## Context

Sunny, verbatim in substance: "we need HITL for every decision we made
so far. No silent failing — always bring the human in if the result of
a step is not something the LLM or our Python code can resolve. E.g. if
there's a new SQL shape we didn't know before, add it to the human's
checklist."

The pipeline already *counts* what it cannot resolve — parse
suppressions, the M shape census's `unknown` signatures, grounding
rejections, dynamic SQL (permanently unparseable, per
[ADR 0044](0044-tree-contract-round-trip-descriptions.md)) — and lands
much of it in `ops_fallout`. But counted is not the same as *owned*: a
funnel bar the admin never clicks is silence with extra steps. Nothing
today guarantees that an unresolvable outcome reaches a human with a
name, a reason, and a place to mark it handled. This is the HITL
principle ([ADR 0004](0004-two-stage-hitl-certification.md), the human
picks in [ADR 0032](0032-deterministic-core-llm-edges.md)) extended
from *answers* to *operations*: when code and LLM are both out of
authority, the human is the resolver of record — Operations Are The
Product ([ADR 0036](0036-operations-are-the-product.md)).

## Decision

Four clauses, mechanically enforced by `tests/test_escalation_contract.py`
(strict-xfail skeletons until implemented — the ADR 0044 gating pattern):

1. **Terminal-state law.** Every `ops_fallout` row carries
   `resolution ∈ {auto_resolved, escalated}` — no third state, no NULL.
   Code that writes fallout must declare, at write time, whether the
   pipeline itself recovers (retry succeeded, replan covers it) or a
   human must act. Undeclared residue fails CI at the writer.
2. **The checklist is a query, not a vibe.** The human checklist is
   `ops_human_checklist`: escalated rows not yet marked done, one row
   per (entity, reason_code), carrying stage, reason text, first-seen
   and last-seen run_at, and a `status ∈ {open, acknowledged, resolved}`
   the admin updates. It joins the admin journey dashboard as its own
   page (RUNBOOK_JOURNEY_DASHBOARD gains the visual when this ships);
   the dashboard still computes nothing.
3. **Novelty always escalates.** Any classifier outcome meaning "we
   have not seen this before" — a census `unknown` M shape, an
   unmodeled SQL construct in the tree's `unextracted` bucket, dynamic
   SQL, a round-trip description that exhausted its bounces
   (`provenance = flagged`) — MUST produce an escalated row. Novelty is
   precisely the case where neither code nor LLM has authority; it is
   never allowed to be only a counter. (Repeats across customers are
   the product-signal channel, per the error-contract philosophy —
   [ADR 0039](0039-errors-link-to-contracts.md).)
4. **Escalations cite their contract.** Every escalated row links the
   failed contract id (the 0039 pattern), so the admin self-serves the
   "what do I do with this?" question from the row itself — supportable
   at a distance.

## Consequences

- "Did anything need me?" becomes one query and one dashboard page;
  an empty checklist is a *verified* all-clear, not an absence of news.
- New-shape discoveries stop dying in run logs: the checklist is the
  intake funnel for parser/census/tree coverage work, ranked by how
  often customers hit each unknown.
- Cost accepted: every fallout writer takes a mandatory resolution
  argument — friction at write time, by design; the declaration IS the
  review.
