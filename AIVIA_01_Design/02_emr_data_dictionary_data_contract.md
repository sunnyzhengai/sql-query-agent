02_emr_data_dictionary_data_contract

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- The EMR's data dictionary, Sunny has authorized access 
- We only need a portion of the EMR's data dictionary, which is decided by what tables and columns are used in the 01_subject_sql_files

Where are these data files from?
- A script parses all sql files in 01_subject_sql_files with ScriptDom (output file 1, the growing sql-side file)
- A script derives the tables and columns used from the tree, into the same file (output file 1, "derived" section)
- A script writes a discovery query; Sunny runs it once and saves the result as csv (output file 3, first move)
- A script writes the 5 sql extraction queries from the discovery facts (output file 3)
- Sunny runs the 5 queries in the EMR's database and saves the results as csv (output file 4)
- A script converts the csv results into the json data sheets and adds embeddings (output file 5): table, column, join, iniitm, value


Do we need to desensitize the data files?
- No.

Where are these sql files located for local development?
- /Users/sunnyzheng/sql-query-agent/AIVIA_01_Data/02_emr_data_dictionary/

Where are these sql files located for production?
- Fabric lakehouse, AIVIA_01_LH/Files/Data/02_emr_data_dictionary/

What is the output of this data contract?
- 3 data sheets, 02_emr_data_dictionary_extraction_table.json, 02_emr_data_dictionary_extraction_column.json, 02_emr_data_dictionary_extraction_join.json


Output File 1: the sql-side file — ONE growing file for everything derived from the sql files (ruled 2026-09-28)
- Name: 02_emr_data_dictionary/02_sql_extraction.json
- One file, sections written by different scripts at different times:
  - "files": the FULL MAPPED TREE per sql file (step 2, ruled 2026-09-27)
  - "derived": the tables and columns used (step 3)
  - "resolution": the dictionary bindings (step 5)
- Section ownership: each script writes only its own section. Re-running the
  parse drops the derived and resolution sections and says so loudly; they
  re-derive by script, deterministic. Stale is worse than absent.
- The derived section keeps ONE census of every table-like name found in the
  trees — nothing is set aside in a side list I would never reread:
  - class, decided by structure now: emr_or_enterprise_table, cte, temp_table,
    table_variable, table_function
  - source, decided by the dictionary at step 5: emr, no_dictionary_match;
    reads "pending" until then. Enterprise tables surface as no_dictionary_match
    by evidence, not by labeling.
  - used columns: sql_file_name, database_name, schema_name, table_name,
    column_name. A star read is one row with column_name "*" — every column at
    read time, never a frozen list.
  - unresolved bare columns: file, column, candidate tables. They bind at
    step 5 when the dictionary says which candidate owns the column. Never
    guessed here.
- Shorthand db..table: database kept, schema left blank; the dictionary
  supplies the real schema at step 5.
- Org fact (optional, my call): in our EMR databases an omitted schema means
  dbo; the derived section fills dbo with this ruling as provenance.

Output File 2: folded into Output File 1, the "derived" section (ruled
2026-09-28). No separate file.

Output File 3: the sql queries, in two moves
- First move, discovery: 02_emr_data_dictionary_discovery.sql — the
  INFORMATION_SCHEMA columns of CLARITY_TBL and CLARITY_COL. I run it once and
  save 02_emr_data_dictionary_discovery.csv. I also answer: which dictionary
  table holds the join relationships.
- Second move, generated from the discovery facts:
  02_emr_data_dictionary_extraction_table.sql,
  02_emr_data_dictionary_extraction_column.sql,
  02_emr_data_dictionary_extraction_join.sql
- The used-table list is written into the queries as literal IN lists, so they
  run standalone in my query tool.
- The column query pulls ALL columns of the used tables, not only the used
  ones: star reads make "used" incomplete by definition, unresolved columns
  need the full list to bind, and the join sheet needs ids for columns the
  files never read.
Output File 3 update (2026-09-28): discovery satisfied by my hand — I pasted the
dictionary shapes (CLARITY_TBL, CLARITY_COL, CLARITY_COL_INIITM, CLARITY_TBL_FK_ALL,
CLARITY_TBL_PK) into chat; recorded in 02_emr_data_dictionary_discovery_facts.md.
No discovery csv.
- Field sources ruled: table_description = TABLE_INTRODUCTION; column_description
  = DESCRIPTION; data_type = DATA_TYPE; join source = CLARITY_TBL_FK_ALL; join_id = "TABLE_ID:FOREIGN_KEY_NUM" — ruled
  2026-09-28: FOREIGN_KEY_NUM restarts at 1 inside every table (34 of our tables
  each have their own FK 1), so the composite id is required; ORDINAL_POSITION =
  ordinal, composite joins reassemble.
