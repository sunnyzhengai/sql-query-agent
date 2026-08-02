# ADR 0012: Build the Product on the Existing Repo, No Rewrite

**Status:** Accepted
**Date:** 2026-07-25 (extracted from MARKETPLACE_PIVOT.md D6)

## Context

Pivoting from POC to commercial product raises the temptation to start a clean
enterprise-grade repository.

## Decision

Build the enterprise product on the existing `sql-query-agent` repository,
retrofitting governance, documentation, and packaging layers around the
battle-tested code.

## Consequences

- The parsing engine's validated accuracy is preserved — a rewrite would
  reintroduce regression risk and waste weeks
- Architecture docs describe reality, not theoretical ideals
- Incremental refactoring (with the regression test suite as the safety net)
  replaces clean-slate redesign
