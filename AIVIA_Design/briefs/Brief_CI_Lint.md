# Brief_CI_Lint — CI's lint step returns to the retired reality: dead paths drop, the eval corpses retire, ruff runs uncached

**Status: APPROVED** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED) — proposed in conversation 2026-09-20 at the push-and-promote CI watch (F13); APPROVED same day at Sunny's "agree with all three, build it"

| field | content |
|---|---|
| class | FIX (CI's lint line returns to what the repo actually contains — a missed consumer of Brief_Retirement) + RETIREMENT (the two eval scripts + their private LLM client died with src/orchestrator on 2026-09-19 and were missed) + a HABIT amendment (the ruff-before-push law gains --no-cache) |
| claims | Contract_Technical_Layer F13 (landed 2026-09-20 at the CI watch: dev red since c346120, main inherits at the promotion; 4 lint errors, all pre-dating the push) · Brief_Retirement (the 2026-09-19 pivot these files missed) · the retirement law (old tests retire WITH their code — these files have none) |
| impacts (computed, step-2 query) | ONE WRITER each: .github/workflows/ci.yml lint step (the ruff line loses `notebooks/` and `./*.Notebook/` — the first is untracked local-only, the second retired); devtools/ loses answer_evals.py + grounding_evals.py + local_llm.py (import the retired src.orchestrator.*/src.parser — ModuleNotFoundError on import, nothing can run them; local_llm consumed ONLY by the two evals). CONSUMERS: none live — references are history docs (CHANGELOG, decisions, BOARD), one dated retirement note in devtools/suite_map.py (stays — it records history), and src/agent_backend.py's docstring (F14's territory, untouched here). TESTS: NEW tests/test_ci_lint_paths.py, RED first — (a) every path CI lints is TRACKED (an untracked path lints green locally and E902s in CI — F13's exact mechanism), (b) no glob in the lint line, (c) the three corpses stay gone (the tripwire against re-creep). DOCS same breath: CLAUDE.md's ruff line gains --no-cache; F13 flips RULED; F14 born (the same class, deeper: src/agent_backend.py imports the retired src.parser at line 24 — a runtime corpse lint cannot see; src/trace_registry.py:561 names tests/test_grounding_evals.py which does not exist); TEST_MAP regen; CHANGELOG; INDEX; ledger. NO wheel (devtools/ and CI config never ship); NO stored data, NO load |
| ambiguities | ALL THREE RULED before drafting (Sunny "agree with all three, build it", 2026-09-20): (1) the ci.yml lint line becomes `ruff check src/ tests/ scripts/ devtools/`; (2) devtools/answer_evals.py + devtools/grounding_evals.py + devtools/local_llm.py retire per the retirement law; (3) the ruff-before-push habit becomes `ruff check --no-cache` (the stale local cache masked the two I001s — "All checks passed" on files CI failed; --no-cache reproduces CI byte-for-byte). F14 (the deeper same-class leftovers in src/) is NOT in scope — its row is landed, its fix awaits his word |
| debt declared | none — no placeholders; F14 is a FINDING row, not a deferral of this brief's scope |
| retirement (pivots only, the 2026-09-19 law) | devtools/answer_evals.py · devtools/grounding_evals.py · devtools/local_llm.py — retired IN THIS ACT (deleted, not frozen; they cannot execute — their imports died 2026-09-19); no tests retire with them because none exist; history (CHANGELOG, decisions, ledger) keeps their names verbatim |
| does this promote? (the Promotion Gate) | at his word — main is red on the same errors, so the fix wants to reach main; push at his word |
| Sunny's approval | "agree with all three, build it" (2026-09-20) |
| closing check | files changed == files declared (filled at BUILT) |

## Files declared

    AIVIA_Design/briefs/Brief_CI_Lint.md
    .github/workflows/ci.yml
    tests/test_ci_lint_paths.py
    devtools/answer_evals.py
    devtools/grounding_evals.py
    devtools/local_llm.py
    AIVIA_Design/Contract_Technical_Layer.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Manifest_Build.md
    docs/architecture/TEST_MAP.md
    CHANGELOG.md
    CLAUDE.md
