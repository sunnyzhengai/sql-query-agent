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
#   rebuilds reports[] from 08_pbi_lineage_output.json (absent file ->
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

# ==== PSEUDO — 0.7.0 THE DELIVERED-GOODS RULING (2026-10-08; ====
# the 09 contract's amendment + D14; AWAITING SUNNY'S APPROVAL;
# red tests before code; the code follows).
#
#   THE NAME:
#   1. FILE -> "12_ai_delivery_output.json". THE MIGRATION READ:
#      load() reads the new name first; absent, the old
#      ai_delivery.json once (a pre-rename tenant's terms and
#      blessings survive); _write() always writes the new name.
#
#   MEMBERSHIP = THE LEDGER (assemble):
#   2. assemble(out_dir, dir07, dir08, dir06, described=None) —
#      described = the set of file stems that had their paid
#      turn. None -> assemble reads the ledger itself from
#      out_dir (new name, then old).
#      NO LEDGER FILE AT ALL -> legacy mode: membership
#      unfiltered (the home/repo flows have no ledger; work
#      always has one — describe() records before assembling).
#      [flagged for Sunny: this keeps the home estate green
#      without a second delivery law — the work path always
#      filters.]
#   3. reportless_files[]: only described stems.
#      reports[]: a report enters when ANY of its stems is
#      described (her ruling) and carries two lists —
#      files_described[] + files_waiting[] (full file names,
#      same form as files[]). files_waiting empty == complete.
#      Description blocks cover the DESCRIBED files only; voice
#      business only when every described file carries a card.
#      A report with zero described files appears NOWHERE.
#   4. THE FAILURE STATUS (honest processed-but-failed): a
#      described stem whose 07 row exists but is not
#      gate_passed/blessed renders floor text with status
#      "gate_failed" (today it hides as "floor"); a described
#      stem with no 07 row at all stays status "floor".
#
#   UNCHANGED: update_terms (runs only over described files by
#   construction), bless_term, _recount + the equations, the
#   determinism laws (sorted, indent=1, no timestamps).
#
#   THE LOCKS (red before code, test_09 the shape owner):
#   5. waiting file absent from reportless_files; half-described
#      report present with correct lists; fully-described report
#      files_waiting == []; zero-described report absent;
#      gate_failed status rides out; no-ledger legacy mode
#      unfiltered; load() migration (old-name delivery read,
#      new name written).
# ====================================================================

# ==== PSEUDO — 0.8.0 AWAITING_HUMAN IN THE DELIVERY (D15, ====
# ruled 2026-10-08 evening; the 09 contract's amendment;
# AWAITING SUNNY'S APPROVAL; red tests before code):
#   1. assemble's _desc: a described stem whose 07 row is
#      awaiting_human ships NO business text — description =
#      {"text": "", "voice": "none", "status":
#      "awaiting_human"}; the entry gains "questions": the 07
#      row's questions verbatim. The 2026-10-08-morning
#      gate_failed/floor passthrough is SUPERSEDED (her
#      evening reopen: a fallback is not a candidate).
#   2. The txt twin renders it honestly: "AWAITING YOUR
#      ANSWER on: <the questions>" — never a technical text
#      in the business slot.
#   3. The Collibra publish notebook skips awaiting_human
#      entries (doc edit, same landing).
# ===============================================================

import json
import re
from pathlib import Path

FILE = "12_ai_delivery_output.json"
FILE_OLD = "ai_delivery.json"      # pre-0.7.0 tenants
LEDGERS = ("10_corpus_ledger_output.json",
           "10_corpus_ledger.json")


def _read_json(path, default):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else default


def load(out_dir):
    """THE MIGRATION READ (2026-10-08): new name first; a
    pre-rename delivery (terms, blessings) is honored once —
    every write lands the new name."""
    for name in (FILE, FILE_OLD):
        p = Path(out_dir) / name
        if p.exists():
            return json.loads(p.read_text())
    return {"basis": {}, "reports": [], "reportless_files": [],
            "counts": {}}


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


