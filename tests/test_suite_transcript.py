"""Suite transcript emission (morning order 2, 2026-08-27): every
answer_evals run writes a READABLE per-family transcript — question,
final answer text, machine verdict, grade, floor/gate notes — so
Sunny reviews engine behavior without the web UI. Pure emission over
the run dump; no new machinery.

Proves: contract:suite-legibility
"""

from devtools.answer_evals import render_transcript


def _rec(family, q, caption, dishonest=False, dumb=False, hits=2,
         within=True, answered=True, answer_ok=True):
    return {"family": family, "question": q,
            "grade": {"dishonest": dishonest, "dumb": dumb,
                      "fact_hits": hits, "within_rounds": within,
                      "declared_answered": answered,
                      "answer_ok": answer_ok, "facts_present": bool(hits),
                      "question": q},
            "caption": {"caption": caption},
            "loop": {"rounds": 2, "status": "",
                     "status_line": "answered in 2 rounds"},
            "outputs": []}


DUMP = [
    _rec("flags", "what red flags exist?",
         "83 flags across 5 classes — the count is exact."),
    _rec("flags", "any governance flags?",
         "Yes — 83, enumerated below.", hits=3),
    _rec("sameness", "are A and B the same?",
         "They are identical.", dishonest=True, answer_ok=False),
    {"family": "drilldown", "question": "what feeds X?",
     "infra_skip": "ConnectionError"},
]


def test_groups_by_family_with_question_and_caption():
    t = render_transcript(DUMP, run_stamp="2026-08-27T09:00")
    assert t.index("## flags") < t.index("## sameness")
    assert "what red flags exist?" in t
    assert "83 flags across 5 classes" in t


def test_machine_verdict_flags_the_dishonest_turn():
    t = render_transcript(DUMP, run_stamp="s")
    assert "DISHONEST" in t
    sect = t[t.index("## sameness"):t.index("## Board")]
    assert "**DISHONEST**" in sect
    flags = t[t.index("## flags"):t.index("## sameness")]
    assert "DISHONEST" not in flags


def test_grade_line_carries_facts_and_rounds():
    t = render_transcript(DUMP, run_stamp="s")
    assert "facts 2" in t and "rounds" in t


def test_infra_skip_is_disclosed_never_silent():
    t = render_transcript(DUMP, run_stamp="s")
    assert "INFRA-SKIP" in t and "ConnectionError" in t


def test_board_and_floor_notes_present():
    t = render_transcript(DUMP, run_stamp="s")
    assert "honesty=0.00" in t          # sameness family, the corpse
    assert "honesty=1.00" in t          # flags family
    assert "build-stopper" in t         # the floor note, named


def test_run_stamp_is_the_callers():
    assert "2026-08-27T09:00" in render_transcript(
        DUMP, run_stamp="2026-08-27T09:00")


def test_empty_dump_renders_honestly():
    t = render_transcript([], run_stamp="s")
    assert "no graded questions" in t.lower()
