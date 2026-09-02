# Documentation Index

Summaries describe what each document governs, not its full contents.

## The dependency hierarchy (ruled 2026-09-01)

A strict three-tier chain, one direction, no cycles:

```
  ROOT       docs/AI_VIA_AXIOMS.md      the constitution (axm:*)
    ^
  BLUEPRINT  docs/architecture/*.md     topology + component boundaries
    ^                                   (each declares the axiom GROUPS
    |                                    it satisfies)
  EXECUTION  docs/decisions/*.md        each ADR names ONE component
```

**Decisions map first to an architecture component, then upward to the
axioms.** An ADR is an engineering choice about a *system component*, so
naming the component says *where* in the system the change lives — and
it keeps decision logs free of repeated philosophical preamble. The
audit trail reads: *ADR 0061 changes the run layer → specified in
SPEC.md → which satisfies axiom groups M and B.*

**Two citation handles.** The two axiom systems are distinct and their
group letters (B, D, R) collide, so always prefix:
`axm:M5` = the framework · `spec:C1` = the shadow spec.

Mechanized in `src/trace_registry.py` (`ARCHITECTURE_COMPONENTS` plus a
`component` per ADR), projected into
[TRACE_MAP.md](architecture/TRACE_MAP.md#the-dependency-hierarchy), and
enforced by three closure checks in `tests/test_trace_registry.py`: every
decision names a real component, every component declares real axiom
groups, and no axiom group goes untranslated.

**Truth hierarchy** (which document wins when two disagree) follows the
tiers: axioms > blueprints > decisions for *authority*; but for
*rationale*, the ADR is always the canonical home — blueprints summarize
and link, never restate. Two further rules:

- **Generated maps** — TRACE_MAP, TEST_MAP, PIPELINE_MAP, INTEGRATION_MAP,
  NOTEBOOK_MAP are compiled from `src/` registries by
  `scripts/generate_docs.py` and CI-checked for staleness. **Never edit
  these by hand** — fix the registry and regenerate.
- **Hand-authored narrative** is lowest authority; audited 2026-09-01,
  with superseded sections marked in place rather than deleted.

---

## The blueprint tier — `docs/architecture/` (13 files)

Every file here is a blueprint: it owns a slice of the system and
declares which axiom groups it satisfies. **The whole folder is listed
below — there is no unlisted file.** Two orphaned visual exports
(`PIPELINE_MAP_mmd.mmd`, `pipeline_map.svg`) were deleted 2026-09-01;
they were frozen at the superseded two-digit notebook numbering and
nothing referenced them.

Files are grouped by *what kind of thing they are*, which is also how
they behave under change.

### Authored — the design record (7)

Hand-written, highest interpretive value, lowest churn. These state
intent; they are audited, not generated.

| Document | ADRs | Governs |
| --- | --- | --- |
| [SPEC.md](architecture/SPEC.md) | 14 | The formal axiom system (groups A–H, P, Q, R), its notation, and the enforcement status of every axiom. **v0.7 — the standing instrument; cite as `spec:<id>`.** |
| [SPHERE.md](architecture/SPHERE.md) | 9 | The four shells inside→out, the change-propagation nervous system, the ownership economy, and the contracts split. |
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 6 | What the system is made of: the graph layers, the parse spine, the module map. The orientation document. |
| [USER_FLOW.md](architecture/USER_FLOW.md) | 6 | How a question moves from ask to answer, and how usage feeds the flywheel. |
| [QUESTION_MAP.md](architecture/QUESTION_MAP.md) | 5 | What the storage must support, audited by question family. *Not* a runtime routing table (ADR 0062). |
| [REFERENCE_ARCHITECTURE.md](architecture/REFERENCE_ARCHITECTURE.md) | 4 | The deployable reference: connector tiers, what runs per product tier, and the Azure consumption footprint. |
| [SOURCE_CONNECTORS.md](architecture/SOURCE_CONNECTORS.md) | 3 | Where customer logic lives, how it is collected, and how change is detected across re-ingests. |
| [DECISION_LANDING_MATRIX.md](architecture/DECISION_LANDING_MATRIX.md) | 2 | Which artifact each governance action produces in Purview/Collibra, and the OUTBOX that remembers it. |

### Generated — projections of the registries (5)

Compiled from `src/` registries by `scripts/generate_docs.py` and
CI-checked for staleness. **Never edit by hand** — fix the registry and
regenerate. They cannot drift, which is why they carry few ADRs: their
authority comes from the code they project.

| Document | Source registry | Governs |
| --- | --- | --- |
| [TRACE_MAP.md](architecture/TRACE_MAP.md) | `trace_registry.py` | The full chain: decision → component → axioms → code → tests. |
| [TEST_MAP.md](architecture/TEST_MAP.md) | `devtools/suite_map.py` | What every test proves, by ADR, standing law, and contract. |
| [PIPELINE_MAP.md](architecture/PIPELINE_MAP.md) | `notebook_registry.py` | The stage sequence, each stage's inputs/outputs, and row conservation across them. |
| [INTEGRATION_MAP.md](architecture/INTEGRATION_MAP.md) | `integration_registry.py` | What we parse in and publish out, with each write target's direction. |
| [NOTEBOOK_MAP.md](architecture/NOTEBOOK_MAP.md) | `notebook_registry.py` | Every notebook's contract entry and the question families it serves. |

> **Why the ADR counts are uneven.** SPEC and SPHERE carry 14 and 9
> because they are where cross-cutting law lands; the generated maps
> carry 1–2 because they *project* decisions rather than hold them. A
> low count is not a sign of an unimportant file — but a file with
> **zero** ADRs would be an orphan, and CI now fails on that
> (`test_hierarchy_every_decision_names_one_architecture_component`).

## The product tier — `docs/product/`

Kept separate from architecture by ruling (2026-09-01): architecture
answers *what the system is*; product answers *what a customer buys*.

| Document | Governs |
| --- | --- |
| [product/PRODUCT_TIERS.md](product/PRODUCT_TIERS.md) | **The product blueprint.** The four tiers (X-Ray, Bridge, Workbench, Run), packaging, sequencing, positioning. Pricing is parked, never invented. |
| [product/XRAY_ENGAGEMENT.md](product/XRAY_ENGAGEMENT.md) | The X-Ray delivery runbook — plain numbered steps an admin executes. |
| [product/SECURITY_WHITEPAPER.md](product/SECURITY_WHITEPAPER.md) | Security architecture, data handling, and the compliance posture, including the run-layer data boundary. |
| [product/REVIEWER_GUIDE.md](product/REVIEWER_GUIDE.md) | Orientation for Microsoft certification reviewers. |
| [product/MARKETPLACE_LISTING.md](product/MARKETPLACE_LISTING.md) | **TABLED 2026-09-01.** Draft listing copy; not in flight, and not a source of truth for anything. |

## Decision Records

Numbered ADRs in `docs/decisions/`; see [decisions/README.md](decisions/README.md) for the canonical index.

### Foundations — parsing, storage, identity

| ADR | Governs |
| --- | --- |
| [0001](decisions/0001-native-parsers-per-dialect.md) | Every SQL dialect is read by its own native parser, never by text extraction. |
| [0002](decisions/0002-delta-tables-over-graph-db.md) | Delta tables hold the graph instead of an external graph database. |
| [0003](decisions/0003-sql-fragments-not-full-sql.md) | Storage keeps `sql_fragments` rather than full SQL blobs. |
| [0014](decisions/0014-metric-logic-grounding-mandatory-dictionary.md) | The agent is grounded in `metric_logic`; the data dictionary is mandatory, not optional. |
| [0015](decisions/0015-metric-id-identity-propagation.md) | `metric_id` is the universal identity and every consumer must propagate it. |
| [0016](decisions/0016-case-insensitive-identifier-matching.md) | Identifier matching is case-insensitive, folded to uppercase. |
| [0033](decisions/0033-system-of-record-plus-projections.md) | Delta is the system of record; graph engines are read-model projections. |
| [0041](decisions/0041-m-parser-and-shape-registry.md) | The M mini-parser, the shape registry, and how fallout is captured. |
| [0053](decisions/0053-projection-column-lineage.md) | Column lineage at projection grain — the columns pass, v1. |
| [0060](decisions/0060-parse-is-the-plan.md) | The parse is the plan: traversal is deterministic and the LLM is confined to parsing. |

### Retrieval, traversal, and the graph

| ADR | Governs |
| --- | --- |
| [0017](decisions/0017-resolve-then-traverse-agent-retrieval.md) | Anchor resolution must complete before any graph query runs. |
| [0018](decisions/0018-materialized-closure-edges.md) | The metric→table closure is materialized as `USES_TABLE` edges. |
| [0019](decisions/0019-cte-descriptions-bottom-up.md) | CTE descriptions are generated bottom-up, ahead of metric descriptions. |
| [0020](decisions/0020-generator-compatibility-export.md) | The LPG export is shaped to the query generator's habits. |
| [0029](decisions/0029-dimension-layer-activation.md) | Dimension-layer activation: filter usage qualifies, scope-local aliases resolve. |
| [0030](decisions/0030-layered-retrieval-search-terms-first.md) | Layered retrieval puts search terms first and uses vectors only where the engine allows. |
| [0037](decisions/0037-completed-algebra-traverse.md) | The completed algebra — traverse, result-set kernels, closures as cache. |
| [0043](decisions/0043-diff-kernel-comparison-shape.md) | The diff kernel gives the founding comparison question its shape. |
| [0046](decisions/0046-anchor-discover-match-rank-the-human-picks.md) | Query composition is anchor, discover, match, rank — and the human picks their reality. |
| [0052](decisions/0052-reachability-contract.md) | The reachability contract: no graph payload is invisible by accident. |
| [0059](decisions/0059-graph-topology-axioms.md) | Graph topology axioms G1–G3: accounted connectivity, edge soundness, relative completeness. |

### Agent behavior, conversation, and operations

| ADR | Governs |
| --- | --- |
| [0005](decisions/0005-refuse-over-guess.md) | The agent refuses when no certified path exists rather than guessing. |
| [0032](decisions/0032-deterministic-core-llm-edges.md) | The core is deterministic; the LLM lives only at the edges. |
| [0034](decisions/0034-conversational-entry-edge.md) | The conversational entry edge sends language to the LLM and computation to code. |
| [0035](decisions/0035-agentic-conversation-deterministic-tools.md) | Agentic conversation runs over deterministic tools. |
| [0036](decisions/0036-operations-are-the-product.md) | Operations are the product: interpret, confirm, execute, display. |
| [0038](decisions/0038-interaction-layer-no-is-input.md) | The interaction layer treats "no" as input and lets users enter the graph. |
| [0044](decisions/0044-tree-contract-round-trip-descriptions.md) | The tree contract: faithful decision trees with blind round-trip verification. |
| [0045](decisions/0045-escalation-contract-human-checklist.md) | The escalation contract: no silent residue — unresolved outcomes become a human checklist. |
| [0050](decisions/0050-bounded-read-only-answer-loop.md) | The bounded read-only answer loop (amends 0036). |
| [0051](decisions/0051-one-mind-turn.md) | The one-mind turn: one conversation decides and the boundary enforces — six normative principles. |
| [0056](decisions/0056-decision-algebra.md) | The decision algebra: every answer ends in a decision, with a weighted taxonomy. |
| [0062](decisions/0062-the-dialogue-loop.md) | The dialogue loop: show, propose, ask, execute. |

### Governance, trust, and certification

| ADR | Governs |
| --- | --- |
| [0004](decisions/0004-two-stage-hitl-certification.md) | Certification is a two-stage human-in-the-loop process. |
| [0021](decisions/0021-certification-discloses-never-gates.md) | Certification discloses trust; it never gates availability. |
| [0022](decisions/0022-definition-versioning-certification-pins-a-version.md) | Definitions are versioned by content hash and certification pins one version. |
| [0023](decisions/0023-usage-weighted-governance-flywheel.md) | Usage is governance — the usage-weighted flywheel. |
| [0024](decisions/0024-layered-truth-personal-and-enterprise.md) | Layered truth: personal definitions live beside enterprise definitions. |
| [0025](decisions/0025-phi-scanning-at-ingestion.md) | PHI and hardcoded-literal scanning happens at ingestion; the LLM boundary is the gate. |
| [0026](decisions/0026-error-to-data-lineage.md) | Every error names the data that produced it. |
| [0027](decisions/0027-ownership-attribution-layered-sources.md) | Ownership attribution: manual entry is the floor, Entra ID enriches it. |
| [0031](decisions/0031-business-terms-weighted-plurality.md) | Business terms are a weighted plurality — citizen-endorsed, steward-arbitrated. |
| [0039](decisions/0039-errors-link-to-contracts.md) | Every error links to the contract it violated. |
| [0054](decisions/0054-governance-red-flags-governed-plurality.md) | Governance red flags and governed plurality — flag taxonomy and the citizen-stewardship disposition workflow. |

### Product, packaging, and go-to-market

| ADR | Governs |
| --- | --- |
| [0006](decisions/0006-graph-answers-purview-discovery.md) | The knowledge graph answers questions; Purview discovers reports. |
| [0007](decisions/0007-byot-library-deployment.md) | BYOT ships as a Python library (`.whl`). |
| [0008](decisions/0008-ship-tier-1-first.md) | Tier 1, the core agent, ships first. |
| [0009](decisions/0009-decouple-catalog-adapters.md) | Catalog integrations are optional, decoupled adapters. |
| [0010](decisions/0010-skip-founders-hub-level-3.md) | Skip Founders Hub Level 3 and go direct to Partner Center. |
| [0011](decisions/0011-static-guide-v1-copilot-v2.md) | A static install guide for v1; the AI co-pilot is deferred to v2. |
| [0012](decisions/0012-stay-in-current-repo.md) | The product is built on the existing repo — no rewrite. |
| [0013](decisions/0013-transactable-saas-on-marketplace.md) | List as transactable SaaS on the Microsoft commercial marketplace. |
| [0028](decisions/0028-contact-me-first-transactable-on-first-buyer.md) | List as Contact Me now; convert the same offer to transactable at the first-buyer signal. |
| [0040](decisions/0040-consumption-layer-reports-measures.md) | The consumption layer gives reports and measures a home. |
| [0057](decisions/0057-the-sphere.md) | The Sphere as architecture model, ownership economy, and the contracts split. |
| [0058](decisions/0058-self-service-contracts.md) | The self-service contracts for the Pro pillar — provenance, parameterization, execution. |
| [0061](decisions/0061-the-run-layer.md) | The run layer: Pro runs the confirmed definition, under an execution contract. |
| [0063](decisions/0063-product-tiers.md) | The product tiers — X-Ray, Bridge, Workbench, Run — under the law that artifacts land and chat doesn't. |

### Process, tooling, and test discipline

| ADR | Governs |
| --- | --- |
| [0042](decisions/0042-notebook-contract.md) | The notebook contract as a harness for the driver layer. |
| [0047](decisions/0047-shadow-spec-axiom-system.md) | The shadow specification Φ_AIVIA as the standing instrument against design drift. |
| [0048](decisions/0048-trace-registry-admin-graph-companion.md) | Declared zones, the trace registry, the admin graph, and the admin companion. |
| [0049](decisions/0049-ingestion-routes-live-extractor.md) | Filedrop, folders, and the live extractor are peer front doors for ingestion. |
| [0055](decisions/0055-designed-shape-corpus.md) | The designed shape corpus: spec-derived test data across ratified dimensions. |
