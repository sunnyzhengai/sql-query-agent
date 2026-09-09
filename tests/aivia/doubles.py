"""Test doubles under the LIVE-SEAT RULE (ruled 2026-09-09).

scripted_proposals — authored test input for the Interpreter seat:
the test DECLARES the proposal it is handing the pipeline ("given
this reading, the law must hold"), the way authored SQL fixtures
declare parser input. Strict by law: keys fold at construction
(the lowercase-lookup trap class died here) and an unscripted
question raises ScriptGap instead of improvising a default.

The embedder double lives here too, en route to recorded-real
vectors (the fake-physics embedder is sentenced; see the manifest).
"""
import hashlib
import re


class ScriptGap(AssertionError):
    """A test asked a question its script never authored."""


def _fold_key(text: str) -> str:
    return " ".join(text.split()).lower()


def scripted_proposals(mapping):
    script = {_fold_key(k): v for k, v in mapping.items()}

    def interpret(question):
        key = _fold_key(question)
        if key not in script:
            raise ScriptGap(
                f"unscripted question: {question!r} — the script "
                f"holds only {sorted(script)}; author the proposal "
                f"this test means to hand the pipeline")
        return script[key]

    return interpret


def fake_embed(texts):
    """Deterministic bag-of-words hashing — SENTENCED (never-fake
    lean, 2026-09-09): dies when the recorded-real fixture lands.
    2048 buckets x three positions per word."""
    out = []
    for text in texts:
        vec = [0.0] * 2048
        for word in re.sub(r"[^a-z0-9 ]", " ", text.lower()).split():
            h = hashlib.sha256(word.encode()).hexdigest()
            vec[int(h[:12], 16) % 2048] += 1.0
            vec[int(h[12:24], 16) % 2048] += 1.0
            vec[int(h[24:36], 16) % 2048] += 1.0
        out.append(vec)
    return out
