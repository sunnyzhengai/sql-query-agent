# Brief_Pilot_Build_1 — the pilot fixes ship: intake hardening (A) · three-part resolution (A2) · the estate manifest step (B)

**Status: BUILT** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED; BUILT 2026-09-20 — suite 776/0 (10:59), ruff zero new, closing check BALANCED 27==27 with the parent brief's three files; CLOSED at Sunny's work re-run on the 2.3.0 wheel) —
the first of the three ship-unit briefs ruling (7) of
Brief_Pilot_Findings_R1 ordered ("i agree, three briefs", Sunny
2026-09-19: brief 1 = A+A2+B, fixes, no stored-text change, one
wheel release; A2 first-and-fast — it unblocks honest re-testing of
the work estate). Every ambiguity these slices stand on was ruled in
the parent brief — rulings (4), (5), (8), each quoted there. The go
to build: Sunny, 2026-09-20 — "can you fix the findings".

| field | content |
|---|---|
| class | fix ×3 — code returns to ruled design: A to the error-contract law (every refusal names its rule; Contract_Technical_Layer F6/F7), A2 to the resolution design (bind on schema via reg.schema_sources; F9), B to the turn-key census (FR8 — no undocumented human step; F8) |
| claims | Contract_Technical_Layer F6 · F7 · F8 · F9, carrying Brief_Pilot_Findings_R1 rulings (4) new ids INTAKE-14/15 · (5) the manifest template, option c · (8) the db part counted-never-refused, option b |
| impacts (step-2 query) | writer touched: kg1_intake.load_snapshot (the ONE extract reader) gains utf-8-sig + INTAKE-14/15; NO stored field changes writer or shape — served/Fabric data UNCHANGED, no load, no regen. Consumers of intake reads: flows.inbound (receive_estate/receive_pbi/receive_descriptions), console.build_store, fabric_run.extract_scripts, flows.glossary — all re-pointed at the one read helper. Consumers of resolution: join_render, condition subjects, owner-possessive — all recover downstream of A2 with zero renderer change (FL12's voice half stays open for brief 2). Tests: new test_intake_hardening.py + test_three_part_resolution.py (RED first); existing intake/mapper/estate suites re-verify byte-identical behavior on BOM-less, db-less inputs |
| ambiguities | NONE OPEN — all inherited rulings quoted in Brief_Pilot_Findings_R1: (4) "i agree, new ids" → INTAKE-14 (exists-but-unparseable, path + parse error) · INTAKE-15 (CSV headers mismatch, expected vs found, per file); (5) "i agree with option c" → extract_scripts writes estate_snapshot/manifest.json with location + default_schema filled and as_of EMPTY; intake refuses on empty as_of with "fill in the date this estate SQL was captured" (INTAKE-17) and on the missing manifest (INTAKE-16) — the refusal is the template's tripwire per the placeholder law; (8) "i agree with option b" → registered db == ref's db binds (the match IS the cross-check passing) · != stays unresolved, COUNTED as a cross-database read with the db named · db_name omitted → schema-only binding per the waiver, census reports distinct db names seen. Build-level readings, recorded not asked (no design question in either): the template NEVER overwrites an existing manifest.json (a filled as_of is the human's data); the header check requires the contract's headers and TOLERATES extras (the pack's extras-tolerated law + the rider-(c) optional data_type) |
| debt declared | none — FL12's fragment voice, FL9–FL18 ride briefs 2/3 as ruled |
| retirement (pivots only) | none — fixes; no direction supersedes |
| does this promote? | at close, at Sunny's word (suite green + zero era-collisions first) |
| Sunny's approval | ruling (7) pre-split the ship units at the parent's approval; the build go is his "can you fix the findings" (2026-09-20) |
| closing check | BALANCED (2026-09-20): 27 files changed == 27 declared (this brief's 24 + the parent record's Brief_Pilot_Findings_R1 / Contract_Logic_Layer.md / its own Contract_Technical_Layer share); suite 776 passed / 0 failed (10:59); ruff zero new offenses (the 18 remaining pre-exist in untouched files); wheel sha256 e9915abe… carries pack.json, 2.2.0 retired. RIDERS born at build, landed same breath: the elided-schema re-base (measured, story in expected_shakedown.json) · F11 (4-part server residue, OPEN) · F12 (the coerced-shape generator + the closed-shape proposal, OPEN — Sunny's ruling) |

## The build, in order

1. **Tests first (RED)** — tests/aisql/test_intake_hardening.py:
   BOM'd manifest.json loads · malformed JSON → INTAKE-14 naming the
   path · BOM'd CSV keeps its first header · headerless CSV →
   INTAKE-15 expected-vs-found · missing estate manifest → INTAKE-16
   · empty as_of → INTAKE-17 with the ruled sentence ·
   extract_scripts writes the template (location + default_schema
   filled, as_of "") and never clobbers · a BOM'd .sql still parses.
   tests/aisql/test_three_part_resolution.py: SIMDB.dbo.<table>
   resolves (RED today) · OTHERDB.dbo.<table> stays unresolved and
   lands in cross_database_reads with the db named · db_name-less
   registration binds on schema and reports db_names_seen.
2. **A** — kg1_intake gains `read_json` (utf-8-sig + INTAKE-14) and
   `CSV_HEADERS` (INTAKE-15); every intake text read re-points:
   inbound (estate manifest, .sql files, pbi manifest/reports,
   descriptions.json), console.build_store (registration, snapshot
   manifest peek), glossary (blessings/entries), fabric_run
   (estate .sql).
3. **A2** — resolve_scope splits ≥3-part names db · schema · table;
   ruling (8) wired into the census.
4. **B** — extract_scripts writes the manifest template; the
   default_schema vendor fact lands as
   AIVIA_Product/source_packs/clarity/pack.json (ruling (6)'s
   principle: vendor knowledge lives IN the pack); build_wheel +
   the wheel pin carry it; the runbook's Fabric route and estate
   scaffold name the one human field.
5. Contract rows + INDEX + ledger, same breath; full suite + ruff;
   wheel 2.3.0 (one-current-wheel law: 2.2.0 retires).

## The build's own find — the elided-schema class (measured re-base)

The A2 rewrite recovered a class the corpus REALLY contains beyond
db-qualified names: `FROM .HOSPITAL_ENCOUNTERS` (reports/
USP_RPTS_IP_SEPSIS.sql) — legal T-SQL, the empty schema part means
the default schema; the old splitter built the unresolvable lookup
key `""` and five such table reads sat in the unresolved count.
VERIFIED ref-by-ref (old vs new bindings diffed): +25 resolved =
5 elided-schema tables + the 20 alias-qualified columns they
disambiguated; unresolved 132→127, ambiguous 37→17, twin
coverage_gaps 700→680, working_set_touched 73→74 (BED_CONFIG was
read ONLY through the elided ref). expected_shakedown.json re-based
BY MEASUREMENT with the story in its _comment; the dated
gap_check_report.md (his 2026-09-06 verdict record) stays verbatim
— history, never current law.

## Files declared

(the 2.2.0 wheel line is a DELETION — retired per the
one-current-wheel law; every other line is an edit or a birth)

    AIVIA_Design/briefs/Brief_Pilot_Build_1.md
    aisql/graph/kg1_intake.py
    aisql/flows/inbound.py
    aisql/flows/glossary.py
    aisql/console.py
    aisql/graph/kg2_mapper/__init__.py
    aisql/fabric_run.py
    AIVIA_Product/source_packs/clarity/pack.json
    AIVIA_Product/source_packs/clarity/README.md
    tests/aisql/test_intake_hardening.py
    tests/aisql/test_three_part_resolution.py
    tests/aisql/test_wheel_boot.py
    devtools/build_wheel.py
    pyproject.toml
    CHANGELOG.md
    dist/sql_query_agent-2.3.0-py3-none-any.whl
    dist/sql_query_agent-2.2.0-py3-none-any.whl
    AIVIA_Design/Contract_Technical_Layer.md
    AIVIA_Design/Contract_Source_Packs.md
    AIVIA_Design/L1_KG1_CONTRACT_DATALOAD.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Manifest_Build.md
    pilots/work_dryrun/README_Runbook.md
    AIVIA_Product/estates/sepsis/expected_shakedown.json
    docs/architecture/TEST_MAP.md
