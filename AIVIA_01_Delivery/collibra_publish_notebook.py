# ruff: noqa: E402 — a notebook source: every cell imports what
# it needs (the notebook_work_wheel precedent)
# collibra_publish_notebook — the Collibra publish, ONE versioned
# file (her rule, 2026-10-10, Brief_Notebook_Import_Law: every
# notebook is importable, never copy-paste). Import the .ipynb
# twin via Fabric "Import notebook", or push with
# sync_notebook.py. Fill the CONFIG cell from tenant_intake.md
# section 4.
#
# THE LAWS this notebook implements:
#   BLESSED-ONLY             unblessed term names never leave
#   CREATE-OR-UPDATE BY NAME re-runs update, never duplicate
#   SANDBOX FIRST            one report + one term into the test
#                            domain before any batch
#   DRY-RUN FIRST            the first run only RESOLVES names
#                            and prints the board; nothing is
#                            written until you read it and flip
#   THE COUNTED CENSUS       every run ends in counted numbers
#
# THE SKIPS (ruled 2026-10-08 + 2026-10-10 evening): a report
# with files_waiting never ships; an awaiting_human description
# never ships; a DELIVERED card ships even with open questions
# or registered findings (her publish-immediately ruling).

# %%
# CONFIG — every value from tenant_intake.md section 4
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

# %%
# AUTH — fill exactly ONE form, run, SCRUB the same sitting
# (paste-interim law: pasted secrets ride cell history and
# screenshots; scrub, then rotate/change what you pasted).
#
# FORM A — an API token from the Collibra admin (SSO shops:
#   the ask is "an API token or service account for the REST
#   2.0 API, read/write on the term + sandbox domains").
# FORM B — your Collibra username + password (works when you
#   sign into Collibra with a password, not only SSO).
# FORM C — vault (when one exists): uncomment, TOKEN_SECRET =
#   the secret's NAME; vault url: portal.azure.com -> search
#   "Key vaults" (banner glitch? "select Simplified View") ->
#   your vault -> Overview -> Vault URI.
import requests

TOKEN    = "PASTE-TOKEN-OR-LEAVE"   # Form A
USERNAME = "PASTE-USER-OR-LEAVE"    # Form B
PASSWORD = "PASTE-PASS-OR-LEAVE"    # Form B

S = requests.Session()
S.headers.update({"Content-Type": "application/json"})
if TOKEN != "PASTE-TOKEN-OR-LEAVE":
    S.headers["Authorization"] = f"Bearer {TOKEN}"
elif USERNAME != "PASTE-USER-OR-LEAVE":
    S.auth = (USERNAME, PASSWORD)
else:
    raise ValueError("fill Form A or Form B above "
                     "(or uncomment Form C)")
# Form C (vault):
# token = notebookutils.credentials.getSecret(
#     "https://<vault-name>.vault.azure.net/", TOKEN_SECRET)
# S.headers["Authorization"] = f"Bearer {token}"
r = S.get(f"{BASE_URL}/rest/2.0/auth/sessions/current")
print("auth:", r.status_code)   # expect 200

# %%
# FINDER — read-only, fills the CONFIG blanks (run after AUTH
# prints 200; added 2026-10-10 at her ask). Domains can also
# be read from the browser: open the domain in Collibra and
# its URL ends /domain/<uuid> — THAT uuid. (A term's own URL
# is /asset/<uuid> — the term's id, NOT the domain's.)
def find(path, name):
    rows = S.get(f"{BASE_URL}/rest/2.0/{path}",
                 params={"name": name,
                         "nameMatchMode": "ANYWHERE",
                         "limit": 10}).json().get("results", [])
    for x in rows:
        print(f"{path:15} | {x['name']:50} | {x['id']}")
    if not rows:
        print(f"{path:15} | (no match for {name!r})")

find("domains", "glossary")   # <- words from YOUR term domain
find("domains", "sandbox")    # <- and your test domain
find("assetTypes", "Business Term")        # -> BT_TYPE_ID
find("assetTypes", "Power BI Report")      # -> REPORT_TYPE_ID
find("attributeTypes", "Description")      # -> DESC_ATTR_ID
find("attributeTypes", "Technical Definition")  # -> TECHDEF

# %%
# LOAD — the delivery file; gather the work. Skips: an
# incomplete report (files_waiting) and an unanswered card
# (awaiting_human) never ship; delivered cards ship even with
# open questions / registered findings (ruled 2026-10-10).
import json

d = json.load(open(DELIVERY_JSON))
pushes = []   # (kind, report, term_name, text, techdef)
for e in d["reports"]:
    if e.get("files_waiting"):
        continue
    if (e.get("description") or {}).get("status") \
            == "awaiting_human":
        continue
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

# %%
# RESOLVE BY NAME — the dry board (law 5.1 automated). READ THE
# BOARD: a report with NO MATCH means Collibra knows it under a
# different name — fix the mapping before writing.
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
                      aid and "EXISTS -> update"
                      or "NEW -> create"))
for row in board:
    print(*row, sep="  |  ")

# %%
# THE WRITES — refuses to run while DRY_RUN
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
assert not DRY_RUN, "DRY_RUN is on — read the board cell first"
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
    except Exception as exc:  # noqa: BLE001 — a failed push is
        # a counted census row, never a dead batch
        census["failures"].append(f"{kind} {report} {term}: "
                                  f"{type(exc).__name__}: {exc}")
print(census)   # THE COUNTED CENSUS — the run's artifact

# %%
# THE EYE — open the sandbox report and term in Collibra. Check:
# the line breaks between the labeled lines survived (if
# flattened, the texts need <br> — say so and the delivery gains
# a renderer switch). Only after that eye: SANDBOX = False,
# re-run the LOAD / RESOLVE / WRITES cells for the batch.
print("the eye: check the sandbox assets in Collibra, then "
      "SANDBOX = False and re-run LOAD -> RESOLVE -> WRITES")
