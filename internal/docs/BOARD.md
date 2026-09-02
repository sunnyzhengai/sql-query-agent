# THE BOARD — Sunny's personal checklist

**Single-session since 2026-09-02** (the dev↔review relay is retired;
restored as a PERSONAL checklist by Sunny's ruling the same day). The
law is unchanged: state changes land here the moment they happen —
conversation-held status doesn't exist. Sections below the current
view are preserved history.

## ⭐ CURRENT VIEW — 2026-09-02 (supersedes 08-31 below; that view's P0 completed, its P1/P2 queue stands)

### DONE since 08-31 (the docs-are-data week; all pushed to dev, ADRs 0064–0073)
- [x] Docs audit + three-tier hierarchy (axioms > blueprints >
      decisions), mechanized in trace_registry w/ closure checks
- [x] SPEC Groups L + T (crosswalk gaps closed; §13 promoted);
      Group P registration bug found + fixed
- [x] Blueprint staleness stamps (`current_through` — landing an
      ADR forces reconciling its blueprint)
- [x] Design-change protocol (docs/INDEX.md — the 6 steps before
      a line of code)
- [x] The prose ratchet, complete: SPHERE→ARCHITECTURE merge;
      SOURCE_CONNECTORS/QUESTION_MAP/USER_FLOW retired into
      registries; landing matrix + crosswalk + **SPEC v1.0 all
      GENERATED**. docs/architecture = 10 files (2 authored + 8
      generated); axiom statuses queryable (32E/13P/2G/1J)
- [x] internal/docs cleanup policy (durable evidence only; 8
      evidence files restored; this BOARD restored 09-02)

### BUILD QUEUE (unchanged from 08-31 ruling: validate → integrate)
- [ ] **P1 TERM-PROPOSE-1/2** — cluster → parent concept + child
      terms; proposal payload w/ prefix, zero custom attributes
      (now data-backed: landing_registry `organize_hierarchy` row)
- [ ] **P2** — Bridge stage-1 hardening → PURVIEW-SPIKE-1 (her
      tenant, hierarchy-by-REST is the risky call) → Collibra
      Import API → outbox implementation (schema now in
      landing_registry: OUTBOX_FIELDS/OUTCOMES)

### THE WEDGE / DESCRIPTIONS — 0074 RATIFIED 09-02; the build queue
- [x] **THE RED CONTRACT LANDED (09-02):** tests/test_desc_0074.py —
      every D-item's exit gate as a strict-xfail test (1 green:
      provenance vocab == spec:B2, cross-checked; 7 red by design).
      Flipping a marker IS the exit gate. Two facts the lock-down
      surfaced: describe_step (the skeleton path) is NOT yet wired
      into generate_descriptions (the loop still fails
      grounded_to_empty), and D5's red EMPIRICALLY CONFIRMS the
      derived-table leak on a live compose_skeleton call.
- [x] **ADR 0074 RATIFIED (all four calls as recommended).** Spec
      landed: B2 vocab = {gate_passed, skeleton_floor, flagged};
      F/T1 = the measurement instrument. Design debt from the field
      weeks is now record, not archaeology.
- [ ] **D1 — provenance persistence** (the B2 stated gap): provenance
      column on stored descriptions, closed-vocab invariant in
      TABLE_REGISTRY, written by 600. EXIT: contract invariant green
      + a red-first fixture per provenance value.
- [ ] **D2 — the verifier becomes the instrument**: corpus harness
      grading gate output (clean/recovered/emptied per class);
      fabrications=0 is the build-stopper, emptied=0 the floor.
      EXIT: scorecard emitted on the recorded corpus; thresholds
      pinned as the honesty-floor pattern.
- [ ] **D3 — metric/file-level composition**: metric <- terminal
      steps (CTE or temp alike); deliverable per SQL FILE; coverage
      = files described. EXIT: red-first skeletons flip green;
      corpus coverage measured in files. Empties per the
      (a) ruling: counted, absent, never loosened.
- [ ] **D4 — the wedge sample**: run_xray gains the description
      sample section with provenance chips. EXIT: XRAY_REPORT
      fixture shows the section; PRODUCT_TIERS/XRAY_ENGAGEMENT gain
      one line each.
- [x] **D5 SHIPPED 09-02 — and it became DESC-SKELETON-3 itself:**
      the AST-first composer (compose_skeleton consumes the faithful
      tree; scope-aware — DecisionSite gains scope, the walker bumps
      depth on QueryDerivedTable/ScalarSubquery). Regex composer
      DELETED; GATE-REGEX-1 mechanized (no re. in the composer,
      banned constants gone). All four 864af2f decoy corpses pinned
      + green (NOT EXISTS voiced, HAVING kept, OR shape-preserved,
      SELECT-CASE no phantom filter) + the 3a leak fixed BY NAME and
      BY VALUE (IN-subquery literals no longer hoovered into outer
      claims — found during the build). Exit marker flipped.
- [x] **EMPTIES RULED (a) — Sunny, 09-02:** absence over
      fabrication; the field stays absent; the voice ban STAYS
      (rules the word-"table" item too). Precedence now law:
      voice/gate kill > skeleton floor > absent; empties counted,
      never silent. D3 fully unblocked.

