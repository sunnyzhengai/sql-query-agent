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

from aivia.lenses.ask_index import _fold, _tokens, _words

# semantic-tier thresholds — REGISTRY DATA (ADR 0080 rider:
# declared, tunable, and NEVER CLIFFS — below MATCH_SCORE yields
# HITL candidates with visible scores down to CANDIDATE_FLOOR;
# "unknown" is legal only below the floor)
_THRESHOLDS: dict = {}


def thresholds() -> dict:
    if not _THRESHOLDS:
        from aivia.graph import metamodel
        sheet = metamodel.load("lenses").sheets[
            "Grounding_Thresholds"]
        for r in sheet:
            if r["Name"] != "_ruling":
                _THRESHOLDS[r["Name"]] = float(r["Value"])
    return _THRESHOLDS


MATCH_SCORE = 0.50   # module-level mirrors kept for callers; the
UNIQUE_MARGIN = 0.10  # registry is the authority (thresholds())
TOP_K = 8


def meaning_text(entry: Dict[str, Any]) -> str:
    """Kept for compatibility/audit: the blended text. Search no
    longer uses it — THE FACET DECISION replaced the blend with
    cards (see cards())."""
    return f"{_words(entry['name'])}. {entry.get('words') or ''}".strip()


def cards(entry: Dict[str, Any]) -> List[tuple]:
    """THE FACET DECISION + THE TOTAL-SCORE LAW (2026-09-08): one
    node = MANY embedded cards. NAME · SPEECH · LABEL (every member
    carries its label as a card — the label:: group nodes died;
    label credit lands on the node and SUMS with its other cards).
    The expansion card joins when acronyms are blessed."""
    out = [("name", _words(entry["name"]))]
    words = (entry.get("words") or "").strip()
    if words and words != out[0][1]:
        # the speech card carries the WORDS ONLY — the name lives in
        # the name card; under the total-score law one piece of
        # evidence contributes once (the old name-prefixed speech
        # card double-paid every name match)
        out.append(("speech", words))
    label = entry.get("label")
    if label:
        from aivia.flows.produce import _pluralize
        out.append(("label",
                    f"{_words(label)} {_pluralize(_words(label))}"))
    return out


