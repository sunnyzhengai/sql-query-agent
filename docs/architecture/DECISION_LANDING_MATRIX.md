<!-- GENERATED FILE — do not edit.
     Source: LANDING_REGISTRY in src/landing_registry.py
     Regenerate: python scripts/generate_docs.py
     CI fails if stale (tests/test_landing_registry.py). -->

<!-- TIER: BLUEPRINT — component key: landing
     src/trace_registry.py ARCHITECTURE_COMPONENTS -->

# The decision landing matrix — SQL Intelligence Agent · Purview · Collibra

Converted to data by ADR 0068 (the ADR 0067 ratchet): the
registry is the truth, this file is its projection. Content
carries the source document's status — Sunny's four rulings
of 2026-08-31 are RULED; the matrix as a whole awaits
Bridge-build ratification. Rationale: the ADRs, never here.

Support legend: `[native]` ships in the tool · `[config]`
needs configuration · `[absent]` no surface — SQL Intelligence Agent holds
it.

## The four workflow rules

- **R1.** We act only when a PARSE SOURCE changes — SQL, TMDL, or the dictionary. No change, no proposal, no noise.
- **R2.** We never repeat a proposal we have already made — the OUTBOX is keyed by logic-hash, not by name.
- **R3.** We look before we write — at write time we read the ONE object we are about to touch, never the catalog at large.
- **R4.** We do not police their catalog between engagements — divergence is an X-Ray finding, not a live subsystem.

## Zero schema footprint (ruled 2026-08-31)

