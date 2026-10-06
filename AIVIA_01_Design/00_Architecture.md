00_Architecture.md

Status: DRAFT — Sunny's product architecture, spoken 2026-10-01 in
chat, scribed verbatim-in-substance by Claude at her direction.
This document is the standing map of where AIVIA is going; it is
updated as rulings land. Sunny owns it.

GOALS (spoken 2026-10-05, Sunny, in chat; scribed by Claude at
her direction)

1. Report descriptions for Collibra. From a data governance
   perspective: parse the organization's SQL files and translate
   them into business descriptions that populate Collibra's
   Power BI report description section — so the whole
   organization's users can read and understand what a report
   includes and excludes, and decide whether it is the right
   report they are looking for. This automates the process so no
   one has to ask a BI developer to read the SQL and translate
   it.

2. Business Terms proposed automatically. By the same token,
   propose Business Terms from the parsed SQL. Sunny's
   definition: all scopes should be Business Terms. Each
   Business Term carries: a name, a business description, a
   technical definition, and the PBI report it ties to. The
   output is a data file with these fields; Sunny then runs a
   notebook script that calls Collibra APIs to update.

THE FOUR PRODUCT PHASES

Naming ruled 2026-10-01 (Sunny, in chat): product phases carry Roman
numerals + a short name — Phase I (Describe), Phase II (Business
Meaning), Phase III (Traverse), Phase IV (Self-Service Run). Arabic
numbers (01, 02, …) belong to build phases only; letters stay with
phase 04's decision-7 stages (A/B, B1/B2) and are not reused for
product phases.
Phase III inserted 2026-10-01 (Sunny, in chat): traversal is its own
phase, not a Phase II rider — Phase II's rollup walk is deterministic
containment inside the description batch job; question-driven
pathfinding is a different machine with different acceptance. The
former Phase III (Self-Service Run) becomes Phase IV.

THE STANDING LAW (ruled 2026-10-01, Sunny, in chat): AIVIA never
creates a query from scratch. Phase III answers with paths and
explanations, never with new SQL; Phase IV re-parameterizes SQL the
organization already wrote and ran — it never writes new logic.

Phase I — Describe: build a complete graph where everything is
interpreted.

- From technical/syntax (the EMR's data dictionary — all things that
  exist) to semantics (the organization's SQL files — the "reality"
  of the organization, a subset of technical objects used to
  construct the business meanings at the organization).
- Our job: build the graphs, build the abstract/synonym lists, build
  the embeddings.
- The chat page allows users to ask and retrieve these descriptions.
  Not to traverse, not to build new SQL logic, not to touch any real
  data behind the SQL.
- This phase is all about putting what exists already into a
  connected graph and translating all technical things into plain
  English.

RULED 2026-10-01 (Sunny, in chat): within Phase I, the semantics
layer (parsed SQL graph) joins the SAME chat page with the same
find-and-describe behavior — one page, one funnel, one confirm flow.
The design addition is per-node-kind DETAIL CONTRACTS: each node
kind declares which stored fields its detail panel renders and in
what form. The syntax layer's (table / column / value), which today
live as scattered rulings in 03_chat_bot.md decisions 3/4/7, get
written down retroactively as the first entries when the semantics
layer's are authored.

RULED 2026-10-01 (Sunny, in chat): TWO DESCRIPTIONS per semantic
node, made by two different machines, serving two purposes:
- The TECHNICAL description — pseudo code rendered MECHANICALLY from
  the ScriptDom parse tree (plain Python walking the tree; no LLM).
  Exact: every line traces to a parse-tree node; nothing paraphrased,
  nothing hallucinated; regenerates free when the SQL changes. This
  is Phase I's output — every semantic node lands with it.
- The BUSINESS description — the LLM translating the technical
  description into plain English that preserves the
  population-shaping facts (filters, exclusions, transformations);
  never a general blurb, because the exact pseudo code is its input.
  "Preserves" FORMALIZED 2026-10-04 (THE MUST-SURVIVE LAW, ruled in
  briefs/Brief_07_Graph_Grounded_Proposer.md Q3): three mechanical
  fact classes — population-shaping survives every composition rung
  with values intact; housekeeping survives as one plain clause;
  plumbing dies at its rung — enforced by a both-directions value
  conservation check at the card.
  This is Phase II's output, composed upward: node, then block, then
  file. Sunny's gap-check is the acceptance.
