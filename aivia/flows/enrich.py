"""PHASE I — the
enrichment pipeline: SCAN (mechanical: the estate's distinct name
tokens) -> SCRIBE (the curation seat proposes expansions — a model,
injected; proposals only) -> BLESS (a human approves; acronym nodes
are born). The live run is gated on Sunny's blessing; everything
here is deterministic machinery around the injected seat.
"""
import json
import re
from typing import Callable, Dict, List

from aivia.graph import kg3_artifacts
from aivia.lenses.ask_index import _tokens


def scan_name_tokens(read) -> List[str]:
    """Every distinct token the estate's names are made of — no
    judgment, no acronym-detection heuristics."""
    toks = set()
    for n in read.nodes(None):
        nm = n.properties.get("name") or n.identity.rsplit("|", 1)[-1]
        toks |= _tokens(str(nm))
    return sorted(toks)


def propose(tokens: List[str],
            scribe: Callable[[List[str]], Dict[str, List[str]]]
            ) -> Dict[str, List[str]]:
    """The Scribe reads the token list and proposes expansions for
    the shorthand it recognizes. PROPOSALS ONLY — nothing lands
    until a human blesses."""
    raw = scribe(tokens) or {}
    return {t.lower(): [e.strip() for e in exps if (e or "").strip()]
            for t, exps in raw.items()
            if t.lower() in {x.lower() for x in tokens}
            and exps}


def bless(store, proposals: Dict[str, List[str]],
          approved_by: str, approved_at: str) -> int:
    """The human act: approved proposals become acronym nodes."""
    n = 0
    for name, exps in sorted(proposals.items()):
        kg3_artifacts.append_acronym(store, name, exps,
                                     approved_by=approved_by,
                                     approved_at=approved_at)
        n += 1
    return n


# ---- THE NAMER SEAT (Grammar_Floor §R5.b, riders c/d ruled
# 2026-09-12): the same shape as the Scribe — deterministic
# machinery around an INJECTED model; proposals only; the gate
# and the field law stand between every candidate and a voice.

def name_worklist(read, scope: str = "voiced") -> List[str]:
    """R5.b's worklist, two scopes (rider (d) extended at Sunny's
    "why are we not running for the dictionary", 2026-09-13 — a
    blessed name is per-column truth, not per-file):
    'voiced' = what actually speaks today — resolves_to target
    COLUMNS (4-part; params are their own nodes, out) then read
    TABLES (3-part); 'dictionary' = ALL of KG1, the backfill
    sweep. Columns first in both: they speak most."""
    if scope == "dictionary":
        return (sorted(n.identity for n in read.nodes("column"))
                + sorted(n.identity for n in read.nodes("table")))
    if scope != "voiced":
        raise ValueError(f"unknown worklist scope '{scope}' — "
                         "voiced or dictionary")
    cols, tbls = set(), set()
    for e in read.edges("resolves_to"):
        if e.to_id.count("|") == 3:
            cols.add(e.to_id)
    for e in read.edges("reads"):
        if e.to_id.count("|") == 2:
            tbls.add(e.to_id)
    return sorted(cols) + sorted(tbls)


def _has_source_words(description: str, name: str) -> bool:
    """Nothing-to-select (R5.b): no letter-run of length >= 2
    anywhere in description ∪ name = no legal word to pick — the
    target is never proposed, only counted. The model never
    guesses past missing vendor truth."""
    return bool(re.search(r"[a-zA-Z]{2,}", f"{description} {name}"))


def propose_blessed_names(read, glossary_dir, namer, model: str,
                          prompt_version: str, run_at: str,
                          cache_path=None,
                          scope: str = "voiced") -> Dict[str, int]:
    """One batch of the namer seat, at Sunny's hand only (rider d):
    per target, TWO independent runs (the double-run law) — agree
    -> gate -> a `proposed` row; differ -> `disputed`, both
    candidates recorded; gate kill -> `rejected` with named
    violations. Machine rows only — `blessed` is a ruled status
    this function may never write NOR overwrite (the field law,
    stale or not). The candidate cache keys on target ·
    description_hash · model · prompt_version: a re-run spends
    nothing. Candidates are normalized mechanically (whitespace
    collapse + lowercase — no word changes) before the gate."""
    from aivia.flows import gates, glossary
    registry = glossary.load_blessed_subjects(glossary_dir)
    cache: Dict[str, List[str]] = {}
    if cache_path is not None and cache_path.is_file():
        cache = json.loads(cache_path.read_text())
    nodes = {n.identity: n for n in read.nodes("column")}
    nodes.update({n.identity: n for n in read.nodes("table")})
    # literal: shape — the batch report, counted never silent
    counts = {"proposed": 0, "disputed": 0, "rejected": 0,
              "kept": 0, "blessed_kept": 0, "nothing_to_select": 0,
              "missing_target": 0, "model_calls": 0,
              "cache_hits": 0, "seat_error": 0}

    def _save_cache():
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache))

    for target in name_worklist(read, scope):
        node = nodes.get(target)
        if node is None:
            counts["missing_target"] += 1
            continue
        prior = registry.get(target)
        if prior and prior.get("status") == "blessed":
            counts["blessed_kept"] += 1  # ruled field, untouchable
            continue
        desc = node.properties.get("description", "")
        name = target.rsplit("|", 1)[-1]
        if not _has_source_words(desc, name):
            counts["nothing_to_select"] += 1
            continue
        dhash = glossary.description_hash(desc)
        if prior and prior.get("description_hash") == dhash \
                and prior.get("proposer", {}).get("model") == model \
                and prior.get("proposer", {}).get(
                    "prompt_version") == prompt_version:
            counts["kept"] += 1  # same input, same verdict stands
            continue
        ck = f"{target}|{dhash}|{model}|{prompt_version}"
        if ck in cache:
            runs = cache[ck]
            counts["cache_hits"] += 1
        else:
            try:
                runs = [" ".join(str(namer(name, desc)).split())
                        .lower()
                        for _ in range(2)]  # the double-run law
            except Exception:  # noqa: BLE001 — the seat-down law:
                # one dead call must never kill the batch (the
                # 2026-09-13 timeout took a whole run + its spends)
                counts["seat_error"] += 1
                continue
            counts["model_calls"] += 2
            cache[ck] = runs
            _save_cache()  # every successful pair survives a crash
        # literal: shape — the machine row; a human flips 'blessed'
        row = {"status": "", "description_hash": dhash,
               "proposed_at": run_at,
               # literal: shape
               "proposer": {"model": model,
                            "prompt_version": prompt_version,
                            "runs": 2}}
        if runs[0] != runs[1]:
            row["status"] = "disputed"
            row["candidates"] = runs
            counts["disputed"] += 1
        else:
            violations = gates.check_blessed_words(runs[0], desc,
                                                   name)
            if violations:
                row["status"] = "rejected"
                row["words"] = runs[0]
                row["violations"] = violations
                counts["rejected"] += 1
            else:
                row["status"] = "proposed"
                row["words"] = runs[0]
                counts["proposed"] += 1
        registry[target] = row
    glossary.save_blessed_subjects(glossary_dir, registry)
    _save_cache()
    return counts
