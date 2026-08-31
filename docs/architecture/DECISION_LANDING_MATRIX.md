# The decision landing matrix — AIVIA · Purview · Collibra

**Status:** DRAFT v2 2026-08-31 — rebuilt on Sunny's three
rulings: (1) HIERARCHY replaces official/sibling, parent is a
CONCEPT node, never a promoted child; (2) approval happens in the
customer's DG workflow — Purview's Unified Catalog publish
workflow (author → steward → expert → owner → published) is
native, correcting review's earlier claim; (3) NO SYNC — the
OUTBOX model. Sunny ratifies; the Bridge adapters build from this.

## 0. The four workflow rules (crystal, no ambiguity)

1. **We act only when a PARSE SOURCE changes** — SQL, TMDL, or the
   dictionary. No change, no proposal, no noise.
2. **We never repeat a proposal we have already made** — the
   OUTBOX (§1) is keyed by logic-hash, not by name.
3. **We look before we write** — at write time we read the ONE
   object we are about to touch (never the catalog at large).
4. **We do not police their catalog between engagements** —
   divergence between catalog text and parsed truth is an X-RAY
   finding (a diagnostic engagement), not a live subsystem.

## 1. The OUTBOX (replaces "sync"; AIVIA-local, small)

One row per thing we ever proposed:
`logic_hash · proposal_kind · target_system · target_object_id ·
proposed_at · last_seen_outcome (published | denied | edited |
missing) · outcome_seen_at`.
- Prevents repeat proposals (rule 2) and records where the fact
  now lives (the handoff receipt the console renders).
- It is NOT a copy of their catalog: no term text, no
  relationships, no status stream — only what WE asserted and
  what we last observed at write time.
- Outcome refreshes only when rule 3 fires (we're touching that
  object anyway) or during an X-Ray.

## 2. The asset & relationship matrix

Every AIVIA action, mapped to the assets it creates/updates and
the relationships it draws, in both tools.
Legend: ✅ native · 🔧 customizable (custom attribute / relation
type) · ❌ absent → AIVIA holds it.

### A1 · certify one definition
| | Purview (Unified Catalog) | Collibra |
|---|---|---|
| assets | ✅ Glossary term (name + definition) · ✅ data asset (proc/view) | ✅ Business Term · ✅ Data Asset (proc/view) |
| relationships | ✅ term → data asset (term assignment) · ✅ term → steward/expert (contacts) · ✅ term → report asset | ✅ term *governs* asset · ✅ term *responsible* steward (responsibility) · ✅ term → report relation |
| status | ✅ Draft → Published via publish workflow | ✅ Candidate → Certified (configurable statuses) |
| attributes | 🔧 custom metadata: `aivia_basis_ref` (proc + decision site), `aivia_parse_hash`, `aivia_proposed_at` | 🔧 custom attributes, same three |
| AIVIA keeps | outbox row only | outbox row only |

### A2+A3 · organize into hierarchy  *(supersedes "designate official" and "differentiate all")*
*The steward's real act on a name family: create the PARENT
CONCEPT, give each variant its own distinct name + definition,
attach as children. Optionally mark one child canonical.*
| | Purview | Collibra |
|---|---|---|
| assets | ✅ parent glossary term (concept, no proc behind it) · ✅ N child terms (one per variant) | ✅ parent Business Term · ✅ N child Business Terms |
| relationships | ✅ parent-child term hierarchy · ✅ each child → its proc (term assignment) · ✅ child → report/steward | ✅ hierarchical relation (parent/child) · ✅ child *governs* its proc · ✅ steward responsibility per child |
| canonical child (optional) | 🔧 `aivia_canonical = true` on the child (Purview has no native "the official one") | 🔧 attribute, or ✅ a configured relation type (`is preferred term`) |
| rename work | ❌ no native task → **AIVIA console work list** | ✅ native workflow task assignment |
| AIVIA keeps | outbox rows + open rename list where the tool has no task surface | outbox rows |

