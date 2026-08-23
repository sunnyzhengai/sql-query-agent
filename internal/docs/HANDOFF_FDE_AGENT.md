# Handoff — the FDE agent: error-controller typing now, the consult surface after Round 4

**From:** Sunny via review session, 2026-08-21. **To:** dev session.
**Vision (Sunny):** ship a per-customer consult/debug/FDE agent that
diagnoses errors the way the review session does — typing each error
against the framework, then routing it to whoever has authority to fix
it. It productizes the review rhythm itself; its grounding corpus is
the ADR corpus, SPEC.md, the contracts, and AI_VIA_AXIOMS.md.

## Verdicts (Sunny, 2026-08-21)

1. **Tier-2 transport is OPT-IN, admin-triggered, never automatic.**
   BYOT's promise stands: nothing leaves the tenant except an explicit
   support-bundle export (whitelist-anonymized signature + contract id
   + versions — the ADR 0041 anonymization mechanics). Whitepaper
   gains the sentence.
2. **The agent NEVER patches without permission — and tier 2 is a
   FLEET flow.** A proposed fix routes through the existing
   discipline: fixture in the home repo first, fix as src/ code with
   tests, shipped in the next wheel (field-patch law, ADR 0042 clause
   6 — the agent never bypasses it, and a helpful agent under
   customer pressure is exactly the expedience threat that law
   exists for). NEW requirement from Sunny: every vendor-typed error
   is EVALUATED FOR GENERALITY — does it apply to other customers? If
   yes, the fix syncs to the home product and pushes to all customers
   via the release channel, not just the reporter. One customer's
   error becomes everyone's fix.
3. **Sequencing:** the error-controller registry and typing land NOW
   (cheap, improves every gate message immediately). The
   conversational FDE surface waits behind Round 4 + the Marketplace
   listing — it is a Pro-tier-shaped flagship feature and launches
   named, not half-built.

## The controller taxonomy (Group R refinement)

    controller : ErrorClass → {customer, vendor, platform}   (total)

    route(customer)  = tier 1: guided remediation — the agent walks
                       the runbook/checklist steps WITH the admin
    route(vendor)    = tier 2: opt-in diagnosis artifact → AIVIA's
                       fixture-first pipeline → generality evaluation
                       → fleet push via next wheel
    route(platform)  = tier 3: human discussion + documented
                       workaround + a RE-TEST TRIGGER (the Fabric
                       three-walls pattern: what the platform vendor
                       must change before we re-probe)

This is the third instance of the framework's typing move: decisions
typed by decider (M5), judgments by epistemics (J2), errors by
CONTROLLER. Candidate amendment for AI_VIA_AXIOMS v0.2 (R3
refinement: "which human depends on controller") — add it to the
framework only after the registry's first live use, per
claim-after-measurement.

## §3b answers (the design's registry rows, as the clause requires)

1. **Inventory:** ERROR_CONTROLLER registry — every reason_code,
   contract id, and signature class carries
   `controller + remediation ref + route`. Frontier = the enumerated
   reason codes today; an error class without a row is unclassified.
2. **Conservation:** every error event is `typed ⊎ unclassified`;
   unclassified ESCALATES (H2 — an error nobody typed is precisely
   where neither code nor model has authority). Tier assignment
   itself obeys the escalation contract.
3. **Drift:** a reason_code without a controller row fails CI. And
   the taxonomy self-corrects by data: a customer-typed error
   recurring across customers is mechanically challenged — repeat
   frequency flips the candidate type to vendor (the error-contract
   product-signal channel, now with teeth).

## What exists vs. what's new

Exists (built for other reasons — reuse, don't rebuild): admin graph
+ diagnosis-as-a-path + step explainer (1.37.0, ADR 0048); contract
ids on every gate failure (0039); fallout terminal states + human
checklist (0045); the shape-census intake loop (0041) — tier 2
generalizes it from M-shapes to all error classes; the one-mind turn
engine (the FDE agent is the SAME engine pointed at the admin graph —
one-engine doctrine, never a second brain); whitelist anonymization;
engine-floor version checks (env-mismatch detection is already
mechanical).

New: the ERROR_CONTROLLER registry + CI closure; controller +route
fields surfacing in gate messages and the checklist; the opt-in
support-bundle export surface; the generality-evaluation step in the
home-repo triage (a checklist item on every inbound bundle: one-off
or fleet?); later, the conversational FDE surface itself.

## Phasing

- **Phase 1 (now):** ERROR_CONTROLLER registry, typing of all existing
  reason codes, CI closure check, controller shown in gate messages
  and checklist rows. Design review cites the §3b answers above.
- **Phase 2 (after Round 4 + listing):** the FDE conversational
  surface (one-mind engine over admin graph + runbooks + framework
  docs), the support-bundle export, the fleet-triage checklist.
  Pro-tier positioning; launch named.

## PARKED (for Sunny)

- FDE agent's product name and tier placement/pricing.
- The support-bundle consent UX wording (whitepaper + listing claims).
- AI_VIA_AXIOMS v0.2 amendment (controller typing) — after phase 1's
  first live use.
