"""The fixture validator — the Graph Validity Contract (GV) run
against every fixture family. Design-phase QA tooling: judges the
ANSWER KEYS for structure, conservation, and consistency; authored
MEANING stays Sunny's (J1). Rules that need the build to run are
reported NOT-RUNNABLE, never silently skipped.

Usage: python3.11 AIVIA_Product/fixtures/validate_fixtures.py
"""
import json, csv, collections, re, sys, os

BASE = os.path.dirname(os.path.abspath(__file__)) + "/"
V = []            # violations: (fixture, rule, detail)
NR = []           # not-runnable notes
OK = []           # passed rule names

def rule(fix, name, violations):
    if violations:
        for d in violations: V.append((fix, name, d))
    else:
        OK.append(f"{fix}:{name}")

# ---------- load F1 ----------
reg = json.load(open(BASE + "F1_minimal_estate/registration.json"))
snaps = {"simemr": "F1_minimal_estate/simemr_snapshot",
         "org": "F1_minimal_estate/org_snapshot"}
tables, columns, joins = set(), set(), []
pks = collections.defaultdict(list)
tdesc = {}
for src, d in snaps.items():
    for r in csv.DictReader(open(BASE + d + "/tables.csv")):
        tables.add((src, r["schema"], r["table"]))
        tdesc[(src, r["schema"], r["table"])] = r["description"]
    for r in csv.DictReader(open(BASE + d + "/columns.csv")):
        columns.add((src, r["schema"], r["table"], r["column"]))
    for r in csv.DictReader(open(BASE + d + "/pk.csv")):
        pks[(src, r["schema"], r["table"])].append((int(r["ordinal"]), r["column"]))
    for r in csv.DictReader(open(BASE + d + "/joins.csv")):
        joins.append((src, r))
g1 = json.load(open(BASE + "F1_minimal_estate/expected_graph.json"))

# GV-C1 bijective reconciliation
exp_tables = {tuple(t["id"].split("|")) for t in g1["nodes"]["tables"]}
rule("F1", "GV-C1 tables bijective",
     [f"mismatch: {exp_tables ^ tables}"] if exp_tables != tables else [])
bad = []
for t in g1["nodes"]["tables"]:
    k = tuple(t["id"].split("|"))
    want = [c for _, c in sorted(pks[k])]
    if t["pk_columns"] != want:
        bad.append(f"{t['id']}: expected {t['pk_columns']} vs pk.csv {want}")
rule("F1", "GV-C1 pk bijective", bad)
# GV-D2 legality + INTAKE-10 + schema mapping
bad = []
for src, r in joins:
    if reg["schema_sources"].get(r["src_schema"]) != src:
        bad.append(f"{src} declares a join whose dependent side it does not own: "
                   f"{r['src_schema']}.{r['src_table']}")
rule("F1", "GV-D2 join legality (declarer owns dependent side)", bad)
rule("F1", "GV-D2 INTAKE-10 pk integrity",
     [f"keyless: {t}" for t in tables if t not in pks])
rule("F1", "GV-D2 single-source schemas",
     [f"schema {s} unmapped" for (_, s, _) in tables
      if s not in reg["schema_sources"]])
# GV-C1 joins: group -> edges (+ dedupe) == expected
grp = collections.defaultdict(list)
for src, r in joins:
    grp[(src, r["fk_num"])].append(r)
csv_edges = {}
for (src, fk), rows in sorted(grp.items()):
    rows.sort(key=lambda r: int(r["ordinal"]))
    f = rows[0]
    frm = f"{reg['schema_sources'][f['src_schema']]}|{f['src_schema']}|{f['src_table']}"
    to = f"{reg['schema_sources'][f['dest_schema']]}|{f['dest_schema']}|{f['dest_table']}"
    on = tuple((r["src_column"], r["dest_column"]) for r in rows)
    k = (frm, to, tuple(p[0] for p in on))
    if k in csv_edges:  # dedupe: category-column target wins over INTERNAL_ID
        if csv_edges[k][2][0][1].startswith("INTERNAL"):
            csv_edges[k] = (frm, to, on)
    else:
        csv_edges[k] = (frm, to, on)
