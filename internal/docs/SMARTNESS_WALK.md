# The Smartness Walk — L3 acceptance protocol (ADR 0051)

Sunny's protocol, written down so nobody has to remember it. Run ONLY
after the conversation suite (L2) clears its thresholds — L3 eyes must
never discover what L2 should have caught. Every rejection here
becomes an L2 fixture BEFORE its fix ships.

How to run: web UI, one sitting, in order, fresh conversation unless a
step says otherwise. Mark each step pass/fail with one sentence.

## The walk

1. **The four corpses, live.** Ask, in one conversation:
   - "how many metrics are there"
   - I added "how many metrics contain ED logic"
   - "how is Sepsis Case Encounters defined"
   - I added "which step is Sepsis Case Encounter in the metric Sepsis Case Encounters?"
   - I added "show me the sql of Sepsis Case Encounter"
   - I added "how is IP_SEPSIS defined"
   - I added "is there a sql file called IP_SEPSIS?"
   - "how is Sepsis Case defined"
   - "in Severe Sepsis Episodes, how is a patient diagnosed with
     severe sepsis"
   - I added "how many steps does it have"
   Pass: exact count; real definition; a did-you-mean over the two
   near-name siblings; step-level criteria (not the summary blurb).

2. **Memory test.** Continuing the SAME conversation, three follow-ups
   by pronoun only (e.g. "who owns it", "how many steps does it
   have", "which tables does it read"). Pass: no re-asking which
   metric; answers track the metric under discussion.

3. **Pointer chase.** One two-hop question (e.g. "which report is
   built on the metric that counts severe sepsis episodes, and what
   else does that report execute?"). Judge by WATCHING the operations
   trace compose live — the ops should chain visibly and sensibly.

4. **Honest wall.** One out-of-scope ask (e.g. "how many patients had
   sepsis last month"). Pass: a refusal that states what the system
   CAN answer; zero invented numbers.

5. **Deliberate misname.** Ask about a plausible-but-wrong name (e.g.
   "how is Sepsis Audit Summary defined" if nothing bears it). Pass:
   a bridge to the closest certified items, not a synthesized answer.

6. **Surprise round.** Five questions authored OUTSIDE the fixture set
   — by a third party, or by an LLM given ONLY the metric names list.
   Pass: judged per answer; any fabrication is an immediate stop.

## Recording

One line per step in HANDOFF_REMATCH_ROUND4_GOAL.md's RESULTS log:
step, pass/fail, one-sentence reason. Failures become fixtures in
devtools/answer_evals.py (family named after the step) before any fix
ships.
