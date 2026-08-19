# ADR 0001: Native Parsers per SQL Dialect

**Status:** Accepted — amended 2026-08-19: the law is total (fallback abolished; sqlglot/sqlparse banned repo-wide, CI-enforced)
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

## Amendment (2026-08-19) — the law is total; the fallback is abolished

Sunny, verbatim: "can we remove sqlglot from ALL code base? under no
circumstances should we use it." The original decision still allowed
sqlglot two lives: structural analysis downstream of ScriptDom
extraction (retired by Option B, 2026-08-04) and a dev-machine
fallback parser. Both repeatedly leaked back toward production
(the tree extractor, the join-map deriver — 2026-08-19), and the
fallback's measured record closed the case: environment-fragile
statement splitting (goldens red for three days in a CI-invisible
tier), 146/417 corpus fragments unparsed, 192 JOINs contributing no
evidence, a /* comment */ embedded in a stored column name, and
CONVERT rewritten to CAST in stored expressions.

**The law, total form:** the dialect's native parser is the ONLY
parser, in every environment — Fabric, dev machines, CI. ScriptDom
runs everywhere via `src/parser/scriptdom_loader` (pythonnet +
coreclr; local runtime in `~/.dotnet`; CI hosts .NET via
setup-dotnet; Apple's hardened system Python is detected by a
subprocess probe and fails with remediation — use Homebrew python3.11).
Where ScriptDom cannot load, parsing FAILS loudly; no other grammar
ever answers in its place.

**Mechanical enforcement** (`tests/test_native_parser_law.py`):
importing sqlglot/sqlparse anywhere in the repo fails CI; declaring
them as dependencies fails CI; instantiating the parser class outside
scriptdom_loader fails CI. The golden corpus tests now run the native
parser on every platform — the CI-invisible tier is dead
(HANDOFF_FALLBACK_GOLDEN_DRIFT resolved by abolition).
