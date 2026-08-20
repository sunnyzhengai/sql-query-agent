"""The judge — ADR 0044 clause 4: tree comparison is deterministic
code, never an LLM. This module must import no LLM client and take no
describe callback (CI-asserted by the tree contract).

κ (canonicalization) compares MEANING, not phrasing: a reconstruction
matches when it carries the same predicates — same operator (polarity
included: NOT_IN ≠ IN), same principal column, same value set — and
the same either/or grouping. Node ids, source text, and clause context
are deliberately outside κ: prose cannot be expected to reproduce
them, and they carry no decision meaning the other fields don't.
"""

from __future__ import annotations


def _norm_value(v: str) -> str:
    return str(v).strip().strip("'\"").upper()


def _norm_column(c: "str | None") -> str:
    if not c:
        return "?"
    return c.split(".")[-1].strip("[]\"'").upper()


def canonical_fact(fact: dict) -> tuple:
    """One predicate → its meaning tuple."""
    values = fact.get("values")
    if values is None:
        values = fact.get("operands")
    if values is None:
        values = []
    if isinstance(values, (str, int, float)):
        values = [values]  # models emit bare scalars; meaning is the same
    cols = fact.get("columns") or ([fact["column"]] if fact.get("column") else [])
    op = str(fact.get("op") or "?").upper()
    if op == "MATCHES":
        op = "EQ"  # reconstructors phrase joins as matches; same meaning
    norm_cols = [_norm_column(c) for c in cols]
    norm_values = frozenset(_norm_value(v) for v in values)
    if len(set(norm_cols)) >= 2 and not norm_values:
        # a column-to-column predicate (a join): its identity is the
        # PAIR — prose may lead with either side
        col_key = frozenset(norm_cols)
    else:
        principal = _norm_column(fact.get("column") or (cols[0] if cols else None))
        col_key = principal
        # non-principal columns (BETWEEN bounds, right-hand refs) carry
        # meaning symmetrically with literal values — fold them in so
        # "between arrival and departure" matches whether the bounds
        # arrive as columns or as stated tokens
        extras = {c for c in norm_cols if c != principal}
        norm_values = frozenset(norm_values | extras)
    return (op, col_key, norm_values)


def _col_str(col_key) -> str:
    if isinstance(col_key, frozenset):
        return "<->".join(sorted(col_key))
    return str(col_key)


def _partition(facts: "list[dict]") -> "dict[tuple, str]":
    """fact-key -> or-group tag ('' = conjunctive)."""
    return {canonical_fact(f): str(f.get("or_group") or "")
            for f in facts}


def tree_diff(expected_facts: "list[dict]",
              reconstructed_facts: "list[dict]") -> "list[str]":
    """Deterministic mismatch list; empty = the round trip holds.

    Same inputs always produce the same output (spec:E2 for the judge).
    """
    exp = _partition(expected_facts)
    got = _partition(reconstructed_facts)
    diffs: "list[str]" = []
    for key in sorted(set(exp) - set(got), key=repr):
        diffs.append(f"missing decision: op={key[0]} "
                     f"column={_col_str(key[1])} values={sorted(key[2])}")
    for key in sorted(set(got) - set(exp), key=repr):
        diffs.append(f"extra decision (not in the tree): op={key[0]} "
                     f"column={_col_str(key[1])} values={sorted(key[2])}")
    # grouping: alternatives read as requirements (or vice versa) change
    # the population — the LDA lesson
    exp_grouped = {k for k, g in exp.items() if g}
    got_grouped = {k for k, g in got.items() if g}
    for key in sorted((exp_grouped ^ got_grouped) & set(exp) & set(got), key=repr):
        want = "an ALTERNATIVE (or-group)" if key in exp_grouped \
            else "a REQUIREMENT (conjunctive)"
        diffs.append(f"grouping mismatch: op={key[0]} "
                     f"column={_col_str(key[1])} must read as {want}")
    return diffs
