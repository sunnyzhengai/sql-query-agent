# test_11_tiered_seats_data_contract_sunny.md

Status: SCAFFOLD 2026-10-09 (Claude) — Sunny's hand-written
cases land here; the run commands below are filled in per the
standing process.

## Sunny's test cases
(yours to write — the scaffold lists the surfaces the build
exposes, as prompts, not as cases)
- the scorecard txt after a real run: does one read tell you
  where the run stands?
- an awaiting question in the scorecard vs the delivery txt:
  the same words, verbatim?
- the seats section: do the token counts move when a real run
  pays, and does your OpenAI usage page agree?
- 0.10.0 the answers file: after a run with unmapped numbers,
  open 07_business_descriptions_answers_output.csv in Excel —
  one open row per number? Fill one `answer` cell with a plain
  meaning, re-run DESCRIBE: does exactly that card re-propose
  and speak your words? Does the row read closed, your text
  untouched?
- the delivery txt: does a shipped card with an unmapped
  number read "DELIVERED WITH QUESTIONS" — text present, never
  blocked?
- 0.11.0 the uniform ship: does a card that failed its repair
  rounds still DELIVER its text, with "DELIVERED WITH
  FINDINGS" and the findings verbatim? Fill a wording row with
  your own card text, re-run DESCRIBE — do your words render,
  free, and does the registry carry your dated ruling? Fill
  another with `accept` — does the finding close with the text
  untouched?

## The commands

Claude's suite (deterministic, no cost):

    /opt/homebrew/bin/python3.11 -m pytest \
        AIVIA_01_Test/test_11_tiered_seats_data_contract.py -v

The full estate suite:

    /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v

The D5 measurement (PAID, home corpus, one file) — RAN
2026-10-09, results in 11_tiered_seats.md D5 RESULTS. To
re-run it yourself (both runs, ~$0.05 total on the 92a file):

    /opt/homebrew/bin/python3.11 \
        <scratchpad>/measure_tiered_seats.py both

(the harness stages sql/tmdl copies and flips the seat map;
the wheel's own scorecard does all counting; each run's
14_run_scorecard_output.txt lands in its out dir)
