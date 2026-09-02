# ADR 0075 — The check contract: checks are claims (spec:G4)

**Status:** ACCEPTED 2026-09-02 — Sunny's three questions on the
sloppy-ban incident, answered as LAW rather than acknowledgment. Adds
`spec:G4` to Group G.

## 1. Context — the incident, and why the axioms didn't stop it

GATE-REGEX-1's first version checked ONE hand-picked function by
substring scan. It was red-first (it could fire) — and still wrong,
because **fire and cover are different properties**: red-first proves
a check catches the corpse you fed it; it says nothing about the
frontier. Three failure classes, one incident:

1. **Conflated properties** — "it fired" was taken as "it covers."
2. **Same mind, same breath** — the check's author and the code's
   author were the same mind minutes apart; correlated blind spots.
   The repo has met this twice before (SKELETON-2's decoys found by
   an independent probe, not the author's tests; the verifier
   re-scoped as a measurement instrument for the same reason).
3. **Expedient default** — the strong prior art existed (`spec:G2`'s
   whole-surface `Uses ∖ S = ∅`) and a weaker local version was
   hand-rolled under momentum.

The memory files record such lessons as intent — and intent decays
(`axm:S2`'s own premise). This ADR converts them to data and checks.

## 2. Decision — spec:G4, three clauses

**G4 — checks are claims: fire and cover.**

    enforcement check  ⇒  frontier enumerated AS DATA, deny-by-default
    trusted check      ⇒  proven against an injected violation,
                          pinned as a PERMANENT test where feasible
    new mechanism      ⇒  names its pattern ancestor on the record

- **Clause 1 (the frontier law)** kills failure 1: a ban/invariant
  test carries its surface as data (sanctioned ⊎ named-debt = all
  users, computed, not hand-picked) with a deny-by-default totality
  assertion AND a staleness assertion (a retired debt item must
  update the list — the record matches reality in both directions).
- **Clause 2 (the injection law)** kills failure 2 for a single-mind
  world: the "different mind" is a mechanical adversary. A check is
  trusted only after an injected violation proved it fires — and the
  injection becomes a pinned meta-test (test the tester), never only
  a session anecdote. Where a live injection cannot be pinned (e.g.
  freshness checks that would need repo mutation), the scanner logic
  is factored out and meta-tested on fixtures.
- **Clause 3 (the ancestry law)** narrows failure 3 to a recorded
  act: an enforcement mechanism's test docstring or registry comment
  names the pattern it extends (G2 inclusion, 0042 planks, 0044
  strict-xfail, the frontier pattern). Writing "no prior art" is
  allowed — silently not looking is not.

**Right vs wrong, as data:** a check's output vocabulary is closed —
{pass, violation(named item)} — and its FRONTIER lists are the
definition of right: `computed_users == sanctioned ⊎ debt`, both
directions asserted. Wrong = any user outside the lists (new,
unsanctioned) OR any listed item no longer real (stale record).

## 3. Bindings

- Standing instances, cited (the axiom predates its name — the 0059
  Q3 precedent): `spec:G2`'s AST inclusion, the 0042 notebook planks,
  the 0044 strict-xfail exit gates, `TestRegexFrontier`.
- NEW: `tests/test_check_contract.py` — the injection law's exemplar:
  the regex-frontier scanner is factored to a pure helper and
  meta-tested on a fixture containing a planted violation (the tester
  is tested); plus the protocol assertion (the design protocol's
  step 4 carries the check contract).
- The design protocol (docs/INDEX.md step 4) gains the contract; the
  BOARD's exit-gate convention already conforms.

## 4. What this is NOT

Not a claim that authorship bias is solved — clause 2 mechanizes the
adversary for the *check* layer; the *content* layer keeps its
instrument (D2) and Sunny's L3 walks. And clause 3 stays partly
judgment: the law forces the question onto the record, not the answer.

## 5. Relations

0067 (docs are data — this is checks-are-data) · 0044 (red-first,
now half of a larger law) · 0047/G2 (the pattern ancestor of the
frontier form) · 0074/D2 (the instrument, clause 2 at content grain)
· the sloppy-ban incident (ec93a66's context, this ADR's §1).
