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
    import re as _re
    for r in compare_rows:
        d = r.get("diff_between_two_largest_groups")
        if d:
            lines = [ln for ln in str(d).splitlines()
                     if (ln.startswith("+") or ln.startswith("-"))
                     and not ln.startswith(("+++", "---"))]
            # the DISTILLED delta (glass check 2026-08-28: E11.80
            # sat buried at the end of two 80-literal lines) — when
            # a -/+ pair differs by quoted-literal SET, the card
            # leads with the exact tokens that changed. Machine
            # set-arithmetic, identical wording every run.
            out: "list[str]" = []
            for i in range(len(lines) - 1):
                a, b = lines[i], lines[i + 1]
                if a.startswith("-") and b.startswith("+"):
                    sa = set(_re.findall(r"'([^']+)'", a))
                    sb = set(_re.findall(r"'([^']+)'", b))
                    added = sorted(sb - sa)
                    removed = sorted(sa - sb)
                    if (added or removed) and len(added) <= 6 \
                            and len(removed) <= 6:
                        for tok in added:
                            out.append(f"+ {tok} — present only in "
                                       "one definition")
                        for tok in removed:
                            out.append(f"- {tok} — absent from one "
                                       "definition")
            return (out + lines)[:8]
    return []


# --- CONSOLE-4 v2 (design RATIFIED 2026-08-30): ONE computation,
# three renderings. The DISTINGUISHING SET per member (parsed
# predicates + reads; shared elements as background) feeds the
# GRID CARD (<=3 members), the GROUPED ROSTER (>3), and the
# developer snippets. Steward view NEVER shows SQL; the hash
# verdict + full fragments stay in the event record.

def _norm_el(s: str) -> str:
    return " ".join(str(s).split())


def _is_equijoin(expr: str) -> bool:
    """CONSOLE-4c item 2: COL = COL (identifier on BOTH sides, no
    literal) is structural plumbing — a join, never a criterion."""
    import re as _re
    return bool(_re.fullmatch(
        r"[\w.\[\]]+\s*=\s*[A-Za-z_][\w.\[\]]*",
        expr.strip()))


def _member_elements(row: dict) -> "list[tuple[str, str]]":
    els: "list[tuple[str, str]]" = []
    for tbl in _as_names(row.get("source_tables")):
        els.append(("read", tbl))
    for site in row.get("decision_sites") or []:
        expr = str((site or {}).get("expression")
                   or (site or {}).get("expression_sql")
                   or (site or {}).get("predicate") or "")
        expr = _norm_el(expr)
        if expr and not _is_equijoin(expr):
            els.append(("pred", expr))
    return els


def _col(token: str) -> str:
    """CONSOLE-4c item 3: alias-qualified columns never face the
    steward — CC.CPT_CODE renders CPT_CODE."""
    return token.strip("[]").split(".")[-1].strip("[]")


def _humanize(table: str) -> str:
    return table.strip("[]").split(".")[-1].replace("_", " ").lower()


def distinguishing_set(member_rows: "dict[str, dict]") -> dict:
    """mid -> its OWN elements minus every other member's; shared =
    the intersection. Pure set arithmetic — the one computation."""
    sets = {mid: set(_member_elements(row))
            for mid, row in member_rows.items()}
    if not sets:
        return {"shared": [], "members": {}}
    shared = (set.intersection(*sets.values())
              if len(sets) > 1 else set())
    members = {}
    for mid, own in sets.items():
        others = (set().union(*(s for m, s in sets.items()
                                if m != mid))
                  if len(sets) > 1 else set())
        members[mid] = sorted(own - others)
    return {"shared": sorted(shared), "members": members}


def _business_words(kind: str, value: str,
                    columns: "list[str] | None" = None) -> str:
    """The ratified template vocabulary — deterministic English for
    a parsed element; the fallback names tables/columns and refers
    to the developer view. SQL never leaks to the steward.

    CONSOLE-4d item 3: a COMPOUND predicate phrases EVERY clause —
    the gestational twins differ only in their second clause
    (NOT LIKE 'O24.4%' vs OR LIKE 'O24.4%'), and phrasing the
    first clause alone made them read identically."""
    import re as _re
    if kind == "read":
        return f"additionally reads {value}"
    v = value.strip()
    parts = _re.split(r"\s+(AND|OR)\s+", v, flags=_re.IGNORECASE)
    if len(parts) >= 3:
        phrases, i = [], 0
        while i < len(parts):
            clause = parts[i].strip().strip("()")
            joiner = (parts[i - 1].lower()
                      if i and parts[i - 1].upper() in ("AND", "OR")
                      else "")
            words = _business_words(kind, clause, columns)
            if "additional recorded condition" in words:
                words = ""
            if words:
                phrases.append(("also " if joiner == "or" else "")
                               + words)
            i += 2
        if phrases:
            return "; ".join(phrases)[:120]
    return _single_predicate_words(v, columns)


