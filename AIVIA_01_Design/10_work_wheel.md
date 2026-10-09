10_work_wheel.md

Status: CONSOLIDATED 2026-10-06 at Sunny's ruling ("my goal is
to have one integrated design doc instead of decisions living
in too many docs") — the standing law of Brief_Packaging
(stamped 2026-10-04) and Brief_Preflight (2026-10-06) folds
into this phase pair; both briefs are SUPERSEDED pointers now.
Current artifact: ai01_sqldesc-0.5.5. Sunny owns it.

Design description:
- Phase 10 is the WORK WHEEL: the engine, packaged to travel.
  It parses SQL, renders technical descriptions, links PBI
  reports, writes business cards and Business Terms through
  the LLM seat, and lands everything in ai_delivery.json — on
  any tenant, with nothing of the estate inside it.
- The law it implements is the wall (ruled 2026-09-18):
  ENGINE-OUTBOUND ONLY — the engine may travel to work;
  nothing of the estate travels with it; work data never
  comes back.

The decisions (all previously stamped where cited; gathered
here verbatim-in-substance):

D1. TWO WHEELS, NEVER CONFUSED (2026-10-04): `aivia01` serves
    HER Fabric tenant (chat estate; never travels to work);
    `ai01-sqldesc` is the work wheel, this phase's artifact.

D2. THE ALLOWLIST + MANIFEST EQUALITY (2026-10-04): a
    work-bound wheel is legal ONLY when its contents equal the
    ruled allowlist exactly — checked mechanically at build,
    refused loud on any drift. The allowlist lives in the
    contract; the wheel carries its own MANIFEST.txt as data.

