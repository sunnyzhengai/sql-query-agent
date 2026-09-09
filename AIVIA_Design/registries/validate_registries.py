"""Registry validator — the embryo of binding mechanisms a and b.

(a) stamp discipline: every registry carries a complete stamp block;
    LIVE since the ratification pass (2026-09-05) — every registry
    version must match its [registry stamp: ...] marker in the doc,
    and only ratified registries may exist here.
(b) rule-to-check closure: every rule row in every Rules_to_Checks
    sheet names at least one check — "a rule with no check is a hope"
    as arithmetic. The explicit design-review exception is honored only
    when declared in the row itself.

Plus cross-registry consistency: each CHECK-* name defined in exactly
one registry; predicate roles closed against the Roles sheet;
denominator dispositions in closed vocab; the logic layer's expression
kind list identical to the kind library's.

Usage: python3 AIVIA_Design/registries/validate_registries.py
"""
import glob
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
V, OK, NR = [], [], []


def rule(name, violations):
    if violations:
        V.extend((name, d) for d in violations)
    else:
        OK.append(name)


regs = {}
for path in sorted(glob.glob(os.path.join(BASE, "*.json"))):
    regs[os.path.basename(path)[:-5]] = json.load(open(path))

# mechanism a: stamp blocks complete
STAMP_FIELDS = {"version", "doc_section", "doc_stamp", "ratified",
                "converted_on", "converted_from"}
rule("RG-A1 stamp block complete",
     [f"{n}: missing {STAMP_FIELDS - set(r.get('stamp', {}))}"
      for n, r in regs.items() if STAMP_FIELDS - set(r.get("stamp", {}))])

# mechanism a LIVE (ratification pass done 2026-09-05): every registry's
# version must appear as a [registry stamp: ...] marker in the doc
doc_text = open(os.path.join(os.path.dirname(BASE),
                             "Design_Graph_Engine.md")).read()
doc_stamps = {}
for block in re.findall(r"\[registry stamps?: ([^\]]+)\]", doc_text):
    for part in block.split("·"):
        name, _, ver = part.strip().rpartition(" v")
        doc_stamps[name] = ver
rule("RG-A2 doc-stamp compare (same-breath rule as mechanics)",
     [f"{n}: registry v{r['stamp']['version']} vs doc "
      f"{'v' + doc_stamps[n] if n in doc_stamps else 'UNSTAMPED'}"
      for n, r in regs.items()
      if doc_stamps.get(n) != r["stamp"]["version"]])
rule("RG-A3 ratified registries only",
     [f"{n}: ratified={r['stamp']['ratified']}" for n, r in regs.items()
      if r["stamp"]["ratified"] is not True])

# mechanism b: rule-to-check closure
bad = []
for n, r in regs.items():
    for sheet, rows in r["sheets"].items():
        if "Rules_to_Checks" not in sheet and "Stages_and_Checks" not in sheet:
            continue
        for row in rows:
            checks = row.get("Named check(s)") or row.get("Checks") or ""
            declared_exempt = "no runtime check" in checks
            if not checks.strip():
                bad.append(f"{n}/{sheet}: rule "
                           f"'{list(row.values())[0][:40]}' names no check")
            elif declared_exempt and "design-review" not in checks:
                bad.append(f"{n}/{sheet}: undeclared exemption")
rule("RG-B1 rule-to-check closure (a rule with no check is a hope)", bad)

# each CHECK-* defined in exactly one registry
CHECK = re.compile(r"CHECK-[A-Z0-9]+-\d+[a-z]?")
defined = {}
for n, r in regs.items():
    for sheet, rows in r["sheets"].items():
        if "Rules_to_Checks" not in sheet:
            continue
        for row in rows:
            for c in CHECK.findall(row.get("Named check(s)", "")):
                defined.setdefault(c, []).append(n)
rule("RG-B2 check names defined once",
     [f"{c} defined in {ns}" for c, ns in defined.items() if len(ns) > 1])

# kind library: predicate roles closed against the Roles sheet
kl = regs["kg2_kind_library"]["sheets"]
role_vocab = set()
for row in kl["Roles"]:
    if row["Role"].startswith("("):
        continue
    for part in row["Role"].split("/"):
        role_vocab.add(part.strip())
bad = []
for row in kl["Predicate_Kinds"]:
    if row["Kind"].startswith("("):
        continue
    for raw in re.sub(r"\([^)]*\)", "", row.get("Roles", "")).split(","):
        tok = raw.strip().rstrip("?")
        if tok and tok not in role_vocab:
            bad.append(f"{row['Kind']}: role '{tok}' not in Roles sheet")
rule("RG-C1 predicate roles closed against Roles sheet (RG-1 ruled: "
     "operators/quantifiers are properties)", bad)

# v1 flag column: every catalog row flagged, closed vocab
rule("RG-C4 lens catalog v1 flags total and closed",
     [f"{row['Lens']}: '{row.get('v1', '')}'"
      for row in regs["lenses"]["sheets"]["Catalog_v1"]
      if not (row.get("v1") == "yes" or
              str(row.get("v1", "")).startswith("deferred ("))])

# denominator dispositions in closed vocab
DISP = ("mapped", "DEFERRED", "RED BUILD", "permanent counted gap")
rule("RG-C2 denominator dispositions closed",
     [f"{row['ScriptDom type']}: '{row['Disposition']}'"
      for row in kl["TSQL_Denominator"]
      if not row["Disposition"].startswith(DISP)])

# logic layer expression kinds == kind library expression kinds
lib_kinds = {row["Kind"] for row in kl["Expression_Kinds"]}
expr_row = next(r for r in regs["kg2_logic"]["sheets"]["Node_Types"]
                if r["Kind"] == "expression")
logic_kinds = {t.strip() for t in
               expr_row["Properties"].removeprefix("kind:").split("|")}
rule("RG-C3 expression kinds identical across KG2 registries",
     [f"symmetric difference: {sorted(lib_kinds ^ logic_kinds)}"]
     if lib_kinds != logic_kinds else [])

print(f"PASSED: {len(OK)} rules")
for name in OK:
    print(f"  ok {name}")
if V:
    print(f"VIOLATIONS: {len(V)}")
    for name, d in V:
        print(f"  !! {name}: {d}")
else:
    print("VIOLATIONS: none")
for note in NR:
    print(f"NOT-RUNNABLE: {note}")
sys.exit(1 if V else 0)
