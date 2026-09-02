"""Group L — the ledger axioms (ADR 0064, SPEC section 14h).

L1  append-only is declared AND OBEYED. TABLE_REGISTRY has carried a
    write_mode field since the beginning and tests/test_table_contracts.py
    checks the LABEL is legal — but nothing checked the label is honoured.
    This module closes that: a table declared `append` may never be
    written with overwrite semantics.

L2  aggregates are derived, never stored. The descent is the purged
    in-place usage counter (a stored count mutated per query); no
    regression guard existed for it until now.

Threat model, both axioms: a contributor under deadline "fixes" a
failing append by switching it to overwrite — which silently destroys
every prior run's telemetry — or reintroduces a stored counter because
recomputing felt expensive. Both are invisible in review and fatal to
the flywheel, because the event log IS the governance record.

Proves: spec:L1, spec:L2, axm:R4
"""

from __future__ import annotations

import re
from pathlib import Path

from src.schemas import TABLE_REGISTRY

ROOT = Path(__file__).resolve().parent.parent

# `df.write.format("delta").mode("<m>").saveAsTable("<t>")` — the one
# sanctioned shape in the notebooks. Real writes wrap across lines with
# backslash continuations, so the gap between `.write` and
# `.saveAsTable` may contain newlines; it may NOT contain a second
# `.write` (that would splice two separate statements together).
_WRITE = re.compile(
    r"\.write(?P<between>(?:(?!\.write)[\s\S])*?)"
    r"\.saveAsTable\(\s*[\"'](?P<table>\w+)[\"']\s*\)"
)
_MODE = re.compile(r"\.mode\(\s*[\"'](?P<mode>\w+)[\"']\s*\)")

# A no-mode saveAsTable is legal ONLY as first-creation, which the
# notebooks guard with tableExists(). We accept it when that guard is
# on a nearby line (the else-branch pattern in 500_validate).
_CREATE_GUARD = re.compile(r"tableExists\(")


def _append_tables() -> "set[str]":
    return {
        name for name, contract in TABLE_REGISTRY.items()
        if contract.get("write_mode") == "append"
    }


def _notebook_sources() -> "dict[str, str]":
    out = {}
    for d in sorted(ROOT.glob("[0-9][0-9]*.Notebook")):
        content = d / "notebook-content.py"
        if content.exists():
            out[d.name.replace(".Notebook", "")] = content.read_text()
    return out


def test_l1_append_tables_are_never_overwritten():
    """spec:L1 — the ledger may only grow. An `append` table written
    with mode('overwrite') destroys every prior run's telemetry."""
    append = _append_tables()
    violations = []
    for notebook, src in _notebook_sources().items():
        lines = src.splitlines()
        for m in _WRITE.finditer(src):
            table = m.group("table")
            found = _MODE.search(m.group("between"))
            mode = found.group("mode") if found else None
            if table not in append:
                continue
            lineno = src[: m.start()].count("\n") + 1
            if mode == "overwrite":
                violations.append(
                    f"{notebook}:{lineno}: {table} is declared append in "
                    f"TABLE_REGISTRY but written with mode('overwrite')")
            elif mode is None:
                window = "\n".join(lines[max(0, lineno - 6):lineno + 2])
                if not _CREATE_GUARD.search(window):
                    violations.append(
                        f"{notebook}:{lineno}: {table} (append) written "
                        f"with no .mode() and no tableExists() guard — "
                        f"an unguarded create silently overwrites")
    assert not violations, (
        "spec:L1 violated — append-only tables written destructively:\n  "
        + "\n  ".join(violations))


def test_l1_every_append_table_is_actually_written_somewhere():
    """A table declared `append` that nothing appends to is a stale
    contract — the declaration should be removed or the writer built."""
    append = _append_tables()
    written = set()
    for src in _notebook_sources().values():
        for m in _WRITE.finditer(src):
            written.add(m.group("table"))
    # Only assert for tables whose owning notebook exists in this repo.
    owners = {
        name: (TABLE_REGISTRY[name].get("owner") or {}).get("notebook")
        for name in append
    }
    present = set(_notebook_sources())
    orphaned = sorted(
        name for name in append - written
        if owners.get(name) in present
    )
    assert not orphaned, (
        f"append table(s) declared but never appended to by their owning "
        f"notebook: {orphaned}")


def test_l2_no_stored_aggregate_is_mutated_in_place():
    """spec:L2 — the purged UsageTracker, pinned as a fixture. Counts
    are recomputed from the append-only event log, never incremented on
    a stored row (the corpse-to-fixture rule, axm:J3)."""
    banned = re.compile(
        r"(?:usage_count|query_count|weight)\s*(?:\+=|=\s*\w+\s*\+\s*1)")
    offenders = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if banned.search(line):
                offenders.append(
                    f"{path.relative_to(ROOT)}:{lineno}: {line.strip()[:70]}")
    assert not offenders, (
        "spec:L2 violated — a stored aggregate is mutated in place. "
        "Derive it from the event log instead (this is the purged "
        "UsageTracker's failure mode):\n  " + "\n  ".join(offenders))


def test_l2_event_tables_are_append_mode():
    """The ledger's own contracts: every gov_*_events table must be
    declared append. An event table on overwrite is not a ledger."""
    wrong = []
    for name, contract in TABLE_REGISTRY.items():
        if not re.match(r"gov_\w*events?$", name):
            continue
        if contract.get("status") != "active":
            continue
        if contract.get("write_mode") != "append":
            wrong.append(f"{name}: write_mode="
                         f"{contract.get('write_mode')!r}, expected 'append'")
    assert not wrong, ("event table(s) not declared append-only:\n  "
                       + "\n  ".join(wrong))
