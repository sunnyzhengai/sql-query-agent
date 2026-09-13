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
mechanically thereafter. *(Status 2026-09-11 late: 18 questions
— the original 8, SUNNY'S SIX, and the join-layer four — ALL
BLESSED ("bless them all"): the six by use, the rest by his
word; 18/18 live. The battery carries Sunny's authority in
full.)*

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
enumerating GQL.

► RULED (Sunny, 2026-09-11 — THE SECOND TARGET: the join layer,
M2, per the batch-earns-the-console law): the console's scope
extends to M2's accepted grains.
- **Scopes join the index**: all 44, their FLOORS are the speech
  (verbatim law); the `_self scope` kind card joins so
  "scopes/selections" ground as the kind.
- **Joins are CONNECTIVE STRUCTURE, never indexed**: a join node
  carries its ON text, joinType, and description as EVIDENCE for
  the connections it makes — planner food, not search targets.
- **THE PASS-THROUGH RULE**: a scope and a table are CONNECTED
  when a join links them (scope —has_part→ join
  —left_side/right_side→ table-or-scope). Enumeration and
  pathfinding treat the two hops THROUGH a join as ONE
  connection; the row cites the join's ON meaning ("via join#1:
  EEF.ENCOUNTER_ID = HE.ENCOUNTER_ID"). The `reads` remainder
  (6 edges) stays a direct connection.
- **Conditions stay counted-out until §D** (the standing
  decision holds; their index entries remain visible exclusions).
- **Edge-kind cards for the join layer are DEFERRED with the
  recorded reason** (the Echo-Law deferral form): a user's
  "read" grounding as a `reads` traversal constraint would VETO
  the side-path connections (only 6 of the ~180 scope-table
  links are `reads` edges) — the constraint law must first learn
  pass-through before these words may constrain. Until then
  has_part/joins_to remain the only edge-kind cards.
- **Battery**: a drafted join-layer family lands for Sunny's
  gap-check; his pass pins them (the blessed-by-use path).

