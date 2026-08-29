# The complete product picture (Sunny + review session, 2026-08-25)

Two pillars, two tiers, one flywheel. Sunny's synthesis, formalized.

## The 2×2

| | Supply side | Demand side |
|---|---|---|
| **GOVERNANCE (Basic)** | parse → graph → red-flag sweep (structural candidates) — NEARLY DONE | the decision algebra (ADR 0056, ACCEPTED): choose / confirm / deny / certify / fork(0038) feeding asserted edges back into the graph |
| **SELF-SERVICE (Pro)** | execute a SQL query (passthrough identity; P5: rows never enter the model) | the three-rung ladder (below) |

Tier line (Sunny's ruling): **Basic governs the definitions; Pro
runs them.** Basic = full governance flywheel (capture AND
application). Pro = data execution — the rubber-meets-the-road
moment; data settles logic debates fastest; self-service is the
holy grail.

## The self-service ladder — rungs are PROVENANCE GRADES

1. **Run as-is** — certified logic verbatim. Zero generation.
   Provenance: certified, untouched.
2. **Parameterize + run** — user supplies VALUES (dates, thresholds,
   locations), never logic; typed substitution into certified SQL
   (injection-safe by construction; certification stays valid).
   LOGIC edits are not rung 2 — they are FORK (0038-gated).
   Provenance: certified logic, user parameters.
3. **Compose from scratch** — assembly from the certified step
   library (the parse layer's 413 verified sub-queries) + data
   dictionary, graph-traversed; free generation only for glue;
   always displayed, always plan-confirmed, always marked
   UNCERTIFIED DRAFT. Provenance: composed draft, pending
   governance. (Amends 0056's "never LLM-generated SQL" →
   "never SILENTLY generated": disclosure, not prohibition.)

Every answer carries its rung on screen. Competitors live at rung 3
with no rungs 1–2 and no disclosure; AIVIA arrives at rung 3 LAST,
composing from certified fragments, with provenance.

## The cross-pillar flywheel

Rung-3 output = a NEW uncertified definition entering the
governance pillar → accumulates testimony (chosen/confirmed/run) →
surfaces to a steward with evidence → certified into the supply
side → strengthens rungs 1–2 for everyone. Self-service demand
manufactures governance supply; governance supply makes
self-service trustworthy. One flywheel across the tier boundary =
the upgrade motive in both directions.

## Positioning sentence (candidate; Marketplace wording is Sunny's)

"Everyone else does text-to-SQL first and governance never. AIVIA
does governance first and text-to-SQL last — and by the time it
writes SQL for you, it is assembling from logic your own stewards
certified." (Round 4 is the recorded evidence for the inversion.)

## Build state vs the picture

- Governance supply: SHIPPED (0053 resolver, 0054 sweep, shape
  corpus proving it).
- Governance demand: ADR 0056 accepted; build sequenced AFTER the
  demo capture.
- Self-service supply (execution engine): design constraints
  recorded in 0056 (plan-confirm, passthrough, P5); not built.
- Self-service demand (the ladder): rung boundaries + provenance
  grades recorded here; rung 3's composition design is future work
  (an ADR of its own when reached — the step library as assembly
  units).

## Open (Sunny)

- Marketplace naming for the two tiers under this picture (existing
  filed names: "Metadata Agent and Data Analytics Agent" — map or
  rename).
- Where the Purview/Collibra write-back now sits (previous Basic
  definition) — candidate: Basic integration add-on or Pro; not yet
  ruled.

## The Ground-Truth Shelf (Sunny's direction, 2026-08-28 evening)

Old SaaS = assured interfaces (autopilot muscle memory). Chat
agents = ephemeral. AIVIA in between → give users a PERSISTENT
SHELF: the sidebar renders their own captured decisions (0056) so
their ground truth visibly accumulates in AIVIA.

Three sections, all views over the 0056 decision store (no new
data model):
1. **My definitions** — confirmed/certified metrics; click →
   instant definition card, no re-ask.
2. **My reports** — PBI links confirmed/clicked from answers,
   ordered by the user's own usage (capture the click, own the
   habit that today lives in browser bookmarks).
3. **My questions** — a saved question is a SAVED OPERATION:
   deterministic ops replay with fresh data, same shape, machine
   stamps. Familiar guarantees, not just familiar pixels — chat
   products structurally cannot offer this.

Principle: **the conversation is the instrument; the shelf is the
ledger.** Retention via accrued ground truth, not lock-in. Shelf =
stage one of citizen stewardship (0038): personal certified items
that many users converge on are promotion candidates — the same
usage-threshold + steward-veto ladder as the 0060 lexicon.

Caveat: personal shelf needs user identity → multi-user version
rides the access-control gate (0038). Single-user shelf suffices
for FILM TWO: empty shelf → walk → shelf accrued on camera; the
flywheel visible without narration.
Sequencing: film one unchanged (governance beats). Shelf + 0056
capture verbs = ONE build = film two's content.

## The Three-Phase Roadmap (Sunny, 2026-08-28 evening — mapped to ratified ADRs)

**Phase 1 — the logic layer (NEARLY SATISFIED):** graph connects
technical/transformational/canonical (0059-verified), descriptions
at every node (RW-6), search embedded over the described surface.
Remaining to satisfaction: the 0060 experiment (routing
consistency) + format-contract glass check. Calibration: vectors
NOMINATE, the confirm step decides (0060 §2a).

**Phase 2 — self-service data (= THE PRO TIER: "Basic governs the
definitions; Pro runs them"):** definition card → user confirms
the logic → execute confirmed SQL → glass shows table/chart.
`run` is already 0056's weight-8 verb — the strongest flywheel
signal. Mock sources exist (aivia_shapes_src). LAWS: P5 absolute —
rows render to glass, NEVER model context (model sees stamps
only: count/schema/as-of) — say this out loud as a
differentiator; honest sampling label machine-composed (TOP N ·
as-of · source). New engineering: read-only execution role, row
caps/timeouts, PHI gate in front, proc-wrapping (steps are
runnable fragments; procs need wrapping/params). Plumbing, not
research.

**Phase 3 — multi-persona (users/developers/stewards):** personas
= the Sphere's human shell; escalation = 0058's ladder's top rung;
"no matching logic" = a CAPTURED DEMAND artifact (0056
deny/absence + conversation attached) feeding the developer queue
— the supply/demand economy live. The user→developer handoff
mirrors our own review↔dev relay (conversation as handoff
artifact). **INK BOUNDARY: AIVIA drafting SQL for a developer is
authoring-time generation — legal ONLY because (a) a human
developer verifies/owns it and (b) the result enters through the
front door (ScriptDom parse → graph → sweep). Answer-time
generation to end users stays banned** (the Fabric-agent
demotion's reasoning, applied consistently).

Sequencing unchanged near-term: film one (governance) → 0060
experiment → shelf + 0056 (film two) → phase 2 build (Pro) →
phase 3 (rides 0038/0058 access-control gates).
