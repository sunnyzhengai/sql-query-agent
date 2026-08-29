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
Last touched: 2026-08-29, dev (PHASE2-SLICE-1 built + gated —
1.59.0; run layer typed-unbound awaiting Sunny's local `run:`
line; awaits review verification).

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
      sanctioned-draft set. AWAITS REVIEW VERIFICATION.
- [ ] Finder-coverage contract (timing = Sunny's call; drilldown
      benefit if pre-capture)
- [ ] 0056 decision layer + presentation reframe (POST-capture by
      ruling; incl. every-round decision UI, cluster-table
      retirement census outcome)

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
