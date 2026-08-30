# The Estate X-Ray — engagement runbook

Fixed-price, one-shot, entirely in the customer's tenant. The
report is the deliverable; the engine is removable after. Plain
steps (an admin executes; each step names what you should see).

## Prerequisites (customer admin, ~15 minutes)
1. A Fabric workspace on active capacity, with permission to
   import notebooks and create a lakehouse.
2. A read-only connection to the SQL estate to be x-rayed
   (gateway or direct — the extractor's three profiles all work).
3. The engagement wheel (.whl) received from the vendor.

## The engagement (one session, ~half a day wall-clock)
1. Create workspace `xray-<customer>` → import the pipeline
   notebooks → attach the wheel to the environment.
   You should see: the environment publishes green.
2. Fill `org_config.yaml` (org name, SQL connection, domain
   filter). No secrets in files — Key Vault refs are supported
   (`keyvault:<name>`).
3. Run 100→300 (harvest → parse → graph). You should see: the
   parse-rate cell (their real number) and graph tables landing.
4. Run 500 (validate) then the sweep rides 300 — flags land as
   `cluster:` nodes. You should see: the flag count.
5. Run the report: `python devtools/run_xray.py "<Customer>"`.
   You should see: `XRAY_REPORT.md` — their counts, their flags
   with members and code basis, the AI-readiness verdict.
6. Deliver the report into THEIR document estate (the artifact
   lands; the chat never existed). Walk the verdict page.
7. Close-out choice: leave the engine dormant (capacity paused)
   or remove the workspace. Either honors the one-shot promise.

## The last page is the order form
The report ends with the Bridge pitch: the same engine,
continuous, every write approved by their people. Pricing:
per the current listing sheet (X-Ray price = Sunny's parked
call).
