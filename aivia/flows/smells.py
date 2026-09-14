"""THE MEANING-SMELL CENSUS + THE PHRASE-CORPUS SWEEP (Sunny's go,
2026-09-14 "go on both"; direction ruled in the 09-12 GENERATOR NOTE).

The generator-level answer to per-round phrasing fixes: every stored
voicing renders into ONE corpus, deduplicated by shape class, swept in
one sitting — and a closed set of mechanical smell detectors runs as
a standing census (clean ⊎ smelled == total, the ADR 0080 equation
shape), so a new phrasing class announces itself before a live round
stumbles over it.

A smell is a FLAG for the sweep, never a verdict: a lawful render can
smell (the Grammar 2.8.0 name-words join render "The ed disposition
code is the ed disposition." is ruled AND echo-smelled). No detector
consults a model; no threshold, no cliff. The founding corpses:
the join tautology ("The encounter is the encounter."), the sentinel
placeholder (38 rows, origin killed 2026-09-14), the source-phrase
stutter ("med admin records records"), raw fragments in prose.
"""
import re
from collections import Counter
from typing import Any, Dict, List

# The floor's own phrase skeleton — the closed masking vocabulary.
# A template keeps these words and masks everything else; two
# voicings with the same template are the same phrasing class.
# literal: mechanical — masking skeleton, Ruling_Center_and_Censuses Piece 6
STRUCTURE_WORDS = frozenset((
    "the", "a", "an", "of", "on", "per", "for", "in", "at", "by",
    "with", "to", "and", "or", "not", "is", "are", "was", "were",
    "has", "have", "no", "none", "one", "any", "all", "its",
    "their", "that", "this", "when", "while", "before", "after",
    "between", "least", "most", "than", "noted", "recorded",
    "drawn", "from", "combined",
))

# Placeholder-shaped text: absence wearing a sentence costume.
# Closed set, full-field match (lowercased, trailing period
# stripped) — the sentinel class and the pipeline's own stubs.
# literal: mechanical — placeholder closed set (Piece 6; the sentinel class)
PLACEHOLDERS = frozenset((
    "no value is present",
    "(description pending re-anonymization)",
    "null", "none", "n/a", "na",
))

_QUOTED = re.compile(r"'[^']*'")
_NOTED = re.compile(r"\(noted [^)]*\)")
_WORD = re.compile(r"[a-z0-9']+")


def detect(text: str) -> List[str]:
    """The closed smell set, mechanically applied. Returns the
    named smells found (possibly several); [] is clean. Order is
    fixed: empty and placeholder are terminal (nothing else to
    say about an absent sentence)."""
    stripped = text.strip()
    if not stripped:
        return ["empty"]
    if stripped.lower().rstrip(".").strip() in PLACEHOLDERS:
        return ["placeholder"]
    found: List[str] = []
    if any("_" in tok for tok in stripped.split()):
        found.append("identifier")
    lower = stripped.lower()
    core = _NOTED.sub("", lower).strip().rstrip(".").strip()
    if " is " in core:
        left, right = core.split(" is ", 1)
        lw, rw = _WORD.findall(left), _WORD.findall(right)
        if lw and lw[0] == "the":
            lw = lw[1:]
        if rw and rw[0] == "the":
            rw = rw[1:]
        if lw and lw == rw:
            found.append("tautology")
    words = _WORD.findall(lower)
    if any(a == b for a, b in zip(words, words[1:])):
        found.append("stutter")
    if "tautology" not in found:
        # a repeated content-bearing bigram: the near-tautology
        # ("the ed disposition ... the ed disposition")
        bigrams = Counter(zip(words, words[1:]))
        for (a, b), n in bigrams.items():
            if n > 1 and not (a in STRUCTURE_WORDS
                              and b in STRUCTURE_WORDS):
                found.append("echo")
                break
    return found


def template(text: str) -> str:
    """The shape of a voicing: structure words kept, every run of
    content words masked, quoted values a single token. Two
    voicings with equal templates are one phrasing class."""
    t = _QUOTED.sub(" ⟨q⟩ ", text.lower())
    out: List[str] = []
    masked_run = False
    for tok in re.findall(r"[a-z0-9_']+|⟨q⟩", t):
        if tok in STRUCTURE_WORDS or tok == "⟨q⟩":
            out.append(tok)
            masked_run = False
        else:
            if not masked_run:
                out.append("⟨…⟩")
            masked_run = True
    return " ".join(out)


