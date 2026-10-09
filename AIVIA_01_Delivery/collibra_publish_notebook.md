# Collibra Publish Notebook — the template

Copy each cell into a Fabric notebook on the tenant. Fill the
CONFIG cell from `tenant_intake.md` section 4. The laws it
implements: BLESSED-ONLY (unblessed term names never leave),
CREATE-OR-UPDATE BY NAME (re-runs update, never duplicate),
SANDBOX FIRST (one report + one term into the test domain
before any batch), and THE COUNTED CENSUS at the end.

DRY_RUN starts True: the first run only RESOLVES names and
prints what WOULD happen — nothing is written until you read
that board and flip it.

## Cell 1 — CONFIG (every value from the intake sheet)

```python
BASE_URL        = "____"   # Collibra instance base URL
TOKEN_SECRET    = "____"   # secret name holding the API token
BT_DOMAIN_ID    = "____"   # Business Term DOMAIN id
BT_TYPE_ID      = "____"   # Business Term ASSET TYPE id
DESC_ATTR_ID    = "____"   # description ATTRIBUTE TYPE id
TECHDEF_ATTR_ID = "____"   # technical-definition ATTRIBUTE TYPE id
REPORT_TYPE_ID  = "____"   # Power BI report ASSET TYPE id
SANDBOX_DOMAIN  = "____"   # test domain id (the one-row rehearsal)

DELIVERY_JSON = ("/lakehouse/default/Files/04_run/"
                 "12_ai_delivery_output.json")
DRY_RUN  = True    # resolve + print only; flip AFTER reading
SANDBOX  = True    # True = write terms into SANDBOX_DOMAIN,
                   # limit to ONE report + ONE term (law 5.2)
```

## Cell 2 — auth (the token from a secret, never a literal)

```python
import requests
token = notebookutils.credentials.getSecret("____vault_url____",
                                            TOKEN_SECRET)
S = requests.Session()
S.headers.update({"Authorization": f"Bearer {token}",
                  "Content-Type": "application/json"})
r = S.get(f"{BASE_URL}/rest/2.0/auth/sessions/current")
print("auth:", r.status_code)   # expect 200
```

## Cell 3 — load the delivery file; gather the work

```python
import json
d = json.load(open(DELIVERY_JSON))
pushes = []   # (kind, report, term_name, text, techdef)
for e in d["reports"]:
    if e.get("files_waiting"):   # ruled 2026-10-08: an
        continue                 # incomplete report never ships
    desc = e.get("description") or {}
    if desc.get("text"):
        pushes.append(("report_desc", e["report"], None,
                       desc["text"], None))
    for t in e.get("terms", []):
        if t.get("bt_name_status") == "blessed":  # the law
            pushes.append(("term", e["report"], t["bt_name"],
                           t["business_description"],
                           t["technical_definition"]))
if SANDBOX:
    pushes = ([p for p in pushes if p[0] == "report_desc"][:1]
              + [p for p in pushes if p[0] == "term"][:1])
print(len(pushes), "push item(s)",
      "(SANDBOX: 1+1)" if SANDBOX else "(full batch)")
```

## Cell 4 — RESOLVE BY NAME (the dry board; law 5.1 automated)

```python
def find_asset(name, type_id, domain_id=None):
    params = {"name": name, "nameMatchMode": "EXACT",
              "typeIds": type_id, "limit": 2}
    if domain_id:
        params["domainId"] = domain_id
    hits = S.get(f"{BASE_URL}/rest/2.0/assets",
                 params=params).json().get("results", [])
    return hits[0]["id"] if len(hits) == 1 else None

board = []
term_domain = SANDBOX_DOMAIN if SANDBOX else BT_DOMAIN_ID
for kind, report, term, text, techdef in pushes:
    if kind == "report_desc":
        aid = find_asset(report, REPORT_TYPE_ID)
        board.append((kind, report, aid and "MATCH" or
                      "NO MATCH -> name-mapping needed"))
    else:
        aid = find_asset(term, BT_TYPE_ID, term_domain)
        board.append((kind, term,
                      aid and "EXISTS -> update" or "NEW -> create"))
for row in board:
    print(*row, sep="  |  ")
```

READ THE BOARD. A report with NO MATCH means Collibra knows it
under a different name — fix the mapping before writing.

## Cell 5 — THE WRITES (refuses to run while DRY_RUN)

```python
def set_attribute(asset_id, attr_type_id, value):
    hits = S.get(f"{BASE_URL}/rest/2.0/attributes",
                 params={"assetId": asset_id,
                         "typeIds": attr_type_id}
                 ).json().get("results", [])
    if hits:   # update in place — idempotent re-runs
        return S.patch(
            f"{BASE_URL}/rest/2.0/attributes/{hits[0]['id']}",
            json={"value": value})
    return S.post(f"{BASE_URL}/rest/2.0/attributes",
                  json={"assetId": asset_id,
                        "typeId": attr_type_id, "value": value})

census = {"reports_updated": 0, "terms_created": 0,
          "terms_updated": 0, "failures": []}
assert not DRY_RUN, "DRY_RUN is on — read Cell 4's board first"
for kind, report, term, text, techdef in pushes:
    try:
        if kind == "report_desc":
            aid = find_asset(report, REPORT_TYPE_ID)
            if not aid:
                raise LookupError(f"no asset: {report}")
            set_attribute(aid, DESC_ATTR_ID, text)
            census["reports_updated"] += 1
        else:
            aid = find_asset(term, BT_TYPE_ID, term_domain)
            if aid:
                census["terms_updated"] += 1
            else:
                aid = S.post(f"{BASE_URL}/rest/2.0/assets",
                             json={"name": term,
                                   "domainId": term_domain,
                                   "typeId": BT_TYPE_ID}
                             ).json()["id"]
                census["terms_created"] += 1
            set_attribute(aid, DESC_ATTR_ID, text)
            set_attribute(aid, TECHDEF_ATTR_ID, techdef)
    except Exception as exc:
        census["failures"].append(f"{kind} {report} {term}: "
                                  f"{type(exc).__name__}: {exc}")
print(census)   # THE COUNTED CENSUS — the run's artifact
```

## Cell 6 — the eye

Open the sandbox report and term in Collibra. Check: the line
breaks between the labeled lines survived (if flattened, the
texts need `<br>` — say so and the delivery gains a renderer
switch). Only after that eye: SANDBOX = False, re-run Cells
3-5 for the batch.
