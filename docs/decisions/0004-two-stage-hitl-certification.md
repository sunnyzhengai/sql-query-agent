# ADR 0004: Two-Stage Human-in-the-Loop Certification

**Status:** Accepted
**Date:** 2026-07 (recorded 2026-08-02)

## Context

Healthcare analytics requires 100% accuracy. Technical correctness (does the SQL
compute what it claims?) and business correctness (is this the right definition
of the metric?) are different competencies held by different people.

## Decision

A metric enters the certified graph only after two independent sign-offs:
1. **Developer review** — the parsed SQL logic is technically correct
2. **Steward review** — the definition is the right one for enterprise use

## Consequences

- Certified answers carry named accountability (steward + developer on the node)
- Certification throughput is bounded by human reviewers — mitigated by the
  usage-weight flywheel, which prioritizes the queue by actual demand
- The Data Agent can be configured to answer only from certified paths (ADR 0005)
