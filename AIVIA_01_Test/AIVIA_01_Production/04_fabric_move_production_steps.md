04_fabric_move_production_steps — Sunny's manual runbook for the M02
load (and the steps that follow).
STEPS A-C RUN CLEAN 2026-09-30 (Sunny): golden counts to the digit. Every file name and command exact.
Written by Claude 2026-09-30; grows as the move steps land.

=====================================================================
PREREQUISITES — check once before the first run
=====================================================================
[ ] The Fabric workspace exists and you can open it in the portal.
[ ] The Environment item AIVIA_01_ENV exists in it, with openai 3.19.2
    in its public libraries (set once, phase 01).
[ ] The lakehouse AIVIA_01_LH exists in the workspace.
[ ] The three ids (filled in 2026-09-30; from portal URLs when each
    item is open):
      workspace id   23112b57-368a-46ed-941b-c10e3baad392
      environment id 1b87c0e2-f56c-4253-9933-fb7a60db181d
      lakehouse id   891d75cb-c87e-4096-9383-9cd7df9d6ef3
[ ] An EMPTY notebook item exists for M02 (create once in the portal:
    workspace > New > Notebook; name it, e.g., nb_m02_load_dictionary;
    notebook id filled in 2026-09-30:
      3fbc2a7d-fb79-4893-8b50-a837614146fb
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

PASTE AS ONE LINE (a multi-line paste drops the backslashes and zsh
splits it into broken commands — met live 2026-09-30):

  /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_wheel.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --environment 1b87c0e2-f56c-4253-9933-fb7a60db181d --notebook 3fbc2a7d-fb79-4893-8b50-a837614146fb --notebook-source AIVIA_01_Code/notebook_m02_load_dictionary_tables.py

  - At "Publish environment now? [y/N]": answer y when you are ready
    to spend the capacity; N leaves it staged for later.
  - Success looks like: publish state success, and aivia01 0.3.0 in
    the printed libraries list next to openai 3.19.2.

=====================================================================
STEP B — upload the asset files to the lakehouse Files (the transport)
=====================================================================
One command, browser sign-in, then the uploads with progress:

PASTE AS ONE LINE:

  /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_files.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --lakehouse 891d75cb-c87e-4096-9383-9cd7df9d6ef3

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
STEP E — M03: declare the graph model + run the validation gate
         (capacity: your go; results land in 04_fabric_move.md same-day)
=====================================================================
E1. RE-USE the existing graph model item AIVIA_01_GRAPH (ruled
    2026-09-30): the item is a container for a declaration and its
    name is phase-neutral — one graph model for the workspace, no
    estate clutter. Open it and DELETE the phase-01 declaration (the
    SQL_FILE node; its record lives in git and the docs, not here).
    The stale "couldn't load your data" banner belongs to the old
    f01 mapping and dies with it.

E2. Declare the model — THE LAW: only the three graph_* tables, NEVER
    dict_* (their 3,072-number embedding columns break the graph
    mapping — met live at F12/F13).
    NODES:
      label Table   from graph_table_nodes,  key tableId
      label Column  from graph_column_nodes, key columnId
    EDGES:
      label hasColumn  from graph_column_nodes:
          source tableId -> Table, target columnId -> Column
          (the same table serves as node table and edge table — its
          tableId column is the ownership edge)
      label joins      from graph_join_edges:
          source sourceTableId -> Table, target destinTableId -> Table
          properties: kind, edgeKey, rule, columnPairs, conditionalC,
          mayBeStaleC, isCurrentDataModelYn, isSupplementalYn
    Build/refresh the model (this is the capacity spend).

E3. THE VALIDATION GATE — run these in the graph query experience and
    compare to the expected answers (computed from the local engine,
    the ground truth). Record what you actually ran and got, verbatim.
    FABRIC GQL LAW (met live 2026-09-30): every returned expression
    MUST carry an AS alias — count(t) alone is a syntax error.

    Probe 1 — node census:
      MATCH (t:Table) RETURN count(t) AS tableCount
        expected: 38
      MATCH (c:Column) RETURN count(c) AS columnCount
        expected: 1618

    Probe 2 — edge census by kind (the L08 provenance law intact):
      MATCH ()-[e:joins]->() RETURN e.kind AS kind, count(e) AS n GROUP BY e.kind
        expected: joins_by_fk 210, joins_by_rule 181
        (Fabric GQL demands the GROUP BY explicitly — met live. If the
        placement also errors, the fallback is two filtered counts:
        ... WHERE e.kind = 'joins_by_fk' RETURN count(e) AS n   -> 210
        ... WHERE e.kind = 'joins_by_rule' RETURN count(e) AS n -> 181)
      MATCH ()-[e:hasColumn]->() RETURN count(e) AS n
        expected: 1618

    Probe 3 — one component of 38 (reachability census from PATIENT):
      MATCH (a:Table {tableName: 'PATIENT'})-[:joins]-{0,20}(t:Table)
      RETURN count(DISTINCT t) AS reachable
        expected: 38
        (every table reachable from PATIENT within 20 undirected hops
        = the whole estate is ONE component, rule edges included —
        DATE_DIMENSION connects only through joins_by_rule, so this
        probe also proves the rule edges landed.)

    Probe 4 — ZC_STATE's 9 edges with the FK owners correct:
      MATCH (src:Table)-[e:joins]->(dst:Table {tableName: 'ZC_STATE'})
      RETURN src.tableName AS owner, e.kind AS kind
        expected: exactly 9 rows, ALL joins_by_fk, ALL with ZC_STATE
        as the DESTINATION (the owners point AT the category — the
        stored direction, never flipped):
          CLARITY_DEP            x1
          CLARITY_EPM            x2
          COVERAGE_MEMBER_LIST   x2
          PATIENT                x2
          PATIENT_4              x1
          PAT_RELATIONSHIP_LIST  x1
      and the reverse direction must be EMPTY:
      MATCH (src:Table {tableName: 'ZC_STATE'})-[e:joins]->(dst:Table)
      RETURN count(e) AS n
        expected: 0

E4. The verdict: all four probes matching = the gate PASSES; paste the
    verbatim results into the chat session and the pass lands in
    04_fabric_move.md dated. Any mismatch = STOP, bring the verbatim
    output — the local engine is the ground truth and the model's
    declaration (not the data) is the first suspect.
    Remember: the chat does NOT read this model — it stands validated
    for the future query-writing phase.

=====================================================================
WHAT COMES AFTER (lands here as each step builds)
=====================================================================
- M04: the chat reads FROM Fabric (stage A) — command lands here.
- M05: Azure OpenAI deployments + Key Vault secret names.
- M06: the Data Agent comparison runs.
