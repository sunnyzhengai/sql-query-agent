# =====================================================================
# pbi_lineage.py — PHASE 08: the PBI-report -> SQL-file link
#
# PSEUDO CODE for Sunny's review, 2026-10-04. No real code lands
# until her stamp on the 08 design doc's D1-D7 and this pseudo;
# then the locks land RED (verbatim pytest), then the code.
#
# The law: 08_pbi_lineage.md (D1-D7) + its data contract.
# Prior art consulted, never re-derived: devtools/pbi_extract.py
# (the proven EXEC pattern + resolve law); divergences named in
# D1 (two new binding kinds) and D3 (no synthetic shells).
# Deterministic end to end: stdlib only, no LLM, no network.
# =====================================================================

# ---------------------------------------------------------------------
# P1. READ — read_models(tmdl_root) -> {model_name: [table rows]}
# ---------------------------------------------------------------------
# - glob <tmdl_root>/*.SemanticModel/definition/tables/*.tmdl
# - skip LocalDateTable_* / DateTableTemplate_* (D4), COUNTED as
#   plumbing_skipped
# - per table file, extract (D1):
#     sourceColumn rows:  ^\t\tsourceColumn: (.+)$   (the proven
#                         regex; tabs per the TMDL emitter)
#     exec binding:       EXEC\s+([\w.\[\]]+)          -> kind exec
#     entity binding:     ^\s*entityName: (.+)$        -> kind entity
#     source binding:     the import-partition M source object —
#                         [Name="X"] / [Item="X"] pairs and the
#                         schema-qualified Sql.Database form
#                                                      -> kind source
#   one table may carry ONE binding (first match by kind order
#   exec > entity > source); a table with none is COUNTED
#   (unbound class), never guessed.
#
# ---------------------------------------------------------------------
# P2. RESOLVE — resolve(raw_target, corpus) -> sql_file | None (D2)
# ---------------------------------------------------------------------
# - corpus = sorted *.sql names under the 01 folder (read once)
# - strip brackets, split on dots, take the last two parts,
#   match case-insensitive as "<schema>/<name>.sql" OR
#   "<name>.sql" (the 01 folder is flat; schema folds into the
#   name match) — the prior resolve law, adapted to 01's layout
# - a miss returns None; the caller writes the unresolved row.
#
# ---------------------------------------------------------------------
# P3. COMPOSE — build08(tmdl_root, dir01, out08) -> reports
# ---------------------------------------------------------------------
# - per model: bindings -> executes (deduped, ordered) +
#   bound_fields {sql_file: [sourceColumns deduped]} + the full
#   bindings evidence list (contract shape)
# - a model resolving to ZERO corpus files is skipped as
#   another-corpus, COUNTED (D3 spirit: only real, only ours)
# - NO shells (D3): corpus files no model touches land in the
#   ledger's unconsumed_sql
# - write 08_pbi_reports.json + 08_lineage_ledger.json; print
#   the conservation equation (bindings == resolved + unresolved)
#
# ---------------------------------------------------------------------
# P4. THE LOCKS (red first, synthetic fixtures only — invented
#     names, never customer text):
# ---------------------------------------------------------------------
# L1 exec binding resolves (the proven path, fixture proc)
# L2 entity binding resolves (DirectLake fixture)
# L3 source binding resolves (view-fed import fixture)
# L4 unresolved binding lands a COUNTED ledger row, build green
# L5 plumbing tables skipped and counted
# L6 no shells: an untouched corpus file -> unconsumed_sql,
#    never a minted report row
# L7 conservation: bindings == resolved + unresolved, and the
#    build is byte-deterministic on a rerun
# =====================================================================

# =====================================================================
# THE CODE (landed 2026-10-04 after Sunny's stamp on D1-D8 and the
# pseudo; the seven locks above it were RED first, verbatim).
# =====================================================================

import json
import re
from pathlib import Path

PLUMBING = ("LocalDateTable_", "DateTableTemplate_")
_SOURCECOL = re.compile(r"^\s*sourceColumn:\s*(.+)$", re.M)
_EXEC = re.compile(r"EXEC\s+([\w.\[\]]+)")
_ENTITY = re.compile(r"^\s*entityName:\s*(.+)$", re.M)
_SCHEMA = re.compile(r'Schema\s*=\s*"([^"]+)"')
_ITEM = re.compile(r'(?:Item|Name)\s*=\s*"([^"]+)"')


