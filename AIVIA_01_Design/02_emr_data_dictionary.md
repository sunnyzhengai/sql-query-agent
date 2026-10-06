02_emr_data_dictionary_design

Description:
Step 2: Prepare access to the "EMR's data dictionary" for AIVIA_01 to use.

Local:
L01: Create a data contract: "02_emr_data_dictionary_data_contract.md".

L02: Create a local file folder: AIVIA_01_Data/02_emr_data_dictionary/. 

L03: Parse the 8 sql files in 01_subject_sql_files/ with ScriptDom (the one parse
    door, ported from aisql/graph/kg2_mapper/scriptdom_loader.py).
    RULED 2026-09-27: the parse artifact is the FULL MAPPED TREE per file —
    statements, scopes, table references, join predicates, columns, each node
    with its evidence (verbatim fragment, offset, line, column). Saved in
    AIVIA_01_Data/02_emr_data_dictionary/02_sql_extraction.json.
    The EMR tables/columns/joins-observed lists are DERIVED from the tree,
    never a second parse. Name resolution is a separate pass that reruns
    against the data sheets when they arrive or change; only a text change
    pays the parser. Anything unclassified is counted remainder, never dropped.
    Write sql extracts based on the tables and columns used.

L04: The dictionary extraction, in moves (details ruled in the data contract):
    - Discovery: satisfied by my hand — dictionary shapes pasted, recorded in
      02_emr_data_dictionary_discovery_facts.md.
    - Move 2: a script generates FIVE standalone queries from the discovery
      facts + the derived census — table, column, join (CLARITY_TBL_FK_ALL,
      composite joins via FOREIGN_KEY_NUM + ORDINAL_POSITION), pk, iniitm.
      Each carries the TBL_DESCRIPTOR_OVR de-dup filter and the used-table
      IN list. I run them and save the five csv files.
    - Move 3: a script generates the category-values queries FROM the join
      csv (FK_ALL's DEST_COLUMN_NAME names each ZC table's id column). I run
      them and save the values csv.
        - Category values, CLARITY_* tables (ruled 2026-09-28): these are category
        tables too, but their columns are not structured like ZC_ tables — so each
        is ruled one by one. The ruled list (id column from the join csv, meaning
        column my ruling):
        CLARITY_BED: BED_CSN_ID -> BED_LABEL
        CLARITY_DEP: DEPARTMENT_ID -> DEPARTMENT_NAME
        CLARITY_EPM: PAYOR_ID -> PAYOR_NAME
        CLARITY_LOC: LOC_ID -> LOC_NAME
        CLARITY_ROM: ROOM_CSN_ID -> ROOM_NAME
        CLARITY_SA: SERV_AREA_ID -> SERV_AREA_NAME
        CLARITY_ADT is NOT a category table (the event data table) — excluded.
        The values query generator obeys this list verbatim; a table not on the
        list and not ZC_ contributes no values. Future category tables join by
        adding a ruled row.
    - The json data sheets: 02_emr_data_dictionary_extraction_table.json,
      _column.json (data_type, pk flags folded in), _join.json (join_id +
      ordinal), _iniitm.json, _value.json. Field lists live in the contract.

L05: A script (build_dictionary_sheets.py) converts the csv files into the
    json data sheets and adds the embeddings — separate name and description
    embeddings per row (ruled). No blanks: a blank description fails loudly.
    Join rows referencing unknown ids fail loudly. Used-but-unmatched objects
    land counted in 02_no_dictionary_match.json. The resolution section of
    02_sql_extraction.json binds the unresolved columns against the column
    sheet — the ruled two-step completes.

L06: Create a local web chat (build on top of the 01_ web chat):
    reads the data sheet json files, embeds the user's question with the same
    model, scores ALL rows by cosine similarity — no early cut.
    Acceptance band = contract parameters (floor / match / margin, starting
    values recalibrated for text-embedding-3-large — the previous build's
    numbers were calibrated on -small and do not transfer).
    Graph stage: adjacency built in memory from the data sheets (join
    sheet = edges); accepted hits are anchors; the answer set is the minimal
    connecting subgraph (union of pairwise shortest paths), gaps and
    relaxations reported, never hidden. All plain Python, local.
    Below-match hits shown as candidates with visible scores — thresholds
    are never cliffs.
    Sunny's hand test cases in test_02_emr_data_dictionary_data_contract_sunny.md
    run against this chat.

L07: ScriptDom per ADR 0001 — native parser only, no fallback; pythonnet +
    DLL facts land in CLAUDE.md operational facts at build time.

L08: The date-dimension rule (ruled 2026-09-28): DATE_DIMENSION stays in
    phase 02. Its joins are not foreign keys and the EMR dictionary
    asserts none — they come from ONE rule, stored as a ruled row, never
    as hand-written edges:
        DATE_DIMENSION.CALENDAR_DT, day grain, joins any column with
        data_type DATETIME through a date conversion.
    The join sheet stays verbatim EMR truth — no rule edge is ever
    written into it. The graph builder applies the rule at EVERY build:
    whenever sql files are added or changed, the builder script reruns
    and re-derives the rule edges from the column sheet's data types
    (196 DATETIME columns today -> 181 edges beyond DATE_DIMENSION's
    own). The rule script is never deleted; stored edges, where a
    runtime needs them (the Fabric edge table), are its regenerable
    output, never its replacement.

    Edge kinds are named by provenance — the standard terms are
    asserted (recorded by the source system) vs inferred (derived by a
    rule):
        joins_by_fk    — asserted by the EMR dictionary; traces to a
                         join-sheet row by join_id.
        joins_by_rule  — inferred from a ruled rule row; this rule is
                         the first. A future rule adds a row, never a
                         code fork.
        joins_observed — evidenced by the sql files' own join
                         predicates; phase 03, the enterprise layer.
                         Not built in phase 02.
    Every edge carries its kind. Every answer names the kind it walked
    ("by dictionary FK" / "by the date-dimension rule").
    Integrity: an edge that cannot be re-derived from a join-sheet row
    or a rule row fails the build. Per-kind edge counts are reported at
    every build, never hidden.


