11_tiered_seats_data_contract

Status: BUILT 2026-10-09 (drafted, pseudo approved and coded
the same day; test surface live in
test_11_tiered_seats_data_contract.py, 22 locks). Sunny's
stamp closes it. Sunny owns it.

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- Everything the describe door already takes — unchanged and
  owned by the 10 contract (sql folder, tmdl folder, out dir,
  dict_dir, the key in the environment, max_new/force).
- THE TWO SEATS, constants in business_descriptions (D1):
  _MODEL_LARGE = "gpt-5.4", _MODEL_SMALL = "gpt-5.4-mini".
  No environment knob, no parameter.
- THE PRICE CARD, a pinned constant beside the seats:
  per-seat USD per 1M input tokens and per 1M output tokens.
  Values land here on measurement day from OpenAI's published
  pricing and are frozen until a re-pin; the scorecard's
  dollars are computed from THIS card, and Sunny's usage
  dashboard stays the verifying eye (D5).
  LANDED 2026-10-09 (developers.openai.com/api/docs/pricing,
  Standard tier): gpt-5.4 = 2.50 in / 15.00 out per 1M;
  gpt-5.4-mini = 0.75 in / 4.50 out per 1M.

What is the output of this data contract?
- THE SEAT RECORD (D4): every 07 sheet row, every voices
  store entry, and every 09 term row carries "model" = the
  seat that produced the SHIPPED text — the actual seat,
  never the constant. A card that escalated records LARGE; a
  carried card keeps its original record; an awaiting_human
  card (no shipped business text) records the seat of its
  last attempt.
- THE SCORECARD FILE: <out>/14_run_scorecard_output.json,
  written by describe() after the delivery lands, plus the
  txt twin 14_run_scorecard_output.txt (the naming law); the
  txt tail also prints in the run cell. Keys, all required:
  - files: {described_this_run, already_done, remaining}
  - status_counts: per grain (file / scope / field /
    term_card / voice), the count per status
    (gate_passed / awaiting_human / floor; voices count
    proposed / blessed-reused / failed)
    (AMENDED 2026-10-10, 0.10.0: gains
    delivered_with_questions — shipped cards whose
    open_questions is non-empty, the visible marker)
    (0.11.0, same evening: gate_failed joins the counts —
    shipped cards that exhausted repairs, findings
    registered; awaiting_human = the empty-text class only)
  - failure_causes: the tally of gate-finding classes
    across ALL rounds of this run, sorted biggest first —
    [{class, count}] where class is the finding's lead tag
    (V-1 basis, V-5 enumeration, call failed, ...)
  - rounds: {round_1, round_2, round_3} — the round each
    landed card landed on
  - escalations: {fired, landed} — how many cards reached
    the LARGE round, and how many of those the gate then
    passed (the standing evidence for the open D3 ruling)
  - awaiting: [{node_id, questions[]}] — every awaiting
    card with its named questions VERBATIM
    (AMENDED 2026-10-10, 0.10.0: wording failures only;
    0.11.0 same evening: the empty-text class only — an
    exhausted card with text ships as gate_failed and its
    findings register in the answers file instead)
  - questions (0.10.0): {open, closed_this_run, by_closure:
    {comment, answer, dictionary, show, omit}} — counted
    from the answers file's rows, never summarized
  - timings_s: wall seconds per step —
    {cards_file_scope, cards_field, fact_voices,
    business_terms, delivery_assembly, total}
  - seats: per seat {calls, input_tokens, output_tokens,
    usd} — token numbers are the API's own returned usage
    counts, summed verbatim, never estimated; usd = tokens
    x the price card
  - price_card: the pinned values used, echoed
  - _law: "counted from the rows and the clock, never
    summarized by a model; no silent caps"

Definitions:
- THE SEAT BY GRAIN (D2, Q1 ruled): file LARGE · scope LARGE
  · term_card SMALL · field SMALL · fact voice SMALL.
- THE ESCALATION (D3, shape awaiting her final ruling on the
  scorecard's evidence): a SMALL-seat card runs rounds 1-2 on
  SMALL; a still-failing card runs round 3 on LARGE; the
  budget stays 3. A BASIS GAP never escalates and never
  repairs — round 1, straight to awaiting_human (D15 stands
  whole). (AMENDED 2026-10-10, 0.10.0: a basis gap still
  never escalates and never repairs, but it SHIPS — number
  shown plainly, question logged open in the answers file —
  instead of blocking at awaiting_human.)
  A fact voice: one SMALL call, one LARGE retry on a
  refused voice, then the recorded miss, as today.
- THE ACCOUNT-LEVEL REFUSAL (D6b, the Echo build): a seat
  answer that says the ACCOUNT cannot pay — 401
  authentication, 429 insufficient quota — raises
  immediately with the provider's message and the fix named;
  the batch stops; NO file is recorded described; the ledger,
  the delivery, and the sheet are not written. Cards already
  landed before the refusal stay in the checkpoint — they are
  real paid work and the next run carries them free. A plain
  timeout or transient error stays what it is today: a failed
  round, never a dead build.
- THE EMPTY-LEDGER REFUSAL (D6a): a ledger file that exists
  but holds no parseable JSON refuses by name — "the ledger
  file <name> is empty or unreadable: delete it for a clean
  start, or rebuild it if cards were already paid" — never a
  bare JSONDecodeError.
- CONSERVATION (asserted before the scorecard lands; a red
  scorecard does not ship): every spec of the run appears in
  exactly ONE status count; rounds_1+2+3 == landed cards;
  escalations.fired >= escalations.landed; every timing step
  appears exactly once and sums to total within the clock's
  honesty; awaiting[] length == the awaiting_human count;
  (0.10.0) questions.open == the answers file's open rows,
  and closed_this_run == the sum over by_closure.

Authorship:
- The engine writes the scorecard; no hand edits it; her
  verdicts never live in it (they live in the 07 stores).
- Sunny rules on seats, escalation, and the price card;
  Claude builds and the tests lock.

Test surface (red before code, per the standing process):
- test_11_tiered_seats_data_contract.py (Claude): the
  seat-by-grain lock (an injected recording caller proves
  which seat each grain asked) · the seat-record honesty lock
  (row "model" == the seat that wrote the shipped text,
  escalated rows record LARGE) · the scorecard shape +
  conservation locks · the escalation counter lock · the
  account-refusal red test (a stub seat answering 401/429
  refuses the batch, nothing recorded described, checkpoint
  survives) · the empty-ledger red test (a 0-byte ledger
  refuses by name) · 0.10.0 (2026-10-10): the basis-gap
  ships-shown lock, the delivered_with_questions count + the
  questions block + its conservation (open == the answers
  file's open rows); the answers-file mechanics themselves
  are locked in test_07 (CSV shape, merge-never-overwrite,
  the five pickup routes) and the delivery marker in
  test_10/test_09 · 0.11.0 (same evening, the uniform ship):
  the exhausted-ships lock (gate_failed, text stands, seats
  unchanged), the empty-awaiting + gate_failed scorecard
  counts, by_closure bless/accept; the wording-row register,
  accept/bless closures, the free carry-convert and the csv
  header migration are locked in test_07; the business-voiced
  gate_failed entry + open_findings in test_09, the
  DELIVERED WITH FINDINGS txt in test_10.
- test_11_tiered_seats_data_contract_sunny.md (Sunny's hand;
  Claude fills in the run command after build).
