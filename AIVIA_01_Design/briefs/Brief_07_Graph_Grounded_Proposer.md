# Brief_07_Graph_Grounded_Proposer — the walk, bottom to top

Status: DRAFT — Sunny's walk, scribed by Claude 2026-10-04. This
replaces the first (dry) draft of the same day. ALL NINE
QUESTIONS RULED 2026-10-04, one sitting (Q5 carries THE ROOM
LAW + THE LINE SELECTORS; Q6 is the named supersession of the
inheriting field docket; Q7 fixes the checker deterministic,
LLM linker excluded; Q9: 07-local walk on the shared read
layer). BUILT AND ACCEPTED same day
(section H, Sunny: "accepted, run the cutover"): pseudo approved,
locks red then green (15 walk locks), live proving runs converged,
three card lines blessed via the ratify door, retirements
executed. The walk is the production 07 pipeline. At build time every ruling
is rewritten into 07_business_descriptions.md and its data
contract per the contract-amendments-first law.

The idea in one line: code walks the phase 05 graph from the
bottom up; at every node the LLM is handed only that node and its
children, speaks one plain-English description, and the
description is attached to the node — so every higher node is
written from finished sentences, never from raw SQL. The LLM
never walks and never chooses; it talks at each stop.

## Step 1 — the floor: predicates

The walk starts at a predicate node. It knows its own comparison
and its bound values ('Canceled' (2), the eight departments, the
0 that means All). Its children are column nodes, each carrying
its 02-dictionary description. That is the whole room: one
comparison, its values, its columns' meanings. The LLM writes one
sentence and it is attached to the predicate.

Nothing to invent from — the material for the census file's bad
sentences (subtype examples, the department list in the wrong
place) is simply not present at this rung.

Questions this step raises:
- Q1 — RULED 2026-10-04 (Sunny, in chat): world knowledge may
  choose the WORDS, never the FACTS. The model may re-express
  what the SQL and the dictionary say, in clinician English
  (decoding date arithmetic, as-of behavior, what a term means
  in general) — but every specific value, name, and number in
  the output must come from the SQL or the dictionary. No
  example values from the model's head, even industry-true ones
  ("such as inpatient, observation" is banned unless those
  values exist in the graph). Start closed; if the proving file
  reads too flat, loosen ONE notch only — examples allowed where
  the 02 dictionary stores the values as graph elements — never
  further. Polish is allowed, invention is not; the license
  loosens only toward the graph.
