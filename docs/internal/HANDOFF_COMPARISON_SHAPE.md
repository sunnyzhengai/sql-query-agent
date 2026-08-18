# Handoff — the comparison shape: a diff kernel for the founding question

**From:** review session, 2026-08-18 (Question Map derivation; Layer 0
approved). **To:** dev session. See docs/architecture/QUESTION_MAP.md,
gap 1.

## Finding

Family F ("are these definitions the same? why do A and B disagree?") is
the founding demo question and the least-served answer shape. The DATA is
ready — step-grain fragments are exactly the aligned decomposition a diff
needs — but no primitive composes them into a diff, and shape-specific
tools (compare_*) are correctly banned by the methodology tests.

## Wanted (doctrine-compliant per ADR 0037)

1. A generic **diff kernel** primitive: given two (or N) metric
   decompositions (ordered steps: name, fragment, tables, filters),
   return aligned pairs + divergences (missing steps, differing
   fragments/filter criteria, differing source tables). Deterministic;
   composes as search -> retrieve xN -> diff; the LLM captions the
   result (ADR 0032: it never judges equivalence itself — the kernel's
   output IS the evidence).
2. Alignment strategy: match steps by name first, then by table-set
   similarity; unmatched steps are themselves findings.
3. Field fixture: the 2026-08-17 work finding of 25 same-name proc pairs
   (16 cross-schema twins with DIFFERENT code) is the natural acceptance
   corpus — anonymized equivalents exist in the golden fixtures' spirit;
   build fixtures shaped like them.
4. Surface: available to the orchestrator algebra AND summarized into a
   precomputable card-adjacent view where hot (e.g., same-bare-name
   groups get a cached divergence summary — cache of the kernel, per
   doctrine level 3).
