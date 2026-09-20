# Brief_Closed_Shape — the coerced-shape generator dies: the name grammar in writing, failure classes closed, diagnoses honest

**Status: APPROVED** (DRAFT → PRESENTED → APPROVED → BUILT →
CLOSED) — drafted at Sunny's "i agree with your recommendation,
draft the brief" (2026-09-20, ruling F12); APPROVED the same day
at his "agree with F11, approved, and push" — both ambiguities
now carry his word, none open.

| field | content |
|---|---|
| class | unplanned addition (a new standing law for consumers of estate-authored input) + update (the resolution census — a DECIDED structure — gains the closed diagnosis enum) + fix (F11: the dropped server part returns to the counted-never-coerced posture F9 established) |
| claims | Contract_Technical_Layer F11 + F12 (RULED 2026-09-20: "i agree with your recommendation, draft the brief" — proposals 1+2+4 as one brief, 3 as the wording rule, shape_unrecognized = suite-fail on pinned corpora / counted with honest words on customer runs) · the error-contract law · the F9/ABX generator find (a shape the code never anticipated is coerced into the nearest known shape and lands in a catch-all with no cause — fired twice, so per the Echo Law the mechanism builds) |
| impacts (step-2 query) | ONE WRITER each: kg2_mapper.resolve writes resolution_census (gains the closed diagnosis class per unresolved_detail row + shape_unrecognized + the F11 server-part keys); flows.inbound.write_intake_result_tables is the ONE renderer of the unresolved_references sheet (gains the wording rule — customer-blaming sentences only for fully-understood classes). CONSUMERS: the intake report/result sheets (DBA-facing — wording changes, no stored graph field changes); expected_shakedown.json (gains the per-class table, MEASURED); NO stored node/edge field changes → NO load, NO export regen, verbatim law untouched. The contract home: THE NAME GRAMMAR table lands in Contract_Logic_Layer (resolve is the logic layer's writer). Tests: new tests/aisql/test_name_grammar.py (the conformance pin, RED-first for the 4-part row) + shakedown per-class re-base + TEST_MAP regen. Wheel: rides the NEXT release word (no churn before his 2.3.0 re-run; the census/wording changes are engine-side and wait fine) |
| ambiguities | (1) RULED (Sunny "agree with F11", 2026-09-20) — the 4-part linked-server name `server.db.schema.table` follows the ruling-(8) symmetry, counted-never-refused — registration's server (optional per MR1a) matches, folded → binds, the match IS the cross-check; declared and DIFFERS → unresolved, counted cross_server_reads with the server named (a linked-server read is by definition another machine's data — binding it to local tables would be a wrong claim); server not declared in the registration → binds on db/schema/table per the waiver pattern and census.server_names_seen reports the names, so the waiver is visible. (2) RULED IN THE PARENT (F12, quoted above): the shape_unrecognized lane split — pinned corpora = suite failure (builder's problem, before it ships); customer runs = counted, the sheet says "AISQL could not read this reference shape — engine finding, report this to AISQL", the boot proceeds (error-contract philosophy: the repeat count across customers is the product signal) |
| debt declared | none — every slice lands whole; the conformance pin's 4-part row is RED-ready the day ambiguity (1) is ruled (no 4-part refs exist in current corpora, so the pin proves the RULED behavior, not a live corpus case) |
| retirement (pivots only) | none — the free-text diagnosis strings inside write_intake_result_tables are REPLACED by the enum-driven forms in the same act (no old direction left standing) |
| does this promote? | at close, at his word |
| Sunny's approval | "agree with F11, approved, and push" (2026-09-20) — both rulings quoted above |
| closing check | files changed == files declared (filled at CLOSED) |

## The slices, in build order

1. **THE NAME GRAMMAR table (proposal 1)** — a new section in
   Contract_Logic_Layer: Microsoft's documented T-SQL object-name
   grammar, 1–4 dot-separated parts, inner parts may be empty —
   FINITE, so the table is exhaustive by construction. One row per
   arity × empty-part case, each naming its RULED bucket (bind ·
   bind-via-default_schema · cross-database counted · cross-server
   counted (amb. 1) · unresolved-with-class). The customer defines
   NOTHING; ScriptDom already refuses arity ≥5 at parse time.
2. **The closed diagnosis enum (proposal 2)** — the classes, in the
   contract and in code as ONE literal (schema-not-mapped ·
   table-not-in-dictionary · cross-database · cross-server ·
   elided-schema-no-default-declared · reader-writer-drift ·
   shape-unrecognized); every unresolved_detail row carries exactly
   one; resolution_census gains unresolved_by_class counts;
   expected_shakedown.json pins the per-class table (MEASURED — a
   class at 100% failure is visible at a glance).
3. **The wording rule (proposal 3)** — write_intake_result_tables
   maps class → sentence; customer-blaming words (drift, missing
   metadata) fire ONLY for fully-understood classes;
   shape-unrecognized prints the engine-finding sentence verbatim.
4. **The conformance pin (proposal 4)** — test_name_grammar.py: the
   generated arity table over F1's ENCOUNTER (bare · dbo. ·
   bracketed · SIMDB.dbo. · SIMDB.. · leading-dot · OTHERDB.dbo. ·
   4-part), each asserting its ruled bucket; plus the standing pin
   shape_unrecognized == 0 over the sepsis and F2 corpora.
5. **F11 lands (per ambiguity 1's ruling)** — the server part is
   examined, never dropped; RED-first via the 4-part conformance
   row.

## Files declared

    AIVIA_Design/briefs/Brief_Closed_Shape.md
    AIVIA_Design/Contract_Logic_Layer.md
    AIVIA_Design/Contract_Technical_Layer.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Manifest_Build.md
    aisql/graph/kg2_mapper/__init__.py
    aisql/flows/inbound.py
    tests/aisql/test_name_grammar.py
    AIVIA_Product/estates/sepsis/expected_shakedown.json
    docs/architecture/TEST_MAP.md
