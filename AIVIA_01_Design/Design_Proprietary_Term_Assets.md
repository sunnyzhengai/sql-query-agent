Design_Proprietary_Term_Assets
Status: RATIFIED (Sunny, 2026-09-30).

THE LAW
AIVIA's term assets — the vocabularies that map how people speak to
what systems store — are AIVIA's proprietary product knowledge. They
are seeded into every deployment to give customers a head start, they
grow with every customer engagement, and that growth compounds into
AIVIA's healthcare-industry moat. Customer-specific names, counts and
data NEVER travel.

THE ASSETS (today)
1. The business terms list (the prior build's meaning ladder): business
   vocabulary bound to technical objects.
2. The technical terms list (AIVIA_01_Data/03_chat_bot/
   03_chat_technical_terms.md): the dictionary graph's own vocabulary —
   node kinds, edge kinds, operations, their synonyms. The file is its
   own ruling registry; adding a row is the ruling, dated.
3. The name-abstract list (03_chat_abstract_names.json): LLM-drafted,
   Sunny-gap-checked abstracts and synonyms per table and column, plus
   the sunny_* override fields — the hand-confirmed vocabulary that
   survives every regeneration.
4. The T-SQL construct rulings (02_tsql_construct_master.json): which
   grammar constructs AIVIA maps vs counts, with reasons.
Future lists join this law by being named here.

THE PORTABILITY SPLIT (the precedent: the construct-master clause,
02 contract)
- TRAVELS with AIVIA: list structures; keyword rows and synonyms;
  rulings and their reasons; abstracts and synonyms of VENDOR-STANDARD
  objects (an Epic table means the same thing at every Epic shop);
  hand-confirmed vocabulary of vendor-standard objects.
- NEVER TRAVELS: customer-written names and descriptions; anything
  derived from customer-local text; usage counts and example
  fragments; customer value lists (bed labels, department names).
- The test at the boundary: "would this row be true at a different
  customer running the same vendor system?" Yes = AIVIA's. No = the
  customer's, stays behind.

WHY THIS IS THE MOAT
Every deployment starts warmer than the last: the seeded vocabulary
answers on day one what took the previous customer weeks of gap-check.
Every gap-check at every customer surfaces vendor-standard phrasings
("inpatient admission" -> PAT_ENC_HSP) that join the master lists.
Competitors can copy features; they cannot copy an accumulated,
hand-confirmed healthcare vocabulary without walking the same years.

DEPLOYMENT MECHANICS (the shape, details per phase)
- The deployment package carries the master lists; the per-customer
  build merges them with customer-generated rows, provenance kept
  (master vs local) so the split stays mechanical at contract renewal
  or offboarding.
- Harvest direction: a customer engagement proposes additions to the
  master lists; Sunny's eye admits them; admission is a dated ruling.

THE AGENT POSTURE (ruled by Sunny 2026-10-01, from the M06 evidence):
NEVER FOUNDATION, ALWAYS BENCHMARK, EVENTUALLY CUSTOMER.
- Never foundation: AIVIA develops on its own engine. A governance-
  first product requires provenance (every answer names its mechanism
  and cites stored rows), determinism (same question, same answer),
  and honest absence. The Fabric Data Agent architecturally has none
  of these — M06 recorded a semantics misread and a FALSE ABSENCE,
  the worst behavior a governance tool can exhibit — and its string-
  based retrieval ceiling (the three exhibits: census-days,
  payor/payer, the DISCH_DISP underscore) is the gap the product
  exists to fill. The standing direction law holds: the Agent is a
  subject, never a validator.
- Always benchmark: the M06 scorecard protocol reruns at each major
  Fabric release — same questions, briefing recorded verbatim, ours
  as ground truth. The moat is measured against the Agent's best,
  never its past.
- Eventually customer: M06 Round B proved an AIVIA briefing took the
  Agent from structural failure (0/2) to 5 clean passes. The agent
  briefing is an AIVIA EXPORT ARTIFACT in the making: the curated
  truth layer (dictionary tables, terms, abstracts) grounding
  whatever agents the enterprise runs — truth layers, never
  gatekeeping. Portability per this document's law: the briefing's
  structure travels as AIVIA's; customer content stays behind.
- M07 boundary: Fabric-ecosystem packaging decisions are made on
  marketplace grounds with ZERO architectural dependency on the
  Agent, either way.