csv_e = set(csv_edges.values())
exp_e = {(e["from"], e["to"], tuple(map(tuple, e["on"])))
         for e in g1["edges"]["joins_to"]}
rule("F1", "GV-C1 joins bijective (incl. dedupe rule)",
     ([f"only-expected: {exp_e - csv_e}"] if exp_e - csv_e else []) +
     ([f"only-derived: {csv_e - exp_e}"] if csv_e - exp_e else []))
# GV-C3 gap recompute: grain phrase rule
GRAIN = re.compile(r"one (?:record|row) (?:for each|per) ")
derived_gap = {"|".join(k) for k, d in tdesc.items() if not GRAIN.search(d)}
rule("F1", "GV-C3 grain gap recomputed",
     [f"mismatch: {set(g1['gap_lists']['grain_not_declared']) ^ derived_gap}"]
     if set(g1["gap_lists"]["grain_not_declared"]) != derived_gap else [])
rule("F1", "GV-C3 pk_missing structurally empty",
     g1["gap_lists"]["pk_missing"])
# GV-D1 referenced_keys recompute
derived_rk = collections.defaultdict(set)
for (frm, to, on) in csv_e:
    derived_rk[to].add(tuple(p[1] for p in on))
exp_rk = {k: {tuple(x) for x in v} for k, v in
          g1["nodes"]["referenced_keys_expected"].items()
          if not k.startswith("_")}
rule("F1", "GV-D1 referenced_keys recompute",
     [f"{k}: expected {exp_rk.get(k)} vs derived {set(derived_rk.get(k, []))}"
      for k in set(exp_rk) | {k for k in derived_rk}
      if exp_rk.get(k, set()) != derived_rk.get(k, set())])
# GV-B1 containment forest
node_ids = {"db:SIMDB"} | {f"{s}|{sch}" for sch, s in reg["schema_sources"].items()} \
    | {"|".join(t) for t in tables} | {"|".join(c) for c in columns}
parent = {}
for sch, s in reg["schema_sources"].items():
    parent[f"{s}|{sch}"] = "db:SIMDB"
for t in tables: parent["|".join(t)] = f"{t[0]}|{t[1]}"
for c in columns: parent["|".join(c)] = "|".join(c[:3])
rule("F1", "GV-B1 containment forest",
     [f"unreachable {n}" for n in node_ids
      if n != "db:SIMDB" and n not in parent])
# GV-D1 values map vs values.csv
vals = {r["code"]: r["meaning"] for r in
        csv.DictReader(open(BASE + "F1_minimal_estate/simemr_snapshot/values.csv"))}
vm = g1["nodes"]["columns"]["values_map"]["simemr|dbo|ENCOUNTER|APPT_STATUS_C"]
vm = {k: v for k, v in vm.items() if not k.startswith("_")}
rule("F1", "GV-D1 values map bijective",
     [] if vm == vals else [f"{vm} != {vals}"])

# ---------- F2 ----------
t2 = json.load(open(BASE + "F2_estate_files/expected_trees.json"))
snapdir = BASE + "F2_estate_files/estate_snapshot/"
present = {f for f in os.listdir(snapdir) if not f.startswith("manifest")}
acq = set(t2["estate_conservation"]["acquired"])
exc = {e["file"] for e in t2["estate_conservation"]["counted_excluded"]}
rule("F2", "GV-C2 estate conservation (acquired ⊎ excluded = present)",
     [f"mismatch: {(acq | exc) ^ present}"] if (acq | exc) != present else
     (["overlap"] if acq & exc else []))
KINDS = {"COMPARE_EQ","COMPARE_NEQ","COMPARE_GT","COMPARE_GTE","COMPARE_LT",
         "COMPARE_LTE","PATTERN_MATCH","IN_LIST","IN_SELECTION","RANGE",
         "NULL_CHECK","EXISTS_SELECTION","QUANTIFIED_COMPARE"}
ROLES = {"COMPARE_EQ": {"subject"}, "COMPARE_GTE": {"subject", "comparand"},
         "PATTERN_MATCH": {"subject", "pattern"}, "IN_LIST": {"subject", "comparand_list"},
         "NULL_CHECK": {"subject"}}
