# ADR 0016: Case-Insensitive Identifier Matching, Folded to Uppercase

**Status:** Accepted
**Date:** 2026-08-02

## Context

Dictionary-to-SQL table matching was case-asymmetric: exact-case match with
an uppercase fallback. It worked for Epic Clarity (all-caps dictionaries)
but silently failed for Caboodle (PascalCase names like `PatientDim`) —
technical nodes ended up with no description, while `06_validate`'s
coverage metric (which uppercased both sides) reported optimistic numbers
the graph join didn't achieve. Three docs made three different claims about
case behavior.

Ground truth of the source engines settles the question:

| Engine | Identifier case behavior |
|---|---|
| SQL Server | Collation-determined; default (`..._CI_AS`) is case-insensitive — Epic runs CI |
| Oracle | Unquoted identifiers fold to UPPERCASE; only quoted are case-sensitive (rare) |
| Snowflake | Same as Oracle (unquoted folds to upper) |
| PostgreSQL | Unquoted folds to lowercase |

For the current market (T-SQL, Tiers 1–2), the database itself treats
`Encounter` and `ENCOUNTER` as the same object.

## Decision

1. **Match keys and graph node IDs are case-folded to UPPERCASE**
   (`fold_identifier` in `src/parser/identity.py`): dictionary lookups, the
   builder's table-name index, technical node IDs (`tech:DBO.ENCOUNTER`),
   and duplicate-identity detection. Stored/display values keep the
   customer's original casing.
2. **Duplicates after folding are rejected loudly** at load: two dictionary
   rows or two SQL files whose identities differ only by case are the same
   object in a CI database — a data error, not two entries.
3. **Identifier folding is a dialect property**, like parsing (ADR 0001).
   Uppercase is correct for T-SQL/Oracle/Snowflake; a future PostgreSQL
   adapter supplies its own folding rule.
4. **Schema-agnostic dictionary matching is an accepted, gated limitation**:
   the dictionary has no schema column, so descriptions attach by bare
   table name across schemas. `06_validate` detects when the customer's SQL
   actually references the same bare name in multiple schemas and BLOCKS
   deployment unless the admin acknowledges via
   `dictionary.accept_schema_ambiguity: true` in org_config.yaml — the
   limitation can never bite silently.

## Consequences

- Caboodle (PascalCase) dictionaries now match; matching mirrors engine
  semantics rather than string luck
- The coverage metric and the builder finally measure the same operation
- Technical node IDs changed casing (`tech:dbo.x` → `tech:DBO.X`); the graph
  is rebuilt each pipeline run, so there is no migration, but external
  references to node IDs (exports, saved queries) refresh on next run
- Rare case-sensitive-collation SQL Server sources are a documented
  limitation: two genuinely distinct objects differing only by case would
  be rejected as duplicates at load