- Q2 — RULED 2026-10-04 (Sunny, in chat): THE SHORT NAME,
  ALWAYS. The traced root was never 06's wording — "the instant
  when the event was supposed to have happened" is Epic's
  verbatim dictionary description of EFFECTIVE_TIME; 06 stays
  closed and the dictionary's words stay verbatim, as context.
  The naming machinery already exists by prior ruling (THE
  NAMING LAW, Design_Proprietary_Term_Assets.md, 2026-10-04:
  ONE naming asset — the 03 abstracts, LLM-drafted once from
  the dictionary words, sunny_* overrides; a 07-local store
  REJECTED). This ruling does not re-home it (an earlier pin
  here said "stored on the graph node" — WRONG, corrected same
  day; the one-home law stands). What this ruling ADDS, two
  riders on the existing ladder:
  (a) COVERAGE: every column and table the walk's prose speaks
      must carry a ruled short name in the 03 asset BEFORE the
      07 build — the ladder's rung 3 (falling back to the R5
      description words) may serve floor rows but may never
      speak in LLM prose; a missing name stages for Sunny's
      eye instead of falling through. Rung-3 fallback speech
      is exactly what voiced Epic's phrase and taught the
      model "scheduled".
  (b) ENFORCEMENT: the checker fails any sentence that calls a
      column or table by anything other than its ladder name
      (sunny_*/blessed first, else the asset's short name) —
      naming is never re-done at description time.

## Step 2 — climbing: structures

An AND, OR, WHERE, or JOIN node reads its predicates' finished
sentences and merges them. Here the ladder's one real risk
appears: a parent cannot quote all its children or the text
grows without bound — it must condense, and condensing is where
facts get dropped.

- Q3 — RULED 2026-10-04 (Sunny, in chat, demonstrated on the
  census SQL's nine WHERE conditions): THE MUST-SURVIVE LAW.
  Three fact classes, assigned MECHANICALLY from where the
  predicate lives in the tree (top-level population path vs ON
  clauses — the prior estate's decisions-lens split), never by
  judgment:
  (1) POPULATION-SHAPING (filters, exclusions, windows, run-time
      choices): survive every rung with VALUES INTACT, to the
      card, each landing on its owning line per the
      line-ownership law. Eight departments at the floor =
      eight named at the card; "several departments" is a
      conservation break.
  (2) HOUSEKEEPING (linkage, data-quality): survive as ONE
      plain clause, values not carried ("records not linked to
      a patient"), landing in Excludes — S12 restated as a
      survival class.
  (3) PLUMBING (join mechanics, markers, split functions,
      special values AS mechanisms): dies at its own rung;
      voiced locally if the local sentence needs it, never
      rides up. The choice survives, its 0 dies; the match
      survives, its SELECT 1 dies.
  ENFORCEMENT: a conservation check at the card — every class-1
  value traces down to a predicate AND every class-1 predicate
  value appears on the card, both directions (the voicing-
  ledger precedent: silent omission has no constructible path).
  BRANCH SCOPE: must-survive runs up the population path to the
  card ONLY — fields are a side branch these facts never enter
  (the line-27 leak was a class-1 fact in the wrong branch).

## Step 3 — selections (scopes)

A scope node reads its structures' sentences plus what it
delivers. Scope sentences have been the loosest in the census
reviews ("required patient selections", "scheduled") because
scope's obligations were never written down.

- Q4 — RULED 2026-10-04 (Sunny, in chat, refined twice on the
  census file's location selection): THE SCOPE MUST-SAYS.
  (1) ONE ROW IS — always said: the selection's grain ("one
      row here is one revenue location chosen when running the
      report").
  (2) KEEPS — said ONLY when the scope owns membership
      conditions in its own WHERE, voiced under the Q3 classes
      (values intact / plain clause / silent). When the scope
      owns none — a parameter split, a bare carry — HONEST
      SILENCE, never filler (the prior estate's R7 precedent).
      "It keeps the locations picked" was caught as a circle:
      the choices are the thing, not a rule applied to it.
  OWNERSHIP BOUNDARY: a scope speaks only its own WHERE; an
  EXISTS sub-selection's condition voices INLINE on the parent
  line per the standing FACTS SHAPE LAW — no double counting.
  PER-SCOPE CONSERVATION: the Q3 value check runs per scope
  over the conditions that scope owns.
  FEEDS — proposed and REJECTED same day (one-home-per-fact):
  the consuming side's sentence owns the relationship ("kept
  when the event's department belongs to one of the chosen
  locations"); the consumed selection never restates it. A
  reader asking "why does this selection exist" is served at
  read time by the graph edge — the chat shows the consuming
  sentence beside the selection; nothing is stored twice.

## Step 4 — the top: the file card

The five ruled lines (One row is / Who's in it / Each row shows /
Time window / Excludes) are written from the scope sentences
below — finished English in, finished English out. Line ownership
stays exactly as ruled: positives on Who's in it, negatives on
Excludes, as-of lives only on Time window.

- Q5 — RULED 2026-10-04 (Sunny, in chat; her two questions —
  "did we make the LLM follow the graph?" and "do the 5 parts
  come from the graph?" — forced both halves):

  (a) THE ROOM LAW — the walk pinned per rung. The LLM never
  walks; code walks bottom-up and makes one call per node.
  Each rung's room, complete:
    PREDICATE — speakable: its columns' short names (Q2
      ladder), its bound values (spoken by their value-node
      names); context-only: the dictionary descriptions; not
      in the room: everything else.
    STRUCTURE (WHERE / AND / OR / JOIN / GROUP) — speakable:
      its child predicates' and child structures' FINISHED
      sentences; nothing else exists. ON-clause structures are
      class-3: voiced locally, die at the rung (Q3).
    SCOPE — speakable: its own structures' finished sentences,
      its grain, its payload kinds; not in the room: any other
      scope's conditions (the Q4 ownership boundary,
      structurally enforced).
    FILE CARD — speakable: its scopes' finished sentences,
      routed per line selector (below); not in the room: raw
      predicates, raw SQL.
    FIELD — speakable: its column's short name, its
      expression; context-only: the dictionary description;
      not in the room: ALL population facts (the line-27
      class dies at the source).
  A fact outside the room cannot be spoken — invention becomes
  a structural impossibility before the checker ever runs; the
  checker (Q7-Q8, open) verifies the residue.

  (b) THE LINE SELECTORS + LINE-BY-LINE ASSEMBLY. The graph
  decides CONTENT; the card decides PRESENTATION. The five
  lines stay — they serve the clinician reader (the tone
  law's territory) — but each line is a NAMED SELECTOR over
  the file's subgraph, never a writing choice:
    One row is      <- the delivery scope's grain
    Who's in it     <- class-1 positive predicates + the
                       run-time choice edges
    Each row shows  <- the payload kinds
    Time window     <- class-1 temporal predicates (window,
                       as-of, the cancel rule)
    Excludes        <- class-1 negative predicates + class-2
                       clauses
  Generation is LINE BY LINE: five calls, each line written
  from its selector's results only, its own conservation
  check, its own repair — a failed line reruns alone; code
  assembles the card. The one-home law stops being a rule the
  model obeys and becomes a wall it cannot see over (the
  as-of facts are never in the Who's-in-it room). The
  rejected alternative — a card whose structure mirrors graph
  topology — is faithful and unreadable; that artifact
  already exists and is the 06 technical description.

## Step 5 — the side branch: fields

Each delivered field reads its column (with its 02 description)
and its expression — and that is all. A field's walk never
reaches the population predicates, so the class of leak where a
field line restated the eight-department exclusion list becomes
impossible at the source, not caught after the fact.

- Q6 — CONFIRMED 2026-10-04 (Sunny, in chat, after the
  conflicting-laws demonstration on the Department field):
  FIELDS FLY BLIND TO POPULATION. This is a NAMED SUPERSESSION,
  not a silent fold: the earlier same-day field-docket clause
  ("...its owning scope's SHAPED filter lines — so a field
  sentence can say what the field means AND inherit the
  population truth") gave Law A: filters ride in the field
  docket as context, with an advisory don't-restate
  instruction. The room law (Q5) gives Law B: population facts
  never enter the field's room. A builder cannot obey both;
  line 27 was Law A's bill (the instruction held for 16 fields
  and broke on the 17th). RULED: Law B wins at the walk build;
  Law A carries a dated superseded rider from today and its CI
  lock (test_field_docket_v2_named_and_inheriting) retires at
  that build. Preserved from Law A's intent: the dictionary
  description stays in the field's room as context-only —
  understanding stays, population leaves.

## The checker at every rung

After each sentence, one deterministic check, both directions:
every specific claim (quoted value, proper noun, number) must
resolve to this node or its children; every must-say element
must appear. Unresolved claim = invention, fail. Missing
must-say = omission, fail. Fails go back as named objections,
repair budget as today (3).

- Q7 — RULED 2026-10-04 (Sunny, in chat, after the
  three-layer answer to her "do we rely on checks?"): THE
  CHECKER IS DETERMINISTIC, AND SMALL BECAUSE THE ROOM IS.
  Why a checker at all: the room closes what we HAND the
  model, not what it KNOWS — its world knowledge rides inside
  every call, so invention from memory stays possible (rare,
  never impossible), and omission (eight departments in,
  seven out, reading smooth) is invisible to any input-side
  design. Three layers: the walk decides content (code), the
  LLM phrases (the one loose layer — the fully deterministic
  version of this step exists and is the 06 text), the
  checker verifies (code). The two code layers pin the loose
  middle from both sides.
  The ruled mechanics: SPECIFIC CLAIMS are three kinds —
  quoted values, proper nouns, numbers; ordinary nouns (bed,
  room, stay) are free speech, the tone law's vocabulary.
  Matching is NORMALIZED DETERMINISTIC: case folded,
  punctuation stripped, simple plural fold, matched against
  four lists only — short names, value-node names, parameter
  plain names, blessed names. AN LLM LINKER IS EXCLUDED BY
  RULING — a probabilistic checker puts judgment back at the
  gate. The strictness cost is accepted and wanted: a true
  thing phrased unresolvably fails and repairs into the ruled
  vocabulary, which is also what makes every report read
  consistently. The check never grows again: not "don't say
  X" but "everything said resolves to the room" — one
  sentence of law covering leak classes not yet seen.
- Q8 — RULED 2026-10-04 (Sunny, in chat): THE CHECKER JOINS
  THE GATE, never replaces it. New named findings — room
  violation, conservation break, name violation — enter the
  existing objection-and-repair loop, budget 3. The shape
  checks stay (five lines, the scope must-says, SQL
  vocabulary ban, the never-list); the tone law stays
  prompt-side with Sunny's eye. V-1 GROUNDED VALUES is
  superseded at the walk build — the resolve-back check is
  V-1 grown to both directions. The pinned CI regressions
  (the semicolon, 'selects', 'language is 1') stay FOREVER —
  history locks, not content checks.

## What does not change

Tone stays prompt law (the clinician voice) plus Sunny's eye —
the checker never judges tone. The blessing registry stays her
RULING (amended 2026-10-04, THE RATIFY CLAUSE in the 07
contract: decision hers alone, write machine-executed at her
explicit ruling — the manual write died at corpus scale); the
ladder blessed > gate_passed > floor stands, extended to
card-line grain the same day. The
build-skips-blessed-rows idea stays out of scope (declined
2026-10-04, "leave as is").

- Q9 — RULED 2026-10-04 (Sunny, in chat): NO SHARED WALKING
  FRAMEWORK. The two phases walk differently — 07 is
  bottom-up, whole tree, every node once (describing
  everything); Phase III is question-driven pathfinding
  (visiting only what the route touches). Different machines,
  same graph. What is shared is ONE LAYER DOWN: the graph
  READ layer — one small read surface, the prior estate's
  read_api precedent (34 lines, the single door). The 07 walk
  builds 07-LOCAL on that read layer; Phase III writes its
  own pathfinder on the same layer when it opens. A framework
  built now would be designed for a phase whose questions are
  not yet designed — speculative structure, the thing a later
  ruling has to tear out.

## The amendment inventory (sweep run 2026-10-04)

Every standing passage the Q1 and Q2 rulings touch. Per the
contract-amendments-first law, each gets rewritten and agreed
with Sunny BEFORE this reopen's first red test. The sweep read
the design docs, data contracts, the card, and the test locks.

Q1 — words free, facts closed:
1. 07_business_descriptions.md, THE ESTATE BOUNDARY ("GENERAL
   DOMAIN KNOWLEDGE IS FREE — 'this is why we use LLM'"):
   NARROWED. Freedom now covers wording, decoding, and
   general explanation only; example values, names, and
   numbers from world knowledge are banned even when
   industry-true (the zone-3 close).
2. 07_business_descriptions.md, THE SURVIVING CHECKS ("quoted
   values + numbers must appear in the docket"): EXTENDED —
   the checked class grows from quoted values and numbers to
   example values and proper names, both directions per the
   walk's checker.
3. 07_business_descriptions_data_contract.md, the gate clause
   ("general domain knowledge is FREE — the gate polices
   docket"): same narrowing as (1).
4. business_descriptions.py SYSTEM_PROMPT ("USE YOUR DOMAIN
   KNOWLEDGE freely"): rewritten at build; today's S15–S18
   band-aid laws retire into the checker where mechanical.
5. Test locks re-pointed: test_domain_knowledge_is_free_
   estate_facts_are_not, test_prompt_carries_s15/s16_to_s18.

Q2 — the short name, always:
1. Design_Proprietary_Term_Assets.md, THE NAMING LAW: home
   and ladder UNCHANGED (one asset, the 03 abstracts; 07-local
   store stays rejected). Gains the two riders: prose-coverage
   (rung 3 never speaks in LLM prose) and checker enforcement.
2. 07_business_descriptions.md, THE NAME LADDER passage: the
   same two riders added where the ladder is consumed.
3. 07_business_descriptions_data_contract.md, the ladder-source
   clause (sunny_*/blessed > first synonym > R5 words): rung 3
   marked floor-only.
4. The 03 asset growth clause (Design_Proprietary_Term_Assets
   .md + the 03 contract): gains the ordering duty — the
   naming pass covers every column and table the 07 build will
   speak, BEFORE that build; gaps stage for Sunny's eye, never
   fall through to description-words speech.
5. technical_descriptions.py _payload_item (the 06-importable
   machinery 07's FACTS re-render through): the branch that
   drops the name when the output alias repeats the column
   token (and so speaks the dictionary phrase alone) is
   amended on the 07 overlay path — the ladder name always
   leads. 06's own floor register stays dictionary-words
   (consumption map unchanged).
6. Test locks extended: test_name_ladder_source_and_order,
   test_facts_speak_short_names, test_recordedness_speaks_
   the_ladder (+ a new lock: no rung-3 speech in prose rows).
7. test_07_business_descriptions_data_contract_sunny.md: the
   command list updated at build, as always.

Q3 — the must-survive law (sweep run + AMENDED same day,
2026-10-04, at Sunny's "amend all previous files" order):
1. 00_Architecture.md, Phase I business-description bullet
   ("preserves the population-shaping facts"): AMENDED — the
   word "preserves" now cites the formalized law (three
   classes, value conservation).
2. 07_business_descriptions.md: THE MUST-SURVIVE LAW block
   ADDED beside its siblings (line-ownership = its landing
   map; tone law). S12/RELEVANCE and THE FACTS SHAPE LAW stand
   unchanged — class 2 restates S12; the facts' one-line-per-
   top-level-condition shape is what class assignment reads.
3. 07_business_descriptions_data_contract.md: VALUE-
   CONSERVATION rider ADDED to the conservation clause; V-6
   MUST-SAY marked superseded-at-the-walk-build (presence
   grows to per-value accounting; V-6 stands until then).
4. At build, not now: the checker code, its red-first locks
   (seeded omission + seeded plumbing-climb tests), and the
   class-assignment reader over the 05 tree (the prior
   estate's decisions-lens split is the ported precedent —
   Brief_05_Prior_Art item 8, aisql/lenses/decisions.py).

Q4 — the scope must-says (sweep run + AMENDED same day,
2026-10-04; LANDING RE-POINTED 2026-10-05: the must-says build
moved from the walk build to build phase 09 — D3, the Business
Term card, 09_business_terms.md — where the scope card gains
its labeled shape: Definition / One row is / Keeps / Excludes):
1. 07_business_descriptions.md: THE SCOPE MUST-SAYS block
   ADDED, closing the standing "scope grain follows last"
   deferral in the DOCKET v2 section. THE FACTS SHAPE LAW
   stands unchanged — its EXISTS-inlines-at-parent clause is
   what the ownership boundary leans on.
2. 07_business_descriptions_data_contract.md: SCOPE arm ADDED
   to the V-2 template clause (check lands at the walk build;
   the current free-form scope grain stands until then).
3. At build, not now: the scope-grain card text
   (_GRAIN_INSTRUCTIONS in business_descriptions.py), its
   shape check, and red-first locks (a filler-KEEPS on a
   condition-less scope must fail; a foreign condition in a
   scope's text must fail).

Q5 — the room law + line selectors (sweep run + AMENDED same
day, 2026-10-04):
1. 07_business_descriptions.md: THE ROOM LAW + THE LINE
   SELECTORS block ADDED beside the other walk-reopen laws;
   the DOCKET v2 section gains a superseded-at-the-walk-build
   rider (the flat FACTS+CONTEXT docket is replaced by
   per-node rooms at that build; stands as written until
   then).
2. 07_business_descriptions_data_contract.md: CARD arm ADDED
   to the V-2 template clause (five lines stay as reader
   format; per-line calls, selectors, conservation, repair at
   the walk build); the DOCKET v2 clause gains the same
   superseded-at-build rider.
3. At build, not now: the walker code (one call per node), the
   per-rung room assembly, the five selectors, per-line
   checks, and red-first locks (a fact outside the room
   appearing in output must fail; a selector value missing
   from its line must fail).
4. Verified consistent, unchanged: the LINE-OWNERSHIP law (the
   selectors are its mechanical form), THE FACTS SHAPE LAW,
   the 06 technical description (named as the graph-topology
   artifact; the card never mirrors topology).

Q6 — fields fly blind (sweep run + AMENDED same day,
2026-10-04):
1. 07_business_descriptions.md, FIELD DOCKET v2 clause (Law
   A): dated SUPERSEDED rider added on the clause itself —
   stands only until the walk build; its CI lock
   (test_field_docket_v2_named_and_inheriting) retires with
   it; original text preserved below the rider.
2. 07_business_descriptions_data_contract.md, the docket
   clause: pre-existing drift caught by this sweep — the
   contract still said field dockets "keep the 10-03 shape
   until a later slice" though field docket v2 had BUILT with
   a passing CI lock; aligned, with the v2-then-superseded
   history written in.
3. At build, not now: remove the filter lines from the field
   room in code, retire the inheriting lock, add its
   replacement (population fact in a field's room must fail).

Q7+Q8 — the deterministic checker (sweep run + AMENDED same
day, 2026-10-04):
1. 07_business_descriptions.md, THE SURVIVING CHECKS: rider
   added — the resolve-back checker joins the gate at the
   walk build as named findings (room violation, conservation
   break, name violation); quoted-values check superseded
   there; passage stands until that build.
2. 07_business_descriptions_data_contract.md, V-1 GROUNDED
   VALUES: superseded-at-build rider with the full checker
   definition (three claim kinds, four match lists,
   normalized-deterministic, LLM linker excluded, budget 3,
   pins stay).
3. Verified unchanged: the repair-loop machinery (budget 3,
   objections named from findings), S10's grounded-numbers
   narrowing (carried into the checker), the pinned CI
   regressions (stay forever), the code-sightings queue
   (ungrounded finds still land sightings).
4. At build, not now: the checker code, the four match lists
   as build artifacts, red-first locks (a seeded
   memory-invention must fail; a seeded omission must fail; a
   paraphrased name must fail).

Q9 — 07-local walk, shared read layer (sweep run + AMENDED
same day, 2026-10-04):
1. 00_Architecture.md, Phase III section: ruling added —
   Phase III writes its own pathfinder; shared piece is the
   read layer only; no framework ahead of its design.
2. At build, not now: the 07 walker lands in 07's code with
   the one read surface named in its pseudo code; the import
   law (only the read surface touches the graph store) gets a
   structural lock, the prior estate's test_planks precedent.
3. Verified unchanged: 05's store/read shape (the walk is a
   consumer, no new graph properties — consistent with Q2's
   one-home verdict), the parked phase-02 connect code note
   in 00_Architecture (still Phase III's, untouched by this
   reopen).

DEBT FOUND AT THE PROVING RUNS (2026-10-04, named per the debt
law): the 05 mapper writes NO parameter resolve edges for
parameters inside table-function sub-selections (STRING_SPLIT's
@ServiceArea/@Location — their exprs land "unresolved"). The
walk works around it mechanically via the node's own stored
EVIDENCE (params_of fallback in business_walk.py, commented at
the site); the real fix belongs to the 05 mapper and closes
this ledger line when built.

Untouched by these two rulings, verified: the 02 contract
(dictionary verbatim — Q2 re-affirms it), the 05 contract (no
new node property; output_name stays the alias record), 03
chat's own lanes.

## Acceptance

The census totals file stays the proving file. The reopen is
accepted when a full bottom-up regeneration produces a card
Sunny reads clean with no new leak classes, and a fabricated-
proposal test proves the checker — not her eye — catches every
seeded invention.
