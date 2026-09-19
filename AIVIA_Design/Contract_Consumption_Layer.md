# Contract_Consumption_Layer — the consumption graph's data contracts

**Status: DRAFT — born WITH the M7 batch (Brief_M7_Consumption_
Governance, Sunny's "approved" 2026-09-17; contracts-first per
his Q5; closes CI-B5's consumption half); populated from the
design + the batch's build; his gap-check flips RATIFIED.**
Fourth document of the contract system (conventions + INVARIANTS
in Contract_Technical_Layer.md). This layer is what CONSUMES the
estate's logic: the BI artifacts that execute it.

## DESIGN_SECTIONS (governing this layer)

| ds_id | says (short) | status | home doc |
|---|---|---|---|
| ds.consumption_vocabulary | consumption = `pbi_report`; edge `executes` (report→file) | RULED | Design_Graph_Engine L2 |
| ds.pbi_mapping | every proc feeds a PBI; reports may be synthetic shells, THE MAPPING IS REAL | RULED 2026-09-08 | the pbi_snapshot manifest (state home rides the CI-B program) |
| ds.report_derived_pair | the report's technical definition = the executed files' catch-alls CHERRY-PICKED to its bound fields + population whole + THE DISCLOSURE LINE; its description = the Scribe's caged summary of that; multi-proc CONCATENATES labeled by proc, one summary | RULED 2026-09-17 (the M7 sitting, Q1/Q3/Q4) | Grammar_Floor §R13 report-grain rider (ratifies at checkpoint 1) + Brief_M7 |
| ds.bound_fields | bound fields = the SemanticModel's imported sourceColumns per EXEC'd proc; date plumbing excluded; model grain (visual grain = THE REPORT-LAYER EXTRACTION, the named future brief) | RULED 2026-09-17 (Q1 "a" + M7-A) | Brief_M7 + the extractor's docstring |
| ds.derivation_ruling | "the report users SHOULD see the logic" — report speech derives from its procs, never separately drafted | RULED 2026-09-09 | Speech_Sources pbi_report row |

## DATA_CONTRACTS

| dc_id | kind | what it is | writer | count (dev / sepsis) | status |
|---|---|---|---|---|---|
| dc.pbi_report | node | one BI report (real TMDL or ruled shell) | PBI intake (reports.json ← the bindings extractor) | 1 / 28 | LIVE (M7 BUILT 2026-09-18) |
| dc.executes | edge | report → the file it executes; unresolved EXEC names stay a COUNTED list, never guessed (2 unresolved, FINAL per "not same") | M7 builder (receive_pbi) | 1 / 28 (measured) | LIVE (M7 BUILT 2026-09-18) |

## CONTRACT_FIELDS

| dc_id | field | writer | rules | checks |
|---|---|---|---|---|
| dc.pbi_report | technical_definition | M7 composer (the cherry-pick) | ds.report_derived_pair · inv.verbatim (stored == recomputed) · THE DISCLOSURE LINE always present | test_report_layer · estate M7 battery |
| dc.pbi_report | description | the Scribe summary, APPROVED only (the M6 file precedent: approved-only, empty counted) | the LLM cage vs the cherry-picked definition · meaning-key anchor | test_report_layer · parity |
| dc.pbi_report | bound_fields (snapshot data) | the bindings extractor (deterministic, from TMDL) | ds.bound_fields; a shell binds nothing → whole-catch-all fallback | extractor determinism pin |
| dc.executes | (unresolved list) | the extractor; alias judgments are DATA (Sunny's eye), never code guesses | inv.no_invented_text posture | counted-unresolved census |

## CONSUMERS

| dc_id | consumer | reads | re-verify |
|---|---|---|---|
| dc.pbi_report | sc.ask_console | description as searchable text | speech parity |
| dc.pbi_report · dc.executes | sc.fabric_export | graph_pbi_report + the executes table (SERVED_LABELS — Q2) | export census |
| dc.pbi_report | sc.collibra_publish (DORMANT) | THE TWO FIELDS — the customer-facing payload (Collibra reads at report grain; files stay lineage) | NONE until the publisher revival brief |
| dc.pbi_report | sc.graph_visual | name · description | FS1 counts |

## GOVERNS

| ds_id | governs |
|---|---|
| ds.report_derived_pair + ds.bound_fields | both dc.pbi_report fields |
| ds.pbi_mapping | the shell census (28 = every proc) |
| ds.derivation_ruling | the derive-never-redraft direction |
| inv.verbatim · inv.one_writer | every field row |

## TESTS

| test_id | proves |
|---|---|
| test_report_layer (M7) | the pair · executes · cherry-pick recompute · the disclosure line |
| estate M7 batteries (dev + sepsis) | counts vs keys, both estates |
| test_graph_export | the served consumption tables |

## FINDINGS (from populating this contract)

| id | finding | kind | status |
|---|---|---|---|
| FC1 | the Screening Trend table carries NO EXEC (a derived/M-transform table) — its columns attribute to no proc and are excluded from bound_fields | measured at the extractor's first run, 2026-09-17 | OPEN — disclosed at checkpoint 1; the report-layer extraction's territory |
| FC2 | EXEC `reports.USP_ED_Sepsis` has no exact corpus match (the corpus file is USP_RPTS_ED_Sepsis.sql) — whether they are the same proc is SUNNY'S knowledge; the machine keeps it counted-unresolved | the no-guessing law working | RULED (Sunny "not same", 2026-09-18): the RPTS files are DIFFERENT procedures — both EXECs stay counted-unresolved as the FINAL truth; no alias data; the multi-proc mechanism stands pinned on a synthetic store, dormant in the estates |
