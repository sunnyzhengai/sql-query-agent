09_business_terms_data_contract

Status: DRAFT — rides the 09 design doc's decisions D1-D8;
complete BEFORE the first red test per the amendments-first
law. Scribed by Claude 2026-10-05; Sunny owns it.

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- AIVIA_01_Data/05_semantic_graph/05_scope_sheet.json — the
  scopes, their kinds, their structures (read only).
- AIVIA_01_Data/06_technical_descriptions/
  06_description_sheet.json — the scope sentences and the
  predicate/condition rows the technical definition re-voices
  (read only).
- AIVIA_01_Data/02_emr_data_dictionary/ — the business names
  for tables and columns (the D4 voice law's source).
- AIVIA_01_Data/07_business_descriptions/
  07_blessing_registry.json — blessed names in, proposals
  recorded back (the D5 flow).
- AIVIA_01_Data/08_pbi_lineage/08_pbi_reports.json — the
  (sql file -> PBI report) tie; a scope's report rows come
  from its file's executes entries (D6).

Run parameters:
- only_file (ruled 2026-10-05, her ask): limits a run to one
  corpus file for cheap iteration; the outputs then hold that
  file's rows only. The full-estate run (no filter) is the
  one that ships to Fabric.

What is the output of this data contract?

THE CONSOLIDATION RULING (2026-10-05, Sunny: "all we need is a
consolidated file, and each step updates part of it... don't
record what no step consumes and no user sees" + "name it
ai_delivery.json"): the delivery layer is ONE file,
AIVIA_01_Data/ai_delivery.json — reports[] (report + files,
step 08's keys; description text/voice/status, step 07's key;
terms[], step 09's key), reportless_files[] (same shape, no
report tie yet), counts (the conservation equations, one block
per step). Each step rewrites ONLY its own keys, whole and
re-runnable; bless() flips statuses in place; the Collibra
notebook reads this one file and filters bt_name_status ==
blessed itself. RETIRED by this ruling: 09_collibra_export
.json (a pure subset), 09_terms_ledger.json (folds into
counts.09), the standalone 09_business_terms.json sheet (the
terms[] section is the rows' one home). THE ROW DIET (the
consumption rule): report_tie dies (the section says it);
plumbing scopes are NOT rows — they land in counts.09 as a
skipped list ({node_id, reason}), which is also her override
surface; gate_findings/rounds_used recorded ONLY on failing
rows; basis_version once at the file top; scope_kind and
concept_reason leave the term rows (the skipped list carries
reasons; concepts need none).

- AIVIA_01_Data/ai_delivery.json, the terms[] section — one
  row per (scope, report) business concept (D1/D2):
  - node_id: the 05 scope node
  - bt_name: the proposed or blessed name (LLM-proposed from
    the block's meaning, per D5)
  - bt_name_status: proposed | blessed
  - name_collision: null, or the existing normalized name
    this proposal collides with (the D5 uniqueness law; a
    collided row cannot bless until renamed or qualified)
  - business_description: the D3 card (Definition / One row
    is / Keeps / Excludes), newline-separated labeled lines
  - technical_definition: the D4 sections (Population /
    Exclusions / Parameters), one bullet per clause,
    newline-separated
  - blessing: absent until blessed; then Sunny's ruling,
    recorded verbatim (the ratify clause)
  - gate_findings + rounds_used: ONLY on a failing row (the
    consumption rule — a clean row records no empty audit)
  The row's report is its PARENT: a terms[] list under a
  reports[] entry (tied via 08) or under reportless_files[]
  (no 08 tie — never pushed to Collibra until tied).
- counts.09 (in the same file) — the conservation block:
  {scopes_total, plumbing_skipped, concepts, report_rows,
  reportless_rows, blessed, proposed} + skipped: [{node_id,
  reason}] (the D2 verdicts — her override surface).
  THE EQUATION, a test not advice: scopes_total ==
  plumbing_skipped + concepts; report_rows + reportless_rows
  == the term-row count. A red block does not ship.
- No Collibra ids anywhere — her notebook maps report and
  term names to Collibra UUIDs at push time, and filters
  bt_name_status == blessed itself.

Definitions:
- A BUSINESS CONCEPT (D2) is a scope whose sources include at
  least one dictionary table; parameter-only and constant-only
  scopes are plumbing — counted, never exported.
- The POSITIVE/NEGATIVE SPLIT (D4) is mechanical: negative
  predicates (is not, none of, does not exist) land under
  Exclusions; positive predicates under Population.
- NAME UNIQUENESS (D5): names compare NORMALIZED — lowercase,
  punctuation stripped, plurals folded. ai_delivery.json
  carries no two blessable term rows with the same normalized
  bt_name; the check is a test. A collision at proposal time
  lands in name_collision, never silently renamed.
- THE ONE GATE (RULED 2026-10-05, supersedes the 09-local
  shape check): the D3 card is gated by business_descriptions
  .gate — V-1/V-2/V-3/V-7 in full plus the V-4 SCOPE arm
  (four labels, negatives only on Excludes), added to that
  one gate at this build. Phase 09 defines no gate of its
  own; a second gate is a contract violation (test-locked).
  Repair loop budget 3; rows carry status (gate_passed |
  gate_failed), gate_findings (verbatim), and rounds_used.
- THE VOICE LAW (D4, ruled 2026-10-05): the technical
  definition speaks dictionary business voice only — no SQL,
  no table names, no numeric codes; parameters voiced plainly;
  business values (e.g. department names) stay.

Who writes what (authorship)?
- ai_delivery.json: each step machine-writes ONLY its own
  keys (08: reports+files; 07: description; 09: terms +
  counts.09), whole-section, re-runnable. bt_name proposals
  and the D3 card are LLM-written (paid API, per the standing
  law); the technical definition and the counts are
  deterministic — no LLM touches them.
- bt_name_status flips to blessed ONLY by Sunny's hand through
  the 07 blessing-registry flow; the build never blesses;
  bless() edits the row in place.
- This contract and the design doc: Sunny owns; amendments
  follow the amendments-first law.
- The Collibra push: Sunny's notebook, outside this repo; this
  phase ends at ai_delivery.json.
