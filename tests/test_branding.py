"""Tests for the product-name seam (src/branding.py)."""

from src import branding


def test_default_name_is_neutral(monkeypatch):
    monkeypatch.delenv("SQA_PRODUCT_NAME", raising=False)
    assert branding.product_name() == branding.DEFAULT_PRODUCT_NAME
    assert "aivia" not in branding.DEFAULT_PRODUCT_NAME.lower()


def test_env_overrides_name(monkeypatch):
    monkeypatch.setenv("SQA_PRODUCT_NAME", "AIVIA")
    assert branding.product_name() == "AIVIA"


def test_legacy_env_prefers_new_name(monkeypatch):
    monkeypatch.setenv("SQA_LLM_MODEL", "new-model")
    monkeypatch.setenv(branding._LEGACY_PREFIX + "LLM_MODEL", "old-model")
    assert branding.legacy_env("LLM_MODEL") == "new-model"


def test_legacy_env_falls_back_with_warning(monkeypatch, caplog):
    monkeypatch.delenv("SQA_LLM_MODEL", raising=False)
    monkeypatch.setenv(branding._LEGACY_PREFIX + "LLM_MODEL", "old-model")
    with caplog.at_level("WARNING"):
        assert branding.legacy_env("LLM_MODEL") == "old-model"
    assert any("deprecated" in r.message for r in caplog.records)


def test_legacy_env_default(monkeypatch):
    monkeypatch.delenv("SQA_KUSTO_DB", raising=False)
    monkeypatch.delenv(branding._LEGACY_PREFIX + "KUSTO_DB", raising=False)
    assert branding.legacy_env("KUSTO_DB", "fallback") == "fallback"
