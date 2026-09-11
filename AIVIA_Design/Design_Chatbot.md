# Design — Chatbot

**OWNERSHIP (the boundary, ruled 2026-09-09):** this doc owns
everything that exists ONLY inside a conversation — the
Interpreter, ask-time search and ranking, memory/ledger, the nine
laws, the UI. Design_Graph_Engine.md owns everything that exists
WITHOUT a conversation — stores, builders, readings, censuses,
speech CONTENT (THE SPEECH CONTRACT) and the Scribe pipeline. The
split test: would it exist with no chatbot at all? Cards and the
semantic index are an engine READING; the ask flow that consumes
them lives here.

*(Born 2026-09-07 from Sunny's first-principles reset: "go back to
first principles, design the user interface/search/chatbot from
scratch." This is the chatbot's design document — companion to
"Design_Graph_Engine.md". Items marked ► RULED are Sunny-ratified
decisions; unmarked sections are design-in-progress under the dig.
Registry/ADR landings follow on Sunny's build order; CODE IS PAUSED
until the dig completes.)*

► RULED (Sunny, 2026-09-07): the pre-made kind-vocabulary table
dies — everything must be searchable; no pre-made mapping tables.
Vocabulary is earned through confirmation, never authored in
advance.

► RULED (Sunny, 2026-09-07): END USERS CONSUME PBI REPORTS (the
Microsoft shop). The report layer is part of the estate: PBI
reports/semantic models (TMDL) enter through the same intake door
as SQL, become nodes of a report kind with their own speech
(report/page/visual names), and carry executes-edges to the procs
they run. Evidence: "ED Sepsis Screening Dashboard.SemanticModel"
found at repo root reading THREE procs via EXEC — reports aggregate
procs; the consumption layer is many-to-many, NEVER fabricated 1:1.
The real dashboards (ED Sepsis, Diabetes) are the honest start.

