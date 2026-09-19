# Contract_Governance_Layer — the governance graph's data contracts

**Status: DRAFT — born with the M7 batch (contracts-first, Q5);
RE-HOMED TO M8 by Sunny's 2026-09-18 re-scope ruling: governance
is its own layer, DESIGNED at the M8 sitting before any build or
serve (his positions recorded in M8 DESIGN INPUTS below); his
gap-check at the M8 design flips RATIFIED.** Fifth document of
the contract system. This layer is the CURATION RECORD: human
acts, blessed vocabulary, drafted and approved English — the
graph's memory of Sunny's judgments.

## DESIGN_SECTIONS (governing this layer)

| ds_id | says (short) | status | home doc |
|---|---|---|---|
| ds.governance_vocabulary | `description · term · usage · disposition · proposal · acronym · person · agent · role (+ drift)`; edges describes / performed_by / approved_by / used_by / supersedes / assigns | RULED | Design_Graph_Engine L2 |
| ds.governance_serves | **RE-SCOPED (Sunny, 2026-09-18): governance is M8, NOT M7 — "make governance M8. plus we need to really design M8 before implementing." The Q2 "yes to fabric" intent stands, but nothing governance rides to Fabric until the M8 design sitting rules the node-vs-property question per item and an M8 brief is APPROVED. History: Q2 (2026-09-17) superseded the 2026-09-13 store-only ruling; this row supersedes Q2's serve-at-M7 landing** | RULED 2026-09-18 | this row (the supersession chain's home) + the registry row + the ledger |
| ds.speech_contract | a node's speech is its OWN aboutness; Scribe drafts land 'drafted'; ONLY APPROVED text speaks; empty = counted | RULED 2026-09-09; APPROVED reached 2026-09-17 (M6) | Design_Graph_Engine — the English ladder |
| ds.blessed_name | R5.b: LLM-selected from vendor words, subset-gated, Sunny blesses by batch, only BLESSED voices | RULED 2026-09-12 | Grammar_Floor §R5.b |
| ds.journal | all user decisions persist; append-only journal, supersede-never-delete, replayed at boot | RULED (E1) | Design_Chatbot (state home rides the CI-B program, B13) |

## DATA_CONTRACTS

| dc_id | kind | what it is | writer | count (dev estate) | status |
|---|---|---|---|---|---|
| dc.blessed_name | node | one blessed voicing target (Sunny's batch blessings) | glossary seed (kg3@) | 113 | LIVE in store; serve + node-vs-property form = M8 design |
| dc.description | node | one description artifact (Scribe-drafted, status-laddered incl. APPROVED since M6) | describe.land | 30 (2 dev / 28 sepsis) | LIVE in store; M8 design input: "descriptions should be properties" |
| dc.agent · dc.role · dc.responsibility | node | actor/rights rows | kg3 acts | 1 each | LIVE in store; actors ruled NODES (M8 input); serve at M8 |
| dc.person · dc.term · dc.usage · dc.acronym · dc.disposition · dc.proposal | node | journal-fed citizens (may be 0 on estate boots) | kg3 acts / journal replay | 0 in estates | LIVE store citizens; serve decision at M8 |
| dc.describes · dc.performed_by · dc.approved_by · dc.used_by · dc.supersedes · dc.assigns | edge | the governance walk | kg3 acts | measured | store connections held as PROPERTIES, derived to edges by connect.py at read (see FG3); the M8 design picks the physical form |

## M8 DESIGN INPUTS (Sunny's positions, 2026-09-18 — the M8 sitting ratifies or overrules each)

| id | his position / the open question | status |
|---|---|---|
| M8-I1 | "actors should be nodes" — person · agent · role. The strongest case measured: 113 blessed_names point `approved_by` at person:sunny, which does not exist as a node (0 person nodes — the hole is counted, see FG3) | HIS POSITION, to ratify at M8 |
| M8-I2 | "descriptions should be properties" — the approved text already lands as a property on the target node (file, pbi_report) since M6; the description NODE would retire, its act history (author · status · basis · timestamps) re-homing to the journal | HIS POSITION, to ratify at M8 |
| M8-I3 | "records in general should not be nodes" — the general law: act records (blessed_name · responsibility · the journal citizens) fold into properties on their targets or stay journal rows, unless a record earns node-hood by the actor/many-to-many tests | HIS POSITION, to ratify at M8 |
| M8-Q1 | blessed_name under M8-I3: fold to column properties (blessed_words · blessed_by · blessed_at) — but the column's writer is the extractor, the blessing's writer is Sunny's batch; ONE WRITER PER FIELD must survive the fold | OPEN — M8 sitting |
| M8-Q2 | responsibility under M8-I3: it is a relationship WITH data (kind=dba) between a role and an artifact — property on which side, or the one record that stays reified? | OPEN — M8 sitting |

## CONTRACT_FIELDS

| dc_id | field | writer | rules | checks |
|---|---|---|---|---|
| dc.description | status | the machine at draft ('drafted'); SUNNY's act to 'approved' (recorded as estate data — the M6 precedent) | the CLOSED set incl. approved (registry 1.47.0) | kg3 refusal tests |
| dc.blessed_name | target · words | the namer seat + Sunny's blessing | GATE-SUBJ subset gate; machine-untouchable when blessed (THE FIELD LAW) | gate battery + registry seed |

## CONSUMERS

| dc_id | consumer | reads | re-verify |
|---|---|---|---|
| dc.blessed_name | sc.grammar_render | words at every voicing position | verbatim suites |
| all governance types | sc.fabric_export | NONE until M8 (the 2026-09-18 re-scope; SERVED_LABELS re-bases to consumption-only at the unwind) | export census |
| dc.description | the boot loader → file/report nodes | APPROVED text only | the M6/M7 field tests |

## TESTS

| test_id | proves |
|---|---|
| test_connection_census · test_part_edges | birth edges, journal citizens |
| test_graph_export (M7 rows) | the served governance tables |
| the kg3 refusal suite | the closed vocabularies |

## FINDINGS (from populating this contract)

| id | finding | kind | status |
|---|---|---|---|
| FG2 | the LLM cage's mechanical form vs the prompt's ruled purpose clause: the Scribe shape ends "for <purpose>" — purpose words (monitoring/tracking/quality/outcomes…) are BY CONSTRUCTION inferences beyond the anatomy; cage v2 flags them (27/28 at the M7 batch), Sunny accepts by eye per batch (M6 + M7 precedent) | found at the M7 batch cage, 2026-09-18 | OPEN — a later ruling picks the standing form: accept-by-eye per batch (today's law) vs a closed purpose-word allowance as registry data |
| FG1 | the governance layer's state-doc homes are thin: ds.journal and the acronym/total-score laws live in Design_Chatbot prose without contract-grade anchors (CI-B4/B13 territory) | known audit debt, restated at this doc's birth | OPEN — the CI-B program's sitting |
| FG3 | the M7 governance serve shipped NODE tables with almost no EDGE tables: the store holds governance connections as node PROPERTIES (description.about · responsibility.about/holder · blessed_name.target/approved_by · author), connect.py derives them into edges at read time, and the export projected none of them — 7 node parquets landed, 1 edge parquet (executes); the served nodes sat unconnected. Also counted: person:sunny referenced 113× but never minted as a node; blessed_name has NO Connection_Ledger row and no connect.py walk (the acronym walk reads label 'acronym', 0 nodes) | found at Sunny's load attempt, 2026-09-18 | CLOSED AS M7 SCOPE by the re-scope ruling (governance withdrawn); the underlying design question = the M8 sitting's first item |
