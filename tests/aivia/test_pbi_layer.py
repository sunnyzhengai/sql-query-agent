"""PHASE H — THE PBI LAYER (Sunny's ruling 2026-09-08: every proc
feeds a PBI report; reports may be synthetic, the mapping is real;
this is the real mapping for words like 'reports'). Suite first.

Pins:
1. PBI Report nodes load from the estate's pbi_snapshot — the real
   dashboard by its real name + one synthetic shell per remaining
   proc; label "PBI Report" (labels are user-facing names).
2. executes edges walk both ways (report ↔ proc files); the
   Connection Ledger covers the label; the census stays whole.
3. Reports SPEAK: description + the displays derived from their
   procs' delivery members (real, from the twins).
4. THE PAYOFF: 'what reports are about ED' — under the total-score
   law the ED dashboard collects credit from BOTH mentions
   ('reports' via its label card + 'ED' via its name) and ranks
   above any single-credit column.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import ask, censuses, connect, grounding
from aivia.graph.read_api import ReadApi

from . import doubles
from .doubles import recorded_embed, scripted_proposals

T0 = "2026-09-08T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, recorded_embed,
                                       doubles.EMBED_MODEL, cache_path=None)
    return store, read, index, semantic


def test_pbi_reports_load_with_their_label(world):
    _store, read, _index, _semantic = world
    reports = read.nodes("PBI Report")
    # 27 since the 1:1 ruling (2026-09-09): the dashboard trimmed
    # to 2 procs, the freed proc gained its own shell
    assert len(reports) == 27
    names = {n.properties["name"] for n in reports}
    assert "ED Sepsis Screening Dashboard" in names  # the real one


def test_executes_edges_walk_both_ways(world):
    _store, read, _index, _semantic = world
    adj = connect.build_adjacency(read)
    dash = next(n for n in read.nodes("PBI Report")
                if n.properties["name"]
                == "ED Sepsis Screening Dashboard")
    edges = {(t, lbl) for t, lbl in adj.get(dash.identity, [])}
    proc = next(t for t, lbl in edges if lbl == "executes")
    assert "USP" in proc
    back = {(t, lbl) for t, lbl in adj.get(proc, [])}
    assert (dash.identity, "executes") in back


def test_ledger_covers_the_label_and_census_holds(world):
    _store, read, _index, _semantic = world
    ledger = censuses.connection_ledger()
    assert ledger["PBI Report"]["edge"] == "executes"
    assert ledger["PBI Report"]["status"] == "edged"
    c = censuses.connection_census(read)
    assert c["unledgered_kinds"] == []
    assert "PBI Report" not in c["counted_missing_kinds"]


def test_reports_speak_their_displays(world):
    _store, _read, index, _semantic = world
    dash = next(e for e in index if e["label"] == "PBI Report"
                and e["name"] == "ED Sepsis Screening Dashboard")
    assert "sepsis" in dash["words"].lower()
    assert "displays" in dash["words"].lower()


@pytest.mark.xfail(strict=True, reason=(
    "HELD in Manifest_Build SectionD (Sunny 2026-09-09): "
    "scoring-law resumption evidence — real-physics residual "
    "after the speech contract; strict forces unmarking when "
    "the ruling lands"))
def test_reports_about_ed_crowns_the_dashboard(world):
    store, _read, _index, semantic = world
    q = "what reports are about ED"
    interp = scripted_proposals({q.lower(): {
        "mentions": ["reports", "ED"],
        "expansions": {"ED": ["emergency department"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    hits = result["hits"]
    first_pbi = next(i for i, h in enumerate(hits)
                     if h["label"] == "PBI Report")
    first_col = next((i for i, h in enumerate(hits)
                      if h["label"] == "column"), len(hits))
    assert first_pbi < first_col  # both words vouched for the report
    assert "ED" in hits[first_pbi]["name"] \
        or "Emergency" in hits[first_pbi]["name"]
