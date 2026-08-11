# Architecture Decision Records

One file per decision, numbered in rough chronological order. ADRs are the
**canonical home for rationale** — other documents (ARCHITECTURE.md, positioning,
guides) summarize and link here rather than restating the reasoning.

Format: Status / Date / Context / Decision / Consequences. A superseded ADR is
never deleted — its status changes and it links to its replacement.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-native-parsers-per-dialect.md) | Native parsers per SQL dialect (ScriptDom for T-SQL) | Accepted |
| [0002](0002-delta-tables-over-graph-db.md) | Delta tables over an external graph database | Accepted |
| [0003](0003-sql-fragments-not-full-sql.md) | Store sql_fragments, not full SQL blobs | Accepted |
| [0004](0004-two-stage-hitl-certification.md) | Two-stage human-in-the-loop certification | Accepted |
| [0005](0005-refuse-over-guess.md) | Agent refuses when no certified path exists | Accepted |
| [0006](0006-graph-answers-purview-discovery.md) | Knowledge graph answers; Purview discovers reports | Accepted |
| [0007](0007-byot-library-deployment.md) | BYOT deployment as a Python library (.whl) | Accepted |
| [0008](0008-ship-tier-1-first.md) | Ship Tier 1 (Core Agent) first | Accepted |
| [0009](0009-decouple-catalog-adapters.md) | Catalog integrations are optional adapters | Accepted |
| [0010](0010-skip-founders-hub-level-3.md) | Skip Founders Hub Level 3, go direct to Partner Center | Accepted |
| [0011](0011-static-guide-v1-copilot-v2.md) | Static install guide for v1; AI co-pilot deferred to v2 | Accepted |
| [0012](0012-stay-in-current-repo.md) | Build the product on the existing repo, no rewrite | Accepted |
| [0013](0013-transactable-saas-on-marketplace.md) | List as transactable SaaS on Microsoft Marketplace | Accepted |
| [0014](0014-metric-logic-grounding-mandatory-dictionary.md) | Ground the agent in `metric_logic`; data dictionary mandatory | Accepted |
| [0015](0015-metric-id-identity-propagation.md) | `metric_id` is the universal identity; consumers must propagate it | Accepted |
| [0016](0016-case-insensitive-identifier-matching.md) | Case-insensitive identifier matching, folded to uppercase | Accepted |
| [0017](0017-resolve-then-traverse-agent-retrieval.md) | Resolve-then-traverse: anchor resolution before any graph query | Accepted |
| [0018](0018-materialized-closure-edges.md) | Materialize the metric→table closure as USES_TABLE edges | Accepted |
| [0019](0019-cte-descriptions-bottom-up.md) | CTE descriptions, generated bottom-up, before metric descriptions | Accepted |
| [0020](0020-generator-compatibility-export.md) | Shape the LPG export to the query generator's habits | Accepted |
| [0021](0021-certification-discloses-never-gates.md) | Certification discloses trust; it never gates availability | Accepted |
| [0022](0022-definition-versioning-certification-pins-a-version.md) | Definition versioning: content-hash versions; certification pins a version | Accepted |
| [0023](0023-usage-weighted-governance-flywheel.md) | Usage is governance: the usage-weighted flywheel | Accepted |
| [0024](0024-layered-truth-personal-and-enterprise.md) | Layered truth: personal definitions beside enterprise definitions | Accepted |
| [0025](0025-phi-scanning-at-ingestion.md) | PHI and hardcoded-literal scanning at ingestion; LLM boundary is the gate | Accepted |
| [0026](0026-error-to-data-lineage.md) | Every error names its data: error-to-data lineage | Accepted |
| [0027](0027-ownership-attribution-layered-sources.md) | Ownership attribution: manual entry is the floor, Entra ID enriches | Accepted |
| [0028](0028-contact-me-first-transactable-on-first-buyer.md) | List as Contact Me now; convert to transactable at first-buyer signal | Accepted |
| [0029](0029-dimension-layer-activation.md) | Dimension layer activation: filter-usage qualifies, scope-local aliases resolve | Accepted |
| [0030](0030-layered-retrieval-search-terms-first.md) | Layered retrieval: search-terms first, vectors where the engine allows | Accepted (amended) |
| [0031](0031-business-terms-weighted-plurality.md) | Business terms: a weighted plurality, citizen-endorsed, steward-arbitrated | Accepted |
| [0032](0032-deterministic-core-llm-edges.md) | Deterministic Core, LLM Edges — the LLM translates, the data answers, the human decides | Accepted |
| [0033](0033-system-of-record-plus-projections.md) | System of record + projections: Delta is the record; graph engines are read models | Accepted |
| [0034](0034-conversational-entry-edge.md) | The conversational entry edge: language to the LLM, computation to code | Accepted |