- The TBL_DESCRIPTOR_OVR IS NOT NULL filter rides on every query: it de-dups —
  without it each table returns 2 entries. This is the consistent unique-table
  filter.
- No reliability filters yet: CONDITIONAL_C, MAY_BE_STALE_C,
  IS_CURRENT_DATA_MODEL_YN ride along as join-sheet columns instead of
  filtering — I don't know yet if they are reliable filters.
- DEPRECATED_YN rides along on the table and column sheets, never filtered —
  a used-but-deprecated object is a finding.
- Estate fact: V_* and F_* names inside the EMR are TABLES, same database and
  schema as the base tables. They are not our organization's views; our views
  and stored procedures live in their own schemas (the ones in the sql files).
- ADDED this phase (my ruling): CLARITY_COL_INIITM and category values.
  - iniitm sheet: column_id, line, column_ini, column_item — extracted with the
    other queries, joined through CLARITY_TBL by table name.
  - category values: the ZC_* tables' code -> NAME rows. Their queries are
    generated in a THIRD move after the join csv lands — FK_ALL's
    DEST_COLUMN_NAME names each ZC table's id column, so the queries derive
    from data, never guessed. Sheet fields: table_name, code, meaning.
  - no embeddings on iniitm or values this phase; revisit at the chat step.
- Move 2 therefore generates FIVE queries — table, column, join, pk, iniitm —
  all filtered by CLARITY_TBL.TABLE_NAME IN (the used tables) plus the de-dup
  filter, ids joined inside each query, standalone-runnable. Move 3 generates
  the values queries from the join csv.


Output File 4: the query results, saved by Sunny
- Name: 02_emr_data_dictionary/02_emr_data_dictionary_extraction_table.csv,
  02_emr_data_dictionary_extraction_column.csv, 02_emr_data_dictionary_extraction_join.csv
- Content: the raw results of the 3 queries, exported as csv by Sunny's hand.

Output File 5: the 3 data sheets
- Name: 02_emr_data_dictionary/02_emr_data_dictionary_extraction_table.json
- Content: table_id, table_name, table_description,
  table_name_embedding, table_description_embedding
- Name: 02_emr_data_dictionary/02_emr_data_dictionary_extraction_column.json
- Content: table_id, column_id, column_name, column_description,
  column_name_embedding, column_description_embedding
- Name: 02_emr_data_dictionary/02_emr_data_dictionary_extraction_join.json
- Content: source_table_id, source_table_name, source_column_id, source_column_name,
  destin_table_id, destin_table_name, destin_column_id, destin_column_name
- table_id and column_id come verbatim from CLARITY_TBL and CLARITY_COL — never minted.
- Ids are the keys; names ride along for readability. The build fails loudly if a
  join row references an id absent from the table or column sheets.
- FK integrity refined (ruled 2026-09-28): the dictionary's join rows reach far
    outside our used tables (5,052 of 5,261 rows point at 930 tables we did not
    extract). All rows are kept; each carries destin_in_scope true/false.
    Integrity fails loudly for source ids always, and for destination ids only
    when destin_in_scope. Outside destinations are the expansion frontier,
    visible, never a failure.
- Descriptions have no blanks; a blank description fails loudly.
- Tables and columns used in the sql files but absent from the EMR data dictionary
  (non-EMR objects) are expected: they are counted and listed by name in
  02_emr_data_dictionary/02_no_dictionary_match.json — never silently absent.

Output File 6: the t-sql construct master list
- Name: 02_emr_data_dictionary/02_tsql_construct_master.json
- One row per t-sql grammar construct, from Microsoft's own parser library
  (ScriptDom, ~1000 constructs). The list is complete by construction —
  no construct can surprise us.
- Script-filled columns, regenerated every run: construct name, keyword hint,
  count in our sql files, one example fragment, and the observed status:
  "mapped" (stored as structure in the tree), "remainder" (stored as counted
  verbatim text, not structure), "unseen" (count 0).
- Sunny-filled column, preserved across rebuilds: the ruling.
  A ruling is required only for constructs that appear in our files and are
  not mapped. Ruling values: "map" (build a handler) or
  "remainder — <reason>" (keep as counted text on purpose).
  Unseen constructs need no ruling.
- Loud rules (test-enforced):
  - a construct that appears in our files with no ruling = tests fail, naming it.
  - a construct ruled "map" that the code does not map = tests fail.
  - a stale ruling (construct no longer needs it) = tests fail.
- The parser never reads this list. Mapping decisions live in the code Sunny
  approved; this list records and audits them. Changing a ruling changes the
  tests, which drives the build — never the parse.
