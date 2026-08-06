# 0025 — PHI and hardcoded-literal scanning at ingestion; the LLM boundary is the gate

**Status:** Accepted
**Date:** 2026-08-06

## Context

Customer SQL embeds literals: date ranges, thresholds, and — in healthcare —
occasionally identifiers (MRNs, CSNs, provider names) hardcoded into WHERE
clauses. The whitepaper documents agent-level redaction and the demo
anonymization engine exists (`src/anonymization.py`, crosswalk-driven), but
nothing scans customer SQL at ingestion. ADR 0019 made this urgent:
description generation sends `sqlFragment` — "the payload most likely to
carry embedded literals" — to an LLM endpoint. Within the customer's own
Azure OpenAI the exposure is bounded, but PHI in prompts is still PHI
processed by an additional service, and generated *descriptions* can echo a
literal into tables that flow onward to catalogs (Purview, Collibra) and
agent answers.

The constitution (ADR 0021) says certification never gates availability.
PHI protection is a different axis: it governs **data egress**, not metric
availability — a gate here is not a steward bottleneck, it is a compliance
boundary, and it must be mechanical (no human in the loop, 5-rule gate).

## Decision

**Scan at ingestion; redact at the LLM boundary; block nothing inside the
tenant.**

1. **Detection runs in 02_parse** over the normalized SQL, deterministic
   and pattern-based — never LLM-based (an LLM detector would require
   sending the text out, the exact thing being protected against).
   Detected classes, each a named rule:
   - `id_literal` — long numeric literals in comparisons against columns
     whose names match id patterns (`*_ID`, `*CSN*`, `MRN`, `*_NBR`)
   - `date_literal` — quoted date/datetime literals
   - `name_literal` — quoted string literals against person-name-ish
     columns (`*NAME*`, `*PROVIDER*`, `*PHYSICIAN*`)
   - `contact_literal` — anything matching email/phone/SSN shapes
   - `threshold_literal` — bare numeric comparisons (lowest severity;
     business thresholds, not PHI, but flagged for steward review since
     hardcoded thresholds are governance smells)
   Rules ship with the library; the crosswalk's `_scan_terms` mechanism
   extends them with org-specific terms (same engine as fixture
   anonymization — one scanner, two callers).
2. **Findings are data:** `ops_phi_findings` (contract draft) — one row per
   finding: metric_id, rule, matched text, masked context, severity,
   disposition. Dispositions: `redact` (default for id/date/name/contact) |
   `allow` (steward-confirmed false positive, e.g. a code-set constant) |
   `open` (threshold_literal awaiting review). Steward dispositions are the
   only human touchpoint, and they only *unredact* false positives — the
   default is safe without anyone acting.
3. **The redaction gate sits at every point where SQL-derived text leaves
   the lakehouse:** description generation (07 / devtools), catalog
   publishes (08/09), and any future export. Fragments with `redact`
   findings get placeholder substitution (`'2023-01-01'` → `<DATE>`,
   `123456789` → `<ID>`) before the prompt is built; the graph itself keeps
   the original fragment — inside the tenant, in the customer's lakehouse,
   nothing is blocked or altered.
4. **The existing leak gate stays as defense-in-depth** (scan-after-generate
   in describe_local and export_test_fixtures); ingestion scanning is the
   layer that catches what crosswalk terms can't — it knows *shapes*
   (SSN-like, MRN-like), not just known names.

## Consequences

- Healthcare-critical box gets a mechanical answer: PHI exposure to the LLM
  is bounded by deterministic redaction with an auditable findings table,
  not by prompt instructions.
- False-positive redaction can dull a description ("filters to `<DATE>`") —
  acceptable: descriptions state logic, and the steward `allow` path
  restores precision where it matters.
- `threshold_literal` findings double as a governance queue: hardcoded
  business thresholds surface for steward review via the flywheel
  (ADR 0023 priority), a feature competitors' scanners don't have.
- New pipeline step in 02; scanner lives beside `src/anonymization.py`
  sharing its scan machinery. Implementation follows as a separate pass;
  this ADR fixes the design so the 07 deploy cycle can depend on it.
