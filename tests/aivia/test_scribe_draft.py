"""Brief_Work_Dryrun (Sunny's "approved, both proposals stand",
2026-09-18): the Scribe draft driver for the work dry run. The
driver REFUSES cheaply — no estate arg or no key means exit
before any boot, any spend, any network. Drafting itself is
Sunny's paid run at his hand (the AIVIA_RECORD posture), so the
pins here prove only the refusals and the entry shape; the
draft chain (scan_undescribed -> evidence -> draft -> land) has
its own suite in test_describe/test_produce.

Proves: contract:aivia-design-to-code
"""
import pytest


def _main():
    from devtools import scribe_draft
    return scribe_draft.main


def test_refuses_without_estate(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        _main()([])
    assert exc.value.code == 2
    assert "estate" in capsys.readouterr().err.lower()


def test_refuses_without_key(monkeypatch, capsys):
    import devtools.scribe_draft as sd
    monkeypatch.setattr(sd, "_env_key", lambda: "")
    with pytest.raises(SystemExit) as exc:
        sd.main(["work_pilot"])
    assert exc.value.code == 2
    assert "key" in capsys.readouterr().err.lower()
