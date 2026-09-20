"""ERA 3 — THE FROM-STRUCTURE NODE FAMILY (Design_Graph_Engine,
ratified by Sunny 2026-09-14: "ratified — build era 3, a1 if the
probe passes"; a1 built as the ruled default while the probe waits
on capacity — the a2 relabel is the recorded contingency).

Every FROM clause walks the same sided shape: scope —has_part→
(join | direct_read) —left_side/right_side→ table-or-scope. The
kind `direct_read` is the single-table FROM — ONE side edge, no
ON, no type: absence lives in the KIND, never a null endpoint. It
twins ScriptDom's NamedTableReference (ADR 0001: the twin claims
parse facts only). The era-2 `reads` remainder edge RETIRES; the
two M2 invariants collapse into one: per scope, side-targets ==
read-set.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql.graph.read_api import ReadApi


@pytest.fixture(scope="module")
def world():
    from aisql.console import build_store
    store, _ = build_store("sepsis")
    return store, ReadApi(store)


def test_reads_edges_are_retired_from_the_store(world):
    store, _ = world
    assert not list(store.current_edges("reads"))


def test_direct_read_nodes_carry_one_side_no_on(world):
    store, read = world
    nodes = read.nodes("direct_read")
    assert nodes  # the sepsis estate has no-join scopes
    tables = {n.identity for n in read.nodes("table")}
    left = {}
    for e in store.current_edges("left_side"):
        left.setdefault(e.from_id, []).append(e.to_id)
    right_from = {e.from_id for e in store.current_edges("right_side")}
    owners = {e.to_id: e.from_id
              for e in store.current_edges("has_part")}
    for n in nodes:
        assert "::read#" in n.identity
        sides = left.get(n.identity, [])
        assert len(sides) == 1 and sides[0] in tables
        assert n.identity not in right_from  # one-sided BY KIND
        assert "on" not in n.properties      # no combining fact
        assert "joinType" not in n.properties
        assert owners[n.identity] == n.identity.rsplit("::read#", 1)[0]
        assert n.properties["description"].startswith("Reads ")


def test_the_one_invariant_side_targets_equal_read_set(world):
    """COVERING, era 3 (DISJOINT is vacuous — one mechanism): per
    scope, the tables on its structure nodes' sides == the tables
    its parse tree reads. Recomputed from the trees, never from
    the edges being checked."""
    from aisql.lenses import decisions
    store, read = world
    by_scope_sides = {}
    tables = {n.identity for n in read.nodes("table")}
    owners = {e.to_id: e.from_id
              for e in store.current_edges("has_part")
              if "::join#" in e.to_id or "::read#" in e.to_id}
    for lbl in ("left_side", "right_side"):
        for e in store.current_edges(lbl):
            if e.to_id in tables and e.from_id in owners:
                by_scope_sides.setdefault(
                    owners[e.from_id], set()).add(e.to_id)

    def tree_read_set(scope):
        out = set()

        def walk(d):
            if isinstance(d, dict):
                for fr in (d.get("from_refs") or []):
                    r = fr.get("resolves_to")
                    if isinstance(r, str) and r.count("|") == 2:
                        out.add(r)
                for v in d.values():
                    walk(v)
            elif isinstance(d, list):
                for v in d:
                    walk(v)
        walk(scope)
        return out

    checked = 0
    for _key, tree in read.trees().items():
        for scope in decisions.named_scopes(tree):
            want = tree_read_set(scope)
            if not want:
                continue
            got = by_scope_sides.get(scope["name_key"], set())
            assert got == want, scope["name_key"]
            checked += 1
    assert checked  # the invariant actually ran


def test_uniform_walk_answers_the_reads_question(world):
    """The era-3 payoff at the console: 'which scopes read T' for
    a NO-JOIN table answers through the SAME sided walk as joined
    tables — the direct_read node is connective structure exactly
    like a join."""
    from aisql import meaning_console as mc
    _store, read = world
    entries, _ = mc.technical_scope(read)
    adj, directed = mc.technical_adjacency(read)
    # a table read ONLY via direct_read in this estate
    dr = read.nodes("direct_read")[0]
    target = next(e.to_id for e in _store.current_edges("left_side")
                  if e.from_id == dr.identity)
    tname = target.rsplit("|", 1)[-1]
    owner = dr.identity.rsplit("::read#", 1)[0]
    kind_entry = next(e for e in entries
                      if e["identity"] == "kind::scope")

    class _Sem:
        def search(self, token, top_k=None, kind=None):
            if token == "scopes":
                return [{**dict(kind_entry), "score": 1.2}]
            return []
    r = mc.answer_question(
        f"which scopes read {tname}?",
        lambda q: {"mentions": ["scopes", "read", tname],
                   "relations": ["read"]},
        entries, _Sem(), read, adj, directed)
    assert r["mode"] == "enumeration"
    assert "reads" in r["edge_constraints"]
    # same-named scopes owner-qualify (the BED_STAY_ID law), so
    # match on identity, not display
    assert owner in {row["a_id"] for row in r["rows"]}
