08_pbi_lineage.md

Status: DRAFT for Sunny's ruling pass — scribed by Claude
2026-10-04 at her "follow our process" word. Prior art: the old
estate's devtools/pbi_extract.py (M7, "approved" 2026-09-17) and
the DevOps-lineage fact (TMDL = deterministic column-level
truth). Nothing builds until she stamps the decisions below.

Design description:
- Phase 08 links Power BI reports to the SQL files that feed
  them, deterministically, from the semantic models' TMDL text —
  no API archaeology, no LLM, no network. A report's model, as
  it lives in a DevOps checkout (or one REST getDefinition
  fetch), is a folder of plain table files; each table file
  names its source (the EXEC'd proc, the view, or the DirectLake
  entity) and the columns the model imports. This phase reads
  those files against the 01 corpus and writes the link table.
- The product fact this serves: "which report does this proc
  feed, and which of its columns does the report actually use" —
  lineage a clinician-facing description can later cite, and the
  first stone of Phase III impact answers.

The decisions (each for her stamp):

D1. BINDING KINDS IN SLICE 1 — three patterns, each row stamped
    with its binding_kind:
    (a) exec:      `EXEC schema.proc` in an import partition
                   (the prior estate's proven pattern)
    (b) entity:    `entityName: X` (DirectLake partitions)
    (c) source:    the M source object for view/table-fed import
                   partitions (Sql.Database(...){[Name="X"]} and
                   the schema-qualified forms)
    DAX calculated columns stay OUT (the prior estate's recorded
    deferral, carried).

D2. RESOLUTION — a binding resolves against the 01 subject
    corpus by schema/name, case-insensitive, brackets stripped
    (the prior resolve() law). Unresolved bindings are COUNTED
    rows in the ledger, never dropped, never guessed.

D3. NO SYNTHETIC SHELLS — divergence from prior art, named: the
    sepsis estate minted a fake report per uncovered proc
    because its test corpus demanded full coverage. AIVIA_01
    records only REAL models; procs no report touches appear in
    the coverage ledger as unconsumed, honestly.

D4. PLUMBING EXCLUDED — LocalDateTable_* / DateTableTemplate_*
    auto-tables skipped by rule (carried).

D5. THE GRAPH STAYS CLOSED THIS SLICE — the output is the 08
    artifact only. Minting pbi_report nodes and executes edges
    in the 05 graph is slice 2, its own contract amendment,
    ruled when she opens it.

D6. PORTABILITY — the extractor is engine code: stdlib-only,
    zero keys, zero network; a candidate for the deterministic
    work wheel's allowlist (Brief_Packaging) at her word. Work
    TMDL and work SQL parsed by it NEVER enter this repo (the
    work_* guard stands).

D7. HOMES — code: AIVIA_01_Code/pbi_lineage.py (one file).
    Data: AIVIA_01_Data/08_pbi_lineage/ (machine-written
    outputs per the contract). Tests: fixtures are SYNTHETIC
    TMDL with invented names only — no customer text ever in
    the fixture (the estate boundary).

D8. THE END-TO-END PROOF (RULED 2026-10-04, Sunny in chat, at
    the stamp: "use my personal Fabric to test the .wheel, and
    start from PBI reports"): after the build, the acceptance
    run happens on HER PERSONAL FABRIC tenant with the
    deterministic wheel (Brief_Packaging) — the full chain in
    one pass: PBI reports' TMDL in -> phase 08 finds their
    linked sql files -> the deterministic engine (06) parses
    and describes them -> ONE OUTPUT FILE: per PBI report, the
    report name + the description of what feeds it
    (08_report_descriptions, shape in the contract). Riders:
    (a) the wheel's allowlist (Brief_Packaging) GAINS
        pbi_lineage.py and the end-to-end command — amended
        there this same day;
    (b) personal tenant only — the capacity law stands (her
        hand or her word per run), and this proof is the work
        wheel's dress rehearsal: same wheel, her tenant first,
        work only after it proves out;
    (c) her gap-check of that output file IS the phase's
        acceptance (supersedes the bare reports-json gap-check
        in the test doc).
