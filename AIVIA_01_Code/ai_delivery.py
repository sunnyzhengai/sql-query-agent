"""ai_delivery.py — THE ONE DELIVERY FILE.

THE CONSOLIDATION RULING (2026-10-05, Sunny: "all we need is a
consolidated file, and each step updates part of it... name it
ai_delivery.json"): the delivery layer is ONE file; each step
writes only its own keys; nothing is recorded that no step
consumes and no user sees. Contract: the 09 contract's output
section carries the ruling; 07 and 08 contracts carry their
keys.
"""

# ==== PSEUDO (the consolidation build, 2026-10-05) ==================
# THE FILE: <out_dir>/ai_delivery.json
#   basis            — versions, once at the top (the row diet)
#   reports[]        — {report, files} (the 08 key) +
#                      {description: {text, voice, status}} (the
#                      07 key) + {terms: [...]} (the 09 key)
#   reportless_files[] — {file, description, terms} for corpus
#                      files no report touches (never pushed)
#   counts           — one block per step; 09's carries the
#                      equations + the skipped list (plumbing is
#                      a COUNT, not rows — her override surface)
#
# update_terms(out_dir, placed, skipped, basis, files_in_run) —
#   the 09 writer: clears terms ONLY on entries whose file is in
#   this run (only_file safety: other files' terms preserved),
#   places rows under their report entry (tied via 08) or their
#   reportless_files entry, merges the skipped list delta-by-
#   node, recomputes THE UNIQUENESS LAW GLOBALLY (collision is a
#   derived field over ALL rows, first-by-order wins, never a
#   silent rename), recomputes counts.09, checks THE EQUATIONS
#   BEFORE writing (a red block does not ship -> raise).
#
# assemble(out_dir, dir07, dir08, dir06) — the 08+07 keys:
#   rebuilds reports[] from 08_pbi_reports.json (absent file ->
#   no reports, everything reportless) and reportless_files[]
#   from the 06 file-grain rows; description per entry = the 07
#   file card when the sheet carries one (voice: business), else
#   the 06 file sentence (voice: technical) — NEVER a silent
#   downgrade, the voice is always labeled. Multi-file reports:
#   one block per file, voice business only when every file
#   carries a card. Terms are PRESERVED by entry key.
#
# bless_term(out_dir, dir07, node_id, report, ruling) — HER HAND
#   ONLY (the ratify clause): refuses plumbing-absent rows,
#   failed cards, collided names; appends to the 07 registry's
#   terms list (delta-by-(node, report)); flips the row in
#   place; recomputes counts; rewrites.
#
# Determinism: sorted entries and terms, indent=1, no
# timestamps. The 06/07/08 stores and the per-file txts stand
# unchanged (her ruling: keep the per-files).
# ====================================================================

import json
import re
from pathlib import Path

FILE = "ai_delivery.json"


def _read_json(path, default):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else default


def load(out_dir):
    return _read_json(
        Path(out_dir) / FILE,
        {"basis": {}, "reports": [], "reportless_files": [],
         "counts": {}})


def _write(out_dir, delivery):
    for e in delivery["reports"]:
        e["files"] = sorted(set(e.get("files", [])))
        e["terms"] = sorted(e.get("terms", []),
                            key=lambda t: t["node_id"])
    for e in delivery["reportless_files"]:
        e["terms"] = sorted(e.get("terms", []),
                            key=lambda t: t["node_id"])
    delivery["reports"].sort(key=lambda e: e["report"])
    delivery["reportless_files"].sort(key=lambda e: e["file"])
    (Path(out_dir) / FILE).write_text(
        json.dumps(delivery, indent=1))
    return delivery


def _normalize(name):
    """D5 — lowercase, punctuation stripped, plurals folded."""
    toks = re.sub(r"[^a-z0-9 ]", " ", name.lower()).split()
    return " ".join(t[:-1] if len(t) > 1 and t.endswith("s") else t
                    for t in toks)


def _report_entry(delivery, report, files=()):
    for e in delivery["reports"]:
        if e["report"] == report:
            e["files"] = sorted(set(e.get("files", []))
                                | set(files))
            return e
    e = {"report": report, "files": sorted(files), "terms": []}
    delivery["reports"].append(e)
    return e


def _file_entry(delivery, fname):
    for e in delivery["reportless_files"]:
        if e["file"] == fname:
            return e
    e = {"file": fname, "terms": []}
    delivery["reportless_files"].append(e)
    return e


def _rows(delivery):
    """[(parent_key, row)] in deterministic order."""
    out = []
    for e in sorted(delivery["reports"], key=lambda e: e["report"]):
        for t in sorted(e.get("terms", []),
                        key=lambda t: t["node_id"]):
            out.append((e["report"], t))
    for e in sorted(delivery["reportless_files"],
                    key=lambda e: e["file"]):
        for t in sorted(e.get("terms", []),
                        key=lambda t: t["node_id"]):
            out.append((e["file"], t))
    return out