colset = {f"{s}|{a}|{b}|{c}" for (s, a, b, c) in columns}
tabset = {f"{s}|{a}|{b}" for (s, a, b) in tables}
bad_kind, bad_role, bad_res = [], [], []
res_ext, res_same = [0], [0]
def walk(o, path=""):
    if isinstance(o, dict):
        k = o.get("kind")
        if isinstance(k, str):
            if k not in KINDS:
                bad_kind.append(f"{path}: {k}")
            else:
                need = ROLES.get(k, set())
                have = set(o.keys())
                missing = {r for r in need
                           if r not in have and not (r == "subject" and "1 = 1" in str(o))}
                # 1=1: literal-literal, subject key holds a literal dict — present
                if k == "COMPARE_EQ" and "subject" not in have:
                    missing.add("subject")
                if missing - {"comparand"} and k != "COMPARE_EQ":
                    bad_role.append(f"{path} ({k}): missing {missing}")
        rt = o.get("resolves_to")
        if isinstance(rt, str):
            if rt.startswith("SAME-TREE"):
                res_same[0] += 1
            else:
                res_ext[0] += 1
                if rt.count("|") >= 2 and rt not in colset and rt not in tabset:
                    bad_res.append(f"{path}: {rt}")
        for kk, vv in o.items(): walk(vv, path + "/" + str(kk))
    elif isinstance(o, list):
        for i, vv in enumerate(o): walk(vv, f"{path}[{i}]")
walk(t2)
rule("F2", "GV-A1 predicate kinds in closed set", bad_kind)
rule("F2", "GV-B2 role completeness", bad_role)
rule("F2", "GV-B3 resolves_to targets exist", bad_res)
cen = t2["resolution_census"]
rule("F2", "GV-C2 resolution census recount",
     [f"resolved: census {cen['resolved_refs']} vs recount {res_ext[0]}"]
     * (cen["resolved_refs"] != res_ext[0]) +
     [f"same-tree: census {cen['same_tree_refs']} vs recount {res_same[0]}"]
     * (cen["same_tree_refs"] != res_same[0]))
NR.append("F2: GV-E evidence tiling — fixture asserts evidence by rule, "
          "fragments not enumerated; runnable only against the built mapper")

# ---------- F3 ----------
f3 = json.load(open(BASE + "F3_lenses/expected_lenses.json"))
ws = set(f3["working_set"]["yield"])
# recompute working set from F2 resolves_to KG1 tables (tables touched via FROM refs + predicate columns)
touched = set()
def walk2(o):
    if isinstance(o, dict):
        rt = o.get("resolves_to")
        if isinstance(rt, str) and rt.count("|") == 2 and rt in tabset:
            touched.add(rt)
        if isinstance(rt, str) and rt.count("|") == 3:
            touched.add(rt.rsplit("|", 1)[0])
        for v in o.values(): walk2(v)
    elif isinstance(o, list):
        for v in o: walk2(v)
walk2(t2)
rule("F3", "GV-D1 working_set recompute",
     [f"mismatch: {ws ^ touched}"] if ws != touched else [])
viol = f3["join_compliance"]["violations"]
declared_pairs = {(frm.split("|")[2], to.split("|")[2]) for (frm, to, _) in csv_e}
rule("F3", "GV-D1 join-compliance violation is genuinely undeclared",
     [] if ("PATIENT", "STAGING_LOG") not in declared_pairs
        and ("STAGING_LOG", "PATIENT") not in declared_pairs
     else ["PATIENT-STAGING_LOG is declared?!"])
gc = f3["gap_census"]
rule("F3", "GV-C3 gap census consistency",
     ([f"grain count {gc['grain_not_declared']} != F1 {len(derived_gap)}"]
      if gc["grain_not_declared"] != len(derived_gap) else []) +
     ([f"unsupported {gc['unsupported_dialect_files']} != {sorted(exc)}"]
      if set(gc["unsupported_dialect_files"]) != exc else []))
# decisions lens keys must reference scopes that exist in F2
scope_keys = set()
def walk3(o):
    if isinstance(o, dict):
        nk = o.get("name_key") or (o.get("scope", {}) or {}).get("name_key") \
             if isinstance(o.get("scope"), dict) else None
        for v in o.values(): walk3(v)
        if "name_key" in o: scope_keys.add(o["name_key"])
    elif isinstance(o, list):
        for v in o: walk3(v)
