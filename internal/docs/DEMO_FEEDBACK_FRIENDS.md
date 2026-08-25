# Informal demo feedback — Fang + Bill (2026-08-23, recorded 08-24)

Audience: Fang — MS-certified database analyst, working Fabric admin
(the ICP). Bill — non-technical independent consultant. Six
happy-path questions on the workbench (walk-passed set).

## The headline find — Fang's real-world story

Last week at work Fang needed impact analysis ("will things break if
I change this table"). She asked **Databricks Genie — because that's
the tool her company uses.** Three product facts in one anecdote:
1. **Validated #1 use case for the analytics buyer: blast radius /
   impact analysis** — the lineage answer, exactly the question she
   watched AIVIA answer with 13 parse-grade readers.
2. **The real competitor is default-tool gravity**, not Copilot
   quality — users ask whatever is already installed.
3. **Fabric Marketplace placement is the moat mechanism**, not just
   distribution.
Also: asked whether Microsoft could clone AIVIA and kill it, Fang
(the target persona) answered unprompted: "Microsoft's Copilot is
dumb."

## Typed finds

- **F1 (display, PRE-CAPTURE RECOMMENDED): error tiles confuse
  users — collapse by default.** Both friends, after question one.
  Anti-flail/error chips read as breakage to outsiders. Remedy
  (display-only, W1 family): error/retry chips fold to a count
  badge, expandable; machinery stays inspectable, default view
  calm. Video viewers would misread them identically.
- **F2 (script calibration): the value landed on question two** —
  Bill: "no one can find which reports to use." The gap in the
  buyer's words is FINDABILITY OF THE TRUSTWORTHY THING, and it
  landed in ~90 seconds. The recorded demo's hook must reach that
  moment at least as fast; consider impact-analysis-first ordering
  for analytics audiences (per the headline find).
- **F3 (product idea, Sunny's scoping): suggested next questions.**
  Bill wants sidebar suggestions to keep the conversation going.
  Two distinct designs: (a) popular-questions from usage — needs the
  flywheel application half (0038-gated, roadmap); (b) machine-
  derived NEXT HOPS from the current display ("see its SQL · which
  reports use it · compare with its sibling") — data-shaped,
  buildable now, M4-clean (suggests OPERATIONS, not canned English),
  and is operations-are-the-product as UI affordance.
- **F4 (GTM idea): pilot cohort to "break it"** (Bill) — the
  surprise-round protocol as a standing program: pilot users try to
  break it, every break becomes a specimen → fixture. Natural slot:
  post-demo, pre-Marketplace. The methodology is already built for
  exactly this intake.
- **F5 (marketing): side-by-side proof** (Bill) — already owned:
  Round 4 (13/13 vs 8/13, approved claim set). Keep claims shaped
  as measured (vs the Fabric Data Agent), let audiences generalize.

## Disposition

F1 → display work order candidate (pre-capture). F2 → script
refresh input (review session). F3/F4 → PARKED for Sunny's scoping.
F5 → covered by the approved Round-4 claim set. Cross-referenced
from REVIEW_DEMO_READINESS.
