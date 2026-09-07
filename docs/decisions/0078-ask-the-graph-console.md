# ADR 0078 — The ask-the-graph console: free questions, typed paths, self-answering nodes

**Status:** ACCEPTED 2026-09-06 — Sunny's goal statement ("through the
web UI... ask questions about anything... without pre-defining answer
shapes"), designed and built same session. **Component:**
architecture. **Depends on:** ADR 0077 (the twin — the reason answer
shapes are unnecessary).

## Decision

A web console over the aivia store that answers free-text questions
about the ESTATE (columns, tables, scopes, files, terms, concepts,
drift names) by deterministic graph traversal — the ask-the-GRAPH
surface. It is NOT the deferred inward flow: no matching of data
questions to estate logic, no generation, no open chat (the tier
lock stands).

## The four laws it builds on (all ratified; none new)

1. **No answer shapes** — because translation is TOTAL (ADR 0077):
   any node renders its own answer from its meaning content, its
   policy-walked floor, its lineage edges, and — where something is
   unsaid — the gap taxonomy's named reason. The answer to any
   question is a rendered graph neighborhood, never a template.
2. **Typed paths** (spec Group E): the question side is a CLOSED
   operation set — lookup · lineage · filters_on · who_reads ·
   define · gaps. The path space is data, enumerable, replayable.
   An LLM seat may PARSE a question into (op, entity) — never
   compose an answer (axm:M5, parse-never-generate); v1 ships the
   deterministic parser and the model seat stays a pluggable hook,
   validated against the closed set (an unknown op or entity from
   the model is refused, and the deterministic parse stands).
3. **The search law** (twin-graph ruling 3d): the index covers
   resolved entities AND unresolved names — a question about a
   drift column returns the finding, never silence.
4. **The usage ledger** (register H5): every ask lands a usage
   event — action `asked`, outcome matched|ambiguous|no-match,
   `about` only on match, question text as payload POST phi-gate.
   The console is the ask surface, the single writer of usage
   (writer census). No-match events are the demand lens's material.

## Outcome semantics (honest, three-valued)

- **matched** — one entity; the op renders its answer.
- **ambiguous** — candidates listed with kinds and words; the human
  picks (never auto-resolved).
- **no-match** — said plainly, counted, with nearest names offered.

## Pieces

- `aivia/lenses/ask_index.py` — the entity index READING (names +
  folded forms + steward words, per entity kind; drift names from
  the resolution census). Named, versioned, writes nothing.
- `aivia/flows/ask.py` — parse (deterministic keyword grammar) →
  op dispatch → deterministic render from meanings/floors → usage
  event via kg3 lifecycle.
- `aivia/console.py` — stdlib HTTP server, localhost, one page:
  search box, rendered answers. `python3.11 -m aivia.console
  <estate>` builds the estate store and serves.
- Registry v1.8.0: `Ask_Console` sheet (the closed op set as law)
  + the ask-index reading in the reclassification.
- `AIVIA_Product/fixtures/F9_ask/cases.json` — answer keys authored
  before the build (the F-series discipline).

## Relations

0077 (the twin; total translation is the enabling fact) · 0063 tier
lock (no open chat; artifacts land, chat doesn't) · H5 (usage) ·
Group E (ask-time determinism) · the no-Fabric-agent validation rule
(the web UI is the sanctioned test surface).
