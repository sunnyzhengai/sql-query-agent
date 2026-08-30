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
        # CONSOLE-2 (Sunny's glass: "not clear HOW they differ"):
        # the card LEADS with MEMBER FINGERPRINTS — one row per
        # member a steward scans (qualified name · reads · key
        # criterion from the top decision site · the RW-6
        # description) — then a machine-assembled owner-named
        # contrast line; the raw diff folds beneath as the
        # labeled receipt. Composition only; one composer serves
        # console cards and workbench answers alike.
        groups = [[str(m) for m in (row.get("members") or [])]
                  for row in crows if "group" in row]
        member_ids = [m for g in groups for m in g]
        fingerprints = []
        for mid in member_ids:
            row = retrieved.get(mid, {})
            owner = (mid.split(":", 2)[1] if ":" in mid
                     else mid.rsplit(".", 1)[0])
            sites = row.get("decision_sites") or []
            criterion = str((sites[0] or {}).get("expression")
                            or (sites[0] or {}).get("predicate")
                            or "")[:80] if sites else ""
            desc = str(row.get("description") or "")
            fingerprints.append({
                "id": mid,
                "name": (row.get("business_name")
                         or row.get("name") or mid),
                "owner": owner,
                "reads": _as_names(row.get("source_tables"))[:5],
                "criterion": criterion,
                "description": desc[:160]})
        def _short(fp) -> str:
            if fp["criterion"]:
                return fp["criterion"][:60]
            if fp["description"]:
                return fp["description"].split(".")[0][:60]
            if fp["reads"]:
                return "reads " + fp["reads"][0]
            return "no recorded basis"
        contrast = ""
        if verdict == "DIFFERS" and 2 <= len(fingerprints) <= 4:
            contrast = "; ".join(
                f"{fp['owner']} — {_short(fp)}"
                for fp in fingerprints)
        diff_label = ""
        if len(groups) >= 2:
            big = sorted(groups, key=len, reverse=True)[:2]
            diff_label = (f"receipt: − {big[0][0]} · + {big[1][0]}"
                          + (f" ({len(groups)} groups — largest "
                             "two diffed)" if len(groups) > 2
                             else ""))
        items = [
            {"name": row.get("business_name") or row.get("id"),
             "description": row.get("description") or ""}
            for r in results if r.get("op") == "retrieve"
            for row in (r.get("rows") or [])
            if row.get("kind") in ("metric", "step")][:4]
        return {"kind": "compare", "verdict": verdict,
                "verdict_note": note[:160],
                "fingerprints": fingerprints[:6],
                "contrast": contrast,
                "diff_label": diff_label,
                "diff_lines": _diff_lines(crows),
                "items": items, "prose": caption}

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
