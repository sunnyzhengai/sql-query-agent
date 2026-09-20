"""The ledger close (Sunny's order, 2026-09-06): the last engine-debt
constructs map — DELETE (voiced as removal, never 'a selection'),
GOTO/LABEL (loop control captured; LABEL operational), PIVOT
(aggregate + in-values), star-through resolution (the star ruling
applied at read time), derived-member and folded-alias binding.
Requires ScriptDom — no fallback (ADR 0001).

Proves: contract:aisql-design-to-code
"""
from aisql.graph.kg2_mapper import map_tree
from aisql.graph.kg2_translator import translate


def test_delete_maps_as_removal_scope():
    tree = map_tree("d.sql",
                    "DELETE FROM reporting.IP_SEPSIS "
                    "WHERE DATE_STAMP < @cutoff")
    stmt = tree["statements"][0]
    assert stmt["statement_kind"] == "DELETE"
    scope = stmt["scope"]
    assert scope["operation"] == "delete"
    assert scope["from_refs"][0]["table_ref"] == "reporting.IP_SEPSIS"
    assert scope["where"]["kind"] == "COMPARE_LT"
    assert tree["remainder"] == []


def test_goto_label_loop_captured():
    tree = map_tree("g.sql",
                    "startloop:\nSET @i = @i + 1\n"
                    "IF @i < 10 GOTO startloop")
    kinds = [s["statement_kind"] for s in tree["statements"]]
    assert kinds == ["LABEL", "SET", "IF"]
    assert tree["statements"][0]["label"] == "startloop"
    assert tree["remainder"] == []
    twin = translate(tree)
    label = next(n for n in twin["nodes"]
                 if n["content"].get("does") == "LABEL")
    assert label["subkind"] == "operational"  # marker, never voiced


def test_pivot_transform_mapped():
    tree = map_tree("p.sql",
                    "SELECT A_VAL FROM (SELECT ENC, MET, VAL FROM T) s "
                    "PIVOT (MAX(VAL) FOR MET IN ([A_VAL],[B_VAL])) p")
    scope = tree["statements"][0]["scope"]
    ref = next(r for r in scope["from_refs"] if r.get("pivot"))
    assert ref["pivot"]["aggregate"] == "MAX"
    assert ref["pivot"]["in_values"] == ["A_VAL", "B_VAL"]
    assert tree["remainder"] == []
    twin = translate(tree)
    source = next(n for n in twin["nodes"]
                  if n["content"].get("pivot"))
    assert source["content"]["pivot"]["aggregate"] == "MAX"


def test_star_through_binds_to_underlying_member():
    # SELECT * INTO #Copy FROM #Base; later a #Copy column resolves
    # through the star to #Base's member — read-time expansion, the
    # star ruling's lawful form (recomputed each run, never frozen)
    tree = map_tree(
        "s.sql",
        "SELECT ENCOUNTER_ID, SCORE INTO #Base FROM T\n"
        "SELECT * INTO #Copy FROM #Base\n"
        "SELECT c.SCORE FROM #Copy c WHERE c.SCORE > 4")
    # resolution requires a store; here the mapper-side shape is the
    # claim: the member walk in resolve() is exercised over the
    # corpus (pins) — this test pins the tree shape it relies on
    scopes = [s["scope"] for s in tree["statements"] if s.get("scope")]
    assert any(m.get("star") for m in scopes[1]["projection"])


def test_folded_alias_and_self_qualifier_shapes():
    tree = map_tree(
        "f.sql",
        "SELECT A.X INTO #T FROM TBL A WHERE a.X = 1\n"
        "SELECT [#T].X FROM #T")
    # lowercase 'a.X' + bracketed '[#T].X' both parse as column refs;
    # the resolver's folded lookup + self-qualifier registration bind
    # them (exercised over the corpus pins; shape pinned here)
    refs = []
    def walk(n):
        if isinstance(n, dict):
            if n.get("kind") == "column_ref":
                refs.append(n["ref"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(tree["statements"])
    assert "a.X" in refs and "#T.X" in refs
