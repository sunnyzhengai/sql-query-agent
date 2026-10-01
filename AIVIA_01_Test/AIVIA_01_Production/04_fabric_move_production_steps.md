04_fabric_move_production_steps — Sunny's manual runbook for the M02
load (and the steps that follow). Every file name and command exact.
Written by Claude 2026-09-30; grows as the move steps land.

=====================================================================
PREREQUISITES — check once before the first run
=====================================================================
[ ] The Fabric workspace exists and you can open it in the portal.
[ ] The Environment item AIVIA_01_ENV exists in it, with openai 3.19.2
    in its public libraries (set once, phase 01).
[ ] The lakehouse AIVIA_01_LH exists in the workspace.
[ ] You have THREE ids, all from portal URLs when the item is open:
      workspace id   .../groups/<workspace-id>/...
      environment id .../environments/<environment-id>
      lakehouse id   .../lakehouses/<lakehouse-id>
[ ] An EMPTY notebook item exists for M02 (create once in the portal:
    workspace > New > Notebook; name it, e.g., nb_m02_load_dictionary;
    copy its id from the URL: .../synapsenotebooks/<notebook-id>).
[ ] Local suite green first:
      /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v
[ ] All commands below run from the repo root:
      cd /Users/sunnyzheng/sql-query-agent

=====================================================================
STEP A — ship the wheel (aivia01 0.3.0) + the M02 notebook definition
=====================================================================
One command builds the wheel, signs you in (normal browser sign-in),
removes stale wheels, uploads, pushes the notebook cell, then ASKS
before publishing (publish = capacity, several minutes):

  /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_wheel.py \
      --workspace <workspace-id> --environment <environment-id> \
      --notebook <notebook-id> \
      --notebook-source AIVIA_01_Code/notebook_m02_load_dictionary_tables.py

  - At "Publish environment now? [y/N]": answer y when you are ready
    to spend the capacity; N leaves it staged for later.
  - Success looks like: publish state success, and aivia01 0.3.0 in
    the printed libraries list next to openai 3.19.2.

=====================================================================
STEP B — upload the asset files to the lakehouse Files (the transport)
=====================================================================
One command, browser sign-in, then the uploads with progress:

  /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_files.py \
      --workspace <workspace-id> --lakehouse <lakehouse-id>

The eight files it ships (local -> Files/Data/..., same names):
  02_emr_data_dictionary_extraction_table.json
  02_emr_data_dictionary_extraction_column.json         (~254 MB)
  02_emr_data_dictionary_extraction_join.json
  02_emr_data_dictionary_extraction_value.json
  02_emr_data_dictionary_extraction_value_embeddings.json (~1.1 GB)
  02_no_dictionary_match.json
  03_chat_technical_terms.md
  03_chat_abstract_names.json
Unchanged files (same size remotely) are skipped; add --force to
re-upload everything. The big two take a few minutes; progress prints
per 32 MB chunk.

=====================================================================
STEP C — run the M02 notebook (capacity: your go)
=====================================================================
1. Open the notebook in the portal.
2. Attach the environment AIVIA_01_ENV (notebook toolbar > Environment)
   and the lakehouse AIVIA_01_LH as the default lakehouse.
3. The one cell is already there from Step A. Run it.
4. THE ACCEPTANCE — the printed counts must equal the golden numbers
   TO THE DIGIT:
     dict_tables 38              dict_columns 1618
     dict_joins 5262             dict_values 14476
     dict_value_embeddings 14476 dict_no_match 1
     chat_abstract_names 1656    chat_technical_terms 9
     graph_join_edges 391        graph_table_nodes 38
     graph_column_nodes 1618
   and the census line ends with joinsByFk 210, joinsByRule 181.
   Any other number = STOP; the loader itself fails loudly on drift,
   so a wrong count on screen means something upstream moved — bring
   the verbatim output back to the chat session.
5. Your eye: in AIVIA_01_LH > Tables, the eleven tables exist; open
   dict_tables and spot-check a row (camelCase columns, PATIENT's
   description reads correctly).

=====================================================================
STEP D — verify from the SQL endpoint (optional, no capacity to speak of)
=====================================================================
In the lakehouse SQL analytics endpoint, these should return the
golden numbers:
  SELECT COUNT(*) FROM dict_tables;          -- 38
  SELECT COUNT(*) FROM dict_columns;         -- 1618
  SELECT kind, COUNT(*) FROM graph_join_edges GROUP BY kind;
                                             -- joins_by_fk 210
                                             -- joins_by_rule 181
  SELECT TOP 5 tableName, code, meaning FROM dict_values
   WHERE tableName = 'ZC_DISCH_DISP';        -- verbatim meanings

=====================================================================
TROUBLESHOOTING (the failures we have already met)
=====================================================================
- Sign-in error 530035: device-code flow is blocked by tenant security;
  the scripts use browser sign-in — if you see this, the browser window
  was skipped; rerun and complete the sign-in page.
- SystemError1009 on a table load: a transient Fabric service fault on
  trial capacity (met at F12/F13) — rerun the cell.
- openai billing_not_active: not a Fabric issue — the OpenAI credit
  balance is empty (Settings > Billing > Add to credit balance). Only
  affects local builds; nothing in Fabric calls OpenAI this step.
- A count mismatch in Step C: never edit lakehouse tables by hand —
  the local sheets are the truth; fix locally, rerun Step B then C.

=====================================================================
WHAT COMES AFTER (lands here as each step builds)
=====================================================================
- M03: declare the graph model over graph_table_nodes /
  graph_column_nodes / graph_join_edges (NEVER over dict_* — the
  embedding columns break the graph mapping) + run the validation
  gate. Capacity: your go.
- M04: the chat reads FROM Fabric (stage A) — command lands here.
- M05: Azure OpenAI deployments + Key Vault secret names.
- M06: the Data Agent comparison runs.
