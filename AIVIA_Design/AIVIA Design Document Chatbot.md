# AIVIA Design Document — Chatbot

*(Born 2026-09-07 from Sunny's first-principles reset: "go back to
first principles, design the user interface/search/chatbot from
scratch." This is the chatbot's design document — companion to
"AIVIA Design Document.md". Items marked ► RULED are Sunny-ratified
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
search score = the MAX over its cards; the answer names WHICH card
matched (provenance); a shared card (a source table's description)
embeds ONCE and is pointed at, never copied. The deciding evidence
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
| THE SCRIBE | drafts descriptions/definitions | curation time | graph facts + source evidence | DRAFT text w/ basis stamp | write ONLY through gate + human approval (door 3); never at ask time |
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

**Dig questions.** Should the LLM mark reference-mentions instead
of a word list? Multi-answer context (the table holds results of
several rounds) — how far back does "those" reach?

## Law 6 — The work is shown

**Statement.** What was searched, what matched, at what score,
what was excluded, what was cut — visible in every answer. The
process is the product; the answer is a caption.

**Implies.** The trace is UI, not log. Suppression is a display
toggle, never a removal. The trace doubles as the audit record.

**Today.** Trace line ships in every round (0080). It is terse —
one line — and does not yet show expansions-not-proposed, facets
checked, or cut candidates.

**Dig questions.** What does the FULL work-shown surface look like
without drowning the answer? Progressive disclosure (caption →
expandable work)?

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

**Dig questions.** Confirmation fatigue — when does asking become
noise? Do confirmations generalize (confirming "ED"="emergency
department" once: does it apply estate-wide, per-user, per-team)?
Who may revoke?

## Law 8 — Consistency is part of honesty

**Statement.** Same question + same truth = same answer; a changed
answer traces to changed truth, never model weather. Failures
degrade to a smaller honest capability, never a fake.

**Implies.** Interpretations cached, answers never; deterministic
tiers immune to model outage; every nondeterministic seat is
bounded, bannered, counted.

**Today.** Built (ledger replay, seat-failure law, change quanta).

**Dig questions.** Embedding-model version bumps change semantic
rankings — is that "changed truth" (announce it?) or weather
(pin the model?)?

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

**Dig questions.** How does the user learn the BOUNDARY of the
store ("we only know the sepsis estate") without asking? Should
every answer carry its coverage statement?

---

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

**The user's own tree (Sunny's proposal, adopted into the draft):**
memory is not a flat ledger — it is a TREE per user: user node →
confirmed vocabulary → confirmed interpretations → reports/queries
actually used (affinity, usage-weighted). Personal trees live beside
the shared estate tree; promotion personal → shared is a steward
blessing (matches the standing personal+enterprise truth-layers
philosophy and the usage-weighted flywheel). Session context sets
snapshot INTO the user's tree on confirmation — so "what I looked at
and blessed" is itself traversable, searchable meaning.
