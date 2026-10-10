# Collibra Publish Notebook — the runbook page

THE CELLS LIVE IN ONE PLACE (her rule 2026-10-10,
Brief_Notebook_Import_Law — no more copy-paste):
`collibra_publish_notebook.py` is the versioned source;
`collibra_publish_notebook.ipynb` is its generated twin for
Fabric's Import notebook. This page keeps only the prose.

## How to get it onto the tenant

1. Download `collibra_publish_notebook.ipynb` from the repo
   (GitHub → the file → Download raw).
2. Fabric workspace → New item → Import notebook → pick the
   file. Import creates a NEW item: attach the lakehouse by
   hand once (the same lesson as the work wheel's import
   fallback, 2026-10-09).
3. Fill the CONFIG cell from `tenant_intake.md` section 4
   (Collibra URL, the token's vault secret name, the domain,
   asset-type and attribute-type ids, the sandbox domain).

## The laws it implements

- BLESSED-ONLY: unblessed term names never leave.
- CREATE-OR-UPDATE BY NAME: re-runs update, never duplicate.
- SANDBOX FIRST: one report + one term into the test domain
  before any batch.
- DRY-RUN FIRST: `DRY_RUN` starts True — the first run only
  RESOLVES names and prints the board; nothing is written
  until you read it and flip the flag.
- THE COUNTED CENSUS: every writing run ends in counted
  numbers (reports_updated / terms_created / terms_updated /
  failures), never a vague "done".

## The skips (what never ships)

- A report with a non-empty `files_waiting` (incomplete).
- An `awaiting_human` description (an unanswered empty-text
  card).
- Everything DELIVERED ships — including cards with open
  questions or registered findings (her publish-immediately
  ruling, 2026-10-10 evening); those markers live in the
  delivery txt and the scorecard, never in Collibra.

## The run order

CONFIG → AUTH (expect 200) → LOAD (the push count) → RESOLVE
(read the board; a NO MATCH report means Collibra knows it
under another name — fix the mapping first) → THE WRITES
(refuses while DRY_RUN) → THE EYE (check the sandbox assets;
line breaks survived? then `SANDBOX = False` and re-run
LOAD → RESOLVE → WRITES for the batch).
