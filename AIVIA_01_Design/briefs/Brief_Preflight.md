# Brief_Preflight — SUPERSEDED 2026-10-06 (same day as birth)

**The standing law moved to `10_work_wheel.md` D8 + the 10 contract** (her consolidation ruling). Historical record below; new amendments land in the 10 pair ONLY.

---

# Brief_Preflight — the wheel's run-time prereq check

Status: RETROACTIVE PAPERWORK, her ruling 2026-10-06 ("i
actually broke my own rules by asking you to code first") —
the code landed 2026-10-06 at the rehearsal (wheel 0.5.4,
commit d55043a); this brief + contract + the deliver-refusal
lock land the same day to close the breach. Homed under the
packaging family: the preflight is a work-wheel command, so
Brief_Packaging's laws are its parents. Sunny owns it.

## Why it exists (the rehearsal's four trip-wires, one night)

Dueling wheels ate the modules; the seat's httpx dependency
never installed; the sql files were uploaded bare (no .sql);
the tmdl path pointed at nothing. Each cost a run to discover.
One check, before any paid call, names them all at once.

## THE DATA CONTRACT

Who owns it: Sunny. Machine-written output; no LLM, no
network, no cost, ever.

Input:
- tmdl_dir, sql_dir, out_dir, dict_dir (optional) — the same
  four the deliver command takes; plus the environment
  (OPENAI_API_KEY presence, SCRIPTDOM_DLL, importability).

Output:
- THE BOARD, printed: one line per check, "PASS <what>" or
  "FAIL <what> -> FIX: <the named fix>"; the closing census
  line "preflight: N pass / M fail".
- The return value: the list of FAIL lines (empty == go).
- The CLI exit code (`ai-describe --preflight ...`):
  0 == all pass, 1 == failures (scriptable gates).

The checks (closed set; growth = a new trip-wire earns a row
+ its lock, dated):
  1. the six engine modules import (the dueling-wheels trap)
  2. the ScriptDom DLL reachable (either of the loader's two
     ruled routes: packaged env var, repo libs/)
  3. httpx + openai import (the seat's dependency tree — the
     2026-10-06 find; fix names the PUBLIC-library route)
  4. OPENAI_API_KEY offered — presence ONLY, never printed
  5. sql_dir holds >=1 *.sql (the bare-name trap)
  6. tmdl_dir holds >=1 *.SemanticModel (the report-less trap)
  7. dict_dir (when offered) holds the three extraction files
  8. out_dir writable (probe file written and deleted)

Laws:
- REPORT-ALL: never stop at the first failure — one run, the
  whole board.
- EVERY FAIL NAMES ITS FIX — the error-contract philosophy.
- ZERO COST: no network, no LLM, no paid anything.
- THE REFUSAL (the automation ruling, 2026-10-06): deliver()
  RUNS the preflight first and REFUSES to start on any
  failure except the missing key (which stays the ruled
  honest degrade: technical voice, no terms, said out loud).
  No paid call can ever fire into a broken environment —
  mechanically enforced, not advised.

## Where the tests live (the shipping question, ruled)

Pytest suites NEVER ship in the wheel (Brief_Packaging's
never-travels law: locks stay home). They prove the CODE once,
at build, at home:
- test_packaging_wheel.py::test_cli_preflight_names_every_
  missing_prereq — the board names each trap, report-all,
  all-pass world clean
- test_packaging_wheel.py::test_deliver_refuses_on_preflight_
  failure — the refusal lock (red first, 2026-10-06)

The PREFLIGHT is the wheel's shipped self-check: it proves the
ENVIRONMENT, every session, wherever the wheel lands — the
notebook's Cell 0 for the human eye, and inside deliver() for
the machine's refusal. Two doors, one law.

## The manual command (hers, any tenant)

    sqldesc_cli.preflight(tmdl_dir, sql_dir, out_dir,
                          dict_dir=...)         # notebook
    ai-describe --preflight <tmdl> <sql> <out> [--dict <d02>]
                                                 # terminal
