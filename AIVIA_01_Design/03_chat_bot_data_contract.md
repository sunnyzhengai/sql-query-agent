03_chat_bot_data_contract

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- The user's natural-language question, typed into the chat page.
- The phase 02 data sheets (table, column, join, iniitm, value + the
  value-embeddings sidecar) and 02_no_dictionary_match.json — read only,
  never written by this phase.
- The technical terms list (Output File 1).
- The name-abstract list (Output File 2).

Where are these data files located for local development?
- /Users/sunnyzheng/sql-query-agent/AIVIA_01_Data/03_chat_bot/

Where are these data files located for production?
- Fabric lakehouse, AIVIA_01_LH/Files/Data/03_chat_bot/

What is the output of this data contract?
- 2 files: 03_chat_technical_terms.md, 03_chat_abstract_names.json
- The question record (chosen-vs-shown) is DEFERRED — ruled in
  principle in the design doc (decision 8), not built in version one.

Output File 1: the technical terms list
- Name: 03_chat_bot/03_chat_technical_terms.md
- Author: Sunny (seeded from the reviewed draft; grows by her hand)
- Content: keyword | maps to | kind (population / operation / property)
  | synonyms. All node types, edge types, operations.
- Used by: the LLM segmentation prompt (carried as data, no examples)
  and lane 2 of the funnel (keyword synonyms).
- Ruling on how a new keyword is added — a ruled row like the CLARITY category list

Output File 2: the name-abstract list
- Name: 03_chat_bot/03_chat_abstract_names.json
- Built by: a python script (L03) calling the LLM — name + stored
  description in, a short abstract and synonyms out. Batched paid
  calls. Regeneration law: rerun when names/descriptions change, reuse
  what is unchanged (the phase-01 economy law).
- Acceptance: Sunny gap-checks; her eye is the gate.
- Completion integrity: every table and every column has a row, or the
  absence is counted and named — part of the graph completion check.
- Portability: Epic-standard abstracts are AIVIA's and carry forward;
  anything derived from customer-local text never travels.
- Fields: object_kind (table|column), object_id, object_name,
  abstract, synonyms[] — script-owned, regenerated;
  sunny_abstract, sunny_synonyms[] — Sunny-owned, preserved across
  every regeneration, the script never writes them (the
  construct-master precedent). A non-blank sunny_abstract stands in
  for the script's abstract; sunny_synonyms are additions.
- lane-2 lexical only

What models are used?
- Segmentation: OpenAI gpt-5-mini — pinned as a code constant, this
  contract names it (same law as EMBEDDING_MODEL).
- Embeddings: OpenAI text-embedding-3-large, 3072 numbers — the same
  model as the sheets; a question token is never embedded with a
  different model than the stored rows.
- Key: OPENAI_API_KEY in .env at repo root (local). Production: Azure
  Key Vault, secret name TBD at the Fabric move.
- Per question: one chat call (segmentation) + one batched embedding
  call (lane-3 tokens). All calls real and paid, never faked.

What are the search acceptance parameters?
- Three declared, tunable contract facts — DISPLAY DEFAULTS, not gates,
  applied per population, to lane-3 (embedding) matches only. Lane 1
  and lane 2 hits bypass them.
  CANDIDATE_FLOOR: below = not shown.
  MATCH_SCORE: at/above = pre-selected by default.
  UNIQUE_MARGIN: a pre-selected hit must be within this of the best hit
  in ITS population to stay pre-selected.
- Starting values: TBD — calibrated by Sunny's hand shapes
  (test_03_chat_bot_data_contract_sunny.md); per-population values
  allowed (tables / columns / values need not share numbers).
- With separate name and description embeddings per row: ranking uses
  the sum of the scores that clear the floor; pre-selection uses the
  best single score (the ruled split, carried forward).

Who can read these files?
- Sunny Zheng
- Claude Code Agent
- Code script authorized by Sunny Zheng

Who can edit these files?
- 03_chat_technical_terms.md: Sunny only.
- 03_chat_abstract_names.json: the L03 script writes its own fields
  (Sunny runs it); the sunny_* fields are Sunny's only, preserved
  across regeneration — a rebuild that loses one is a test failure.

How to test?
/opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v
TBD (the chat startup command lands here at build, L06)

What are the data contracts:

{
  "03_chat_technical_terms.md": {
    "_what": "Output File 1, Sunny-authored vocabulary. The LLM prompt carries it as data.",
    "rows[]": ["keyword", "maps_to", "kind (population|operation|property)", "synonyms[]"]
  },

  "03_chat_abstract_names.json": {
    "_what": "Output File 2, built by the L03 script, Sunny gap-checked. Lane 2 of the funnel. sunny_* fields preserved across regeneration.",
    "rows[]": ["object_kind (table|column)", "object_id", "object_name",
               "abstract", "synonyms[]",
               "sunny_abstract (blank = script's stands)",
               "sunny_synonyms[] (additions, never removed by the script)"]
  }
}
