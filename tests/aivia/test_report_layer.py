"""M7 THE REPORT LAYER — pins authored FAILING (test-first;
Brief_M7_Consumption_Governance, Sunny's "approved" 2026-09-17).

The ruled design: executes becomes a real edge (unresolved EXEC
names stay a COUNTED property, never guessed); the report's
technical_definition = the executed files' catch-alls
CHERRY-PICKED to its bound fields + population whole + THE
DISCLOSURE LINE (Q4 "a"); a shell (no bound fields) falls back
to the whole catch-all; multi-proc CONCATENATES labeled by proc
(Q3 "a"); the description is the Scribe summary, APPROVED only
— the shell text stands as the counted fallback until approval
(the ruled "shell description only when no proc speaks",
extended: shell until approved).

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.console import build_store
from aivia.flows import inbound
from aivia.graph.read_api import ReadApi

DISCLOSURE = ("Filters shown are the procedure's; the report "
              "may filter further in Power BI.")


@pytest.fixture(scope="module")
def dev():
    store, _ = build_store("ed_sepsis_dev")
    return store, ReadApi(store)


@pytest.fixture(scope="module")
def sepsis():
    store, _ = build_store("sepsis")
    return store, ReadApi(store)


def test_executes_is_a_real_edge_resolved_only(dev):
    store, read = dev
    rpt = store.current_nodes("pbi_report")[0]
    edges = [e for e in store.current_edges("executes")
             if e.from_id == rpt.identity]
    file_ids = {n.identity for n in store.current_nodes("file")}
    assert edges, "the resolved EXEC becomes an edge"
    assert all(e.to_id in file_ids for e in edges)
    # the dev corpus holds ONE file: exactly one resolves
    assert len(edges) == 1
    unresolved = rpt.properties.get("unresolved_executes") or []
    assert len(unresolved) == 2  # counted, never guessed


def test_report_definition_cherry_picked_with_disclosure(dev):
    store, read = dev
    rpt = store.current_nodes("pbi_report")[0]
    td = rpt.properties.get("technical_definition")
    assert td and td.strip()
    assert td == inbound._render_report_definition(
        read, rpt.identity)
    assert DISCLOSURE in td
    # the cherry-pick keeps bound outputs and drops unbound ones:
    # the model imports the compliance flag; it stays
    assert "fps bolus abx re screen compliance" in td.lower()
    # population rides WHOLE (Q4): the proc's date window speaks
    assert "the arrival date is between the d start date " \
           "parameter and the d end date parameter" in td


def test_shells_fall_back_to_the_whole_catch_all(sepsis):
    store, read = sepsis
    shells = [n for n in store.current_nodes("pbi_report")
              if "shell" in str(n.properties.get("source") or "")]
    assert shells, "the sepsis estate carries the 27 shells"
    fids = {e.from_id: e.to_id
            for e in store.current_edges("executes")}
    files = {n.identity: n for n in store.current_nodes("file")}
    checked = 0
    for sh in shells:
        td = sh.properties.get("technical_definition")
        target = fids.get(sh.identity)
        if not target or target not in files:
            continue
        ftd = files[target].properties.get("technical_definition")
        if not ftd:
            continue
        checked += 1
        assert td.startswith(ftd[:60])  # the whole catch-all rides
        assert DISCLOSURE in td
    assert checked > 5


def test_multi_proc_concatenates_labeled():
    """Q3's mechanism, pinned on a synthetic store (the ESTATE
    case waits on Sunny's alias ruling — FC2: both reports.*
    EXECs are RPTS-alias questions the machine may not guess;
    measured 2026-09-17: 1 resolves + 2 counted in BOTH
    estates)."""
    from aivia.graph.store import Store
    store = Store()
    t0 = "2026-09-17T00:00:00Z"
    for fid, td in (("repo://x/reporting/USP_A.sql",
                     "Presents: alpha. Population filters: "
                     "In the a selection: one."),
                    ("repo://x/reports/USP_B.sql",
                     "Presents: beta. Inner joins: Joins X "
                     "with Y on X.I = Y.I.")):
        store.append_node("file", fid,
                          {"technical_definition": td}, t0, "x")
    store.append_node("pbi_report", "pbi://x/dash",
                      {"name": "Dash", "bound_fields": {}},
                      t0, "x")
    for fid in ("repo://x/reporting/USP_A.sql",
                "repo://x/reports/USP_B.sql"):
        store.append_edge("executes", "pbi://x/dash", fid, {},
                          t0, "x")
    td = inbound._render_report_definition(
        ReadApi(store), "pbi://x/dash")
    assert td.count("From USP_") == 2
    assert "From USP_A: Presents: alpha." in td
    assert "From USP_B: Presents: beta." in td
    assert td.rstrip().endswith(DISCLOSURE)


def test_the_alias_questions_stay_counted(sepsis):
    """FC2 both ways: reports.USP_ED_Sepsis and
    reports.USP_IP_SEPSIS match no corpus file exactly (the
    corpus is RPTS-prefixed) — they stay COUNTED, never guessed,
    until Sunny rules the aliases as DATA."""
    store, _ = sepsis
    rpt = next(n for n in store.current_nodes("pbi_report")
               if "real-tmdl" in str(n.properties.get("source")
                                     or ""))
    unresolved = rpt.properties.get("unresolved_executes") or []
    assert sorted(unresolved) == ["reports/USP_ED_Sepsis.sql",
                                  "reports/USP_IP_SEPSIS.sql"]


def test_description_is_the_approved_summary(dev):
    """The approved-only posture at report grain, SECOND state:
    the checkpoint-2 batch landed Sunny's approval (2026-09-18)
    — the stored description IS the approved Scribe summary,
    byte-identical, carrying THE AI-GENERATED PREFIX (his ruling
    at the served gate, same day: agent-authored text lands
    labeled; the approved artifact stays pure)."""
    store, _ = dev
    rpt = store.current_nodes("pbi_report")[0]
    assert rpt.properties.get("description") == (
        "AI-generated: "
        "sepsis screening metrics, blood pressure readings and "
        "timing, for emergency department patient assessment.")
