"""THE LIVE-WIRE TOGGLE (Design_Chatbot.md rider, ruled by Sunny
2026-09-12 — "where is the graph db? is it still faking it?"):
the console's displayed GQL executes against the SERVED Fabric
graph on demand. Local execution stays the answer path (the
execution-locality default, until M11/M12); the wire lays the
served rows BESIDE the local ones as per-round evidence.

The wire is the documented public contract (GQL Query HTTP API,
public preview): POST /v1/workspaces/{ws}/GraphModels/{gm}/
executeQuery?preview=true with a bearer token for resource
api.fabric.microsoft.com and body {"query": ...}; a typed TABLE
comes back; success = status codes with 00/01/02/03 prefixes,
anything else renders code + description verbatim (the
error-contract). Config rides the environment — the token is
NEVER stored by the console. Unconfigured = the toggle reports
DISABLED with its reason (the seat-down banner law).

Tests inject a scripted transport (the doubles law) — the live
wire fires only by Sunny's hand, one capacity spend per query,
counted visibly.
"""
import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

FABRIC_RESOURCE = "https://api.fabric.microsoft.com"
_ENDPOINT = (FABRIC_RESOURCE + "/v1/workspaces/{ws}/GraphModels/"
             "{gm}/executeQuery?preview=true")
# GQL status classes 00-03 are success (00 complete · 01 warning ·
# 02 no data · 03 information) — everything else is an error
_SUCCESS_PREFIXES = ("00", "01", "02", "03")  # literal: mechanical

WORKSPACE_VAR = "AISQL_FABRIC_WORKSPACE"
GRAPH_MODEL_VAR = "AISQL_FABRIC_GRAPH_MODEL"
TOKEN_VAR = "AISQL_FABRIC_TOKEN"

# transport contract: (url, headers, body_bytes) -> (http_status,
# response_body_text); tests script it, production speaks HTTP
Transport = Callable[[str, Dict[str, str], bytes], Tuple[int, str]]


def _http_transport(url: str, headers: Dict[str, str],
                    body: bytes) -> Tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers=headers,
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


def az_token() -> str:
    """One user-delegated token from the az CLI (the documented
    path: az account get-access-token --resource api.fabric...).
    Held in memory only — the console never writes it anywhere."""
    out = subprocess.run(
        # literal: mechanical
        ["az", "account", "get-access-token",
         "--resource", FABRIC_RESOURCE, "-o", "json"],
        capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError("az token fetch failed: "
                           + out.stderr.strip()[:200])
    return str(json.loads(out.stdout)["accessToken"])


class FabricGraphWire:
    """Executes GQL against one served graph model. Stateless per
    the API contract; the token provider is called lazily and the
    token lives only in this object's memory."""

    def __init__(self, workspace_id: str, graph_model_id: str,
                 token_provider: Callable[[], str],
                 transport: Optional[Transport] = None) -> None:
        self.url = _ENDPOINT.format(ws=workspace_id,
                                    gm=graph_model_id)
        self._token_provider = token_provider
        self._transport = transport or _http_transport
        self._token: Optional[str] = None

    def execute(self, gql: str) -> Dict[str, Any]:
        """One query = one capacity spend. Returns the normalized
        outcome — never raises on application errors (they render
        verbatim per the error-contract)."""
        if self._token is None:
            try:
                self._token = self._token_provider()
            except Exception as err:  # noqa: BLE001 — seat-down law
                # literal: shape
                return {"ok": False, "code": "token",
                        "description": str(err), "columns": [],
                        "rows": [], "row_count": 0}
        # literal: mechanical
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json",
                   "Authorization": "Bearer " + self._token}
        body = json.dumps({"query": gql}).encode("utf-8")
        try:
            http_status, text = self._transport(self.url, headers,
                                                body)
        except Exception as err:  # noqa: BLE001 — seat-down law
            # literal: shape
            return {"ok": False, "code": "transport",
                    "description": str(err), "columns": [],
                    "rows": [], "row_count": 0}
        if http_status == 401:
            # one refresh on an expired token, then honest failure
            self._token = None
            try:
                self._token = self._token_provider()
            except Exception as err:  # noqa: BLE001
                # literal: shape
                return {"ok": False, "code": "token",
                        "description": str(err), "columns": [],
                        "rows": [], "row_count": 0}
            headers["Authorization"] = "Bearer " + self._token
            http_status, text = self._transport(self.url, headers,
                                                body)
        if http_status != 200:
            # literal: shape
            return {"ok": False, "code": f"http {http_status}",
                    "description": text[:300], "columns": [],
                    "rows": [], "row_count": 0}
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as err:
            # literal: shape
            return {"ok": False, "code": "decode",
                    "description": str(err), "columns": [],
                    "rows": [], "row_count": 0}
        status = payload.get("status") or {}
        code = str(status.get("code") or "")
        if not code.startswith(_SUCCESS_PREFIXES):
            # literal: shape
            return {"ok": False, "code": code,
                    "description": str(status.get("description")
                                       or ""),
                    "columns": [], "rows": [], "row_count": 0}
        result = payload.get("result") or {}
        columns = [str(c.get("name") or "")
                   for c in (result.get("columns") or [])]
        rows = list(result.get("data") or [])
        # literal: shape
        return {"ok": True, "code": code,
                "description": str(status.get("description") or ""),
                "columns": columns, "rows": rows,
                "row_count": len(rows)}


def from_env(env: Optional[Dict[str, str]] = None,
             token_fetch: Callable[[], str] = az_token,
             transport: Optional[Transport] = None,
             ) -> Tuple[Optional[FabricGraphWire], str]:
    """(wire, reason). No wire = the toggle renders DISABLED with
    the reason — the seat-down banner law, never a silent local
    fallback pretending to be the served graph."""
    e = os.environ if env is None else env
    ws = (e.get(WORKSPACE_VAR) or "").strip()
    gm = (e.get(GRAPH_MODEL_VAR) or "").strip()
    if not ws or not gm:
        missing = [v for v, val in ((WORKSPACE_VAR, ws),
                                    (GRAPH_MODEL_VAR, gm))
                   if not val]
        return None, ("live wire disabled: set "
                      + " and ".join(missing)
                      + " (ids from the AISQL_GRAPH_MODEL item; "
                      "see docs/deployment/FABRIC_GRAPH_LOAD.md)")
    token_env = (e.get(TOKEN_VAR) or "").strip()
    provider = (lambda: token_env) if token_env else token_fetch
    return (FabricGraphWire(ws, gm, provider, transport=transport),
            "")


def run_round(wire: FabricGraphWire,
              result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fire the round's displayed GQL — the exact artifact strings,
    nothing re-planned — one spend per query. The comparison line
    is claimed ONLY where it is honest: a single query beside a
    local rows table; otherwise each block reports its own served
    count as evidence without a verdict."""
    gql = [g for g in (result.get("gql") or []) if g]
    local_rows = result.get("rows") or []
    comparable = len(gql) == 1 and bool(local_rows)
    blocks: List[Dict[str, Any]] = []
    for g in gql:
        outcome = wire.execute(g)
        block = {"gql": g, **outcome}
        if comparable and outcome["ok"]:
            block["local_count"] = len(local_rows)
            block["verdict"] = ("MATCH" if outcome["row_count"]
                                == len(local_rows) else "DIVERGE")
        blocks.append(block)
    return blocks
