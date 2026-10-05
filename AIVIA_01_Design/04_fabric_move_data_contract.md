04_fabric_move_data_contract

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- The phase 02 sheets and phase 03 assets, built and gap-checked
  LOCALLY (the ruled refresh story: local stays the truth; Fabric is
  a sync destination, never a rebuild site this phase).
- The aivia01 wheel and the phase 01 sync machinery (wheel sync,
  notebook sync, browser sign-in) — the proven plumbing this phase
  extends.

Where do the assets live?
- Local (the truth): AIVIA_01_Data/02_emr_data_dictionary/ and
  AIVIA_01_Data/03_chat_bot/ — unchanged by this phase.
- Fabric: lakehouse AIVIA_01_LH, Delta tables (Output File 1).
- RULED 2026-09-30: DELTA ONLY — no json Files archive in the
  lakehouse. The local sheets are the verbatim archive; the tables
  are the Fabric truth.

What is the output of this data contract?
- Output File 1: the Delta tables (one per asset, schemas below).
- Output File 2: the derived graph edge table + the declared Fabric
  graph model with its validation record.
- Output File 3: the stage-A chat reading Fabric (an asset-source
  parameter on the existing chat — never a fork).
- Output File 4: the Data Agent comparison scorecard.

Output File 1: the Delta tables
- Names: CONFIRMED by Sunny 2026-09-30, as listed below.
- Loaded by the M02 loader (wheel code, F11 pattern extended), Sunny's
  hand runs the load; counts verified against the local sheets TO THE
  DIGIT before the load is accepted; Sunny's eye on the first load.
- Ids verbatim from the sheets — never minted. Embeddings ride as
  array<float> columns (3,072 each) — the oversized-json problem
  dissolves into Delta.
- Proposed tables and fields (mirroring the ruled sheet contracts):
  dict_tables:           table_id, database_name, schema_name,
                         table_name, table_description, deprecated_yn,
                         table_name_embedding, table_description_embedding
  dict_columns:          column_id, table_id, database_name,
                         schema_name, table_name, column_name,
                         data_type, is_primary_key, key_ordinal,
                         column_ini, column_item, column_description,
                         deprecated_yn, column_name_embedding,
                         column_description_embedding
  dict_joins:            join_id, ordinal, source_table_id,
                         source_table_name, source_column_id,
                         source_column_name, destin_table_id,
                         destin_table_name, destin_column_id,
                         destin_column_name, conditional_c,
                         may_be_stale_c, is_current_data_model_yn,
                         is_supplemental_yn, destin_in_scope
  dict_values:           table_name, code, meaning
  dict_value_embeddings: table_name, code, meaning, meaning_embedding
  dict_no_match:         database_name, schema_name, table_name,
                         column_name, sql_file_names
  chat_abstract_names:   object_kind, object_id, object_name,
                         abstract, synonyms, sunny_abstract,
                         sunny_synonyms
  chat_technical_terms:  keyword, maps_to, kind, synonyms, ruled

Output File 2: the graph model (decision 2, RULED)
- The derived graph edge table, written by the loader, regenerable,
  never hand-edited (proposed name: graph_join_edges): edge_key, kind
  (joins_by_fk | joins_by_rule — the L08 provenance law lands as a
  column), source_table_id, destin_table_id, column_pairs, rule,
  ride-along flags. 210 fk + 181 rule rows today.
- The Fabric graph model declared over the lakehouse tables:
  table nodes from dict_tables; column nodes from dict_columns (the
  L09 ruling — columns are nodes); has_column edges from
  dict_columns' own table_id; join edges from graph_join_edges.
