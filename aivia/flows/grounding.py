"""GROUND (ADR 0079 step 2): a mention becomes graph nodes through
tiers — kind word (registry vocabulary) -> exact identity -> exact
folded name -> SEMANTIC (vector over meaning text) -> HITL. The
deterministic tiers run first and are model-free; the semantic tier
needs an embedder, which is INJECTED (matching is model-shaped and
belongs behind honesty machinery — never a lens). Every stored
vector is stamped (identity, text hash, model): a meaning that did
not change never re-embeds (the change quanta, extended).
"""
import hashlib
import json
import math
import pathlib
from typing import Any, Callable, Dict, List, Optional

from aivia.lenses.ask_index import _fold, _words

# semantic-tier thresholds — DECLARED here, tuned by evidence
MATCH_SCORE = 0.50      # best hit at/above -> candidates worth showing
UNIQUE_MARGIN = 0.10    # best beats runner-up by this -> auto-ground
TOP_K = 8


def meaning_text(entry: Dict[str, Any]) -> str:
    """What gets embedded: the entry's name in readable form plus its
    steward words — meaning, never raw identifiers alone."""
    return f"{_words(entry['name'])}. {entry.get('words') or ''}".strip()


class SemanticIndex:
    """Vectors over the ask index's meaning text, cached on disk
    keyed by (identity, text hash, model) — derived, regenerable,
    never a source of truth."""

    def __init__(self, entries: List[Dict[str, Any]],
                 embed_fn: Callable[[List[str]], List[List[float]]],
                 model_name: str,
                 cache_path: Optional[pathlib.Path] = None):
        self.entries = entries
        self.vectors: List[Optional[List[float]]] = []
        cache: Dict[str, List[float]] = {}
        if cache_path and cache_path.is_file():
            cache = json.loads(cache_path.read_text())
        texts, missing = [], []
        keys = []
        for i, e in enumerate(entries):
            text = meaning_text(e)
            key = (f"{e['identity']}|"
                   f"{hashlib.sha256(text.encode()).hexdigest()[:12]}|"
                   f"{model_name}")
            keys.append(key)
            if key in cache:
                self.vectors.append(cache[key])
            else:
                self.vectors.append(None)
                texts.append(text)
                missing.append(i)
        if missing:
            fresh = embed_fn(texts)
            for i, vec in zip(missing, fresh):
                self.vectors[i] = vec
                cache[keys[i]] = vec
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(cache))
        self.embed_fn = embed_fn
        self.embedded_now = len(missing)

    def search(self, text: str, top_k: int = TOP_K,
               kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scores over ALL entries (optionally restricted to one
        kind BEFORE ranking — live find #5: pooling before the kind
        filter let columns crowd files out of a truncated pool, a
        silent cap distorting the set)."""
        query = self.embed_fn([text])[0]
        qn = math.sqrt(sum(v * v for v in query)) or 1.0
        scored = []
        for entry, vec in zip(self.entries, self.vectors):
            if kind is not None and entry["kind"] != kind:
                continue
            dot = sum(a * b for a, b in zip(query, vec))
            vn = math.sqrt(sum(v * v for v in vec)) or 1.0
            scored.append((dot / (qn * vn), entry))
        scored.sort(key=lambda t: (-t[0], t[1]["identity"]))
        return [{"score": round(s, 4), **e} for s, e in scored[:top_k]]


def ground(mention: str, index: List[Dict[str, Any]],
           kind_words: Dict[str, str],
           semantic: Optional[SemanticIndex]) -> Dict[str, Any]:
    """One mention -> {tier, outcome, ...}. Outcomes: kind | matched |
    candidates (HITL) | unknown. Deterministic tiers never touch a
    model; the semantic tier reports scores and auto-grounds only on
    a clear margin — otherwise the human picks."""
    wanted = _fold(mention.strip())
    kind = kind_words.get(wanted)
    if kind:
        return {"tier": "kind", "outcome": "kind", "kind": kind,
                "mention": mention}
    by_identity = [e for e in index if _fold(e["identity"]) == wanted]
    if by_identity:
        return {"tier": "exact-identity", "outcome": "matched",
                "entity": by_identity[0], "mention": mention}
    exact = [e for e in index if e["folded"] == wanted]
    identities = {(e["kind"], e["identity"]) for e in exact}
    if len(identities) == 1:
        return {"tier": "exact-name", "outcome": "matched",
                "entity": exact[0], "mention": mention}
    if exact:
        return {"tier": "exact-name", "outcome": "candidates",
                "candidates": exact[:TOP_K], "mention": mention}
    if semantic is not None:
        try:
            hits = semantic.search(mention)
        except Exception:  # noqa: BLE001 — the seat-failure law: an
            # embed failure downgrades the SEMANTIC tier only; the
            # deterministic tiers above already had their chance
            return {"tier": "none", "outcome": "unknown",
                    "mention": mention, "seat_down": True,
                    "nearest": []}
        strong = [h for h in hits if h["score"] >= MATCH_SCORE]
        if strong and (len(strong) == 1
                       or strong[0]["score"] - strong[1]["score"]
                       >= UNIQUE_MARGIN):
            return {"tier": "semantic", "outcome": "matched",
                    "entity": strong[0], "mention": mention,
                    "score": strong[0]["score"]}
        if strong:
            return {"tier": "semantic", "outcome": "candidates",
                    "candidates": strong, "mention": mention}
    return {"tier": "none", "outcome": "unknown", "mention": mention,
            "nearest": [e for e in index
                        if wanted[:4] and wanted[:4] in e["folded"]][:6]}
