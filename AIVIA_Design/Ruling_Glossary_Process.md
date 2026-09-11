# Ruling — THE GLOSSARY PROCESS

**Status: RATIFIED (Sunny, 2026-09-11 — derived first-principles in
conversation; supersedes the bare scan→scribe→bless pipeline of the
one-vocabulary law's first run).**

## The principle

An acronym's meaning is almost never invented — it is **documented
somewhere, at some scope**. The process is an evidence-gathering
LADDER from strongest source to weakest; guessing (the LLM seat) is
the last rung, never the first. And a conservation law holds
throughout: **every scanned token holds exactly one status in the
ledger; nothing vanishes silently** (the alt/cnt lesson: both were
in the 2026-09-08 scan, the Scribe proposed neither, and no record
said so).

## The five phases

| phase | act | authority |
|---|---|---|
| 0 | **Import the documented truth**: vendor naming standards (Epic Clarity suffix conventions: _CNT, _AMT, _DTTM, _YN, _C, _ID …), the org's glossary, the source system's dictionary | source, with named provenance |
| 1 | **Total scan**: every distinct name token in the estate, with carrier count, sample carriers, and position (suffix/prefix/mid/only) | mechanical |
| 2 | **Mechanical classification**: token matches a Phase-0 dictionary entry → `matched` (cites the entry); ordinary words → `plain` | mechanical proposal; Sunny ratifies in bulk |
| 3 | **Evidence-packed proposal**: the Scribe sees CONTEXT, never bare tokens — carriers, home table, neighbor speech, SQL usage, domain frame. Three legal outputs: propose with cited evidence · plain · **explicitly unknown** (abstention is a disposition, never silence) | machine-proposed |
| 4 | **Human ruling, scoped**: bless / correct / hold-with-reason; every blessing carries scope of validity (estate / schema / table / position) — PTA is "prior to arrival" in the ED and "physical therapy assistant" in rehab | human-only |
| 5 | **It stays alive**: each intake re-scans; the token delta enters the queue; coverage % and the findability battery are the acceptance instruments | mechanical + acceptance |

**Customer prereq (ruled):** Phase 0 joins the customer checklist —
the abbreviation dictionary is an intake input beside the data
dictionary descriptions. Our dev estates have no source to ingest,
so we AUTHOR the fixture (marked as such, gap-checked by Sunny).

## The two files (ruled: one folder, one ledger)

Per estate, `<estate>/glossary/`:

- **`abbreviation_dictionary.json`** — Phase 0. Read-only to the
  pipeline; only imports change it. Entries carry expansions,
  optional position constraint, and the file names its source.
- **`acronym_ledger.json`** — Phases 1–4 in ONE file, one entry per
  scanned token, so every token's whole life is visible in one
  place. Conservation is a group-by over `status`.

**Status vocabulary:** `unreviewed · matched · plain · proposed ·
abstained · blessed · held`. The review queue at any moment is the
`proposed + abstained + unreviewed` slice, impact-ordered by
carrier count.

**THE FIELD LAW (what makes one file safe):** machine fields
(`carriers`, `sample`, `position`, and `proposed`/`evidence` while
unruled) are refreshable; ruled fields (`status` once
blessed/held/plain, `expansions`, `scope`, `why_held`,
`approved_by`, `approved_at`) are human-only — a refresh may update
a blessed token's carrier count, NEVER its expansion or status.
Same separation the store enforces (builders never journal; humans
rule), applied to columns of one file.

## Downstream (unchanged in spirit)

- The **seed** reads the ledger's `blessed` slice and births the
  governance journal through the real write path (`enrich.bless`) —
  delta by name, per-entry approvals; the journal stays untracked
  and reborn. Acronym NODES and their edges remain exactly the
  one-vocabulary law's shape (Design_Chatbot.md).
- The **scan excludes governance/vocabulary kinds** (`acronym`,
  `person`, `agent`, `role`) — the estate's names are what speak;
  blessed vocabulary must not become its own carrier.
- `acronym_blessings.json`, `acronym_remainder.json`, and the DRAFT
  proposals file **retire**: their content folds into the ledger
  (blessings → `blessed` with provenance; remainder → `held` with
  `why_held` carried). Git history keeps the originals.

## THE PREREQ ADDENDUM (ruled by Sunny, 2026-09-11 — the
## vendor-vs-site partition)

The estate's delivered dictionary mixes vendor-shipped and
site-built objects indistinguishably; the intake can prove "this
reference isn't in what you delivered" but not "this object isn't
the vendor's, so your team owns its documentation." Ruled:

- **The vendor's OWN object dictionary becomes a declared intake
  input** (a customer prereq beside the abbreviation dictionary
  and the data-dictionary descriptions).
- At intake, delivered objects partition against it: covered =
  vendor-documented; **not covered = presumptively site-built →
  THE RESIDUE LIST**, emitted for the hospital's admin in the
  same intake-report pattern the DBA loop already uses
  (`intake_result_tables/` — the 164→9 unresolved-references
  precedent).
- The residue list carries two obligations: **descriptions** for
  undescribed objects (feeding the existing documentation census)
  and **name tokens** entering the glossary ladder at the
  org-glossary/Scribe rung — no vendor dictionary will ever
  expand a name the site invented.

This completes the three-grain accounting, each grain with a
named owner for its unmatched remainder:

| grain | compared against | unmatched goes to | status |
|---|---|---|---|
| SQL reference | delivered dictionary | `unresolved_references.csv` → DBA | built (loop proven, 164→9) |
| dictionary object | vendor's object dictionary | THE RESIDUE LIST → hospital admin | ruled here, NOT BUILT |
| name token | abbreviation dictionary | `acronym_ledger.json` → Sunny's ruling queue | built 2026-09-11 |

## Standing gaps (recorded, awaiting build/ruling)

1. **Phase 2 `plain` classification** needs a ruled word source
   (an English wordlist is env-dependent); until then ordinary
   words sit as `unreviewed` — honest, visible.
2. **Phase 3 rework** (evidence-packed Scribe with abstention) is
   designed here but NOT yet built; the first run's Scribe saw
   bare tokens, which is why it guessed "Overdose" from two
   letters.
3. **Bulk-ratification surface** (bless the `matched` slice in one
   act) — quality-of-life; hand-editing the ledger works today.
4. **THE RESIDUE LIST** (the prereq addendum's build): vendor
   object dictionary as intake input + the vendor-vs-site
   partition + the emitted admin list — ruled above, not built;
   slots into the intake-report machinery.
