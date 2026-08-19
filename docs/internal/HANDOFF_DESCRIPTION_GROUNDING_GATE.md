# Handoff — deterministic grounding gate on generated descriptions

**From:** dev session, 2026-08-18 (the USP_ED_Sepsis deep trace —
see TRACE_USP_ED_SEPSIS.md). **To:** dev session. CRITICAL for the
"certified" claim.

## Field evidence

The trace found, in production descriptions on the demo tenant:
1. **Selected-columns-as-filters hallucination**: Base_Pop's step
   description asserts three filters (pending/cancelled exclusion,
   triage-time requirement, non-null admission) that do not exist in
   the SQL — the LLM turned SELECTed columns into imaginary WHERE
   clauses. The same boilerplate repeats across ~12 steps.
2. **Invented literals**: LDA steps cite flowsheet IDs "123/456/789/
   101"; the real codes are 900112/900111. Placeholder numbers,
   stated as fact.
3. The metric summary faithfully composed the step fabrications
   upward — composition is fine; step grounding is the failure point.

The STEP_PROMPT already says "Ground every line in the SQL above."
Prompt instructions are intent; they decay under model pressure —
only mechanical verification survives (the notebook-contract lesson,
applied to stage 600).

## Wanted — post-generation checks, deterministic, per step

Run after `describe()` returns, before the description is accepted
into cache/graph. Failures mark the row REJECTED (the 610 pattern:
persisted, retried, queryable) or FLAGGED for steward review:

1. **Literal-value grounding**: every number/quoted code in the
   generated text (regex: digit-runs ≥2, quoted tokens) must appear in
   the step's own fragment (or its dictionary block). Catches
   123/456/789/101 instantly.
2. **Filter-claim grounding**: lines beginning "- " that assert an
   exclusion/requirement must have lexical support in the fragment —
   a claim term ("pending", "cancelled", "triage", "admission") that
   appears NOWHERE in the fragment text fails. Conservative keyword
   check; false negatives acceptable, false certifications are not.
3. **Column-vs-filter check** (the precise mechanism): a claim naming
   a concept that appears ONLY in the SELECT list (never in WHERE/ON/
   HAVING) is flagged "selected, not filtered".
4. Existing observers (_VAGUE_FILLERS, _RAW_IDENTIFIERS) promote from
   run-report flags to the same reject/flag path.
5. Surface counts in 600's tally + ops_fallout rows (stage
   600_grounding, reason ungrounded_value | ungrounded_filter_claim)
   so the funnel and journey show description-quality fallout.

## Also (same trace, small)

- Orchestrator card facts don't carry logic_last_changed_at /
  source_extracted_at (assemble-layer KQL predates 1.19) — the web
  agent cannot cite freshness. Extend the card query + facts dict.
- PROMPT_VERSION bump when the step prompt is hardened → cache
  regenerates everything, as designed.