def phrase_corpus(read) -> List[Dict[str, Any]]:
    """Every stored voicing with its class and smells — condition
    and scope grains, the floor's whole spoken output."""
    rows: List[Dict[str, Any]] = []
    for label in ("condition", "scope"):
        for n in read.nodes(label):
            p = n.properties
            text = p.get("description", "") or ""
            kind = p.get("kind", "-")
            shape = template(text)
            # literal: shape — the corpus row
            rows.append({
                "identity": n.identity, "label": label,
                "kind": kind,
                "degenerate": p.get("degenerate", "false"),
                "text": text, "smells": detect(text),
                "template": shape,
                "class": f"{label}|{kind}|{shape}",
            })
    return rows


def corpus_classes(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group the corpus by phrasing class: one exemplar, the count,
    the union of smells, every member identity. Sorted largest
    first — the sweep reads impact-down."""
    by_class: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        # literal: shape — the class card
        k = by_class.setdefault(row["class"], {
            "class": row["class"], "label": row["label"],
            "kind": row["kind"], "template": row["template"],
            "count": 0, "exemplar": row["text"],
            "_exemplar_smelled": bool(row["smells"]),
            "smells": [], "members": []})
        k["count"] += 1
        k["members"].append(row["identity"])
        if row["smells"] and not k["_exemplar_smelled"]:
            # the sweep must SEE the smell — a clean exemplar under
            # a smelled label would hide the class's own evidence
            k["exemplar"] = row["text"]
            k["_exemplar_smelled"] = True
        for s in row["smells"]:
            if s not in k["smells"]:
                k["smells"].append(s)
    for k in by_class.values():
        del k["_exemplar_smelled"]
    return sorted(by_class.values(),
                  key=lambda k: (-k["count"], k["class"]))


def smell_census(read) -> Dict[str, Any]:
    """The fourth equation (ADR 0080 family, ruled 2026-09-14):
    clean ⊎ smelled == total voicings; every smell counted by
    name, never silent."""
    rows = phrase_corpus(read)
    smelled = [r for r in rows if r["smells"]]
    by_smell: Counter = Counter(
        s for r in smelled for s in r["smells"])
    # literal: shape
    return {"total": len(rows), "clean": len(rows) - len(smelled),
            "smelled": len(smelled), "by_smell": dict(by_smell),
            "classes": len(corpus_classes(rows))}


def render_corpus(rows: List[Dict[str, Any]]) -> str:
    """The sweep artifact — every class renders, no silent caps.
    Markdown for Sunny's one-sitting read: smelled classes first
    within each grain, then by size."""
    classes = corpus_classes(rows)
    smelled = [r for r in rows if r["smells"]]
    by_smell = Counter(s for r in smelled for s in r["smells"])
    # literal: frame — the artifact's page furniture
    lines = [
        "# The phrase corpus — the sweep artifact",
        "",
        "Every stored voicing, one row per phrasing class "
        "(Sunny's go, 2026-09-14: kill classes in one sitting, "
        "not per-round). A smell is a flag, never a verdict.",
        "",
        f"- census: {len(rows) - len(smelled)} clean + "
        f"{len(smelled)} smelled == {len(rows)} voicings",
        f"- smells: {dict(sorted(by_smell.items())) or 'none'}",
        f"- {len(classes)} classes; every class renders below — "
        "no silent caps",
    ]
    for label in ("condition", "scope"):
        subset = [k for k in classes if k["label"] == label]
        subset.sort(key=lambda k: (not k["smells"], -k["count"]))
        # literal: frame — the table header
        lines += ["", f"## {label} ({len(subset)} classes)", "",
                  "| count | kind | smells | template | exemplar |",
                  "|---|---|---|---|---|"]
        for k in subset:
            smell = ", ".join(k["smells"]) or "—"
            lines.append(
                f"| {k['count']} | {k['kind']} | {smell} "
                f"| {k['template']} | {k['exemplar']} |")
    lines.append("")
    return "\n".join(lines)
