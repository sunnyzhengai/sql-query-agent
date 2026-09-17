# Audit — Documentation Review (2026-09-09)

**Status: EXECUTED 2026-09-09.** (Header line added 2026-09-17,
audit CI-C3.)

*(Executed 2026-09-09: naming ruled, fixes 1-6 landed — file names below are the BEFORE state this audit found.)*

*Sunny's charge: (1) is the graph-engine design complete? (2) is the
folder's naming consistent? (3) is there a built-vs-queue checklist?
Trigger: the file-description gap — a thing believed built that never
was. This audit answers all three and names every fix. No code moved.*

## 1. Is the graph-engine design complete?

**The spine is complete and strong.** `AIVIA Design Document.md`
carries: the L0 sentence, the three-layer graph with the KG2a/KG2b
twin, the builders/readings law, the center law, the 12-equation
integrity battery, the flows, hardening passes, ratified MVP scope,
and the design-to-code protocol. A reader can derive the ENGINE from
it.

**Three real gaps:**

**GAP 1 — the speech-CONTENT layer is not designed (the generator of
the file-description finding).** Speech_Sources declares WHICH stored
property each label speaks; no section says what that property's
content SHOULD BE. For files, the composed structural voicing filled
the hole — 4,600-character lineage walls passed the speech census
because the census counts non-empty, not meaningful. The Scribe seat
has a rights row ("drafts descriptions/definitions, curation time,
draft + basis stamp, gate + human approval") but NO design section:
what it drafts, from what evidence, where drafts land (kg3), how a
blessed description becomes the spoken property, and what the speech
card may NOT contain (type words that belong to the label card;
upstream catalog text that belongs to the source nodes). This section
must exist before the speech-card fix is coded.

**GAP 2 — the search design is split across two docs and
self-contradicts.** The main doc's SEARCHABILITY census says scores
"roll UP the tree" (never built as written). The chatbot doc's early
FACET section says "score = the MAX over its cards" while its later
TOTAL-SCORE law says "no max" — the sum. The ruled truth (sum) is
findable only by knowing which line supersedes which. The pending
card-grain MATCH question (this week's real-physics finding) is not
yet in any doc — correctly, since it awaits ruling — but when ruled
it must land in ONE place.

**GAP 3 — no declared boundary between the two design documents.**
Which doc owns search? Speech? The seats? Today: the engine doc owns
censuses that constrain search; the chatbot doc owns the search that
must satisfy them. Nothing says so.

## 2. Is the naming convention consistent?

No. Five inconsistency classes:

| class | offenders |
|---|---|
| spaces vs underscores | `AIVIA Design Document.md`, `AIVIA Design Document Chatbot.md` — the only two space-named files |
| status in the FILENAME | `*_DRAFT` on 10 xlsx + `Slice_Plan_DRAFT.md` + `Port_Manifest_DRAFT.md`; the no-version-suffix law's cousin — status belongs in the doc header, filenames stay stable |
| stale status claims | Slice Plan and Port Manifest still say DRAFT/"for ratification" — the slices SHIPPED 09-06; registries/README.md says "NOT yet ratified, every stamp false" — all seven JSONs say `ratified: true` |
| type markers mixed | prefix (`Audit_`) vs suffix (`_RULING`, `_Manifest`) vs none (`Floor_Grammar`) |
| no index | `docs/` has INDEX.md; AIVIA_Design has none — nothing says which of four plan/manifest docs is CURRENT |

## 3. Is there a built-vs-queue checklist?

The discipline exists — and has drifted. TWO claims ledgers run in
parallel: `Chatbot_Build_Manifest.md` (39 clauses, statuses with
evidence — good law) and `Search_Rebuild_Manifest.md` (17 gaps +
step J). The chatbot manifest was not updated after the search
rebuild: its claim #1 still cites "max-over-cards" as BUILT (dead —
superseded by the total-score law), and its OPEN/PARTIAL rows
(10, 12, 17, 23, 28, 31, 35) have no pointer to where they now
live. Plus two executed plans still marked DRAFT. Four queue-shaped
docs, no single truth.

**Honest-deferral check (the "what else did I think was built"
question):** the recorded DEFERREDs are clean — Smoother, tree/queue
surfaces, revoke UI, lexical scorer, PBI-TMDL parser all carry
reasons. The file-description gap hid precisely because it was in NO
ledger: it fell between the speech census (counts presence) and the
Scribe row (a seat named but never scoped as a claim). Rule to draw:
**every seat in the rights table must appear in the build ledger as
a claim** — a named seat with no claim row is an unbuilt-build
waiting to be believed.

## The fixes (proposed order, each needing only Sunny's go)

1. **Naming law** (one ruling): `Type_Name.md`, types = `Design_`,
   `Ruling_`, `Manifest_`, `Audit_`, `Grammar_`, registry sources
   keep `L*_`; status lives in the header line, never the filename.
   Renames: the two space-named docs → `Design_Graph_Engine.md`,
   `Design_Chatbot.md`; `*_RULING` → `Ruling_*`; drop `_DRAFT`
   everywhere; executed plans stamped EXECUTED in their headers.
2. **One build ledger**: merge the two manifests' live rows into
   `Manifest_Build.md` (sections per workstream, the 39+17 claims
   reconciled, stale claim #1 corrected to the total-score law);
   the superseded files become header-stamped archives or die.
3. **Stale-claims sweep**: registries/README ratification line;
   DRAFT headers; chatbot-manifest rows that the search rebuild
   changed.
4. **The missing design section** (GAP 1): "The Speech Contract" —
   what each label's spoken property must contain (aboutness, this
   node's own meaning only), the two bans (type words, borrowed
   source catalog text), and the Scribe pipeline design
   (draft → attribute → bless → speak), written BEFORE the
   speech-card code fix resumes.
5. **Boundary + contradiction pass** (GAPs 2, 3): each design doc
   opens with an ownership line; the superseded MAX sentence gets
   its dated SUPERSEDED block; searchability census wording aligned
   to cards.
6. **Index**: `AIVIA_Design/INDEX.md` — one line per file, its
   type, its status, its owner.