def _single_predicate_words(v: str,
                            columns: "list[str] | None" = None) -> str:
    import re as _re
    if _re.match(r"NOT\s+EXISTS", v, _re.IGNORECASE):
        m = _re.search(r"FROM\s+([\w.\[\]]+)", v, _re.IGNORECASE)
        src = m.group(1) if m else "the checked table"
        return f"excludes those with a match in {src}"
    m = _re.match(r"([\w.\[\]]+)\s+(NOT\s+)?IN\s*\(", v,
                  _re.IGNORECASE)
    if m:
        n = v.count(",") + 1
        neg = "excludes" if m.group(2) else "limits"
        trunc = (not v.rstrip().endswith(")")
                 or v.count("'") % 2 == 1)
        count = f"\u2265{n}" if trunc else str(n)
        return f"{neg} {_col(m.group(1))} to {count} listed value(s)"
    m = _re.search(r"COUNT\s*\([^)]*\)\s*(>=|>)\s*(\d+)", v,
                   _re.IGNORECASE)
    if m:
        k = int(m.group(2)) + (1 if m.group(1) == ">" else 0)
        return f"requires at least {k} occurrence(s)"
    m = _re.match(r"([\w.\[\]]+)\s*(>=|<=|>|<|=)\s*(\S+)", v)
    if m:
        opword = {">=": "at least", "<=": "at most",
                  ">": "more than", "<": "under",
                  "=": "exactly"}[m.group(2)]
        return (f"requires {_col(m.group(1))} {opword} "
                f"{m.group(3).strip(chr(39))}")
    m = _re.match(r"([\w.\[\]]+)\s+NOT\s+LIKE\s+(\S+)", v,
                  _re.IGNORECASE)
    if m:
        return (f"excludes the pattern {m.group(2).strip(chr(39))} "
                f"on {_col(m.group(1))}")
    m = _re.match(r"([\w.\[\]]+)\s+LIKE\s+(\S+)", v,
                  _re.IGNORECASE)
    if m:
        return (f"matches the pattern {m.group(2).strip(chr(39))} "
                f"on {_col(m.group(1))}")
    if columns:
        return ("has an additional condition on "
                + ", ".join(columns[:3])
                + " (see developer view)")
    return "has an additional recorded condition (see developer view)"


def _element_words(el: "tuple[str, str]",
                   columns: "list[str] | None" = None) -> str:
    return _business_words(el[0], el[1], columns)


def _difference_lead(dset: dict, retrieved: dict,
                     set_summary: str = "") -> str:
    """The bolded first sentence — deterministic cases over the
    computed sets only. The approved mock's shape: a literal-set
    delta with ONE only-in clause leads with exactly that."""
    if set_summary and set_summary.count("only in") == 1:
        clause = next(b for b in set_summary.split(" · ")
                      if "only in" in b)
        return f"The one difference: {clause}."
    distinct = {m: els for m, els in dset["members"].items() if els}
    if not distinct:
        return ""
    if len(distinct) == 1:
        mid, els = next(iter(distinct.items()))
        name = _member_display(retrieved, mid)
        if len(els) == 1:
            return (f"The one difference: {name} "
                    f"{_element_words(els[0])}.")
        return (f"All differences sit in {name}: "
                + "; ".join(_element_words(e)
                            for e in els[:3]) + ".")
    total = sum(len(e) for e in distinct.values())
    return (f"{total} distinguishing element(s) across "
            f"{len(distinct)} member(s) — the grid marks what is "
            "the same and what is not.")


def _pattern_line(dset: dict, set_summary: str,
                  verdict: str) -> str:
    """The 💡 reading — deterministic templates keyed ONLY on
    computed relations."""
    if verdict == "SAME":
        return ("byte-equal logic under different names — reads as "
                "a duplicate, not two purposes")
    only_counts = [len(e) for e in dset["members"].values() if e]
    if (set_summary and "only in" in set_summary
            and set_summary.count("only in") == 1
            and sum(only_counts) <= 2):
        return ("one side is a strict superset by a single value — "
                "reads as a stale copy, not two purposes")
    reads_only = all(all(k == "read" for k, _v in e)
                     for e in dset["members"].values() if e)
    if reads_only and any(only_counts):
        return ("the members draw from different sources — reads "
                "as distinct purposes sharing a name")
    return ""


