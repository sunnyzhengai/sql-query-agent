# ADR 0080 — The center and the three censuses: code orbits the graph; reachable, speaking, searchable

**Status:** ACCEPTED 2026-09-07 — drafted from the live-find series
(#5/#8/#9/#10) after Sunny fired the generator clause ("are we
making ad hoc patches again?"), ratified via the landing order.
**Component:** architecture. **Supersedes** the pending find-#10
"topic law" patch (dead — its cases fall out of facet search + the
censuses). Full ruling text: `AIVIA_Design/Center_and_Censuses_
RULING.md`; design-doc landings in L0 and the builders/readings
contract.

## The generator this kills

Every live find of the testing sessions was one event: **code built
an ad-hoc side-structure instead of reading the graph.** The ask
index authored its own "words" beside the twin; search embedded
that sidecar, not the tree; the card and the search text re-derived
file meaning independently and drifted (the cause-1 corpse: a fix
landed in one, missed the other); the kind vocabulary sat outside
the search. The KGs were the product but not the center of the
code. Sunny's ruling closes the class: **code either consumes the
KG or produces/edits the KG — nothing else.**

## The center law

Every line of code is one of exactly three things:

1. **BUILDER** — authors one KG layer, only its own (standing law).
2. **READING** — renders stored facts via a ratified versioned
   grammar; may cache only as a **verbatim projection** of stored
   properties. Never authors.
3. **FLOW** — sequences builders and readings; holds no meaning.

The authoring/rendering line: *authoring* = deciding what something
means (a description, a summary, a meaning slice) — builders only,
into their layer. *Rendering* = applying a ratified rule to stored
facts. Corollary: **composition is the translator's job** — a
composite node's meaning (a file's up-composed subject) is built
and stored in the twin, never assembled at point of use; change
quanta then apply for free. Enforcement: a census per derived
structure (projection text == stored property or grammar rendering;
reading-side composition logic == 0).

## The three censuses

Sunny's three questions, as conservation laws (the voiced ⊎ counted
shape):

1. **REACHABILITY** — `reachable ⊎ ruled-isolated == total nodes`.
   The L0 lineage guarantee given its standing census. Status at
   ratification: UNVERIFIED in aivia (parameters, terms, twin
   interiors never checked).
2. **SPEECH** — every node kind declares its spoken property in the
   registry (`Speech_Sources`); `speaks ⊎ counted-gap ⊎ ruled-mute
   == total`. Kinds themselves speak and are searchable nodes.
   Status: FAILS (files spoke a self-referential slice; conditions,
   parameters, kinds speak nothing).
3. **SEARCHABILITY** — `searchable ⊎ ruled-silent == everything
   that speaks`; speech is indexed VERBATIM plus word-grain name
   tokens; embeddings are a content-keyed cache of speech; search
   matches **facets** with scores rolling up the tree and
   provenance kept ("matched via its condition", 0.80 vs 0.57
   blended — the 2026-09-07 probe). Blending is banned. Status:
   FAILS (partial flat sidecar; conditions and kinds absent).

Each census is a standing test AND a gap-check report bucket.

## Riders (all ratified with the ruling)

- **Thresholds are never cliffs**: below-threshold = HITL
  candidates with visible scores, never "unknown". Grounding
  thresholds stay registry data.
- **The trace displays**: every round shows mentions, expansions,
  facet hit, score — plan-confirm-execute-display applied to
  search. Always-on for now; suppression later is a toggle, never
  a removal. The trace is the audit record of what was searched.
- **Expansions are data**: the interpreter proposes acronym/synonym
  expansions ("ED" → "emergency department", "ER"; "procs" →
  kind:file) as extra search strings only — never facts; a
  confirmed expansion lands as a KG3 term / registry vocabulary
  row. The LLM proposes, the human confirms, the ledger remembers.
- **The landing map** (ruling piece 4) fixes one home per concern;
  flows hold none of them.

## Acceptance (the standing corpses for the build phase)

1. "how is reporting/USP_ED_SEPSIS.sql defined" — grounds
   deterministically; the file's stored speech carries
   emergency-department meaning.
2. "what reports are about ED" — word-grain name tokens find the
   ED files deterministically; BED_CONFIG never matches; the trace
   shows what was searched.
3. "sepsis screening alerts" — matched via the condition facet,
   provenance shown (the 0.80-vs-0.57 probe pinned).
4. "what metrics are about ED" — kind grounds, topic searches
   facets, empty answers as an honest zero; NO MATCH is legal only
   when nothing grounds.
5. The three census equations hold on the sepsis estate, numbers
   in the gap-check report.

## Consequences

The build is ONE phase (translator stores composed file meaning;
speech column; facet index as verbatim projection; census tests +
report buckets; trace display), replacing the per-find patch
stream. A question shape with no covering law becomes a CI failure,
not a live find. Registries v1.18.0 carry `Speech_Sources` and the
census declarations.
