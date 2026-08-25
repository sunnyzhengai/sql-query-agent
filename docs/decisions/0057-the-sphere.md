# ADR 0057 — The Sphere: architecture model, ownership economy, contracts split

**Status:** ACCEPTED 2026-08-25 — the outcome of the Sunny +
review-session design debates (five rounds), ratified by Sunny in
session ("yes, crystallize"). Design record: this ADR changes the
BUILD QUEUE not at all; it binds future design.

**The full model lives in docs/architecture/SPHERE.md. This ADR
records the decisions:**

1. **Four shells:** foundation (sovereign EMR reality; built at BYOT
   ingestion incl. standard vocabularies; rung-3 prerequisite) →
   org artifacts (SQL + PBI reports; parsed truth; writes OBSERVED
   at ingestion diff, AIVIA is never the editor) → canonical
   (concepts as first-class nodes, born bottom-up, many-to-many
   claims; descriptions remain 1:1 org-node attributes; governed =
   claims consistent-or-dispositioned) → human shell (users as
   nodes; decisions and ownership as typed scoped edges; adds,
   never rewrites).
2. **The nervous system:** one rule — changed node → one hop →
   notify ownership edges with typed deltas; meaning-leads-code
   gaps open by assertion and close ONLY by parsing; inboxes
   usage-ranked.
3. **The ownership economy:** subscriber/accountable/authority
   unbundled; testimony edges are the subscription list;
   **stewards follow uses, never meanings** — stewardship =
   accountability for a consuming use; terms without single-truth
   uses need no steward; staffing by HARVEST (opt-in offer at the
   moment of demonstrated care) with appointed override; rung-3
   creator owns immediately; ownership lifecycle conservation
   (unowned+unused = retirement candidate; unowned+used = harvest
   queue).
4. **Typed deny** (amends ADR 0056): defect → developer; mismatch →
   fork offer; noncompliance → use-owner. Plus new decision
   `accept-stewardship` (the harvest response).
5. **Contracts split:** static system contracts stay
   code-authoritative, PROJECTED read-only into the graph with a
   projection==code conservation check; dynamic governance
   contracts (ownership/authority/subscriptions) are graph-native,
   read-enforced by code. Guard: rules about changing rules never
   leave code. Self-ingestion of AIVIA's own pipeline recorded as a
   direction.
6. **SPEC amendment authorized:** the round-trip translatability
   axiom (SQL↔meaning; meaning→data declared incomplete until Pro
   execution) joins Φ_AIVIA beside reachability; the
   answer-or-named-gap totality stated as conditional on the op
   algebra, failing loud at plan time beyond it.
7. **New flag classes recorded** (build later, with 0056/0038 work):
   reference-vocabulary violations; orphaned ownership; retirement
   candidates.

**Sequencing (unchanged by this ADR):** Sunny's scenario red-pen →
palette v2 → dashboard call → re-walk → capture. The 0056 decision
layer builds after capture; the sphere's new machinery (nervous
system, ownership economy, contracts projection) enters the queue
only by future work orders.