### ~~ORDERABLE~~ → GATE-RECUT SHIPPED (ordered + built 09-02)
- [x] **GATE-RECUT:** query_shape() in the tree (closed outcomes,
      parse_ok visible, scope-aware) now feeds parsed_grain /
      parsed_tables / parsed_columns / the deciding set; the 240-char
      windows and 4 SQL regexes DELETED. The checker-side 3a mirror
      is closed (claiming a derived table's filter now violates);
      a subquery GROUP BY no longer sets the outer grain. SQL-side
      regex debt: EMPTY. All 78 prior gate tests unchanged-green.
      En route: the frontier scanner's own blind spot fixed
      (module-level compiled patterns — planted and pinned).

### RULINGS OPEN FOR SUNNY (carried + new)
- [ ] Landing matrix v3 overall ratification (now generated from
      landing_registry; content unchanged, awaiting Bridge build)
- [ ] CONSOLE-6 item 2 — confirm handoff-receipts to unblock
- [ ] X-Ray price + engagement length (listing time)
- [ ] Film sequencing · capture day
- [ ] landing_registry OPEN_ITEMS: Collibra relation types ·
      canonical-child marking · outbox retention

### WORKING-TREE HYGIENE — ALL CLEARED (09-02, Sunny's "take care of it"; pushed fb8690d)
- [x] internal/docs mass deletion committed (99 files + 2 probes)
- [x] merge damage DISCARDED — the working-tree changes were
      deletions of the shipped DESC-MEANING-1 skeleton + its test
      file (the aborted merge's losing side); HEAD stands, suite
      regained 14 grounding tests (1481 passing)
- [x] dist/ wheels 1.58.4→1.83.0 committed (continues tracked series)
- [x] working tree fully clean for the first time since 08-31

### DEFERRED BY DESIGN (re-enter via the protocol, not prose)
- [ ] REFERENCE_ARCHITECTURE slim (at the listing push)
- [ ] MARKETPLACE_LISTING — TABLED 2026-09-01
- [ ] spec:T2 κ-diff — goes live when fragment stitching ships
- [ ] FCOTS/RLS personalization — roadmap (ADR 0071; verified unbuilt)

---

## 🗄️ HISTORY — 2026-08-31 view and older (preserved)


## CURRENT VIEW — 2026-08-31 (historical; P0 complete, P1/P2 carried forward above)

**Sunny's ordering ruling (2026-08-31): validate before we
integrate.** Rationale: Bridge's whole value claim is "accurate
descriptions your stewards never write." Plumbing them into a
customer's system of record before the content is proven would
deliver wrong text faster. Everything below is in dependency
order; nothing skips ahead.

### P0 — PROVE DESCRIPTION GENERATION (ORDERED 2026-08-31, re-cut: P0-a gate extension → P0-b live corpus → P0-c 790-proc run + Sunny's hand-graded sample)
- [x] **P0-a DESC-GATE-2 BUILT (08-31 dev, 1.80.0)** — the one
      gate gained TABLE claims (FROM/JOIN minus own CTEs; the
      violation names what the fragment does read) and GRAIN
      claims (DISTINCT/GROUP BY keys, else SELECT *_ID; unknown
      grain refuses nothing; both-keys evidences both). SQL-only,
      retry+fallback wiring untouched. Red-first proven per class
      (disable table → 2 red; disable grain → 1 red). 1,393 green
      + ruff. AWAITS review → P0-b.
- [ ] ~~DESC-GATE-1~~ — PREMISE CORRECTED BY DEV SURVEY (08-31,
      nothing built):** a grounding gate ALREADY EXISTS and is
      field-proven — src/descriptions.py `grounding_violations()`
      checks ungrounded VALUES + filter-CLAIMS against the SQL's
      deciding windows, dialect-aware, wired with a corrective
      retry + surgical fallback, 33 tests. The real gap is an
      EXTENSION: TABLE assertions and GRAIN are unchecked today.
      Recommend re-cutting this item as "extend the gate to table
      + grain claims, red-first fixture per class". Full survey in
      the handoff.
- [x] **P0-b DESC-CORPUS-1 BUILT + RUN (08-31 dev, 1.80.1)** —
      devtools/desc_corpus.py over 11 adversarial classes, live:
      **clean 6 · recovered 5 · salvaged 0 · emptied 0** (never
      fabricated past the retry). The 5 catches were one class:
      an accurate description + an INTERPRETIVE clinical tail the
      SQL cannot support — caught, retried away, pinned. The
      --dry mode found 2 gate defects before any LLM call (alias
      leaking into grain; encounter-shaped keys unseen) — both
      fixed + pinned; retry note now names all four classes.
- [x] **P0-c DESC-LIVE-1 RUN (08-31 dev, 1.81.0)** — option (a)
      as ruled: **26 CTE-step descriptions, 26 clean (100%), zero
      first-pass violations, zero fallbacks.** TWO LIMITS STATED
      IN THE REPORT: coverage (only 5 of 28 procs use CTEs; 23
      stage through temp tables — describing those is a separate
      UNBUILT capability) and scale (28 procs, difficulty real,
      never extrapolated). Three defects found and fixed en
      route: temp tables invisible to the gate (would false-
      violate on any Clarity estate), sibling CTEs read as base
      tables, and a first harvest that scored 23/23 while
      silently covering 3 of 28 procs (BEGIN…END bodies —
      recursive descent now). **SAMPLE READY FOR SUNNY:**
      internal/docs/DESC_LIVE_SAMPLE.md (description + fragment +
      parsed facts, hand-gradable).
- [x] **DESC-VOICE-1 BUILT (08-31 dev, 1.82.0)** — Sunny's
      grading: no fabrications, voice failures only. Three rules
      now mechanical in the one gate (tech-vocabulary ban, subject
      from parsed grain, grounded-or-absent acronym expansion);
      voice=False spares the machine-composed template floor. A
      row-number FALSE POSITIVE was caught by checking variance
      (2 clean / 2 violating across re-drafts) — it had emptied an
      honest description. **RE-RUN: 25 clean · 1 recovered · 0
      emptied, zero technical vocabulary in all 26 descriptions.**
      Sample regenerated for her grading.
- [x] **DESC-VOICE-2 BUILT (08-31 dev, 1.83.0)** — lead line =
      what this IS; concrete values (elided past ~6); purpose
      speculation banned at the gate (source-stated purpose may
      be quoted). **Two self-inflicted classes found live: my
      prompt's EXAMPLE became data** (its literals copied into
      unrelated steps — every concrete example removed from both
      prompts) and prompt PLACEHOLDERS echoed into descriptions
      (now its own gate class). **Re-run: 18 clean · 5 recovered
      · 3 emptied** — the empties are the gate working (invented
      organism names, verified absent from source). Bar moved
      from "true" to "true AND concrete AND purpose-free";
      reporting the honest number. Sample ready for read #3.
- [x] **DESC-TEMP-1 BUILT (08-31 dev)** — temp-table staged
      steps (`SELECT…INTO #X`, `INSERT INTO #X`) now harvest
      through ScriptDom: **26 steps/5 procs → 413 steps/15
      procs**. Three false-violation defects fixed: write targets
      counted as READS (a step read itself), a `--limit`ed run
      reporting itself as COVERAGE ("2 of 28" when the harvester
      reaches 15), and `--limit` taking a contiguous head (60
      steps from 2 procs). Coverage is now measured over the
      whole corpus, and the cap is stratified.
      **Stratified 60-step sample: 30 clean · 17 recovered · 2
      salvaged · 11 emptied.**
- [x] **DESC-VOICE-3 BUILT (08-31 dev)** — (1) MISATTRIBUTED
      PREDICATE: a sentence naming a predicate's operands must
      name its SUBJECT; caught on the real #BPA specimen and
      fired twice more on fresh text. Subject matching is by
      STEM because rule 2 bans the raw tokens. Probed 8/8 both
      directions, pinned. (2) NO COLUMN NAMES: developer-shaped
      tokens only — first draft flagged the ordinary word
      "result" and an existing test caught it. Fallback ruling
      built: `undocumented_columns()` + `readable_column()`.
      **Re-run: 15 clean · 23 recovered · 8 salvaged · 14
      emptied**; `column name` = 74 first-pass violations, the
      largest class. **Caveat REPORTED: 156/156 columns have no
      dictionary in this devtool run** — worst case by
      construction; the pipeline path supplies them.
      Sample ready for read #4.
- [x] **DESC-VOICE-3.2 FRAMING FIX (08-31 dev)** — tested my own
      claim that "the dictionary makes these better" and it was
      HALF WRONG. Live A/B: the dictionary fixes the TRUTH problem
      (misattribution 2→0) but NOT the voice one — the model
      copies the dictionary's KEYS. Cause is FRAMING: a glossary
      reads as vocabulary to cite, substitutions read as words to
      use instead. **10 column-name violations → 0 across 6
      steps.** Production `build_fact_prompt()` was using glossary
      framing; now substitutions. FACT_PROMPT_VERSION → 5, pinned.
      The 74 in read #4 was measured under the OLD framing with no
      dictionary — a worst-case floor, not the product.
- [x] **DESC-VOICE-3.2 RE-RUN + SELF-CAUGHT BLIND SPOT (08-31
      dev)** — re-run under substitution framing: **50 clean · 7
      recovered · 1 salvaged · 2 emptied** (was 15/23/8/14),
      column-name violations **74 → 0**. BUT reading the prose
      showed a description graded CLEAN containing three raw
      column names: `parsed_columns` matched only QUALIFIED
      references, so bare columns in SELECT…INTO staging were
      invisible. Fixed red-first (bare underscored identifiers,
      tables subtracted). **The 50-clean number is flattered by
      that blind spot and must not be quoted as-is.**
- [x] **DESC-MEANING-1 steps 3-5 BUILT (08-31 dev)** —
      `compose_skeleton()` (deterministic) + `describe_step()`
      (bounded smoothing, **skeleton ships if smoothing violates**,
      also on empty output and model exception). Live: 20 steps,
      **0 empty** — the empties ruling answered by construction.
      Three defects found by reading OUTPUT not counters: inline
      comments became values; the real filter was DROPPED
      (`#Base_Pop` composed to "line is 1" while its date range
      went unstated — a grounded decoy); join keys read as
      filters. WHERE-only was too blunt — **56 of 413 steps put a
      real filter inside a JOIN ON**. Correct rule: join key
      (col=col) vs literal filter (col=value).
- [ ] **DESC-SKELETON-3 (08-31, ORDERED — Sunny's "lift,
      re-cut")** — compose_skeleton reads the ScriptDom parse
      tree, not text; the five SQL regexes DELETED; NOT-EXISTS/
      HAVING/OR/SELECT-CASE become structurally impossible; eight
      probe cases land red-first. Ships with **GATE-REGEX-1**: a
      pinned test making SQL-structure regexes in src/ unwritable
      (Echo Law mechanism; must go red on the current composer
      first). DESC-SKELETON-2 retired; reverted patch = analysis
      only. **REVIEW FINDING (pre-build): the parse was never
      missing — it was DISCARDED.** descriptions.py imports no
      parser at all, while desc_live_run.harvest_steps already
      holds each step as a live ScriptDom node and passes down only
      text. So the re-cut is PLUMBING + a renderer, not a parsing
      project. Also verified: **ScriptDom cannot host on Sunny's
      Mac** — ~~RETRACTED, review was wrong (Sunny's question
      caught it)~~. Truth: the **VENV is on Apple CLT Python 3.9.6**
      (hardened); ScriptDom runs fine on Homebrew 3.11, verified
      live today (TSqlScript, 0 errors) with pythonnet + .NET 8 +
      the DLL all already installed. **ENV-SCRIPTDOM-1 ordered as a
      prerequisite**: rebuild .venv on Homebrew 3.11, report the
      test skip-count delta, no text fallback ever.
      **PROBES NOW EXECUTABLE:** `devtools/probe_skeleton_8.py`,
      baseline captured — **1-4 FAIL, 5-8 PASS** on the committed
      composer. Acceptance = 8/8 with 5-8 never regressing.
      **FIFTH FINDING (output read, not counters):** `@dStartDate`
      renders as "dstartdate" — a parameter shown to a steward as
      if it were a value; ordered into the re-cut (render by NODE
      TYPE: variable vs column vs literal). Dev building next.
- [ ] **DESC-FILE-1 (08-31, ordered)** — deliverable is a
      description per SQL FILE; steps are how, not what. Retires
      DESC-WHOLE-1. Coverage = files described / files present.
      Dev recon recorded in handoff (terminal statement must be
      found by parser, not text position; 7 of 28 files deliver
      via INSERT to a persistent table). Builds after
      DESC-SKELETON-3.
- [x] ~~the word "table" empties true descriptions~~ — RULED by
      the empties-(a) ruling (09-02, current view): ban stays,
      absence stands, counted.
- [ ] **PARKED FOR SUNNY — DESC-WHOLE-1: 13 of 28 procs get NO
      description.** They are single-SELECT report procs (no CTE,
      no temp staging — verified per file). 46% of the estate is
      silent. Whole-proc description is NEW capability, so it is
      not built here. Pinned `TestDescWhole1Gap`.
- [ ] ~~P0-c blocked~~ (resolved by the option-(a) ruling):
      the "790-proc corpus" is the WORK estate (Epic Clarity) —
      the separation wall forbids it here, and 790 was always a
      PARSE-RATE fact from the work deployment, never an
      AIVIA-side artifact. Dev did NOT substitute a corpus.
      Choose: (a) run on the 28-proc synthetic corpus + shapes
      estate (~100 descriptions, honest rates on our own data —
      dev recommends, unblocks P1); (b) Sunny runs at work and
      reports aggregate rates only (no text crosses); (c) defer
      to a design-partner tenant. Full note in the handoff.

### P1 — BUILD TERM PROPOSAL (Tier 1's actual product; unbuilt)
- [ ] **TERM-PROPOSE-1:** cluster → PARENT CONCEPT term + child
      terms with distinct names/definitions (hierarchy per the
      landing matrix A2+A3); naming rules deterministic where
      possible, gate-checked where generated.
- [ ] **TERM-PROPOSE-2:** proposal payload = assets +
      relationships (term↔proc, term↔report, steward) with the
      `AIVIA agent generated:` prefix; zero custom attributes.

### P2 — INTEGRATE (transport only, after P0+P1)
- [ ] Bridge stage 1 hardening (files) → stage 2 API
- [ ] **PURVIEW-SPIKE-1:** prove on Sunny's tenant, via API:
      parent term · child term · parent-child link · term
      assignment · description update. Hierarchy-by-REST is the
      known-risky call; CSV fallback if it fails.
- [ ] Collibra: Import API v2 port (assets + relations +
      responsibilities in one job) — straightforward per API docs
- [ ] Outbox implementation (logic_hash · target · last outcome)

### RATIFICATION / RULINGS OPEN FOR SUNNY
- [ ] Decision landing matrix v3 — overall ratification (zero
      schema footprint + outbox + hierarchy all recorded)
- [ ] CONSOLE-6 item 2 — resolved in principle as handoff
      receipts (matrix §3); confirm to unblock the build
- [ ] X-Ray price + engagement length (listing/sales time)
- [ ] Film sequencing · capture day

### PARKED (unblocked, not urgent)
- [ ] Run button's first click; probe-curation ruling ("leave" —
      recorded, no build)
- [ ] Purview secret rotation · shareable-connection click
- [ ] ADR 0058 sub-calls, tier naming, reviewer deck (listing-time)

### STANDING GUARDS (running)
- [x] Nightly cold battery ~6:23am (pause-aware) + fuzzer
- [x] Watcher on origin/dev both sessions

---

**Rule:** the moment a task changes state, the session that saw it
change updates this file (handoff-verdicts law applied to status).
Detail lives in the linked handoffs; this file stays short.

**THE AUTONOMOUS RELAY PROTOCOL (2026-08-27, Sunny's directive to
un-bottleneck herself):** both sessions run a background watcher on
origin/dev and WAKE when the other pushes — the repo is the channel,
the push is the doorbell. Bounds: (1) a session acts ONLY on the
other's commits, never its own, workspace commits are informational;
(2) auto-advance covers ONLY board-listed, already-ruled work —
anything new, any ruling, any tenant/UI click PARKS for Sunny, as
always; (3) every autonomous action lands in the handoffs + this
board exactly as if relayed; (4) if a session isn't running, the
loop falls back to Sunny's doorbell; (5) SHARED-TREE SAFETY: the sessions share one working tree —
inspect remote movement via fetch + origin refs; PULL ONLY WHEN THE
TREE IS CLEAN of the other session's work (a stash around the
other's in-flight edits is a collision hazard — near-miss 08-27);
(6) DELIVERED-NESS HAS ONE
TRUTH — the handoff RESULTS sections: hold only on what the files
show pending, never on remembered sequence (first-deadlock lesson,
08-27). Review session's watcher: LIVE
as of 2026-08-27. Dev session's watcher: LIVE as of 2026-08-27
(persistent 60s poll; re-armed at each dev session start — memory
recorded).
Last touched: 2026-08-29, dev (1.60.0: RW-17a/b/c built — cluster
compare expands members, right-cure errors, give-up label — AND
0060 sameness class LIVE with confirm-parse; the codeset beat now
rides the planner; awaits review verification + Sunny's re-ask).

## 🎯 THE CRITICAL PATH → demo capture

- [x] **Fused build** — DELIVERED 08-27 and **APPROVED by review
      the same day** (verdict in HANDOFF_0055_BUILD; suite 1,110
      green; B3 unblocked):
  - [x] payload 1 — palette v2 (08-26; 39/39 cells, gapcheck v2)
  - [x] payload 2 — graph-native clusters + 300 fold + consumer
        census (0059 live leg green; 83 clusters live; **1.58.1 env
        PUBLISHED by Sunny 08-27; gov_red_flags Eventhouse shortcut
        REMOVED by Sunny** — census consumer #4 retired)
  - [x] payload 3 — Diabetes Registry Dashboard (08-27 dev: git
        items on the sepsis pattern, U7 EXEC link + by-path visual,
        description EMPTY + test-held; report joins the shape graph
        via real TMDL parse; render check = Sunny's tenant step)
- [~] Sunny 08-27: dashboard params set ✓, credentials bound ✓ —
      tables await FIRST REFRESH, blocked on the shape seed
      (expected; don't refresh early). agent spot-check 08-27 FAILED honestly → triggered the DEMOTE
      ruling. Publish RETIRED (never happens); Sunny deletes the
      tenant agent later. Remaining Sunny: post-seed dashboard
      refresh → render → description-empty check; PLUS delete the
      Lakehouse `gov_red_flags` table in the UI (~10s — dev's API
      delete was permission-blocked; F-2's last physical step).
- [x] **F-order EXECUTED as re-cut (08-27 dev, release 1.58.2):**
      F-1 = PRODUCT export — six flat governance columns on
      graph_nodes (cluster: rows), contract + L0 + shapes green; no
      agent work, per the ruling. Docs re-cut: Step 6 retired →
      appendix recipe w/ disclaimer. F-2 repo-side clean (census
      zero refs); physical table = Sunny's UI step above. F-3
      cancelled. Columns materialize on the next 300 rerun (rides
      the shape-seed run; no urgency).
- [x] **Tenant load of the shape store — COMPLETE + VERIFIED 08-28** (26 clusters w/ flat columns = local oracle; semantic_search live; U7→dashboard pointer chase ready; full record in HANDOFF_0055_BUILD). RE-WALK UNBLOCKED.
- [x] THREE engine-surface shortcuts CREATED via UI (Sunny, 08-28
      — graph_nodes / graph_edges / output_metric_logic; 3-of-3,
      confirmed). **LOAD CLOSED (08-28): four-way verification GREEN — 26 flat-
      column clusters, search live, dashboard link on record.
      APPROVED by review (1,135 green).**
- [ ] **RE-WALK — UNBLOCKED, Sunny's session when ready** (section
      B grades against B3; section I against the 26 flags; demo-
      note questions in SHAPES_GAPCHECK) (incl. section B vs B3,
      section I flags; suite transcript may cover part)
- [ ] Script refresh (review session — workbench-only, candidate
      phrases, Fang's impact-analysis framing)
- [ ] CAPTURE

## 🔧 DEV QUEUE (behind the fused build, in order)

- [ ] Tenant nit: sepsis semantic model bound directly, not via
      DemoSqlServer/DemoSqlDatabase parameters (git-vs-tenant
      drift; align when convenient)

- [x] B3 step dep-chains — COMPLETE (step_deps 1.00; verified in worktree 08-27)
- [x] TEST_MAP.md generated + freshness CI (08-27 dev — 106 modules
      / 1,072 tests all accounted; docs/architecture/TEST_MAP.md)
- [x] Suite transcript artifact (08-27 dev — every answer_evals run
      writes internal/docs/SUITE_TRANSCRIPT.md)
- [x] Ops finds status REPORTED (08-27 dev): shortcut
      create-then-verify BUILT (devtools/create_kql_shortcut.py,
      create→poll query path→delete ghost + fail loud); org_config
      referential audit BUILT (devtools/org_config_audit.py, green
      --tenant in the 1.58.0 preflight); probe-eh rename NOT BUILT
      — parked for Sunny (her UI + recorded ref-edit list)
- [x] **PHASE2-SLICE-1 BUILT (08-29 dev, release 1.59.0)** — ADR
      0061 run layer slice 1: ScriptDom single-SELECT gate (typed
      refusals), TOP-200 cap-as-fact, /api/run + run button, P5
      cage GREEN (rows display-only, stamps-only to model + event;
      run not an engine tool), decision-event capture live,
      cohort-105 sqlite fixture (zero tenant dep). TYPED-UNBOUND
      until Sunny adds the local `run:` block (runbook line in
      HANDOFF_0055_BUILD). 1,182 green + ruff; 0061 exits the
      sanctioned-draft set. **VERIFIED by review 08-29** (P5 cage
      re-run, gate read in full; listing note recorded: customer
      sources need a dedicated read-only principal).
- [x] **RW-BATCH-4 + RW-16 BUILT (08-29 dev, release 1.59.1)** —
      RW-15 sameness-verdict duty (floor names compare(refs=[ids]);
      W12b hand-off; W6-echo safe) + turn-grain co-occurrence
      nudge + member-name collision qualify (W3a mechanism reused)
      + RW-16 run-failure cures (pip/brew+apt/az-login typed at
      bind AND execute). GATE CHANGE flagged: endpoint-hygiene
      re-scoped to git-reachable files (gitignored exempt BY
      MECHANISM; companion test earns it) after Sunny's sanctioned
      `run:` binding tripped the scan. 1,200 green + ruff.
      **VERIFIED by review 08-29** (design conformance approved).
- [x] **RW-17 + 0060 SAMENESS CLASS LIVE (08-29 dev, 1.60.0)** —
      17a cluster-id compare expands to members (the glass root
      cause dead); 17b id-kind mismatch names its own cure, infra
      text never misattributed; 17c give-up answers never file the
      answered verdict. Planner: sameness parses render a confirm
      card, click executes the deterministic plan (same DIFFERS
      line every run), engine fallback intact, opt-in wiring.
      1,211 green + ruff. **VERIFIED by review 08-29 — first
      production class served by parse-is-the-plan (0060), ordered→
      built→verified inside 24h of the ADR's acceptance.**
- [x] **Codeset beat PASS on glass (Sunny, 08-29)** — planner-
      served: parse card → click → DIFFERS, "+ E11.80" first line,
      full diff, evidence-verified. **LAST QA BLOCKER CLOSED.**
      Retrospective recorded in WALK_VERDICTS_SHAPES (five
      failures, five distinct causes, one generator — the 0060
      saga is the experiment's baseline).
      Remaining glass (Sunny): first bound Run → then the QA gate.
- [ ] Palette wording sweep (rides NEXT palette touch, per review
      08-29): descriptions must not imply structure the SQL lacks
      — USP_Active_Diabetics says "joined to an active-status
      flag" over a column filter; sweep "joined" where no JOIN
      exists (lands with the next 300 rerun + re-embed).
- [ ] Finder-coverage contract (timing = Sunny's call; drilldown
      benefit if pre-capture)
- [ ] 0056 decision layer + presentation reframe (POST-capture by
      ruling; incl. every-round decision UI, cluster-table
      retirement census outcome)
- [ ] Shelf standing-confirmation mechanics (0061 call 3 RULED
      08-29: shelf items stay runnable, the shelf IS the
      confirmation; change propagation invalidates an entry when
      its definition changes) — sequenced, no order yet; shelf v1
      replays the question (re-confirm via the card), which is
      correct until the saved-operation form lands

## 👩‍⚕️ SUNNY'S OPEN DECISIONS (no deadline pressure)

- [x] input_metric_names RESTORED (Sunny, 08-27 night) — the
      incident's damage ledger closes.
- [x] Env 1.58.3 PUBLISHED (Sunny, 08-28 morning) — realism-300
      precondition wheel live.
- [x] semantic_catalog_shapes shortcut CREATED via UI (Sunny,
      08-28 morning; accelerate off — the API ghosted 2/2, both
      caught by create-then-verify). **DEV: RESUME the chain
      --from 700_refresh_search_index → 800 → full verification.**

- [x] **Endpoint-leak residual: RULED — ACCEPT** (Sunny 08-27:
      auth-gated endpoint, no secret material; history rewrite risk
      exceeds gain; HEAD clean).
      STANDING RULE (amended 08-27, the echo): never COMMIT the
      parameter-bound model (re-leak) and never UNDO it (re-wipe) —
      LEAVE IT PENDING untouched until dev's connection-binding fix
      (ordered, pre-capture) ends the hazard permanently.
- [x] gov_red_flags Lakehouse table DELETED by Sunny 08-27 — F-2
      fully closed; the flags' only home is the graph.
- [x] Rename + sweep DONE (08-27): sql_catalog_eh / semantic_catalog
      live, zero probe refs — ops-find #3 CLOSED. (Sweep push shipped
      3 red tests from in-flight seed work — fix-forward flagged.)

- [ ] **RULING REQUESTED — the generator clause (Echo Law
      amendment, proposed in the 08-29 retrospective):** two
      failures on ONE beat with DISTINCT proximate causes → stop
      building at the failure's level; the missing mechanism is
      one level up, in what generates the variance. (Full text in
      WALK_VERDICTS_SHAPES.)
- [ ] **RW-24 item 2 (probe curation):** corpus probes
      (Line-Ending Probe A/B, Reference Forms Probe, …) in census
      display — badge as `control` w/ split count line (review
      recommends) / leave as-is / filter from default census.
- [ ] ADR 0058 self-service contracts: ratify + 2 sub-calls
      (parameter-range depth; quarantine release authority)
- [ ] Tier naming (listing-copy time; seeds recorded in
      PRODUCT_PICTURE)
- [ ] Reviewer deck (themes recorded; thinking)
- [ ] Finder-coverage timing (pre- vs post-capture)
- [ ] Purview/Collibra write-back tier placement (PRODUCT_PICTURE
      open item)
- [x] **Fabric agent: RULED — DEMOTED to integration recipe**
      (Sunny 08-27 evening; ruling + re-cut order in
      HANDOFF_0055_BUILD; tenant agent DELETED by Sunny 08-27 ✓;
      Graph Agent + eh_probe confirmed long gone)
- [ ] **Delivery architecture** (listing-time): workbench as
      container-in-customer-tenant w/ Entra SSO (near-term) vs
      native Fabric Workload (strategic — answers default-tool
      gravity with OUR surface); shapes the Marketplace offer type

## 🔍 REVIEW SESSION'S ITEMS

- [ ] Verify dev's fused-build report (gates + gapcheck v2 + demo
      note) when it lands
- [ ] Script refresh (blocked on re-walk)
- [ ] W10 refusal-posture design (standing, M4-hard)
- [ ] Relationship-claims-without-compare design (deferred by dev
      08-27 with recorded reason; the walk Q4 family; M4-hard)
- [ ] M2 decision-evidence design (standing; finder-coverage may be
      the lever)

## 📌 STANDING CLARIFICATIONS (so recurring questions stop recurring)

- **The Fabric agent is DEMOTED to an integration recipe (Sunny,
  08-27)** — supersedes the 08-22/23 "ship it" posture. We ship
  surfaces we can back; we don't maintain reasoning we can't. AIVIA
  builds/verifies/publishes NO Fabric agent; Step 6 becomes an
  optional grounding recipe over surfaces we do back.

## 🅿️ PARKED DIRECTIONS (recorded, unordered)

- Semantic cloud / domain clusters (deterministic only)
- Graph visualization (first step: shape-corpus render, 140 nodes)
- Predicate-grain decision clusters (use-pulled)
- Updater-as-product; FDE agent (post-demo strategy)
- Pilot cohort program (post-demo, pre-Marketplace)

## ✅ SHIPPED (recent milestones, newest first)

- [x] 0059 topology axioms ratified + live leg green (08-26/27)
- [x] Sphere + ADR 0057 (ownership economy, contracts split,
      presentation doctrine, clusters-are-nodes) (08-25/26)
- [x] ADR 0055 shape corpus, 26/26 cells + diabetic scenarios
      confirmed (08-24/25)
- [x] ADR 0054 governance sweep LIVE end-to-end; original corpse
      question answered by machine verdict (08-23/24)
- [x] Round 4 closed: 13/13 vs 8/13; claim set approved (08-22/23)
- [x] Walk 1562 + caption batch + W12/W13 fixes + engine smoke
      (08-23/24)
- [x] Echo Law (build-first) + demo law + slogan book (08-23→26)

- [x] WALL RESTORED (Sunny, 08-28): work-Collibra block + Purview
      secret removed from BOTH tenant org_configs (the 08-16
      demo-only sanction finally fully unwound).
- [ ] Purview secret ROTATION still recommended (exposed in
      screenshots twice; removal stops future exposure, rotation
      invalidates past) — Sunny, five Azure minutes, no deadline.
- Recorded direction: secrets-in-yaml is itself debt — Key Vault
  references are the enterprise end state (ties to delivery
  architecture; when Purview push is next needed, the rotated
  secret returns via the proper path).

- [x] Workbench store lever BUILT (08-28 dev): env >
      org_config.yaml search.kusto_db (Sunny's line now works
      workbench-side) > default; startup banner prints the active
      store + its source. Demo switch = one local config line.

## 📋 STRATEGY DIRECTIONS (Sunny's three questions, 2026-08-28 — recorded, sequenced post-capture)

- **Doc-trace layer:** physical layout stays type-based (append-only,
  ADR-numbered); vertical per-feature views are DERIVED — stable
  record IDs + typed links + a doc-registry with totality (0052
  pattern for documentation) + generated feature pages; end state =
  docs ingested as graph nodes ("show me everything about
  clusters"). Facts stay put; alignment is always derived.
- **Pro tier as goal-handoff:** the Round-4 pattern scaled — Sunny
  writes product goals; review decomposes to ADRs; involvement
  points contractual (ratifications, gap-checks, human-only clicks;
  new axioms/spend/pricing always park). Kickoff = 0058
  ratification + the goals page. Sequenced AFTER capture.
- **Shipped ops agent / adminless install:** honest form only —
  deterministic updater (boundary-echo skeleton) + ops agent that
  APIs everything possible, verifies everything, and degrades to
  guided one-click runbooks with expected observations at platform
  walls (Fabric UI-only gaps are real: publish buttons, shortcut
  ghosts 5/5). "Admin reduced to guided minutes," never
  "zero-human" — which is also the enterprise trust story.

## MORNING SUNNY (parked 2026-08-28 night → resume 08-29)
- [ ] Re-walk the TWO fixed beats when dev reports RW-BATCH-3
      green: flags (expect identity + member names + why-sentence
      on cards) and codesets (expect DIFFERS + E11.80 diff lines)
- [ ] Then the script QA gate (6 verbatim questions) → capture
      cleared
- [ ] Ratify ADR 0061 open calls: sample cap (rec 200) · charts in
      slice 1 (rec no) · re-confirm cadence (rec shelf-standing)
- [ ] Standing open: flywheel film sequencing · shareable-
      connection click · Purview secret rotation
- [ ] NEW (08-29): bind the run layer — one local org_config line
      (`run:` server/database → aivia_shapes_src; runbook in
      HANDOFF_0055_BUILD). Until then runs refuse typed (correct).
- [ ] (morning, optional, 2 min) Bind the run layer: add the
      `run:` block to org_config.yaml per dev's note in
      HANDOFF_0055_BUILD.md, restart, check banner "[run layer]
      bound read-only to aivia_shapes_src" — then click Run on any
      confirmed step: the first DATA on glass.

## ⛔ DEVELOPMENT HOLD — Sunny, 2026-08-29
ALL code changes are PAUSED effective now. Sunny is taking time to
understand the routing/planner issue in full; she and review will
plan together before any further execution. No new builds, no
patches, no refactors — including items already ordered
(RW-BATCH queues, planner class expansion, 0061 slices). Reading,
answering questions, and writing analysis docs remain fine.
The hold lifts only by Sunny's explicit word, recorded here.
— Dev session: HOLD ACKNOWLEDGED (08-29). No code moves; watcher
  stays armed for the planning conversation; available for
  questions and analysis docs on request.
— Dev session 08-29: the surfaced suite-red was remediated by
  review same-day (EOF removed, 0062 registered, TRACE_MAP
  regenerated) — dev re-verified 1,211 green.
— **ON LIFT (per 0062 ACCEPTED, call 2): dev's FIRST task is the
  iteration-card conversion** (parse card → show/propose/ask/
  execute, developer door visible every round). QA gate + capture
  follow the conversion.
- [x] **ITERATION-CARD CONVERSION BUILT (08-29 dev, 1.61.0,
      immediately on lift)** — SHOW grounded matches at parse time
      (per-entity, collisions whole), PROPOSE reading, ASK with
      prune checkboxes + engine fallback + THE DEVELOPER DOOR
      every round; /api/escalate captures demand as a 0056 deny
      event + mailto (org_config escalation.contact, optional);
      prune-to-empty refuses typed. 0062 exits sanctioned-draft.
      1,215 green + ruff. **VERIFIED by review 08-29 (invariant by
      invariant).**
- [x] **RW-BATCH-5 + REMOVE-THE-TYPE BUILT (08-29 dev, 1.62.0)** —
      type deleted (A1 test-held; no silent fallback anywhere;
      no-match card B9; engine only via the button C5); blank
      screen MEASURED (serial per-token store probes = the 30s)
      and KILLED (one labeled scan: MISS 30.5s→~5s) + skeleton/
      parallel/streamed card + confirm streaming + latency stamps;
      count_rows lexicon word (B10); **RUN LAYER LIVE (bind bug
      was dev's import — fixed, probe verified)**;
      walk_runner_0062 ready for review's E-battery. 1,230 green
      + ruff. **E-battery run by review 08-29: architecture PASS
      (B1≡QA3 determinism), finish work FAILED → RW-BATCH-6.**
- [x] **RW-BATCH-6 BUILT (08-29 dev, 1.63.0)** — transport killer
      dead (az subprocess ran PER QUERY + serialized concurrent
      threads on its cache lock; in-process token cache + session
      keep-alive → MISS 30.5s→1.9s, warm hit 0.67s, token 0ms);
      FEEDS + MAP composer cards (kind-None never an answer);
      "another way/other than"→variants; kind phrases become
      filters, never missed entities; B4 real table name +
      compose-driven no-match (table words plan lineage). 1,237
      green + ruff. **E-BATTERY RE-RUN REVIEW-GREEN 16/16 (08-29):
      cards 0.8-2.6s, executes 0.9-8s, B2 timeout→8s w/ DIFFERS,
      kind-None extinct. SUNNY CLEARED TO WALK** (her glass =
      clarity judgment + the untried RUN BUTTON). Demo prep note:
      warm the store with one throwaway question before capture
      (~14s idle-wake). Cosmetic nit noted: "red flags" rendered
      as an unmatched entity beside the flags relation.
      **Sunny's first walk found RW-BATCH-7 → walk paused.**
- [x] **RW-BATCH-7 BUILT (08-29 dev, 1.64.0)** — RW-19 no-match
      card crash fixed (dev's guard on the wrong listener; door
      now wires on EVERY card) + the page-JS gate gained a RUNTIME
      leg (node dom_harness renders every card variant; red-on-bug
      proven); RW-20 stem-tier generous grounding ("diabetes
      codeset" grounds; candidates always prunable); RW-21
      kind-only census restored ("what metrics are there" → census
      card). Battery extended B11-B15. 1,241 green + ruff.
      **Extended battery run by review: 20/21 healthy — sole
      blocker RW-22 (census composes no card).**
- [x] **RW-22 BUILT (08-29 dev, 1.64.1)** — census card (count
      line + rows, per the format contract); composer-gap law
      AMENDED to ANY successful op (wording bug dead, test-held);
      DOM harness census variant. 1,243 green + ruff.
      **EXTENDED BATTERY REVIEW-GREEN 21/21 (08-29 evening):
      Sunny's own walk-breakers pass, cards 0.7-2.2s warm, DIFFERS
      oracles ×3. SUNNY CLEARED TO WALK — restart, one warm-up
      question, then anywhere; the Run button awaits its first
      click. Then QA gate → CAPTURE.**
      Sunny's walk resumed and found RW-23 (chars-of-string).
- [x] **RW-23 BUILT (08-29 dev, 1.64.2)** — string source_tables
      split on commas, never iterated as chars (the tables answer
      renders full names, content-test-held); B16 verbatim in the
      battery; runner prints card CONTENT (assertion blindness
      closed). 1,245 green + ruff. **BATTERY 22/22 REVIEW-GREEN
      (08-29 night): B16 renders real table names on live content.**
- [x] **RW-24 item 1 BUILT (08-29 dev, 1.64.3)** — positional
      language dead in composed text (census overflow links the
      round ref; the gate found a SECOND live instance — the
      headline citation — on its first run); grep gate standing.
      1,246 green + ruff. Item 2 = SUNNY'S CALL below.
      **VERIFIED by review (gate caught #2 on first run).**
- [x] **RW-25 BUILT (08-29 dev, 1.65.0)** — idle-wake closed:
      grounding auto-retries once (skeleton says "store waking"),
      persistent failure = typed card WITH a retry button,
      invented-infra-cause duty in the honesty gate (causes from
      stamps, never the model), wake cure in the engine infra
      text. 1,252 green + ruff. AWAITS review verification → Sunny
      resumes → QA gate → CAPTURE.
- [x] **FUZZER-1 BUILT (08-29 dev)** — walk_fuzzer.py: N LLM
      phrasings per known intent; card-always + grounding +
      planted-oracle assertions; misses logged verbatim = lexicon
      food; standalone + nightly-battery stage. 1,256 green +
      ruff. Runs cold nightly with review's battery.
- [x] **TIER2-1 BUILT (08-29 dev, 1.66.0)** — semantic candidates
      nominate on the card (labeled, prunable, capped 3, zero
      extra queries); deterministic relevance bar (stem token in
      name/description — junk still misses honestly); prunes are
      captured [PRUNE] decisions. 1,258 green + ruff. **VERIFIED
      by review 08-29 (clean-worktree run).**
- [x] **FLYWHEEL-1 BUILT (08-29 dev, 1.67.0)** — src/flywheel.py
      (0056 v1): usage weights from the four decision classes;
      definition/map cards disclose provenance ("confirmed N× ·
      run M× — no official designated"); Ground-Truth Shelf v1
      (/api/mine + folding panel: definitions/reports/questions w/
      REPLAY). Promotion ladder stubs at single-user as ordered.
      1,268 green + ruff. **THE AUTHORIZED QUEUE IS FULLY
      DELIVERED AND VERIFIED (review 08-29, clean worktree).**
- [x] **FUZZ-FINDINGS-1 BUILT (08-29 dev, 1.67.1)** — standalone
      entries fixed; five missed phrasings consumed into the
      sameness surface forms; multi-relation plans dedup + 422s
      lead with the reading. 1,270 green + ruff. Nightly fuzzer
      re-judges until green.
- [x] **FUZZER-2 BUILT (08-29 night, queue-2 item 1)** — all 8
      intent classes fuzz w/ per-intent oracles; kind_any admits
      the data-driven card set. 1,272 green + ruff.
- [x] **FUZZ-FINDINGS-2 BUILT (08-29 night, 1.67.2)** — four
      misses consumed: whole-phrase sameness forms; flags census
      filters by the grounded CANONICAL name (mechanism), flags
      surface forms widened. 1,274 green + ruff.
- [x] **FUZZ-FINDINGS-3 BUILT (08-29 night, 1.68.0, GENERATOR
      CLAUSE EXECUTED)** — RELATION_LEXICON is data;
      detect_relations() a pure function owns the primitives (LLM
      = entity extraction + fallback only); prompt generates from
      the lexicon (one source); @prev fragility dead (explicit-id
      compare). Flip-flop class structurally impossible,
      determinism test-held. 1,279 green + ruff. **ACCEPTED by
      review (byte-identical double run — stability proven).**
- [x] **FUZZ-FINDINGS-4 + KEYVAULT-1 BUILT (08-30 dev, 1.69.0)**
      — relation-word entities dropped (the stable E11.80 misses'
      root); "different manner/way" = variants as ruled;
      secrets_vault.py: keyvault: refs resolve at config load,
      every failure names its cure, zero tenant action (Sunny's
      vault click completes later). 1,288 green + ruff.
- [x] **RW-26 BUILT (08-30 dev, 1.69.1)** — nominate means OFFER:
      nominations default-unchecked AND server-side default-
      excluded (include_ids opts in); the 5-way-compare dilution
      cannot recur. 1,290 green + ruff. **VERIFIED — fuzzer fully
      green twice (24 phrasings, zero findings both passes).**
- [x] **0060-EXPERIMENT-CLOSE DELIVERED (08-30 dev)** — full live
      measurement incl. Sunny's 15 walk phrasings EXECUTED through
      both systems: PROPOSED dominates every metric (2/2 vs 1/2 ·
      7/7 vs 5/7 · 0 vs 6 floors · fails closed vs guessed census
      · 15/15 composed vs 5 floors). ADR status records
      EXPERIMENT CLOSED w/ data. **OVERNIGHT QUEUE 2 FULLY
      DELIVERED + CLOSED by review (morning report posted).**
- [x] **RUNG2-1 + PROC-RUN-1 BUILT (08-30 dev, 1.70.0, queue 3)**
      — parameterized runs: token-equality-except-literal-sites
      (types only per C2); logic edits refuse as variant_fork w/
      the 0038 language; rung stamp (C1) on every result (label +
      payload + model stamps); single-SELECT procs run via
      offset-sliced bodies; multi-statement stays refused. 1,305
      green + ruff. **VERIFIED — QUEUE 3 COMPLETE ("run it, change
      a VALUE and run it, never change the LOGIC without it
      becoming yours"). Standing guards only until morning.**
- [x] **GRAPH-PANEL-1 BUILT (08-30 dev, 1.71.0)** — receipts-only
      subgraph per answer (machine-composed, deterministic,
      P4/P5-safe); layered SVG panel w/ kind colors, anchor
      emphasis, red conflict edges, dashed computed edges; click →
      /api/node card (read-guaranteed); run badges its rung on the
      panel. DOM-harness gated. 1,311 green + ruff. **VERIFIED;
      Sunny's eye-check on restart.**
- [x] **X-RAY-1 BUILT (08-30 dev, 1.72.0, tier queue #1)** — the
      wedge report (counts w/ disclosed absences, flags w/ code
      basis, deterministic AI-readiness verdict, order-form last
      page) + engagement runbook + CLI; LIVE SAMPLE on the shapes
      estate (37 metrics/65 steps/26 flags → NOT-AI-READY) at
      internal/docs/XRAY_REPORT.md. 1,316 green + ruff. **Gates
      green w/ ONE blocking find (XR-1: count-vs-list).**
- [x] **XR-1 BUILT (08-30 dev, 1.72.1)** — all members render
      (qualified labels); store shortfall discloses; KQL cap
      12→64; live regen: the 10-member family lists 10 w/
      qualified twins, 0 shortfalls estate-wide; membership
      semantics verified (26/26 reconcile). 1,318 green + ruff.
      **VERIFIED — X-Ray engagement-ready.** XR-2 wording polish
      (name-grain "named variants" counts) parked to next x-ray
      touch, non-blocking.
- [x] **BRIDGE-1 STAGE 1 BUILT (08-30 dev, 1.73.0)** — file-first
      exporters: Collibra assets+relations CSVs (parsed edges
      only, no invention) + Purview glossary CSV (Draft always);
      every row provenance-graded w/ named approver; LIVE EXPORT
      in internal/docs/bridge_exports (37 assets · 64 relations ·
      37 terms) — real files for Sunny's Purview experiments.
      1,324 green + ruff. **Gates green; BR-1 (dupe names,
      blocking) + BR-2 (stewards) found.**
- [x] **BR-1 + BR-2 BUILT (08-30 dev, 1.73.1)** — colliding names
      qualify + disclose (integrity gate: a dupe-Name file never
      leaves the house); stewards/experts pre-fill from the store;
      live regen: 37/37 unique, 6 families qualified, 16 stewarded
      rows. THE FILES FOR SUNNY'S PURVIEW EXPERIMENT ARE READY
      (internal/docs/bridge_exports). 1,327 green + ruff.
      **VERIFIED — Sunny cleared to experiment on the exports.**
- [x] **CONSOLE-1 BUILT (08-30 dev, 1.74.0)** — the Resolution
      Console/Inbox: LANDING_MAP as data w/ mechanized totality
      (unknown verb = "no action without a landing"); persona +
      reason gates; every press a graded 0056 event, folded back
      (latest wins, compare lands nowhere); /console page w/ verb
      buttons + live compare evidence via the existing algebra.
      1,344 green + ruff. **THE TIER-LOCKED QUEUE IS COMPLETE —
      VERIFIED by review at law grade (live smoke: /console serves
      the estate's 26 flags). ALL FOUR 0063 TIERS HAVE THEIR v1:
      X-Ray · Bridge stage 1 · Console · Run (rungs 1-2).**
      SUNNY'S GLASS: /console awaits her eye (the launch demo's
      heart) → film plan → capture day.
      **First eye-pass found CONSOLE-2 ("not clear HOW they
      differ").**
- [x] **CONSOLE-2 BUILT (08-30 dev, 1.74.1)** — compare leads w/
      member fingerprints (name·owner·reads·criterion·why),
      owner-named machine contrast, diff folded as labeled
      receipt; console act retrieves members; one composer, every
      surface. 1,348 green + ruff. **VERIFIED.**
- [x] **CONSOLE-2 AMENDMENT + CONSOLE-3 BUILT (08-30 dev,
      1.75.0)** — set-summary elision ("79 shared · E11.80 only in
      X"; lists stay folded); certify → the three-outcome chooser
      w/ member picker (landing map = 9 verbs, totality extended;
      picker verbs refuse memberless; members ride decisions,
      never fold keys). 1,353 green + ruff. **VERIFIED
      code-side.** Review's probe then found CONSOLE-2b (page
      ignored the composer).
- [x] **CONSOLE-2b BUILT (08-30 dev, 1.75.1)** — console page
      renders the full composer card (RED-FIRST DOM case: a
      payload-ignoring renderer cannot pass); criterion reads
      expression_sql + IN-lists sketch to counts (contrast now
      criterion-first: "IN (80 values)" vs "(81)"); set_summary
      live-verified + asserted on literal-set deltas. 1,356 green
      + ruff. **Probe found CONSOLE-2c (false counts + bare
      names).**
- [x] **CONSOLE-2c BUILT (08-30 dev, 1.76.0)** — false counts
      root-caused to the STORE's 500-char expression cap (raised
      to 4000; sketch DISCLOSES on truncated stores, never
      fabricates); bare-name class GENERATOR-KILLED (every member
      render through _member_display; collision gate holds all
      card fields). 1,358 green + ruff. SUNNY LINE: publish 1.76
      env + 300 rerun → true counts on glass. AWAITS review →
      Sunny's one restart.

## RULED (Sunny, 2026-08-29): THE GENERATOR CLAUSE — Echo Law amendment
"Fail twice, no matter the cause, triggers an investigation."
Stronger than review's draft: two failures on ONE beat — even with
different proximate causes — mandate a generator investigation
one level up before any further same-level patch. Effective
immediately; joins the Echo Law.

## ✅ HOLD LIFTED — Sunny's explicit word, 2026-08-29
Development resumes. Build order (per ACCEPTED 0062):
1. FIRST: convert the purple parse card → the ITERATION CARD
   (show / propose / ask; developer door on EVERY round via
   email/Teams; no-nag boundary per the certain-answers rule).
2. Review verifies; Sunny glass-checks the converted codeset beat.
3. QA gate (script V2, six questions) → CAPTURE CLEARED.
4. Then the ratified queue: lexicon growth under the loop, Run
   button first click, flywheel film, Phase 2 slices.
All work binds to 0062's invariants: no question types; LLM
proposes only; deterministic assembly; every decision captured.
- [x] Test automation: nightly COLD battery live (review cron,
      ~6:23am, 7-day auto-expire — re-arm on session recycle);
      paraphrase fuzzer ordered to dev (FUZZER-1)

## SUNNY'S SHELF (back from swimming — all unhurried)
- [ ] Probe-curation ruling: badge (rec) / leave / filter
- [ ] The Run button's first click — first data on glass
- [ ] Flywheel film sequencing (film two vs reopen)
- [ ] QA gate formality + pick a capture day
- [ ] Standing: shareable-connection click · Purview rotation ·
      0058 ratification · tier naming
Dev queue: RW-25 → FUZZER-1 → TIER2-1 → FLYWHEEL-1 (all
Sunny-authorized; review verifies each per the loop)

## ☀️ MORNING REPORT for Sunny (overnight 08-29→30)
Seven releases (1.67.1→1.70-line), every one review-verified:
- Fuzzer green ACROSS THE BOARD: 24 phrasings × 8 intents × double
  runs = ZERO findings. Its whole catch-list was consumed en route
  (lexicon surface forms, variants collision, nominate-means-offer).
- Generator clause fired once more and won: parse-layer flip-flops
  killed by making the relation pass a pure function of the
  question string (LLM keeps only entity extraction; confirm
  covers it).
- RW-26: semantic nominations now default-unchecked (offer ≠
  include) — traced live by review, fixed by dev, proven by
  double-run.
- KEYVAULT-1 code-side done (your optional tenant click completes
  it whenever).
- 0060 experiment CLOSED with data: the planner beats the old
  router on every metric, including an honest refusal where the
  old engine ran a census at a poem request.
- Nightly cold battery + fuzzer stand guard from 6:23am daily.
YOUR SHELF (unchanged): probe curation · Run button first click ·
film sequencing · capture day · optional tenant clicks.
- [x] Probe curation RULED (Sunny, 2026-08-29): LEAVE AS-IS — the
      controls stay in the census unbadged; their descriptions
      disclose. No build.

## 🌙 NIGHT CLOSE (2026-08-29 ~11:30pm, per Sunny's word)
- Fabric capacity `aiviafabric` (F4, rg-fabric-prod) SUSPENDED
  after dev finished (tree clean, all queues delivered+verified
  through 1.71.0 incl. the graph panel).
- The 6:23am cold battery cron is CANCELLED for the pause (it
  would false-alarm against a paused store). RESUME RITUAL
  (morning): Sunny resumes the capacity (portal or:
  az rest --method post --uri .../capacities/aiviafabric/resume)
  → tell review → review re-arms the nightly cron + runs a warm
  battery as the day's first check.
- Dev's standing note: local fixture tests need no tenant — code
  work is unaffected by the pause.
- [x] 2026-08-30 morning: capacity Active · warm battery 22/22
      green · fuzzer 24/0 · nightly cron re-armed (pause-aware).
      Estate handed to Sunny green.

## ⏸️ STRATEGY PAUSE (Sunny, 2026-08-30 morning)
Development paused for the TIER LOCK debate. No new dev orders
until tiers are ruled. Standing guards (nightly battery, fuzzer,
watcher) continue. Input: Sunny's architect conversation
(metadata pain validated; chat = value front-end, catalog sync =
enterprise entry ticket; moat = deterministic parse + tenant-local
+ closed loop).

## ▶️ PAUSE LIFTED — Sunny, 2026-08-30
Tier lock complete (0063 ACCEPTED, total landing map in). Dev
resumes on the TIER-LOCKED QUEUE, recommended order ratified by
the lift:
1. **X-RAY-1** — productize the sweep into the diagnostic report
   (their counts, flags w/ code basis, AI-readiness verdict) +
   engagement runbook. The wedge.
2. **BRIDGE-1 stage 1** — file exporters from approved review
   sets: Collibra Data Intake Excel/CSV (incl. relations) +
   Purview glossary CSV, every row provenance-graded. Also hands
   Sunny a real file for her Purview import experiments.
3. **CONSOLE-1** — the Inbox: flag-driven sessions, the button
   verbs (compare · certify · delegate · deny | approve-technical
   · fork), two-persona approval flows, all atop the existing
   engine; every landing per 0063's total map.
Scope lock in force: new ideas get a tier box before any build.
Review verifies each delivery per the standing loop.

## ⛔ DEVELOPMENT HOLD #2 — Sunny, 2026-08-30 evening
ALL code changes paused. CONSOLE-4 is SUSPENDED before build —
do not start (or stop if started; no partial lands). Sunny and
review are designing the steward-facing compare experience
together first. Standing guards (nightly battery, fuzzer,
watcher) continue. Lifts only by Sunny's word, recorded here.

**DEV ACK (08-31):** hold observed. DESC-SKELETON-2 had already
been BUILT when the hold landed; per its own instruction I
reverted — tree identical to 8ce6b4f, suite back to 1,442 green,
**nothing committed, no partial land**. Diff preserved outside the
repo (session scratchpad) so nothing is lost either way.
**Evidence for the open question, not a decision:** all four
defects were fixable and all eight probe cases passed — but none
was a pattern tweak. Each needed structure regexes cannot express
(balanced-paren subquery excision; aggregate-call left-hand sides;
top-level boolean nesting; SELECT-list vs FROM scope), so the fix
meant hand-building a partial parser in a codebase whose standing
law is that the native parser decides (ADR 0001). That matches
review's root-cause reading. Cost/risk of the AST re-cut is
Sunny's call.
**Also recorded (recon only, no code):** DESC-FILE-1 corpus map —
21 files end in a returning SELECT, 7 in an INSERT to a persistent
table; the terminal statement cannot be found by text position
(correlated subqueries sit later in the text); **11 of 12
single-statement files have NO conditions**, so a conditions-only
skeleton is the decoy class at file scale; 22 of 28 files carry an
author Description header, which needs strict same-line capture
(a lax regex fabricated one for USP_ED_SEPSIS).
- [x] HOLD #2 LIFTED (design ratified 2026-08-30 evening) — dev
      builds CONSOLE-4 v2 per the approved spec in the handoff
- [x] **CONSOLE-4 v2 BUILT (08-30 night, 1.77.0)** — the
      distinguishing set (one computation); grid card ≤3 w/
      difference-lead first, sames marked, 💡 pattern line,
      consequence notes; grouped roster >3 w/ pair drill-down;
      NO SQL in steward fields (test-held); snippets per member
      for developers; fragments display-retired (events keep
      them). 1,361 green + ruff. **PAIR GRID VERIFIED; roster
      needed CONSOLE-4c.**
- [x] **CONSOLE-4c BUILT (08-30 night, 1.77.1)** — method-read
      group headers ("By diagnosis codes"), equijoins filtered
      from the distinguishing set (structural, never criteria),
      aliases stripped, phrase caps, description-leads-on-degrade.
      1,365 green + ruff. **Roster probe found CONSOLE-4d (truth
      defects).**
- [x] **CONSOLE-4d BUILT (08-31 dev, 1.78.0)** — cross-attribution
      root-caused to DEAD CTEs: sites now come from OUTPUT-
      REACHABLE steps only (canonical→transform + dep closure),
      unreached disclosed; ALL members retrieve (cap 16); one
      label form per family; compound predicates phrase every
      clause (gestational twins now distinct); all-distinct never
      says "shared logic only"; spot-asserts vs real SQL. Live
      roster probe TRUTH-CLEAN. 1,373 green + ruff. **TRUTH
      VERIFIED by review; two cosmetics → CONSOLE-4e.**
- [x] **CONSOLE-4e BUILT (08-31 dev, 1.78.1)** — method-word
      headers (token-driven map, degrades on unseen estates;
      reference codesets demoted to lookups → 7 groups became 6)
      + roster lines end at the criterion (reads-tails trimmed).
      Live probe: six clean method groups. 1,376 green + ruff.
      **CONSOLE-4 COMPLETE — both cards probe clean; Sunny's
      double read is GO.**
- [x] **CONSOLE-5 BUILT (08-31 dev, 1.79.0)** — fold-back was
      never broken; the EVENT PATH was cwd-relative (a server
      started elsewhere read an empty store = the double-ruling
      hazard, traceless). Path now resolves to the repo root with
      a startup banner stating the fold count; decided cards sink
      visible w/ actor+date+target; REOPEN appends (never
      mutates), carries its reason, returns the flag to the open
      queue. 1,384 green + ruff. **VERIFIED — fold-back live (8
      dispositions, sunk-but-visible); Sunny's certifies were
      never lost.**
- [x] **SUNNY'S DOUBLE READ PASSED (08-31): "much clearer than
      earlier"** — both cards read clearly.
- [x] **CONSOLE-6 items 1+3 BUILT (08-31 dev, 1.79.1)** — one
      evidence block per flag (replace, never stack); click
      feedback (pressed + working…, restores on result or network
      failure). Harness defect found + killed while proving
      red-on-bug: async cases reported ok BEFORE their assertions
      ran (a green that could not fail) — now awaited; classList
      added. 1,384 green + ruff.
- [ ] **CONSOLE-6 item 2 — RESOLVED IN PRINCIPLE by the landing
      matrix §E (draft 08-31), awaiting Sunny's ratification of
      that doc:** decided cards become HANDOFF RECEIPTS — state
      chip + approver + "proposed to <catalog> · <last seen
      outcome> · [open in catalog]" (v2 §3 — the outcome comes
      from the OUTBOX row, not a sync), sunk beneath open work
      behind a Resolved (N) filter. Dev builds on ratification;
      nothing built yet.
- [ ] **Decision landing matrix — DRAFT v2 (08-31) — Sunny
      ratifies:** rebuilt on her three rulings — (1) HIERARCHY
      (parent CONCEPT + named children) replaces official/sibling;
      (2) approval happens in the CUSTOMER'S workflow (Purview UC
      publish workflow is native — corrects review's earlier
      claim; AIVIA hosts NO approval queue); (3) NO SYNC — the
      OUTBOX (logic-hash keyed, one row per proposal, no copy of
      their catalog). Four workflow rules: act only on parse-
      source change · never repeat a proposal · look before we
      write (one object, at write time) · never police their
      catalog between engagements (divergence = an X-RAY finding).
      Open calls (§5): aivia_* attribute names + v1 transport ·
      Collibra relation types · canonical-child marking · outbox
      retention (recommend keep — it IS the anti-repeat memory).
      **Bridge adapters + the console's receipt line build from
      this table once ratified.**

## ⛔ DEVELOPMENT HOLD #3 — Sunny, 2026-08-31
ALL code changes paused, effective immediately. DESC-SKELETON-2
is SUSPENDED before build — do not start; if started, stop and
revert (no partial lands), as with hold #2. Standing guards
(nightly battery, fuzzer, watcher) continue.
CONTEXT AT THE PAUSE: review's probe found four decoy-class
defects in compose_skeleton (NOT EXISTS silent · HAVING dropped ·
OR reads as AND · SELECT-CASE phantom filter) and traced them to
ONE root cause — the composer scans SQL with REGEXES instead of
reading the ScriptDom AST the rest of the system already uses
(ADR 0001's native-parser law). The open question at the moment
of pause: patch four patterns, or re-cut as AST-first
composition. Nothing decided, nothing built.
Lifts only by Sunny's word, recorded here.

## ✅ HOLD #3 LIFTED — Sunny's word, 2026-08-31: "lift, re-cut"
AST re-cut ruled; regex patch rejected (reverted diff = analysis
only, must not land). DESC-SKELETON-2 retired. Orders in the
handoff: **DESC-SKELETON-3** (compose_skeleton reads the ScriptDom
tree; the five regexes deleted, not bypassed; eight probe cases as
red-first fixtures) + **GATE-REGEX-1** (Echo Law mechanism: pinned
test banning SQL-structure regexes in src/, red-first against the
current composer). Then DESC-FILE-1, then sample #4 for Sunny.