def _described_stems(out_dir):
    """The ledger's stems, or None when no ledger exists at all
    — legacy mode: the home estate has no ledger; a work tenant
    always does (describe() records before assembling)."""
    for name in LEDGERS:
        p = Path(out_dir) / name
        if p.exists():
            return {Path(n).stem for n in
                    json.loads(p.read_text()).get("hashes", {})}
    return None


def assemble(out_dir, dir07, dir08, dir06, described=None):
    """The 08 + 07 keys; terms preserved by entry key.
    THE DELIVERED-GOODS RULING (2026-10-08): membership = the
    ledger (described; None = read it from out_dir). A waiting
    file appears NOWHERE; a report enters on its first described
    file with files_described[] + files_waiting[] (empty waiting
    == complete); description blocks cover described files only;
    a zero-described report is absent. No ledger at all = legacy
    unfiltered."""
    dir07, dir08, dir06 = Path(dir07), Path(dir08), Path(dir06)
    if described is None:
        described = _described_stems(out_dir)
    def member(stem):
        return described is None or stem in described
    delivery = load(out_dir)
    old_report_terms = {e["report"]: e.get("terms", [])
                        for e in delivery["reports"]}
    old_file_terms = {e["file"]: e.get("terms", [])
                      for e in delivery["reportless_files"]}
    six = _read_json(dir06 / "06_technical_descriptions_output.json", [])
    floors = {r["node_id"].split("::")[1]: r["sentence"]
              for r in six if r["grain"] == "file"}
    seven = _read_json(dir07 / "07_business_descriptions_output.json", [])
    cards = {r["node_id"].split("::")[1]: r["audience_text"]
             for r in seven
             if r["grain"] == "file"
             and r.get("status") in ("gate_passed", "blessed")}
    # processed-but-failed is honest (2026-10-08): a described
    # file whose card missed the gate says so, never "floor"
    failed = {r["node_id"].split("::")[1]: r["status"]
              for r in seven
              if r["grain"] == "file"
              and r.get("status") not in ("gate_passed",
                                          "blessed", None)}

    def _desc(stem):
        if stem in cards:
            return {"text": cards[stem], "voice": "business",
                    "status": "gate_passed"}
        return {"text": floors.get(stem,
                                   "(no description rendered)"),
                "voice": "technical",
                "status": failed.get(stem, "floor")}

    reports = _read_json(dir08 / "08_pbi_lineage_output.json", [])
    delivery["reports"] = []
    tied = set()
    for r in sorted(reports, key=lambda r: r["name"]):
        stems = [f.removesuffix(".sql") for f in r["executes"]]
        have = [s for s in stems if member(s)]
        if not have:
            continue      # zero described: not yet delivered
        tied.update(stems)
        descs = [_desc(s) for s in have]
        if len(descs) == 1:
            d = descs[0]
        else:  # one block per file; business only when all are
            d = {"text": "\n\n".join(
                    f"[{s}]\n{x['text']}"
                    for s, x in zip(have, descs)),
                 "voice": ("business" if all(
                     x["voice"] == "business" for x in descs)
                     else "technical"),
                 "status": "assembled"}
        delivery["reports"].append(
            {"report": r["name"], "files": sorted(r["executes"]),
             "files_described": sorted(s + ".sql" for s in have),
             "files_waiting": sorted(s + ".sql" for s in stems
                                     if s not in have),
             "description": d,
             "terms": old_report_terms.get(r["name"], [])})
    delivery["reportless_files"] = [
        {"file": stem, "description": _desc(stem),
         "terms": old_file_terms.get(stem, [])}
        for stem in sorted(set(floors) - tied)
        if member(stem)]
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
    reg_path = Path(dir07) / "07_business_descriptions_blessings_output.json"
    registry = _read_json(reg_path, None)
    if registry is None:   # the migration read (2026-10-08):
        # honor a pre-rename registry once; the write below
        # lands the new name — no blessing is ever lost
        registry = _read_json(
            Path(dir07) / "07_blessing_registry.json", {})
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
