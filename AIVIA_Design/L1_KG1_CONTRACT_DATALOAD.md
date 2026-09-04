# AIVIA Contract — Data Load (the registered extract)

**Status:** DRAFT v0.1, authored by Claude 2026-09-04 at Sunny's
request; ratification is Sunny's, in the AIVIA Design Document.
**Level:** L2 (details the technical layer's input seam).
**Vendor-neutral by rule:** nothing in this file names any vendor's
objects. Vendor specifics live in SOURCE PACKS (see §2) —
fingerprinted packs in AIVIA_Protected/ (never shipped), synthetic
packs in AIVIA_Product/ (the demo/marketplace path). Both implement
this one contract.

## 1. What one extract is

One extract = one source system's dictionary, at one point in time,
identified by (source, as_of). Self-contained: a full snapshot,
never a delta; sufficient alone to rebuild that source's portion of
the technical layer. One source per extract; each source on its own
clock.

## 2. The source pack (per vendor, versioned)

Everything vendor-specific, packaged and versioned as the
registered definition of how that source is read:

- the metadata extraction script(s) (tables/columns + joins)
- the values-dump generator (uniform per-table SELECTs)
- the phrase rules (see §4)
- the dedup rule and its assertion (see §5)
- the join grouping rule parameters (see §6)
- the source-pack version — stamped into every extract it produces

A source pack containing real vendor object names or boilerplate
text is PROTECTED material: it ships privately to licensed
customers, never in public/demo assets.

## 3. The four parts of an extract

1. **manifest** — human-typed fields: source label, operator name.
   Captured fields (emitted by the scripts themselves, never
   typed): database name, server, run timestamp (= as_of),
   source-pack version.
2. **tables + columns** — physical names, declared descriptions,
   and each table's SCHEMA (ruled 2026-09-04: containment is an
   explicit extract field — the manifest's captured db plus the
   per-table schema close the db -> schema -> table chain; a
   single-schema source still states it).
3. **joins** — declared column-pair rows with group identifiers
   and ordinal positions, as the source's own metadata states them.
4. **values** — (code, meaning) rows per value-carrying table,
   produced by the generated uniform dump; which tables to dump is
   read from the declared joins (a value table is a join
   destination), never from naming conventions.

**Data boundary (ruled 2026-09-04):** an extract contains METADATA
AND CONFIGURATION VALUES ONLY — dictionary text and value-table
(code, meaning) rows — never clinical/transactional rows. The
runbook states this to the DBA; intake may additionally scan
incoming text as defense in depth (build deferred).

## 4. Phrase rules (declared prose -> structured properties)

Where a source declares facts inside fixed-boilerplate description
text, the source pack states one PHRASE RULE per fact. v0.1 rules
for the first source:

- **business_name** — the friendly name inside the description's
  standard opening.
- **grain** — the description's standard grain-declaration clause
  ("one record per X" in spirit; the vendor's exact phrasing lives
  in the source pack).
- **pk_columns** — the key columns as called out in the table
  description.

Phrase-rule law: deterministic pattern against declared text only;
a description that does not match the pattern yields ABSENT +
a counted gap-list entry — never a guess. Phrase rules are part of
the versioned source pack: when the vendor's boilerplate changes,
the pack version changes, and every governed extract regenerates.

**Field-calibrated 2026-09-04:** phrase rules are OPPORTUNISTIC,
not primary — real-estate measurement showed the boilerplate lives
on core tables only (~0.5% of all tables, disproportionately the
ones estates actually use). Each rule carries its variant-pattern
list as source-pack data. The PRIMARY structural source for keys
is **referenced_keys**, derived from the declared join data: every
inbound FK's destination column-set is a declared reference key of
that table — vendor-declared, no prose involved, and it covers
every table anything joins to. Phrase-rule coverage is reported
against two denominators: all tables (honest) and, once the logic
layer exists, the estate's working set (meaningful).

## 5. Dedup rule (empirical rules get guards)

A source pack may include an empirically-chosen filter (e.g. to
remove duplicated metadata rows). Every such filter ships with an
INTAKE ASSERTION of the outcome it exists to produce (e.g. exactly
one row per table, zero tables lost). The filter is the rule; the
assertion is what makes an imperfectly-understood filter safe.
(Field-confirmed 2026-09-04: the first source's dedup filter passed
its assertion exactly — one row per table — on a live estate.)

