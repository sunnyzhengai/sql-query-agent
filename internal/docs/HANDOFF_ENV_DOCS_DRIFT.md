# Handoff — environment definition drift: two lists, one truth

> **Status (2026-08-18, dev session): implemented in 1.16.1.**
> requirements.txt now carries azure-identity==1.25.3; a release-consistency test pins requirements.txt == the environment item's environment.yml; environment/README.md uses <version> and the no-hardcoded-version docs test now covers it.

**From:** review session, 2026-08-17 (found walking Sunny's work setup).
**To:** dev session.

## Findings

1. **requirements.txt lags the environment item.** The shipped
   sql-logic-env PublicLibraries/environment.yml includes
   `azure-identity==1.25.3`; environment/requirements.txt does not. A
   customer building an environment from requirements.txt (the README's
   documented path) gets a different environment than the git-synced item
   — azure-identity missing breaks the Kusto/search path.
2. **environment/README.md hardcodes a stale wheel version** ("upload
   sql_query_agent-1.1.0-py3-none-any.whl"). The docs suite already bans
   hardcoded versions in the install guide
   (test_install_guide_does_not_hardcode_package_version) — this README
   escaped the net.

## Wanted

1. One source of truth: generate environment/requirements.txt FROM the
   environment item's environment.yml (or vice versa), plus a consistency
   test pinning the two lists equal — same pattern as the
   wheel/pyproject/environment release-consistency tests.
2. Extend the no-hardcoded-version docs test to environment/README.md.
