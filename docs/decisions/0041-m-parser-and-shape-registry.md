# 0041 — M mini-parser, shape registry, and fallout capture

**Status:** Accepted
**Date:** 2026-08-18

## Context

The first full-estate harvest (601 models, 5 workspaces) exposed three
compounding failures:

1. **Pattern misses at scale.** 277 SQL-shaped partition sources
   (Odbc.Query, Sql.Database) were missed because regex patterns expect
   canonical argument shapes — real estates pass servers as PARAMETERS,
   bracket their EXEC identifiers, and build query strings by
   CONCATENATION. The same source function appears in volume on both
   the parsed and missed sides; argument KIND is the discriminator.
2. **Silent absence.** 174 models yielded zero sources and left no
   record — the evidence existed only in stdout scrollback and session
   memory. Root-cause distribution was unknowable by query.
3. **The support model doesn't scale.** Sunny (verbatim intent):
   "instead of waiting for lineage harvesting to fail, collect all
   possible shapes from the customer's workspaces, and per shape have a
   src/ handler... I cannot go to each customer to troubleshoot."

Sunny's design challenge, upheld: adding more regex patterns extends
the disease. The existing patterns ARE regex over M text — the native
parsers doctrine (ScriptDom for T-SQL, the TMDL parser for TMDL) had
not been applied to the third language in the stack: M.

## Decision

Four parts, all house patterns:

1. **M mini-parser** (`src/mquery/parser.py`): tokenizer + recursive
   descent over the needed M subset (let, application, `&`
   concatenation, records, lists, navigation, identifiers, literals,
   if/each/try). Resilient by contract — anything outside the subset
   degrades to an Opaque node; the parser NEVER raises, because total
   classification must not depend on total parsing.
2. **Shape signatures with argument kinds**
   (`src/mquery/signature.py`): a partition's shape is its source
   function plus the KINDS of its arguments (literal / parameter /
   concat / record{...}). Anonymization is WHITELIST-based: only M
   standard-library names appear verbatim; every unrecognized
   identifier is emitted as a kind. Strip-based anonymization fails on
   the unrecognized by definition; whitelist-based cannot leak. A CI
   leak test enforces it.
3. **Shape registry** (`src/mquery/registry.py`): the declarative
   authority on known shapes — a peer of TABLE_REGISTRY and
   INTEGRATION_REGISTRY. Statuses: supported / recognized_unsupported /
   unknown. CI enforces that every `supported` shape has a fixture that
   both classifies to its entry AND yields a source through
   `parse_tmdl_partition` — a supported claim without a passing fixture
   fails the build. (The guard caught its first gap the day it was
   written: Schema/Item navigation was claimed and unextractable.)
4. **Fallout capture** (`ops_fallout`, TABLE_REGISTRY): every stage
   that drops an entity writes a row — run_at, stage, entity_id,
   machine reason_code, human reason_text, contract_id. Unknown-shape
   fallout rows carry the anonymized signature. Root-cause aggregation
   is a GROUP BY; the census coverage report states up front what a
   harvest will and won't extract.

The support loop becomes: signature in → fixture added → handler
shipped in the next wheel. Cross-customer signature frequency (with
consent) is the data-ranked connector roadmap — the error-contract
philosophy's product-signal flywheel, now mechanical.

## Consequences

- The filed regex pattern fixes (param server / brackets / concat /
  Schema-Item navigation) shipped alongside as the immediate recovery
  (~430 files at the reference estate); the census makes the NEXT gap
  a data point instead of an incident. The regex extractor remains the
  handler layer for now; migrating extraction itself onto the M AST is
  the natural follow-up, tracked in HANDOFF_SHAPE_CENSUS.
- Lineage QA stays deterministic (amendment upheld): membership against
  the parsed corpus now; TMDL-column vs proc-output-column overlap
  scoring is the wanted next reconciliation signal. LLM triage, if
  ever, is judgment assistance on flagged residue only (ADR 0032).
- The reference-estate aggregates in HANDOFF_SHAPE_CENSUS are the
  acceptance target: the shipped census re-run on that estate should
  reproduce them at file grain.