def _recount(delivery):
    rows = _rows(delivery)
    # THE UNIQUENESS LAW, global (collision = derived field)
    seen = {}
    for _, t in sorted(rows, key=lambda x: (x[1]["node_id"], x[0])):
        if not t.get("bt_name"):
            continue
        key = _normalize(t["bt_name"])
        first = seen.setdefault(key, t)
        t["name_collision"] = (first["bt_name"]
                               if first is not t
                               and first["node_id"] != t["node_id"]
                               else None)
    skipped = delivery["counts"].get("09", {}).get("skipped", [])
    concepts = {t["node_id"] for _, t in rows}
    counts = {
        "scopes_total": len(concepts) + len(skipped),
        "plumbing_skipped": len(skipped),
        "concepts": len(concepts),
        "report_rows": sum(len(e.get("terms", []))
                           for e in delivery["reports"]),
        "reportless_rows": sum(len(e.get("terms", []))
                               for e in delivery["reportless_files"]),
        "blessed": sum(1 for _, t in rows
                       if t.get("bt_name_status") == "blessed"),
        "proposed": sum(1 for _, t in rows
                        if t.get("bt_name_status") == "proposed"),
        "skipped": skipped,
    }
    if counts["scopes_total"] != (counts["plumbing_skipped"]
                                  + counts["concepts"]) \
            or (counts["report_rows"] + counts["reportless_rows"]
                != len(rows)):
        raise ValueError(f"red counts.09 — does not ship: {counts}")
    delivery["counts"]["09"] = counts


def update_terms(out_dir, placed, skipped, basis, files_in_run):
    """The 09 key. placed = [(report_or_None, file, row)]."""
    delivery = load(out_dir)
    delivery["basis"]["07"] = basis
    run = set(files_in_run)
    for e in delivery["reports"]:
        if any(f.removesuffix(".sql") in run
               for f in e.get("files", [])):
            e["terms"] = []
    for e in delivery["reportless_files"]:
        if e["file"] in run:
            e["terms"] = []
    for report, fname, row in placed:
        if report:
            _report_entry(delivery, report,
                          [fname + ".sql"])["terms"].append(row)
        else:
            _file_entry(delivery, fname)["terms"].append(row)
    kept = [s for s in
            delivery["counts"].get("09", {}).get("skipped", [])
            if s["node_id"].split("::")[1] not in run]
    merged = {s["node_id"]: s for s in kept + list(skipped)}
    delivery["counts"].setdefault("09", {})["skipped"] = sorted(
        merged.values(), key=lambda s: s["node_id"])
    _recount(delivery)
    return _write(out_dir, delivery)


def assemble(out_dir, dir07, dir08, dir06):
    """The 08 + 07 keys; terms preserved by entry key."""
    dir07, dir08, dir06 = Path(dir07), Path(dir08), Path(dir06)
    delivery = load(out_dir)
    old_report_terms = {e["report"]: e.get("terms", [])
                        for e in delivery["reports"]}
    old_file_terms = {e["file"]: e.get("terms", [])
                      for e in delivery["reportless_files"]}
    six = _read_json(dir06 / "06_description_sheet.json", [])
    floors = {r["node_id"].split("::")[1]: r["sentence"]
              for r in six if r["grain"] == "file"}
    seven = _read_json(dir07 / "07_business_sheet.json", [])
    cards = {r["node_id"].split("::")[1]: r["audience_text"]
             for r in seven
             if r["grain"] == "file"
             and r.get("status") in ("gate_passed", "blessed")}

    def _desc(stem):
        if stem in cards:
            return {"text": cards[stem], "voice": "business",
                    "status": "gate_passed"}
        return {"text": floors.get(stem,
                                   "(no description rendered)"),
                "voice": "technical", "status": "floor"}

    reports = _read_json(dir08 / "08_pbi_reports.json", [])
    delivery["reports"] = []
    tied = set()
    for r in sorted(reports, key=lambda r: r["name"]):
        stems = [f.removesuffix(".sql") for f in r["executes"]]
        tied.update(stems)
        descs = [_desc(s) for s in stems]
        if len(descs) == 1:
            d = descs[0]
        else:  # one block per file; business only when all are
            d = {"text": "\n\n".join(
                    f"[{s}]\n{x['text']}"
                    for s, x in zip(stems, descs)),
                 "voice": ("business" if all(
                     x["voice"] == "business" for x in descs)
                     else "technical"),
                 "status": "assembled"}
        delivery["reports"].append(
            {"report": r["name"], "files": sorted(r["executes"]),
             "description": d,
             "terms": old_report_terms.get(r["name"], [])})
    delivery["reportless_files"] = [
        {"file": stem, "description": _desc(stem),
         "terms": old_file_terms.get(stem, [])}
        for stem in sorted(set(floors) - tied)]
    if "09" in delivery["counts"]:
        _recount(delivery)
    return _write(out_dir, delivery)


def bless_term(out_dir, dir07, node_id, report, ruling):
    """HER HAND ONLY (the ratify clause) — recorded verbatim."""
    delivery = load(out_dir)
    row = next((t for key, t in _rows(delivery)
                if t["node_id"] == node_id and key == report),
               None)
    if row is None:
        raise ValueError(f"no term row ({node_id}, {report})")
    if row["status"] != "gate_passed":
        raise ValueError("a failed card must not bless (D3)")
    if row.get("name_collision") is not None:
        raise ValueError("a collided row must not bless (D5); "
                         "collides with: " + row["name_collision"])
    reg_path = Path(dir07) / "07_blessing_registry.json"
    registry = _read_json(reg_path, {})
    terms = [t for t in registry.get("terms", [])
             if (t["node_id"], t["report"]) != (node_id, report)]
    terms.append({"node_id": node_id, "report": report,
                  "bt_name": row["bt_name"], "ruling": ruling})
    registry["terms"] = sorted(
        terms, key=lambda t: (t["node_id"], t["report"]))
    reg_path.write_text(json.dumps(registry, indent=1))
    row["bt_name_status"] = "blessed"
    row["blessing"] = ruling
    _recount(delivery)
    return _write(out_dir, delivery)
