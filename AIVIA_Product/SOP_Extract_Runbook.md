# AIVIA Data Extract — DBA Runbook

*This runbook is vendor-neutral and ships with the product. The
scripts it references come from your engagement's SOURCE PACK,
provided separately for your licensed source system. Time required:
about 15 minutes. Nothing in this procedure reads patient data —
only your system's own data dictionary.*

## Before you start (checklist)

- [ ] You can run read-only queries against the source system's
      metadata/dictionary tables
- [ ] You received the source pack for your system (a small set of
      SQL scripts) from your AIVIA engagement contact
- [ ] You know which database the source system's dictionary
      lives in

## Steps

1. **Open the source pack's Script 1 (metadata extract)** in your
   SQL client, connected to the dictionary database.
2. **Run Script 1.** You should see result sets for tables/columns
   and for declared joins, plus a small header result (database
   name, server, timestamp) the script captures automatically.
   *Expected: thousands of rows for a production system. Zero rows
   means the connection or database is wrong — stop and check the
   checklist.*
3. **Save each result set** as a CSV file, named exactly as the
   script's comments instruct.
4. **Run Script 2 (values dump).** It generates and runs one
   uniform SELECT per value table. Save the single combined result
   as a CSV.
5. **Fill in the two manifest fields** in the provided manifest
   file: the source label (given in the source pack) and your name.
   Everything else in the manifest was captured by Script 1 —
   do not edit those values.
6. **Package the CSVs + manifest** into one folder named as the
   manifest instructs (source label + date) and deliver it through
   your engagement's agreed channel.

## What happens next

AIVIA validates your extract and produces an **intake report** in
your organization's environment: what loaded, what was counted as
missing (for example, tables with no declared primary key), and
anything quarantined for review. If the extract is refused, the
refusal message names the exact rule that failed and what to fix —
you should not need a support call to correct and resend.

Nothing you deliver leaves your organization's environment.