- THE VALIDATION GATE (this phase's only consumer): GQL probes vs the
  local engine's golden answers — one component of 38; 210 + 181 edge
  counts by kind; ZC_STATE's 9 edges with correct FK owners. Results
  recorded in the design doc the day they run. The chat never reads
  the model this phase.
- Capacity: declaring or refreshing the model is a capacity op —
  Sunny's go, one refresh per batch.

Output File 3: stage-A chat
- The chat's asset source becomes a parameter: a local dir OR the
  lakehouse — one code path, never a fork. Acceptance: the startup
  census matches local TO THE DIGIT (38 / 1,618 / 14,476 / 1,656 /
  210 / 181) and the twelve shapes rerun green against Fabric-backed
  assets.

Output File 4: the Data Agent comparison (decision 8, RULED)
- The same twelve shapes (plus the live session questions) against
  BOTH the Data Agent and our chat; the scorecard lands in
  Sunny's 04 shapes md, dated, per question: ours / theirs / verdict.
- DIRECTION LAW: our chat is ground truth and the acceptance gate;
  the Data Agent is the subject, never the validator.
- Capacity + per-question cost: Sunny's go.

What models are used in production?
- Embeddings: text-embedding-3-large on the customer's Azure OpenAI —
  THE PARITY LAW (decision 4, ruled): identical model to the stored
  embeddings or re-embed everything; never mix. The M05 parity check:
  one known text re-embedded on the Azure endpoint, compared to the
  stored vector, recorded.
- Segmentation: gpt-5.4-mini — ADOPTED 2026-10-01 (newer than the
  planned gpt-5-mini, already deployed on aivia; chat has no parity
  law). Deployments on aivia (East US 2), names = model names:
  text-embedding-3-large and gpt-5.4-mini. Endpoint
  https://aivia.openai.azure.com/. PARITY VERIFIED 2026-10-01:
  cosine 0.999999 vs the stored PATIENT vector — and it stands as a
  LIVE regression test in the suite forever.

Where do the keys live?
- Local development: OPENAI_API_KEY in .env (unchanged).
- Production: Azure Key Vault aivia01-kv, secret
  aivia01-azure-openai-key (RULED 2026-10-01 — the 02/03 TBDs close).
- Identity: Entra ID sign-in (the phase 01 browser sign-in precedent).

What is the refresh story? (decision 6, ruled)
- Local rebuild (parse, sheets, abstracts, gap-check) -> Sunny's load
  command -> Delta tables refresh -> graph model refresh on her go.
- One refresh per batch. A Fabric-side rebuild pipeline is NOT this
  phase.

Who can read these tables?
- Sunny Zheng; the chat (stage A); the declared graph model; the Data
  Agent (for the comparison only).

Who can edit these tables?
- The M02 loader only (Sunny runs it). No hand edits in the lakehouse
  — the local sheets are the truth; a lakehouse-only change is drift
  and the next load erases it.

THE SYNC MANIFEST EXTENSION (AMENDED 2026-10-04, Sunny's "go,
build step 0" — the 07 runbook's named build item): the files
transport ships, beyond the eight 02/03 files, the 05/06/07
estate AT CENSUS SCOPE (the corpus stays paused by her word):
- 05_semantic_graph/: all twelve 05 sheets
- 06_technical_descriptions/: the description sheet, the voicing
  ledger, the census .txt and .svg
- 07_business_descriptions/: the business sheet, the blessing
  registry, fact voices, code sightings, walk trace, naming
  gaps, the census .txt and .facts.txt
Destination Files/Data/<subdir>/<name>, unchanged mechanics
(skip-if-unchanged, --force, chunked). The lock
(test_sync_file_list_matches_the_contract) pins the full list;
future scope growth (the corpus, 08 outputs) re-amends here
first, red test second, constant third — the standing order.

How to test?
/opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v

The production commands all live in the runbook
(AIVIA_01_Test/AIVIA_01_Production/04_fabric_move_production_steps.md):
Step A wheel+notebook sync, Step B files sync, Step C the M02 load,
Step E the M03 graph gate, Step F the stage-A chat, Step H the full
production shape (--fabric --azure) and the parity check. All run and
accepted 2026-09-30/10-01.

What are the data contracts:

{
  "dict_tables":           {"rows[]": ["table_id", "database_name", "schema_name", "table_name", "table_description", "deprecated_yn", "table_name_embedding", "table_description_embedding"]},
  "dict_columns":          {"rows[]": ["column_id", "table_id", "database_name", "schema_name", "table_name", "column_name", "data_type", "is_primary_key", "key_ordinal", "column_ini", "column_item", "column_description", "deprecated_yn", "column_name_embedding", "column_description_embedding"]},
  "dict_joins":            {"rows[]": ["join_id", "ordinal", "source_table_id", "source_table_name", "source_column_id", "source_column_name", "destin_table_id", "destin_table_name", "destin_column_id", "destin_column_name", "conditional_c", "may_be_stale_c", "is_current_data_model_yn", "is_supplemental_yn", "destin_in_scope"]},
  "dict_values":           {"rows[]": ["table_name", "code", "meaning"]},
  "dict_value_embeddings": {"rows[]": ["table_name", "code", "meaning", "meaning_embedding"]},
  "dict_no_match":         {"rows[]": ["database_name", "schema_name", "table_name", "column_name", "sql_file_names"]},
  "chat_abstract_names":   {"rows[]": ["object_kind", "object_id", "object_name", "abstract", "synonyms", "sunny_abstract", "sunny_synonyms"]},
  "chat_technical_terms":  {"rows[]": ["keyword", "maps_to", "kind", "synonyms", "ruled"]},
  "graph_join_edges":      {"_what": "derived by the loader, regenerable, never hand-edited; the L08 provenance column", "rows[]": ["edge_key", "kind (joins_by_fk|joins_by_rule)", "source_table_id", "destin_table_id", "column_pairs", "rule", "conditional_c", "may_be_stale_c", "is_current_data_model_yn", "is_supplemental_yn"]}
}
