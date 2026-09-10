"""STEP 4 of the Connection Ledger build — PART EDGES. The test
suite, shown to Sunny before any implementation (step discipline).

The review's INDEX-ONLY rows: conditions and parameters are
searchable (speech, facet cards) but NOT traversable — their
ownership lives in index `owner` fields and code owner-chains, not
in the graph. Step 4 makes the parts walk:

- condition —belongs_to→ its scope (both-ended), so a condition
  chains condition → scope → file by pure traversal.
- parameter —belongs_to→ its file.
- The ledger documents ALL pseudo-node citizens (condition,
  parameter, derived column, drift) with their edges — status
  edged-pseudo: adjacency citizens born from trees, not store
  nodes, outside the store census by ruling (registry 1.24.0).

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import censuses, connect
from aivia.graph.read_api import ReadApi

T0 = "2026-09-07T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    read = ReadApi(store)
    return read, connect.build_adjacency(read)


def test_conditions_walk_to_their_scopes(world):
    _read, adj = world
    cond = "reporting/USP_ED_SEPSIS.sql::#Base_Pop::c0"
    edges = {(n, lbl) for n, lbl in adj.get(cond, [])}
    assert ("reporting/USP_ED_SEPSIS.sql::#Base_Pop",
            "belongs_to") in edges
    back = {(n, lbl) for n, lbl in
            adj.get("reporting/USP_ED_SEPSIS.sql::#Base_Pop", [])}
    assert (cond, "belongs_to") in back


def test_parameters_walk_to_their_files():
    """Corrected pin: the sepsis estate declares ZERO parameters at
    tree grain (empirically probed — the corpus lacks the
    IF-default pattern the mapper captures), so the edge is proven
    on a synthetic tree that exercises it."""
    from aivia.graph import kg2_mapper

    class FakeRead:
        def __init__(self, trees):
            self._trees = trees

        def trees(self):
            return self._trees

        def nodes(self, kind=None):
            return []
    tree = kg2_mapper.map_tree("p.sql", """
IF @dStart IS NULL SET @dStart = '2026-01-01';
SELECT ENCOUNTER_ID INTO #Out FROM dbo.T WHERE D >= @dStart;
""")
    assert tree["parameters"], "the synthetic exercises the pattern"
    adj = connect.build_adjacency(FakeRead({"p.sql": tree}))
    name = tree["parameters"][0]["name"]
    edges = {(n, lbl) for n, lbl in adj.get(f"p.sql::param/{name}", [])}
    assert ("p.sql", "belongs_to") in edges


def test_a_condition_chains_to_its_file_by_traversal(world):
    """condition -> scope -> file: two hops, no owner-chain code."""
    _read, adj = world
    cond = "reporting/USP_ED_SEPSIS.sql::#Base_Pop::c0"
    scopes = {n for n, lbl in adj.get(cond, [])
              if lbl == "belongs_to"}
    assert scopes
    files = set()
    for s in scopes:
        files |= {n for n, lbl in adj.get(s, []) if lbl == "has_part"}
    assert any(str(f).endswith("reporting/USP_ED_SEPSIS.sql")
               for f in files)


def test_ledger_documents_the_pseudo_citizens(world):
    """Every adjacency citizen born from trees (not the store) is
    ruled in the ledger — status edged-pseudo, outside the store
    census by ruling, never undocumented."""
    read, _adj = world
    ledger = censuses.connection_ledger()
    assert ledger["condition"]["edge"] == "belongs_to"
    assert ledger["condition"]["status"] == "edged-pseudo"
    assert ledger["parameter"]["edge"] == "belongs_to"
    assert ledger["parameter"]["status"] == "edged-pseudo"
    assert ledger["derived_column"]["status"] == "edged-pseudo"
    assert ledger["drift"]["status"] == "edged-pseudo"
    # the store census stays whole and clean
    c = censuses.connection_census(read)
    assert c["unledgered_kinds"] == []
    assert c["birth_edged"] + c["counted_missing"] + c["rooted"] \
        == c["total"]
