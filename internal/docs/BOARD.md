# THE BOARD — living checklist (both sessions update ON EVERY STATE CHANGE)

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
      panel. DOM-harness gated. 1,311 green + ruff. AWAITS review
      → then SUNNY'S EYE is the acceptance (legibility).

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