- Go-live gate: zero constructs observed-and-unruled.
- Portability: the construct names, keywords, rulings and reasons are AIVIA's
  own domain knowledge and carry forward to future customers. The counts and
  example fragments are this customer's data and never travel.

Who can read these data dictionary files?
- Sunny Zheng
- Claude Code Agent
- Code script authorized by Sunny Zheng

Who can edit these data dictionary files?
- Sunny Zheng

Who can edit the data sheet?
- Sunny Zheng to run the scripts
- Script authorized by Sunny Zheng; 
- Claude asks before updating the data sheets

What model is used to embed the file names?
- Embedding model: OpenAI text-embedding-3-large, 
- 3072 numbers per embedding; 
- key in .env file.

Where does the key live in production?
— Azure Key Vault aivia01-kv, secret aivia01-azure-openai-key
  (RULED 2026-10-01 at 04 M05; local dev: .env).

What are the search acceptance parameters?
- Three declared, tunable contract facts — never cliffs:
  CANDIDATE_FLOOR: at/above = shown as a candidate with its visible score; below may be "unknown".
  MATCH_SCORE: at/above = a real match; accepted hits become graph anchors.
  UNIQUE_MARGIN: an accepted hit must be within this of the best hit to stay in the anchor set.
- Starting values 0.25 / 0.5 / 0.1 are PLACEHOLDERS from the previous build,
  calibrated there on text-embedding-3-small. They do not transfer to
  text-embedding-3-large. Calibration lands via Sunny's hand test cases in
  test_02_emr_data_dictionary_data_contract_sunny.md; the values are not final
  until that run.
