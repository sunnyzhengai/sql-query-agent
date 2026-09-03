# ADR 0076 — Compositional interpretation: capture once, interpret by grammar (spec:G5)

**Status:** ACCEPTED 2026-09-03 — Sunny's first-principles ruling
("we cannot enumerate all possible depth for all sql syntax; what's
the best approach to interpret AST"), built same day. Adds `spec:G5`
to Group G. Includes the ordered post-mortem: which contract failed,
and why the docs did not produce this approach on their own.

## 1. Decision

1. **Capture once.** The extractor's walk — already standing on every
   scalar node when it builds a predicate leaf — captures the
   subtree as a neutral IR (`ExprNode`: kind ∈ `EXPR_KINDS`, closed;
   role-ordered sides, subject first) instead of flattening to token
   bags. One walk of the ScriptDom tree, zero re-parses; the flat
   summary fields survive only as legacy fallback.
2. **Interpret by grammar.** The composer renders the IR by
   structural recursion: ONE rule per grammar kind, never a rule per
   shape — recursion handles depth, so no combination is ever
   enumerated. Generic rules guarantee grounded coverage of every
   expression; per-function phrasing (DATEDIFF, ABS) is an
   EVIDENCE-ORDERED overlay: a function earns a phrase when estate
   counts order it, never speculatively.
3. **Closed outcomes at every grain.** Kinds outside the rule table
   (`case`, `subquery`, `unknown`) are recorded with reasons and die
   counted (raw echo → gate refusal → counted empty). The kind
   frontier is data: `RENDERED_KINDS ⊎ UNRENDERED_KINDS ==
   EXPR_KINDS`, both directions (the G4 form).
4. **Checkers read the same truth.** Misattribution and
   selected-not-filtered accept a claim voiced via a DECIDING
   column's dictionary meaning (`_dict_meanings` bridge); a
   SELECT-only column's meaning deliberately still fails —
   role-faithful, not a loosening.

Result on the recorded estate (28 procs, 461 descriptions):
emptied 124 → 17, failed 2 → 0; every survivor of the ruled voice
classes ships; corpus instrument 11/11 throughout.

## 2. Post-mortem — which part of the contract failed us

Ordered by Sunny with the build. Three failures, in causal order:

1. **Conservation was quantified at the wrong grain.** 0044's law —
   every decision site handled-or-counted — is SITE-grain. A site
   could be "handled" while the extractor flattened the expression
   INSIDE it to token bags; totality at the coarse grain hid
   information destruction at the fine grain. The quantifier needed
   to be scale-invariant: handled-or-counted at every grain the
   parser provides.
2. **spec:G2 was read as a law about the entry point, not the
   path.** "Native parsers, never text" governed HOW we parse; it
   said nothing about what may be done to structure AFTER parsing.
   Flat token bags are text-shaped data — the regex era's output
   format — reappearing downstream of a fully compliant parser, and
   no law could see it. The same corpse sits in the git log three
   days earlier ("the parse was never missing, it was discarded"),
   at a different layer: the failure class recurs wherever structure
   is lowered before its consumer.
3. **The composer's input was never a named component.** No document
   ever asked "what representation does interpretation require?" —
   so the answer accreted as fields (`column`, then `func`, then
   `exprs`) instead of being designed. Meanwhile the codebase held
   its own precedent unnamed: the boolean layer (`_convert` /
   `_render`) has interpreted arbitrary-depth AND/OR/NOT by
   structural recursion for weeks. Because "structural recursion"
   was never articulated as a principle, its HALF-application (stops
   at the predicate leaf) was invisible as half.

**Why the Generator Clause did not fire in the record:** three beats
on one generator (LIKE-family ops → aggregates → DATEDIFF) were
fixed shape-by-shape, each green, before the first-principles
question was asked — and it was asked by Sunny, not forced by any
check. The instrument counts OUTCOMES (empties per class), which
kept improving; nothing in the design protocol demanded stating the
INTERPRETATION PRINCIPLE, so rule-per-shape was never visible as a
choice requiring justification.

## 3. Tightenings (landed with this ADR, as data)

- **spec:G5 — structure carried, never lowered.** Captured structure
  is carried AS STRUCTURE to every consumer; lowering to text or
  token bags before the point of use is a violation of the same law
  G2 states at the entry point. Corollary: interpretation rules are
  per-grammar-production; a rule-per-shape design requires a
  recorded reason (the question the protocol now asks).
- Checks bound to G5: the kind-frontier totality and compositional
  tests (test_skeleton_composer), the op frontier
  (test_op_frontier) as the layer-1 instance.
- docs/INDEX.md design protocol gains the question: "does this
  interpret per grammar production or per shape? per-shape needs a
  recorded reason."

## 4. Relations

0044 (conservation — the grain lesson) · 0047/G2 (the entry-point
half of the same law) · 0074 (the acceptance this renders for) ·
0075/G4 (the frontier form used twice here) · DESC-LEAF-1 and
OP-FRONTIER-1 (the shape-by-shape beats this ends).
