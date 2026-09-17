# THE LITERAL LAW — enforcement plan (PLAN ONLY, 2026-09-07)

**Status: OPEN — plan only.** (Header line added 2026-09-17,
audit CI-C3. INDEX's "step F" stamp could not be verified against
this file's text — the open-step claim needs Sunny's confirmation
or an INDEX correction.)

*(Sunny's order: "how can we enforce no hardcoding, no enumeration,
no pre-built lists/tuples… make the process ironclad… then a
complete code review." This document is the plan and the review's
method. NO CODE until Sunny ratifies the plan and orders the build.
Companion: Audit_Literal_Census_Review.md — the review's findings.)*

## 1. The law (for ratification)

A literal string collection in code is judged by what its contents
ANSWER. Six classes; two are banned from code entirely:

| class | answers | legal home | proof obligation |
|---|---|---|---|
| **vocabulary** ❌ | what does a word mean / map to? | the graph (earned terms) — NEVER code, NEVER prompts | — |
| **ruling** ❌ | what is ruled / what categories exist? | the registry, via the converter | — |
| shape | what fields does this record carry? | code, marked | review-time |
| mechanical | what is this string transform? | code, marked | the never-regex blessed-boundary test: the literal IS the complete spec |
| frame | what label does the UI print? | code, marked | claim/frame law (L2-D2): never a sentence about the estate |
| schema-mirror | what does the metamodel/registry define? | code, marked + CITED | a MIRROR-CHECK test: code set == cited registry sheet, mechanically |
| grammar | how does a ratified rule render? | code, marked + cites the rule ID (Grammar_Floor Rn) | the byte-exact fixture tests (F4) pin it |

The two banned classes HAVE NO MARKER — there is no comment that
legalizes a vocabulary list or a ruling in code. The only path is
the converter (registry bump → doc stamps → Sunny's review chain).
Smuggling becomes structurally impossible, not discouraged.

## 1b. ► RULED (Sunny, 2026-09-07, the root-cause exchange)

- **#3 exempt**: internal envelope labels (shape) are outside the
  no-hardcoding rule.
- **THE BUILDER'S CAGE**: Claude-the-builder is a model seat like
  the Interpreter — its domain knowledge is a PROPOSAL, never an
  author. Legal knowledge sources for the system: the graph (incl.
  registry), the user's live input, confirmed memory. When none has
  it, THE HONEST GAP SHIPS — a young system that asks questions is
  correct, not embarrassing. Builder knowledge enters only through
  design documents Sunny ratifies.
- **THE THREE COUNTERS stand** (one per root cause of the
  enumeration relapses): (1) the literal census as a standing test
  — no marker class exists for vocabulary/rulings; (2) the step
  discipline — each step's TEST SUITE is designed and shown to
  Sunny BEFORE its code; (3) the builder's cage above, ratified in
  writing.

## 2. The three locks (build order, on GO — after the review)

1. **The literal census** — a standing test: an AST scanner over
   aivia/ flags every literal collection of 3+ strings; each must
   carry a marker comment (`# literal: shape` etc.). Unmarked =
   CI failure. Every new list is a visible, classified decision in
   the diff; none enters silently.
2. **The mirror-checks** — every `schema-mirror` cites its registry
   sheet and a test asserts set equality. Code-vs-registry drift
   (the VALID_KINDS disease) becomes impossible.
3. **Prompts are registry data** — the seats' prompts move into the
   registry as versioned rows (the AST cannot see enumeration
   inside prose; the review chain can). A prompt edit is a registry
   bump Sunny reviews.

Residual risk, stated honestly: misclassification (calling a
vocabulary a "frame") is still possible — bounded by the small
closed class set, the census's per-class-per-file report (drift
visible), and the standing process order (no code without GO).
What is GUARANTEED: no silent lists, no unreviewed mappings, no
code-declared rulings, no prompt-buried vocabularies.

## 3. The review method (executed now, read-only)

- Scope: the `aivia/` package (the product). `src/` is the frozen
  pre-clean-room engine — out of scope. Tests are exempt (fixtures
  simulate states) but their vocabulary fixtures are noted.
- Scanner: AST walk; every List/Tuple/Set/Dict with 3+ string
  constants; capture file:line, members, enclosing definition.
- Every hit gets ONE verdict: **OFFENSE-vocabulary /
  OFFENSE-ruling** (must move), **MIRROR** (stays, gains citation +
  mirror-check), or **INNOCENT** (shape/mechanical/frame/grammar,
  gains its marker).
- Prompts and long prose strings reviewed by hand (the scanner is
  blind to them) — the interpreter prompt is already a known
  offense (kind enumeration + synonym hints in prose).
- Output: Audit_Literal_Census_Review.md — the full inventory with
  verdicts; the offense list is the sweep's worklist.

## 4. The sequence (nothing starts without its GO)

1. ~~Plan~~ (this document) → Sunny ratifies/amends the law.
2. ~~Review~~ (Audit_Literal_Census_Review.md) → Sunny reads the verdicts,
   overrules any classification.
3. BUILD (one phase, claims-ledger discipline): ADR for the law;
   registry gains the sheets the offenses move into (ruled-isolated
   kinds, drift sentence, display modes, seat prompts, …); the
   census test red-first; markers + mirror-checks laid down; the
   sweep executed; census green = the permanent gate.
4. The pending find-package (shape-only kind marking, revoke at the
   surface, prompt hardening, labels) merges into the same build —
   it is the same disease.
