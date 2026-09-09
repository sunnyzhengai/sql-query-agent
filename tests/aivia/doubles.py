"""Test doubles under the LIVE-SEAT RULE (ruled 2026-09-09).

scripted_proposals — authored test input for the Interpreter seat:
the test DECLARES the proposal it is handing the pipeline ("given
this reading, the law must hold"), the way authored SQL fixtures
declare parser input. Strict by law: keys fold at construction
(the lowercase-lookup trap class died here) and an unscripted
question raises ScriptGap instead of improvising a default.

recorded_embed — REAL prod physics, replayed. Every vector is a
genuine text-embedding-3-small embedding, recorded once against
the live model (AIVIA_RECORD=1) into a committed fixture and
replayed byte-identically ever after. Nothing is faked: the model
computed every number; the fixture only removes the network. A
text with no recording raises RecordingGap naming the remedy —
never a silent fabrication (the hash-bucket fake embedder died
under the never-fake ruling).
"""
import base64
import gzip
import hashlib
import json
import os
import pathlib
import struct

EMBED_MODEL = "text-embedding-3-small"
FIXTURE = (pathlib.Path(__file__).resolve().parents[2]
           / "AIVIA_Product" / "fixtures" / "embeddings"
           / f"{EMBED_MODEL}.json.gz")


class ScriptGap(AssertionError):
    """A test asked a question its script never authored."""


class RecordingGap(AssertionError):
    """A test embedded a text the fixture never recorded."""


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


# ---- recorded-real embeddings ----------------------------------------
_STORE = None


def _text_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def _encode(vec):
    return base64.b64encode(
        struct.pack(f"<{len(vec)}e", *vec)).decode()


def _decode(blob: str):
    raw = base64.b64decode(blob)
    return list(struct.unpack(f"<{len(raw) // 2}e", raw))


def recorded_store() -> dict:
    global _STORE
    if _STORE is None:
        if FIXTURE.is_file():
            _STORE = json.loads(gzip.decompress(FIXTURE.read_bytes()))
        else:
            _STORE = {"model": EMBED_MODEL, "texts": {},
                      "vectors": {}}
    return _STORE


def recorded_embed(texts):
    store = recorded_store()
    missing = [t for t in texts
               if _text_key(t) not in store["vectors"]]
    if missing:
        if not os.environ.get("AIVIA_RECORD"):
            raise RecordingGap(
                f"{len(missing)} text(s) hold no recorded vector — "
                f"first: {missing[0]!r}. Run AIVIA_RECORD=1 pytest "
                f"to record against the real {EMBED_MODEL}, then "
                f"commit {FIXTURE.name}")
        from aivia.console import _env_key, make_embedder
        fresh = make_embedder(_env_key())(missing)
        for text, vec in zip(missing, fresh):
            key = _text_key(text)
            store["texts"][key] = text
            store["vectors"][key] = _encode(vec)
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_bytes(gzip.compress(
            json.dumps(store, sort_keys=True).encode()))
    return [_decode(store["vectors"][_text_key(t)]) for t in texts]
