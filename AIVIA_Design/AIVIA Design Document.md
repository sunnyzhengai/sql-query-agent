**** AIVIA Description Level 0

AIVIA is a knowledge graph of a customer's analytical logic — built from per-file semantic trees over a shared technical vocabulary, from which decisions are derived as lenses, holding all metadata and governance artifacts as citizens of the graph itself — and it serves two directions: outward, generating catalog metadata from the estate; inward, matching user inquiries to the estate logic that answers them — and generating new estate when none exists, which enters the graph the same way everything else does.

**** Content Descriptions Level 1

The knowledge graph layer 1 - source dictionaries technical layer
- Node types: 
    -- db
        --- description
        --- as_of
    -- schema
        --- description
        --- as_of
        --- source
    -- table
        --- description
        --- as_of
        --- pk_columns
        --- grain
    -- column
        --- description
        --- as_of
        --- values
- Edge types: 
    -- db to schema: contains, as_of
    -- schema to table: contains, as_of
    -- table to column: contains, as_of
    -- table to table: joins_to, as_of, on, cardinality
        Normal join — one edge, one pair:

        ENCOUNTER ──joins_to──▶ PATIENT
           on: [[PATIENT_ID, PATIENT_ID]]
           cardinality: many_to_one

        Composite join — still one edge, two pairs:

        DX_COMMENT ──joins_to──▶ ENCOUNTER_DX        (pk_columns: [ENCOUNTER_ID, LINE])
           on: [[ENCOUNTER_ID, ENCOUNTER_ID], [DX_LINE, LINE]]
           cardinality: many_to_one
- Rules
    -- single source of authority, per object: every node and edge derives
   from the registered dictionary extract of the source system that
   owns it; nothing enters this layer except through a registered
   extract — nothing parse-derived, nothing hand-typed. The org's own
   dictionary (control_ tables, join mappings) is a registered source
   like any vendor's. 
    -- regenerability: the layer rebuilds from extracts alone  
    -- metamodel conformance: every node/edge matches the declared kinds and properties
    -- property-vs-node: in the regenerable technical layer, prefer properties; promote to nodes only on demonstrated need — promotion is a re-extract, not a migration.
    -- primary key: every table carries pk_columns when the dictionary declares one; tables without a declared key land in a counted gap list — never guessed. 
    -- join legality: a joins_to edge is legal only if declared by the
   dictionary of the source that owns its dependent (FK) side. Joins
   between two vendor tables must be vendor-declared — never invented
   by the org; joins from org tables into vendor tables are declared
   by the org's dictionary. A practiced join violating this is a
   compliance finding, not a graph edit.
   -- source inheritance: a schema belongs to exactly one source; tables/columns inherit source from the containment chain; a mixed schema is the recorded trigger to push source down a level.

**** Design-to-Code Protocol (Level 0 law; appended by Claude at Sunny's request, 2026-09-04 night — edit freely)

Six steps, in order, for every component; no step skipped:
1. Doc section ratified here first — the doc is the design authority.
2. Metamodel registry updated: the doc's node/edge/property
   definitions restated as a machine-readable data file. Code and
   tests consume the registry, never the prose; any doc change
   updates the registry in the same breath.
3. Every rule gets named checks, enumerated before code — a rule
   with no check is a hope (the rule-to-check map).
4. Fixtures authored: synthetic input + hand-authored expected
   output (the answer key), written before any builder exists.
5. Only then code — until the checks are green. Code never
   introduces a concept the registry doesn't have.
6. Discoveries flow backward: anything code reveals goes to the DOC
   first, then registry, then code — never patched in place.

Companion artifacts are indexed to this doc's levels and live
beside it (L2_* files); the doc holds WHAT and the rules, the
companions hold the machine-readable and test-facing detail.

Open items (technical layer): grain — pending Sunny's dictionary
check; extract format — the layer's input contract, next design
conversation before any code.