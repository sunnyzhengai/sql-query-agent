# ADR 0079 — The interpreter and the speaking graph: never-regex, match-then-connect, the graph's own vocabulary as the only language

**Status:** ACCEPTED 2026-09-06 — designed in live brainstorm with
Sunny after four console finds traced to one generator; every open
point blessed explicitly. **Component:** architecture. **Supersedes**
ADR 0078's ask path (the op list + keyword grammar); the console
surface, H5 usage events, honest outcomes, and Kind_Vocabulary
survive.

## The generator this kills

Four live asks failed in one evening — unpickable ambiguity, "what
metrics are there," the vocabulary audit, "what reports are about
sepsis" — and all four were ONE failure: question understanding was
an enumerated pattern list (regex grammar, then a five-verb algebra
proposal — smaller, same species). Enumeration over natural language
is never total; every unenumerated phrasing arrives as a corpse.
This is the same law that killed the flat decision yields this
morning (ADR 0077). Sunny's ruling closes the class, not the
instance.

## Law 1 — NEVER-REGEX (ruled, with the blessed boundary)

**Meaning is never extracted from human or code language by
pattern.** Language is understood by a native parser (code — the
standing ADR 0001 law) or a caged interpreter (natural language),
both emitting typed, validated structures.

The blessed boundary: regex remains legal as a MECHANICAL STRING
TOOL where the pattern IS the complete specification of a
deterministic transform (whitespace collapse, CamelCase splitting,
bracket-stripping in fold(), the R5 boilerplate-stripper). The
census distinction: regex applied to QUESTION TEXT or SQL TEXT to
decide what it means = violation; regex as string utility = legal.
Enforcement: a code census check (to build with the implementation;
until then this ADR is the law's record). The console's keyword
grammar RETIRES; the outage floor is an honest structured form
(pick kind, pick entity, press a display mode) — never a fake
parser, because "an outage costs polish, never truth" applies to
understanding too.

## Law 2 — the only language is the graph's own vocabulary

No new request algebra, no op enumeration. The metamodel — kinds,
edges, the meaning twin — is already ratified, closed, and TOTAL
over meaning (the homomorphism law). Anything the graph can answer
is expressible in the graph's own terms by construction. Sunny's
skepticism of pre-defined operation sets is hereby standing law:
inventing a second vocabulary beside the metamodel is the
enumeration disease wearing types.

## The ask pipeline (Tier A — the metadata console)

1. **UNDERSTAND** (the interpreter, caged): free text -> typed
   mentions {entity-ish phrases, topic phrases} + optional display
   hint. The model PARSES, never generates (axm:M5); its output is
   validated against the index and the metamodel; a failed
   validation degrades to HITL, never to a guess.
2. **GROUND** (deterministic tiers + embeddings): each mention
   resolves exact-identity -> exact folded name -> SEMANTIC
   (vector) -> HITL. The semantic index embeds each node's MEANING
   TEXT (descriptions, steward words, floors) — possible only
   because translation is total (ADR 0077). Every stored vector is
   stamped (content_key + embedding-model version): the change
   quanta extend for free — a meaning that did not change never
   re-embeds. Embedding endpoints live inside the customer boundary
   (the standing customer-Azure-OpenAI governance ruling); only
   door-1-redacted text is ever embedded.
3. **CONNECT** (graph algorithms, no intent enumeration): the
   answer to a multi-mention question is the CONNECTING SUBGRAPH —
   k-shortest paths / capped Steiner-style neighborhood between the
   grounded nodes; single-mention questions get the node's
   neighborhood. Caps and counts are VISIBLE ("showing 5 of 23
   paths"), never silent truncation. Path RANKING inputs (edge-kind
   weights, meaning similarity) are DECLARED, TUNABLE DATA in the
   registry — never a hidden model judgment.
4. **SPEAK** (the graph answers for itself): every node on a path
   renders through the existing policy machinery — floors, steward
   words, the gap taxonomy's named silences. Rendering a path is
   walking it. No answer shapes, no answer generation.
5. **STEER** (HITL; the blessed resolution of irreducible intent):
   where intent is underdetermined, the console shows the connected
   neighborhood and the human drills. DISPLAY MODES — list it,
   floor it, trace it, census it — are BUTTONS THE USER PRESSES,
   never intents a model classifies. Some questions get an
   exploration answer rather than a direct one; that is the design,
   not a limitation.
6. **REMEMBER** (the interpretation ledger): every confirmed
   interpretation lands as a governed event: (question text ->
   grounded mentions + display), with author and model basis.
   Repeat questions match confirmed interpretations by folded text
   BEFORE any model call — instant, free, deterministic — and the
   plan re-executes against the CURRENT graph (the interpretation
   is cached, never the answer). Stewards can list and REVOKE
   interpretations (dispositions). Default confirmation friction
   (adjustable): confirm on first sighting and on low confidence;
   silent on ledger hits.

## Law 3 — THE SEAT-FAILURE LAW (amended 2026-09-06, live find #6:
## "I can't continue to ask more questions")

The first Tier A build caged the interpreter's OUTPUT but not its
FAILURES: a rate limit or network blip raised straight through the
pipeline and killed the page — and the single-threaded server let
one hung seat call freeze every ask. Half a cage. The law:

- **A seat failure is an OUTCOME, never an exception.** Every model
  seat call (interpret, embed) is contained under a DECLARED time
  budget; failure or budget-exceeded yields `seat_down` — the
  deterministic tiers keep answering, the console banners the
  degradation honestly ("interpreter unavailable — exact names,
  kinds, and the structured form still work"), and the failure is
  COUNTED (repeated seat failures are product signal, per the
  error-contract philosophy).
- **The console serves concurrently**: a slow seat call never
  blocks other asks; deterministic questions stay instant
  regardless of model weather.
- **Bounded retry, visible state**: one retry within the budget,
  then seat_down. No infinite spinners, no silent hangs, no
  tracebacks as the only witness.

This is the outage-floor law ("an outage costs polish, never
truth") applied to the seats themselves — the understanding floor
was stated at ratification; the seat floor is its missing half.

## Law 4 — FOLLOW-UP CONTEXT IS DATA, NOT CHAT (amended 2026-09-07,
## live find #7 — "I still can't continue to ask follow up
## questions"; supersedes the mis-read of find #6, which fixed real
## seat defects but not the asked-for thing)

The pipeline was single-turn by design: the entities an answer just
showed were unavailable to the next question, so every natural
follow-up ("which of THOSE are in the ED report?", "show ITS
filters") dead-ended. The old engine's open M2 anaphora residual,
arriving on schedule. The law:

- **Every answer produces a CONTEXT SET** — the grounded entities
  plus the entities the answer LISTED. A typed list of graph
  identities; never prose, never a transcript. The session carries
  it; the ask's usage event RECORDS its context snapshot, so replay
  determinism holds (same question + same recorded context = same
  answer). The tier lock stands: this is a sliding window of
  grounded THINGS, not chat memory.
- **The anaphor tier** (grounding tier 0): the interpreter may mark
  REFERENCE mentions ("those", "it", "the first one", "those
  scopes"); they resolve DETERMINISTICALLY against the context set —
  kind word filters it, ordinals index it, "it" takes the single
  subject. Ambiguity goes to HITL like everything else. The model
  never sees prior answer text — only the entity set is context.
- **The ledger stays context-free**: a confirmed follow-up stores
  the RESOLVED identities, never the anaphor — ledger hits replay
  concrete forever.
- **Answers are clickable**: entities named in an answer render as
  links — the zero-typing follow-up.

**THE CONVERSATION SURFACE (amended 2026-09-07, second leg of live
find #7 — the resolution machinery shipped but the console stayed a
page-per-question form, so the follow-up experience still did not
exist; Echo-Law generator finding: "follow-up" was treated as an
engine property when it is a PRODUCT SURFACE — the conversation is
an operation, and operations are the product):**

- **The console is a transcript, not a page**: rounds APPEND — the
  previous question and answer stay on screen; the input CLEARS
  after each send and stays at the bottom, focused. No full-page
  reloads: the client submits by fetch and receives the round as
  data. (This is the old workbench's proven surface shape,
  src/webapp WORKBENCH_PAGE, adopted deliberately.)
- **Context is CONVERSATION-scoped**: the client holds a
  conversation id and sends it with every ask; the server keys the
  Law-4 context set by it. Two conversations (tabs) never share
  context. A global mutable is a defect, not a simplification.
- **What we refuse from the old workbench**: it fed the prose
  history to the model every turn (run_turn(conv.history, ...)).
  That violates the cage. The split is law: the transcript is
  DISPLAY memory; the typed context set is MEANING memory; the
  interpreter sees one question at a time, never prior answer text.

## Tier B — the logic console (designed now, built after Tier A)

Sunny's AST proposal, landed in the existing vocabulary: the
interpreter builds a QUESTION FRAGMENT — a partial meaning tree in
the ratified kind library ("a selection of encounters · condition
on a sepsis-ish code · RANGE within 30 days of discharge") — and
answering is STRUCTURAL MATCHING of the fragment against the
estate's twins (content_keys + subtree similarity). The answer:
"this existing logic already computes what you describe" -> its
floor. This IS the inward flow's MATCH stage from L0, no longer a
parked mystery; it shares grounding, embeddings, and the ledger
with Tier A. Sequencing blessed: Tier A ships and gets tested
first; Tier B follows; GENERATION (new estate when nothing
matches) remains deferred and gated by the tier lock.

## What survives from ADR 0078

The console surface and its honesty machinery: three outcomes,
clickable ambiguity, H5 usage events (extended to carry the
interpretation), Kind_Vocabulary as grounding data, the drift-
findable-by-name search law, no open chat (the tier lock). The op
list retires as a LANGUAGE; its useful members survive as display
modes and deterministic renderers.

## Open at ratification

- ~~The demo interpreter/embedding endpoint~~ RESOLVED 2026-09-06:
  OPENAI_API_KEY in .env (Sunny's key), verified live — interpreter
  = gpt-4o-mini, embeddings = text-embedding-3-small (1536 dims).
  Demo-only: the estate is synthetic; production stays governed by
  the customer-Azure-OpenAI ruling (a config swap — llm_client
  already speaks both header styles).
- The never-regex census check (mechanical enforcement) ships with
  the implementation.
- Ranking-weight defaults: seeded by us, tuned by evidence,
  declared in the registry.

## Relations

0077 (total translation makes NL-NL grounding and speaking-nodes
possible) · 0078 (superseded in part) · 0076 (compose, never
enumerate — now applied to questions) · 0001 (native parsers; the
code-side of never-regex) · L0 inward flow (Tier B is its MATCH
stage) · the tier lock (no open chat; artifacts land, chat doesn't).
