# ADR 0081 — The birth-edge law: no node is alone; the connection census and the integrity battery

**Status:** ACCEPTED 2026-09-07 — born from Sunny's review of the
first two rows of a code-embedded exemption list ("a term should
not be alone — a term is deduced from a file's SQL; a usage event
is connected to the user and the item it used"), both overruled.
**Component:** architecture. Plan/review:
`AIVIA_Design/Audit_Graph_Integrity_Plan.md` (ratified) +
`Audit_Graph_Integrity_Review.md` (23 kinds classified). Built in
five Sunny-reviewed steps, each test-suite-first.

## The law

**No node is alone.** Every node was deduced from something, and
that deduction is a TRAVERSABLE EDGE — "why do you exist?" is
answered by walking, never by reading prose properties. This is
the L0 lineage guarantee applied to the governance world with the
rigor the SQL world already had (resolves_to, draws_from,
conservation).

**The connection census** (census 1's successor — the reachability
exemption list died under review):

```
birth-edged ⊎ counted-missing ⊎ rooted == total store nodes
```

- The per-kind expected-edge table is the **Connection_Ledger**
  registry sheet (never a code dict — the literal law), closed at
  birth: a new kind declares its row before its first write or the
  census fails.
- **counted-missing** is honest engine debt, per node, with its
  landing step named in the ledger — never ruled silence.
- **rooted** is exactly the estate root (the db node carrying the
  registration trace) — checkable: rooted == 1.

## What the five steps landed (registries 1.21.0 → 1.25.0)

1. **The adjacency walks the governance world**: usage—about→item,
   description—describes, responsibility—assigns, disposition—
   rules_on, proposal/redaction—about, concept—minted_by,
   meaning_twin—translates→file, and the KG1 spine
   (db—contains→schema—contains→table) — connections that existed
   as properties and were invisible to traversal.
2. **Term origins**: append_term REQUIRES derived_from (LC3-F6:
   "no node is alone — a term cites the act it was deduced from");
   the junk self-about died (the KG3 spine carries real targets);
   blessed vocabulary cites its confirming event — the user's
   click becomes a walkable edge.
3. **Person nodes**: actors minted on first act (person/agent/role
   by prefix, idempotent); every authored node walks —by→ its
   actor (one pass over all nodes, no kind list); the user tree
   has its trunk. Actor kinds joined the KG1 node catalog via the
   converter's APPEND_ROWS mechanism (PATCHES' sibling: recorded
   rulings that ADD rows to xlsx-born sheets).
4. **Part edges**: conditions—belongs_to→scopes,
   parameters—belongs_to→files; condition→scope→file is two
   pure-traversal hops; all four tree-born pseudo-citizens
   (condition, parameter, derived column, drift) documented as
   edged-pseudo — outside the store census by ruling, never
   undocumented. (Estate fact recorded: the sepsis corpus declares
   ZERO tree-grain parameters — it lacks the IF-default pattern.)
5. **Root edges**: exclusions store the estate root reference at
   write and walk excluded_from→root; the root ruling is a census
   assertion.

Live sepsis numbers at landing: 5017 birth-edged + 0
counted-missing + 1 rooted == 5018; missing kinds: none;
unledgered: none. run_event remains ruled missing-counted (no
target stored — future debt, on record).

## The integrity battery

The design doc gains the catalog of every standing equation that
continuously audits AIVIA — twelve entries, one list (conservation,
homomorphism, resolution, voicing, speech, searchability,
connection, verbatim, literal census, mirror-checks, claims
ledger, validators/shakedowns). "What audits this system" is no
longer folklore.

## Relations

0080 (the censuses this extends; census 1 superseded) · the
literal law (Audit_Literal_Law_Plan — the ledger is registry data;
the exemption list was its offense #3) · the user-tree design
(person nodes are its trunk) · Twin_Graph_KG ruling (the lineage
guarantee at L0).
