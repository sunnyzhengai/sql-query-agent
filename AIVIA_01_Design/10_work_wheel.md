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

D4. THE KEY LAW (2026-10-05, amended at the rehearsal): the
    key NEVER rides. The seat reads OPENAI_API_KEY from the
    environment FIRST (the notebook sets it from a vault/
    workspace secret), the repo's .env reader second. Missing
    key = the ruled HONEST DEGRADE: technical voice, no terms,
    said out loud — never a crash, never a silent downgrade.

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

D7. THE CLI SURFACE: ai-describe <sql> <out> [--dict] ·
    --reports <tmdl> <sql> <out> [--dict] [--business] ·
    --deliver <tmdl> <sql> <out> [--dict] (the Collibra
    chain: 08 -> 05 -> 06 -> 07 cards -> 09 terms ->
    ai_delivery.json + the official txt) · --preflight (D8).

D8. THE PREFLIGHT + THE REFUSAL (2026-10-06, her ask after
    the httpx find; built red-first): one zero-cost check of
    EVERY prereq before any paid call — report-all, every
    FAIL names its fix; and deliver() RUNS it first, refusing
    on any failure except the missing key (D4's degrade).
    No paid call ever fires into a broken environment —
    mechanically enforced. The check set is closed; a new
    trip-wire earns a row + its lock, dated.

D9. THE ONE-WHEEL LAW (2026-10-05, learned at the rehearsal):
    exactly ONE sqldesc wheel in a Fabric environment, ever —
    two versions under different package names silently fight
    over the same module files. Delete old before publish;
    STOP the session after every publish (old sessions never
    see a new environment).

D10. THE VERSION LADDER: any byte change to the artifact
    bumps the version — 0.5.0 LLM phases, 0.5.1 env-first
    key, 0.5.2 names offer, 0.5.3 corpus offer, 0.5.4
    preflight, 0.5.5 the refusal. The packaging lock pins the
    name to the builder's VERSION so a changed artifact can
    never ship under an old number.
