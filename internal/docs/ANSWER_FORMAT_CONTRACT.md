# The Answer Format Contract (RW-10)

**Status:** DRAFT 2026-08-28 — review-authored from Sunny's
13-question walk verdicts ("all correct, presentation confusing").
Dev builds against this; Sunny's clarity check is the acceptance.

## The one rule

**The conclusion card is machine-composed from stamped fields.
Model prose fills gaps only — it never carries the verdict, never
repeats what a machine field already says, and never renders
twice.** (RW-9 fixed the duplication; this contract prevents its
class.) Wherever a deterministic field exists — a verdict, a diff,
a count, a flag class, a description — the card uses THE FIELD.
Stochastic narration of deterministic facts is the defect this
contract retires.

## Per-class card composition

### 1. Definition ("what does X use / how is X defined")
- Line 1: business name + the authored description (store field).
- Line 2: the criteria sentence from the TOP DECISION SITE
  (machine: the WHERE/CASE text, trimmed), with `show SQL` fold.
- Governance strip: family flags if any (chips, see §3 gloss).
- NO numbered template ("1. Description: 2. SQL Logic:") — the
  skeleton is retired.

### 2. Sameness / difference ("are X and Y the same / how differ")
- Verdict chip first: **SAME** / **DIFFERS** (compare stamp,
  machine).
- **The machine diff lines, always** — composed from compare's
  diff field, e.g.:
  `+ E11.80 — present only in Diabetic Codeset (reports copy)`
  `grain: DISTINCT PATIENT_ID vs one row per visit`
  Never model-paraphrased; identical wording on every run.
- One line per item: name + description (store fields).
- Model prose MAY add one business-consequence sentence ("every
  patient with that code silently vanishes from one team's
  numbers") — additive color only.

### 3. Flags ("what red flags / what's wrong with X")
- FLAG CARDS on the conclusion card itself (not folded away):
  identity, class chip + severity, members · distinct logics ·
  disposition, and the sweep's why-sentence (store mint).
- **Plain-language gloss per class, on the card:**
  - cousin_conflict — "same name, different logic: one name doing
    N jobs"
  - duplicate — "identical logic under different names: these
    compute exactly the same thing" (+ member names)
  - misnomer — "the shared name doesn't mean the same thing
    everywhere"
  - grain_shift — "same name, different unit of count (e.g.,
    patients vs visits)"
- Closing machine line: "N flags · flags disclose, never gate ·
  sweep receipt <timestamp>".

### 4. Variants / ways-of ("all the ways of defining X")
- Machine count line: "N certified variants carry this name
  family."
- Member list: name + description one-liners (store fields).
- Cross-reference chip to the family's flags ("these N sit in a
  cousin-conflict flag — 10 distinct logics").

### 5. Lineage / feeds ("which metrics read T / feed dashboard D")
- The chain, grain disclaimer verbatim from the headline
  ("reads-grain, not logic-grain...").
- If the probe carries a NON-EVIDENCE stamp, the card carries the
  stamp's next-step sentence (RW-8 already enforces the verdict
  side).

### 6. Data questions ("how many patients...") — POLICY REFUSAL (RW-11)
- FIRST-ROUND typed refusal, fixed wording:
  "AIVIA answers definitions, not data — patient rows never reach
  the model. Here is the certified definition, and where it runs."
- Followed by the §1 definition card for the named metric.
- NEVER budget-wander toward an unanswerable question.

## Display seating

- The conclusion card renders ONCE, on top (RW-9).
- Rounds stay folded to stamped one-liners beneath (RW-5).
- Flag cards and diff lines live ON the card — the card is the
  answer; the folds are the receipts.

## Relation to 0060

This contract is the presentation half of 0060 §2g ("captions
shrink toward zero"): the more the card is machine-composed, the
less any model authors. When the parse-plan lands, classes above
map 1:1 to relation primitives — the contract survives the
architecture swap unchanged.
