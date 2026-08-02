# ADR 0005: Agent Refuses When No Certified Path Exists

**Status:** Accepted
**Date:** 2026-07 (recorded 2026-08-02)

## Context

When a user asks about a metric with no certified graph path, the agent could
attempt a best-effort answer (like a generic LLM) or decline.

## Decision

The agent says "I don't have a certified definition for that yet," notifies the
data steward, and still checks Purview for existing reports that may help. It
never guesses.

## Consequences

- In healthcare, a wrong answer is worse than no answer — the graph is the guardrail
- Every refusal feeds the flywheel: the question is logged with asker, time, and
  frequency, becoming the steward's prioritized certification queue
- Early deployments see many Path B ("don't know") responses; coverage grows with
  usage rather than upfront committee work
