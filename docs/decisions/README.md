# Architecture Decision Records

One file per decision, numbered in rough chronological order. ADRs are the
**canonical home for rationale** — other documents (ARCHITECTURE.md, positioning,
guides) summarize and link here rather than restating the reasoning.

Format: Status / Date / Context / Decision / Consequences. A superseded ADR is
never deleted — its status changes and it links to its replacement.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-native-parsers-per-dialect.md) | Native parsers per SQL dialect (ScriptDom for T-SQL) | Accepted (amended 2026-08-19: total — fallback abolished, ban CI-enforced) |
| [0002](0002-delta-tables-over-graph-db.md) | Delta tables over an external graph database | Accepted |
| [0003](0003-sql-fragments-not-full-sql.md) | Store sql_fragments, not full SQL blobs | Accepted (amended 2026-08-19 by 0044: fragments stay as provenance, no longer the LLM's input) |
| [0004](0004-two-stage-hitl-certification.md) | Two-stage human-in-the-loop certification | Accepted |
| [0005](0005-refuse-over-guess.md) | Agent refuses when no certified path exists | Accepted |
| [0006](0006-graph-answers-purview-discovery.md) | Knowledge graph answers; Purview discovers reports | Accepted (amended 2026-08-19: reports are in-graph since 0040; Purview covers the rest of the estate) |
| [0007](0007-byot-library-deployment.md) | BYOT deployment as a Python library (.whl) | Accepted |
| [0008](0008-ship-tier-1-first.md) | Ship Tier 1 (Core Agent) first | Accepted |
| [0009](0009-decouple-catalog-adapters.md) | Catalog integrations are optional adapters | Accepted |
| [0010](0010-skip-founders-hub-level-3.md) | Skip Founders Hub Level 3, go direct to Partner Center | Accepted |
| [0011](0011-static-guide-v1-copilot-v2.md) | Static install guide for v1; AI co-pilot deferred to v2 | Accepted (amended 2026-08-20: trigger is now "admin graph projected", see 0048) |
| [0012](0012-stay-in-current-repo.md) | Build the product on the existing repo, no rewrite | Accepted |
| [0013](0013-transactable-saas-on-marketplace.md) | List as transactable SaaS on Microsoft Marketplace | Accepted |
| [0014](0014-metric-logic-grounding-mandatory-dictionary.md) | Ground the agent in `metric_logic`; data dictionary mandatory | Accepted |
| [0015](0015-metric-id-identity-propagation.md) | `metric_id` is the universal identity; consumers must propagate it | Accepted |
| [0016](0016-case-insensitive-identifier-matching.md) | Case-insensitive identifier matching, folded to uppercase | Accepted |
| [0017](0017-resolve-then-traverse-agent-retrieval.md) | Resolve-then-traverse: anchor resolution before any graph query | Accepted |
| [0018](0018-materialized-closure-edges.md) | Materialize the metric→table closure as USES_TABLE edges | Accepted |
| [0019](0019-cte-descriptions-bottom-up.md) | CTE descriptions, generated bottom-up, before metric descriptions | Accepted (amended 2026-08-19 by 0044: step input becomes tree facts; round-trip acceptance) |
| [0020](0020-generator-compatibility-export.md) | Shape the LPG export to the query generator's habits | Accepted |
| [0021](0021-certification-discloses-never-gates.md) | Certification discloses trust; it never gates availability | Accepted |
| [0022](0022-definition-versioning-certification-pins-a-version.md) | Definition versioning: content-hash versions; certification pins a version | Accepted |
| [0023](0023-usage-weighted-governance-flywheel.md) | Usage is governance: the usage-weighted flywheel | Accepted |
| [0024](0024-layered-truth-personal-and-enterprise.md) | Layered truth: personal definitions beside enterprise definitions | Accepted |
| [0025](0025-phi-scanning-at-ingestion.md) | PHI and hardcoded-literal scanning at ingestion; LLM boundary is the gate | Accepted |
| [0026](0026-error-to-data-lineage.md) | Every error names its data: error-to-data lineage | Accepted |
| [0027](0027-ownership-attribution-layered-sources.md) | Ownership attribution: manual entry is the floor, Entra ID enriches | Accepted |
| [0028](0028-contact-me-first-transactable-on-first-buyer.md) | List as Contact Me now; convert to transactable at first-buyer signal | Superseded 2026-08-11 (Contact Me unavailable; ship transactable) |
| [0029](0029-dimension-layer-activation.md) | Dimension layer activation: filter-usage qualifies, scope-local aliases resolve | Accepted |
| [0030](0030-layered-retrieval-search-terms-first.md) | Layered retrieval: search-terms first, vectors where the engine allows | Accepted (amended) |
| [0031](0031-business-terms-weighted-plurality.md) | Business terms: a weighted plurality, citizen-endorsed, steward-arbitrated | Accepted |
| [0032](0032-deterministic-core-llm-edges.md) | Deterministic Core, LLM Edges — the LLM translates, the data answers, the human decides | Accepted (description edge narrowed 2026-08-19 by 0044) |
| [0033](0033-system-of-record-plus-projections.md) | System of record + projections: Delta is the record; graph engines are read models | Accepted (amended 2026-08-19: read model ships with 0046) |
| [0034](0034-conversational-entry-edge.md) | The conversational entry edge: language to the LLM, computation to code | Superseded in part by 0035 (dialogue machinery); engine content survives |
| [0035](0035-agentic-conversation-deterministic-tools.md) | Agentic conversation over deterministic tools — computed answers, disclosed judgments, generated language | Superseded in part by 0036 (conversation protocol); tool layer survives as primitives |
| [0036](0036-operations-are-the-product.md) | Operations are the product: interpret → confirm → execute → display over a primitive algebra | Accepted |
| [0037](0037-completed-algebra-traverse.md) | The completed algebra: traverse (join=1 hop, closure=*), result-set kernels, closures as checkable cache | Accepted |
| [0038](0038-interaction-layer-no-is-input.md) | The interaction layer: no is input; users and concepts enter the graph — gated on the access-control ADR | Accepted (build gated) |
| [0039](0039-errors-link-to-contracts.md) | Every error links to its contract: error → contract → data; registry-derived precondition gates cite stable contract ids | Accepted |
| [0040](0040-consumption-layer-reports-measures.md) | The consumption layer: report + measure nodes from TMDL lineage; ghost dimension layer removed; fabric_pbi wired via lineage-exact publish | Accepted |
| [0041](0041-m-parser-and-shape-registry.md) | M mini-parser + shape registry: recognized shapes parse, unknown shapes are counted | Accepted |
| [0042](0042-notebook-contract.md) | The notebook contract: registry + six AST-enforced planks for the driver layer | Accepted |
| [0043](0043-diff-kernel-comparison-shape.md) | The diff kernel: step-aligned decomposition comparison; twins cache; op_compare | Accepted |
| [0044](0044-tree-contract-round-trip-descriptions.md) | The tree contract: faithful decision trees, blind round-trip verified descriptions — locked in red before implementation | Accepted (phased) |
| [0045](0045-escalation-contract-human-checklist.md) | The escalation contract: no silent residue — unresolved outcomes become the human checklist | Accepted (phased) |
| [0046](0046-anchor-discover-match-rank-the-human-picks.md) | Query composition: anchor, discover, match, rank — the human picks their reality; one engine for metadata and Pro | Accepted |
| [0047](0047-shadow-spec-axiom-system.md) | The shadow specification Φ_AIVIA: axiom system + enforcement homes; drift becomes a named, checkable violation | Accepted |
| [0048](0048-trace-registry-admin-graph-companion.md) | Declared zones, the trace registry, the admin graph, and the admin companion — the closed system made walkable | Accepted |
| [0049](0049-ingestion-routes-live-extractor.md) | Ingestion routes: filedrop, folders, and the live extractor are peer front doors | Accepted (retroactive record — first ghost finding of the 0048 totality check) |
| [0050](0050-bounded-read-only-answer-loop.md) | The bounded read-only answer loop: plan to the answer, caption answers, read-only auto-continue — 0035's shape in 0036's frame | Accepted (amends 0036) |
| [0051](0051-one-mind-turn.md) | The one-mind turn: one conversation decides, the boundary enforces — supersedes the three-call shape of 0036/0050, keeps their floors | Accepted |
| [0052](0052-reachability-contract.md) | The reachability contract: every graph payload reachable by a named op or excluded with a reason; ratifies SPEC §3b | Accepted |
| [0053](0053-projection-column-lineage.md) | Projection-grain column lineage: transform_to_column edges, resolved-only, conservation-counted | Accepted |
| [0054](0054-governance-red-flags-governed-plurality.md) | Governance red flags and governed plurality: misnomer/duplicate/cousin sweep over content hashes; citizen-stewardship disposition | Accepted |
| [0055](0055-designed-shape-corpus.md) | The designed shape corpus: spec-derived test data, category-partition over name × logic × scope | Accepted |
| [0056](0056-decision-algebra.md) | The decision algebra: every answer ends in a decision (typed deny, usage weights) | Accepted (typed deny amended by 0057) |
| [0057](0057-the-sphere.md) | The Sphere: four shells, the nervous system, the ownership economy, the contracts split | Accepted (design record; model re-homed to ../architecture/ARCHITECTURE.md by 0066) |
| [0058](0058-self-service-contracts.md) | The self-service contracts: provenance rungs, parameterization, execution floors for the Pro pillar | Accepted (builds with Pro) |
| [0059](0059-graph-topology-axioms.md) | The graph topology axioms: connected, sound, complete — measured, then formalized as SPEC Group Q | Accepted |
| [0060](0060-parse-is-the-plan.md) | The parse is the plan: parser-only LLM, deterministic traversal, correction flywheel | Accepted (one-shot confirm superseded by 0062; parse-never-generate core stands) |
| [0061](0061-the-run-layer.md) | The run layer: Pro runs the confirmed definition — read-only, ScriptDom-gated, rows never enter model context | Accepted (slice 1 built; GA gated on the output-side PHI gate) |
| [0062](0062-the-dialogue-loop.md) | The dialogue loop: show, propose, ask, execute — there are no question types | Accepted (supersedes 0060's one-shot confirm) |
| [0063](0063-product-tiers.md) | The product tiers: X-Ray, Bridge, Workbench, Run — artifacts land, chat doesn't | Accepted (TIER LOCK + scope lock) |
| [0064](0064-the-ledger-and-drift-axioms.md) | Group L: the ledger (append-only obeyed, aggregates derived) and drift-fires — closes the two crosswalk gaps | Accepted (all three calls ruled 2026-09-01; SPEC v0.8) |
| [0065](0065-promote-the-double-sided-function.md) | Promote §13 to Group T: the double-sided function as numbered law (T0 the law, T1–T3 the instances) | Accepted (SPEC v0.9) |
| [0066](0066-merge-sphere-into-architecture.md) | One system-model file: SPHERE merges into ARCHITECTURE — build status per section; kills the rival layer models | Accepted |
| [0067](0067-docs-are-data.md) | Docs are data: the record invariant + the prose ratchet; turn 1 = the axiom ledger (spec_registry) | Accepted |
| [0068](0068-landing-matrix-as-data.md) | The landing matrix as data: landing_registry + generated projection; 0063's two invariants mechanized | Accepted (content stays DRAFT v3 pending Bridge build) |
| [0069](0069-source-connectors-retire.md) | SOURCE_CONNECTORS retires into the integration registry — 8 rows + change/identity doctrine as data; first file the ratchet deletes | Accepted |
| [0070](0070-question-map-retires.md) | QUESTION_MAP retires into the notebook registry — FAMILY_RECORDS + cross-registry storage check + both-ways coverage | Accepted |
| [0071](0071-user-flow-retires.md) | USER_FLOW retires — the flywheel folds into ARCHITECTURE; nothing else was law; FCOTS/RLS recorded as unbuilt roadmap | Accepted |
| [0072](0072-crosswalk-goes-generated.md) | The crosswalk goes generated — Direction 1 from spec_registry (parents + why), Direction 2 from AXM_UNMAPPED | Accepted |
| [0073](0073-spec-goes-generated.md) | SPEC v1.0 — the spec becomes a projection of its own ledger; changelog freezes; statuses are data (final ratchet turn) | Accepted |
| [0074](0074-description-architecture-ratified.md) | The description architecture ratified: skeleton floor + gate acceptance (amends 0044 ph.3), terminal-step metric composition + per-file deliverable (amends 0019), provenance vocab, the wedge sample | **PROPOSED — 4 calls await Sunny** |
