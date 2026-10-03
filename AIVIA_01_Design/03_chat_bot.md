03_chat_bot.md

Design description:
- The chatbot is the interface where technical users ask questions in
  natural language; the bot parses the question, searches the phase 02
  dictionary graph, and returns high-fidelity technical answers with the
  user confirming intent at every ambiguous step.
- Plan - confirm - execute - display. The user's confirmed selections ARE
  the plan; the answer is a record of what was confirmed, never more.
- This phase supersedes the phase 02 L06 chat. The phase 02 graph engine
  (sheets, graph build, scoring) is the foundation this phase calls; the
  question-side pipeline and the page are this phase's build. The phase
  02 traversal code is NOT called here (decision 4).
- Future phases stay unnamed and unnumbered until we reach them.

The ten decisions (ruled 2026-09-29/30):

1. Who the user is — technical; speaks table/column/join language.
   - The search targets the technical layer and returns high-fidelity
     technical terms by their stored names, texts and embeddings.
   - The search never interprets the semantics of EMR assets. It FINDS
     stored things; meaning-making is not this layer's job.

2. How intent is resolved — LLM segmentation + data classification +
   user confirmation.
   - The LLM's ONLY jobs: segment the question into meaning-bearing
     tokens, tag keywords from the technical terms list, and associate
     keywords with the tokens they modify. The LLM never decides whether
     a token is a name or a value — the data decides.
   - Token outcomes: technical keyword | technical name | value |
     non-meaningful (catch-all). Descriptions are never an outcome —
     they are a search pathway; a description hit resolves to the name
     of the object that owns the description.
   - Three search mechanisms, descending fidelity, funnel stops at the
     first lane with hits:
       lane 1 LEXICAL — exact match against keywords / names / values.
         "Exact" folds case and underscore/space ("pat enc hsp" ->
         PAT_ENC_HSP, "department id" -> DEPARTMENT_ID).
       lane 2 ABSTRACT — lexical match against the curated
         abstract/synonym lists: keywords (the terms file's synonym
         column) and names (the generated abstract list, L03 below).
         Values have NO abstract lane — lanes 1 and 3 cover them; an
         exception requires a ruled row, like the CLARITY category list.
       lane 3 EMBEDDING — the token is embedded (one batched call for
         all lane-3 tokens) and searched against ALL stored embeddings:
         table/column names and descriptions, value meanings. Hits
         resolve to their owning name or value.
   - Every match names its mechanism — lexical / abstract / embedding —
     the way every edge names its kind. Fidelity provenance decides how
     much confirmation a match needs.
   - A token that is unknown or ambiguous is shown to the user for
     confirmation — never assumed, never skipped. Exact-match ambiguity
     is normal by construction (DEPARTMENT_ID exact-matches ten
     columns): shown grouped by table.
   - The technical terms list: AIVIA_01_Data/03_chat_bot/
     03_chat_technical_terms.md — all node types, edge types, operations
     and their synonyms. Sunny authors; the LLM prompt carries the list
     as data and nothing else (no hardcoded examples; shapes illustrated
     abstractly).