D3. WHAT TRAVELS (2026-10-04; LLM AMENDMENT 2026-10-05,
    "approve the wheel change"): the engine modules + the two
    LLM phases (business_descriptions, business_terms) +
    ai_delivery + the CLI + the ScriptDom DLL + the ratified
    kind library. NEVER: business_walk, chat/loader modules,
    AIVIA_01_Data/**, .env, any key, the test suites (locks
    stay home — they prove the CODE at build; the preflight
    proves the ENVIRONMENT at run, D8).

D4. THE KEY LAW (2026-10-05, amended at the rehearsal;
    DEGRADE RETIRED 2026-10-08, Sunny — effective wheel
    0.7.0): the key NEVER rides. The seat reads
    OPENAI_API_KEY from the environment FIRST (the notebook
    sets it from a vault/workspace secret), the repo's .env
    reader second. Missing or failed key = a BLOCKING
    preflight FAIL like any other — the sequence stops, the
    runner fixes it, nothing is delivered (her ruling: "if
    the key failed, fail loudly, don't deliver anything").
    The 2026-10-05 honest-degrade path (technical voice, no
    terms) is RETIRED; it stands in code only until 0.7.0
    ships.
    THE SEAT SPEAKS UNCOMPRESSED (find #6, 2026-10-06): the
    client requests Accept-Encoding identity — Fabric cluster
    images carry stale decompressors that die on compressed
    responses (the TypeError that floored 151 nodes); skipping
    the decoder entirely works on ANY cluster, work's included.

D5. THE BRAND SCRUB (2026-10-05, "replace aivia with ai
    everywhere in the wheel"): staged COPIES are scrubbed
    case-preserving; repo sources keep the true AIVIA_01
    citations; a lock asserts no member carries the string in
    any case, any byte.

D6. RUNTIME-OFFERED EVERYTHING (2026-10-04/05/06, the
    rehearsal ladder): the wheel ships NO data and NO homes —
    the runner offers them: --dict (the 02 words), the names
    asset (AI_NAMES_DIR, auto-offered when 03_chat_bot sits
    beside the dictionary), the corpus (AI_SQL_DIR, deliver
    sets it), the DLL (packaged, env-var route), the key (D4).
    Absence of an optional offer is HONEST (fallback words,
    blessed-only names), never fatal. The repo-relative
    default class is CLOSED (the parents[1] sweep,
    2026-10-05).
    THE OFFER-READ LAWS (rehearsal finds #4/#5, 2026-10-06):
    an offer is read AT CALL TIME, never frozen at import —
    the loader re-reads SCRIPTDOM_DLL on every lookup (find
    #5: a module-level constant froze an empty pointer the
    moment anything imported the engine). A pointer at a path
    that no longer exists is CLEARED, never trusted (find #4:
    as_file() can hand out a self-deleting temp copy); the
    packaged DLL is staged to a STABLE dir by our own hand.

D7. THE CLI SURFACE: ai-describe <sql> <out> [--dict] ·
    --reports <tmdl> <sql> <out> [--dict] [--business] ·
    --deliver <tmdl> <sql> <out> [--dict] (the Collibra
    chain: 08 -> 05 -> 06 -> 07 cards -> 09 terms ->
    ai_delivery.json + the official txt) · --preflight (D8).
    AMENDED 2026-10-08 (D14, wheel 0.7.0): two new doors,
    build() (free: 05+06+08 + the 13 stamp) and describe()
    (paid: 07+09+10+12). deliver() SURVIVES as the one-call
    wrapper — build then describe, nothing more (her ruling:
    keep it).

D8. THE PREFLIGHT + THE REFUSAL (2026-10-06, her ask after
    the httpx find; built red-first): one zero-cost check of
    EVERY prereq before any paid call — report-all, every
    FAIL names its fix; and deliver() RUNS it first, refusing
    on ANY failure — the missing-key exception retired with
    D4's degrade (2026-10-08; effective wheel 0.7.0).
    No paid call ever fires into a broken environment —
    mechanically enforced. The check set is closed; a new
    trip-wire earns a row + its lock, dated.
    AMENDMENTS same day, from the rehearsal:
    - THE SEAT CHECK CONSTRUCTS (the httpx2 find): never
      guess transport library names — import openai and
      construct the client with a dummy key (zero network);
      a missing dependency fails with its REAL message.
      (openai 3.x moved from httpx to httpx2; the check that
      hardcoded "httpx" failed a healthy environment.)
    - ORDER (find #5): the preflight stages the DLL pointer
      BEFORE any engine import — checks must never poison
      the state they check.

D9. THE ONE-WHEEL LAW (2026-10-05, learned at the rehearsal):
    exactly ONE sqldesc wheel in a Fabric environment, ever —
    two versions under different package names silently fight
    over the same module files. Delete old before publish;
    STOP the session after every publish (old sessions never
    see a new environment).

D10. THE VERSION LADDER: any byte change to the artifact
    bumps the version — 0.5.0 LLM phases, 0.5.1 env-first
    key, 0.5.2 names offer, 0.5.3 corpus offer, 0.5.4
    preflight, 0.5.5 the refusal, 0.5.6 the construct check
    (httpx2), 0.5.7 stable DLL staging + dead pointers
    cleared, 0.5.8 call-time env reads + preflight stages
    before imports, 0.5.9 the seat speaks uncompressed
    (find #6), 0.6.0 the work scale-up (D11 path 2 + D12 +
    D13 in one ladder step, 2026-10-07). The packaging lock
    pins the name to the builder's VERSION so a changed
    artifact can never ship under an old number.

D11. MULTI-WORKSPACE TMDL (ruled 2026-10-07, her work
    scale-up — "path 1 today, path 2 on the docket";
    PATH 2 BUILT same day, wheel 0.6.0):
    - Files/03_tmdl/ (the 2026-10-08 naming law; was tmdl/)
      may hold one SUBFOLDER PER SOURCE WORKSPACE;
      read_models walks recursively and model identity = the
      path relative to 03_tmdl/ ("WS One/Fix Twin") — top-level
      models keep bare names, so the flat layout stays legal
      and unchanged. Same-named models in two workspaces
      coexist; the qualified name rides through 08/09/
      blessings whole.
    - The preflight REFUSES on bare-name collision (names the
      twins and their folders) and its tmdl count walks
      recursively — the eyeball is retired.
      Locks: test_08 l8+l9, test_10_incremental_delivery
      collision test.

D13. THE VIEW CLASS (ruled 2026-10-07, her work scale-up —
    "we need to add views, there are hundreds"; BUILT same
    day, wheel 0.6.0 — locks: test_05 view class x3): the
    three view wrappers
    (CreateViewStatement / CreateOrAlterViewStatement /
    AlterViewStatement) unwrap to their single SelectStatement
    the way the proc trio unwraps to its StatementList — the
    SELECT then maps scopes/structures/predicates unchanged;
    file identity stays the filename. Declared-column-list
    headers (CREATE VIEW v (a,b) AS) are OUT of this slice —
    the SELECT's own names speak; flagged for a follow-up
    ruling only if a work view renames via the header.

D12. INCREMENTAL DELIVERY (ruled 2026-10-07; BUILT same day,
    wheel 0.6.0): described = DONE. deliver() keeps a
    content-hash ledger (10_corpus_ledger.json in <out>); a
    file whose hash is unchanged is never re-sent to the seat
    — its 07 card text and 09 terms are reused from the prior
    sheets (07: skip_files carries prior rows VERBATIM behind
    a refusal when the prior sheet can't supply them; 09: the
    L13 files_in_run carry, no refusal — a described file may
    honestly hold zero terms); new TMDL tying a NEW report to
    an unchanged file re-ties the existing text for free.
    Changed hash or `force=True` = full re-describe. THE
    BATCH DOOR (her 3.2 ask — no manual typing, ever): the
    runner uploads everything; `max_new=N` takes at most N
    not-yet-described files (name order); files beyond N are
    DEFERRED — a third class, dropped from the run entirely
    (defer_files: no rows, no carry, no refusal; a later run
    takes them). The run says it: "N described (K already
    done), M remain". The ledger records ONLY what this run
    described, only after the paid chain succeeded (the
    no-key degrade is retired per D4's 2026-10-08 amendment —
    an unkeyed run REFUSES and records nothing). The skip
    lands BEFORE 07 spec construction (fact voices are paid —
    a skipped file costs zero, voices included); 05/06/08
    always build the WHOLE corpus (local, free — the graph
    stays whole; FROM the D14 split they build in the BUILD
    cell, not per paid run).
    Accepted trade (her 3.1): an unchanged file's text never
    re-reads later arrivals.
    Locks: test_10_incremental_delivery x7, test_07 skip x2 +
    defer x1, test_09 l16 + l17.

D14. THE SPLIT + THE STAMP (ruled 2026-10-08, Sunny — one
    build, wheel 0.7.0, with the step-table renames in
    10_work_wheel_data_contract.md):
    - TWO CELLS: build() = the free whole-corpus work (05
      graph, 06 technical, 08 links) — run it when the input
      folders change; describe() = the paid batch (07 cards,
      09 terms, 10 ledger, 12 delivery) — run it repeatedly
      until "0 remain". deliver() = build + describe in one
      call, kept as the shortcut.
    - THE STAMP (step 13): build() writes
      13_build_stamp_output.json — a content hash of
      01_sql_input (the build-side twin of the 10 ledger:
      the ledger says what the seat described, the stamp
      says what corpus the build saw).
    - THE GUARD: describe() recomputes the hash FIRST; a
      mismatch REFUSES with "run the build cell first" — no
      paid call against a stale graph, mechanically enforced.
    - THE SEQUENCE LAW (her words): cells run in order; any
      FAIL stops the session — fix, re-run that cell, only
      then proceed. No cell runs past a failing earlier one.
    - DELIVERY MEMBERSHIP moves to delivered-goods-only with
      completeness lists — shape owned by the 09 contract
      (its 2026-10-08 amendment), not re-stated here.

D15. THE 0.8.0 SLICE (RULED 2026-10-08 evening, the view-test
    arc — the 47080 lesson, her reopen of the floor; contracts
    amended same day: 06 R8 flip, 07 V-1 + awaiting_human, 09
    awaiting_human; BUILD PENDING):
    - COMMENT-FIRST: the inline comment is the meaning, first
      choice in every voice; a card never writes raw digits a
      comment names. The SQL is the ONE meaning store — no
      side dictionary, no registry row, the comment stored
      nowhere else (her ruling; high-occurrence numbers may
      earn a store later, recorded option only).
    - THE HEADER Description: line -> the file card's
      first-choice wording.
    - BASIS GAPS go to HER, not to repair rounds and never to
      a technical fallback: status awaiting_human, questions
      named, publish skips; her verdicts = fix the SQL
      comment / let it show / keep it out.
    - THE VIEW TIE: build08 learns the view consumption
      patterns (NativeQuery SELECT ... FROM <object>, and
      [Item="..."] table imports) so views reach their
      reports — the first tenant's views are all reportless
      today, and reportless terms never publish.
