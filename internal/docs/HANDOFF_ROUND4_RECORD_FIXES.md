# Handoff — Round 4 record fixes: absorb the review session's runner edit, close the gaps properly

**From:** review session via Sunny, 2026-08-22. **To:** dev session.
**Mode: work order** (small, bounded). Context: the Round-4 record
audit (REVIEW_ROUND4_RECORD_AUDIT.md) found the scorecard prose
contradicted the machine table; root cause was reporting tooling
(400-char truncations only, no hit accounting persisted).

## State of the working tree — read this first, don't collide

The review session already made these UNCOMMITTED edits (a process
deviation, disclosed; treat the code edit as a PR to review, not a
fait accompli — absorb, amend, or reimplement at your judgment):

1. `devtools/rematch_round4.py` — CODE (your lane, review-authored):
   - `characterize(answer, oracle)`: pure fact-accounting helper —
     which oracle alternatives an answer carries/lacks, both the
     overlap path and the group path.
   - `grade_fabric` now built on it; return gains `facts` dict
     (`fact_hits` kept for compatibility).
   - `REMATCH_ROUND4_RAW.jsonl` written beside the scorecard: per
     fixture, untruncated answers (both surfaces), oracle, grades,
     latencies. Truncated fresh at run start, appended per row.
   - Scorecard writer: header states overlap thresholds; new
     machine-emitted section "Misses and partial passes" — every
     miss and every PASS earned on partial overlap of a small
     (≤10-name) oracle, with carried/absent name lists.
   - ruff clean, py_compile clean; `characterize` sanity-checked
     offline against the real IP_SEPSIS reader oracle (truncated
     Fabric answer scores 1/2 needed — confirming the recorded PASS
     came from text beyond the truncation).
2. `internal/docs/HANDOFF_REMATCH_ROUND4_GOAL.md` — RECORD (review
   lane, keep): inline correction flag on the wrong miss
   characterization + a dated "ROUND 4 RECORD CORRECTED" entry +
   parked-ruling additions.
3. `internal/docs/REMATCH_ROUND4_SCORECARD.md` — RECORD (review
   lane, keep): hand-labeled audit appendix (true miss list,
   name-cousin finding, ruler asymmetry, raw-log gap for this round).
4. `internal/docs/REVIEW_ROUND4_RECORD_AUDIT.md` — the audit itself.

## Work order

1. **Review the runner edit** as you would a PR. Points of taste that
   are yours: RAW_LOG naming/location (internal/docs vs a runs/
   dir), whether `facts` should also ride the homegrown grade dict
   instead of a separate `home_facts` row key, JSON `default=str`.
2. **Tests (required — the review session broke the test-first law
   shipping this untested):** L0 unit tests for `characterize` —
   overlap path (hit/missed/need/total), group path, empty answer,
   case-insensitivity. Plus one test that the scorecard writer emits
   a partial-overlap PASS line and a miss line from canned rows (the
   writer may need a small extract-function refactor to be testable
   without a live run — your call, notebook contract applies).
3. **Standing rule to encode where the next author will read it**
   (docstring already carries it; consider the runbook too):
   scorecard prose annotates machine-emitted lines, never free-writes
   a miss list; any "X is not in the catalog" claim carries its grep
   receipt.
4. **Do NOT rerun Round 4.** Protocol is one run; the round is
   closed. The tooling is for future rounds. This round's
   untruncated answers were never persisted — unrecoverable, and the
   scorecard appendix says so.

## Constraints

- Pin untouched (no SYSTEM_PROMPT/ENGINE_TOOLS changes anywhere in
  this order). Ruff before push; CI lints separately.
- The record files (items 2–4 above) are review-session verdicts —
  amend only for factual error, and via a new dated entry.

## REVIEW VERDICT (review session, 2026-08-23): APPROVED — one follow-up finding

Work order complete and verified: `scorecard_lines()` extraction makes
the writer testable and machine-emitted end to end; the 10 L0 tests
cover every requested case (overlap path incl. case-insensitivity and
empty answer, group path incl. first-alt reporting, grade_fabric
pass/forbidden, writer partial-pass + miss emission, silent on full
hit, header→raw-log pointer); the standing reporting rule is encoded
in RUNBOOK §6 and the writer docstring with the grep-receipt clause.
RAW_LOG staying in internal/docs: accepted (beside the scorecard).
Full suite on python3.11: 977 passed, 0 failed; ruff clean.
(Reviewer note for the record: an initial 118-failure read was the
reviewer running the 3.9 .venv without pythonnet — env error, not a
regression. Review runs use python3.11.)

**FINDING (follow-up, one small patch — the codebase's own
no-silent-caps law applied to the bonus item):** the answer_evals
INFRA-SKIP comment promises "skips are counted, printed, and >20%
aborts as infra," but `infra_skipped` is write-only — no abort gate
exists, no end-of-run summary, and skipped questions silently shrink
a family's denominator (3 of 6 skipped → the family scores over n=3
and looks healthy). Also `except Exception` will file an ENGINE crash
as INFRA-SKIP transport noise. Wanted: (a) implement the promised
>20% abort; (b) per-family skip counts printed with the board and
carried in the scorecard dump so n is honest; (c) narrow the except
to transport types (or re-raise unrecognized types) so engine bugs
still crash loudly. Not a blocker; the work order is closed.

## PARKED (Sunny's rulings — record, don't decide; also listed in the goal file)

- Criterion 4 (p50 < 3s): amend vs record unmet-and-accepted.
- Criterion 1 drilldown (0.33 under the post-dated grain gate):
  superseded-by-tightening vs unmet.
- Fabric-side `readers_of_table` mitigation: narrows the demo
  contrast — product call.
- Marketplace phrasing of Round 4 ("invents names" is known-false;
  the checkable claim is reach + routing consistency +
  lineage-by-parse vs lineage-by-name).