- **Source is a relationship, never a field** — the term-to-asset link (Collibra `governs` / Purview term assignment) IS the statement 'this definition comes from that procedure' — no source field, no code fragment, no frozen line pointer.
- **Attribution is a prefix in the description text**: `{product} agent generated: ` (rendered with the deployment's product name) — machine-authored descriptions begin with the prefix; a steward rewriting the text and dropping it is itself the signal of human authorship.
- **Logic identity stays home** — the parse hash (normalized fingerprint of a logical unit) lives only in the OUTBOX — we are the party proposing, so we are the party that must remember.
- **Accepted limit:** with no marker in their catalog, a lost outbox means our artifacts are recognisable only by the prefix text — so the outbox is a BACKED-UP asset and the prefix is the fallback.

## The OUTBOX (replaces "sync")

One row per thing we ever proposed: `logic_hash` · `proposal_kind` · `target_system` · `target_object_id` · `proposed_at` · `last_seen_outcome` · `outcome_seen_at`

Outcomes: published | denied | edited | missing.

NOT a copy of their catalog: no term text, no relationships, no status stream — only what WE asserted and what we last observed at write time; outcomes refresh only when rule R3 fires or during an X-Ray.

## The landing matrix

### certify one definition

- **Grade:** steward-certified, approver named
- **Purview:** assets: [native] glossary term (name + definition); [native] data asset (proc/view) · relations: [native] term -> data asset (term assignment); [native] term -> steward/expert (contacts); [native] term -> report asset · status: [native] Draft -> Published via publish workflow
- **Collibra:** assets: [native] Business Term; [native] Data Asset (proc/view) · relations: [native] term `governs` asset; [native] term `responsible` steward; [native] term -> report relation · status: [native] Candidate -> Certified (configurable statuses)
- **SQL Intelligence Agent keeps:** outbox row only

### organize a name family into hierarchy

- **Grade:** steward-certified per child
- **Purview:** assets: [native] parent glossary term (concept, no proc behind it); [native] N child terms (one per variant) · relations: [native] parent-child term hierarchy; [native] each child -> its proc; [native] child -> report/steward · status: [native] hierarchy + description wording — no native 'official one', no custom field added · rename_work: [absent] no native task -> console work list
- **Collibra:** assets: [native] parent Business Term; [native] N child Business Terms · relations: [native] hierarchical relation; [native] child `governs` its proc; [native] steward responsibility per child · status: [config] `is preferred term` relation where the estate has one · rename_work: [native] workflow task assignment
- **SQL Intelligence Agent keeps:** outbox rows + open rename list where the tool has no task surface

### deny with reason

- **Grade:** asserted (testimony; disposition recorded)
- **Purview:** assets: [native] the term (stays, not published) · status: [native] workflow rejection — the rejection IS the record; no field added · reason: [native] workflow rejection comment
- **Collibra:** assets: [native] the term · status: [native] Rejected/Denied (configurable) · reason: [native] comment / workflow reason
- **SQL Intelligence Agent keeps:** outbox row outcome=denied — rule R2 then prevents re-proposal for that logic-hash

### approve technical write

- **Grade:** parsed-by-SQL Intelligence Agent, approved-by developer
- **Purview:** assets: [native] data asset description; [native] column descriptions; [native] glossary term (Draft) · relations: [native] lineage (process entities); [native] term -> asset · status: [native] workflow roles (steward/expert/owner) approve
- **Collibra:** assets: [native] asset attributes; [native] Business Term (Candidate) · relations: [native] `is derived from` / lineage; [native] term `governs` asset · status: [native] workflow roles + responsibilities
- **SQL Intelligence Agent keeps:** outbox row (proposed -> published/denied as last seen)

### fork (developer authors a variant) *(UNBUILT — no authoring surface today)*

- **Grade:** asserted, owner = creator
- **Purview:** assets: [native] the new proc becomes an asset once parsed; [native] its term Draft · relations: [native] lineage child -> parent proc; [native] term hierarchy under the concept parent · status: [native] as certify, once parsed
- **Collibra:** assets: [native] same · relations: [native] same · status: [native] same
- **SQL Intelligence Agent keeps:** the draft ONLY until it re-enters through the parser (0058-C4: claimed = parsed)

### reopen a ruling

- **Grade:** new cycle — inherits the fresh proposal's grade
- **Purview:** status: [native] term returns to Draft via workflow
- **Collibra:** status: [native] back to Candidate; native history
- **SQL Intelligence Agent keeps:** outbox row updated at next write-time read (R3)

### delegate to citizen steward

- **Grade:** delegate's answer returns as testimony; the STEWARD lands the conclusion
- **Purview:** status: [native] workflow assignment (publish workflow roles)
- **Collibra:** status: [native] workflow task
- **SQL Intelligence Agent keeps:** queue only where the tool lacks one

### escalate — none of these is right

- **Grade:** demand artifact; the conversation attaches
- **Lands:** SQL Intelligence Agent only — neither catalog has a surface for this
- **SQL Intelligence Agent keeps:** the demand queue (+ optional ticketing export later)

### machine signals (never leave)

- **Grade:** machine weights (0056 w3/w8); rung stamps
- **Lands:** SQL Intelligence Agent only — neither catalog has a surface for this
- **SQL Intelligence Agent keeps:** user confirms (usage weight) - run telemetry + rung stamps - parse corrections / lexicon growth - sweep state - the outbox itself. A catalog cannot consume these.

## Consequences

- **Console:** decided cards are HANDOFF RECEIPTS: state chip + approver + 'proposed to <tool> - <last seen outcome> - [open in catalog]'; they sink beneath open work with a Resolved (N) filter — governance is reviewed IN THE CATALOG; the console proves the handoff.
- **Divergence:** catalog text vs parsed truth is NOT a live subsystem: it is an X-Ray finding — at engagement time we read the objects in our outbox and report the mismatch count. A paid diagnostic (rule R4)..

## Open at ratification

- **attribute names** (closed): CLOSED 2026-08-31 by zero schema footprint — no names to decide; v1 transport file-first (ruled), Unified Catalog API evaluated at stage 2
- **collibra relation types** (open): operating-model relation types on the target estates (Sunny's expertise)
- **canonical-child marking** (open): attribute vs configured Collibra relation type — cosmetic, decide at build
- **outbox retention** (open): keep forever (recommended: small, and it is the anti-repeat memory) vs prune with the estate
