# Handoff — fallback-parser golden smoke red since the corpus de-dialect

**From:** dev session, 2026-08-19. **Status: RESOLVED same day, by
abolition** — the fallback parser is deleted under the total
native-parser law (ADR 0001 amendment). ScriptDom now runs locally and
on CI (scriptdom_loader + ~/.dotnet + setup-dotnet); the goldens are
native structural pins that run on EVERY platform (no CI skip — the
invisible tier is dead), and sqlglot/sqlparse imports fail CI
(tests/test_native_parser_law.py). Wanted-items below kept for history.

## What was found

`tests/golden/test_parse_goldens.py` has been failing locally since
**1.11.1 (054caa1, "corpus fully de-dialected", 2026-08-16)** — bisected
in a throwaway worktree: 19 failures at 054caa1, identical failures at
1.11.3, 1.24.0, and HEAD. Composition:

- 18 × `test_extraction_produces_structure`: the FALLBACK parser
  (sqlparse/sqlglot path, dev-machine tool) extracts **0 CTEs** from
  de-dialected corpus files it previously handled (per-query parse
  warnings, e.g. `reports/USP_RPTS_NonSevere_Sepsis.sql` 12/12 queries
  fail to split/parse).
- 1 × manifest drift: the de-dialect renamed
  `reporting/USP_ED_Sepsis.sql` → `USP_ED_SEPSIS.sql` on disk without
  the manifest key following. **Fixed in this commit** (manifest key
  case-corrected; test green).

## Why nobody saw it for 3 days — and the honest part

These tests are `skipif(GITHUB_ACTIONS)` — CI has NEVER run them; CI's
parse truth is the recorded ScriptDom fixtures
(`tests/test_recorded_pipeline.py`), which pass everywhere. So every
"CI green" since 1.11.1 was truthful about production parsing and
silent about the fallback. The release drill claims "full local suite"
— these failures were present during the 1.12→1.25 releases and were
missed. That is exactly the silent-residue class ADR 0045 now bans:
a local-only test tier with no escalation path is a counter nobody
reads.

## What this is NOT

- Not a production parse problem: ScriptDom (ADR 0001) parses the
  de-dialected corpus exactly — recorded fixtures + the live 43/43
  deep trace (TRACE_USP_ED_SEPSIS.md) prove it.
- Not caused by 1.25.0's truncation fix (failures predate it).

## Wanted

1. Decide the fallback parser's contract against the de-dialected
   corpus: either repair its statement splitter for the new corpus
   shape (it is the dev-machine/BYOT-lite path), or formally demote
   these 18 files in the manifest as
   `known_fallback_limitation` WITH reason strings — never by zeroing
   `cte_count` to make red disappear (no-expedient-defaults).
2. Escalation-contract tie-in (ADR 0045 §3): a local-only test tier
   needs a surfacing mechanism — e.g. the release drill records the
   local tally in the commit message or a `docs/internal/` run log, so
   "19 failed locally" can never ride along silently again.