def _criterion_sketch(raw: str) -> str:
    """The decision predicate, one-breath sized: long IN-lists
    summarize to column + value count (CONSOLE-2b). CONSOLE-2c:
    COUNTS MUST BE TRUE — a store-truncated expression (the old
    500-char cap produced "IN (49 values)" against a real 80)
    discloses instead of fabricating; the raised cap + a 300 rerun
    make counts true again."""
    import re as _re
    raw = " ".join(str(raw).split())
    m = _re.match(r"(\S+)\s+(?:NOT\s+)?IN\s*\(", raw,
                  _re.IGNORECASE)
    if m and raw.count(",") >= 3:
        truncated = (not raw.rstrip().endswith(")")
                     or raw.count("'") % 2 == 1)
        if truncated:
            return (f"{m.group(1)} IN (≥{raw.count(',') + 1} "
                    "values — list truncated in this store; a "
                    "graph rebuild restores the true count)")
        return f"{m.group(1)} IN ({raw.count(',') + 1} values)"
    return raw[:80]


def _member_display(retrieved: "dict[str, dict]", mid: str) -> str:
    """CONSOLE-2c GENERATOR KILL (the bare-name class, third
    surface): EVERY member-name render goes through this — a name
    another member shares renders QUALIFIED with its id; bare
    rendering of colliding members is unwritable (the collision
    gate in tests holds every card field).

    CONSOLE-4d item 2: the ONE label form is the business name;
    a member the store never delivered (an empty row) still
    renders as a name + ref, never a raw id alone."""
    row = retrieved.get(mid, {})
    name = str(row.get("business_name") or row.get("name") or "")
    if not name:
        # unretrieved member — name it from its ref, never raw
        return f"{mid.rsplit('.', 1)[-1]} ({mid})"
    for oid, other in retrieved.items():
        if oid == mid:
            continue
        oname = str(other.get("business_name")
                    or other.get("name") or "")
        if oname and oname == name:
            return f"{name} ({mid})"
    return name


