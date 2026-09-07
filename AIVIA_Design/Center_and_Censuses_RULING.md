# THE CENTER AND THE THREE CENSUSES — RATIFIED
*(Drafted 2026-09-07 from the live-find series #5/#8/#9/#10 and the
generator finding behind them; RATIFIED 2026-09-07 — Sunny ordered
the landing pass ("update the design doc, and then the other
supporting docs"). Landed: design doc L0 (center law + three
censuses), builders/readings contract amendment, ADR 0080,
registries v1.18.0 (Speech_Sources + Censuses), F10 census family.
R-5 confirmed: the find-#10 "topic law" patch is DEAD, superseded
by this ruling's one build phase.)*

---

## The finding that forces this ruling

Every live find of the testing sessions reduces to one sentence:
**code kept building ad-hoc side-structures instead of reading the
graph.** The ask index composed its own "words" (a second meaning,
beside the twin). The search embedded that sidecar, not the tree.
The file card re-derived file meaning separately from the search
text, so a fix landed in one and missed the other. The kind
vocabulary sat outside the search. Each was locally reasonable;
together they are the disease: **the KGs were the product, but not
the center of the code.**

---

## Piece 1 — THE CENTER LAW

Every line of AIVIA code is exactly one of three things:

1. **A BUILDER** — authors one KG layer, and only its own:
   loader → KG1 · parser → KG2a · translator → KG2b ·
   humans/ledger events → KG3. (Already law: the builder ruling.)
2. **A READING** — consumes the graph and RENDERS. A reading may
   apply a **ratified grammar** (a versioned, total mapping from
   stored facts to text — the floors) but may never AUTHOR: never
   choose, compose, or invent meaning content outside a ratified
   rule. If a reading needs a derived structure (an index, an
   adjacency, an embedding), that structure is a **verbatim
   projection** of stored properties — a cache of the graph, never
   a second source of it.
3. **A FLOW** — sequences builders and readings. Holds no meaning.

**The authoring/rendering line, precisely:** rendering = applying a
versioned rule to stored facts (compose_floor over the twin).
Authoring = deciding what something means (writing a description,
composing a summary, choosing a meaning slice). Authoring happens
only in builders and only into their layer. The cause-1 corpse
pinned: `file_words()` authored a file's search meaning inside a
reading, at point of use — the card and the vector then drifted
because the meaning had no single home.

**Corollary — composition is the translator's job.** A composite
node's meaning composes from its children (the composed-meaning
amendment, already ratified). Therefore a FILE's composed meaning
(what the report is about, up-composed from its scopes' sources and
their KG1 steward words) is **built and stored in the twin** by the
translator — not assembled at search time. The change quanta then
apply for free: a file's stored meaning re-derives only when its
parts change.

**Mechanical enforcement (the Echo-Law build):** a census test per
derived structure asserting verbatim-ness — every text the ask
index carries equals a stored property or a versioned-grammar
rendering of stored properties; composition logic in readings = 0.
A new sidecar that authors is a CI failure, not a live find.

---

## Piece 2 — SPEECH: every node kind declares what it speaks

Sunny's mind model, adopted as the design sentence:

> *A tree per file; typed nodes; each node carries its description;
> search runs against those properties while traversing.*

To make that total, the kind library (registry) gains one column
per node kind: **SPEECH — the stored property this kind speaks for
search and cards.**

| kind | speech source (stored, one home) |
|---|---|
| table, column | KG1 steward description (words as loaded) |
| scope (selection) | its floor lead + composition (grammar render of the twin) |
| file | its **composed meaning** in the twin (Piece 1 corollary): delivery lead + base compositions + read-tables' steward words, stored |
| condition (predicate) | its voiced phrase (grammar render, stored on the twin node) |
| parameter | its voiced phrase |
| term (KG3) | its definition |
| drift name | the standing drift sentence |
| kind itself | its registry definition — **kinds are searchable nodes** ("reports"/"procs"/"dashboards" ground to kind:file by meaning, not by a fixed word list) |
| operational statements | RULED-MUTE (reason: no reader-facing meaning) |

A node whose speech source is empty is a **counted documentation
gap** (existing posture, now uniform). Missing speech is honest,
never silent.

---

## Piece 3 — THE THREE CENSUSES (the questions, as conservation laws)

The three questions become three standing equations, same shape as
`voiced ⊎ counted == total`:

**Census 1 — REACHABILITY: is everything reachable?**
Every stored node is reachable from the estate root by typed edges,
or its unreachability is ruled with a reason.
`reachable ⊎ ruled-isolated == total nodes.`
This is the L0 lineage guarantee ("never silently absent") finally
given its census. *Honest status today: UNVERIFIED in aivia — the
adjacency covers contains/reads/cites/defines/sighted; parameters,
terms, and twin interior nodes have never been census-checked.*

