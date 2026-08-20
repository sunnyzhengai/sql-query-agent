# Handoff — work-term hygiene: leak check, old wheels, history decision

**From:** review session, 2026-08-18, following the dev session's fixture
de-identification. Companion action already taken: the real-term
inventory moved OUT of docs/development/ANONYMIZATION_STRATEGY.md into
gitignored private/SCRUB_TERMS.md; the repo doc is now method-only.
**To:** dev session.

## Wanted

1. **Local leak-check script** (scripts/, runs locally only): reads
   private/SCRUB_TERMS.md if present (skips gracefully in CI, where the
   list must not exist), sweeps the FULL repo — src (incl. docstrings),
   tests, fixtures, *.Notebook, docs — and fails on any hit. Intended as
   pre-push / pre-release discipline. Lesson driving scope: both prior
   sweeps (review session's docs-only, and the original anonymization)
   missed src docstrings and fixtures; leak checks must be repo-wide and
   term-list-driven, never memory-driven.
2. **Old wheels in dist/**: wheels built before the de-identification
   embed the old identifier-carrying docstrings. They are never shipped
   (packaging uses current only; work snapshots exclude old wheels) but
   sit in the working tree. Recommend pruning to current-version-only
   (release-consistency tests need only the current wheel) or explicitly
   accepting them as history-equivalent — decide and record.
3. **Git-history rewrite decision — record it**: identifiers exist
   throughout history (fixtures since July; the strategy doc; handoffs
   pre-scrub). Recommendation: DEFER while the repo is private, but make
   it a HARD PRE-CONDITION before any third-party repo access
   (Marketplace certification reviewers, contractors, open-sourcing).
   Add to the pre-ship checklist so it cannot be forgotten at the moment
   it matters.
