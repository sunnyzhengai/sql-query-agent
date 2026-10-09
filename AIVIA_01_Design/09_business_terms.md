09_business_terms.md

Status: D1-D8 STAMPED 2026-10-05 (Sunny, in chat: "i agree
with all your points"). Scribed by Claude 2026-10-05 from the
GOALS session (00_Architecture.md); Sunny owns it. Serves GOAL
2 (Business Terms for Collibra) and rides GOAL 1's voice laws.
Consistency sweep run 2026-10-05: the 07 contract's SCOPE arm,
the 07 design doc's must-says block, and brief Q4's landing
clause re-pointed to this phase's build.

THE KEYWORD (RULED 2026-10-05, the vocabulary keyword law,
Design_Proprietary_Term_Assets.md): BUSINESS TERM is reserved
for this governance object — the specific meaning of a finite
data set, defined in a SQL logic block, specific to the org's
reality. Two origins: user-defined manually (a future phase's
intake) or auto-extracted from SQL (this phase). Healthcare
VOCABULARY (words and meanings from vendor dictionaries, org
SQL, industry files) is the separate broad asset; terms SPEAK
vocabulary, they are not vocabulary.

Design description:
- Phase 09 turns parsed scopes into Business Term proposals for
  Collibra. Each term carries a name, a business description, a
  technical definition, and the PBI report it ties to. The
  output is a data file Sunny's notebook reads to call Collibra
  APIs — this repo never talks to Collibra.
- The product fact this serves: the whole organization reads in
  Collibra what a report includes and excludes, and whether it
  is the right report — without asking a BI developer to read
  and translate the SQL.

The decisions (each for her stamp):

D1. THE UNIT — a Business Term is one scope of one PBI report:
    one row per (scope, report) pair this phase. A SQL file
    feeding several reports yields one row per report. Dedup
    across reports (one concept, many assets) is a future
    phase, its own ruling.

D2. THE BUSINESS-CONCEPT RULE — mechanical, no LLM: a scope
    whose sources include at least one dictionary (EMR) table
    is a business concept and becomes a term candidate; a scope
    reading only parameters or constants (e.g. the
    STRING_SPLIT(@param) chooser lists) is plumbing and is
    counted, not exported. Every candidate row carries
    is_business_concept + the reason; Sunny's bless pass (D5)
    is the human backstop and may override.

D3. THE BUSINESS DESCRIPTION — the scope card, labeled lines:
    Definition (one glossary sentence — what this population
    IS), One row is, Keeps, Excludes. This is the 07 contract's
    SCOPE arm landing (THE SCOPE MUST-SAYS, ruled 2026-10-04):
    ONE ROW IS always; KEEPS only where the scope owns
    membership conditions, honest silence otherwise; a scope
    speaks only its own WHERE. The tone law (clinician's voice)
    and the line-ownership law (negatives live ONLY in
    Excludes) apply.
    THE ONE GATE (RULED 2026-10-05, her ruling: "can we use
    the same algorithm/method for both sql file and BT
    descriptions" — SUPERSEDES this decision's original
    09-local shape check, which shipped 2026-10-05 and leaked
    SQL into the first real cards): the card is checked by THE
    ONE 07 GATE — business_descriptions.gate — whose
    grain-agnostic laws apply in full (V-1 grounded values,
    V-2 never-list, V-3 SQL register and @tokens, V-7
    restriction anchoring), plus a V-4 SCOPE arm added to THAT
    gate at this build: the four labels in order, negatives
    only on Excludes. Phase 09 ships NO gate of its own — one
    gate, one law, two consumers (test-locked). The prompt
    rides business_descriptions.SYSTEM_PROMPT (tone,
    one-home-per-fact, say-the-choice-not-the-mechanism) plus
    the scope-card instruction and the D5 name instruction.
    THE REPAIR LOOP: budget 3, the 07 _propose_loop pattern —
    named findings return to the proposer; still failing after
    3 -> status gate_failed, findings kept. (The original
    one-round debt is RETIRED: its named Echo trigger — the
    first real gate_failed on the census corpus — fired on
    run 1, 2026-10-05, twice.)

D4. THE TECHNICAL DEFINITION — deterministic, no LLM, complete:
    three labeled sections, one bullet per predicate clause —
    Population: (positive conditions)
    Exclusions: (negative conditions — is not / none of / does
      not exist; the split is mechanical)
    Parameters: (each run-time parameter, voiced plainly, with
      its default status)
    Voice law (her ruling 2026-10-05): dictionary business
    voice ONLY — no SQL, no table names, no numeric codes;
    parameters voiced plainly (@StartDate -> "the chosen start
    date"). Business values (department names) stay. No Source
    section, no Carries section. Complete-versus-summarized is
    the distinction from D3: the technical definition lists
    every condition, values intact, and regenerates free when
    the SQL changes; the card is the readable summary.

D5. THE NAME (AMENDED 2026-10-05, her ruling: "the LLM propose
    a name based on the meaning of the sql block... make sure
    it's unique") — the LLM proposes a business name FROM THE
    MEANING of the SQL block (the scope's card and technical
    definition are its input — the name says what the
    population IS, never echoes the SQL). THE UNIQUENESS LAW:
    before a proposal lands, it is checked against every
    existing name (blessed and proposed, normalized —
    case/punctuation/plural folded); an exact or similar
    collision is flagged on the proposal row with the
    colliding name, and the proposer must qualify (e.g. the
    report context) or the row waits for Sunny's hand. The
    export never carries two terms with the same normalized
    name — a test, not advice. Sunny blesses through the 07
    blessing-registry flow; only blessed names reach the
    export. No unblessed name ever ships to Collibra.

D6. THE DELIVERY (AMENDED 2026-10-05, the consolidation
    ruling: "all we need is a consolidated file... name it
    ai_delivery.json") — ONE file, AIVIA_01_Data/ai_delivery
    .json; each step updates only its keys (08: reports +
    files; 07: the description; 09: terms + counts.09); the
    separate export, ledger, and standalone sheet are
    RETIRED. Blessed-only filtering is the notebook's act at
    push time, as is mapping names to Collibra UUIDs — no
    invented ids, no Collibra ids in the build. The (scope ->
    report) tie rides phase 08's lineage; files no report
    touches live under reportless_files[], counted, never
    silently dropped and never pushed.
    AMENDED 2026-10-08 (the delivered-goods ruling, wheel
    0.7.0 — full text in the 09 contract): membership is
    LEDGER-ONLY (a file appears only after its paid turn;
    waiting files appear nowhere — the 06 sheet is the
    whole-corpus view); a report entry appears from its
    first described file and carries files_described[] +
    files_waiting[] (empty waiting == complete; the push
    notebook skips incomplete); the file is renamed
    12_ai_delivery_output.json + .txt per the naming law.

D7. HOMES — code: AIVIA_01_Code/business_terms.py (one file).
    Data: AIVIA_01_Data/09_business_terms/ (machine-written per
    the contract). Tests: AIVIA_01_Test/
    test_09_business_terms_data_contract.py + the _sunny.md
    manual cases. LLM calls (D3 card, D5 name proposals) are
    paid API calls per the standing law; D4 never calls one.

D8. ACCEPTANCE — the census corpus runs end to end; Sunny
    gap-checks the export file (the Collibra-bound artifact) —
    her eye on names, cards, and technical definitions IS the
    phase acceptance. The Collibra push itself is her notebook,
    downstream, out of this repo's scope.
