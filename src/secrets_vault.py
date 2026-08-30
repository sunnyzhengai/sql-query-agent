"""KEYVAULT-1 (code-side, overnight queue 2): secrets resolve from
Azure Key Vault when org_config carries a `key_vault:` block; plain
file values remain the fallback. NO tenant action is taken here —
Sunny's vault click completes the loop later; this closes the
ship-readiness gap in code.

Config shape:
    key_vault:
      url: https://<vault>.vault.azure.net
    adapters:
      purview:
        client_secret: "keyvault:purview-client-secret"

Any string value of the form "keyvault:<secret-name>" resolves at
config-load time. Every failure NAMES ITS CURE (the RW-16 pattern):
a ref with no vault block, a missing secret, a permission refusal,
and a missing credential each say exactly what to do.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

PREFIX = "keyvault:"
_AUDIENCE = "https://vault.azure.net"


class KeyVaultError(Exception):
    """Typed, cure-bearing — never a bare traceback at config load."""


def _default_token_provider():
    """Fabric notebook first (notebookutils), az CLI otherwise —
    the connection.py pattern; failures name the cure."""
    try:
        import notebookutils  # Fabric runtime provides this
        return notebookutils.credentials.getToken(_AUDIENCE)
    except ImportError:
        pass
    import subprocess
    try:
        out = subprocess.run(
            ["az", "account", "get-access-token", "--resource",
             _AUDIENCE, "--query", "accessToken", "-o", "tsv"],
            capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception as e:  # noqa: BLE001 — the cure names itself
        raise KeyVaultError(
            "no Key Vault credential available — cure: run `az "
            "login` (dev machine) or run inside Fabric (notebook "
            f"token). ({type(e).__name__})") from e


def fetch_secret(vault_url: str, name: str,
                 token_provider=None) -> str:
    token = (token_provider or _default_token_provider)()
    req = urllib.request.Request(
        f"{vault_url.rstrip('/')}/secrets/{name}?api-version=7.4",
        headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return str(json.loads(r.read().decode()).get("value", ""))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise KeyVaultError(
                f"secret {name!r} not found in {vault_url} — cure: "
                "create it (az keyvault secret set --vault-name "
                f"<vault> --name {name} --value <secret>)") from e
        if e.code in (401, 403):
            raise KeyVaultError(
                f"access to {vault_url} refused ({e.code}) — cure: "
                "grant your identity the Key Vault Secrets User "
                "role (or an access policy with secret GET), then "
                "retry") from e
        raise KeyVaultError(
            f"Key Vault answered {e.code} for {name!r} — check the "
            "vault URL and network reach") from e
    except urllib.error.URLError as e:
        raise KeyVaultError(
            f"could not reach {vault_url} — check the URL and "
            f"network/VPN ({e.reason})") from e


def resolve_config_secrets(raw: dict, token_provider=None) -> dict:
    """Walk the loaded org_config; every "keyvault:<name>" string
    resolves through the `key_vault:` block's vault. Refs with NO
    vault block fail loudly naming the cure; configs without refs
    pass through untouched (and no vault is ever contacted)."""
    vault_url = str(((raw.get("key_vault") or {}).get("url")
                     or "")).strip()

    refs: "list[str]" = []

    def walk(node, resolve: bool):
        if isinstance(node, dict):
            return {k: walk(v, resolve) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, resolve) for v in node]
        if isinstance(node, str) and node.startswith(PREFIX):
            name = node[len(PREFIX):].strip()
            refs.append(name)
            if resolve:
                return fetch_secret(vault_url, name, token_provider)
        return node

    if not vault_url:
        walk(raw, resolve=False)
        if refs:
            raise KeyVaultError(
                "config references Key Vault secrets "
                f"({', '.join(sorted(set(refs))[:4])}) but has no "
                "key_vault: block — cure: add\n  key_vault:\n"
                "    url: https://<vault>.vault.azure.net")
        return raw
    return walk(raw, resolve=True)
