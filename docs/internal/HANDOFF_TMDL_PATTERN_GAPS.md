# Handoff — TMDL partition patterns: real estates write messier M

> **Status (2026-08-18, dev session): implemented in 1.17.0.**
> All three breakers fixed for Sql.Database AND Odbc.Query (shared _parse_exec_target incl. 3-part bracketed; _M_SOURCE_ARG accepts literal/@param/plain/#\"quoted\" servers; Query= taken as first literal chunk, mid-record position allowed). Bonus from the census guard: Schema/Item navigation now extracts too. Per-file fallout rows land in ops_fallout with classified reason_codes — the 174-silent-models class is structurally impossible. Field patch can be retired on the next wheel. Fixtures mirror the live sample.

**From:** review session, 2026-08-18 (full-estate taxonomy over a live
5-workspace harvest: 601 models, 1065 sources parsed, 174 models yielded
ZERO sources). **To:** dev session. All examples anonymized — shapes only.

## Field taxonomy of the 174 vanished models' partitions

- 203 m:Odbc.Query + 74 m:Sql.Database = 277 SQL-SHAPED sources the
  patterns missed — the dominant fallout, all recoverable.
- ~110 genuinely non-SQL (calculated tables, Folder.Files, Excel,
  Table.FromRows/Combine/NestedJoin, DateTime.LocalNow) — correct to
  skip, must become fallout rows with reasons.
- 21 m:Snowflake.Databases (live Snowflake sources at a real estate —
  connector-roadmap datapoint).
- ~70 mixed/unclassified by the crude field regex (nested lets,
  entity/DirectLake, incremental-refresh 'query' partitions) — the real
  parser's fallout rows should classify these.

## The pattern-breakers (one live sample carried all three)

    Sql.Database(@ServerParam, "SomeDb",
        [Query="exec [SCHEMA_X].USP_Some_Proc '"& StartDate &"' , '"& EndDate &"' "])

1. **Parameter as server argument** (@Name / plain identifier, not a
   string literal) — patterns expecting quoted server miss the call.
2. **Bracketed identifiers** in the EXEC ([SCHEMA].[PROC] / mixed).
3. **String-concatenated Query** ("exec … '"& Param &"' …") — the exec
   target lives in the FIRST literal chunk; extraction must tolerate the
   concatenation tail. Same variants presumably occur in Odbc.Query
   (203 misses there).

## Wanted

1. Extend patterns to cover the three variants above for Sql.Database
   AND Odbc.Query; add fixtures shaped like the sample (anonymized).
2. Per-partition fallout rows (ties to HANDOFF_FUNNEL_AND_FALLOUT):
   every table file yields a source row OR a fallout row with
   reason_code (non_sql_source:<fn> | unrecognized_shape | no_partition
   | directlake_entity ...). The 174-model silent absence must be
   impossible afterward.
3. After shipping: a 12 rerun at a live estate should move most of the
   277 into parsed lineage; the funnel view (when built) will show the
   recovery as a before/after.

## Field patch in production (2026-08-18, disclosure)

A work-side notebook cell implements a scoped version of these fixes
(exec/FROM extraction over pattern-missed Sql.Database/Odbc.Query files,
appending contract-shaped rows to input_report_sources) — deadline-driven
(work meeting). Deliberate, marked in-notebook, and self-sunsetting: the
next proper 12 run on a fixed wheel overwrites its rows. Treat its
recovery count (reported by Sunny) as another acceptance number.
