# Handoff — proactive shape census + shape registry (go-live requirement)

**From:** review session, 2026-08-18. **To:** dev session.
**Origin (Sunny, verbatim intent):** "instead of waiting for lineage
harvesting to fail, collect all possible shapes from the customer's
workspaces, and per shape have a src/ handler. Once listed, I cannot go
to each customer to troubleshoot because we didn't have a shape ready."
Field context: 174/601 models yielded zero sources, silently; 277
SQL-shaped sources were pattern misses (HANDOFF_TMDL_PATTERN_GAPS).

## Design (four parts, all existing house patterns)

1. **Shape census** — total classification of every partition source
   into a SHAPE SIGNATURE without requiring successful parsing. Runs as
   12's pre-step AND standalone (install-time; potentially pre-sales /
   LEAD_HANDLING). Cheap, read-only. The 2026-08-18 field regex +
   taxonomy histogram is the prototype and first output.
2. **Shape registry (src/, declarative)** — one entry per known shape:
   detector/signature, handler fn (per-shape extractor), status
   (supported | recognized_unsupported | unknown), notes. CI: every
   supported shape MUST have fixture(s) that parse (mechanical
   enforcement); docs source-shape matrix becomes a GENERATED projection
   of the registry.
3. **Coverage report = census x registry** — at install: "N sources:
   X% supported, Y% recognized non-SQL (listed), Z% unknown (signatures
   attached)". 12's gate states coverage up front instead of silent
   partial harvests. Unknown/unsupported partitions become fallout rows
   (HANDOFF_FUNNEL_AND_FALLOUT) carrying the signature as reason detail.
4. **Anonymized signature protocol** — signature = M skeleton only:
   function names + argument KINDS (literal/parameter/concatenation),
   identifiers and literals stripped. Safe for customers to send; safe
   to aggregate in telemetry (consent) → cross-customer shape frequency
   = data-ranked roadmap (error-contract philosophy: repeats across
   customers = product signal). Support loop becomes: signature in →
   fixture added → handler shipped in wheel update. No on-site
   troubleshooting.

## Sequencing suggestion

Pattern gaps already filed (brackets/param-server/concat) land first as
ordinary fixes; census+registry is the structural layer that makes the
NEXT gap a data point instead of an incident. ADR-worthy — the shape
registry is a peer of TABLE_REGISTRY and INTEGRATION_REGISTRY.

## Amendment (2026-08-18, Sunny's two challenges — both upheld)

1. **No regex. The foundation is a minimal M expression parser.** The
   existing patterns 1-5 ARE regex over M text — that is the root cause
   of the field misses, and adding patterns extends the disease. Build a
   tokenizer + small recursive-descent over the needed M subset (let,
   function application, string concatenation, records,
   identifiers/parameters); census classifies the AST, shape handlers
   walk it. Native-parsers doctrine applied to layer three. (Microsoft's
   powerquery-parser is a grammar reference.) The filed regex pattern
   fixes (brackets/param/concat) may still ship as a stopgap; the parser
   retires them.
2. **Lineage QA is deterministic reconciliation, not an agent:**
   (a) membership: extracted (schema, object) must exist in the parsed
   corpus / source catalog; (b) COLUMN RECONCILIATION: TMDL carries each
   report table's column list (columnIdentities/sourceColumn) and
   ScriptDom knows each proc's output columns — overlap score per
   lineage edge = objective cross-layer correctness signal; low overlap
   flags suspect edges; (c) per-shape known-answer fixtures in CI;
   (d) optional LLM triage ONLY for flagged residue and unknown-shape
   classification proposals — judgment assistant, never authority
   (ADR 0032: deterministic core, LLM edges).
