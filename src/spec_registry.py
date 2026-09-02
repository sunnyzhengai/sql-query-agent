"""SPEC_REGISTRY — the axiom ledger as data (ADRs 0067 + 0073).

The eighth peer registry, COMPLETE as of the final ratchet turn (ADR
0073): every axiom's law formula, gloss, origin, framework parents,
declared checks, and status live here as fields. docs/architecture/
SPEC.md is the GENERATED projection (scripts/generate_docs.py, frame
prose in scripts/spec_frame.md); the ledger is the truth.

Field guide:
- law          the formula/statement — THE law (the gloss teaches)
- gloss        the plain-language teaching aid
- origin       the incident/ADR the axiom descends from
- parents      framework axioms (docs/AI_VIA_AXIOMS.md) it applies
- parent_note  the one-line why of that mapping
- checks       file paths that enforce it (existence-verified)
- checks_note  why checks is empty/partial, in SPEC's own words
- status       ENFORCED | PARTIAL | GATED | JUDGED (closed)
- status_note  the stated gap/caveat — honesty is a field

Extracted mechanically from SPEC.md v0.9 (2026-09-02) and spot-
verified; changing an axiom still requires an ADR (the amendment
rule); status-label changes require only the check's citation.
Closure checks: tests/test_spec_registry.py.
"""

from __future__ import annotations

# JUDGED = the human is the judge by construction (L3 stratum, T3).
STATUSES = ("ENFORCED", "PARTIAL", "GATED", "JUDGED")

GROUPS = {'A': 'Identity',
          'B': 'Soundness',
          'C': 'Completeness',
          'D': 'Derived structure',
          'E': 'Ask-time determinism',
          'F': 'The round trip',
          'G': 'Mechanism uniqueness',
          'H': 'Escalation',
          'L': 'The ledger',
          'P': 'The one-mind turn',
          'Q': 'Graph topology',
          'R': 'Ask-time interpretation + run boundary',
          'T': 'The double-sided function'}