### A4 · deny with reason
| | Purview | Collibra |
|---|---|---|
| assets | ✅ the term (stays, not published) | ✅ the term |
| status | ✅ workflow rejection (term not published); 🔧 `aivia_denied = true` for explicit denied-state (Purview's status set is not user-configurable) | ✅ status = Rejected/Denied (configurable) |
| attributes | 🔧 `aivia_denied_reason`, `aivia_denied_by`, `aivia_denied_at` | 🔧 same, or ✅ native comment + workflow reason |
| AIVIA keeps | outbox row with `last_seen_outcome = denied` — **rule 2 then prevents re-proposal for that logic-hash** (no "memory" beyond this) | same |

### A5 · approve technical write  *(NOTE: approval happens in THEIR workflow)*
*Flow: Bridge parses → proposes Draft term/description →
**their** publish workflow routes author → steward → expert →
owner → published. AIVIA does not host an approval queue.*
| | Purview | Collibra |
|---|---|---|
| assets | ✅ data asset description · ✅ column descriptions · ✅ glossary term (Draft) | ✅ asset attributes · ✅ Business Term (Candidate) |
| relationships | ✅ lineage (process entities / scanned sources) · ✅ term → asset | ✅ *is derived from* / lineage relations · ✅ term *governs* asset |
| approvers | ✅ workflow roles (steward/expert/owner) | ✅ workflow roles + responsibilities |
| AIVIA keeps | outbox row (proposed → published/denied as last seen) | same |

### A6 · fork (developer authors a variant)  *(UNBUILT — no authoring surface today)*
| | Purview | Collibra |
|---|---|---|
| assets | ✅ the new proc becomes an asset once parsed; ✅ its term Draft | ✅ same |
| relationships | ✅ lineage child → parent proc; ✅ term hierarchy under the concept parent | ✅ same |
| AIVIA keeps | the draft ONLY until it re-enters through the parser (0058-C4: claimed = parsed) | same |

### A7 · reopen a ruling
*Under the outbox model this is simply a NEW proposal cycle: the
underlying SQL changed (rule 1) or a human reopens in their tool.*
| | Purview | Collibra |
|---|---|---|
| assets/relations | ✅ the term returns to Draft via workflow | ✅ status back to Candidate; ✅ native history |
| AIVIA keeps | outbox row updated at next write-time read (rule 3) | same |

### B · tasks & requests
| action | Purview | Collibra | AIVIA |
|---|---|---|---|
| delegate to citizen steward | ✅ workflow assignment (publish workflow roles) | ✅ native workflow task | queue only where the tool lacks one |
| escalate ("none of these is right") | ❌ not a demand system | ❌ | **AIVIA** (+ optional ticketing export later) |

### C · machine signals — AIVIA only
user confirm (usage weight) · run telemetry + rung stamps · parse
corrections / lexicon growth · sweep state · outbox itself.
A catalog cannot consume these; they never leave.

## 3. Console consequence

Decided cards are **handoff receipts**: state chip + approver +
"proposed to <Purview|Collibra> · <last seen outcome> · [open in
catalog]". They sink beneath open work with a Resolved (N)
filter. Governance is reviewed IN THE CATALOG; the console proves
the handoff and points there.

## 4. Divergence (catalog text vs parsed truth)

Not a live subsystem. It is an **X-Ray finding**: at engagement
time we read the objects in our outbox and report "N terms whose
catalog text no longer matches the code that computes them." A
paid diagnostic, consistent with rule 4.

## 5. Open at ratification

1. Purview custom-metadata attribute names (the `aivia_*` set)
   and v1 transport: file-first (ruled) vs the Unified Catalog
   API (preview) for stage 2.
2. Collibra operating-model relation types on Sunny's target
   estates (her expertise).
3. Canonical-child marking: attribute (both tools) vs a
   configured Collibra relation type — cosmetic, decide at build.
4. Outbox retention: keep forever (recommended — it is small and
   it is the anti-repeat memory) vs prune with the estate.
