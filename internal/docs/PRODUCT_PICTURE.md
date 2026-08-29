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
