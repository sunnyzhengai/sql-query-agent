"""M7 — THE BINDINGS EXTRACTOR (Brief_M7_Consumption_Governance,
Q1 "a" + M7-A, Sunny's "approved" 2026-09-17).

Reads the repo's *.SemanticModel folders (TMDL — deterministic
column-level truth, the DevOps-lineage fact) and writes each
estate's pbi_snapshot/reports.json with `bound_fields`: per
report, per EXEC'd proc, the columns the semantic model IMPORTS
(`sourceColumn` rows). Model-grain by ruling (Q4 "a"); the
LocalDateTable_*/DateTableTemplate_* plumbing is excluded
(M7-A); calculated columns (DAX) are the REPORT-LAYER
EXTRACTION's territory — the named future brief.

Per-proc keying refines M7-A's flat list in service of the Q3
ruling: concatenation composes per executed proc, so the fields
must know their proc. Presented at checkpoint 1.

The sepsis estate's reports.json is AUTHORED here (the ruled
2026-09-08 mapping: every proc feeds a PBI — the real dashboard
where the TMDL maps, a synthetic shell per remaining proc; the
reports may be fake, the mapping is real).

Deterministic, re-runnable, free.
Usage: python3.11 devtools/pbi_extract.py
"""
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
ESTATES = REPO / "AIVIA_Product" / "estates"
PLUMBING = ("LocalDateTable_", "DateTableTemplate_")


def read_model(model_dir: pathlib.Path):
    """One SemanticModel -> {table_name: {"exec": proc, "columns":
    [sourceColumn...]}} — imported columns only."""
    out = {}
    for tf in sorted((model_dir / "definition" / "tables").glob("*.tmdl")):
        if tf.name.startswith(PLUMBING):
            continue
        text = tf.read_text()
        cols = re.findall(r"^\t\tsourceColumn: (.+)$", text, re.M)
        m = re.search(r'EXEC\s+([\w.\[\]]+)', text)
        out[tf.stem] = {"exec": m.group(1) if m else None,
                        "columns": [c.strip() for c in cols]}
    return out


def estate_files(estate: pathlib.Path):
    """Relative .sql paths of the estate's corpus."""
    snap = estate / "estate_snapshot"
    return sorted(str(p.relative_to(snap)).replace("\\", "/")
                  for p in snap.rglob("*.sql"))


def resolve(exec_name, files):
    """EXEC reporting.USP_ED_Sepsis -> reporting/USP_ED_SEPSIS.sql
    (case-insensitive; unresolved names return themselves so the
    counted-unresolved list stays honest)."""
    if not exec_name:
        return None
    tail = exec_name.replace("[", "").replace("]", "")
    parts = tail.split(".")
    want = ("/".join(parts[-2:]) + ".sql").lower()
    for f in files:
        if f.lower() == want or f.lower().endswith("/" + want):
            return f
    return "/".join(parts[-2:]) + ".sql"


def build_reports(estate: pathlib.Path):
    files = estate_files(estate)
    fileset = {f.lower(): f for f in files}
    reports = []
    covered = set()
    for model_dir in sorted(REPO.glob("*.SemanticModel")):
        tables = read_model(model_dir)
        executes, bound = [], {}
        for tname, t in sorted(tables.items()):
            target = resolve(t["exec"], files)
            if target is None:
                continue
            if target not in executes:
                executes.append(target)
            bound.setdefault(target, [])
            for c in t["columns"]:
                if c not in bound[target]:
                    bound[target].append(c)
        resolved = [e for e in executes if e.lower() in fileset]
        if not resolved:
            continue  # this model belongs to another corpus
        covered.update(resolved)
        name = model_dir.name.removesuffix(".SemanticModel")
        reports.append({
            "name": name,
            "description": f"Power BI dashboard: {name}.",
            "executes": executes,
            "bound_fields": bound,
            "source": (f"real-tmdl ({model_dir.name}; EXEC names "
                       "mapped to the corpus; bound_fields = the "
                       "model's imported sourceColumns per proc, "
                       "date plumbing excluded — M7-A)"),
        })
    # the 2026-09-08 mapping: every remaining proc feeds a shell
    for f in files:
        if f in covered:
            continue
        base = f.rsplit("/", 1)[-1].removesuffix(".sql")
        reports.append({
            "name": f"{base} Report",
            "description": f"Report shell for {base}.",
            "executes": [f],
            "bound_fields": {},  # a shell binds nothing — the
            # report definition falls back to the whole catch-all
            "source": "synthetic shell (the 2026-09-08 mapping: "
                      "every proc feeds a PBI; the report may be "
                      "fake, the mapping is real)",
        })
    return reports


def main():
    for estate_name in ("ed_sepsis_dev", "sepsis"):
        estate = ESTATES / estate_name
        reports = build_reports(estate)
        out = estate / "pbi_snapshot" / "reports.json"
        # preserve the dev estate's curated description on the
        # real dashboard (the shell text is estate data already)
        if out.is_file():
            old = {r["name"]: r for r in
                   json.loads(out.read_text())}
            for r in reports:
                if r["name"] in old and old[r["name"]].get(
                        "description"):
                    r["description"] = old[r["name"]]["description"]
        out.write_text(json.dumps(reports, indent=1))
        real = sum(1 for r in reports
                   if r["source"].startswith("real-tmdl"))
        print(f"{estate_name}: {len(reports)} reports "
              f"({real} real-tmdl, {len(reports) - real} shells) "
              f"-> {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