L09: The graph metadata map (ruled 2026-09-29). Every field of every
    sheet has exactly ONE home in this map — a sheet field with no home
    fails the contract check. Nothing rides along undefined.

    NODE KINDS
    table  — key table_id (verbatim EMR). Properties: database_name,
             schema_name, table_name, table_description, deprecated_yn,
             name and description embeddings. 38 today.
    column — key column_id (verbatim EMR). Properties: column_name,
             data_type, is_primary_key, key_ordinal, column_description,
             deprecated_yn, column_ini, column_item, name and
             description embeddings. 1,618 today.
             Columns are nodes BY RULING even though no phase 02 edge
             terminates at them: phase 03's edges (vocabulary term ->
             column, joins_observed, lineage) do, and the graph keeps
             one shape across phases. (Reworded 2026-10-05 per the
             vocabulary keyword law, Design_Proprietary_Term_Assets:
             "business term" is reserved for the phase 09 governance
             object; these chat edges carry healthcare vocabulary.)
    iniitm (ruled): line 1 only becomes the column_ini/column_item
             properties. Columns with more lines (38 today, the
             date+time item pairs and multi-source derived columns) are
             COUNTED at every build — dropped rows (45 today) land in a
             ledger, never silently. A column without iniitm (155
             today) is legal and counted, never a failure.

    EDGE KINDS (all table -> table except has_column; provenance per L08)
    has_column     — table -> column, derived from the column row's
                     table_id, never stored separately. The only edge a
                     column node has in phase 02.
    joins_by_fk    — table -> table, keyed by join_id, ONE edge per
                     join carrying its ordered column pairs as edge
                     properties (composite joins are one edge by
                     construction — reassembly is structural, never a
                     runtime step) plus conditional_c, may_be_stale_c,
                     is_current_data_model_yn, is_supplemental_yn.
                     210 edges today from the destin_in_scope rows.
    joins_by_rule  — table -> table, keyed by rule name + source
                     column_id, one edge per matched column (parallel
                     edges between the same table pair are distinct
                     joins — admission date and discharge date are
                     different hops). 181 today from the date rule.
    joins_observed — phase 03. Not built here.
    Join grain ruling: joins are table-level relationships with the
    column pairs as the relationship's definition (the ER /
    INFORMATION_SCHEMA / semantic-model standard). Column-to-column
    edges are the LINEAGE idiom and belong to phase 03.

    CATEGORY VALUES (ruled)
    Values are properties under the MEANING column node (ZC NAME
    columns; the ruled CLARITY meaning columns) — "cancelled" must land
    on the column whose text it is. code rides on every value row: the
    matched meaning supplies the filter caption (meaning 'Left Against
    Medical Advice' -> ZC_DISCH_DISP code 7 -> the referencing fact
    column = 7). 14,476 rows over 20 tables today.
    Values ARE embedded — one embedding per row, meaning text only,
    same model, same acceptance band. This supersedes the contract's
    "no embeddings on values this phase" line; iniitm stays unembedded.
    Embeddings live in a SIDECAR file
    (02_emr_data_dictionary_extraction_value_embeddings.json, keyed
    table_name + code); the value sheet stays readable.

    SEARCH AND TRAVERSAL (the grain rules)
    Search scores the question's embedding against ALL embedded rows —
    table names/descriptions, column names/descriptions, value
    meanings — one band, no early cut. Accepted anchors resolve to
    their owning TABLE node (a column anchor through has_column, a
    value anchor through its meaning column's table). Traversal walks
    table nodes over the join edge kinds. Answers cite back DOWN the
    grain: the exact join columns from the edge, the column
    descriptions, the value code for filters. Every answer names the
    edge kind it walked.

    PROMOTION RULE (standing)
    A thing becomes a node in the phase that builds the first edge
    terminating at it. Columns crossed that line by phase 03's needs;
    values may cross it there too (term -> value); iniitm items may
    cross at the workflow layer (127 (ini,item) pairs already appear
    under multiple columns — same source item, a candidate inferred
    edge). Until crossed: properties.

    CONTRACT AMENDMENTS this ruling requires (the doc lags the build):
    - table.json and column.json field lists add deprecated_yn (built
      files already carry it, per the rides-along ruling).
    - column.json field list adds column_ini, column_item.
    - The values "no embeddings this phase" line: superseded for
      values, stands for iniitm.
    - value.json keying by table_name (not ids) is BLESSED with reason:
      values are generated from the join csv's name columns and ZC
      codes have no dictionary ids of their own; names are unique
      in scope.

    INTEGRITY CHECKS (each row of this map is one test)
    - node keys unique; descriptions non-blank; embeddings length 3072;
      deprecated_yn in {Y,N}; data_type in the observed set.
    - every column's table_id resolves; has_column count = column rows.
    - every joins_by_fk edge re-derives from destin_in_scope join rows;
      ordinals contiguous from 1 per join_id.
    - every joins_by_rule edge re-derives from the rule row + data
      types alone.
    - every value row's table resolves in scope (ZC_* or the ruled
      CLARITY list); codes unique per table; every value row has a
      sidecar embedding and vice versa — counts match exactly.
    - iniitm ledger count + kept count = iniitm csv row count.
    - connectivity: one component, or every extra component named with
      a reason.
    - per-kind node and edge counts reported at every build.




