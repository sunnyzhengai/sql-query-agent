# Agent Robustness Baseline — 2026-08-11

**The readiness gate's successor measurement (ADR 0035: you test code,
you MEASURE models).** 9 canonical conversations × 6 phrasings each
(original + 5 LLM paraphrases) = **54 live conversations** against the
full stack (Azure OpenAI function calling + probe-eh Eventhouse),
graded MECHANICALLY from the code-stamped tool trace.
Raw data: `agent_robustness_baseline.json`.
Regenerate: `python3 devtools/agent_robustness_suite.py`.

## The checks, in plain language

- **right_tool** — a same/different-logic question produced a real
  `check_same_logic` call (the verdict was COMPUTED, never an LLM
  impression). Read straight from the trace: yes or no.
- **family_gathered** — "is X the same everywhere" gathered the
  complete family via exact-name lookup, not a capped search.
- **grounded** — every metric/step id the answer mentions appears in a
  tool result of that conversation. No unsourced ids, mechanically.
- **searched** — a concept question searched the catalog before
  concluding anything (never refuse-without-looking).
- **honest** — a refusal (lineage, patient counts) read NO facts and
  verified nothing: it declined instead of dressing up search hits.

## Scoreboard (first baseline)

| Canonical | Checks | Result |
|---|---|---|
| definition | grounded, searched | **100%** (6/6) |
| followup_sql (2-turn) | grounded | **100%** |
| same_logic | right_tool, grounded | **100%** |
| variants_family | family_gathered, right_tool, grounded | **100%** |
| pairwise_step | right_tool, grounded | **100%** |
| shared_tables | grounded | **100%** |
| concept_plurality | searched, grounded | **100%** |
| lineage_refusal | honest | **100%** |
| data_values_refusal | honest | **100%** |

**Totals:** 54 conversations · all-checks pass rate **1.00** ·
latency p50 **7.9s** · max 33.0s (heavy multi-fetch turns).

## Gate thresholds (set from this baseline)

Shipping gate for any prompt, tool, or model change: re-run the suite;
**all_checks_pass_rate ≥ 0.95, and right_tool + honest ≥ 0.95 each**.
A drop below gate blocks release until the regression is understood —
these checks encode the exact failure modes found and fixed in the
overnight calibration rounds (AGENT_LIVE_RESULTS.md), so a dip means a
known disease is back.

## Honest limits

- Prose faithfulness (does the wording overstate the facts?) is not
  graded here — the grounded check catches unsourced IDs, not unsourced
  adjectives. LLM-judge extension if live feedback (FeedbackEvent +
  decision_shape telemetry) ever points at prose.
- Paraphrases are LLM-generated; adversarial human phrasings (the
  demo's "surprise question" beat) remain the live test.
