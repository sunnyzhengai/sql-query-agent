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
3b. **primary keys** (added 2026-09-05, Sunny's ruling — the
   source's pk metadata table): declared pk rows per table.
   INTEGRITY: every table in part 2 must have pk rows here —
   violation is a named refusal (INTAKE-10). pk is DECLARED DATA,
   never prose-derived.
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

- ~~business_name~~ — CUT 2026-09-05 (Sunny): stored derivation
  of the stored description; no ratified consumer. If display
  demand materializes, it becomes a read-time lens over the
  description, by ratification.
- **grain** — the description's standard grain-declaration clause
  ("one record per X" in spirit; the vendor's exact phrasing lives
  in the source pack).
- ~~pk_columns by phrase~~ — RETIRED 2026-09-05: pk loads from
  the source's pk metadata table (part 3b), declared data. The
  historical prose mentions (89 of 39,565) stay historical.

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
- INTAKE-8 registered db (added 2026-09-05, A1 refined): an
  extract naming a db not in the DBA registration prerequisite is
  a named refusal
- INTAKE-9 declared-vs-captured agreement (added 2026-09-05): the
  script's captured db name must match the registration prereq;
  disagreement is a refusal naming both values
- INTAKE-10 pk integrity (added 2026-09-05, Sunny's ruling): every
  table in the extract has >=1 declared pk row; violation is a
  named refusal listing the keyless tables

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

## 11. Node lifecycle contract (ratified 2026-09-05)

One actor, period: the EXTRACT BUILDER, acting only on a registered
extract intake. Under the one law there is no update (SUPERSEDE)
and no delete (RETIRE).

| Action | Trigger | Postconditions | Tests |
|---|---|---|---|
| CREATE | object in a registered extract, not in graph | metamodel conformance (structured values map, ordered pk_columns); as_of + extract identity; containment chain complete; source inherited; pk loaded from declared pk rows (INTAKE-10 guarantees presence) | LC-C1 minimal extract -> authored nodes (F1) · LC-C2 keyless table -> node + gap row · LC-C3 orphan column (no parent) -> refused + counted, not half-created |
| SUPERSEDE | object changed in a new extract | never in place: new version appended, prior retired (valid_to = new as_of); identity (db.schema.table) stable; change-report row; prior version still resolvable (basis + resolves_to bind to IDENTITY, not version); dependent staleness derivable | LC-S1 changed description -> two versions, current derived, change row · LC-S2 artifact citing prior still resolves · LC-S3 unchanged object -> NO new version (idempotent) |
| RETIRE | object absent from the new extract | marked retired, never removed; inbound references stay valid; change-report row; attached artifacts surface in the steward queue | LC-R1 dropped table -> retired + flag + attachments surfaced · LC-R2 retired readable, excluded from current |
| READ | anyone (lenses, L2 resolver) | completeness declared; current-vs-including-retired is an explicit parameter, never a default surprise | LC-D1 current excludes retired; full read includes with status |

Forbidden paths, each structurally checked: any second writer
(LC-F1 writer census) · in-place mutation (LC-F2 no update op
exists) · physical delete (LC-F3 no delete op exists) · hand-typed
content (LC-F4 every version traces to an extract id) · partial
intake (LC-F5 an extract applies atomically or not at all).

This table is the TEMPLATE: the same lifecycle exercise repeats
for layers 2 and 3 (their tables live in the design doc / their
registries).

## 12. Registration prerequisite (ruled 2026-09-05, A1 refined)

The db is never extract-derived. Registration = a DBA-completed
prerequisite (db name, server, DBA team, registered sources, and
the SCHEMA MAPPING: schema -> source system — organizational
knowledge no system view holds; ruled 2026-09-05), existing
BEFORE any intake; an extract's schemas must appear in the
mapping under that extract's source (mismatch = named refusal,
folded into INTAKE-8); the db node and its layer-3 dba
responsibility mint from it. Extracts attach schemas downward into
a pre-registered db only. New checks: INTAKE-8 unregistered db =
named refusal · INTAKE-9 declared-vs-captured db agreement (the
script's DB_NAME() capture corroborates the prereq; disagreement
is a refusal naming both values).
