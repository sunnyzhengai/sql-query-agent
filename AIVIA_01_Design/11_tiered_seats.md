11_tiered_seats.md

Status: BUILT 2026-10-09 (pseudo approved same day, Sunny:
"approved. write the actual code"; red-first held — 19 red,
then green; suite green with a funded seat; wheel 0.9.0).
Sunny's validation pass + the D5 measurement close it. Q2
(escalation's worth) stays OPEN on the scorecard's evidence.
Amends phases 07/09; ships via the 10 work wheel.

Design description:
- TIERED SEATS: the paid seat stops being one model for every
  card. The hard dockets keep the large seat; the small,
  formulaic cards move to the small seat; the gate — unchanged,
  one law for every sentence — is what makes the cheap seat
  safe. A card the small seat cannot land escalates to the
  large seat. We pay large-model prices only where large-model
  judgment is needed.
- Why now (measured 2026-10-09, the first work-tenant batch):
  10 files -> 604 cards, 1h43m, ~ $1 per file, every call on
  gpt-5.4. Field-grain rows are the bulk of the 604; their
  dockets are short and their sentences formulaic. At this rate
  the remaining 293 work files cost ~ $300; the tier is the
  largest single saving available without touching any law.

The proposed decisions (each awaits Sunny's ruling):

D1. THE TWO SEATS, PINNED: _MODEL_LARGE = "gpt-5.4" (today's
    seat, unchanged), _MODEL_SMALL = "gpt-5.4-mini". Module
    constants in business_descriptions — one truth, no env
    knob, same pinning discipline as every seat before it.

D2. SEAT BY GRAIN (Q1 RULED 2026-10-09, Sunny: "use SMALL"):
      file card   -> LARGE  (the long docket, the lead text)
      scope card  -> LARGE
      term card   -> SMALL  (her ruling; escalation applies)
      field card  -> SMALL  (short docket, formulaic sentence)
      fact voice  -> SMALL  (one fact, one sentence)

D3. THE ESCALATION LADDER (the gate is the law; the seat is
    plumbing): a SMALL-seat card runs rounds 1-2 on SMALL;
    if the gate still finds, round 3 runs on LARGE. The
    repair budget stays 3 — no new rounds, no new cost
    ceiling. BASIS GAPS UNCHANGED (D15 stands whole): a
    number with no stored meaning goes straight to
    awaiting_human on round 1 and NEVER escalates — no seat,
    however large, may invent a meaning.
    (AMENDED 2026-10-10, the 0.10.0 show-and-log ruling: a
    basis gap still never repairs and never escalates, but
    it no longer blocks — the card ships with the number
    shown plainly and the question logged open in the
    answers file. The sentence "no seat, however large, may
    invent a meaning" stands whole.)
    Fact voices: one SMALL call; a voice the voice-gate
    refuses gets exactly ONE LARGE retry, then the recorded
    miss (machine fact ships), as today.
    HER QUESTION, OPEN (2026-10-09): "does escalation really
    resolve issues? or just surface to human without
    escalation" — the evidence case for escalation is in the
    chat record of the same day; the D5 measurement counts,
    per card: rounds used, whether escalation fired, and
    whether the LARGE round landed. If the count shows
    escalation not earning its keep, it is retired on that
    evidence. Her final ruling lands here.

D4. THE HONEST RECORD: every sheet row and voice-store entry
    records the seat that produced the SHIPPED text (the
    existing "model" field carries the actual seat, not a
    constant). An escalated card records LARGE; a carried
    card keeps its original record.

D5. THE MEASUREMENT (Sunny's ask, 2026-10-09: "use the sql
    file you had to test: record the time and money spent"):
    the acceptance run is ONE file of the home corpus
    (AIVIA_01_Data/01_subject_sql_files, via only_file),
    live paid calls, the SAME file twice — once on the
    current seat (the baseline), once on the tiered build —
    recording wall time and token usage per seat. AMENDED
    SAME DAY by D8: the RUN SCORECARD is the measuring
    instrument — the wheel itself carries the telemetry, and
    both measurement runs read from the same scorecard (the
    injected-counting-caller clause is superseded). Dollars
    are computed from the price card; the price card's
    values land in the data contract on measurement day from
    OpenAI's published pricing, and Sunny verifies the spend
    on the OpenAI usage page. Proposed file:
    Reporting_USP_Hospitalist_Daily_Census_Report_92a_PBI
    (report-tied, field-rich — exercises every seat; see Q5).

Touched-passage inventory (the ruling sweep, due with the
stamp): 07_business_descriptions.md + contract (seat
language, model record), 09_business_terms.md + contract
(terms ride bd's caller; seat named), 10_work_wheel.md (wheel
version note), test_07/test_09 suites (red first), the 07
pseudo-code blocks in business_descriptions.py.

D6. THE TWO FIELD DEFECTS RIDE THIS WHEEL (Q3 RULED
    2026-10-09, Sunny: "same wheel"):
    (a) the empty-ledger read refuses with a named error
        ("the ledger file is empty: delete it, or rebuild it
        if cards were paid") instead of a bare
        JSONDecodeError;
    (b) an account-level refusal from the seat (401 bad key /
        429 no credits) REFUSES THE WHOLE BATCH at first
        sight — no burned rounds, no file recorded described,
        the sequence-law stop — an ECHO (fired twice in one
        day), mandatory build under the Echo Law.
    Each gets its own red test. A THIRD field issue from the
    2026-10-09 run is incoming from Sunny; it lands here when
    named.

D7. THE CORPUS STRATEGY NOTE (Sunny, 2026-10-09): the work
    run narrows to the CENSUS REPORT COHORT only — the same
    cohort whose home copies live in
    AIVIA_01_Data/01_subject_sql_files — not the full
    303-file folder. Scale math in this doc reads
    accordingly; the wheel itself needs no change (the
    corpus is whatever 01_sql_input holds).

D8. THE RUN SCORECARD (RULED 2026-10-09, Sunny: "keeping
    track of scorecards to measure what caused the failures,
    how many rounds of fixes, how many awaiting human, so at
    the end of each run, i can read the scorecard and know
    where we are. also track how long each step takes"):
    describe() ends by writing 14_run_scorecard_output.json
    and its txt twin (the naming law), and prints the txt
    tail in the cell. The scorecard carries, per run:
      - STATUS COUNTS by grain: gate_passed /
        awaiting_human / floor; files described this run and
        remaining;
      - FAILURE CAUSES: a tally of gate-finding classes
        across all rounds (V-1 basis, V-5 enumeration, call
        failed, ...), so the biggest cause reads first;
      - ROUNDS: how many cards landed at round 1 / 2 / 3;
        escalations fired and whether the LARGE round landed
        (this count is the standing evidence for her open
        D3 ruling);
      - AWAITING: the count + every named question,
        verbatim (the rule-them-in-one-sitting list);
        (AMENDED 2026-10-10, 0.10.0: awaiting now carries
        wording failures only; a new QUESTIONS block counts
        the answers file — open, closed this run, and by
        closure route (comment / answer / dictionary / show
        / omit) — and status counts gain
        delivered_with_questions, the visible marker);
      - TIMINGS: wall seconds per step — 07 file/scope
        cards, 07 field cards, fact voices, 09 business
        terms, delivery assembly;
      - SEAT USAGE: calls and tokens per seat (SMALL /
        LARGE), with dollars computed from the pinned price
        card — her dashboard stays the verifying eye.
    The scorecard is mechanical truth only — counted from
    the rows and the clock, never summarized by a model; no
    silent caps.

D5 RESULTS (2026-10-09, the first measurement — scorecards
verbatim, both runs green, all cards gate_passed first or
second round):
  baseline (all-large): 23.4s,
    gpt-5.4 8 calls 5150 in / 599 out = $0.0219,
    gpt-5.4-mini 1 call (see the declared gap) = $0.0014,
    total $0.0233.
  tiered (the shipped map): 22.3s,
    gpt-5.4 4 calls 5668 in / 586 out = $0.0230,
    gpt-5.4-mini 5 calls 1645 in / 193 out = $0.0021,
    total $0.0251.
  THE HONEST READING: the ruled file produced ZERO field
  cards on the home estate — the very grain the tier targets
  — so the tier only moved the voices + the one term to the
  small seat, and run-to-run text variance (one scope needed
  a repair round in each run) swamped the pennies involved.
  NO saving is claimed from this file. The work corpus is
  field-heavy (604 rows over 10 files on 2026-10-09), and the
  scorecard now rides every RUN 5 — the next real work batch
  is the honest evidence, at no extra measurement cost.
  DECLARED HARNESS GAP: the 09 term seat is pinned in code
  (small on rounds 1-2), so the baseline's term card ran the
  small seat — the baseline is all-large on cards + voices
  only.
  Q2 EVIDENCE: escalations fired 0 in both runs — the
  question stays open on real-batch counts.

Future design items (named, not ruled, not in this wheel):
F1. THE DICTIONARY ROUTE for recurring numbers (Sunny,
    2026-10-09: "note the dictionary route as a future
    design item"): a bare constant that recurs across files
    (a line-of-business code, a program code, a pilot year)
    asks her once PER FILE today. The cure is a stored
    basis: the code lands in the 02 dictionary (a value
    meaning), and every card that cites it passes honestly
    with no ask. Design to come: how work-tenant value
    meanings enter 02 (the zc-batch door exists), and
    whether an awaiting_human verdict can offer "store this
    meaning" as a third answer beside show/omit.
    (PARTIALLY BUILT 2026-10-10, the 0.10.0 ruling: the
    HAND route exists — a meaning filled in the answers
    file becomes a 02 value meaning with provenance, and
    the "store this meaning" third answer IS that fill.
    Still open: the BULK route — how a work-tenant value
    table loads into 02 at batch scale.)

The questions, resolved and open:
Q1. RULED: terms -> SMALL (D2).
Q2. OPEN inside D3: escalation's worth — evidence case made,
    the D5 measurement counts it, her final ruling lands in
    D3.
Q3. RULED: same wheel (D6); third issue incoming.
Q4. RULED: number 11 stands.
Q5. RULED: the measurement file is
    Reporting_USP_Hospitalist_Daily_Census_Report_92a_PBI.
