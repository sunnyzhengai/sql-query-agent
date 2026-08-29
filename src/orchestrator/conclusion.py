"""The Answer Format Contract (RW-10, ordered 2026-08-28): the
conclusion card is MACHINE-COMPOSED from stamped fields; model prose
fills gaps only — it never carries the verdict, never repeats a
machine field, never renders twice (RW-9's class dies here).

Card class is DATA-DRIVEN — derived from WHICH results the turn
displayed (flags present → flags card; compare present → verdict +
machine diff lines; records → definition; lineage → chain), never
from typing the question's prose (P4 holds). Stochastic narration of
deterministic facts is the defect this module retires.
"""

from __future__ import annotations

from src.branding import product_name

# plain-language glosses per flag class (the contract's §3)
FLAG_GLOSS = {
    "cousin_conflict": "same name, different logic: one name doing "
                       "several jobs",
    "duplicate": "identical logic under different names: these "
                 "compute exactly the same thing",
    "misnomer": "the shared name doesn't mean the same thing "
                "everywhere",
    "grain_shift": "same name, different unit of count (e.g., "
                   "patients vs visits)",
}

# RW-11 (mandatory — W10 gone live): the FIXED refusal wording; the
# system prompt instructs it verbatim, and the composer recognizes
# the policy card by this exact machine-checkable sentence. Brand
# routes through product_name() (brand-neutral-core law — the gate
# caught the hardcode).
POLICY_REFUSAL = (f"{product_name()} answers definitions, not data "
                  "— patient rows never reach the model.")


def _results(outputs: "list[dict]") -> "list[dict]":
    return [o["result"] for o in outputs if o.get("result")]


def _diff_lines(compare_rows: "list[dict]") -> "list[str]":
    for r in compare_rows:
        d = r.get("diff_between_two_largest_groups")
        if d:
            lines = [ln for ln in str(d).splitlines()
                     if (ln.startswith("+") or ln.startswith("-"))
                     and not ln.startswith(("+++", "---"))]
            return lines[:8]
    return []


def compose_conclusion(outputs: "list[dict]", caption: str,
                       answered: bool) -> "dict | None":
    """The machine card, or None when no stamped fields exist to
    compose from (the page then renders prose alone, once)."""
    results = _results(outputs)
    caption = str(caption or "")

    if POLICY_REFUSAL in caption:
        card: dict = {"kind": "policy_refusal",
                      "refusal": POLICY_REFUSAL}
        for r in results:
            for row in r.get("rows") or []:
                if row.get("kind") == "metric":
                    card["definition"] = {
                        "name": row.get("business_name")
                        or row.get("id"),
                        "description": row.get("description") or ""}
                    break
        card["prose"] = caption
        return card

    flag_rows = [row for r in results for row in (r.get("rows") or [])
                 if row.get("flag_class")]
    if flag_rows:
        receipt = next(
            (str(r.get("note") or "") for r in results
             if "sweep receipt" in str(r.get("note") or "")), "")
        return {"kind": "flags",
                "cards": [
                    {"identity": f.get("identity") or f.get("flag_id"),
                     "flag_class": f.get("flag_class"),
                     "severity": f.get("severity"),
                     "member_count": f.get("member_count"),
                     "distinct_logics": f.get("distinct_logics"),
                     "disposition": f.get("disposition") or "open",
                     "why": f.get("description") or "",
                     "gloss": FLAG_GLOSS.get(
                         str(f.get("flag_class")), "")}
                    for f in flag_rows[:12]],
                "closing": (f"{len(flag_rows)} flag(s) · flags "
                            "disclose, never gate"
                            + (f" · {receipt[:120]}" if receipt
                               else "")),
                "prose": caption}

    compare = next((r for r in results if r.get("op") == "compare"),
                   None)
    if compare is not None:
        note = str(compare.get("note") or "")
        verdict = ("DIFFERS" if "DIFFERS" in note
                   else "SAME" if "IDENTICAL" in note else "")
        items = [
            {"name": row.get("business_name") or row.get("id"),
             "description": row.get("description") or ""}
            for r in results if r.get("op") == "retrieve"
            for row in (r.get("rows") or [])
            if row.get("kind") in ("metric", "step")][:4]
        return {"kind": "compare", "verdict": verdict,
                "verdict_note": note[:160],
                "diff_lines": _diff_lines(compare.get("rows") or []),
                "items": items, "prose": caption}

    records = [row for r in results if r.get("op") == "retrieve"
               for row in (r.get("rows") or [])
               if row.get("kind") in ("metric", "step")]
    if records:
        top = records[0]
        sites = top.get("decision_sites") or []
        criteria = ""
        if sites:
            criteria = str((sites[0] or {}).get("expression")
                           or (sites[0] or {}).get("predicate")
                           or "")[:220]
        return {"kind": "definition",
                "name": top.get("business_name") or top.get("id"),
                "description": top.get("description") or "",
                "criteria": criteria,
                "flags_line": str(top.get("governance") or "")[:200],
                "prose": caption}

    lineage = next((r for r in results if r.get("op") == "lineage"),
                   None)
    if lineage is not None:
        return {"kind": "lineage",
                "grain_line": str(lineage.get("universe") or "")[:220],
                "note": str(lineage.get("note") or "")[:220],
                "prose": caption}

    return None