► RULED (Sunny, 2026-09-07, "finalize this decision"): THE FACET
DECISION. One node = MANY embedded cards, never one blended vector:
a NAME card, a SPEECH card, and its PART-cards (conditions,
parameters — already separate nodes since ADR 0080). A node's
search score = the MAX over its cards [SUPERSEDED 2026-09-08 by
THE TOTAL-SCORE LAW below: the score is the SUM of card hits
across all mentions — no max; this sentence stands as the facet
decision's record, not the scoring rule]; the answer names WHICH
card matched (provenance); a shared card (a source table's
description) embeds ONCE and is pointed at, never copied. The deciding evidence
(live probes, 2026-09-07, text-embedding-3-small):

| "ED Sepsis" vs USP_ED_SEPSIS as… | score |
|---|---|
| name card ("usp ed sepsis") | 0.7783 — auto-match |
| raw name ("USP_ED_Sepsis") | 0.7715 — casing/underscores fine |
| today's one blended vector (4,774 chars) | 0.3954 — buried |

| query vs ENCOUNTER_ID | blended | name card |
|---|---|---|
| "encounter id" (spacing) | 0.7559 | 1.0000 |
| "Enconter_id" (typo) | 0.5140 | 0.5689 → HITL candidate |
| "unique id for the patient visit" (paraphrase) | 0.6197 | 0.5308 |

The last two rows are the proof both cards are NEEDED: the name
card wins name-shaped queries, the speech card wins meaning-shaped
queries — one vector forces a choice and both choices lose
somewhere. Typos land mid-range on either card and surface as
scored candidates (the honest "did you mean?"), which only works
because thresholds are floors, never cliffs (ADR 0080).

The elimination principle (from the same exchange): every
hand-written mapping is a bridge between user language and graph
things. The replacement: **the graph's own self-description + the
LLM's language knowledge as proposer + human confirmation +
the ledger as memory.** Only the physics stays authored (store,
parser, grammar) — never the mappings.

---

## The architecture (three stores, two seats, three functions, one envelope, one surface)

```
              ┌───────────────────────── THE SURFACE ─────────────────────────┐
              │  transcript · confirm affordance · buttons · clickable things │
              │  the trace (work shown) · coverage line                       │
              └──────────────▲────────────────────────────────┬───────────────┘
                             │ envelope                       │ question
              ┌──────────────┴───────────┐      ┌─────────────▼──────────────┐
   PURE       │  RENDERER                │      │  INTERPRETER (model seat)  │
   FUNCTIONS  │  subgraph → words        │      │  words → PROPOSAL only     │
              │  (ratified grammar)      │      │  {phrases, expansions,     │
              ├──────────────────────────┤      │   steering hint}           │
              │  ENGINE                  │      └─────────────┬──────────────┘
              │  matched sets → answer   │                    │
              │  subgraph (filter ∩      │      ┌─────────────▼──────────────┐
              │  traverse · neighborhood)│◄─────┤  MATCHER                   │
              │  ONE engine, no shapes   │      │  any string → scored       │
              └────────────▲─────────────┘      │  matches over FACET CARDS  │
                           │                    │  (exact→semantic, max over │
                           │                    │   cards, floors not cliffs)│
              ┌────────────┴────────────────────┴──────────────┐
   STORES     │ TRUTH STORE: the graph — content + its own     │
              │  SELF-DESCRIPTION (types, capabilities,        │
              │  boundaries are nodes; written by builders)    │
              │ MEMORY: per-user TREES + the shared estate     │
              │  tree — confirmed interpretations, earned      │
              │  vocabulary, usage affinity (human acts only)  │
              │ SESSION: the table — this conversation's       │
              │  context set (ephemeral; snapshots into the    │
              │  user's tree on confirmation)                  │
              └────────────────────────────────────────────────┘
```

**The stores** are the only stateful parts. Truth: written by
builders only, self-describing. Memory: per-user trees beside the
shared tree, written by human acts only, promotion personal→shared
is a steward blessing. Session: the table of shown things.

**The model seats** are stateless proposers: the interpreter turns
one question into a typed PROPOSAL (phrases, expansions, steering
hint) that expires unless confirmed; the smoother (gated) polishes
prose and changes no facts.

**The pure functions**: ONE matcher over the facet cards of
everything (content, types, vocabulary); ONE engine doing set
algebra over matches and edges (no per-question-shape branches);
ONE renderer via the ratified grammar.

**The envelope** is the contract every response travels in:
{outcome, payload, evidence+scores, trace, context set, coverage} —
identical for answers, clarifies, honest zeros, and degraded modes.

**The loop**: hear → propose → match → (confirm when new or
ambiguous) → connect → render → present → remember. Confirmation is
a first-class stop in the loop, never an error path.

**Forbidden by construction**: no component both holds state and
decides; models touch no state; nothing maps language to things
except matching-over-cards plus memory; every kind of knowledge has
exactly ONE home — so "fixed in the card but not the search" cannot
recur.

---

## Law 1 — Truth lives outside the model

**Statement.** The chatbot is a window onto a knowledge store,
never an oracle. Every claim traces to something stored; the model
contributes zero facts. If it isn't in the store: "it isn't there."

**Implies.** Provenance per claim, not per answer. Model output
that can't be traced is discarded, not shown.

**Today.** Mostly held (floors, the cage, honest no-match). The
model's smoothing seat is designed but gated.

**Dig outcomes (2026-09-07, Sunny's Law-1 pass):**

► RULED: THE GRAPH IS THE REALITY. Absence claims never speculate
about the un-loaded world: "no <kind> named <x> exists" is the
honest and complete answer when the graph holds nothing. The
system claims nothing about what was never loaded. (What the graph
DOES hold about its own intake — receipts, registrations — is
graph truth and may speak like any other node; but there is no
"outside coverage" speech.)

► RULED: "what is sepsis" FINDS SEPSIS. A concept question is a
SEARCH, not a dictionary lookup — the estate answers with what it
knows: the files, tables, conditions, and codes that carry the
word/meaning. The estate's conditions ARE its definition-in-
practice (how sepsis is identified HERE: the codes, the alerts,
the thresholds). "No definition stored" as a dead-end was wrong —
absence of a minted term never blocks the search; the term-mint
invitation rides at the END of a full answer, never instead of one.

► DIRECTED: the model seats get DISTINCT NAMES and a RIGHTS
CONTRACT — the conversation model and the description-writing
model are different operations, different scopes, different I/O,
and the graph's data contract must state which model may do what.
(Names proposed below, awaiting Sunny's confirmation.)

► RULED (Sunny, 2026-09-07): the seat names + rights table below
stand. Clarifications from the same pass:
- **The Interpreter and the user's tree**: the Interpreter still
  writes NOTHING — the pen belongs to the human's CONFIRM act,
  which writes the (proposal + resolution) into the user's tree as
  a governed event. The ask flow records the raw proposal on the
  usage event as EVIDENCE (auditable, expiring), never as truth.
  Seats never write; flows record events; human acts create truth.
- **Smoothed text is never in the user's tree**: the tree stores
  THINGS and ACTS (what was viewed, what was confirmed), never
  prose — stored prose goes stale the moment the graph moves.
  Smoothed renderings may live in a regenerable shared CACHE keyed
  by (floor content, smoother model) — the embeddings posture
  exactly — recomputed freely, truth never.

► RULED: D2 — EVERY RENDERED LINE IS A CLICKABLE NODE. The answer
is a list of addressable facts, not a paragraph; each line links to
the node that justifies it (per-claim provenance = the UI default;
collapses into Law 5's context set).

► RULED: the Smoother grounds by SLOT-SURVIVAL — load-bearing
spans (column phrases, values, numbers, negations) are immutable
slots that must survive VERBATIM, checked mechanically after the
call; a failed check ships the floor. Presentation-only, visibly
marked, floor one click away.

**Seat names + rights (RULED):**

| seat | operation | runs at | INPUT | OUTPUT | graph rights |
|---|---|---|---|---|---|
| THE SCRIBE | drafts descriptions/definitions | curation time | graph facts + source evidence | DRAFT text w/ basis stamp | write ONLY through gate + human approval (door 3); never at ask time. FULL DESIGN: THE SPEECH CONTRACT + Scribe pipeline, Design_Graph_Engine.md (09-09). Build status: OPEN — only the acronym proposer has ever run (Manifest_Build §C) |
| THE INTERPRETER | parses questions | ask time | ONE question string | typed PROPOSAL (phrases, expansions, hint) | NONE — reads nothing, writes nothing |
| THE RANKER | embeds text for matching | index/ask time | speech texts / query | vectors, scores | derived cache only; asserts nothing |
| THE SMOOTHER | polishes rendered prose | presentation time | rendered floor | display text, facts unchanged | NONE — never stored; floor one click away |

Open from this pass: D1 (three doors, refined statement) — implied
accepted by the seat contract, awaiting explicit word; D2 (every
line a clickable node) — explained, awaiting ruling; D5 grounding
method for the smoother — slot-survival check proposed.

## Law 2 — Language is the interface, not the storage

**Statement.** Understanding converts words into references to
stored things; answering converts stored things back into words.
The model translates at the two boundaries only.

**Implies.** No prose memory anywhere in the middle; no
model-written text stored as truth.

**Today.** Held at the surface (context sets, not transcripts).
Violated historically whenever a reading authored words.

**Dig outcomes (2026-09-07, Sunny's Law-2 pass — all ruled):**

► RULED (D1): CONFIRMATION ATTACHES TO THE REFERENCE-SET, NOT THE
PHRASING. The ledger was a phrasebook (folded-text keys: "what
reports use ENCOUNTER_ID" confirmed ≠ "which reports use
encounter_id" — same meaning, model re-called, re-confirmed); it
becomes a MEANING-BOOK. The blessed object is the resolved
reference-set; the folded-text key survives only as a model-
skipping fast path. A new phrasing resolving to a confirmed
reference-set answers immediately (trace: "resolved to your
confirmed interpretation of <date>"); only fresh reference-sets
confirm. Phrasings attach to meanings as earned evidence — "these
4 phrasings mean this question" is flywheel vocabulary.

► RULED (D2): CLAIM WORDS vs FRAME WORDS. Any sentence ABOUT the
estate comes only from speech or the ratified grammar (claim).
Labels, counts, section headers ("Connected:", "28 of them") are
FRAME — mechanical presentation code may author. The review-time
question for every new string: claim or frame?

► RULED (D3): THE CONFIRM CARD IS THE INBOUND BOUNDARY, VISIBLE.
It must display the COMPLETE boundary artifact — every mention →
its reference, every expansion tried, the steering hint — and
confirming blesses exactly that artifact, nothing hidden. With
lines-are-nodes (Law 1) covering the outbound seam, the whole
translation layer is inspectable.

Corollary (restated as Law-2 law): the inbound boundary is the PHI
boundary — raw text passes the phi-gate before any storage; the
Interpreter runs inside the customer model boundary; once words
become references, everything downstream (ledger, context, tree)
holds references, never prose.

## Law 3 — Refusing to guess is expertise

**Statement.** "I don't know" and "which did you mean?" are expert
answers. No-match, ambiguity, partial answers ship with evidence.

**Implies.** No cliff anywhere: uncertainty is shown with scores,
never collapsed into silence or a guess.

**Today.** Cliffs removed; BUT the clarify list quality is poor
(the ED-Sepsis pick-list buried the obvious file — ranking, dedup,
and expansion failures make honest clarifies feel dumb).

**Dig outcomes (2026-09-07, Sunny's Law-3 pass — all ruled). The
dug law: NEVER GUESS SILENTLY, NEVER ASK LAZILY — refusal earns its
honesty through the quality of the evidence and of the question
asked back, and both are measurable.**

► RULED (D1): THE THIRD RESPONSE SHAPE — the PROVISIONAL ANSWER.
Evidence profile picks among three shapes: clear winner -> ANSWER
with the assumption visibly stated + runners-up one click away
("Answering for USP_ED_SEPSIS · also matched: ... — switch");
close cluster -> CLARIFY; nothing above the floor -> honest
absence. A disclosed, reversible assumption is not a guess — a
guess is an UNDISCLOSED assumption. Margins are registry data.

► RULED (D2): CLARIFY OBLIGATIONS. A lawful clarify: dedupes at
name grain (one row, "in N tables"); groups by kind; caps visibly
("… and 12 more — narrow?"); every candidate carries score + one
line of speech (choosing between meanings, never identifiers).
If the true referent was not IN the list, the clarify FAILED.

► RULED (D3): THE CLARIFY-MISS COUNTER. The user's next action
after a clarify is recorded on the usage event: picked (hit) /
re-typed (miss) / abandoned. The clarify-miss rate is a standing
census number — rising = ranking or speech failing = product
signal (the error-contract philosophy applied to the questions we
ask back).

► RULED (D4): PARTIAL ANSWERS ARE LAW. Multi-mention questions are
never all-or-nothing: what grounded answers, what did not is NAMED
ungrounded in the same breath. (Ratifies the 0080 anchored-topic
behavior as the Law-3 shape.)

## Law 4 — The user's words outrank the system's categories

**Statement.** The question's own words select what comes back;
narrowing comes from the user, never from a classifier. No
predefined question shapes.

**Implies.** No intent lists, no op sets, no hand-authored
word→category tables (► RULED above). The LLM proposes mappings;
the graph's matches decide; the human ratifies.

**Today.** VIOLATED in two live places: the Kind_Vocabulary table
(hand-authored rows) and execute()'s branch dispatch (hand-written
combination cases). Both named for death in the 0080 diagnosis;
the dispatch survived the build (the unbuilt-build lesson).

**Dig outcomes (2026-09-07, Sunny's Law-4 pass — all ruled). The
dug law: THE SYSTEM BRINGS SETS AND CONNECTIONS; THE USER'S OWN
WORDS BRING THE SHAPE.**

► RULED (D1): THE ONE ENGINE — the dispatch's death warrant. Every
grounded mention is a SET of nodes (entity=singleton, kind=all of
type, anaphor=context pool, topic=scored matches). The engine does
ONE thing: CONNECT THE SETS — keep elements linking to the other
sets by edges, ownership chains, or short paths (two singletons ->
the path IS the answer; big set + singleton -> connected members;
big set + scored set -> connected members ranked). THE DISPLAY SET
IS CHOSEN BY THE USER'S OWN WORDS: a named kind is the answer
shape ("business logic in ED Sepsis" -> the conditions, because
the user said so); no kind named -> the subject's neighborhood or
the path. Nothing is ever classified. execute()'s branches die
into this at build.

► RULED (Sunny, 2026-09-08, the scoring walkthrough): THE
TOTAL-SCORE LAW + THE ONE-VOCABULARY LAW.

**THE TOTAL-SCORE LAW.** A node's cards: NAME · SPEECH · LABEL
(the label word — every member node carries its label as a card;
the label:: group entries DIE) · EXPANSION (its acronyms'
expansions, when blessed). A node's score for a question = THE SUM
of all its card hits across all mentions — each card counts once
per mention; no max, no propagation, no "which card hit first."
"reports"+"ED" both crediting the dashboard's cards is what ranks
it first; the census emerges ("what tables are there" = every
table's label card at ≈1). The LEXICAL scorer (hybrid search) is
DEFERRED-CONDITIONAL: built only if columns still overcrowd the
right labels after total-score + the PBI layer land — the trigger
is observed overcrowding, recorded when seen.

**THE ONE-VOCABULARY LAW.** Acronym expansions live as ACRONYM
nodes (label: acronym) — NEVER in code, NEVER in prompts, and NOT
as terms ("term" is reserved for the governed logic units:
'diabetic patients', 'cancelled appointments'):
  {name: "ED", expansions: ["emergency department", ...],
   approved_by: person:..., approved_at: ...}
Edges: —approved_by→ the person (direct; timestamp as data; no
ceremony event) · —used_by→ every node whose name carries the
token, DERIVED AT GRAPH BUILD (boot + after each intake): a newly
loaded node gains the edge automatically — no re-approval, no
manual step, and NEVER computed at question time. Both readers
consume the same stored expansions verbatim: card building (the
expansion card) and query building (mention token → expansions
appended to the search text, deterministic) — supply and demand
read one string, so their vectors meet at ≈1 by construction. The
pre-vocabulary window (unblessed tokens) is the Interpreter's
proposal space; every blessing shrinks it permanently. Pipeline:
SCAN (mechanical: distinct name tokens) → SCRIBE (curation-time
seat proposes expansions) → BLESS (human approves the batch) →
acronym nodes.

► RULED (Sunny, 2026-09-11): THE GLOSSARY PROCESS refines this
pipeline into the five-phase evidence ladder — dictionary-first
(vendor/org truth is a customer prereq; ours authored), guessing
last, every scanned token conserved in ONE ledger file
(`<estate>/glossary/acronym_ledger.json`), the Scribe fed
evidence and allowed to abstain. Full ruling:
Ruling_Glossary_Process.md. The acronym NODE shape above is
unchanged; only the road to blessing changed.

► RULED (Sunny, 2026-09-09): THE LIVE-SEAT RULE. Wherever
production calls a model seat, a LIVE test calls the same seat —
same registry prompt, same estate — so test and prod behavior are
provably consistent. The live tier is run locally before any
"done" claim (never by CI: keys, cost, and a red build must mean
broken code) and is nightly-able. Deterministic tests remain the
per-push safety net: REPLAYED REAL recordings (the content-keyed
caches as fixtures — never synthetic physics; the fake embedder
dies) and SCRIPTED proposals (authored test inputs, loud on miss).
Deciding evidence: the 'ED → term' over-marking was invisible to
every deterministic test and only surfaced live.

**LABEL, not kind — everywhere.** The node-type field and every
surface says LABEL (the industry standard; Sunny's standing
ruling). The rename is promoted ahead of the search rework. The
TWIN's meaning-node taxonomy (the ratified kind library:
COMPARE_EQ, selection, reference...) is a DIFFERENT concept and
keeps its ratified name — documented here so the two never blur.

► RULED (Sunny, 2026-09-07, the search walkthrough): THE SEARCH IS
THE ANSWER — Sunny's envisioned pipeline verbatim, superseding the
tier ladder and the outcome branching:

1. The question hits the LLM DIRECTLY (no pre-anything, no string
   tier — never-regex means NEVER; the "mechanical boundary"
   carve-out is revoked from the search path).
2. The LLM understands INTENTION: extracts the mentions ("reports",
   "ED") and expands ("ED" -> emergency department, emergency room).
3. VECTOR SEARCH runs against EVERYTHING in the graph — every
   label (itself a vectorized entry, so "tables" can hit the group
   "table"), every name, every description — all pre-vectorized
   and cached. The search text is mention + expansions.
4. RANKED HITS WITH SCORES return to the user — mixed labels
   welcome (the PBI dashboard, the procs, a column), grouped by
   label for readability, each with its score and which card
   matched. The search result IS the answer; clarify and the
   provisional answer are EMERGENT from the ranking (several
   strong hits / one dominant hit), never coded branches.
5. CLICKS ARE STEER: a click opens the entity round (floors,
   views, lineage) and lands on the table. Relational questions
   traverse on demand from found things.

THE SUBSUMPTION FACT (measured): exact matching is the cosine≈1
case of vector search — "encounter id" vs its name card scored
1.0000; typos land 0.5-0.6 (honest "did you mean" candidates);
paraphrases 0.5-0.7. One mechanism covers the whole spectrum; the
string tiers were a redundant second implementation of its top.
What survives beneath: the memory checks (ledger/meaning-book —
Sunny's decisions replayed), the proposal cache, pinned model
versions (Law 8), and cosine arithmetic itself.

Labels are chosen at modeling time to BE the words users say
("PBI Report") — naming the model well IS the vocabulary work.
The graph's own label entries answer type words; org synonyms are
earned. Thresholds become DISPLAY BANDS (how much of the list to
show) — frame, not behavior.

(The earlier pre-tier ruling below stands as the record of the
first step of this arc.)

► RULED (Sunny, 2026-09-07, the step-by-step walkthrough): THE
PRE-TIER DIES (option c). Typed input is LANGUAGE and language
always goes through the Interpreter — the system never pre-guesses
that a typed string is a name (the "sepsis"-column hijack, caught
live, is the deciding corpse). Two forced consequences, both
ruled with it:
- CLICKS ARE NOT QUESTIONS: a click on a rendered node is STEER,
  not language — the surface routes it as a direct entity round
  (the display-mode pattern), never through ask()'s language path.
  Clicks stay instant and deterministic WITHOUT any pre-tier.
- THE DEGRADATION LADDER AMENDS (level 2, interpreter down): what
  still works = clicks, buttons, the table, ledger/meaning-book
  hits, and proposal-cache hits — typed exact names NO LONGER
  answer during an outage (the honest price of never guessing;
  registry ladder row updates with the build).
The memory lookups (folded-question ledger, meaning-book, proposal
cache) are NOT guessing — they are earned determinism and stay
ahead of the model.

► RULED (D2): THE COLD START — the system is allowed to be young.
Day one: exact tiers work; the graph's SELF-DESCRIPTION (kind
nodes speaking metamodel definitions = physics, legitimately
shipped) grounds type words via Interpreter proposal + confirm;
every confirm is flywheel capital. Week one asks more questions —
that is the feature (learning the org's dialect), never a defect.
No shipped vocabulary.

► RULED (D3): THE ANAPHOR TABLE DIES THE SAME DEATH. The
Interpreter marks reference-roles in its proposal; resolution
against the context set stays fully deterministic; confirmed
reference-words accrete like all vocabulary. Day-one "those" costs
one model call + confirm; free thereafter. Seat-down floor:
clicking the Referenced links.

► RULED (D4): VIEWS ARE NOT INTENTS. Display modes are VIEWS of a
thing (chart types), never types of question — the user presses,
the hint may PRESELECT visibly. Intent enumeration decides what a
question MEANS (banned); a view decides how to LOOK at the answer
the user already chose (STEER). The view set is closed product
surface, changed only by ruling.

## Law 5 — What was shown becomes addressable

**Statement.** Conversation state is the THINGS on the table, not
the chat prose. "Those / the first one / its filters" resolve
against exact entities.

**Implies.** Every answer yields a typed context set; replay is
deterministic; the model never re-reads prior prose.

**Today.** Built (Law 4 of ADR 0079 + the conversation surface).
The anaphor WORD LIST is still hand-authored — same species as the
kind table; candidate for the same elimination.

**Dig outcomes (2026-09-07, Sunny's Law-5 pass — all ruled). The
dug law: THE TABLE IS REAL — stacked, visible, and everything the
user does lands on it.**

► RULED (D1): THE STACKED TABLE. Context is a bounded stack of
rounds (depth = registry data, ~5). Bare anaphors and ordinals
resolve against the TOP, always (predictability beats reach);
kind-qualified anaphors ("those scopes") search DOWN for the
nearest matching pool; cross-round ambiguity clarifies WITH round
provenance; beyond the bound, things fall off — durable recall is
the tree (D4).

► RULED (D2): SELECTIONS ARE ACTS. A click, a clarify-pick, a mode
press lands on the table exactly like a typed answer. A
clarify-pick is a LIGHTWEIGHT CONFIRMATION: phrase -> chosen
reference accretes to the user's tree (feeds the Law-2
meaning-book; the next ask leads with the pick as a provisional
answer). Every clarify the user answers makes the next one
unnecessary.

► RULED (D3): THE TABLE IS VISIBLE. A persistent surface region
shows what is on it (top expanded, older rounds collapsed), every
item re-invocable; "CLEAR THE TABLE" is an explicit user act. Law
6 applied to Law 5: if "those" resolves against state, the user
sees the state before typing.

► RULED (D4): SESSION TABLE vs USER TREE — two memories, never
confused. Anaphors NEVER cross sessions ("those" tomorrow = an
honest "nothing on the table yet"); durable recall is a TREE QUERY
("the report I viewed yesterday" — acts accreted, deterministic).
Confirmed rounds snapshot the pool they used; replays hold
regardless of the table's later state.

## Law 6 — The work is shown

**Statement.** What was searched, what matched, at what score,
what was excluded, what was cut — visible in every answer. The
process is the product; the answer is a caption.

**Implies.** The trace is UI, not log. Suppression is a display
toggle, never a removal. The trace doubles as the audit record.

**Today.** Trace line ships in every round (0080). It is terse —
one line — and does not yet show expansions-not-proposed, facets
checked, or cut candidates.

**Dig outcomes (2026-09-07, Sunny's Law-6 pass — all ruled). The
dug law: EVERYTHING THAT SHAPED THE ANSWER IS REACHABLE FROM THE
ANSWER — in human words, rendered from recorded facts.**

► RULED (D1): THREE LAYERS — caption (the answer, always), work
(the compact trace line, always, expandable), evidence (the full
record: every candidate, every card, everything cut). NOTHING
about how an answer was produced may exist only in a log.

► RULED (D2): THE TRACE SPEAKS HUMAN, RENDERED FROM DATA. Plain
process-language via fixed templates ("Looked for X by exact name —
nothing. Searched by meaning — 8 close matches, best 0.63. No
expansions were proposed."); scores stay visible; raw technical
form one expansion deeper. Trace lines are the third word class —
PROCESS WORDS: claims about what the system did, rendered ONLY
from recorded trace data, never hand-narrated, never
model-summarized.

► RULED (D3): THE COMPLETENESS SPEC (closed). Per mention: tiers
tried in order w/ outcomes; expansions proposed AND the explicit
"no expansions proposed". The winner: match, score, WHICH CARD
(facet provenance). The engine's choice: one line of display-set
rationale ("showing conditions — you named the kind"). The cuts:
below-floor counts, caps applied. The negative space: a kind
answer carries the kind's counted exclusions when nonzero.
Closing rule: anything the system did that shaped the answer
appears; anything not in trace data may not be claimed about the
process.

► RULED (D4): THE TRACE IS DERIVABLE, NEVER STORED PROSE. The
recorded facts are its INPUTS — the question, the Interpreter's
raw proposal (already evidence), the context snapshot (already
Law 5). Everything downstream is deterministic: any past round's
full trace recomputes on demand, exactly, forever.

## Law 7 — Learning happens only through confirmation

**Statement.** The system improves by remembering what the human
blessed — interpretations, vocabulary, mappings — revocable and
auditable. It never drifts toward its own guesses.

**Implies.** Every learned thing has an author, a timestamp, a
basis, and a revoke path. The model's proposals expire unless
confirmed.

**Today.** Interpretation ledger + expansion→term lifecycle built;
the PROPOSER half is dark (the prompt never invites expansions —
the unbuilt-build lesson, instance one).

**Dig outcomes (2026-09-07, Sunny's Law-7 pass — all ruled). The
dug law: THE SYSTEM'S ENTIRE EDUCATION IS A LEDGER OF HUMAN ACTS —
personal first, promoted by use, anchored to meaning, revocable
with eyes open — and it never grades its own homework.**

► RULED (D1): THE SCOPE LADDER. Every confirmation lands PERSONAL
first (the user's tree; zero friction, zero blast radius). Usage
aggregates into PROMOTION CANDIDATES (N users confirm the same
mapping -> the steward's queue, usage-weighted). STEWARD BLESSING
makes it estate-shared. Two tiers now; team scoping can slot later
without changing the law. Nothing is born shared.

► RULED (D2): INLINE BY DEFAULT. Confirmation blocks only when the
engine is genuinely stuck (close cluster); otherwise the
provisional answer ships WITH "I read it as X — confirm/correct"
attached. USING AN ANSWER IS NOT CONFIRMING IT: clicks are
affinity evidence (promotion candidacy), never silent blessing —
consent is a click on the confirm, nothing softer.

► RULED (D3): REVOCATION. Personal blessings: the user revokes;
estate-shared: the steward. Revocation = a superseding EVENT,
never deletion. Past answers STAND (they cite their basis); future
asks stop using the mapping immediately; dependent ledger entries
flag stale and re-interpret on next use. The BLAST RADIUS shows at
revoke time ("affects 12 remembered questions") — no blind
revokes.

► RULED (D4): BLESSINGS ANCHOR TO MEANING IDENTITY (content keys —
the Phase-D law applied to the ledger). Time never expires a
blessing; a TRUTH CHANGE orphans it visibly and invites
re-confirmation. And the sharpest edge: TELEMETRY PROPOSES, THE
SYSTEM NEVER SELF-MODIFIES — the clarify-miss counter may put
"floor 0.22?" in front of the admin; the registry change is a
human act, always. Auto-tuning is drift wearing a dashboard.

## Law 8 — Consistency is part of honesty

**Statement.** Same question + same truth = same answer; a changed
answer traces to changed truth, never model weather. Failures
degrade to a smaller honest capability, never a fake.

**Implies.** Interpretations cached, answers never; deterministic
tiers immune to model outage; every nondeterministic seat is
bounded, bannered, counted.

**Today.** Built (ledger replay, seat-failure law, change quanta).

**Dig outcomes (2026-09-07, Sunny's Law-8 pass — all ruled). The
dug law: EVERY SOURCE OF VARIATION IS EITHER DECLARED (a versioned
rule), EARNED (a recorded act), OR NARRATED (a change caption) —
nothing just happens.**

► RULED (D1): THE EMBEDDING MODEL IS PART OF THE RANKING RULE —
neither truth nor weather. Pinned as registry data (vectors
already stamped); upgrading is a DELIBERATE RULE-CHANGE ACT:
announced, versioned, total re-embed (the grammar-bump quantum).
Migrations are validated by the clarify-miss rate — measured, not
vibes.

► RULED (D2): THE PROPOSAL CACHE. Interpreter proposals cache by
(question text, model version) — derived, regenerable, never
truth. One model call per distinct question per model version;
determinism extends to UNCONFIRMED asks; an interpreter upgrade
becomes a declared rule change, not drift.

► RULED (D3): THE DEGRADATION LADDER, DECLARED AS DATA. Five
levels, each bannered with WHAT STILL WORKS, each drop counted:
all-up · Interpreter down (exact tiers + every CONFIRMED question
still answers — the flywheel is the outage insurance) · Ranker
down (deterministic only) · both down (names, clicks, buttons,
the table) · store down (the honest outage).

► RULED (D4): THE CHANGE CAPTION. Answers never cache — but when a
confirmed/ledger question re-executes and differs from its
recorded snapshot, the answer says so: "changed since you asked on
<date>: 3 scopes added, 1 description changed," full diff
recomputable on demand, never stored. Consistency's other half:
accounting for every instability.

## Law 9 — Nothing is silently absent

**Statement.** Everything stored is findable, everything findable
speaks for itself, whatever can't is COUNTED out loud. Absence is
a statement, never a hole.

**Implies.** Census equations as standing tests AND user-visible
numbers; honest zeros ("0 reports about X") instead of no-match
when the question was understood.

**Today.** The three censuses live with numbers. The user-facing
surface of absence is uneven (the honest zero exists; "the store
doesn't cover that AREA" does not).

**Dig outcomes (2026-09-07, Sunny's Law-9 pass — all ruled; THE
DIG IS COMPLETE, all nine laws). The dug law: THE SYSTEM KNOWS
WHAT IT KNOWS, SAYS WHAT IT DOESN'T, AND TURNS EVERY ABSENCE INTO
AN ADDRESS.**

► RULED (D1): THE COVERAGE LINE — header always (ambient: "sepsis
— 28 files · 90 tables · loaded Sep 5"), INLINE on absence answers
("no report named X exists — searched all 28 files"): the zero
cites its searched universe. All of it graph self-knowledge
(receipts, censuses), never claims about the un-loaded world
(Law-1 graph-is-reality).

► RULED (D2): THE CENSUS IS THE FRONT DOOR. The empty-table state
IS the estate card: what's here, the kinds, the biggest topics,
and — honest before impressive — the gap numbers. "What can I ask
you?" answers from self-description, day one.

► RULED (D3): EVERY COUNTED THING IS ASKABLE. "What don't you
know?" is a first-class question: census buckets queryable by
name; counted ITEMS are nodes (drift already; parse exclusions
join). The system's map of its own ignorance is queryable.

► RULED (D4): ABSENCE ANSWERS ARE DOORS. Every honest zero ships:
the searched universe + the nearest true things + the NEXT ACT
(mint a term / flag to steward / load an extract, role-scoped).
Repeated hits on one absence = demand data for the steward queue.
Scope note: SEARCHABILITY IS ACCESS-SCOPED — personal trees
owner-only, governance events steward-only; the searchability
census gains a scope column.

---

## THE TURN DEFAULT — HITL after every turn (► RULED, Sunny 2026-09-11)

**Statement.** EVERY chatbot turn ends at a human choice point.
The machine's findings are OFFERED — ranked candidates with their
labels and scores, a visible cap with the remainder counted — and
the human's pick (a click or new words) steers the next act. This
is the DEFAULT for every chatbot surface AIVIA ships (the product
Workbench/Resolution Console and the meaning-test console alike);
a surface that omits the choice point needs a ruling naming why.

**The shape (non-blocking).** The turn still ANSWERS — the crown
proceeds by default so momentum survives — but the runners-up ride
along as live choices. Choosing re-runs the act with the pick
PINNED. Blocking clarify remains reserved for genuine ambiguity
(the clarify obligations, L3-D2); the choice point is an offer,
never a gate.

**The pick's authority.** A pin is the HUMAN ACT: it becomes the
crown for that mention and outranks scores, margins, and
constraints (the user may overrule their own earlier words). A pin
whose candidate has left the match set is an honest reported miss
— never a silent fallback. Picks are steer and accrete as acts
(clicks-are-steer; selections-are-acts, L5-D2).

**Why this is the default, not a feature.** It closes the loop the
whole design is built on — machine proposes → human chooses →
deterministic execution → display (plan-confirm-execute-display;
operations are the product). It is also the flywheel's mouth:
every pick is usage evidence for the meaning-book without any
self-tuning (Law 7 — learning only through confirmation). First
implementation: the meaning-test console's choice step (step-3
rider above, built 2026-09-11 with acceptance tests from Sunny's
ADT_EVENT rounds).

**The machine never chains past a choice point.** No autonomous
multi-turn continuation: a turn's output is findings + offered
choices, and only a human act (pick, confirmation, or a new
question) starts the next turn.

## The elimination worklist (today's authored bridges, for the dig)

| authored thing | species | replacement under the laws |
|---|---|---|
| Kind_Vocabulary table | word→type mapping | ► RULED dead: kinds are searchable nodes; LLM proposes, human confirms, ledger remembers |
| Anaphor_Vocabulary table | word→role mapping | candidate: LLM marks reference-mentions; deterministic resolution against the context set stays |
| execute() branch dispatch | combination cases | one engine: matched sets → filter/connect by edges → speak |
| interpreter prompt rules | behavior spec | stays (physics of the cage), but must INVITE proposals |
| grounding tier order | mechanism | stays (physics), thresholds already data |
| display modes | ratified buttons | stays (user-pressed); LLM may propose a preselection (hint), human sees it |
| grammar / parser / store | physics | stays authored — the one legitimate zone |

---

## The data contracts (question 1 of the readiness dig, 2026-09-07)

One row per part. WRITES means the only writer; APPROVES means the
only authority that can make the output durable.

| part | INPUT | OUTPUT | READS | WRITES | EDITS | APPROVES |
|---|---|---|---|---|---|---|
| builders (loader/parser/translator) | source extracts, SQL, TMDL | truth-store layers (KG1/KG2a/KG2b) | sources + own layer's inputs | its ONE layer | replaces whole (quantum), never patches | contract validators (mechanical) |
| truth store | builder writes | nodes/edges/speech to any reader | — | — (written only by builders) | never in place | — |
| interpreter (model seat) | ONE question string (never history) | PROPOSAL {mentions, expansions, steering hint} — typed, validated, expiring | nothing | nothing | nothing | the human (via confirm) or discard |
| matcher | any string | scored match set over speech (exact tiers → semantic; facets; floor, no cliffs) | truth store speech + memory vocabulary | nothing | nothing | thresholds = registry data |
| engine | matched sets + edges | answer subgraph (filter ∩ traverse · neighborhood), caps visible | truth store edges | nothing | nothing | — |
| renderer | answer subgraph | words via ratified grammar + typed context set | truth store | nothing | nothing | grammar version = law |
| smoother (model seat, gated) | rendered text | polished text, facts unchanged | nothing | nothing | nothing | diff-gate; floor ships without it |
| envelope | any outcome | {outcome, payload, evidence+scores, trace, context set, coverage} | — | — | — | shape is law, all outcomes equal |
| session (the table) | context sets per round | context for anaphors; snapshot on confirm | — | conversation-scoped state | replaced per answer | — |
| memory (the ledger / USER TREE) | confirmed proposals, usage | interpretations, vocabulary, affinity — deterministic on replay | — | HUMAN ACTS ONLY (confirm/revoke); usage events append | never edited — superseded by new events | the user (personal) / steward (shared) |
| surface | envelope | transcript round, confirm affordance, buttons, clickable things, visible trace | — | nothing | — | the human presses; models never press |

► RULED (Sunny, 2026-09-07, the ledger-miss walkthrough): ALL USER
DECISIONS ARE STORED IN THE USER TREE — PERSISTENTLY. Confirmations,
clarify-picks, blessings, revocations survive console restarts; the
walkthrough exposed that KG3 events live in memory only (the 5:11pm
confirmations died with that console). Design shape: an append-only
GOVERNANCE JOURNAL per estate (human acts as events, supersede
never delete — the KG3 posture on disk), replayed at boot; each
user's TREE is a view over it rooted at their person node (step 3's
trunk). The ledger's "deterministic forever" becomes literally
forever. Build item: suite-first, queued with the find-package.

**The user's own tree (Sunny's proposal, adopted into the draft):**
memory is not a flat ledger — it is a TREE per user: user node →
confirmed vocabulary → confirmed interpretations → reports/queries
actually used (affinity, usage-weighted). Personal trees live beside
the shared estate tree; promotion personal → shared is a steward
blessing (matches the standing personal+enterprise truth-layers
philosophy and the usage-weighted flywheel). Session context sets
snapshot INTO the user's tree on confirmation — so "what I looked at
and blessed" is itself traversable, searchable meaning.

---

## THE DERIVED UI (2026-09-07, from the nine dug laws — for Sunny's pass)

Nothing here is invented; every element cites the ruling that
forces it. Three surfaces: THE CONVERSATION (everyone), THE TREE
(mine), THE QUEUE (stewards/admins).

### The conversation surface

```
┌──────────────────────────────────────────────────────┬───────────────┐
│ AIVIA · sepsis — 28 files · 90 tables · loaded 09-05 │  THE TABLE    │
│ ⚠ banner only when degraded: "interpreter down —     │  (L5-D3)      │
│    names, clicks, and confirmed questions work"      │ ▼ this round  │
├──────────────────────────────────────────────────────┤  · #Base_Pop  │
│                                                      │  · 42 scopes… │
│  ROUND N  (appends; prior rounds stay)               │ ▸ round N-1   │
│  ┌────────────────────────────────────────────────┐  │ ▸ round N-2   │
│  │ you: what business logic is in ED Sepsis       │  │  [clear the   │
│  ├────────────────────────────────────────────────┤  │   table]      │
│  │ Answering for USP_ED_SEPSIS · also matched:    │  ├───────────────┤
│  │ USP_RPTS_ED_Sepsis — switch        (L3-D1)     │  │  MY TREE ▸    │
│  │ ✓ I read "business logic" as conditions —      │  │  (L5-D4,      │
│  │   confirm · correct                (L7-D2)     │  │   L7-D1)      │
│  │                                                │  │               │
│  │ 12 conditions in USP_ED_SEPSIS:                │  └───────────────┘
│  │ · The BPA locator is 900130001 [→node] (L1-D2) │
│  │ · The date arrived is between… [→node]         │
│  │   … each line clickable = its node             │
│  │                                                │
│  │ changed since you asked Sep 5: +2   (L8-D4)    │
│  │ views: card lineage filters readers  (L4-D4)   │
│  ├────────────────────────────────────────────────┤
│  │ searched: "ED Sepsis" — exact name: no ·       │
│  │ by meaning: 2 files (best 0.78 via name card) ·│
│  │ "business logic" → conditions (confirmed 09-07)│
│  │ · no expansions proposed · showing conditions —│
│  │ you named the kind        ▸ full evidence      │
│  │ (L6-D1/D2/D3: caption above, work here,        │
│  │  evidence one click deeper)                    │
│  └────────────────────────────────────────────────┘
│                                                      │
├──────────────────────────────────────────────────────┤
│ [ ask anything…                                    ] │  ← clears, stays
└──────────────────────────────────────────────────────┘
```

**The empty state** is the ESTATE CARD (L9-D2): the census as a
welcome — what's here, the kinds, top topics, honest gap numbers —
plus three example asks drawn from the estate's own biggest topics.

**The anatomy of a round** (top to bottom, laws cited):
1. Your words, kept verbatim (display memory only — L2).
2. The ASSUMPTION line when provisional (L3-D1): what was assumed,
   runners-up one click away.
3. The INLINE CONFIRM (L7-D2): non-blocking; confirming writes the
   boundary artifact to my tree (L2-D3); ignoring costs nothing.
4. The CAPTION: the answer as clickable fact-lines (L1-D2) — every
   line is its node; clicking lands it on the table (L5-D2).
5. The CHANGE CAPTION when a confirmed question moved (L8-D4).
6. VIEWS as buttons (L4-D4) — pressed, never model-chosen; a hint
   may preselect visibly.
7. THE WORK line (L6): plain process words rendered from trace
   data; expands to full evidence. Contains the display-set
   rationale ("you named the kind" — L4-D1's user-words provenance).

**The other round shapes:**
- CLARIFY (L3-D2): deduped rows grouped by kind, score + one line
  of speech each, capped visibly; my pick is recorded and accretes
  (L5-D2). If my referent isn't listed, my next typing counts the
  miss (L3-D3) — silently, no extra UI.
- ABSENCE (L9-D4): the zero + searched universe ("searched all 28
  files") + nearest true things + the NEXT ACT for my role (mint a
  term / flag to steward / load an extract). A door, never a wall.
- DEGRADED (L8-D3): the banner says what STILL WORKS; confirmed
  questions keep answering without any model.

**The table** (right rail, L5): stacked rounds, top expanded;
every item re-invocable; kind-qualified anaphors reach down;
[clear the table] is an explicit act. I can see what "those" will
mean before I type it.

### The tree surface (mine — L5-D4, L7)

My accumulated relationship with the estate, owner-only (L9-D4
scope): things I viewed (affinity), questions I confirmed (the
meaning-book — phrasings attached to meanings, L2-D1), vocabulary
I blessed. Each blessing shows its anchor state (intact/orphaned —
L7-D4) and offers REVOKE with blast radius (L7-D3). "The report I
was looking at yesterday" is a query here, not an anaphor.

### The queue surface (stewards/admins — L7-D1, L9-D4)

The promotion queue: mappings N users confirmed (usage-weighted),
one blessing promotes to estate-shared. The demand ledger:
repeated absence hits ("4 users asked for PBI reports"). The
telemetry proposals: "clarify-miss rate suggests floor 0.22 —
apply?" — a human act on registry data, never self-applied
(L7-D4). Migration console: embedding/interpreter version bumps as
announced rule changes validated by the miss rate (L8-D1/D2).

### What the UI refuses to have (by law)

No intent pickers or query builders (L4). No unmarked model prose
(L1/L2). No spinners hiding seat failures (L8-D3). No dead-end
"no results" (L9-D4). No invisible state — if it affects
resolution, it is on screen (L5-D3, L6-D1). No settings that let
the system tune itself (L7-D4).

## THE MEANING-TEST CONSOLE — the ruled five-step algorithm

*(READ WITH THE ► RIDERS at this section's end — same-day rulings
2026-09-11 superseded parts of the body below: THE MATCHED GRAPH
killed the crown rule and made the minimal connecting subgraph
the FALLBACK, not the default; the label constraint, kind
subsumption, and THE CHOICE STEP were added to step 3. The body
stands as the ruled starting point; the riders are current law.)*
(Sunny, 2026-09-11; the L4 ruling in Design_Graph_Engine.md names
this section as its algorithm. Purpose: MEANING testing of each
ACCEPTED ladder batch — readability, findability, grounding.
Gates verify structure; this console tests meaning; it closes
nothing. The Fabric Data Agent ban stands — it fabricated;
chatbot-testing as such is ruled IN.)

**The algorithm (Sunny's formulation, ruled):**

1. **The user asks an NL question.**
2. **The LLM interprets intention and tokenizes** — extracts
   MEANING UNITS (multi-word phrases stay whole) plus the
   intention shape. The LLM's ONLY seat: it proposes, visibly;
   it never writes queries and never touches answers.
3. **Token vectors search the graph's card index** — name card +
   description card per node (the facet law). Output per token: a
   MATCH SET with scores; thresholds are registry data
   (Grounding_Thresholds); below-threshold = visible candidates,
   never silent "unknown"; a no-match token is a returned fact.
4. **The matches drive a DETERMINISTIC PLANNER that writes a
   GRAPH query covering all matches** (graph, never SQL — SQL
   cannot discover paths). Topology algorithms fit the scenario;
   multiple may coexist; START WITH ONE: the minimal connecting
   subgraph (union of shortest paths across match sets; fewer
   intermediates preferred — the hub-explosion bound). The query
   is an ARTIFACT: rendered in GQL, shown with the answer —
   operations are the product.
5. **Return all relevant results** — the connecting subgraph as
   arranged evidence (nodes with descriptions, edges with keys),
   completeness declared, absence honest (nearest neighbors,
   never invention). Partial-answers law: disconnected match sets
   return honestly with the gap named.

**THE THREE MATCH CLASSES** (the label lesson honored — kinds
ground by meaning, never by word lists):
- INSTANCE match (node id) → an ANCHOR the traversal must touch;
- KIND match (a label's self-description — the _self speech
  rows) → a TYPE CONSTRAINT in the query, never an anchor;
- EDGE-KIND match (joins_to / has_part meanings) → a TRAVERSAL
  CONSTRAINT (which edge types the path may walk).

**What embeds:** everything that SPEAKS in scope — instance
cards (name + description) + kind self-descriptions + edge-kind
meanings. NOT properties as such, NOT edge instances (topology is
the planner's food, not the matcher's). Vectors are an L3
PROJECTION: file cache now (content-keyed), node-row columns at
M12 — the planner is location-blind because matches arrive as
node identities.

**Execution locality (ruled default):** the query EXECUTES
locally over the store; the GQL text is displayed (paste-able
into Fabric). The whole loop moves server-side only when M12
lands vectors on node rows.

**Scoping per ladder:** the console boots from the store-as-built
and additionally scopes its INDEX to the accepted grains under
test; exclusions are COUNTED in the coverage line, never silent.
First target: THE TECHNICAL LAYER (table · column instances;
db/db_schema/table/column kinds; joins_to/has_part edge kinds).

**The pinned battery (test-first):** questions with expected
crowns across the families — findability · meaning readback ·
column search · relationship grounding · absence honesty ·
enumeration · impact — deterministic pipeline parts tested
keyless; the live seats under the live-seat rule. Sunny
gap-checks and blesses the battery; regressions surface
mechanically thereafter. *(Status 2026-09-11: 14 questions —
the 8 drafted + SUNNY'S SIX, hand-tested on the web UI and
pinned; 14/14 live. The six are blessed by use; the drafted 8
pass but still await his explicit word.)*

► RULED (Sunny, 2026-09-11, from the ADT_EVENT rounds): TWO
riders on step 3. (1) THE LABEL CONSTRAINT WIRED: a token that
grounds as a label constrains the other tokens' instance
anchoring to that label — the user's own words pick the grain; a
constraint is a PROPOSAL, never a veto (an empty constrained set
relaxes and reports, the planner's edge-kind law). (2) THE
CHOICE STEP (HITL after matching): every token's runners-up are
OFFERED in the round (top candidates with labels and scores,
visible cap with the counted remainder); a click PINS that
candidate and re-runs the round. A pin is the HUMAN ACT — it is
that token's crown and outranks scores and constraints; a pin
whose candidate left the match set is an honest miss, reported,
never a silent fallback. Picks are steer (the clicks-are-steer
law), keeping the loop: machine proposes → human chooses →
deterministic planner executes → display. Generalized the same
day as THE TURN DEFAULT (see the section after the nine laws):
HITL after every turn is the DEFAULT for all chatbot surfaces.

► RULED (Sunny, 2026-09-11, from the EVENT_ID round — THE
MATCHED GRAPH; supersedes the crown rule): steps 3–5 re-derived.
THE CROWN RULE IS DEAD — "one token, one winner" silently
discarded ¾ of an exact truth (four EVENT_ID columns found, three
dropped), a Law-9 violation dressed as a rule. The law: LET THE
MATCHED GRAPH DRIVE THE QUERY AND THE DELIVERY.
- **SET FORMATION**: a token's match is a SET — exact hits are
  ALL equal citizens; semantic hits form THE BAND (≥ MATCH_SCORE
  and within UNIQUE_MARGIN of the best — registry thresholds,
  nothing new minted). The label constraint applies BEFORE
  banding and stays a proposal, never a veto. A pin replaces the
  token's whole set (the human act).
- **THE KIND'S TWO FACES**: a kind token meets a set of its OWN
  label as a CONSTRAINT (its job is picking the grain); it meets
  a set of ANOTHER label as a CONNECTION — its full population
  joins the projection ("tables" × the EVENT_ID columns).
- **PROJECTION**: light the matched sets on the store; the edges
  that ALREADY EXIST among lit nodes are the answer's skeleton.
- **SHAPE → QUERY (deterministic ladder)**: sets connected in the
  projection → ENUMERATE those connections (the answer predates
  the question); ≥2 sets unconnected and the question connective
  → the minimal connecting subgraph (pathfinding is the FALLBACK
  for missing structure, never the default); one member →
  neighborhood; one set, many members → the list; nothing →
  the honest zero.
- **DELIVERY BY RESULT SHAPE**: rows → a rendered table (visible
  cap, counted remainder); one node → the card; a path → the path
  told; and the CONSERVATION LINE rides along ("4 of 90 tables
  connect; 86 do not") — Law 9 made visible in every enumeration.
Acceptance: "show me all tables that use EVENT_ID" returns
exactly the four carriers (ADT_EVENTS · ED_EVENT_INFO ·
ED_PATIENT_INFO · V_PATIENT_LOCATION_HISTORY) as rows with the
enumerating GQL. RULED same day — THE KIND-SUBSUMPTION RULE
(from measured scores: 'tables' → kind 1.576 vs top
table-instance 1.760, the gap entirely the instances' own label
cards): same-labeled instances outscoring their kind is CIRCULAR
credit — the kind speaks through its members. A kind entry
≥ MATCH_SCORE whose name equals the top instance's label CLAIMS
the token. Phrases stay safe by the same bar (measured: kind
0.307 / rank 2026 for a real phrase — nowhere near).