def _binding_of(text):
    """ONE binding per table, kind order exec > entity > source
    (the stamped pseudo's judgment call); None = unbound."""
    m = _EXEC.search(text)
    if m:
        return "exec", m.group(1)
    m = _ENTITY.search(text)
    if m:
        return "entity", m.group(1).strip()
    item = _ITEM.search(text)
    if item:
        sch = _SCHEMA.search(text)
        raw = (f"{sch.group(1)}.{item.group(1)}" if sch
               else item.group(1))
        return "source", raw
    return None, None


def read_models(tmdl_root):
    """{model_name: [ {table, kind, raw, columns} ]} + the
    plumbing count. Deterministic order throughout (D4, P1)."""
    models, plumbing = {}, 0
    for mdir in sorted(Path(tmdl_root).glob("*.SemanticModel")):
        rows = []
        tdir = mdir / "definition" / "tables"
        for tf in sorted(tdir.glob("*.tmdl")):
            if tf.name.startswith(PLUMBING):
                plumbing += 1
                continue
            text = tf.read_text()
            kind, raw = _binding_of(text)
            rows.append({
                "table": tf.stem,
                "kind": kind,
                "raw": raw,
                "columns": [c.strip() for c in
                            _SOURCECOL.findall(text)],
            })
        models[mdir.name.removesuffix(".SemanticModel")] = rows
    return models, plumbing


def resolve(raw_target, corpus_files):
    """D2: brackets stripped, last name part, case-insensitive
    into the flat 01 corpus; a miss returns None, the caller
    writes the counted row — never a guess."""
    if not raw_target:
        return None
    tail = raw_target.replace("[", "").replace("]", "")
    name = tail.split(".")[-1].strip()
    want = (name + ".sql").lower()
    for f in corpus_files:
        if f.lower() == want:
            return f
    return None


def build08(tmdl_root, dir01, out08):
    """The phase door (P3): reports + ledger, deterministic,
    no shells (D3), everything counted (D2)."""
    out = Path(out08)
    corpus = sorted(p.name for p in Path(dir01).glob("*.sql"))
    models, plumbing = read_models(tmdl_root)

    reports, unresolved = [], []
    tables_read = bindings = resolved_n = 0
    consumed = set()
    for mname, rows in models.items():
        executes, bound, brow = [], {}, []
        for r in rows:
            tables_read += 1
            if r["kind"] is None:
                continue
            bindings += 1
            target = resolve(r["raw"], corpus)
            brow.append({"table": r["table"],
                         "binding_kind": r["kind"],
                         "raw_target": r["raw"],
                         "resolved": target})
            if target is None:
                unresolved.append({"model": mname,
                                   "table": r["table"],
                                   "binding_kind": r["kind"],
                                   "raw_target": r["raw"]})
                continue
            resolved_n += 1
            if target not in executes:
                executes.append(target)
            bound.setdefault(target, [])
            for c in r["columns"]:
                if c not in bound[target]:
                    bound[target].append(c)
        if not executes:
            continue  # another corpus's model (D3 spirit)
        consumed.update(executes)
        reports.append({
            "name": mname,
            "executes": executes,
            "bound_fields": bound,
            "bindings": brow,
            "source": f"tmdl ({mname}.SemanticModel; "
                      "plumbing excluded)",
        })

    ledger = {
        "unresolved": unresolved,
        "unconsumed_sql": [f for f in corpus
                           if f not in consumed],
        "counts": {"models": len(models),
                   "tables_read": tables_read,
                   "plumbing_skipped": plumbing,
                   "bindings": bindings,
                   "resolved": resolved_n,
                   "unresolved": len(unresolved)},
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "08_pbi_reports.json").write_text(
        json.dumps(reports, indent=1))
    (out / "08_lineage_ledger.json").write_text(
        json.dumps(ledger, indent=1))
    c = ledger["counts"]
    print(f"08 lineage: {len(reports)} report(s); conservation "
          f"{c['bindings']} bindings == {c['resolved']} resolved "
          f"+ {c['unresolved']} unresolved")
    return reports