- With separate name and description embeddings per row: ranking uses the sum of
  the scores that clear the floor; "is it a real match" uses the best single score
  (the previous build's ruled split — several weak scores are not one real match).

How to test?
/opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v
/opt/homebrew/bin/python3.11 AIVIA_01_Code/parse_sql_tree.py AIVIA_01_Data/01_subject_sql_files AIVIA_01_Data/02_emr_data_dictionary/02_sql_extraction.json AIVIA_01_Data/02_emr_data_dictionary/02_tsql_construct_master.json


What are the data contracts:

{
  "02_sql_extraction.json": {
    "_what": "THE one growing sql-side file. Sections owned by different scripts; re-parse drops derived/resolution loudly.",
    "files[]": {
      "_owner": "parse_sql_tree.py (step 2)",
      "entry": ["node", "name", "dialect", "tree_version", "statements[]", "remainder[]", "comments[]?", "dynamic_sql?"],
      "statement": ["statement_kind", "position", "evidence",
                    "ctes[]?", "scope?", "predicate?", "then[]?", "else[]?", "body[]?",
                    "variable?", "expression?", "options?", "on?", "declarations[]?",
                    "targets[]?", "if_exists?", "argument[]?", "reconstruction?",
                    "procedure?", "database?", "comments[]?"],
      "scope": ["node", "evidence", "from_refs[]", "join_on[]", "where?", "group_by[]?",
                "order_by[]?", "projection[]", "distinct?", "set_op?", "name?",
                "insert_columns[]?", "declared_columns[]?", "comments[]?"],
      "set_op": ["kind", "all", "sides[2]"],
      "from_ref (named table)": ["table_ref", "alias", "evidence", "apply?", "comments[]?"],
      "from_ref (table variable)": ["table_ref", "variable", "evidence"],
      "from_ref (derived table)": ["derived_scope", "alias", "evidence"],
      "from_ref (table function)": ["function_ref", "args[]", "alias", "evidence"],
      "join_on entry": ["(a predicate node)", "join_type"],
      "expression": ["node", "kind", "evidence", "comments[]?",
                     "name? (column_ref/function)", "value? + literal_type? (literal)",
                     "args[]? distinct? over? within_group? (function)",
                     "op? first? second? (arithmetic)", "op? expression? (unary)",
                     "expression? data_type? style? (cast)",
                     "input? whens[]? else_result? (case)", "scope? (subquery_ref)",
                     "qualifier? (star)"],
      "over": ["partition_by[]", "order_by[]"],
      "within_group": ["order_by[]"],
      "case when": ["when", "then"],
      "order_by element": ["expression", "sort?"],
      "predicate": ["node", "kind", "evidence", "comments[]?",
                    "subject? comparand? (COMPARE_*)", "members[]? (AND/OR/IN_LIST)",
                    "member? (NOT)", "subject? pattern? (PATTERN_MATCH)",
                    "subject? scope? (IN_SELECTION/EXISTS_SELECTION)",
                    "subject? low? high? (RANGE)"],
      "projection_member": ["node", "position", "name", "expression?", "star?",
                            "qualifier?", "set_variable?", "evidence", "comments[]?"],
      "declaration": ["name", "data_type", "value?"],
      "reconstruction": ["variable", "text", "placeholders[]", "dropped[]",
                         "reconstructed?", "statements[]?", "remainder[]?", "errors[]?"],
      "evidence": ["fragment", "offset", "line", "column"],
      "comment": ["text", "offset", "line", "column", "kind", "position? (absent at file level)"],
      "remainder item": ["type", "reason", "evidence"]
    },
    "derived": {
      "_owner": "derive_tables_columns.py (step 3)",
      "tables[]": ["sql_file_name", "name", "class", "database_name", "schema_name", "source", "written_as"],
      "columns[]": ["sql_file_name", "database_name", "schema_name", "table_name", "column_name"],
      "unresolved[]": ["sql_file_name", "column_name", "candidates[]"],
      "anomalies[]": ["sql_file_name", "name", "reason"]
    },
    "resolution": {
      "_owner": "build_dictionary_sheets.py (step 5)",
      "table_source": "{table name: emr | no_dictionary_match}",
      "bindings[]": ["sql_file_name", "column_name",
                     "outcome (bound | ambiguous | no_match)",
                     "table_name (when bound)", "owners[] (when ambiguous)"]
    }
  },

  "02_tsql_construct_master.json": {
    "_what": "Output File 6, the construct master.",
    "rows[]": ["construct", "keywords", "count_in_corpus", "example", "status", "ruling"]
  },

  "02_emr_data_dictionary_discovery.sql": {
    "_what": "Output File 3 first move. A query file, no data fields. Read-only."
  },
  "02_emr_data_dictionary_discovery.csv": {
    "_what": "Sunny's saved discovery result.",
    "rows[]": ["TABLE_CATALOG", "TABLE_SCHEMA", "TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "ORDINAL_POSITION"]
  },

  "02_emr_data_dictionary_extraction_table.sql": {"_what": "generated at move 2 from discovery facts"},
  "02_emr_data_dictionary_extraction_column.sql": {"_what": "generated at move 2 from discovery facts"},
  "02_emr_data_dictionary_extraction_join.sql": {"_what": "generated at move 2; source table named by Sunny"},

  "02_emr_data_dictionary_extraction_table.csv": {
    "_what": "Output File 4. Field names fixed by the generated table query at move 2."
  },
  "02_emr_data_dictionary_extraction_column.csv": {
    "_what": "Output File 4. Field names fixed by the generated column query at move 2."
  },
  "02_emr_data_dictionary_extraction_join.csv": {
    "_what": "Output File 4. Field names fixed by the generated join query at move 2."
  },

  "02_emr_data_dictionary_extraction_table.json": {
    "_what": "Output File 5, the table sheet.",
    "rows[]": ["table_id", "database_name", "schema_name", "table_name",
               "table_description", "table_name_embedding", "table_description_embedding"]
  },
  "02_emr_data_dictionary_extraction_column.json": {
    "_what": "Output File 5, the column sheet. is_primary_key/key_ordinal only if the dictionary exposes them (discovery tells).",
    "rows[]": ["column_id", "table_id", "database_name", "schema_name", "table_name",
               "column_name", "data_type", "is_primary_key?", "key_ordinal?",
               "column_description", "column_name_embedding", "column_description_embedding"]
  },
  "02_emr_data_dictionary_extraction_join.json": {
    "_what": "Output File 5, the join sheet. join_id groups the column pairs of ONE join; ordinal orders them — multi-column joins must reassemble.",
    "rows[]": ["join_id (TABLE_ID:FOREIGN_KEY_NUM)", "ordinal",
               "source_table_id", "source_table_name", "source_column_id",
               "source_column_name", "destin_table_id", "destin_table_name",
               "destin_column_id", "destin_column_name", "conditional_c",
               "may_be_stale_c", "is_current_data_model_yn",
               "is_supplemental_yn", "destin_in_scope"]  },
 "02_emr_data_dictionary_extraction_iniitm.json": {
    "rows[]": ["column_id", "line", "column_ini", "column_item"]
 },
 "02_emr_data_dictionary_extraction_value.json": {
    "rows[]": ["table_name", "code", "meaning"]
 },

  "02_no_dictionary_match.json": {
    "_what": "Used in the sql files, absent from the dictionary — counted, never silently absent. Enterprise tables surface here by evidence.",
    "rows[]": ["database_name", "schema_name", "table_name", "column_name (blank = table-level miss)", "sql_file_names[]"]
  }
}