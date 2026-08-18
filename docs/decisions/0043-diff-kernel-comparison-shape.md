# 0043 — The diff kernel: the founding question gets its shape

**Status:** Accepted
**Date:** 2026-08-18

## Context

The Question Map (Layer 0 approved 2026-08-18) named family F —
"are these definitions the same? WHY do A and B disagree?" — as the
founding demo question and the least-served answer shape. The data was
ready (step-grain fragments ARE the aligned decomposition a diff
needs); the existing partition kernel could say THAT two metrics
differ, but nothing could say WHERE. Shape-specific tools (compare_*)
are correctly banned by the methodology tests, so the answer had to be
a generic kernel composing with the algebra. Field grounding: 25
same-name proc pairs at a live estate (2026-08-17), 16 of them
cross-schema twins with DIFFERENT code.

## Decision

1. **The kernel** (`src/graph/decomposition_diff.py`): deterministic
   step alignment over N metric decompositions — folded NAME first,
   then identical fragment CONTENT (renamed-but-identical steps match),
   then TABLE-SET Jaccard (≥ 0.5) where table sets are known. Aligned
   pairs report fragment identity (whitespace/case forgiven — the same
   forgiveness as the partition kernel, so the two can never disagree
   on "identical"), per-step table divergence, and a capped unified
   fragment diff. Unmatched steps are findings. N-way = pairwise
   against an explicit base. The LLM captions; it never judges
   equivalence — the kernel's output IS the evidence (ADR 0032).
2. **Algebra surface**: a fourth compare kernel in `op_compare`
   (aspect `steps`). METHODOLOGY AMENDMENT, made loudly per the
   amendment rule: `op_compare`'s justification now reads four data
   types (text bodies, sets, scalars, ordered step sequences) and
   `steps` joins SYSTEM_VOCAB — approved via HANDOFF_COMPARISON_SHAPE
   (Question Map gap 1) and Sunny's go-ahead on the implementation
   order, 2026-08-18. Composition: search → retrieve×N → compare(steps).
3. **Doctrine level 3 precomputation**: `output_metric_twins` —
   same-bare-name groups (the hot comparison) get a cached kernel
   verdict (identical | divergent, divergent/missing step counts, a
   deterministic summary), recomputed on every 04 run. Verifiable
   cache of the kernel, never a per-question answer table.
4. **Agent surface**: instructions teach twin-cache-first for sameness
   questions, verbatim verdict reporting, and the sameness-claim rule
   (only a kernel verdict or identical logic supports "the same").

## Consequences

- The founding demo question is answerable with localized evidence:
  which step, which filter, which tables.
- Acceptance fixtures mirror the field corpus (cross-schema twins with
  a differing age filter, missing exclusion steps, renamed identical
  steps, rewritten same-source steps).
- The ops-layer kernel aligns by name/content today; per-step table
  alignment there arrives with op_traverse (ADR 0037) — the pure
  kernel already supports it, and 04's twin cache uses it in full.