## 6. Join grouping rule

Declared join rows group into joins_to edges by their EXPLICIT
GROUP IDENTIFIER (field-confirmed 2026-09-04: the first source's
join metadata carries one, repeated across a composite key's rows);
ordinal position orders the pairs within a group. Consequences:

- single-column join: one group, one pair -> one edge
- composite join: one group, n ordered pairs -> one edge
- multiple distinct joins between the same two tables: different
  groups -> parallel edges, each identified by its `on` set
- rows whose group/ordinals are malformed: QUARANTINED and counted,
  named in the intake report — never silently grouped
- a value-table link declared twice (once to the category column,
  once to the internal id, same values): deduplicated to one edge
  by stated rule
- **referenced_keys** (see §4): each table's declared reference
  keys are derived at intake from its inbound join groups — the
  destination column-set of each group is a declared key of the
  destination table

## 7. Intake: checks and refusal semantics

Intake validates an arriving extract against this contract before
anything touches the graph. Every check has a name; every refusal
names its violated rule (the error-contract law: a failed intake is
self-serviceable by the customer's DBA without a support call).

- INTAKE-0 parts presence (all four parts arrived; a missing part
  is a named refusal, not a partial load)
- INTAKE-1 manifest completeness (two human fields present; all
  captured fields present and internally consistent)
- INTAKE-2 dedup assertion (§5) — hard refusal on failure
- INTAKE-3 join grouping (§6) — quarantine + count, load proceeds
- INTAKE-4 phrase-rule yields (§4) — gap lists, load proceeds
- INTAKE-5 values coverage — every declared value-table link has a
  dump; missing dumps counted
- INTAKE-6 declaration legality — an extract may not declare a join
  whose dependent side belongs to another source (refused + counted)
- INTAKE-7 source-pack version match — extract produced by an
  unknown/retired pack version is refused

## 8. The intake report

The intake report is DATA FIRST: result tables written beside the
graph in the customer's tenant (counts per part, check outcomes,
gap lists, quarantines, version stamps), from which two renderings
derive — a human-readable summary and a BI dashboard template bound
to the result tables. Residency: the report derives from the
customer's licensed estate and stays in their tenant; the engagement
operator reads it there. Only de-identified aggregates may ever
leave, and only by explicit decision.

## 9. Versioning and succession

Every extract is stamped (source, as_of, source-pack version).
Every technical-layer node/edge carries the extract identity it
derives from (per-object authority). A source-pack change
regenerates everything it governs — same mechanism as every other
versioned definition in AIVIA.

**Succession (ruled 2026-09-04):** a new extract SUPERSEDES its
predecessor for that source. Intake produces a CHANGE REPORT —
added / removed / changed objects and meanings. A removed object
that has artifacts pointing at it is FLAGGED, never silently
deleted; changed meanings trigger regeneration of the artifacts
that cite them (the standing version-stamp mechanism). Development
of succession handling is deferred; the rule is ratified now so the
second extract ever loaded is a designed event, not an improvised
one.

## 10. Status and open items

**CONTRACT COMPLETE (Sunny, 2026-09-04):** all four completeness
gaps ruled and documented (schema containment §3, data boundary §3,
succession §9, INTAKE-0 §7). ALL DEVELOPMENT DEFERRED by ruling —
the current phase completes contracts layer by layer before any
build. Deferred-to-build with reason: file-format minutiae
(encoding/delimiters/size — build-time detail); multi-db sources
(no real case yet); intake text scan (defense in depth).

- ~~FK grouping identifier confirm (§6)~~ — CLOSED 2026-09-04:
  explicit group id exists; §6 rewritten to use it
- ~~grain-phrase consistency confirm (§4)~~ — CLOSED 2026-09-04:
  boilerplate real but rare (~0.5% of all tables); phrase rules
  demoted to opportunistic, referenced_keys promoted to primary
- ~~AIVIA_Design/ tracking~~ — CLOSED 2026-09-04: tracked in git;
  AIVIA_Protected/ stays local-only