SPEC_REGISTRY = {
    "A1": {
        "title": 'folding is idempotent',
        "law":
            '    ∀x ∈ Ident.  fold(fold(x)) = fold(x)',
        "gloss":
            'folding twice changes nothing — so it never matters how many '
            'times a value has been folded before matching.',
        "origin":
            'ADR 0016.',
        "parents": ['D2'],
        "parent_note":
            'one folding rule, one definition',
        "checks": ['tests/parser/test_identity.py'],
        "status": 'ENFORCED',
    },
    "A2": {
        "title": 'metric_id is a key',
        "law":
            '    ∀m, m′ ∈ Metric.  id(m) = id(m′) → m = m′',
        "gloss":
            'two metrics with the same id are the same metric, everywhere, '
            'including every downstream projection (Purview qualifiedName, '
            'exports).',
        "origin":
            'ADR 0015.',
        "parents": ['D3'],
        "parent_note":
            'identity -> exactly one owner per metric',
        "checks": ['tests/test_invariants.py', 'tests/test_table_contracts.py'],
        "status": 'ENFORCED',
    },
    "A3": {
        "title": 'fold-collisions are rejected loudly',
        "law":
            '    ∀s, s′ ∈ SourceRow.  fold(name(s)) = fold(name(s′)) ∧ s ≠ '
            's′  →  reject(load)',
        "gloss":
            'two inputs whose identities differ only by case are one object '
            'in a case-insensitive database — a data error, never two '
            'entries.',
        "origin":
            'ADR 0016.',
        "parents": ['D2'],
        "parent_note":
            'one folding rule, one definition',
        "checks": ['tests/test_invariants.py'],
        "status": 'ENFORCED',
    },
    "B1": {
        "title": 'witness totality (the anti-fabrication axiom)',
        "law":
            '    ∀e ∈ E_G.  ∃w ∈ D ∪ P ∪ M ∪ O ∪ Gov.  justifies(w, e)',
        "gloss":
            'every edge in the graph traces to a source fact — a dictionary '
            'row (join edges: a (PK, FK) pair), an AST node, a TMDL '
            'partition, an org declaration, a governance record. No edge is '
            'ever asserted from model memory or heuristic guess. (Refuse- '
            'over-guess, ADR 0005, stated as structure.)',
        "origin":
            'ADRs 0005, 0032, 0044.',
        "parents": ['B1'],
        "parent_note":
            "witness totality IS 'no claim without a witness'",
        "checks": ['tests/test_invariants.py', 'tests/test_tree_contract.py'],
        "checks_note":
            'PARTIAL by construction in builders; not yet a uniform '
            'declared invariant on every edge table',
        "status": 'PARTIAL',
        "status_note":
            'holds by construction for edges built in 03; not yet a uniform '
            'declared invariant on every edge table. Debt: every edge-table '
            'contract declares its witness reference.',
    },
    "B2": {
        "title": 'description provenance is total and closed',
        "law":
            '    ∀d ∈ Desc.  provenance(d) ∈ {round_trip_verified, '
            'template_fallback, flagged}',
        "gloss":
            'no description exists without a stated epistemic status; no '
            'fourth value; no NULL.',
        "origin":
            'ADR 0044 clause 6.',
        "parents": ['B1', 'J4'],
        "parent_note":
            'provenance closed -> every description judged',
        "checks": ['tests/test_tree_contract.py'],
        "status": 'PARTIAL',
        "status_note":
            'stated gap: provenance persistence on stored descriptions '
            "lands with 600's phase-3b wiring.  ---",
    },
    "C1": {
        "title": 'the frontier is enumerated (no undeclared source kind)',
        "law":
            '    ∀k ∈ SourceKinds.  (∃ F_k)  ∨  (∃ exclusion(k))',
        "gloss":
            'every kind of source fact — dictionary join rows, dictionary '
            'descriptions, SQL decision sites, TMDL partitions, DAX column '
            'refs, org reference tables — either has a declared extractor '
            'or a recorded "deliberately not extracted, because…". There is '
            'no third state ("nobody thought about it").',
        "origin":
            "the EMR-joins incident: `J_D` (the dictionary's join map) had "
            'no functor and no exclusion — the violation existed at the '
            'inventory level before any code ran, which is why only a code- '
            'walk found it. *Seeded exclusion rows (ruled by Sunny '
            '2026-08-19):* Snowflake views and Databricks/dbt models are '
            '**excluded for the Fabric-native v1** — real hospital estates '
            'increasingly run them, so the rows exist to make the roadmap '
            'pressure visible, per ADR 0001 each future dialect gets its '
            'own native parser.',
        "parents": ['D1'],
        "parent_note":
            'the enumerated frontier -> nothing unreachable',
        "checks": ['tests/test_extraction_registry.py'],
        "status": 'ENFORCED',
        "status_note":
            '`src/extraction_registry.py` + '
            '`tests/test_extraction_registry.py` (functor XOR exclusion per '
            'row; conservation citations resolve; the joins incident pinned '
            'as the acceptance test; every reference structure D/P/M/O/Gov '
            'covered).',
    },
    "C2": {
        "title": 'conservation per extractor (no third bucket)',
        "law":
            '    ∀k.  dom(R_k) = handled_k ⊎ fallout_k',
        "gloss":
            'every source row is either extracted or counted as fallout — '
            'the sum matches the total, and nothing vanishes.',
        "origin":
            'ADR 0044 clause 1 (decision sites: `handled + unextracted == '
            'total`), ADR 0041 (M shapes), ADR 0045 (fallout resolution).',
        "parents": ['R1'],
        "parent_note":
            'handled + fallout = total (conservation)',
        "checks": ['tests/test_tree_contract.py', 'tests/mquery/test_mquery.py'],
        "status": 'PARTIAL',
        "status_note":
            "enforced for trees and M shapes; C1's registry (now ENFORCED) "
            'carries a conservation citation per row and the citations are '
            'checked to resolve — full per-row equation checks remain the '
            'stated gap.',
    },
    "C3": {
        "title": 'images land in the graph',
        "law":
            '    ∀k.  F_k(handled_k) ⊆ G',
        "gloss":
            'what an extractor extracts actually arrives — no silent drops '
            'between extraction and the graph.',
        "parents": ['R1'],
        "parent_note":
            'handled + fallout = total (conservation)',
        "checks": ['tests/test_invariants.py'],
        "status": 'PARTIAL',
        "status_note":
            '(same universality note as C2).',
    },
    "C4": {
        "title": 'leaf grounding (the termination axiom)',
        "law":
            '    ∀f ∈ P.  ∀ℓ ∈ leaves(tree(f)).   ℓ ∈ T_D ∪ T_org   ∨   ℓ ∈ fallout(f)\n'
            '    completely_parsed(f)  ⟺  fallout(f) = ∅',
        "gloss":
            'after internal references resolve (CTEs and temp tables '
            'resolve to their defining steps), every remaining leaf of '
            'every parsed tree must bottom out on a vendor table or an org '
            'reference table. Anything else — an unresolvable name, a '
            'dynamic-SQL branch — is counted fallout, and "completely '
            'parsed" is a **computed per-file verdict**, never an '
            'impression. Gives the funnel a new honest number: fraction of '
            'files fully grounded.',
        "origin":
            'Sunny\'s blind reconstruction, 2026-08-19 ("any AST tree branch '
            "that does not end in EMR tables or org's custom reference "
            'table is not a completely parsed sql file").',
        "parents": ['R1', 'D1'],
        "parent_note":
            'leaf grounding: termination + reachability',
        "checks": ['tests/governance/test_leaf_grounding.py'],
        "status": 'ENFORCED',
        "status_note":
            '`src/governance/leaf_grounding.py` (verdict + fraction + '
            'escalated fallout, stage `500_leaf_grounding`), wired into '
            '500; `tests/governance/test_leaf_grounding.py`. First '
            'recorded-corpus verdict: 27/28 files completely parsed '
            '(USP_Severe_Sepsis reads 6 tables absent from the dictionary — '
            'the number is already working).',
    },
    "D1": {
        "title": 'materialized closures equal the fixpoint',
        "law":
            '    reach(x,y) ← dep(x,y)\n'
            '    reach(x,z) ← reach(x,y) ∧ dep(y,z)\n'
            '    uses(m,t)  ← calc(m,s) ∧ reach(s,s′) ∧ reads(s′,t)\n'
            '    Axiom:  uses_materialized = lfp(uses)',
        "gloss":
            'the precomputed USES_TABLE / closure edges must equal what a '
            'live traversal would compute. The closure is a **cache with a '
            'proof obligation**, not a second truth.',
        "origin":
            'ADRs 0018, 0033, 0037 (closures reclassified as checkable '
            'cache; the 5-of-13 undercount was an unstated D1 violation).',
        "parents": ['D4'],
        "parent_note":
            'closure = shape-defined derivation',
        "checks": ['tests/test_recorded_pipeline.py'],
        "checks_note":
            'oracles ENFORCED; the general closure-vs-live diff is UNBOUND '
            '(ADR 0037 stated gap)',
        "status": 'PARTIAL',
        "status_note":
            '(oracles ENFORCED; general diff UNBOUND).',
    },
    "D2": {
        "title": 'count oracles',
        "law":
            '    |{m : uses(m, HOSPITAL_ENCOUNTERS)}| = 13,   … (fixture '
            'constants)',
        "gloss":
            'certified cardinalities from recorded fixtures pin the truth; '
            'a derivation change that alters a known count is a red build, '
            'never a silent undercount.',
        "origin":
            'ADR 0018.',
        "parents": ['J1'],
        "parent_note":
            'count oracles = founder-defined correctness',
        "checks": ['tests/test_recorded_pipeline.py'],
        "status": 'ENFORCED',
    },
    "D3": {
        "title": 'projections are functions of the record',
        "law":
            '    ∀ projection Π ∈ {LPG export, Eventhouse catalog, term nodes,\n'
            '                      usage-layer edges, Fabric Graph read model}.\n'
            '        Π = f_Π(Record),   f_Π deterministic and recomputable',
        "gloss":
            'no projection carries information absent from the Delta '
            'record; every projection can be rebuilt at will and can never '
            'drift into a second source of truth. This is why business '
            'terms live in `gov_business_terms` (durable, human-owned) and '
            'are *designed to be projected* into the graph each build — the '
            'graph is overwritten every run, so anything living only in it '
            'would be destroyed. AUDIT FIND (2026-08-19): the Term '
            'projection is not yet implemented (no Term nodes, no '
            'implements edges) — recorded as an EXTRACTION_REGISTRY '
            'exclusion until the builder lands; the gov record and '
            'candidate mining exist.',
        "origin":
            'ADRs 0031, 0033, 0038 (usage-layer discipline).',
        "parents": ['D3'],
        "parent_note":
            'projections have one owning record',
        "checks": [],
        "checks_note":
            'by construction in the builders; no general recompute-and-diff '
            'check yet (SPEC stated gap)',
        "status": 'PARTIAL',
    },
    "E1": {
        "title": 'the path space is finite and enumerable',
        "law":
            '    G_tech finite ∧ static\n'
            '      ⟹  Paths_k(A) = { walks of length ≤ k over joinable, connecting A }\n'
            '          is finite and mechanically enumerable, for any anchor set A',
        "gloss":
            "the vendor's join map is a known, finite structure. Given "
            'anchored nodes, all candidate paths between them are **facts '
            'waiting to be enumerated** — a search problem, not a synthesis '
            'problem. Nothing needs to "generate" a path, so nothing '
            'stochastic may.',
        "origin":
            "ADR 0046 (Sunny's position, settled 2026-08-19).",
        "parents": ['S3'],
        "parent_note":
            'the path space is data-shaped, hence enumerable',
        "checks": ['tests/test_spec_gates.py'],
        "status": 'PARTIAL',
        "status_note":
            'the deterministic primitive is ENFORCED '
            '(`src/discovery/paths.py` + `tests/test_spec_gates.py`, '
            '1.33.0: replay-deterministic simple-path enumeration over the '
            'join map, both orientations, hop-capped presentation-never- '
            'pruning). Stated gap: the composed 0046 engine '
            '(anchor→discover+match→rank→pick) is not built.',
    },
    "E2": {
        "title": 'replay determinism for retrieval components',
        "law":
            '    resolve, discover, rank are functions:\n'
            '      same (token, catalog_state)  ⟹  byte-identical output',
        "gloss":
            'an LLM fails this **by construction** (it samples) — so it is '
            'excluded from these seats by type, not by policy. The '
            'recurring "should the LLM help compose the query" debate '
            'terminates here: the component violates E2.',
        "origin":
            'ADRs 0032 (the testable definition of deterministic), 0046.',
        "parents": ['J2'],
        "parent_note":
            'replay determinism = the computable type',
        "checks": ['tests/orchestrator/test_core.py'],
        "status": 'PARTIAL',
    },
    "E3": {
        "title": 'the decision typing rule (which decider is legal where)',
        "law":
            '    decider(d) may be an LLM\n'
            '      ⟺  codomain(d) is language  ∨  ground_truth(d) is human intent\n'
            '    a right answer computable from data  ⟹  decider(d) must satisfy E2',
        "gloss":
            'three kinds of decision — computable (code only), judgment '
            '(human), linguistic (LLM). An LLM decision is acceptable only '
            'where its error mode is visible and bounded. You TEST code; '
            'you can only MEASURE models.',
        "origin":
            'ADR 0035 (the taxonomy), 0032, 0046.',
        "parents": ['M5', 'J2'],
        "parent_note":
            'the decision-typing rule, verbatim',
        "checks": ['tests/test_methodology.py'],
        "status": 'ENFORCED',
        "status_note":
            'for the control path; each new component declares its decider '
            'kind at review.',
    },
    "E4": {
        "title": 'pick containment (the human picks, structurally)',
        "law":
            '    pick_human(S) ∈ S        and  no auto-pick:  |S| = 1 does '
            'not bypass',
        "gloss":
            'the chosen candidate must be one of those presented — enforced '
            'by code, so a silent top-1 pick or an out-of-list answer is '
            'impossible, not just discouraged. One candidate is treated the '
            'same as ten.',
        "origin":
            'ADRs 0032, 0046 (reaffirmed in strongest form).',
        "parents": ['M5'],
        "parent_note":
            'intent decisions bind to the human',
        "checks": [],
        "checks_note":
            'structural pick validation in the orchestrator (prose binding, '
            'no file named; 0046 re-binds)',
        "status": 'PARTIAL',
        "status_note":
            '(enforced where the orchestrator surface runs; the 0046 engine '
            're-binds it).',
    },
    "E5": {
        "title": 'filter grounding (the 123/456 lesson)',
        "law":
            '    ∀v ∈ FilterValues(answer ∪ executed SQL).\n'
            '        v ∈ Sites ∪ ValueSets ∪ HumanInput',
        "gloss":
            'every literal value in any presented or executed filter comes '
            'from a stored decision site, a value-set table (T_org), or the '
            'human — never from model memory. Carries the shared- '
            'schema/varying-values fact: the EMR schema travels between '
            'hospitals; the values never do.',
        "origin":
            "ADR 0046 grounding rules; ADR 0044's captured fabrications.",
        "parents": ['B1'],
        "parent_note":
            'filter values need witnesses',
        "checks": ['tests/test_spec_gates.py'],
        "status": 'PARTIAL',
        "status_note":
            'the deterministic primitive is ENFORCED '
            '(`src/discovery/grounding.py`, 1.33.0: refuse-over-guess on '
            'any value without a source). Stated gap: binds to real '
            'presented/executed filters when the 0046 engine composes them.',
    },
    "E6": {
        "title": 'presentation honesty',
        "law":
            '    rank PRESENTS, never prunes (caps are disclosed)\n'
            '    displayed signals ∈ { closeness (relative), usage weight (derived),\n'
            '                          certification status }\n'
            '    probabilities are banned display vocabulary',
        "gloss":
            '"confidence" in conversation always means derived edge/usage '
            'weights — never a probability the model invented. Closeness is '
            'relative geometry, not a likelihood.',
        "origin":
            'ADRs 0032 (threshold is a volume control), 0046 (ranking '
            'presents, never prunes)',
        "parents": ['B2', 'B3'],
        "parent_note":
            'boundary honesty + bounded quantified claims',
        "checks": ['tests/orchestrator/test_core.py', 'tests/orchestrator/test_caption_gate.py'],
        "status": 'ENFORCED',
        "status_note":
            '(plan surface) — the STAMPED HEADLINE is rendered by code from '
            "typed metadata (E6 amendment 2026-08-20, stamp don't audit); "
            'the caption LINT is retained as defense-in-depth, MEASURED not '
            'tested; stated residue: the superseded agent-loop surface (ADR '
            '0035) is unstamped pending its demolition',
    },
    "F": {
        "title": 'the round trip (ADR 0044 as equations)',
        "law":
            '    desc  = τ(facts(tree), dict)          τ = translator;  SQL ∉ inputs(τ)\n'
            '    tree′ = ρ(desc, dict)                 ρ = verifier;    SQL, tree ∉ inputs(ρ)\n'
            '    ACCEPT(desc)  ⟺  κ(tree′) = κ(tree)   κ and = are deterministic code\n'
            '    after N rejections:  desc := τ₀(tree),  provenance := template_fallback',
        "gloss":
            'the translator renders typed tree facts (never raw SQL) into '
            'prose; a blind verifier reconstructs a tree from the prose '
            'alone; a deterministic judge compares canonicalized trees; '
            'exhausted retries degrade to the stilted-but-true template. '
            'The blindness clauses are **information-flow constraints**: '
            'the SQL is not merely ignored — it is unreachable from the '
            "function's inputs (enforced at the signature, the "
            'noninterference trick).',
        "origin":
            'ADR 0044 clauses 2-6',
        "parents": ['J4'],
        "parent_note":
            "the round trip is the description's oracle",
        "checks": ['tests/test_tree_contract.py'],
        "status": 'ENFORCED',
        "status_note":
            "all six clause gates flipped 1.31.0-1.32.0; stated gap: 600's "
            'production wiring of the verifier (reconstructor callback + '
            'provenance persistence) is phase 3b',
    },
    "G1": {
        "title": 'one owner per capability',
        "law":
            '    own : C → M  is a function            (single-valued: no capability\n'
            '                                           has two implementing modules)',
        "gloss":
            'the registry itself is the proof — a second row claiming an '
            'owned capability is a registry validation error, caught before '
            'any code review.',
        "parents": ['D2'],
        "parent_note":
            'one owner per capability, mechanized',
        "checks": ['tests/test_capability_registry.py'],
        "status": 'ENFORCED',
        "status_note":
            '`src/capability_registry.py` (unique keys, one owner prefix '
            'per row) + `tests/test_capability_registry.py`.',
    },
    "G2": {
        "title": 'sanctioned powers only (import-graph inclusion)',
        "law":
            '    Uses ⊆ S,   where  S = { (own(c), p) : c ∈ C, p ∈ prims(c) }\n'
            '    equivalently:  Uses ∖ S = ∅',
        "gloss":
            '`Uses` = every (module, powerful-primitive) pair actually '
            'present in the code, computed from the AST. `S` = the '
            'sanctioned pairs. The check is set difference = empty. '
            'Powerful primitives: regex, SQL/M parsers, LLM clients, '
            'embedding calls, Delta writes.',
        "parents": ['D2'],
        "parent_note":
            'one owner per capability, mechanized',
        "checks": ['tests/test_capability_registry.py',
                   'tests/test_native_parser_law.py',
                   'tests/test_notebook_contract.py'],
        "status": 'ENFORCED',
        "status_note":
            'the general registry + whole-`src/` inclusion check shipped at '
            'adoption: '
            '`test_capability_registry.py::test_g2_sanctioned_powers_only` '
            'computes Uses from the AST and asserts `Uses ∖ S = ∅` for '
            'pythonnet/clr/requests/httpx (+ the absolute sqlglot/sqlparse '
            'ban, which no row may ever sanction).',
    },
    "G3": {
        "title": 'no undeclared power',
        "law":
            '    ∀ use of p ∈ PowerPrims.  ∃c.  p ∈ prims(c)',
        "gloss":
            'every use of a dangerous primitive maps back to a declared '
            'capability — nothing powerful is used "off the books."',
        "parents": ['D2'],
        "parent_note":
            'one owner per capability, mechanized',
        "checks": ['tests/test_capability_registry.py'],
        "status": 'ENFORCED',
        "status_note":
            'same inclusion check (an unowned use fails with the registry '
            'named) + `test_g3_banned_parsers_have_no_owner`.  *Honest '
            'residue:* G-group catches the high-risk primitive classes. Two '
            'innocent pure-Python functions independently reimplementing '
            'the same logic (a second fold, a second hash) are not '
            'mechanically detectable — mitigated by owning primitive '
            'operations in single modules and by review. Stated so nobody '
            'mistakes the fence for a force field.  ---',
    },
    "H1": {
        "title": 'fallout resolution is total and closed',
        "law":
            '    resolution : FalloutRow → {auto_resolved, escalated} '
            '(total; no NULL)',
        "gloss":
            'everything the pipeline cannot resolve is either recovered by '
            "the pipeline or lands on a human's checklist — counted is not "
            'the same as owned.',
        "origin":
            'ADR 0045',
        "parents": ['R3'],
        "parent_note":
            'novelty escalates',
        "checks": ['tests/test_escalation_contract.py'],
        "status": 'GATED',
        "status_note":
            'strict-xfail skeletons, 4 clauses (status shared with H2)',
    },
    "H2": {
        "title": 'novelty always escalates',
        "law":
            '    outcome(x) = unknown  →  resolution(x) = escalated',
        "gloss":
            'everything the pipeline cannot resolve is either recovered by '
            "the pipeline or lands on a human's checklist — counted is not "
            'the same as owned.',
        "origin":
            'ADR 0045.',
        "parents": ['R3'],
        "parent_note":
            'novelty escalates',
        "checks": ['tests/test_escalation_contract.py'],
        "status": 'GATED',
    },
    "L1": {
        "title": 'append-only is declared AND obeyed',
        "law":
            '    ∀t ∈ Tables.  write_mode(t) ∈ {overwrite, append}\n'
            '    ∧  write_mode(t) = append  →  no writer of t uses overwrite semantics',
        "gloss":
            'a table that declares itself a ledger may only ever grow. The '
            'declaration existed since the beginning '
            '(`TABLE_REGISTRY.write_mode`; 39 overwrite / 10 append) and '
            "the label's legality was checked — but nothing checked the "
            'label was HONOURED. An append flipped to overwrite destroys '
            "every prior run's telemetry silently.",
        "origin":
            'ADR 0064; the 2026-08-15 audit note in 500_validate ("a '
            'failing append must RAISE — never silently become an '
            'overwrite").',
        "parents": ['R4'],
        "parent_note":
            'the ledger may only grow',
        "checks": ['tests/test_ledger_contract.py', 'tests/test_table_contracts.py'],
        "status": 'ENFORCED',
    },
    "L2": {
        "title": 'aggregates are derived, never stored',
        "law":
            '    ∀a ∈ Aggregates.  a = f(Events),  f deterministic and recomputable\n'
            '    no counter is mutated in place',
        "gloss":
            'usage weights, funnel counts, and every governance number are '
            'recomputed from the append-only log — never incremented on a '
            'stored row. This is D3 (projections are functions of the '
            'record) applied to COUNTS, and it is the law the purged '
            'UsageTracker broke.',
        "origin":
            "ADR 0064; the purged in-place usage counter (`axm:R4`'s "
            'descent), which had no regression guard until now — the '
            'corpse-to- fixture rule (`axm:J3`) applied retroactively.',
        "parents": ['R4', 'D3'],
        "parent_note":
            'aggregates derived, never stored',
        "checks": ['tests/test_ledger_contract.py'],
        "status": 'ENFORCED',
    },
    "L3": {
        "title": 'every declaration has a firing mechanism',
        "law":
            '    ∀d ∈ Declarations.  ∃m.  fires(m, divergence(d))',
        "gloss":
            "§3b's third question, promoted from a review ritual to an "
            'axiom: when reality diverges from a declaration, something '
            'MECHANICAL fires — a red build, a checklist row, a funnel bar. '
            '"Someone would notice" is the definition of a missing feedback '
            'loop.',
        "origin":
            'ADR 0064, closing axm:R2',
        "parents": ['R2'],
        "parent_note":
            'every declaration has a firing mechanism',
        "checks": ['tests/test_spec_gates.py'],
        "checks_note":
            'ENFORCED by citation (0059 Q3 precedent): the registry closure '
            'checks, funnel, reachability',
        "status": 'ENFORCED',
        "status_note":
            '(by citation — the 0059 Q3 precedent): the seven registry '
            'closure checks, the funnel, and reachability ARE the firing '
            'mechanisms; stated gap: a NEW declaration acquires its '
            'mechanism by review (section 3b), not yet by a mechanical '
            'check that one exists',
    },
    "P1": {
        "title": 'one conversation decides a turn; no separate planner/judge/c',
        "law":
            'one conversation decides a turn; no separate '
            'planner/judge/captioner minds',
        "parents": ['M2'],
        "parent_note":
            'one mind, full evidence',
        "checks": ['tests/orchestrator/test_turn_engine.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "P2": {
        "title": 'full tool results enter the SAME history and persist across ',
        "law":
            'full tool results enter the SAME history and persist across '
            'rounds and turns; compaction degrades oldest to stamped '
            'headline + totals, never drops',
        "parents": ['M2'],
        "parent_note":
            'one mind, full evidence',
        "checks": ['tests/orchestrator/test_turn_engine.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "P3": {
        "title": 'thinking room — no forced tool_choice except the final typed',
        "law":
            'thinking room — no forced tool_choice except the final typed '
            'verdict',
        "parents": ['M3'],
        "parent_note":
            'thinking room',
        "checks": ['tests/orchestrator/test_turn_engine.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "P4": {
        "title": 'no question-family casebook anywhere — invariants + tool sem',
        "law":
            'no question-family casebook anywhere — invariants + tool '
            'semantics only',
        "parents": ['M4'],
        "parent_note":
            'no question-shaped control flow',
        "checks": ['tests/orchestrator/test_turn_engine.py', 'tests/test_methodology.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "P5": {
        "title": 'honesty at the boundary only',
        "law":
            'honesty at the boundary only: headlines, caption gate, '
            'machine-verified evidence-quote verdict, read-only dispatch, '
            'write plan-confirm, caps as code',
        "parents": ['B2'],
        "parent_note":
            'honesty at the boundary, never the interior',
        "checks": ['tests/orchestrator/test_turn_engine.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "P6": {
        "title": 'failure is observation',
        "law":
            'failure is observation: tool errors return into the '
            'conversation; caps bound flailing',
        "parents": ['M1'],
        "parent_note":
            'failure as observation = loop-shape capability',
        "checks": ['tests/orchestrator/test_turn_engine.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "Q1": {
        "title": 'accounted connectivity',
        "law":
            'accounted connectivity: components enumerated every build; '
            'exactly one PRINCIPAL derived component; foundation-only '
            'islands legitimate under the FOUNDATION EXCEPTION (enumerated, '
            'never findings); degree-0 forbidden (enumerated exclusion: the '
            'govmeta:sweep receipt)',
        "parents": ['D1'],
        "parent_note":
            'accounted connectivity -> nothing unreachable',
        "checks": ['tests/graph/test_topology.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "Q2": {
        "title": 'edge soundness',
        "law":
            'edge soundness: every edge referential AND provenance-mapped — '
            'parsed / declared / derived / asserted, exactly one class per '
            'edge type (EDGE_PROVENANCE, 0052-pattern totality)',
        "parents": ['B1'],
        "parent_note":
            'every edge provenance-mapped',
        "checks": ['tests/graph/test_topology.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "Q3": {
        "title": 'relative completeness',
        "law":
            'relative completeness: every completeness claim is a '
            'conservation equation (refs = minted ⊎ dropped; swept = '
            'flagged ⊎ clean ⊎ excluded; matrix/reachability totality) with '
            'ask-time boundary disclosure; absolute completeness claims '
            'forbidden',
        "parents": ['B3'],
        "parent_note":
            'completeness claims are conservation equations',
        "checks": [],
        "checks_note":
            'ENFORCED by citation — the existing conservation asserts '
            'predate the axiom (ADR 0059)',
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED (by citation — no new mechanism needed; the equations '
            'predate the axiom)',
    },
    "R1": {
        "title": 'Parse, never generate',
        "law":
            '**Parse, never generate.** The LLM maps the sentence to entity '
            'phrases + relation words drawn from a closed lexicon; it never '
            'composes a query, never selects a route, never authors a '
            'verdict. A model-composed query cannot be stamped; a parse can '
            'be confirmed.',
        "parents": ['M4', 'M5'],
        "parent_note":
            'parse-never-generate: free composition + typing',
        "checks": ['tests/orchestrator/test_parse_plan.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED (prototype + measured gate: PARSE_EXPERIMENT, 7/7 '
            'oracles vs 5/7)',
    },
    "R2": {
        "title": 'No question types',
        "law":
            "**No question types.** The answer's shape EMERGES from the "
            'matched subgraph; no enumeration of question shapes, classes, '
            "or families may exist in the control path. (0062's abolition; "
            'the P4 casebook ban generalized from prompts to structure.)',
        "parents": ['M4'],
        "parent_note":
            'no question types',
        "checks": ['tests/test_methodology.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED for the control path',
    },
    "R3": {
        "title": 'Interpretation confirms before it executes',
        "law":
            '**Interpretation confirms before it executes.** Every reading '
            'renders on glass and waits for the click; fuzzy grounding may '
            "NOMINATE, only the human's click EXECUTES. Plan-confirm- "
            'execute-display applied to the interpretation itself (0060 '
            'call 1, RULED: confirm every parse).',
        "parents": ['B4'],
        "parent_note":
            'irreversible acts confirm - applied to interpretation',
        "checks": ['tests/webapp/test_app.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "R4": {
        "title": 'No dead ends',
        "law":
            '**No dead ends.** Every state — failure, empty, ambiguity, '
            'exhaustion — renders as action items; an exhausted loop '
            'becomes a CAPTURED DEMAND handoff to a developer, never a '
            'shrug. The escalation door stands at every round.',
        "parents": ['R3'],
        "parent_note":
            'no dead ends -> novelty escalates',
        "checks": ['tests/webapp/test_app.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "R5": {
        "title": 'Certain answers',
        "law":
            '**Certain answers.** Under ambiguity, execute only what every '
            'surviving reading supports; only genuine ambiguity spawns a '
            'clarify item. We iterate on UNDERSTANDING, never on mechanical '
            'execution steps.',
        "parents": ['B3'],
        "parent_note":
            'certain answers = bounded claims under ambiguity',
        "checks": [],
        "checks_note":
            'the no-nag boundary in the loop; no general multi-reading '
            'intersection check (SPEC: PARTIAL)',
        "status": 'PARTIAL',
        "status_note":
            'PARTIAL — the rule is implemented in the loop; no general '
            'multi-reading intersection check',
    },
    "R6": {
        "title": 'Rows never enter model context',
        "law":
            '**Rows never enter model context.** Results render to the '
            "USER'S GLASS; the model sees machine stamps only — row count, "
            'column schema, elapsed, as-of, source. P5 absolute, extended '
            'to result sets.',
        "parents": ['B2'],
        "parent_note":
            'rows never enter model context',
        "checks": ['tests/test_run_layer.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "R7": {
        "title": 'Nothing is generated; the confirmed SQL is what runs',
        "law":
            '**Nothing is generated; the confirmed SQL is what runs.** '
            'Byte-for-byte the parsed, displayed step the user confirmed — '
            'not NL2SQL. Read-only by construction: a dedicated read-only '
            'credential AND a ScriptDom statement-type check (the native- '
            'parser law: the parser decides, never regex). DML/DDL/EXEC → '
            'typed refusal.',
        "parents": ['B4'],
        "parent_note":
            'confirmed-only execution',
        "checks": ['tests/test_run_layer.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "R8": {
        "title": 'Sampling is machine-labelled',
        "law":
            '**Sampling is machine-labelled.** Every result carries `N rows '
            '· TOP <cap> · as of <timestamp> · source <db> · read-only`, '
            'composed by code, never model-written. The cap is a disclosed '
            "fact, not a hidden truncation (E6's presentation honesty, "
            'applied to data).',
        "parents": ['B3'],
        "parent_note":
            'machine-labelled sampling',
        "checks": ['tests/test_run_layer.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED',
    },
    "T0": {
        "title": 'the round-trip law',
        "law":
            '    ∀t ∈ Tree.  κ(ρ(τ(t))) = κ(t)        modulo '
            'canonicalization',
        "gloss":
            'meaning rendered from structure must translate back to the '
            "same structure. Each direction's correctness is certified by "
            'running the opposite direction — which is why no instance may '
            'be checked by inspecting only its own output.',
        "origin":
            'ADR 0044 (instance 1), generalized here.',
        "parents": ['J4'],
        "parent_note":
            'the round-trip law: kappa(rho(tau(t))) = kappa(t)',
        "checks": [],
        "checks_note":
            'instantiated as T1-T3, each with its own judge; no single '
            'check by design (ADR 0065)',
        "status": 'PARTIAL',
        "status_note":
            'instantiated three times below with three different judges; T1 '
            'is ENFORCED, T2 PARTIAL, T3 human-judged by construction. The '
            'law is only as strong as its weakest instance, and that is '
            'stated rather than averaged away.  The law is instantiated '
            '**three times**, at three grains, with three judges:  | # | '
            'Instance | τ | ρ | Judge | Status | |---|---|---|---|---|---| '
            '| **T1** | Descriptions (ADR 0044) | translator | blind '
            'verifier | deterministic tree diff (κ-equality) | **ENFORCED** '
            '— `tests/test_tree_contract.py`, all six clause gates green; '
            'this is `spec:F` stated as a member of the family | | **T2** | '
            'SQL stitching (ADR 0033/0061, tier 2) | compile fragments → '
            'SQL text | parse back through ScriptDom | tree equality (the '
            'parser) | **PARTIAL** — '
            '`src/run_layer.py::check_single_select` parses every executed '
            'statement through ScriptDom, so PARSEABILITY round-trips and a '
            'malformed compile fails closed. **Stated gap:** no κ-equality '
            'diff between the compiled tree and the source tree; the parser '
            'confirms the SQL is well-formed, not that it means the same '
            'thing | | **T3** | Definition creation (ADR 0038/0062, tier 1) '
            '| render proposal back for confirmation | user prose → '
            'proposed canonical tree | **the human** | **JUDGED, not '
            'tested** (§14d L3) — the confirm step (`spec:R3`) is the '
            "mechanism; correctness is the human's click. Recorded as "
            'judged so nobody mistakes a rendered proposal for a verified '
            "one |  **Why T2's gap matters and is not quietly closed.** "
            'Instance 1 earned its judge — a blind verifier plus κ-equality '
            "— because a fabricated description corrupts the human's pick "
            '(the E4 dependency). Instance 2 executes SQL against patient '
            'data; its current judge answers "does this parse?" and not "is '
            'this the tree the user confirmed?" `spec:R7` narrows the '
            'exposure to near zero by requiring the executed SQL be byte- '
            'for-byte the confirmed step — nothing is compiled at run time '
            'today — so the gap is latent, not live. It becomes live the '
            'moment fragment stitching ships, and T2 is the axiom that will '
            'then need its κ-diff.  And the tiers are the two directions of '
            'one correspondence:      Tier 1 (metadata):     Question '
            '--ρ--> anchors --enumerate/match/rank--> '
            'shapes --τ--> captions --human picks--> answer     Tier 2 '
            '(self-service): same prefix, then: '
            'picked shape --compile--> SQL --execute--> data '
            '--human approves--> stamped canonical  **Tier 2 = Tier 1 + '
            'exactly one arrow** (compile∘execute) — ADR 0046\'s "Pro adds '
            'exactly ONE layer" as a formula. Tier 1 moves '
            'structure→meaning; tier 2 moves meaning→structure→data; each '
            "direction's correctness is certified by running the opposite "
            'direction. Every human approval in either direction is an '
            'appended Event, which is how the flywheel (ADR 0023) is the '
            'same object as the verification machinery: **verification '
            'events ARE governance data.**  ---',
    },
    "T1": {
        "title": 'Descriptions',
        "law":
            'tau=translator; rho=blind verifier; judge=deterministic tree '
            'diff (κ-equality)',
        "parents": ['J4'],
        "parent_note":
            'descriptions - blind verifier + kappa-diff',
        "checks": ['tests/test_tree_contract.py'],
        "status": 'ENFORCED',
        "status_note":
            'ENFORCED — `tests/test_tree_contract.py`, all six clause gates '
            'green; this is `spec:F` stated as a member of the family',
    },
    "T2": {
        "title": 'SQL stitching',
        "law":
            'tau=compile fragments → SQL text; rho=parse back through '
            'ScriptDom; judge=tree equality (the parser)',
        "parents": ['J4', 'B1'],
        "parent_note":
            'SQL stitching - parseability round-trips; kappa-diff is the '
            'stated gap',
        "checks": ['tests/test_run_layer.py'],
        "checks_note":
            'parseability round-trips; the kappa-equality diff is the '
            'stated gap, live when stitching ships',
        "status": 'PARTIAL',
        "status_note":
            'PARTIAL — `src/run_layer.py::check_single_select` parses every '
            'executed statement through ScriptDom, so PARSEABILITY round- '
            'trips and a malformed compile fails closed. Stated gap: no '
            'κ-equality diff between the compiled tree and the source tree; '
            'the parser confirms the SQL is well-formed, not that it means '
            'the same thing',
    },
    "T3": {
        "title": 'Definition creation',
        "law":
            'tau=render proposal back for confirmation; rho=user prose → '
            'proposed canonical tree; judge=**the human**',
        "parents": ['M5', 'J2'],
        "parent_note":
            'definition creation - the human is the judge (L3 stratum)',
        "checks": [],
        "checks_note":
            'JUDGED, not tested — the human is the judge by construction '
            '(SPEC 14d, L3 stratum)',
        "status": 'JUDGED',
        "status_note":
            'JUDGED, not tested (§14d L3) — the confirm step (`spec:R3`) is '
            "the mechanism; correctness is the human's click. Recorded as "
            'judged so nobody mistakes a rendered proposal for a verified '
            'one',
    },
}
