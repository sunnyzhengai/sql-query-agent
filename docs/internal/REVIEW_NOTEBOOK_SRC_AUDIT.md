# Review — pipeline notebooks: code that belongs in src/

**From:** dev session, 2026-08-18 (Sunny asked: "is there any code in the
notebooks that is better off in src/?"). Full read of all 19 pipeline
notebooks against the house standard: notebooks are thin orchestration
shells (config, spark I/O, calls into tested src/ steps, display);
anything with a policy or a branch belongs in src/ with tests.

**Overall verdict:** the derivation notebooks (02–05, 10, 12) are in
excellent shape — genuine thin shells. The findings cluster in the
ACQUISITION routes (00a–00e, newest, built fast) and in two config
blocks that bypass the validated Config model. Ranked:

## High — real drift/correctness risk

1. **Two implementations of object identity (00a vs 00b).**
   00a uses `extract_object_identity` (src/parser/identity.py); 00b
   re-implements the same concern as an inline CREATE-header REGEX in
   PySpark (`ident = r"(?i)CREATE\s+..."`). Two authorities for the same
   contract = the normalize-early/enumerate-all-cases bug class. Fix:
   collect to driver (corpora are small) and run the same src function,
   or at minimum move the regex constant into src/parser/identity.py so
   there is ONE spelling. (HANDOFF_INGESTION_ROUTES already wants
   parse-based identity — that upgrade would collapse this.)

2. **`llm:` and `search:` config blocks bypass load_config (07, 11).**
   Both notebooks read org_config.yaml with raw `yaml.safe_load` because
   `LlmConfig`/`SearchConfig` don't exist in src/config.py. They get no
   pydantic validation, no example-yaml consistency, and misspellings
   fail at use-time instead of load-time. Fix: add both models to
   Config; notebooks go through `config.llm` / `config.search`.

3. **00c hand-builds StructType schemas that mirror contracts.**
   Cell 3 hand-writes the 7-column input_sql_sources schema (with a
   comment admitting it "MUST match the contract") and Cell 4 hand-writes
   the tracking schema — while EXTRACTION_TRACKING exists in
   TABLE_REGISTRY and 00a already uses `to_spark_schema(SQL_SOURCES)`.
   Contract changes silently drift 00c. Fix: `to_spark_schema` both.
   Same class: 07b hand-builds desc_schema instead of
   `to_spark_schema(AGENT_DESCRIPTIONS)`.

4. **00e merge precedence is not actually guaranteed.**
   "Primary rows win on duplicates" is implemented as
   `unionByName(...).dropDuplicates([...])` — Spark's dropDuplicates
   keeps an ARBITRARY row per key across partitions; union order is not
   a contract. Small dictionaries usually work; nothing enforces it.
   Fix: pure merge function in src (dict-based, explicit precedence,
   tested), notebook feeds it collected rows.

## Medium — policy living untested in notebooks

5. **00a Cell 1 row-assembly loop** (~40 lines): walk, read, identity,
   filename-fallback policy, skip collection. The filename-fallback
   ("no CREATE header → filename becomes metric_id") is a POLICY with no
   test. Fix: `src/steps/ingest_filedrop.py` pure function
   (files → rows/skips/collisions), notebook does I/O only.
6. **00d CSV validation** (~40 lines duplicated for tables/columns):
   required-column checks, warn-vs-fatal policy, empty-DESCRIPTION fill.
   Fix: one validated loader function in src, called twice.
7. **01 Cell 2 coverage-preview regex**: a second, weaker table-ref
   extractor with a hand-maintained keyword stoplist — text-based
   extraction (the banned kind), acceptable only because it's labeled a
   preview; still belongs in src with tests so the stoplist has an owner.
8. **09 Cell 3 MetadataRecord composition**: description assembly
   (append source tables/details), properties dict — content policy for
   what Purview displays, untested. Fix: `purview_records(metrics)` in
   the adapter or a step module.
9. **13 Cell 1 agent-description overlay loop**: encodes the precedence
   contract "07b beats 07" as an inline loop. Fix: small tested function
   in src/steps/agent_descriptions.py.
10. **06 Cell 5 threshold values** (0.90/0.80/0.70) are policy pinned in
    a notebook; the assembly around them already lives in readiness.py.
    Fix: move defaults into src/steps/readiness.py (org_config override
    later if customers need it).

## Low — worth folding in on next touch

11. **02 `read_source()`**: three-branch source resolution (csv/path/
    table) — unused flexibility; delete or move to src.
12. **12 skip-note mapping** (`{"not-exportable": "expected...", ...}`):
    remediation text for collector skip classes lives in the notebook,
    classification lives in src — they can drift. Move next to the
    classifier. (Superseded by fallout-row work — reason text becomes
    contract data.)
13. **02/06 report formatting** (worst-5 suppressions, top-errors,
    funnel labels): candidates for `summary_lines()` methods on the
    step results, pattern already used by 07b.

## Clean bills of health

03, 04, 05, 10 are model thin shells. 02's ScriptDom CLR init MUST stay
in-notebook (runtime-specific). The `try: import src` boilerplate and
precondition/postcondition gate calls are correct notebook-side code.

**Status (2026-08-18): filed. Items 1–4 are release-sized fixes; 5–10
fold into their notebooks' next planned touches (ingestion-routes
upgrade, funnel retrofit). Item 12 is absorbed by HANDOFF_FUNNEL_AND_FALLOUT.**
