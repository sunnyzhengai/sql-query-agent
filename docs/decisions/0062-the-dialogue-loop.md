# ADR 0062 — The dialogue loop: show, propose, ask, execute

**Status:** DRAFT 2026-08-29 — the agreed outcome of Sunny's
pause-and-plan (her Plan B + review's synthesis + the literature's
validated pattern converged). Awaits Sunny's ratification; the
DEVELOPMENT HOLD stands until her word. Supersedes 0060's one-shot
confirm; keeps 0060's parse-never-generate core. ABOLISHES
question types outright.

## 1. Context — why this exists

Five failures of one question proved the router disease (the
generator clause was ruled from it). The 0060 prototype fixed one
"class" — and Sunny correctly caught that classes ARE types, and
types can never be enumerated ("we cannot predict all question
types" — her long-standing objection, now law). Her Plan B:
iterative human-in-the-loop — show what the graph found, propose
the understanding, confirm, execute; repeat. Research verdict
(2026-08-29, recorded below): no proven complete NL→graph system
exists; interaction IS the field's validated remedy.

## 2. The decision

**There are no question types.** A question is understood as:
generously extracted entity phrases + kind words + relation
words; entities matched against the full name+description
universe (exact tier, then vector-candidate tier); relation words
mapped through a small closed lexicon to EDGE SELECTORS and
derived computations (virtual edges); the answer's shape EMERGES
from the matched subgraph. Composition, never enumeration.

**The loop (per iteration):**
- **SHOW** — what the graph matched so far: stamped, deterministic
  (nodes, kinds, candidate edges; virtual edges computed where
  relation words demand).
- **PROPOSE** — the LLM's reading of the ask, in human terms.
  Proposing is the model's ONLY authorship; it never routes,
  never verdicts.
- **ASK** — concrete decision items: confirm the reading, prune a
  match, choose between readings, supply the missing word.
  **No dead ends:** every state — including failures, empties,
  ambiguities — renders as action items (the right-cure law
  generalized to every turn).
- **EXECUTE** — only what was confirmed, through the existing
  deterministic op algebra. Results stamped; any surviving prose
  gate-checked; assembly per the ANSWER FORMAT CONTRACT
  (deterministic tables/cards; LLM narration only when the user
  asks for explanation or as a single gate-checked gloss).
- Iterate as needed. The user may stop at any point with the map
  shown so far.
- **THE ESCALATION RUNG (Sunny's ruling, 2026-08-29): if the human
  says none of our understanding or options is right, we punt to a
  developer.** The exhausted loop is not a dead end either — it
  becomes a CAPTURED DEMAND handoff: the full conversation (every
  shown match, proposed reading, and human rejection) attaches to
  a 0056 deny/absence event and enters the developer queue. The
  developer arrives already knowing what the user wants and what
  the graph lacks; their NL→SQL authoring follows the Phase 3 ink
  boundary (human-verified, front-door re-parse). The loop's
  failure mode IS the supply-demand economy's intake.

**The no-nag boundary (certain-answers rule):** parts of the
question true under every reading execute after ONE confirm;
only genuine ambiguity spawns a clarify item. We iterate on
UNDERSTANDING, never on mechanical execution steps — one confirm
ratifies a reading; its ops run without further ceremony.

**Capture:** every confirm/prune/correction is a 0056 decision
event. Corrections grow the personal phrase map, promoting to the
estate lexicon by usage threshold + steward veto (0060 call 2,
unchanged). The loop makes the next question's first proposal
better — the flywheel's front door.

## 3. Borrowed, proven results (Sunny's directive: axioms with pedigree)

- **A1 Compositionality** (Frege; Montague's fragments): meaning
  of the whole = function of the parts + their combination →
  word-grain lexicon; composition covers unbounded questions.
- **A2 Small algebras cover huge spaces** (Liang's λ-DCS: ~6
  combinators sufficed for open-domain KGQA) → our op algebra
  (match, traverse, compare, census, negate, aggregate) is the
  right size; invest there.
- **A3 Completeness is provable ONLY at the formal layer** (graph
  query language semantics) → "complete and correct" is the op
  algebra's property to earn and test — never English's.
- **A4 Ambiguity is irreducible in NL** (fragment ceiling;
  2025 KGQA surveys: implicit relations, temporal/ordinal/
  aggregation constraints remain open) → do not chase full
  auto-disambiguation.
- **A5 Interaction closes the gap** (MISP / DialSQL /
  step-by-step correction / information-gain disambiguation
  2019–2025: HITL clarification measurably improves accuracy AND
  user confidence) → the loop is the remedy, not a crutch.
- **A6 Certain answers** (database theory): under ambiguity,
  answer only what every reading supports — otherwise ask.

## 4. What changes in the built system (when the hold lifts)

- The purple parse card generalizes to the ITERATION CARD
  (show + propose + ask). The one-shot sameness "class" is
  re-founded: "same" becomes a lexicon edge-selector entry; its
  machinery (grounding, whole-collision anchoring, compare
  execution, machine diff card) is the seed, unchanged.
- The engine's free-routing path shrinks as the lexicon grows;
  fallback remains the engine + duties (defense in depth) until
  retirement is evidence-justified.
- Guards/duties/gate: unchanged. They protect whatever executes.

## 5. Open calls (Sunny, at ratification)

1. Iteration cap before the escalation rung is OFFERED proactively
   (the rung itself is RULED — "none of these is right" always
   punts to a developer; the open call is only whether we also
   offer it unprompted after N loops, and what N is)?
2. Does the iteration card replace the parse card for the
   already-shipped sameness path immediately, or at the next
   natural build?
3. Ratify §3 as the standing axiom register (cited in future
   drift debates like spec:IDs)?
EOF