def _as_names(v) -> "list[str]":
    # RW-23 (Sunny's walk find): source_tables arrives as a STRING
    # on metric facts — iterating it spelled "DIAGNOSIS_CODES" as
    # "D, I, A, G…". Strings split on commas; lists pass through;
    # characters never iterate.
    if v is None:
        return []
    if isinstance(v, str):
        return [s.strip() for s in v.split(",") if s.strip()]
    return [str(x) for x in v]


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
                     "member_names": (f.get("member_names")
                                      or [])[:12],
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
        crows = compare.get("rows") or []
        retrieved = {str(row.get("id")): row
                     for r in results if r.get("op") == "retrieve"
                     for row in (r.get("rows") or [])}
        groups = [[str(m) for m in (row.get("members") or [])]
                  for row in crows if "group" in row]
        member_ids = [m for g in groups for m in g]
        member_rows = {m: retrieved.get(m, {}) for m in member_ids}
        # CONSOLE-4 v2: THE ONE COMPUTATION
        dset = distinguishing_set(member_rows)
        set_summary = ""
        diff_label = ""
        if len(groups) >= 2:
            big = sorted(groups, key=len, reverse=True)[:2]
            diff_label = f"receipt: − {big[0][0]} · + {big[1][0]}"
            import re as _re
            for row in crows:
                d = row.get("diff_between_two_largest_groups")
                if not d:
                    continue
                minus = [ln for ln in str(d).splitlines()
                         if ln.startswith("-")
                         and not ln.startswith("---")]
                plus = [ln for ln in str(d).splitlines()
                        if ln.startswith("+")
                        and not ln.startswith("+++")]
                sa = {m for ln in minus
                      for m in _re.findall(r"'([^']+)'", ln)}
                sb = {m for ln in plus
                      for m in _re.findall(r"'([^']+)'", ln)}
                if len(sa) < 3 and len(sb) < 3:
                    continue
                shared_n = len(sa & sb)
                bits = [f"{shared_n} value(s) shared"]
                for tok in sorted(sb - sa)[:4]:
                    bits.append(f"{tok} only in " + _member_display(
                        retrieved, big[1][0]))
                for tok in sorted(sa - sb)[:4]:
                    bits.append(f"{tok} only in " + _member_display(
                        retrieved, big[0][0]))
                if shared_n and len(bits) > 1:
                    set_summary = " · ".join(bits)
                break
        # CONSOLE-4d item 2: ONE label form per family — when ANY
        # member needs qualification, EVERY member carries its ref,
        # so a roster never mixes bare and qualified names
        family_names = [str((member_rows.get(m) or {}).get(
            "business_name") or (member_rows.get(m) or {}).get(
            "name") or "") for m in member_ids]
        uniform_qualify = len(family_names) != len(set(family_names))
        members = []
        for mid in member_ids:
            row = member_rows.get(mid, {})
            els = dset["members"].get(mid, [])
            sites = row.get("decision_sites") or []
            cols = [str(c) for s in sites
                    for c in (s or {}).get("columns") or []]
            disp = _member_display(retrieved, mid)
            if uniform_qualify and not disp.endswith(f"({mid})"):
                disp = f"{disp} ({mid})"
            members.append({
                "id": mid,
                "name": disp,
                "owner": (mid.split(":", 2)[1] if ":" in mid
                          else mid.rsplit(".", 1)[0]),
                "description": str(row.get("description")
                                   or "")[:200],
                "distinguishing_plain": [
                    _element_words(e, cols) for e in els[:4]],
                "snippets": [e[1] for e in els if e[0] == "pred"][:4],
                "reads": _as_names(row.get("source_tables"))[:6],
                "steward": str(row.get("steward") or "")})
        # the GRID (<=3) rows with sames marked; the ROSTER above
        mode = "grid" if len(members) <= 3 else "roster"
        grid_rows = []
        if mode == "grid" and members:
            aspects = [
                ("what it is", [m["description"] for m in members]),
                ("the distinguishing element", [
                    "; ".join(m["distinguishing_plain"]) or "(none)"
                    for m in members]),
                ("selects from", [", ".join(m["reads"]) or "—"
                                  for m in members]),
                ("steward", [m["steward"] or "—" for m in members]),
            ]
            for label, cells in aspects:
                same = len(set(cells)) == 1
                grid_rows.append({"aspect": label, "same": same,
                                  "cells": cells})
        roster_groups = []
        if mode == "roster":
            # CONSOLE-4c: group key = the DOMINANT DISTINGUISHING
            # READ, worded ("By diagnosis codes"); a member whose
            # templates degrade leads with its RW-6 description;
            # phrases cap at one breath
            by_header: "dict[str, list]" = {}
            background = {v for k, v in dset["shared"]
                          if k == "read"}
            for m in members:
                # the METHOD read: the member's reads minus the
                # ALL-shared background (a read two cousins share
                # is exactly what groups them — the strictly-
                # unique set is for the grid, not the key)
                method_reads = [r for r in m["reads"]
                                if r not in background]
                els = dset["members"].get(m["id"], [])
                preds = [v for k, v in els if k == "pred"]
                if method_reads:
                    header = f"By {_humanize(method_reads[0])}"
                elif preds:
                    import re as _re2
                    cm = _re2.match(r"([\w.\[\]]+)", preds[0])
                    header = (f"By {_humanize(_col(cm.group(1)))}"
                              if cm else "By shared sources")
                else:
                    header = "By shared logic"
                plain = m["distinguishing_plain"]
                degraded = all("developer view" in ph
                               for ph in plain) if plain else True
                if degraded and m["description"]:
                    phrase = m["description"].split(".")[0][:70]
                else:
                    phrase = "; ".join(plain)[:70]
                if not phrase:
                    # CONSOLE-4d assertion: when the hash partition
                    # proves all-distinct, "(shared logic only)" is
                    # a LIE — the description or a typed pointer
                    all_distinct = (len(groups) == len(members)
                                    and len(groups) > 1)
                    phrase = (m["description"].split(".")[0][:70]
                              if m["description"] else
                              ("distinct logic — see developer view"
                               if all_distinct
                               else "(shared logic only)"))
                by_header.setdefault(header, []).append({
                    "id": m["id"], "name": m["name"],
                    "phrase": phrase,
                    "steward": m["steward"]})
            roster_groups = [
                {"header": h, "members": ms}
                for h, ms in sorted(by_header.items())]
        shared_reads = sorted({v for k, v in dset["shared"]
                               if k == "read"})
        shared_preds = sum(1 for k, _v in dset["shared"]
                           if k == "pred")
        return {"kind": "compare", "verdict": verdict,
                "verdict_note": note[:160],
                "mode": mode,
                "difference_lead": _difference_lead(dset, retrieved,
                                                    set_summary),
                "pattern_line": _pattern_line(dset, set_summary,
                                              verdict),
                "set_summary": set_summary,
                "shared": {"reads": shared_reads,
                           "predicate_count": shared_preds},
                "members": members,
                "grid": grid_rows,
                "roster": roster_groups,
                "diff_label": diff_label,
                "prose": caption}

    # RW-BATCH-6 item 2 (E-battery B6): a retrieved REPORT record
    # carries its parsed links — the FEEDS card renders the chain
    # (metrics executed, tables read, measures) instead of nothing.
    # Data-driven: link fields present on displayed rows, never
    # question typing.
    link_rows = [row for r in results if r.get("op") == "retrieve"
                 for row in (r.get("rows") or [])
                 if row.get("executes_metrics") is not None
                 or row.get("reads_tables") is not None]
    if link_rows:
        top = link_rows[0]
        def _names(field):
            return [str(x.get("name") or x.get("id") or "")
                    for x in (top.get(field) or [])][:8]
        return {"kind": "feeds",
                "name": (top.get("business_name") or top.get("name")
                         or top.get("id")),
                "executes_metrics": _names("executes_metrics"),
                "reads_tables": _names("reads_tables"),
                "measures": _names("measures"),
                "link_state": str(top.get("link_state") or ""),
                "prose": caption}

    records = [row for r in results if r.get("op") == "retrieve"
               for row in (r.get("rows") or [])
               if row.get("kind") in ("metric", "step")]
    if len(records) == 1:
        top = records[0]
        sites = top.get("decision_sites") or []
        criteria = ""
        if sites:
            criteria = str((sites[0] or {}).get("expression")
                           or (sites[0] or {}).get("predicate")
                           or "")[:220]
        return {"kind": "definition",
                "id": top.get("id"),
                "name": top.get("business_name") or top.get("id"),
                "description": top.get("description") or "",
                "criteria": criteria,
                "flags_line": str(top.get("governance") or "")[:200],
                "prose": caption}
    if records:
        # RW-BATCH-6 item 2: MULTIPLE records with no compare = the
        # MAP card — every record shown with its connections; the
        # single-record definition card must not swallow the rest
        return {"kind": "map",
                "items": [
                    {"id": row.get("id"),
                     "name": (row.get("business_name")
                              or row.get("name") or row.get("id")),
                     "record_kind": row.get("kind"),
                     "of_metric": row.get("of_metric"),
                     "description": str(row.get("description")
                                        or "")[:160],
                     "steps": [str(s.get("name") or "")
                               for s in (row.get("steps") or [])][:6],
                     "source_tables":
                         _as_names(row.get("source_tables"))[:6]}
                    for row in records[:6]],
                "prose": caption}

    lineage = next((r for r in results if r.get("op") == "lineage"),
                   None)
    if lineage is not None:
        return {"kind": "lineage",
                "grain_line": str(lineage.get("universe") or "")[:220],
                "note": str(lineage.get("note") or "")[:220],
                "prose": caption}

    # RW-22 (extended battery, the sole blocker): a CENSUS composes
    # the census card — the count line + the rows (name +
    # description), per the format contract. Flag censuses composed
    # above; this catches every other kind.
    census = next((r for r in results if r.get("op") == "census"),
                  None)
    if census is not None:
        crows = census.get("rows") or []
        return {"kind": "census",
                "ref": str(census.get("ref") or ""),
                "count_line": (str(census.get("headline") or "")
                               or f"{len(crows)} item(s) — "
                                  + str(census.get("universe")
                                        or "")[:160]),
                "items": [
                    {"name": (row.get("business_name")
                              or row.get("name") or row.get("id")),
                     "description": str(row.get("description")
                                        or "")[:160]}
                    for row in crows[:12]],
                "total": len(crows),
                "prose": caption}

    # RW-BATCH-6 item 2, AMENDED by RW-22 (the composer-gap law):
    # ANY successful op's rows compose — a bare card of names and
    # kinds beats no answer, always
    any_rows = [row for r in results
                for row in (r.get("rows") or []) if row.get("id")]
    if any_rows:
        return {"kind": "map",
                "items": [
                    {"name": (row.get("business_name")
                              or row.get("name") or row.get("id")),
                     "record_kind": row.get("kind") or "record",
                     "of_metric": row.get("of_metric"),
                     "description": str(row.get("description")
                                        or "")[:160],
                     "steps": [], "source_tables": []}
                    for row in any_rows[:6]],
                "prose": caption}
    return None


