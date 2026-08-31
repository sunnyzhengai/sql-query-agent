# The decision landing matrix — AIVIA · Purview · Collibra

**Status:** DRAFT 2026-08-31 — Sunny's directive after challenging
review's "ledger with no reader": every decision must land where
someone will actually consume it. Mechanizes ADR 0063's landing
map against real DG object models. Sunny ratifies; the Bridge
adapters build from this table.

**The governing rule (Sunny's ruling, this session):** ASSERTIONS
ABOUT THE ESTATE go to the customer's DG tool — that is where
humans review governance. AIVIA retains only (a) provenance/audit
of what it proposed and who approved it, and (b) machine signals
a catalog cannot use. *A record with no reader is exhaust, not
governance.*

Legend — **P** = Purview (Unified Catalog unless noted) · **C** =
Collibra · ✅ native · 🔧 customizable (custom attribute / custom
asset type / relation type) · ❌ not available → AIVIA holds it.

---

## A. Assertions — land in the DG tool

### A1 · certify one definition
*The steward affirms this metric's definition is correct and
official.*
- **P:** ✅ Glossary term (definition text) + ✅ term-to-asset
  assignment; steward/expert on the term; provenance + AIVIA
  basis via 🔧 custom attributes (Unified Catalog custom
  metadata, preview) — `aivia_provenance`, `aivia_basis_ref`,
  `aivia_certified_at`.
- **C:** ✅ Business Term asset + ✅ "governs / is governed by"
  relation to the technical asset; ✅ status = Certified/Approved;
  provenance via 🔧 custom attributes on the term.
- **AIVIA keeps:** the write record (what/when/approver) for
  audit; nothing else.

### A2 · designate official (among same-named variants)
*One member becomes the canonical bearer of the name; the others
are variants.*
- **P:** ✅ canonical Glossary term; ✅ Related terms
  (synonym/related) linking variants; variant status via 🔧
  custom attribute (`aivia_variant_of`, `aivia_status =
  variant | deprecated-candidate`). Purview's relation model is
  less configurable than Collibra's — attributes carry the
  semantics.
- **C:** ✅ Business Term (canonical) + ✅ configurable relation
  types (`is variant of`, `replaces`) between terms; ✅ workflow
  can drive deprecation.
- **AIVIA keeps:** audit only.

### A3 · differentiate all (governed plurality)
*The family is legitimately N distinct purposes; each earns its
own label. Output: N terms + a renaming work list.*
- **P:** ✅ N glossary terms (one per member, distinguishing
  description); ✅ related-terms links between siblings; the
  rename work list as 🔧 attribute (`aivia_action =
  needs-distinct-name`) — Purview has no native task queue for
  this, so the list ALSO stays in AIVIA's console until done.
- **C:** ✅ N Business Terms + ✅ sibling relations; ✅ **native
  workflow/task** can carry the rename assignment — Collibra
  fully absorbs it.
- **AIVIA keeps:** the open work list where the DG tool has no
  task surface (Purview today).

### A4 · deny with reason  *(Sunny: "exactly what we need to store")*
*A proposal is rejected, and WHY — institutional memory that
stops perpetual re-proposal.*
- **P:** ✅ the reason as 🔧 custom attribute on the term/asset
  (`aivia_denied_reason`, `aivia_denied_by`, `aivia_denied_at`);
  ❌ no native "rejected proposal" object → the attribute is the
  record. AIVIA must ALSO suppress re-proposal (see §C).
- **C:** ✅ comment/attribute on the asset + ✅ workflow rejection
  step with reason; ✅ status = Rejected.
- **AIVIA keeps:** the suppression rule (do not re-propose what
  was denied unless the underlying SQL changes) — a machine
  behavior no catalog performs.

### A5 · approve technical write (developer)
*A parsed description / lineage relation is accurate and may be
published.*
- **P:** ✅ asset & column descriptions; ✅ lineage (Atlas
  process entities / scanned sources); approver via 🔧 attribute.
- **C:** ✅ asset attributes + ✅ relations (data element ↔ term ↔
  report); ✅ responsibility (approver as steward role).
- **AIVIA keeps:** audit only.

### A6 · fork (developer authors a variant)
*A new definition derived from a certified one.*
- **P/C:** ✅ once the new SQL is parsed and ingested it becomes a
  normal asset/term with lineage to its parent.
- **AIVIA keeps:** the draft until it re-enters through the
  parser (0058 C4 — claimed must equal parsed); then it lands.

### A7 · reopen a ruling
- **P:** ✅ attribute/description update + ❌ limited native
  history → AIVIA's audit trail supplies the "who changed what
  when" narrative.
- **C:** ✅ native asset history + workflow re-open.

---

## B. Tasks & requests — DG tool if it has a task surface, else AIVIA

### B1 · delegate to citizen steward
- **P:** ❌ no native task/workflow assignment in Unified Catalog
  → **AIVIA holds the queue** and notifies (email/Teams).
- **C:** ✅ native workflow task — assign in Collibra; AIVIA
  mirrors status.
- Rule: *land the task where the customer's tool can carry it;
  AIVIA is the fallback queue, never the duplicate.*

### B2 · escalate ("none of these is right" → developer)
- **P/C:** ❌ neither is a demand-intake system → **AIVIA** (and
  optionally the customer's ticketing: Jira/ADO/ServiceNow via
  the same export/API pattern — future).

---

## C. Machine signals — AIVIA only (a catalog cannot use them)

| Signal | Why it stays |
|---|---|
| user **confirm** (workbench) | usage weight, not an assertion; feeds ranking + promotion thresholds |
| **run** (Tier 3) | execution telemetry; rung stamps; P5-safe counters |
| **prune / parse correction** | lexicon growth; meaningless to a catalog |
| flag **sweep state** | recomputed every build; the DG tool receives conclusions, not intermediate state |
| **denial suppression rule** | machine behavior derived from A4 |

---

## D. What AIVIA keeps in ALL cases (the audit spine)

For every landed artifact: what was proposed, its parsed basis
(proc + decision site), who approved it, when, which system it
was written to, and the response. This is provenance for the
catalog's own claims ("approved by Dr. Peterson" needs evidence)
and is required by 0058-C6's conservation audit. It is NOT a
second governance archive: **the console's decided items are
handoff receipts, and each links out to the catalog object that
now owns the fact.**

## E. Consequences for the console (resolves the open UI question)

Decided cards become **handoff receipts**: state chip + approver
+ *"written to <Purview/Collibra> → [open in catalog]"* (or
*"queued for export"* in file-first stage 1). They sink beneath
open work with a Resolved (N) filter. The steward reviews
governance IN THEIR CATALOG; the console shows only that the
handoff happened and where it went.

## F. Open at ratification

1. Purview custom-metadata attribute names + whether we require
   the (preview) Unified Catalog API or stay file-first for v1.
2. Collibra: confirm the operating model's relation types on
   Sunny's target estates (she owns this expertise).
3. Delegate in Purview estates: AIVIA queue + notification is the
   v1 answer — confirm acceptable.
4. Denial suppression: how long does a denial suppress
   re-proposal — until the SQL changes (recommended), or a fixed
   window?
