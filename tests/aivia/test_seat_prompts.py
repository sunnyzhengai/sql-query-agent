"""STEP C of the search rebuild — THE PROMPT IS REGISTRY DATA.
Suite first (step discipline).

Gaps 2+3: the Interpreter's prompt still carries the dead kind
menu with synonym lists (vocabulary in prose — the literal law's
blind spot) and drops mentions; and the proposal cache key ignores
the prompt version, so a prompt fix would silently not apply to
already-asked questions.

Pins:
1. The prompt loads from the registry (Seat_Prompts sheet) with a
   VERSION — a prompt edit is a registry bump Sunny reviews.
2. The prompt contains NO kind vocabulary (no type menu, no
   synonym hints) and no 'kinds' field invitation.
3. The prompt REQUIRES every referring word as a mention (the
   'reports'-dropping hardening — asserted on the instruction
   text).
4. The cache key includes the prompt version: same question, new
   prompt version -> the cached old proposal is NOT replayed.

Proves: contract:aivia-design-to-code
"""
import json

from aivia import console


def test_prompt_is_registry_data_with_a_version():
    text, version = console.interpreter_prompt()
    assert text and len(text) > 100
    assert version  # e.g. "3.0.0"
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Seat_Prompts"]
    row = next(r for r in sheet if r["Seat"] == "interpreter")
    assert row["Prompt"] == text
    assert row["Version"] == version


def test_prompt_carries_no_kind_vocabulary():
    text, _ = console.interpreter_prompt()
    low = text.lower()
    assert '"kinds"' not in low
    # the dead menu's synonym hints are gone
    for leak in ("reports/procs", "filters/rules",
                 "(tables, columns", "kind word"):
        assert leak not in low
    # the shapes that DO belong
    assert "mentions" in low and "expansions" in low \
        and "references" in low


def test_prompt_requires_every_referring_word():
    text, _ = console.interpreter_prompt()
    low = text.lower()
    assert "every" in low and "mention" in low
    assert "never drop" in low or "never omit" in low


def test_cache_key_includes_the_prompt_version(tmp_path, monkeypatch):
    calls = []

    def fake_openai(path, payload, key):
        calls.append(payload)
        return {"choices": [{"message": {"content":
                json.dumps({"mentions": ["fresh"]})}}]}
    monkeypatch.setattr(console, "_openai", fake_openai)
    cache_file = tmp_path / "proposals.json"
    _text, version = console.interpreter_prompt()
    # seed a STALE cache entry keyed under an old prompt version
    stale_key = f"what reports are about ed|{console.INTERPRETER_MODEL}|v0-stale"
    cache_file.write_text(json.dumps(
        {stale_key: {"mentions": ["Ed"], "kinds": {"Ed": "term"}}}))
    interpret = console.make_interpreter("k", cache_path=cache_file)
    out = interpret("what reports are about ED")
    # the stale entry was NOT replayed — the model was called fresh
    assert out == {"mentions": ["fresh"]}
    assert len(calls) == 1
    # and the fresh result landed under the CURRENT versioned key
    cache = json.loads(cache_file.read_text())
    good_key = (f"what reports are about ed|"
                f"{console.INTERPRETER_MODEL}|{version}")
    assert good_key in cache
