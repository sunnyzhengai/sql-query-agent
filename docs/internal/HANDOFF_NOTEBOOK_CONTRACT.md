# Handoff — the notebook contract: a harness for the driver layer

**From:** review session, 2026-08-18. **To:** dev session.
**Origin (Sunny):** "like our data contract for the engine, do we have a
contract for our notebooks? your default is regex and fixing things in
notebooks — these two behaviors will get us in support black holes. I
need a contract to stop us, and it should tie notebooks to their source
and their outcomes." Threat model is explicit and novel: the contract's
primary target is the AI collaborators, whose demonstrated failure mode
(this week, repeatedly) is locally-reasonable expedience — regex under
deadline, logic patched into notebooks under deadline. Discipline that
lives in intent decays exactly when pressure arrives; only mechanical
enforcement survives.

## Exists already (partial harness — build on, don't duplicate)

precondition/postcondition gates (outcomes, runtime); writers-ground-
truth test (declared vs actual writes, CI); ruff/brand/docs tests over
notebook sources; PIPELINE_MAP generation. Missing: thinness, regex ban,
version binding, field-patch law.

## Wanted — NOTEBOOK_REGISTRY (truth-as-data) + six planks

1. **Registry**: per numbered/lettered notebook: step_name, family
   (acquisition | derivation | publisher | verification), permitted
   src.steps entry points, REQUIRES_ENGINE floor. PIPELINE_MAP + guide
   sections generate from it; freshness tests as usual.
2. **Regex ban in notebooks**: `import re` / `re.` fails CI in
   *.Notebook sources. Regex lives only in src/ with tests. (No
   allowlist to start; if a legitimate need appears, it argues for a
   src/ function, which is the point.)
3. **Thinness by AST**: no class defs; no function defs beyond the
   registry's whitelisted thin wrappers; imports restricted to an
   allowed list (src.steps.*, src.config, src.schemas, src.branding,
   pyspark, yaml, stdlib-minimal). Enforced by a CI test parsing
   notebook-content.py ASTs.
4. **Gates by family**: derivation notebooks must contain
   precondition_gate + postcondition_gate calls; acquisition notebooks
   must write fallout/identity checks; registry-driven source test.
5. **Version binding**: notebook declares REQUIRES_ENGINE; cell 0
   asserts src.__version__ satisfies it (loud named failure kills the
   version-skew class that haunted the work deployment all week).
6. **Field-patch law**: patches legal ONLY as marked cells
   (# FIELD PATCH <date> <handoff-ref> <sunset condition>); CI fails if
   the marker appears in repo notebooks — patches exist only in
   deployments and die on sync. Formalizes the 2026-08-17/18 discipline.

ADR-worthy (peer of TABLE_REGISTRY / INTEGRATION_REGISTRY / the shape
registry). Sequencing: after the current four opens or alongside —
Sunny has removed deadline pressure specifically to do this right.

## Amendment (2026-08-18, Question Map — approved by Sunny)

Registry entries gain a `serves` field: the Layer-0 question families
(A-G, see docs/architecture/QUESTION_MAP.md) each notebook ultimately
exists for. Enforcement: every notebook must serve >=1 family (else it
is by definition a ghost); the QUESTION_MAP's layer-4 table becomes a
generated projection of the registry once built.
