# 0022 — Definition versioning: content-hash versions; certification pins a version

**Status:** Accepted
**Date:** 2026-08-06

## Context

Source SQL changes. Today the pipeline overwrites the graph on every run
(`write_mode: overwrite` everywhere), so a metric silently *becomes* its new
definition — and any certification recorded against it would silently apply
to logic the steward never saw. ADR 0004's sign-offs are meaningless unless
they bind to a specific definition. The repo already computes content hashes
in two places (`ops_extraction_tracking.sql_hash`, `step_content_hash` in
description caching), so definition identity by content is established
practice here.

## Decision

1. **A definition version is a content hash.** For each metric,
   `definition_hash` = SHA-256 of its normalized source SQL (the same
   normalization the parser already applies). A monotonically increasing
   `definition_version` (1, 2, 3…) is assigned per `metric_id` whenever the
   hash changes — the hash is identity, the ordinal is for humans.
2. **Certification pins (metric_id, definition_hash).** Certification events
   (dev or steward) record the hash they reviewed. A certification never
   applies to a definition it did not name.
3. **Freshness is a derived axis, not a new state.** The certification state
   machine keeps its three states (`draft`, `dev_certified`,
   `steward_certified`); a metric whose current hash differs from its last
   certified hash is **stale-certified** — computed by comparing
   `definition_hash` to `certified_hash`, never stored as a status that a
   human must remember to flip. Per ADR 0021 a stale-certified metric still
   answers, disclosing "certified for a previous version; current changes
   pending review."
4. **Recertification is a diff review.** When a certified metric's hash
   changes, the steward queue item carries old and new fragments; the
   steward re-affirms or rejects the *delta*, not the whole definition from
   scratch. Version history lives in the append-only
   `gov_certification_events` log (contract draft in `src/schemas.py`), so
   "who certified what, when, against which logic" is a query, not an
   archaeology dig.

Planned column additions (to land with the implementation, kept out of the
active contracts until a writer exists — the contract registry stays
truthful to code): `graph_canonical` and `output_metric_logic` gain
`definition_hash`, `definition_version`, `certification_status`,
`certified_hash`, `certified_version`.

## Consequences

- Sign-offs become durable facts: a steward's name never attaches to logic
  they didn't review. This is the precondition for named accountability in
  answers (ADR 0004, ADR 0021 disclosure).
- The overwrite pipeline needs one new comparison per run (current hash vs.
  last event's hash) to detect drift and emit queue items — cheap, and the
  hash machinery already exists.
- Stale-certification surfaces silently drifted metrics — today invisible —
  as a first-class steward queue category, prioritized by usage weight
  (ADR 0023).
- Description caching (ADR 0019) and versioning share the hash foundation:
  a definition change invalidates descriptions and certification in the
  same run, for the same reason, visibly.
