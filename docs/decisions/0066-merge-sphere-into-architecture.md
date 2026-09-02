# ADR 0066 — One system-model file: SPHERE merges into ARCHITECTURE

**Status:** ACCEPTED 2026-09-02 — Sunny's ruling ("i think we only
need one"), analysis concurring. SPHERE.md retires; ARCHITECTURE.md
becomes the single system-model blueprint, organized BY the Sphere
model, with a build status per section.

## 1. Context

ARCHITECTURE.md (born 2026-07-18, the POC era) and SPHERE.md (born
2026-08-25, the design-debate era) were both hand-authored narrative
describing the same system. The split was historical accretion, not
design — unlike SPEC/TEST_MAP, whose separation is structural
(hand-authored law vs generated projection) and stands.

The evidence the split was harmful:

- **Three rival layer models coexisted:** ARCHITECTURE's three layers
  (July), SPHERE's four shells (August), SPEC §4's five node-sort
  layers (the pinned vocabulary, ruled 2026-08-19). Two narrative
  files maintaining rival models of one thing is where the
  2026-09-01 audit found its drift.
- **The supposed benefit was not delivered.** The split's rationale
  was "current position vs destination" — but SPHERE itself never
  marked built vs unbuilt, so readers could not tell shipped behavior
  from design intent anyway.
- ARCHITECTURE's remaining content was largely duplication
  (native-parser rationale restating ADR 0001 against the
  README rule that ADRs are the canonical home; a design-decisions
  table duplicating decisions/README) and archaeology (the superseded
  question-flow section).

## 2. Decision

1. **One file, `ARCHITECTURE.md`** — the conventional name newcomers
   and tools expect. Its organizing model IS the Sphere; SPHERE's
   ratified prose transplants intact (ADR 0057's model is unchanged —
   this ADR moves its home, not its content).
2. **Every section carries a build status** — `BUILT` / `PARTIAL` /
   `DESIGN` — the SPEC per-axiom honesty device applied to narrative.
   The temporal distinction the two files encoded now lives inside
   one file, explicitly, instead of between two files, implicitly.
3. **Deleted in the merge** (rationale lives in the ADRs; git keeps
   the lineage): the three-layer diagram (SPEC §4 is the layer
   vocabulary), the superseded question-flow section (ADR 0062 is
   the record), the native-parsers deep-dive (→ a paragraph + ADR
   0001), the design-decisions table (→ decisions/README), the
   deployment section (→ REFERENCE_ARCHITECTURE).
4. **Registry surgery:** the `sphere` component merges into
   `architecture`; its 9 ADRs re-route; `satisfies` becomes the
   union (D, S, J, R); `current_through` = 0066. SPHERE.md is
   deleted (recoverable from git).
5. **ADR 0057 is NOT superseded** — its decisions stand in full. It
   gains a location note (the model now lives in ARCHITECTURE.md),
   per the never-silently-edit convention.

## 3. What this is NOT

- NOT a demotion of the Sphere model — the opposite: it becomes the
  organizing frame of the primary architecture document.
- NOT a precedent for merging SPEC/TEST_MAP or any authored/generated
  pair — that separation is structural and stands.

## 4. Consequences

- The three-rival-layer-models failure mode dies permanently: one
  narrative model (the shells), one formal vocabulary (SPEC §4).
- Built-vs-unbuilt marking exists for the first time in narrative.
- docs/architecture drops to 13 files; the `sphere` component key
  retires; all closure checks police the re-route.

## 5. Relations

- **ADR 0057** — the model itself; unchanged, re-homed.
- **ADR 0048 / the hierarchy ruling (2026-09-01)** — this amends the
  blueprint tier, which is why it needs an ADR.
- **The 2026-09-01 audit** — found the drift this merge prevents.
