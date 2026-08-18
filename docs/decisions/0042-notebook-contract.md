# 0042 — The notebook contract: a harness for the driver layer

**Status:** Accepted
**Date:** 2026-08-18

## Context

Sunny, verbatim: "like our data contract for the engine, do we have a
contract for our notebooks? your default is regex and fixing things in
notebooks — these two behaviors will get us in support black holes. I
need a contract to stop us, and it should tie notebooks to their source
and their outcomes."

The threat model is explicit and unusual: the contract's primary target
is the AI collaborators, whose demonstrated failure mode (the field
week, repeatedly) is locally-reasonable expedience — regex under
deadline, logic patched into notebooks under deadline. Discipline that
lives in intent decays exactly when pressure arrives; only mechanical
enforcement survives. A partial harness existed (pre/postcondition
gates, writers ground-truth, ruff/brand/docs tests, PIPELINE_MAP
generation); what was missing: thinness, the regex ban, version
binding, and a law for field patches.

## Decision

**NOTEBOOK_REGISTRY** (`src/notebook_registry.py`) — truth-as-data for
the driver layer, a peer of TABLE_REGISTRY / INTEGRATION_REGISTRY /
SHAPE_REGISTRY. Per notebook: family (acquisition | derivation |
publisher | verification), `serves` (Layer-0 question families A–G per
QUESTION_MAP; ≥1 required — a notebook serving none is by definition a
ghost), permitted `src.steps` entry points, whitelisted wrapper
functions, required gates, and REQUIRES_ENGINE floor.
`docs/architecture/NOTEBOOK_MAP.md` (including the QUESTION_MAP
layer-4 coverage table) is a generated projection.

Six planks, all enforced by `tests/test_notebook_contract.py` parsing
the notebook sources (AST, not grep):

1. **Registry 1:1** with the `[0-9]*.Notebook` dirs; fields validated.
2. **Regex ban**: `import re` / `re.` fails CI in notebook sources.
   Regex lives only in src/ with tests. No allowlist: a legitimate
   need argues for a src/ function, which is the point. (Enforcing
   this moved 01's coverage preview into `src.dictionary` and gave the
   00b identity pattern ONE spelling in `src.parser.identity`.)
3. **Thinness by AST**: no class defs; function defs only from the
   registry's wrapper whitelist (CLR init, spark closures — shims that
   genuinely cannot live in src/); imports restricted to an allowed
   list; `src.steps` imports restricted to declared entry points.
4. **Gates by family**: registry-declared gate calls must appear in
   source; every derivation notebook must declare precondition_gate.
   Deviations are visible as data, never hidden.
5. **Version binding**: every notebook declares REQUIRES_ENGINE and
   cell 0 calls `require_engine(src.__version__, ...)`
   (`src/engine_floor.py`) — notebook/wheel skew dies loudly at the
   top with the remediation in the message, killing the version-skew
   class that haunted the field deployment.
6. **Field-patch law**: a deployment may patch a notebook ONLY as a
   marked cell — `# FIELD PATCH <date> <handoff-ref> <sunset
   condition>` — and CI fails if the marker appears in repo notebooks.
   Patches exist only in deployments and die on the next sync; the fix
   merges as src/ code with tests or not at all.

## Consequences

- "Why does this notebook exist?" is answerable by query, and the
  QUESTION_MAP audit is permanent: new notebooks cannot land without
  declaring what they serve.
- The next expedient regex or inline function fails CI with a message
  that names the alternative (a src/ function), converting pressure
  moments into the right move.
- Version-skew support incidents become a one-line error naming the
  notebook, versions, and fix.
- Cost accepted: adding a legitimate wrapper or entry point requires a
  registry edit — friction by design; the registry edit IS the review.