**Census 2 — SPEECH: does everything speak?**
Every node's kind declares a speech source (Piece 2); every node
either has non-empty speech or is counted (gap) or ruled-mute.
`speaks ⊎ counted-gap ⊎ ruled-mute == total nodes.`
*Honest status today: FAILS — files spoke a self-referential slice
(the cause-1 corpse); conditions, parameters, and kinds speak
nothing.*

**Census 3 — SEARCHABILITY: is every speech searchable?**
Everything that speaks is in the search index with its speech
VERBATIM (plus its name tokens, word-grain); embeddings are a
content-keyed cache of speech.
`searchable ⊎ ruled-silent == everything that speaks.`
And search matches **facets** — each node's speech is its own
facet; a file is found through its parts' facets with the score
rolling up the tree and PROVENANCE kept ("matched via its
condition: the sepsis screening alert", 0.80 vs 0.57 blended — the
probe of 2026-09-07). One-blob-per-node blending is the flattening
disease and is banned.
*Honest status today: FAILS — search runs over the sidecar's
partial flat list; conditions (the best-scoring facets) are not in
it; kinds are not in it.*

Each census is a standing test AND a report bucket in the gap-check
report — the numbers Sunny reads, not just CI.

---

## Piece 4 — THE LANDING MAP (where does each concern live?)

The "what lands where" question, answered as a table. Every concern
from the live-find series has exactly one home:

| concern | home | why |
|---|---|---|
| steward descriptions | KG1 (loader) | declared truth |
| composed meaning (scope, file) | KG2b twin (translator, stored) | composition is building, not reading |
| floors / cards / speech rendering | readings via ratified grammar | render, never author |
| acronym & synonym expansions ("ED" → "emergency department", "ER") | proposed by the interpreter per-ask; **confirmed ones land as KG3 terms** | vocabulary is meaning-as-data; the LLM proposes, the human confirms, the ledger remembers |
| kind synonyms ("procs", "dashboards") | same path — kinds are searchable nodes (Piece 2); confirmations land in the registry vocabulary | node types are part of the search |
| embeddings | derived cache of speech, content-keyed (existing stamp law) | regenerable, never truth |
| ask index | verbatim projection of speech + name tokens | a cache of the graph, never a second graph |
| adjacency | verbatim projection of edges | same |
| the search trace (what was searched, expansions, facet hit, score) | the DISPLAY — rendered in every round, always-on for now | plan-confirm-execute-display; suppression later is a toggle, never a removal; the trace is also the audit record |
| context sets (Law 4) | conversation-scoped data + ledger snapshots | already law |
| grounding thresholds | registry data | declared, tunable, never hidden — and never a cliff: below-threshold = HITL candidates with scores, never "unknown" |

**Flows hold none of this.** The ask flow sequences:
GROUND-over-facets → CONNECT → SPEAK → trace-display. The intake
flow sequences builders. That is all a flow is.

---

## Piece 5 — ACCEPTANCE (what the build phase must show, when ratified)

The finds of 2026-09-07 become the standing corpses:

1. "how is reporting/USP_ED_SEPSIS.sql defined" → the file grounds
   deterministically AND its speech carries emergency-department
   meaning (census 2 kills cause 1 at the root).
2. "what reports are about ED" → word-grain name-token match finds
   the ED files deterministically; BED_CONFIG never matches; the
   trace shows the expansions searched.
3. "sepsis screening alerts" → matched via the condition facet with
   provenance (census 3; the 0.80-vs-0.57 probe pinned as a test).
4. "what metrics are about ED" → kind grounds, topic searches
   facets, empty is an honest zero — never NO MATCH while a kind
   grounded.
5. The three census equations hold on the sepsis estate, numbers in
   the gap-check report.

---

## Open register calls for Sunny

- R-1: Ratify the center law (Piece 1) incl. the authoring/rendering
  line and the composition-belongs-to-the-translator corollary?
- R-2: Ratify SPEECH as a kind-library column (Piece 2) and the
  speech table as drafted (esp. kinds-as-searchable-nodes)?
- R-3: Ratify the three censuses as standing tests + report buckets
  (Piece 3)?
- R-4: Ratify the landing map (Piece 4) — notably: expansions as
  KG3 terms; the always-on trace; thresholds-never-cliffs?
- R-5: Sequencing — this ruling's build replaces the pending
  find-#10 patch (the "topic law" is superseded by facet search +
  censuses); confirm the patch is dead and the build is one phase?
