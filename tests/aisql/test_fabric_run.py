"""Brief_Fabric_Resident FR4+FR5 (Sunny's "all eight as proposed,
build it", 2026-09-19): the THIN-SHELL driver. In Fabric the
notebook is three one-line cells; every line of logic lives here,
in the wheel, tested. These pins prove: the boot takes an explicit
estate PATH (FR4 — a lakehouse Files folder, with the repo name
route unchanged); dry_run refuses a non-estate folder cheaply and
speaks the census + both description kinds; scribe refuses without
a key BEFORE any boot or spend (the AISQL_RECORD posture, same as
devtools/scribe_draft.py whose core moved into the wheel per THE
TURN-KEY RULING). Doubles law: the store is a scripted double —
no Fabric, no network, no paid seat anywhere in this module.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql import console, fabric_run


class _Node:
    def __init__(self, identity, label, properties):
        self.identity = identity
        self.label = label
        self.properties = properties


class _Store:
    def __init__(self, nodes):
        self._nodes = nodes

    def current_nodes(self):
        return list(self._nodes)


def _estate(tmp_path):
    (tmp_path / "registration.json").write_text("{}")
    return tmp_path


def test_estate_base_accepts_a_path_and_a_name(tmp_path):
    base = _estate(tmp_path)
    assert console._estate_base(str(base)) == base
    named = console._estate_base("ed_sepsis_dev")
    assert named.name == "ed_sepsis_dev"
    assert named.parent.name == "estates"


def test_dry_run_refuses_a_non_estate_folder(tmp_path):
    with pytest.raises(SystemExit) as err:
        fabric_run.dry_run(str(tmp_path / "nowhere"))
    assert err.value.code == 2


def test_dry_run_speaks_census_and_both_description_kinds(
        monkeypatch, tmp_path, capsys):
    base = _estate(tmp_path)
    store = _Store([
        _Node("db.dbo.f1.sql::file", "file", {
            "technical_definition": "TD-SENTINEL text",
            "description": "AI-generated: DESC-SENTINEL text"}),
        _Node("db.dbo.t1::table", "table", {}),
        _Node("db.dbo.t1.c1::column", "column", {}),
    ])
    monkeypatch.setattr(
        console, "build_store",
        lambda estate, journal_path=None, descriptions=True:
        (store, base))
    fabric_run.dry_run(str(base))
    out = capsys.readouterr().out
    assert "file 1" in out and "table 1" in out and "column 1" in out
    assert "TD-SENTINEL text" in out
    assert "AI-generated: DESC-SENTINEL text" in out


def test_scribe_refuses_without_key_before_any_boot(
        monkeypatch, tmp_path):
    base = _estate(tmp_path)
    monkeypatch.setattr(console, "_env_key", lambda: "")
    monkeypatch.setattr(
        console, "build_store",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("boot happened before the key refusal")))
    with pytest.raises(SystemExit) as err:
        fabric_run.scribe(str(base))
    assert err.value.code == 2


def test_dry_run_speaks_composed_texts_first(monkeypatch, tmp_path,
                                             capsys):
    """Brief_Dryrun_Order (Sunny, 2026-09-20, from the work pilot:
    "i can't find the scope descriptions or statement or sql
    file's. can you update to show these descriptions first?"):
    file -> scope -> statement speak BEFORE the dictionary flood,
    each label under a counted header so the flood is skippable."""
    base = _estate(tmp_path)
    store = _Store([
        _Node("db.dbo.c9::column", "column",
              {"description": "COLUMN-SENTINEL"}),
        _Node("db.dbo.t9::table", "table",
              {"description": "TABLE-SENTINEL"}),
        _Node("f1.sql::stmt/1", "statement",
              {"description": "STATEMENT-SENTINEL"}),
        _Node("f1.sql::scope/a", "scope",
              {"description": "SCOPE-SENTINEL"}),
        _Node("db.dbo.f1.sql::file", "file",
              {"technical_definition": "FILE-SENTINEL"}),
    ])
    monkeypatch.setattr(
        console, "build_store",
        lambda estate, journal_path=None, descriptions=True:
        (store, base))
    fabric_run.dry_run(str(base))
    out = capsys.readouterr().out
    order = [out.index(s) for s in (
        "FILE-SENTINEL", "SCOPE-SENTINEL", "STATEMENT-SENTINEL",
        "COLUMN-SENTINEL")]
    assert order == sorted(order), out
    assert out.index("=== file (1) ===") < out.index(
        "=== scope (1) ===") < out.index("=== statement (1) ===")
    assert "=== column (1) ===" in out and "=== table (1) ===" in out
