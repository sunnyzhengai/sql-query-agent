"""KEYVAULT-1 (code-side): "keyvault:<name>" refs resolve through
the org_config key_vault: block at load time; plain values pass
untouched; every failure NAMES ITS CURE (the RW-16 pattern).

Proves: contract:suite-legibility
"""

import pytest

from src.secrets_vault import (
    KeyVaultError,
    resolve_config_secrets,
)


def _fetch(store):
    calls = []

    def fetch(vault_url, name, token_provider=None):
        calls.append((vault_url, name))
        if name not in store:
            raise KeyVaultError(f"secret {name!r} not found")
        return store[name]
    return fetch, calls


class TestResolveConfigSecrets:
    def test_refs_resolve_through_the_vault(self, monkeypatch):
        import src.secrets_vault as sv
        fetch, calls = _fetch({"purview-secret": "s3cr3t"})
        monkeypatch.setattr(sv, "fetch_secret", fetch)
        raw = {"key_vault": {"url": "https://v.vault.azure.net"},
               "adapters": {"purview": {
                   "client_secret": "keyvault:purview-secret",
                   "account_name": "plain"}}}
        out = sv.resolve_config_secrets(raw)
        assert out["adapters"]["purview"]["client_secret"] == "s3cr3t"
        assert out["adapters"]["purview"]["account_name"] == "plain"
        assert calls == [("https://v.vault.azure.net",
                          "purview-secret")]

    def test_no_refs_means_no_vault_contact(self, monkeypatch):
        import src.secrets_vault as sv
        fetch, calls = _fetch({})
        monkeypatch.setattr(sv, "fetch_secret", fetch)
        raw = {"org": {"name": "x"},
               "key_vault": {"url": "https://v.vault.azure.net"}}
        assert sv.resolve_config_secrets(raw) == raw
        assert calls == []

    def test_ref_without_vault_block_names_the_cure(self):
        raw = {"adapters": {"purview": {
            "client_secret": "keyvault:purview-secret"}}}
        with pytest.raises(KeyVaultError) as e:
            resolve_config_secrets(raw)
        msg = str(e.value)
        assert "purview-secret" in msg
        assert "key_vault:" in msg and "url:" in msg   # the cure

    def test_plain_config_passes_untouched(self):
        raw = {"org": {"name": "x"},
               "extractor": {"sql_server": {"host": "h",
                                            "database": "d"}}}
        assert resolve_config_secrets(raw) == raw


class TestFetchSecretCures:
    def _http_error(self, code):
        import urllib.error
        return urllib.error.HTTPError("u", code, "m", {}, None)

    def test_missing_secret_names_the_create_line(self, monkeypatch):
        import src.secrets_vault as sv

        def boom(req, timeout):
            raise self._http_error(404)
        monkeypatch.setattr(sv.urllib.request, "urlopen", boom)
        with pytest.raises(KeyVaultError, match="keyvault secret set"):
            sv.fetch_secret("https://v.vault.azure.net", "nope",
                            lambda: "tok")

    def test_permission_refusal_names_the_role(self, monkeypatch):
        import src.secrets_vault as sv

        def boom(req, timeout):
            raise self._http_error(403)
        monkeypatch.setattr(sv.urllib.request, "urlopen", boom)
        with pytest.raises(KeyVaultError,
                           match="Key Vault Secrets User"):
            sv.fetch_secret("https://v.vault.azure.net", "s",
                            lambda: "tok")