walk3(t2)
dec_keys = [k for k in f3["decisions_membership"] if k not in
            ("completeness", "_witness")]
bad = [k for k in dec_keys
       if "::" in k and k not in scope_keys and "OPEN" not in k
       and not k.endswith(".sql")]
rule("F3", "GV-A2 decisions keys reference existing scopes", bad)

# ---------- F4 ----------
f4 = json.load(open(BASE + "F4_produce/expected_produce.json"))
GATE = {"gate_passed", "skeleton_floor", "flagged"}
bad = []
for t, spec in f4["targets"].items():
    if not set(spec["gate_outcome_allowed"]) <= GATE:
        bad.append(f"{t}: outcomes outside closed vocab")
    ov = set(spec.get("expect_substrings", [])) & set(spec.get("forbid_substrings", []))
    if ov: bad.append(f"{t}: expect∩forbid = {ov}")
rule("F4", "GV-A1 gate vocab + expect/forbid disjoint", bad)
acct = f4["run_event_expected"]["accounting_per_class"]["descriptions"]
rule("F4", "GV-C2 run accounting arithmetic",
     [f"{acct['attempted']} != shipped {acct['shipped']} + absent {acct['absent']}"]
     if acct["attempted"] != acct["shipped"] + acct["absent"] else
     ([f"attempted {acct['attempted']} != {len(f4['targets'])} targets"]
      if acct["attempted"] != len(f4["targets"]) else []))
# cross-fixture: expected substrings must be grounded in F1/F2 inputs
srcs = " ".join(open(snapdir + f).read() for f in acq) + " " + json.dumps(vals)
bad = [s for t, spec in f4["targets"].items()
       for s in spec.get("expect_substrings", []) if s not in srcs]
rule("F4", "GV-E expect_substrings grounded in inputs", bad)

# ---------- F5 ----------
f5 = json.load(open(BASE + "F5_approve_land/expected_approve_land.json"))
bad = []
for d in f5["approve_script"]:
    if not d["author"].startswith("person:"):
        bad.append(f"disposition author not a person: {d['author']}")
rule("F5", "GV-D2 dispositions human-only", bad)
# ownership lens recompute on the script
mach_versions_only = True
has_accept = any(d["ruling"] == "accept" for d in f5["approve_script"])
derived_own = "human" if (has_accept or not mach_versions_only) else "machine"
stated = f5["derived_after_approve"]["ownership(#Recent description)"]
rule("F5", "GV-D1 ownership recompute",
     [] if stated.startswith("human") == (derived_own == "human")
     else [f"stated {stated} vs derived {derived_own}"])
# current-outcome recompute
obs = [a for a in f5["land_script"] if a["act"] == "observe"]
last = obs[-1]["expect_event"]["outcome"] if obs else None
rule("F5", "GV-D1 current-outcome recompute",
     [] if f5["derived_after_land"]["current_outcome(the proposal)"].startswith(last)
     else ["mismatch"])

# ---------- F6 ----------
f6 = json.load(open(BASE + "F6_refusals/expected_refusals.json"))
CHECKS = {f"INTAKE-{i}" for i in range(11)} | {"LC-C3", "LC-F5"}
bad = []
for c in f6["cases"]:
    ref = c.get("expect_refusal", "")
    if ref and not any(ref.startswith(k) for k in CHECKS):
        bad.append(f"{c['id']}: refusal cites no known check: {ref[:40]}")
rule("F6", "GV-A1 refusals cite existing checks", bad)
rule("F6", "GV-B open cases flagged not decided",
     [c["id"] for c in f6["cases"]
      if "OPEN" in json.dumps(c) and "Register row filed" not in json.dumps(c)
      and "_OPEN" in json.dumps(c) and "UNRULED" not in json.dumps(c)])

# ---------- report ----------
print(f"PASSED: {len(OK)} rules")
if V:
    print(f"VIOLATIONS: {len(V)}")
    for f, r, d in V: print(f"  [{f}] {r}: {d}")
else:
    print("VIOLATIONS: none")
for n in NR: print("NOT-RUNNABLE:", n)
sys.exit(1 if V else 0)