- The pair is the audit chain: a wrong business description is
  checked against its technical description — pseudo code wrong =
  extraction bug; pseudo code right = summarization bug.
- Portability: both descriptions derive from customer SQL and never
  travel; the rendering rules and prompt shapes are AIVIA's and do.
- Open for the build phase's design doc: which description feeds
  lane-3 embeddings — technical, business, or both.
- PRIOR ART (Sunny's directive, 2026-10-01): the previous estate
  already built the technical part — deterministic sentence/
  description generation from ScriptDom parse trees (the aisql
  package; see USP_ED_SEPSIS_descriptions.txt at repo root and its
  generator). Consult it BEFORE designing Phase I's technical
  descriptions; do not re-derive what it already solved.

Phase II — Business Meaning: generate business terms and report
descriptions.

- We give a semantic object (CTE, temp table, independent SQL block)
  its business meaning by using the LLM to translate from each node
  in this structure and summarize it.
- This is possible because in Phase I the graph is already complete:
  everything is connected, and every node has descriptions — so we
  are now able to create meaning for a pre-determined business logic
  unit.
- When every meaningful block is translated into a business
  description, we then summarize the SQL file's description and save
  it with the SQL file's node.
- The chat page in this phase allows a user to ask questions and
  returns the descriptions of a certain report or business term.
- This phase also allows us to bulk-generate descriptions and sync
  up with Collibra (by populating report descriptions or creating
  new business terms through API or extracts).

RULED 2026-10-05 (Sunny, in chat — the GOALS session): the
Business Term unit is the SCOPE — one term per (scope, report)
this phase, dedup later. A scope is a business concept by a
mechanical rule (reads at least one dictionary table; parameter-
only scopes are plumbing). Each term carries a name (LLM
proposes, Sunny blesses, blessed-only export), a business
description (the scope card: Definition / One row is / Keeps /
Excludes — the SCOPE MUST-SAYS landing), and a technical
definition (deterministic, no LLM: Population / Exclusions /
Parameters, one bullet per clause, dictionary business voice —
no SQL, no table names, no codes). Build phase 09 owns this;
design + contract: 09_business_terms.md and its data contract.

Phase III — Traverse: lineage, impact, and path answers over the
Phase I graph.

- Question-driven pathfinding at chat time: "which procedures
  ultimately feed this report field?", "if I change this column,
  what downstream breaks?", "how do these two tables connect through
  intermediates?"
- The answer is a PATH — a new answer shape: the route lit up on the
  map, each hop a stored edge, each node carrying its Phase I
  description so the path reads in plain English.
- The phase 02 connect code (parked since 03_chat_bot.md decision 4)
  finds its home here.
- Needs only Phase I's completed graph to work; Phase II's
  descriptions make path answers readable. Ordered after Phase II by
  value and risk, not by dependency.
- RULED 2026-10-04 (brief Q9): Phase III writes its OWN pathfinder —
  it does not reuse Phase II's description walk (bottom-up whole-tree
  vs question-driven path search: different machines, same graph).
  The shared piece is the graph READ layer only, one small read
  surface (the read_api precedent). No shared walking framework is
  built ahead of this phase's own design.
- BOUNDARY (named at birth, per the standing law): traversal answers
  with paths and explanations, never with new SQL. A join-path
  answer is not an invitation to generate a query.

Phase IV — Self-Service Run: connect with the database to execute a
business term / report to retrieve data.

- Since in Phase II users can ask questions and be mapped to the
  closest report or business term, we will allow users to define
  their own parameters that the SQL behind the scenes already
  contains.
- It is a self-service for existing reports running on user-defined
  parameters.
- This phase connects with the real database, runs the SQL with the
  new parameters, and brings back data.
