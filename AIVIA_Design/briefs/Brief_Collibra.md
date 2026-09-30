# Brief_Collibra — the Power BI report description lands on its Collibra Power BI Report asset

**Status: DRAFT** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED)

Sunny's goal, his words (2026-09-21): *"when we create a
description for a PowerBI report, we need to use it to update in
Collibra, the PBI asset type's description"*.

ONE sentence of scope: the stored `dc.pbi_report.description` —
the approved Scribe summary AIVIA already computes — is written
onto the Collibra asset of type Power BI Report that stands for
that same report, into its native Description attribute, and
never on top of a human's words.

Out of scope, named so it cannot creep: the file grain (files
stay lineage in Collibra, Sunny's M6 decision #2) · Purview
(his "Collibra first, Purview later") · the technical definition
field · term/glossary publishing · any write to Power BI itself
(the retired `src/adapters/fabric_pbi.py` wrote to the Fabric
API — a DIFFERENT target, and NOT this goal).

| field | content |
|---|---|
| class | **planned addition** — fills a slot already declared, not a new idea. `Contract_Consumption_Layer.md` CONSUMERS already carries the row `dc.pbi_report | sc.collibra_publish (DORMANT) | THE TWO FIELDS — the customer-facing payload (Collibra reads at report grain; files stay lineage) | NONE until the publisher revival brief`. THIS IS that publisher revival brief. It also re-enters `sc.collibra_publish` through the change process exactly as the F3 ruling requires |
| claims | `ds.report_derived_pair` (the description being published) · `ds.consumption_vocabulary` (`pbi_report` is the grain) · F3 ruling 2026-09-16 (DORMANT; "revival re-enters via the change process (ruling → contract → tests)") · M6-1 ruling 2026-09-17 ("Collibra first, Purview later"; "files stay lineage in Collibra, reports are the customer-facing assets") · `landing_registry.ZERO_SCHEMA_FOOTPRINT` (Sunny 2026-08-31, no custom attributes) · `landing_registry.OUTBOX_FIELDS` + rules R1–R4 · LAND-1..5 (the B4 clause) |
| impacts (computed, step-2 query) | **writers**: NO stored field gains a new writer — `dc.pbi_report.description` keeps its ONE writer (the Scribe summary, approved-only). This brief adds an OUTWARD surface and the outbox, nothing inward. **new state**: the outbox rows (kg3 proposal/observed events — `land.py` already appends `sent`; `lens_current_outcome` already reads `observed`) + the resolved asset mapping (C2). **consumers**: `sc.collibra_publish` flips DORMANT → LIVE; `export_headers.json` gains a second target; the console's handoff receipt (`landing_registry.CONSEQUENCES["console"]`) — NOT built here, declared as debt. **served data**: **NONE** — no stored description changes, no re-voicing, **no Sunny load, no AISQL_RECORD run** (no new searchable sentence: the text published is text the ask index already holds). **registries**: expected NONE (no metamodel change; the outbox rides kg3's existing proposal/disposition doors). **wheel**: the next cut carries; no wheel need of its own. **tests**: new `tests/aisql/test_collibra_land.py` + additions to `test_approve_land.py` for the second target |
| ambiguities | C1–C8 below. **C1, C2, C4, C6 RULED by Sunny 2026-09-21.** STILL OPEN: **C2-b** (does a Fabric report id exist on the Collibra asset — settled by the build's first discovery act, not by reasoning) · **C6-a** (does the prefix change ride this brief) · C3, C5, C7, C8 (proposals await his word) |
| debt declared | (1) **THE OVERWRITE GUARD** — C1 ruled the pilot overwrites everything; the read-first/never-overwrite-human-text mechanism is his explicit "for future build". Recorded reason: his ruling, a scoped pilot. Landing step: **Brief_Collibra_Guard**, before any run against a non-Dev instance. Tripwire (the placeholder law): a test refusing any non-Dev base_url while the guard is absent. (2) **the console handoff receipt** — `landing_registry.CONSEQUENCES` rules decided cards show "proposed to <tool> · <last seen outcome> · [open in catalog]". Not built here; the outbox rows it reads are born here. Landing step: the Workbench/Resolution Console brief. (3) **divergence detection** — already ruled NOT a live subsystem (rule R4, "a paid diagnostic"); a standing ruling, not debt. (4) **Purview** — his "later" |
| retirement (pivots only, the 2026-09-19 law) | This SUPERSEDES the Era-1 Collibra publish path, all of it already retired in commit `91b198a` and recorded in `Brief_Retirement_manifest.txt` lines 31–32, 563–565, 602–604, 719. Nothing is un-retired wholesale: the new code is written fresh against the Era-2 graph, and the old files stay dead. What is CARRIED FORWARD is knowledge, not code — the four field-scars in C7. The `_PBI`-suffix fuzzy matcher (`extract_match_key`, `fuzzy_match_score`) is **NOT revived** — see C2; it stays retired |
| does this promote? (the Promotion Gate) | at close — expected YES if the suite is green and C1's answer keeps the write behind a human confirmation; no served data moves, so nothing blocks on a load |
| Sunny's approval | **PENDING** — nothing is built until he rules C1–C8 |
| closing check | (filled at CLOSED) |

---

## What already exists — measured, not assumed

Stated so the brief is not re-deriving what is already true.

| piece | state today | evidence |
|---|---|---|
| the description text | **LIVE** | `dc.pbi_report.description`, M7 BUILT 2026-09-18; 1 report in ed_sepsis_dev, 28 in sepsis |
| approved-only, empty counted | **LIVE** | the M6 file precedent, `Contract_Consumption_Layer` CONTRACT_FIELDS |
| report → proc (Sunny's M-code point) | **LIVE** | `dc.executes`, from TMDL partition parsing (ADR 0040), 28 measured, 2 counted-unresolved RULED FINAL 2026-09-18 |
| the send gate | **LIVE** | `land.py` LAND-1 (accepting disposition + named human), LAND-2 (no re-send when denied), LAND-3 (sent event BEFORE transport) |
| PHI redaction on egress | **LIVE** | `land.py` calls `phi_gate.egress_redact` — "Text LEAVING the tenant … the full rule set redacts here" (ADR 0025) |
| the column-set-as-data mechanism | **LIVE** | `export_headers.json` + LAND-4's `assert set(row) == set(binding["columns"])` |
| the outcome lens | **LIVE** | `derivation.lens_current_outcome` reads `observed` proposals |
| Collibra Power BI Report asset type | **KNOWN** | `00000000-0000-0000-0000-100000000006` (OOTB), from the retired matcher |
| Collibra Description attribute type | **KNOWN** | `00000000-0000-0000-0000-000000003114` (OOTB default) |
| writing a description to a real Collibra PBI asset | **PROVEN ONCE, then retired** | `notebooks/utilities/collibra_update_description.py` ran `update_description()` against Sunny's Collibra **Dev** instance on the asset `"340B Eligible Charges for HB and PB"`, with a read-back verify cell |
| **never overwrite human text** | **NEVER BUILT** | no prefix check existed anywhere in the retired code |
| **the outbox** | **NEVER BUILT** | designed in `landing_registry.OUTBOX_FIELDS`, never coded |

**The gap is small.** This is not a revival of 850 lines. It is: a
read pass, a prefix guard that never existed, a target binding, a
write, and the outbox — on top of a send gate that already works.

---

## The design

### The shape, end to end

    AIVIA graph                    Collibra
    ───────────                    ────────
    pbi_report node
      .name  ────────────────────► find asset, type 100000000006,
      .description                   name matched EXACTLY (C2)
      (approved Scribe summary)      │
                                     ├─ not found → counted-unresolved,
                                     │              NEVER guessed
                                     └─ found → read Description attr
                                                  │
                                    ┌─────────────┴──────────────┐
                              starts with our prefix,      a human wrote it
                              or is empty                        │
                                    │                            ▼
                                    ▼                    REFUSE + report
                              eligible to write           by name (C1)
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            the PREVIEW FILE                  the WRITE
         (what will be sent,              PATCH the Description
          reviewable, no network)          attribute (C1 decides
                    │                       whether this happens
                    ▼                       here or by import)
            Sunny reads it
                    │
                    ▼
         named human confirmation ──► LAND-1 satisfied
                    │
                    ▼
            sent event lands FIRST (LAND-3)
                    │
                    ▼
            outbox row: target_object_id = the Collibra asset id

### What goes in the Description attribute

The stored `dc.pbi_report.description`, egress-redacted, with the
attribution prefix when the author is an agent — the identical
rule `land.py:render` already applies:

    text = phi_gate.egress_redact(current["description"]).text
    if str(current.get("author", "")).startswith("agent:"):
        text = HEADERS["attribution_prefix"] + text

Prefix today: `"AISQL agent generated: "`. No other field. No
custom attribute. The prefix IS the provenance marker —
`ZERO_SCHEMA_FOOTPRINT` ruled it, and C1's guard depends on it.

### Why the prefix is load-bearing

`ZERO_SCHEMA_FOOTPRINT.attribution_note`, Sunny's 2026-08-31
ruling: *"machine-authored descriptions begin with the prefix; a
steward rewriting the text and dropping it is itself the signal of
human authorship."*

That sentence, written for attribution, is ALSO the overwrite
rule. A description that does not start with the prefix was
written or edited by a person. So "never overwrite human text"
needs no new field, no custom attribute, no timestamp compare —
it is a string test on text we already put there. The zero-schema
ruling and the overwrite ruling turn out to be the same mechanism.

`accepted_limit` is the honest cost, already recorded: *"with no
marker in their catalog, a lost outbox means our artifacts are
recognisable only by the prefix text."* If the prefix string ever
changes, every previously-written description reads as human and
becomes unwritable. That is a real consequence — C6.

---

## The ambiguities — Sunny rules each

### C1 — Where does the write actually happen?

**RULED (Sunny, 2026-09-21):** *"for this pilot, let's over write
everything. for future build, we'll add the read first then only
write when no human writing is in."*

**THE PILOT OVERWRITES.** No read-before-write guard, no prefix
check, no refusal path. Every resolved report's Collibra
Description attribute is overwritten with our text.

Consequence, stated plainly so it is not discovered later: **a
steward's hand-written description on a matched asset will be
destroyed, with no warning and no undo.** The attribution prefix
still goes in the text (it is the zero-schema-footprint ruling,
independent of the guard), but in the pilot it marks authorship
only — it gates nothing.

Containment, since the pilot is destructive:
- **Dev instance only** (C4) — never a production Collibra.
- LAND-1 still holds: an accepting disposition + a NAMED HUMAN
  confirmation before any send. The B4 clause is not waived by
  the overwrite ruling; nothing sends itself.
- C8's preview still lists every asset and the text to be
  written, so the blast radius is visible BEFORE confirmation.
  Under overwrite, the preview cannot show what is being
  destroyed (that needs the read) — it shows what will be
  written and onto which named asset. **Recorded limit.**

**Debt, with its landing step (the placeholder law):** the guard
is the next brief — read the Description attribute, write only
when it is empty or carries a known agent prefix, refuse and
report otherwise. The mechanism is already designed in this
brief's earlier draft and in `ZERO_SCHEMA_FOOTPRINT.
attribution_note`; the prefix tuple of C6 is what it will test
against. It does not ship here by Sunny's ruling, not by
oversight. Landing step: **Brief_Collibra_Guard**, before any
run against a non-Dev instance.

The tripwire that keeps the placeholder from shipping naked: a
test asserting the flow REFUSES any target whose configured
instance is not the Dev base_url, so the overwriting pilot
cannot reach production while the guard is absent.

### C2 — BLOCKING. Which Collibra asset is the right one?

Sunny raised the M-code: *"we are getting from fabric POWERBI's
m-code: to find out the name of the proc used."* He is right, and
that link is live — it is `dc.executes`, report → proc, from TMDL.
But it is a different link from the one this brief needs. Three
links, easy to blur:

| link | source | state |
|---|---|---|
| report → proc | the M-code / TMDL | **LIVE** (`dc.executes`) |
| proc → Collibra proc asset | Collibra name match | retired; not needed here |
| **report → Collibra PBI Report asset** | **this question** | **unanswered** |

The retired working code answered it WITHOUT any proc hop or
relation traversal: load every asset of type
`00000000-0000-0000-0000-100000000006`, match the TMDL-derived
report name case-insensitively, score 1.0, and *the heuristic
never runs*. Its own comment states the failure posture:

> *"A recorded exact name that is absent from Collibra is a real
> answer (asset not synced yet) — do NOT fall through to fuzzy
> guessing against a known-correct name."*

That is exactly the FC2 posture Sunny ruled on 2026-09-18 ("not
same" — unresolved stays counted, never guessed), written a month
earlier by the same instinct.

**RULED (Sunny, 2026-09-21):** *"use M-code's report name to match
with our fabric PowerBI report name"* — exact name matching, the
`_PBI` fuzzy tier stays retired. (c) remains the escape hatch for
any report the exact match misses: resolved as data, his eye,
never a code guess.

#### C2-a — where the report name actually comes from (his question, answered)

He asked: *"did you check where we got the PowerBI report name,
from fabric, right?"*

**Measured answer: NOT from Fabric. From the repo.**
`devtools/pbi_extract.py` reads `*.SemanticModel` folders on
disk; the report name is **the folder name** (`ED Sepsis Screening
Dashboard.SemanticModel` → `ED Sepsis Screening Dashboard`). No
Fabric API call exists anywhere in the extractor. For a
git-synced Fabric workspace the folder name equals the item's
display name — but **nothing in our code verifies that**, and the
brief should not claim TMDL provenance it does not have. My
earlier phrase "the TMDL-derived report name" was flattering;
corrected here.

#### C2-b — OPEN. Is there an ID that matches? (his question)

He asked: *"since Collibra pulls the PBI reports from Fabric, are
you sure there's not an ID of some sort that will match?"*

**Likely yes on Collibra's side; NO on ours today.** Measured:

| GUID | where it lives | is it the Fabric item id? |
|---|---|---|
| `logicalId` c1191c9e-a2d8-b198-4e43-f2f4817a4f22 | the Report's `.platform` | **NO** — Fabric *git-integration* identity, a different namespace from the workspace item id |
| `logicalId` c7cc5162-d9cf-9b7b-48de-2bf1533e9959 | the SemanticModel's `.platform` | NO — same |
| `semanticmodelid=c0fa87c5-…` | a `.pbir` connection string | the MODEL's id, not the report's |

Three blockers to matching on an id today:
1. **`reports.json` holds no id at all** — its keys are `name`,
   `description`, `executes`, `bound_fields`. `read_model()`
   regexes only `sourceColumn` and `EXEC`. Capturing an id is a
   change to the extractor.
2. **`logicalId` is the wrong GUID.** It is stable across a
   repo's branches; it is not what the Power BI REST API returns
   and not what a Collibra harvest would carry.
3. **Those files are retired** (commit `91b198a`) — the GUIDs
   above were read from git history, not from the live tree.

**The supporting clue for his instinct:** Collibra report names
in his estate carry bracketed GUIDs *inside the display name* —
`[433bbb97-…] 340B Eligible Charges [667ad212-…]` (real shape,
from the retired `normalize_report_name`). Two GUIDs, almost
certainly workspace id + report id, leaking from the harvest into
the name field. So **the ids may be recoverable from Collibra's
side with no new Fabric call at all** — by parsing them out of
the name rather than by us carrying them.

**This cannot be settled from the repo.** It needs one look at a
real Collibra PBI Report asset: is the Fabric report id a proper
field/attribute on the asset, or only embedded in the name? That
is a read-only API call (C4), Sunny's hand.

**Proposal:** the pilot ships on **exact name matching per his
ruling** — it is sufficient and it is what the working code did.
The id question becomes the FIRST act of the build: a read-only
discovery pass that prints one Collibra PBI Report asset's
fields, attributes and relations. If a Fabric report id is there,
id-matching supersedes name-matching in this same brief (name
matching stays the fallback); if it is not, name matching stands
and this row closes as measured. Discovery is cheap, read-only,
and answers a question neither of us can answer by reasoning.

**Why it matters beyond the pilot:** a display-name match breaks
silently on rename. An id match does not. For 28 reports a rename
is a nuisance; for a real estate it is the difference between a
mapping that holds and one that quietly rots.

### C3 — the Collibra target's column set (only if C1 = (b) or a file ships)

`export_headers.json`'s `_comment` already anticipates this:
*"real targets (Purview glossary CSV, Collibra Data Intake) bind
per engagement from the same precedent shapes."* The v1 target
`catalog_a` binds `Name · Full Name · Asset Type · Domain ·
Description · Stewards` with constants `Asset Type = "Logic
Scope"`, `Domain = "AISQL X-Ray"`.

A Collibra PBI target needs its own native set. Under C1=(a) the
preview file is OURS (not an import format) and can reuse a
simple set. Under C1=(b) it must be the real Data Intake column
set — **which only Sunny can supply.**

**Proposal:** bind `collibra_pbi` with `Name · Full Name · Asset
Type · Domain · Description`, `Asset Type = "Power BI Report"`,
Domain from config. Stewards dropped unless he wants the accepters
carried. His correction expected.

### C4 — BLOCKING. Credentials, and which instance

The retired notebook read `config.adapters.collibra` from
`org_config.yaml` — base_url, username, password, api_key,
domain_id, community_id, asset_type_id — and the example file
still carries the commented block. `.env` holds `OPENAI_API_KEY`
today.

Questions: which instance does the build test against — **Dev**,
as the 2026-08 work did? Do credentials live in `.env` (like the
OpenAI key) or stay in `org_config.yaml`? And does any test in
the suite touch the network, or is every test offline against
recorded shapes?

**RULED (Sunny, 2026-09-21):** *".env is fine."* Credentials live
in `.env` alongside `OPENAI_API_KEY`, read automatically — he is
never told to "set his key".

The rest of the proposal stands unless he says otherwise: **every
suite test offline** against recorded response fixtures; the live
call is his hand only, against **Dev**; no CI job ever reaches
Collibra. Under C1's overwrite ruling the Dev restriction is not
a preference but the pilot's containment — it carries the
tripwire test named there.

### C5 — may this brief ever CREATE a Collibra asset?

The retired adapter's `publish()` created assets when absent —
and that path is precisely where the 2026-08-15 duplicate-asset
bug lived.

**Proposal: NO. This brief only ever UPDATES an existing asset's
Description.** An asset that does not exist is counted-unresolved
(C2), never created. The `CollibraLookupError` class is therefore
unnecessary — we never branch to a create. This removes one of the
two historical bugs by construction rather than by fixing it.

### C6 — the attribution prefix

**RULED (Sunny, 2026-09-21):** *"don't mention 'AIVIA', always. in
this case, just use AI agent generated."*

Two rulings in one sentence, and the first is **standing, not
local to this brief**: the brand name AIVIA never appears in text
that leaves us. The prefix becomes:

    "AI agent generated: "

Note it is also no longer the product name at all — it says what
authored the text, not who sells the tool. That is a better fit
for `ZERO_SCHEMA_FOOTPRINT`'s purpose (marking machine
authorship) and it means the string never needs to change again
when branding does. The whole C6 fragility disappears: a prefix
that names no product cannot go stale when the product is
renamed.

#### C6-a — BLOCKING FOR THE BUILD. This is a live constant with pins.

The prefix is not brief-local. Measured, it lives in:

| home | current value |
|---|---|
| `aisql/flows/export_headers.json` `attribution_prefix` | `"AISQL agent generated: "` |
| `src/landing_registry.py` `ZERO_SCHEMA_FOOTPRINT` | `"{product} agent generated: "` (template, rendered by `src.branding.product_name()`) |
| `tests/aisql/test_full_circle.py:107` | asserts `startswith("AISQL agent generated: ")` |
| `tests/aisql/test_approve_land.py:101` | asserts the same |
| `tests/aisql/test_phi_gate.py:37` | uses it in a fixture string |
| `docs/architecture/DECISION_LANDING_MATRIX.md` | generated projection of the registry |
| `internal/docs/BOARD.md:647` | carries the stale `AIVIA agent generated:` — evidence the old brand DID ship in this string once |

So changing it is its own small change touching the `catalog_a`
target, a registry, three test pins and a generated doc — none of
which is Collibra work, and one of which (`landing_registry.py`)
is in the docs-untangle territory.

**Question for Sunny — the only one left blocking:** does the
prefix change ride THIS brief (declared in its Files list, done
in the same build), or land as its own small change first? I
recommend **riding this brief**: it is four files, the pins are
one-line edits, and it must be true before the first Collibra
write or the pilot ships the old string into his catalog.

**The AIVIA-never-in-outbound-text ruling is broader than the
prefix** and should land in standing law, not only here. Nothing
else currently measured ships "AIVIA" outward — the domain
constant is already `"AISQL X-Ray"` — but the brand tripwire
that exists today watches for "aivia" as a *rename* check, not as
an outbound-text ban. Recorded here; its home is Sunny's call.

### C7 — the four field-scars: which become tests?

Knowledge from the retired code worth keeping as pins:

| scar | date | proposed pin |
|---|---|---|
| the Description is a SEPARATE attribute write; payload-only reported SUCCESS while every description was silently dropped | 2026-08-15 audit | **read-back verify**: after a write, GET the attribute and assert the stored value equals what was sent. Byte-exact — this is `inv.verbatim` reaching into their catalog |
| enterprise layouts display a DIFFERENT attribute as the description box (written, wrong field shown) | 2026-08-17 field find | `description_attr_type_id` stays CONFIG, default OOTB `…3114`; a test pins that the id is read from config and never hardcoded at the call site |
| a failed lookup read as "not found" created duplicate assets | 2026-08-15 audit | moot under C5 (we never create) — but a pin that a lookup ERROR refuses the send rather than proceeding |
| qualified names produced junk keys → 128 unmatched + garbage 1.00 scores | 2026-08-18 field failure | moot under C2=(a) — the fuzzy tier stays retired. A pin that no fuzzy matcher exists in the new path |

**Proposal: all four, phrased as above.** Three are cheap; the
read-back verify is the one that earns its keep — and under C1's
overwrite ruling it earns MORE, because it is now the pilot's
only evidence that what landed in Collibra is what we sent. With
no read-before-write, the read-AFTER-write is the whole
verification story.

### C8 — what does Sunny see before he confirms?

LAND-1 needs a named human confirmation of the send. He should not
confirm blind.

**Proposal:** a preview listing, per report — the Collibra asset
name and id · the current Description (first ~100 chars, or
`(empty)`) · the text to be written · the verdict (`will write` /
`REFUSED — human text` / `unresolved — no Collibra asset`) — plus
three counts. Nothing is sent until he confirms. Under C1=(a) this
is the preview file; under (b) it is the import file plus a
refusal report.

---

## Contract rows this will need (DECLARED, NOT YET APPLIED)

Not written in this act — another Claude session is mid-build on
Business Voice and holds `Manifest_Build.md` and the registries
uncommitted (Sunny's instruction, 2026-09-21: *"draft the brief
only"*). These apply in the build, same breath as the code:

| document | row | change |
|---|---|---|
| `Contract_Surfaces.md` | `sc.collibra_publish` | DORMANT → **LIVE**; promises + re-verify tests filled |
| `Contract_Surfaces.md` | GOVERNS | the F3 row amended — revival happened, by this brief |
| `Contract_Consumption_Layer.md` | `dc.pbi_report | sc.collibra_publish` | re-verify `NONE until the publisher revival brief` → the new test ids |
| `Contract_Consumption_Layer.md` | FINDINGS | any new finding from the build |
| `Manifest_Build.md` | one ledger entry | the arc, at close |
| `AIVIA_Design/INDEX.md` | — | no new design doc; no line needed |
| `docs/architecture/TEST_MAP.md` | new test file rows | the suite-map tripwire forces this |
| `landing_registry.OPEN_ITEMS` | `"collibra relation types"` | **stays OPEN** — this brief needs no relation type (C2=(a) matches by name); the item belongs to term/glossary publishing, not here |

---

## Files declared

    AIVIA_Design/briefs/Brief_Collibra.md

Only this file, and only while the brief is DRAFT. Per H3 a DRAFT
brief unlocks NOTHING — no code edit can pass the gate under it.
The full list is added at APPROVED, with Sunny's word, per H5.

Expected additions at approval (named now so the list is no
surprise, NOT yet authorized):

- `aisql/flows/collibra.py` — the read/match/guard/write flow
- `aisql/flows/export_headers.json` — the `collibra_pbi` target
- `tests/aisql/test_collibra_land.py` — the pins, RED first
- `tests/aisql/test_approve_land.py` — the second-target additions
- `AIVIA_Design/Contract_Surfaces.md`
- `AIVIA_Design/Contract_Consumption_Layer.md`
- `AIVIA_Design/Manifest_Build.md`
- `docs/architecture/TEST_MAP.md`

---

## Build order (after APPROVED, per the process)

0. **DISCOVERY FIRST — the C2-b answer** (read-only, Sunny's
   hand, before any code): one Collibra Dev PBI Report asset,
   printed whole — its fields, its attributes, its relations. Two
   questions it settles: does the asset carry a Fabric report id
   as a real field, or only inside the bracketed display name?
   and what is the Description attribute's type id on HIS
   instance (C7's 2026-08-17 scar)? Id-matching supersedes
   name-matching in this same brief if the id is there.
1. **tests first**, authored failing: exact-name match binds ·
   a name absent from Collibra stays counted-unresolved and is
   NEVER fuzzy-matched · no create path exists (C5) · read-back
   verify equals what was sent · `description_attr_type_id` comes
   from config, never hardcoded at the call site · a lookup error
   refuses rather than proceeds · LAND-1/2/3 hold for the new
   target · the preview's counts · **the non-Dev refusal
   tripwire** (C1's debt) · the new prefix string (C6).
2. the flow: resolve → preview → confirm → write → read-back →
   outbox row. **No read-before-write guard in the pilot** (C1).
3. the target binding in `export_headers.json` + the prefix
   change across its four homes (C6-a, if it rides this brief).
4. contract rows + TEST_MAP, same breath.
5. full suite (`python3.11 -m pytest tests AIVIA_Test -q`, ≈11 min)
   + `python3.11 -m ruff check --no-cache`.
6. **no export regen, no Sunny load, no AISQL_RECORD run** — no
   stored text changes.
7. Sunny's hand: the live Dev run, his named confirmation, his
   eye on the read-back.
8. close: files changed == Files declared.

**Sequencing note (2026-09-21):** another Claude session is mid-
build on Business Voice, holding `Manifest_Build.md`, the seven
registry JSONs and two estate glossaries uncommitted on `dev`.
Steps 3–4 touch shared files. This brief's build waits for that
arc to commit, or takes a worktree. Step 0 is read-only and can
run any time.