# --- GRAPH-PANEL-1 (Sunny's direction: show the inner workings) -------

_KIND_COLUMN = {"report": 0, "measure": 0, "metric": 1, "flag": 1,
                "step": 2, "term": 2, "table": 3, "column": 3}


def compose_subgraph(outputs: "list[dict]") -> "dict | None":
    """The answer's SUBGRAPH — derived EXCLUSIVELY from the turn's
    stamped results (receipts only; nothing model-claimed renders):
    displayed records as nodes; their step/read/link fields as
    edges; compare verdicts as DERIVED edges, labeled as computed.
    Deterministic: sorted nodes and edges — identical answers give
    identical pictures. P4/P5-safe: ids, names, kinds, flag classes
    only — never rows."""
    results = _results(outputs)
    nodes: "dict[str, dict]" = {}
    edges: "set[tuple]" = set()

    def add_node(nid, kind=None, name=None, flag_class=None):
        nid = str(nid or "")
        if not nid:
            return ""
        n = nodes.setdefault(nid, {"id": nid, "kind": "", "name": ""})
        if kind and not n["kind"]:
            n["kind"] = str(kind)
        if name and not n["name"]:
            n["name"] = str(name)
        if flag_class:
            n["flag_class"] = str(flag_class)
        return nid

    anchors: "set[str]" = set()
    compared: "list[list[str]]" = []
    for r in results:
        params = r.get("params") or {}
        if r.get("op") == "retrieve":
            anchors.update(str(i) for i in params.get("ids") or [])
        rows = r.get("rows") or []
        if r.get("op") == "compare":
            group_members = [
                [str(m) for m in (row.get("members") or [])]
                for row in rows if "group" in row]
            flat = [m for g in group_members for m in g]
            if flat:
                compared.append(flat)
            for m in flat:
                add_node(m, kind="step" if
                         m.startswith("transform:") else "metric")
            continue
        for row in rows:
            rid = add_node(row.get("id"), row.get("kind"),
                           row.get("business_name") or row.get("name"),
                           row.get("flag_class"))
            if not rid:
                continue
            for s in row.get("steps") or []:
                sid = add_node(s.get("id") or
                               f"{rid}:{s.get('name')}", "step",
                               s.get("name"))
                edges.add((rid, sid, "step", False))
            src = row.get("source_tables")
            src_list = ([x.strip() for x in src.split(",")]
                        if isinstance(src, str) else list(src or []))
            for tname in src_list:
                if tname:
                    tid = add_node(f"table:{tname}", "table", tname)
                    edges.add((rid, tid, "reads", False))
            for field, label in (("executes_metrics", "executes"),
                                 ("reads_tables", "reads"),
                                 ("measures", "measures")):
                for x in row.get(field) or []:
                    xid = add_node(
                        x.get("id"),
                        "table" if label == "reads" else "metric",
                        x.get("name"))
                    if xid:
                        edges.add((rid, xid, label, False))
            for m in row.get("members") or []:
                mid = add_node(m.get("id"), None, m.get("name"))
                if mid:
                    edges.add((mid, rid, "member_of", False))
            if row.get("of_metric"):
                pid = add_node(row["of_metric"], "metric")
                edges.add((pid, rid, "step", False))
    # DERIVED edges (drawn distinctly, labeled as computed): the
    # compare verdict connects every compared pair
    for flat in compared:
        for i in range(len(flat) - 1):
            a, b = sorted((flat[i], flat[i + 1]))
            edges.add((a, b, "compared", True))
    if not nodes:
        return None
    for nid in anchors:
        if nid in nodes:
            nodes[nid]["anchor"] = True
    out_nodes = sorted(
        nodes.values(),
        key=lambda n: (_KIND_COLUMN.get(n["kind"], 2),
                       n["name"] or n["id"], n["id"]))[:40]
    kept = {n["id"] for n in out_nodes}
    out_edges = sorted(
        [{"from": a, "to": b, "label": lb, "derived": dv}
         for a, b, lb, dv in edges if a in kept and b in kept],
        key=lambda e: (e["from"], e["to"], e["label"]))
    return {"nodes": out_nodes, "edges": out_edges,
            "truncated": len(nodes) > 40}
