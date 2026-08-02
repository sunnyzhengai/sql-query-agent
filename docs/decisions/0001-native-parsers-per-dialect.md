# ADR 0001: Native Parsers per SQL Dialect

**Status:** Accepted
**Date:** 2026-07 (recorded 2026-08-02)

## Context

Enterprise stored procedures are programs in a procedural dialect (T-SQL, PL/SQL)
with SQL embedded inside. Generic SQL parsers understand the SQL parts but choke
on the procedural scaffolding. Approaches tried and their parse/extraction rates:

| Approach | Result | Why it failed |
|---|---|---|
| Regex stripping | 64–87% | Can't predict all ways developers write code |
| sqlparse splitting | 32–87% | Doesn't understand T-SQL procedural grammar |
| LLM extraction | 79% | Non-deterministic, slow, garbles output |
| Token walking | 56% | Can't split statements without semicolons |
| ANTLR Python wrapper | Correct but ~7 min/proc | antlr-tsql not production-viable |
| **ScriptDom** | **100% extraction** | Microsoft's own T-SQL parser (powers SSMS) |

## Decision

Use the dialect's own native parser — never a universal text-based extractor.
T-SQL: Microsoft ScriptDom (.NET DLL via pythonnet in Fabric notebooks). The AST
is walked to lift SELECT/INSERT statements verbatim; sqlglot then does structural
analysis on the clean, isolated statements. Future dialects get their own native
parser (ANTLR PL/SQL grammar for Oracle, ANTLR Snowflake grammar).

## Consequences

- Deterministic, instant, free parsing; extracted SQL is character-for-character original
- No regex maintenance, no LLM dependency in the trust-critical path
- Each new dialect requires integrating a new native parser (a per-dialect adapter layer)
- Fabric deployments must ship and load the ScriptDom DLL (pythonnet/CoreCLR constraint:
  no `%pip install` after CLR load — packages must come from the Fabric Environment)
