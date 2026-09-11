"""THE GLOSSARY PROCESS (Ruling_Glossary_Process.md, ruled by
Sunny 2026-09-11): estate acronyms are DOCUMENTED, not guessed — a
five-phase evidence ladder (dictionary-first, guessing last) with a
conservation law: every scanned token holds exactly one status in
the ledger; nothing vanishes.

Two files per estate under glossary/:
  abbreviation_dictionary.json — Phase 0: the imported source truth
    (customer prereq; our dev estates carry an authored fixture).
  acronym_ledger.json — Phases 1-4 in one file: one entry per
    scanned token, its whole life visible in one place.

THE FIELD LAW: machine fields (carriers, sample, position, and
proposed/evidence while unruled) refresh mechanically; ruled fields
(status once blessed/held/plain, expansions, scope, why_held,
approvals) are human-only — refresh may NEVER touch them.
"""
import json
import pathlib
from typing import Dict, List, Tuple

from aivia.flows import enrich
from aivia.lenses.ask_index import _tokens

DICTIONARY = "abbreviation_dictionary.json"
LEDGER = "acronym_ledger.json"
# the scan sweeps the ESTATE's names — governance/vocabulary kinds
# are not estate names (blessed vocabulary must not carry itself)
# literal: mechanical — the scan's governance-kind exclusion
SCAN_EXCLUDED = ("acronym", "person", "agent", "role")
# literal: frame — the ledger's status contract (machine vs ruled)
MACHINE_STATUSES = ("unreviewed", "matched")
# literal: frame — human/Scribe-owned statuses; refresh never writes
RULED_STATUSES = ("plain", "proposed", "abstained", "blessed", "held")
SAMPLE_CAP = 5


def scan(read) -> Dict[str, Dict]:
    """Phase 1 — the total scan: every distinct name token outside
    the excluded governance kinds, with carrier count, sample
    carriers, and observed positions (only/first/mid/last)."""
    found: Dict[str, Dict] = {}
    for n in read.nodes(None):
        if n.label in SCAN_EXCLUDED:
            continue
        nm = str(n.properties.get("name")
                 or n.identity.rsplit("|", 1)[-1])
        for t in sorted(_tokens(nm)):
            row = found.setdefault(
                # literal: shape
                t, {"carriers": 0, "sample": [], "position": set()})
            row["carriers"] += 1
            if len(row["sample"]) < SAMPLE_CAP \
                    and nm not in row["sample"]:
                row["sample"].append(nm)
            row["position"].add(_position(t, nm))
    for row in found.values():
        row["position"] = sorted(row["position"])
    return found


def _position(token: str, name: str) -> str:
    parts = [p for p in _split_words(name)]
    hits = [i for i, p in enumerate(parts) if p == token]
    i = hits[0] if hits else 0
    if len(parts) == 1:
        return "only"
    if i == 0:
        return "first"
    if i == len(parts) - 1:
        return "last"
    return "mid"


def _split_words(name: str) -> List[str]:
    # the same folding the ask index uses, kept ordered so position
    # is meaningful (a set loses first-vs-last)
    out, cur = [], []
    for ch in name:
        if ch.isalnum():
            cur.append(ch.lower())
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    # camelCase seam: the ask tokenizer folds these too; positions
    # stay coarse (whole-word grain) which is enough for the ledger
    return out


def load_dictionary(glossary_dir: pathlib.Path) -> Dict[str, Dict]:
    f = glossary_dir / DICTIONARY
    if not f.is_file():
        return {}
    return json.loads(f.read_text()).get("entries", {})


def load_ledger(glossary_dir: pathlib.Path) -> Dict[str, Dict]:
    f = glossary_dir / LEDGER
    if not f.is_file():
        return {}
    return json.loads(f.read_text())


def ledger_refresh(read, glossary_dir: pathlib.Path) -> Dict[str, int]:
    """Phases 1+2, idempotent, THE FIELD LAW enforced: upsert every
    scanned token (new -> unreviewed), refresh machine facts on
    every entry, classify unreviewed/matched against the Phase-0
    dictionary. Ruled entries keep their ruled fields untouched.
    Returns the status census (the conservation reading)."""
    ledger = load_ledger(glossary_dir)
    dictionary = load_dictionary(glossary_dir)
    for token, facts in scan(read).items():
        row = ledger.setdefault(token, {"status": "unreviewed"})
        row["carriers"] = facts["carriers"]
        row["sample"] = facts["sample"]
        row["position"] = facts["position"]
        if row["status"] in MACHINE_STATUSES:
            hit = _dictionary_match(token, facts["position"],
                                    dictionary)
            if hit is not None:
                row["status"] = "matched"
                row["proposed"] = list(hit["expansions"])
                row["evidence"] = f"{DICTIONARY}: {token}"
            else:
                row["status"] = "unreviewed"
                row.pop("proposed", None)
                row.pop("evidence", None)
    glossary_dir.mkdir(parents=True, exist_ok=True)
    (glossary_dir / LEDGER).write_text(
        json.dumps(ledger, indent=1, sort_keys=True) + "\n")
    census: Dict[str, int] = {}
    for row in ledger.values():
        census[row["status"]] = census.get(row["status"], 0) + 1
    return census


def _dictionary_match(token: str, positions: List[str],
                      dictionary: Dict[str, Dict]):
    entry = dictionary.get(token)
    if entry is None:
        return None
    want = entry.get("position")
    if want and not ({want, "only"} & set(positions)):
        return None
    return entry


def seed_journal(store, read, glossary_dir: pathlib.Path) -> int:
    """The seed, repointed to the ledger's BLESSED slice: births
    acronym nodes through the real write path (enrich.bless), so a
    journal-wired store writes each blessing as a governance-journal
    line — the journal is BORN, never copied. Delta by name: names
    already in the store (a replayed journal) are skipped, so a
    ruled bless in the ledger lands at the next boot."""
    ledger = load_ledger(glossary_dir)
    have = {n.properties["name"].lower()
            for n in read.nodes("acronym")}
    made = 0
    for name in sorted(ledger):
        row = ledger[name]
        if row.get("status") != "blessed" or name.lower() in have:
            continue
        made += enrich.bless(
            store, {name: row["expansions"]},
            approved_by=row["approved_by"],
            approved_at=row["approved_at"])
    return made


def review_queue(glossary_dir: pathlib.Path
                 ) -> List[Tuple[str, Dict]]:
    """The ruling view: what awaits Sunny, impact-ordered by
    carrier count (matched first — cheap bulk ratification)."""
    ledger = load_ledger(glossary_dir)
    # literal: mechanical — the queue's status order
    order = {"matched": 0, "proposed": 1, "abstained": 2,
             "unreviewed": 3}
    rows = [(t, r) for t, r in ledger.items()
            if r.get("status") in order]
    rows.sort(key=lambda x: (order[x[1]["status"]],
                             -x[1].get("carriers", 0), x[0]))
    return rows
