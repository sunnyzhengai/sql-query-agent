# ADR 0063 — The product tiers: X-Ray, Bridge, Workbench, Run

**Status:** ACCEPTED 2026-08-30 — the tier lock, debated to
convergence; Sunny ratified with three rulings same-day: Tier 2
v1 = the RESOLUTION CONSOLE (not open chat); integration is
FILE-FIRST (she experiments with her Purview instance); the
Write-Back Queue is law. Only X-Ray pricing/length remains
parked. This ADR is also a SCOPE LOCK: every new idea is sorted
into a tier's v1 or the roadmap BEFORE it is built; what fits no
box waits.

## 0. The cross-cutting law: artifacts land, chat doesn't

Enterprises run on systems of record, not chat history. Every
tier's output lands as a durable, graded artifact in a system of
record (their DG catalog, Power BI, AIVIA's certified graph);
the chat is a query surface and stores nothing. (The company
discovered this law twice independently: the relay protocol's
"conversation-held decisions don't exist," and the product
architecture — that convergence is the evidence it is real.)
**The DG tool receives conclusions, not conversations.**

## 1. The wedge — the Estate X-Ray (land)

Fixed-price one-shot diagnostic, entirely in the customer tenant:
deploy the engine → harvest + parse the SQL/PBI estate → run the
0054 sweep + closeness machinery → deliver THE X-RAY REPORT:
their real counts (procs parsed, metrics discovered, red flags
with members and code-level basis) + the AI-readiness verdict
("this is why your Copilot hallucinates"). Engine removable or
dormant after. Cheap to accept (no integration, no end users, one
admin); the report's final page is Tier 1's order form.

## 2. Tier 1 — AIVIA Bridge (headless; the anchor and the entry ticket)

Admin-only. No end-user interface. Continuous harvest → parse →
graph → and the WRITE-BACK QUEUE into the customer's existing
governance estate:
- business + technical descriptions onto assets (Purview/Collibra)
  and Power BI report descriptions;
- PROPOSED business terms derived from parsed transformations;
- relationships: technical tables ↔ business terms ↔ PBI reports
  (Collibra relations; Purview term assignment + Atlas typed
  relationships);
- steward conflict alerts (drift, misnomers, grain fights) into
  their workflow;
- continuous monitoring: estate changes re-parse and re-propose.

**The Write-Back Queue (Sunny's Plan C — law of this tier):**
every proposed write enters a review set — TECHNICAL items
approved by a developer; BUSINESS items approved by a steward —
then lands, logged with approver + basis. Nothing machine-
authored enters an enterprise record unapproved; every landed
artifact carries its provenance grade ("parsed by AIVIA,
approved by <name>" / "steward-certified"). Confirm-before-
execute, applied to the last mile.

**Integration strategy (Sunny's Plan B = stage 1, not fallback):**
- Stage 1 — FILE-FIRST (RULED priority, 2026-08-30): approved
  review sets export as native import files (Collibra Data Intake
  Excel/CSV incl. relations; Purview glossary CSV); the admin
  uploads. Zero API risk; the file is a second HITL artifact.
  Sunny experiments with her Purview instance to validate the
  CSV surface firsthand.
- Stage 2 — DIRECT API: Collibra Import API; Purview Atlas REST
  (entities/relationships/lineage) + governance APIs (domains,
  terms, data products). Adapter targets the surface spanning
  classic catalog and Unified Catalog.
Positioning: "you aren't buying a new tool; you're buying the
engine that makes your expensive catalog true."

## 3. Tier 2 — AIVIA Workbench v1 = THE RESOLUTION CONSOLE (Sunny's ruling, 2026-08-30)

NOT open chat at launch. The workbench answers RED-FLAGGED
questions: every session starts from a machine-found flag with
its computed evidence (members, diffs, why-sentences, the graph
panel), and every action is a PREDEFINED BUTTON — the 0056 verbs
in uniform: **compare · certify · delegate to citizen steward ·
deny (with reason)**; developers additionally **approve technical
writes / fork**. Closed domain = zero open-world parse risk; the
dialogue-loop machinery (grounding, compare cards, diff lines,
graph panel) is the ENGINE underneath, rendering evidence and
executing buttons. Open interrogation ("ask anything") moves to
the ROADMAP as a re-openable surface — the engine stays tested by
the nightly battery + fuzzer regardless.
**THE INBOX (unification of #3 and Plan C):** the console and the
Write-Back Queue are ONE SURFACE — stewards see flags to resolve
+ business writes to approve; developers see technical writes to
approve. Every approval lands through the queue, graded, logged.
(§8.2 dissolves into this.)
LANDING TAXONOMY (what crosses to the DG tool):
- steward CERTIFY (0056 w5) → glossary/asset description update,
  grade steward-certified — through the Write-Back Queue;
- differentiation rulings → term updates/relations/deprecations;
- user confirms → usage weights + personal shelf ONLY;
- pinned deep-dives → certified note nodes in AIVIA's graph
  (v1 internal; DG gets at most a link);
- raw Q&A → nowhere, ever.

## 4. Tier 3 — AIVIA Run (later; gated)

Certified + parameterized execution (rungs 1–2, built), the
runnable shelf; rung-3 composition, personas, and the escalation
economy as the 0038/0058 path matures. GA on customer sources is
GATED on the output-side PHI gate and dedicated read-only
principals (recorded listing blockers).

## 5. Packaging + sequencing (RULED in debate)

- **Separable SKUs, bundled launch** (Sunny, 2026-08-30): Bridge
  is purchasable alone (the UI-averse enterprise exists); the
  launch offer and every demo lead with Bridge + Workbench
  together — the sync proves ROI, the chat proves magic, and the
  pairing defeats the middleware pricing ceiling.
- Launch motion: X-Ray → Bridge+Workbench bundle. Run when gates
  clear and pilots warrant.
- Naming/pricing final wording: parked to listing time (standing
  shelf item). The $25k/yr anchor (architect) noted, not ruled.

## 6. Positioning (the architect's four moats, recorded)

1. Catalog-first incumbents vs graph-native engine (architecture
   debt cuts both ways — ours is the light one).
2. Generic LLM summarization hallucinates; deterministic parsers
   + gate give code-level trust anchors (13–8 is the evidence).
3. Tenant-local: no data ever reaches AIVIA; PHI-safe by
   construction.
4. Closed loop: not descriptions-in-a-parking-lot but
   diagnose → interrogate → certify → write back.

## 7. Build delta (honest, so the lock is real)

Tier 2's ENGINE is built (grounding, compare, cards, graph
panel, gate); its v1 SURFACE — the Resolution Console/Inbox — is
new work: flag-driven sessions, the button verbs, the approval
flows (est. days-to-a-week; all buttons invoke existing ops).
Tier 3 built through rung 2 (gates recorded). X-Ray
= productizing the existing sweep (report generator + engagement
runbook). Tier 1 delta: term-proposal into DG object models,
relationship writing, steward alerts, the Write-Back Queue UI,
provenance-graded fields, file exporters (stage 1) then API push
(stage 2) — weeks of integration-depth work, no research risk.

## 8. Open at ratification

1. X-Ray price point + engagement length (Sunny, with sales
   motion).
2. RESOLVED by the Inbox unification (§3): the queue's surface IS
   the Resolution Console.
3. Deferred with file-first: API target order decided at stage 2
   (Atlas-first remains the recommendation).
