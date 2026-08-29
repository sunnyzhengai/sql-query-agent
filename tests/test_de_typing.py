"""TESTPLAN_0062 section A — the de-typing proof (the ruling's
teeth, 2026-08-29: remove the type first; no silent fallback
anywhere; no recognition step exists).

Proves: law:walk-finds
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_a1_no_shape_recognition_in_the_routing_layer():
    """A1: the whole-question template is DELETED — the routing
    layer (webapp) holds zero references to any question class;
    'same_or_different' survives ONLY as a word-grain lexicon entry
    inside parse_plan."""
    app_src = (REPO / "src" / "webapp" / "app.py").read_text()
    assert "same_or_different" not in app_src
    assert 'primitives != [' not in app_src
    assert 'primitives == [' not in app_src


def test_a1_engine_has_no_silent_planner_bypass():
    """The interception never returns None once the planner is on —
    every state is a card (grep the mechanism, not the vibes)."""
    app_src = (REPO / "src" / "webapp" / "app.py").read_text()
    start = app_src.index("def _planner_intercept")
    end = app_src.index("@app.post(\"/api/ask\")")
    body = app_src[start:end]
    assert "return None" not in body, (
        "_planner_intercept can silently fall through — the ruling "
        "bans every silent route; every state must be a card")


def test_a3_behavior_varies_only_with_grounding():
    """A3 (Sunny's acceptance sentence): two same-shape questions
    with different entities → different groundings, same mechanics.
    The plans differ only in the ids the words grounded to."""
    from src.orchestrator.parse_plan import Parse, compose_plan

    def anchors(*ids):
        return [{"entity": i, "id": i, "kind": "metric", "rows": [{}]}
                for i in ids]

    plan_x = compose_plan(Parse(["A", "B"], ["same_or_different"]),
                          anchors("A", "B"))
    plan_y = compose_plan(Parse(["C", "D"], ["same_or_different"]),
                          anchors("C", "D"))
    strip = lambda p: json.dumps(  # noqa: E731
        [{k: ("<ids>" if k in ("ids", "refs") else v)
          for k, v in s.items()} for s in p])
    assert strip(plan_x) == strip(plan_y)      # identical mechanics
    assert plan_x != plan_y                    # different groundings


def test_c4_the_door_is_on_every_card_by_construction():
    """C4 structural half: ONE card renderer exists and it always
    includes the developer door — no_match only removes the run
    button. (The event-capture half lives in the webapp tests.)"""
    app_src = (REPO / "src" / "webapp" / "app.py").read_text()
    assert app_src.count("function renderParseCard") == 1
    card_fn = app_src[app_src.index("function renderParseCard"):]
    card_fn = card_fn[:card_fn.index("\nasync function")]
    assert "doorbtn" in card_fn
    assert "contact a developer" in card_fn