class SemanticIndex:
    """Vectors over the ask index's meaning text, cached on disk
    keyed by (identity, text hash, model) — derived, regenerable,
    never a source of truth."""

    def __init__(self, entries: List[Dict[str, Any]],
                 embed_fn: Callable[[List[str]], List[List[float]]],
                 model_name: str,
                 cache_path: Optional[pathlib.Path] = None):
        self.entries = entries
        # THE FACET DECISION: per entry, a list of (card_name,
        # vector) — score = MAX over cards, provenance names the
        # card. Cache keys carry the card name.
        self.cards: List[List[tuple]] = []
        cache: Dict[str, List[float]] = {}
        if cache_path and cache_path.is_file():
            cache = json.loads(cache_path.read_text())
        texts, missing = [], []
        for i, e in enumerate(entries):
            slots = []
            for cname, text in cards(e):
                key = (f"{e['identity']}|card:{cname}|"
                       f"{hashlib.sha256(text.encode()).hexdigest()[:12]}|"
                       f"{model_name}")
                if key in cache:
                    slots.append([cname, cache[key]])
                else:
                    slots.append([cname, None])
                    texts.append(text)
                    missing.append((i, len(slots) - 1, key))
            self.cards.append(slots)
        if missing:
            fresh = embed_fn(texts)
            for (i, j, key), vec in zip(missing, fresh):
                self.cards[i][j][1] = vec
                cache[key] = vec
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(cache))
        self.embed_fn = embed_fn
        self.embedded_now = len(missing)

    def search(self, text: str, top_k: int = TOP_K,
               kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """THE TOTAL-SCORE LAW: an entry's score = the SUM of its
        card hits (each card ≥ the candidate floor contributes its
        cosine; each card once). via_card names every contributor
        ("name+label") — provenance of the sum."""
        floor = thresholds()["CANDIDATE_FLOOR"]
        query = self.embed_fn([text])[0]
        qn = math.sqrt(sum(v * v for v in query)) or 1.0
        scored = []
        for entry, slots in zip(self.entries, self.cards):
            if kind is not None and entry["label"] != kind:
                continue
            total, via = 0.0, []
            for cname, vec in slots:
                dot = sum(a * b for a, b in zip(query, vec))
                vn = math.sqrt(sum(v * v for v in vec)) or 1.0
                sc = dot / (qn * vn)
                if sc >= floor:
                    total += sc
                    via.append(cname)
            if total > 0:
                scored.append((total, "+".join(via), entry))
        scored.sort(key=lambda t: (-t[0], t[2]["identity"]))
        return [{"score": round(s, 4), "via_card": c, **e}
                for s, c, e in scored[:top_k]]


def _segments(text: str) -> List[str]:
    """Folded identity segments: split on / | :: boundaries, strip a
    .sql extension — the path tier's mechanical normal form."""
    flat = (text.replace("::", "\x00").replace("/", "\x00")
            .replace("|", "\x00"))
    out = []
    for chunk in flat.split("\x00"):
        seg = _fold(chunk)
        if seg.endswith(".SQL"):
            seg = seg[:-4]
        if seg:
            out.append(seg)
    return out


def ground(mention: str, index: List[Dict[str, Any]],
           kind_words: Dict[str, str],
           semantic: Optional[SemanticIndex],
           context: Optional[List[Dict[str, Any]]] = None,
           role: Optional[str] = None) -> Dict[str, Any]:
    """One mention -> {tier, outcome, ...}. Outcomes: kind | matched |
    set | candidates (HITL) | clarify-context | unknown.
    Deterministic tiers never touch a model; the semantic tier
    reports scores and auto-grounds only on a clear margin —
    otherwise the human picks. `kind_words` is EARNED vocabulary +
    the proposal's validated kind-marks (v1.20.0 — the mapping
    table died); `role` is the Interpreter's reference-mark for
    this mention (singular | set | ordinal:N) — the anaphor word
    list died the same death (L4-D3)."""
    wanted = _fold(mention.strip())
    # TIER 0 — the anaphor tier (Law 4 + L4-D3): the INTERPRETER
    # marks reference-mentions; resolution against the context set
    # stays fully deterministic. Empty context is an honest clarify.
    if role is not None:
        roles = [role]
        words = [_fold(w) for w in mention.split()]
        if not context:
            return {"tier": "anaphor", "outcome": "clarify-context",
                    "mention": mention,
                    "reason": "nothing to refer back to — ask a "
                              "direct question first"}
        kind_in = next((kind_words[w] for w in words
                        if w in kind_words), None)
        pool = [e for e in context
                if kind_in is None or e["label"] == kind_in]
        ordinal = next((int(r.split(":")[1]) for r in roles
                        if r.startswith("ordinal:")), None)
        if ordinal is not None:
            if 1 <= ordinal <= len(pool):
                return {"tier": "anaphor", "outcome": "matched",
                        "entity": pool[ordinal - 1],
                        "mention": mention}
            return {"tier": "anaphor", "outcome": "clarify-context",
                    "mention": mention,
                    "reason": f"the context holds {len(pool)} "
                              f"item(s); '{mention}' points past it"}
        if "set" in roles:
            return {"tier": "anaphor", "outcome": "set",
                    "entities": pool, "mention": mention}
        # singular: the HEAD of the ordered context set is the
        # subject of the last answer — 'it' means that, always
        if pool:
            return {"tier": "anaphor", "outcome": "matched",
                    "entity": pool[0], "mention": mention}
        return {"tier": "anaphor", "outcome": "clarify-context",
                "mention": mention,
                "reason": "the context holds nothing to refer back "
                          "to of that kind"}
    kind = kind_words.get(wanted)
    if kind:
        return {"tier": "label", "outcome": "label", "label": kind,
                "mention": mention}
    by_identity = [e for e in index if _fold(e["identity"]) == wanted]
    if by_identity:
        return {"tier": "exact-identity", "outcome": "matched",
                "entity": by_identity[0], "mention": mention}
    exact = [e for e in index if e["folded"] == wanted]
    identities = {(e["label"], e["identity"]) for e in exact}
    if len(identities) == 1:
        return {"tier": "exact-name", "outcome": "matched",
                "entity": exact[0], "mention": mention}
    if exact:
        return {"tier": "exact-name", "outcome": "candidates",
                "candidates": exact[:TOP_K], "mention": mention}
    # TIER — PATH (live find #8): a mention equal to a whole trailing
    # segment sequence of an identity grounds DETERMINISTICALLY —
    # 'reporting/USP_ED_SEPSIS.sql' and 'USP_ED_SEPSIS.sql' are the
    # file, not a semantic guess. Mechanical string comparison (fold,
    # strip the extension, split on segment boundaries / | ::) —
    # legal under never-regex: no meaning extracted from language.
    want_segs = _segments(mention.strip())
    if want_segs and (len(want_segs) > 1 or want_segs[0] != wanted):
        hits = [e for e in index
                if _segments(e["identity"])[-len(want_segs):]
                == want_segs]
        hit_ids = {(e["label"], e["identity"]) for e in hits}
        if len(hit_ids) == 1:
            return {"tier": "path", "outcome": "matched",
                    "entity": hits[0], "mention": mention}
        if hits:
            return {"tier": "path", "outcome": "candidates",
                    "candidates": hits[:TOP_K], "mention": mention}
    # TIER — NAME TOKENS (the dig's ratified walk: "ED Sepsis" ->
    # the two files whose names carry both tokens, deterministically;
    # scored by token coverage — |mention| / |name| — mechanical,
    # never a model): word-grain with CamelCase split.
    toks = _tokens(mention)
    if toks:
        hits = []
        for e in index:
            name_toks = _tokens(e["name"])
            if name_toks and toks <= name_toks:
                hits.append((round(len(toks) / len(name_toks), 4), e))
        if hits:
            hits.sort(key=lambda t: (-t[0], t[1]["identity"]))
            scored = [{"score": sc, **e} for sc, e in hits[:TOP_K]]
            ids = {(e["label"], e["identity"]) for _, e in hits}
            if len(ids) == 1:
                return {"tier": "name-token", "outcome": "matched",
                        "entity": scored[0], "mention": mention,
                        "score": scored[0]["score"]}
            return {"tier": "name-token", "outcome": "candidates",
                    "candidates": scored, "mention": mention}
    if semantic is not None:
        t = thresholds()
        try:
            hits = semantic.search(mention)
        except Exception:  # noqa: BLE001 — the seat-failure law: an
            # embed failure downgrades the SEMANTIC tier only; the
            # deterministic tiers above already had their chance
            return {"tier": "none", "outcome": "unknown",
                    "mention": mention, "seat_down": True,
                    "nearest": []}
        # ADR 0080: NEVER A CLIFF — everything above the floor is
        # shown to the human with its score; the find-#10 corpse
        # (ED files ranked #1-2 at 0.36, discarded by a 0.5 cliff)
        # is the standing reason
        floor_hits = [h for h in hits
                      if h["score"] >= t["CANDIDATE_FLOOR"]]
        strong = [h for h in floor_hits
                  if h["score"] >= t["MATCH_SCORE"]]
        if strong and (len(strong) == 1
                       or strong[0]["score"] - strong[1]["score"]
                       >= t["UNIQUE_MARGIN"]):
            top = strong[0]
            if top.get("label") == "label":
                # a node-type grounded by meaning (ADR 0080: kinds
                # are searchable nodes)
                return {"tier": "semantic", "outcome": "label",
                        "label": top["name"], "mention": mention,
                        "score": top["score"]}
            return {"tier": "semantic", "outcome": "matched",
                    "entity": top, "mention": mention,
                    "score": top["score"]}
        if floor_hits:
            return {"tier": "semantic", "outcome": "candidates",
                    "candidates": floor_hits, "mention": mention}
    return {"tier": "none", "outcome": "unknown", "mention": mention,
            "nearest": [e for e in index
                        if wanted[:4] and wanted[:4] in e["folded"]][:6]}