3. Answer semantics — STRICT. The answer is the stored detail of the
   confirmed items, nothing more. Filter captions are shown at choice
   time, on the result rows, so the user decides with full information.
   Nothing unconfirmed rides into the answer; every line traces to a
   confirmation. A question that ends with nothing confirmed gets an
   honest empty answer ("nothing confirmed; the candidates shown are
   the closest this dictionary has") — never padded with guesses.

4. NO TRAVERSAL at this layer (ruled 2026-09-30). The chatbot finds
   stored things; it does not pathfind. Joins remain FIRST-CLASS
   searchable and displayable data — technical users ask about joins:
   - A found table's detail lists its join rows verbatim.
   - Two confirmed tables show the join rows directly between them, if
     any — a lookup on the join sheet, no graph machinery.
   - No direct join recorded = the honest answer, with the map (below)
     showing the neighborhood. Multi-hop path answers belong to a
     future phase; the phase 02 traversal code (connect) stays built
     and tested, unused here, waiting for that phase.

   THE GRAPH DISPLAY (ruled 2026-09-30): the page draws the whole
   estate as a MAP; search lights it up; the user's eye does the
   connecting.
   - Everything a search can land on is drawn: table nodes, column
     nodes (as small satellites clustered around their table), join
     edges. Values are properties — they show in the detail panel of
     their column, never as drawn nodes.
   - Parallel joins collapse visually: one drawn line per table pair
     (122 today) with a count badge; clicking the line opens the
     verbatim join rows — columns, direction, FK owner — in the detail
     panel.
   - Rule edges draw dashed, visually apart from solid FK lines, OFF
     by default with a toggle (they all point at DATE_DIMENSION and
     would dominate the picture).
   - Highlight semantics mirror the confirm flow: dim = the estate;
     lit = found by search; bold = confirmed. A found column lights its
     own satellite dot and its owning table.
   - Deterministic server-side layout, computed in plain Python at
     startup, identical every session — same-place-every-time is what
     turns a diagram into a map users build spatial memory of.
   - Version one is pinned small: static layout, pan/zoom, highlight,
     detail panel. Table labels always; column labels only on zoom or
     highlight. No animation, no new packages — hand-rolled SVG in the
     existing page.
   - Click-to-confirm on the map is a LATER enhancement, explicitly
     out of version one.

5. The acceptance parameters are DISPLAY DEFAULTS, not gates — per
   population, for lane-3 (embedding) matches only. Lane 1 and lane 2
   hits bypass the band entirely. The defaults pick what comes
   pre-selected; the user overrides with a click. Calibration tunes
   defaults, so a slightly-off value costs a click, never a wrong
   answer. Parameter values live in the 03 data contract (moved from
   the 02 contract, where they governed the superseded L06 chat).

6. Column hits display grouped by their owning table — a descriptive
   term hitting ten DEPARTMENT_IDs is shown as "these tables carry a
   department pointer", each lighting its satellite dot on the map.
   No anchoring concept exists — nothing traverses.

7. Value hits carry their filter caption as STORED DETAIL — the
   value's code, meaning, and the fact columns that reference its
   category id column, read off the join sheet (e.g.
   PAT_ENC_HSP.ADT_PAT_CLASS_C = 101 "Inpatient"). A confirmed value
   shows its category table's joins in the detail panel — the join the
   filter needs is one of them.
   RULED 2026-09-30 (from the shape 10/11 run): a confirmed TABLE's
   detail includes its value rows when it has any — capped at 50 with
   the total named, never silently truncated. A table without values
   shows an honest empty list (shape 12's guard).

8. What gets recorded — DEFERRED (ruled 2026-09-30): the question
   record (chosen-vs-shown at both confirmation layers) is ruled in
   principle — it is AIVIA telemetry, the flywheel seed and term-asset
   ore, never a user feature — but NOT built in version one. It joins
   a later build by its own ruling; nothing in version one records
   questions.

9. The LLM boundary — phase 02 is embedding-only; the parse LLM lives
   in THIS phase. Model: OpenAI gpt-5-mini, pinned as a code constant
   and named in the contract (same law as EMBEDDING_MODEL). The
   existing OPENAI_API_KEY covers it; no .env change. Per question:
   one chat call (segmentation) + one batched embedding call (lane-3
   tokens). All calls real and paid, never faked.

10. Calibration — Sunny's twelve shapes (moved to
    test_03_chat_bot_data_contract_sunny.md) each gain: expected
    segmentation, expected shown-per-population, expected confirmed
    answer. "Correct" = the right item present and top-ranked IN ITS
    POPULATION, never a global-pool rank. Band defaults calibrate from
    these runs.

Local build steps:

L01: Create the data contract: 03_chat_bot_data_contract.md — the
    pipeline's inputs/outputs, the acceptance defaults (moved from the
    02 contract), the terms and abstract lists' fields, model pins,
    authorship. DONE 2026-09-30.

L02: Create the folder AIVIA_01_Data/03_chat_bot/ and place
    03_chat_technical_terms.md (Sunny's, from the reviewed draft).

L03: The name-abstract list (ruled 2026-09-30): a contract and a python
    script that calls the LLM to write the abstract/synonym list for
    every table and every column (name + stored description in, a short
    abstract and synonyms out; batched paid calls; regeneration law —
    rerun when names/descriptions change, reuse what is unchanged).
    Sunny gap-checks the output; her eye is the acceptance.
    - COMPLETION INTEGRITY: abstract coverage is part of the graph's
      completion check — every table and column has an abstract row, or
      the absence is counted and named. The check fails loudly on
      silent gaps.
    - PORTABILITY (the standing law, per the construct-master clause):
      abstracts of Epic-standard objects are AIVIA's own domain
      knowledge and carry forward to future customers; anything derived
      from a customer's local names or descriptions never travels.
    - The funnel skips an empty lane 2 LOUDLY (startup census) until
      this list lands.

L04: Split the phase 02 engine out of graph_chat.py into
    dictionary_graph.py (load_sheets, build_graph, connect, scoring —
    phase 02 code, tests stay in test_02). Retire the L06 page. The
    chat does NOT call connect; it stays tested and waiting for the
    future phase that writes queries.

L05: Build the chat: the two-step page (segment + search -> user
    confirms -> detail answer), the funnel, mechanism provenance,
    per-population display with defaults, the graph map (decision 4's
    display spec). No question record in version one (decision 8).
    Pseudo code first, Sunny approves, tests red, then code — the
    standing process.

L06: Claude's tests in test_03_chat_bot_data_contract.py; Sunny's
    twelve shapes run against the page by her hand; the HOW TO RUN
    block re-added to her md with the new commands.

Companion edits when this doc lands (Sunny's hand, other files):
- The twelve shapes: 5 reshapes to "show the join rows between PATIENT
  and CLARITY_DEP" (a lookup); 6 reshapes to the honest-no plus the map
  ("no direct join recorded; the map shows both connect to
  CLARITY_ADT"); 7's direction-truthfulness moves into the join-row
  display. Shapes 1-4 and 8-12 stand as written.
- 02_emr_data_dictionary.md L06: body replaced with "superseded — the
  chat is its own phase, 03_chat_bot.md".
- 02 contract: the "search acceptance parameters" section moves here.
- AIVIA_01_Design/Design_Proprietary_Term_Assets.md: the moat philosophy —
  term lists (business, technical, abstracts) are AIVIA assets seeded
  into every deployment; customer names, counts and data never travel.