► RULED (Sunny, 2026-09-11 night — THE THIRD TARGET: the
condition layer, M3, per the batch-earns-the-console law; this
rider IS the design change that supersedes the §D hold FOR THE
CONSOLE — §D's scoring work itself stays where it was left):
- **The SCOPE-ROOTED condition trees join the index** (the
  WHERE/CASE membership logic): their VOICED phrases are the
  speech — names are mechanical (cond#N), the meaning lives in
  the grammar-voiced phrase. Degenerate conditions stay out,
  COUNTED. The `_self condition` and `_self parameter` kind
  cards join, so "conditions/filters/parameters" ground as
  kinds.
- **JOIN-ROOTED (ON) conditions stay UNINDEXED** — their
  meaning already speaks through the join's evidence line
  (measured: join-key equalities voice vacuously, "the unique
  identifier is the unique identifier" — indexing them would be
  noise wearing a grain's name). They remain connective
  structure.
- **The census-twin condition rows retire from the index as a
  COUNTED exclusion** — the accepted store grains supersede the
  tree-derived census entries (same predicates, older
  representation).
- **Params join the index** (they speak); `uses_param` walks.
- **Adjacency gains**: scope—has_part→condition-root ·
  condition—has_part→condition · condition—resolves_to→
  column-or-param (role-tagged) · join—has_part→condition ·
  uses_param.
- **THE PASS-THROUGH RULE GENERALIZES**: the connective labels
  are {join, condition} — a CHAIN of connective nodes is ONE
  connection; the citation is the phrase of the connective
  NEAREST THE ANCHOR (the leaf that resolves to the column — the
  most specific true thing).
- **New shapes**: "which scopes filter on the arrival date?"
  (enumeration through condition chains) · "what conditions does
  #Base_Pop apply?" (the WHERE bullets in the neighborhood) ·
  "which scopes use @dStartDate?" (impact via uses_param).
- **Battery**: a condition-family lands; blessing per the
  standing path.

RULED same day — THE KIND-SUBSUMPTION RULE
(from measured scores: 'tables' → kind 1.576 vs top
table-instance 1.760, the gap entirely the instances' own label
cards): same-labeled instances outscoring their kind is CIRCULAR
credit — the kind speaks through its members. A kind entry
≥ MATCH_SCORE whose name equals the top instance's label CLAIMS
the token. Phrases stay safe by the same bar (measured: kind
0.307 / rank 2026 for a real phrase — nowhere near).

► RULED (Sunny, 2026-09-12 — THE LIVE-WIRE TOGGLE, demo; from
his question "where is the graph db? is it still faking it?"):
the console's displayed GQL EXECUTES against the SERVED Fabric
graph on demand — the graph answers for itself. The execution-
locality default above STANDS: local execution remains the
answer path until M11/M12; the wire is per-round EVIDENCE laid
beside it, never a replacement.
- **The toggle is Sunny's hand (the capacity law):** OFF at every
  boot; flipped visibly in the UI for the session; every fired
  query is one capacity spend, COUNTED on the round (a visible
  spend line — no silent spends, ever). No default flips it.
- **What fires is the ARTIFACT:** the exact GQL strings the round
  already displays — nothing re-planned, nothing rewritten for
  the wire. If the displayed query weren't the real query, the
  wire would expose it; that is the point.
- **Delivery = the comparison:** Fabric's rows render beside the
  local rows with a per-round conservation line (local N rows ·
  served N rows · MATCH / DIVERGE). A divergence is a FINDING,
  reported never smoothed — the mirror's equality, until now
  proven only at batch gates, becomes checkable per round.
- **The wire is the documented contract** (GQL Query HTTP API,
  public preview): POST /v1/workspaces/{ws}/GraphModels/{gm}/
  executeQuery?preview=true · bearer token (resource
  api.fabric.microsoft.com) · body {"query": …} · typed TABLE
  back; success = status codes 00–03 prefixes, anything else
  renders code + description VERBATIM (the error-contract).
- **Config is Sunny's, never committed:** workspace id + graph
  model id + token ride environment (token alternatively fetched
  from `az account get-access-token` at need); the console NEVER
  stores a token. Unconfigured or unreachable = the toggle shows
  DISABLED with the reason — the seat-down banner law, never a
  silent fallback to local-only.
- **Tests:** deterministic with a scripted transport double (no
  live HTTP in the suite — the doubles law); the live wire fires
  only by Sunny's hand. This surface keeps THE TURN DEFAULT: the
  wire adds evidence to the round, it steals no choice point.

► RULED (Sunny, 2026-09-12 — "please fix these gaps", after the
#AllMeds gap-check) — THE STRUCTURE-WORD CLAIM, superseding the
kind-subsumption rule's label-agreement clause:

In the semantic tier, the STRUCTURE VOCABULARY claims first: a
token whose top-scoring kind or edge-kind entry clears
MATCH_SCORE is claimed by that entry, by ITS OWN score. The old
clause required the kind's name to equal the top instance's
label — which picked the kind by the NOISE instance's label:
'filters' top-matched the column REF_RANGE_TYPE, so kind
`column` claimed the token while kind `condition` (whose
self-speech literally says "filter") stood cleared-but-ignored;
the round then said "constrained to label: column (your word)"
— a word the user never said. The guards, unchanged: exact-name
instance hits outrank every claim (a user who types a name
means the thing); the choice step still offers the instance
runners-up; a pin outranks any claim (THE TURN DEFAULT). The
same-label circular-credit case ('tables' vs table instances,
the rule's founding measurement) falls out as a corollary — the
kind clears the bar and claims regardless of who supplied the
label credit.

► RULED (same breath — THE RELATION-WORD SEAT, prompt 3.1.0;
the 2026-09-12 morning park is LIFTED by the same word):

Relation words are referring words. The Interpreter keeps them
as mentions and marks them in a caged `relations` field — a
ROLE classification exactly like reference-roles (L4-D3), never
a type target (the kinds-field ban stands). A relation-marked
token grounds ONLY against structure entries (edge-kinds, then
kinds): it never instance-anchors and never joins anchor sets —
a relation word whose structure entries clear nothing is a
COUNTED no-claim, reported on the round, steering nothing.
Containment words reach `has_part` BY MEANING: edge kinds gain
honest self-speech (Speech_Sources `_edge` rows — Shape_Ledger
engineering Notes stop serving as speech). The `reads`
edge-kind card stays DEFERRED with its recorded reason (a
'read' constraint would veto join-side travel); the traversal
vocabulary is has_part + joins_to until that deferral is
re-ruled.

THE COUNTED REMAINDER rides along (the landing condition from
the live-fire root-cause note): when an edge-kind constraint
confines an enumeration, the walk also counts what the
constraint excluded — "N <label>(s) connect only outside the
constrained edge kind(s) — counted, not lost." A constraint
narrows visibly or not at all.

► RULED (Sunny, 2026-09-12 evening — "all 3, go", from his
#AllMeds table verdict "this is not meaningful") — THE MEANING
ROWS, three laws in one breath:

**1. STRUCTURE NEVER ROWS.** A condition enumeration delivers
MEANINGS, not tree anatomy. By the `kind` property already on
every node: composite kinds (AND/OR) never row — their
conjunction semantics voice as the FRAME of the delivered list
("all of the delivered parts must hold together (…::cond#4
joins them with AND)"); a NOT rows as ONE folded meaning and
its operand never rows separately; degenerates (1=1) never row;
anything reached THROUGH a join — composite or not — is the
join's own structure, never a filter row (the ON ruling carried
to delivery; class order matters). Every excluded class is
COUNTED on the round ("not rows, counted: 3 join structure · 1
frame · 1 degenerate · 1 folded into NOT"). The store keeps
every grain — the gates still see anatomy; only the ANSWER
speaks meanings. Why cond#4 ever rowed is recorded plainly: the
delivery equated "condition node" with "answer row"; nothing
had ever ruled the gap between a grain in the store and a row
in an answer.

**2. THE NEAR-FIRST DEFAULT.** When an OWNER grain (scope ·
file · statement) anchors a question about its OWNED logic
(condition · join · param · derived_column), the default reach
is the anchor's own subtree (the ownership edges: has_part ·
uses_param · cites); connections beyond it are COUNTED with the
wider reach ONE CLICK AWAY (reach=wide — a choice point, THE
TURN DEFAULT, never a guess). An explicit relation word
overrides the default in either direction. Entity anchors and
entity populations keep the blessed pass-through unchanged
(scopes-read-table, the EVENT_ID carriers — Sunny's pinned
six stand). This is not intelligence, it is a precedence rule:
near answers first, far reach counted, deterministic.

**3. COMPOSITES COMPOSE (Grammar 2.5.0).** NOT folds into its
child — one meaning, one phrase, per-kind negations from the
closed set (NULL_CHECK speaks the positive fact; order
comparisons flip to their opposites; membership/pattern kinds
negate their verb; no ruled negation = the honest wrapper
sentence, never a guess). The condition STORE nodes inherit the
fold. AND/OR keep their structural sentence BECAUSE they frame
and never row. The LLM stays where the English ladder put it —
compression where composition is LARGE; a four-part WHERE is
render territory. (Grammar_Floor v2.5.0 records the rules and
the caught 2.4.0 version-constant drift.)

The acceptance for all three is Sunny's own table: "what
filters are in the #AllMeds subquery?" → exactly four rows,
each a filter speaking its phrase (taken time has a recorded
value · is before the ED departure · route is 11 · MAR action
one of 16 codes), framed by the AND, everything else counted
(test_condition_tree_delivers_whole).

**4. THE MEANING CARD DEFAULT (Sunny, 2026-09-13: "the table
question came back with too much information. can we make
table answers like the column answers?").** When the question
NAMES the asked grain with a kind word ("what does the
ADT_EVENT **table** mean") and one instance anchors under that
label, the answer is the anchor's OWN meaning row — the same
shape the column answer already had — never the neighborhood
dump. The old behavior was a population-size ACCIDENT, not a
ruling: BED_STAY_ID matched two same-named columns and fell
into the many-equal-citizens list (meaning rows); ADT_EVENTS
matched one table and fell into the single-anchor neighborhood
(20 of 106 connections). The discriminator is the kind word's
constraint face: your word named the grain, so the grain's own
meaning IS the answer; the neighborhood stays ONE ASK AWAY
(the bare-name question — "#ADT", "ADT_EVENTS" — keeps its
neighborhood card, unchanged). Same law as near-first: the
wide view is a choice, never the default.
