# ruff: noqa: E402 — a notebook source: every cell imports what
# it uses, so each cell runs alone (the notebook law).
# notebook_work_wheel.py — THE WORK NOTEBOOK, whole and clean
# (2026-10-08, the naming law + D14; requires wheel 0.8.0+).
#
# This file is the SOURCE OF TRUTH for the tenant notebook.
# Push it to Fabric with one command from the home repo
# (browser sign-in, your hand; lakehouse/environment
# attachments are preserved):
#
#   python3.11 sync_notebook.py \
#       --workspace <workspace-id> --notebook <notebook-item-id> \
#       --source notebook_work_wheel.py
#
# Cells are separated by "# %%". SETUP cells run once per tenant
# (or when inputs change); RUN cells are the repeatable batch.
# THE SEQUENCE LAW (ruled 2026-10-08): run cells in order; any
# FAIL stops the session — fix it, re-run that cell, only then
# proceed. Never run a later cell past a failing earlier one.

# %%
# SETUP A — the lakehouse folders (once). 01-03 are YOURS to
# fill; 04_run is the ENGINE's (delete it = clean slate).
import os

for folder in ("01_sql_input", "02_dictionary", "03_tmdl",
               "04_run"):
    os.makedirs("/lakehouse/default/Files/" + folder,
                exist_ok=True)
print("folders ready")

# %%
# SETUP B — pull the TMDL from DevOps into 03_tmdl (re-run any
# time; overwrites by name). Fill the <placeholders>; the PAT
# is a password — scrub it back to PASTE-PAT-HERE after the run.
import io
import os
import shutil
import zipfile

import requests

ORG, PROJECT, REPO = "<org>", "<project>", "<repo>"
BRANCH = "main"
FOLDERS = ["<repo folder>"]  # or ["/"] = whole repo
PAT = "PASTE-PAT-HERE"
TMDL = "/lakehouse/default/Files/03_tmdl"

url = (f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/git/"
       f"repositories/{REPO}/items")
os.makedirs(TMDL, exist_ok=True)
n = 0
for folder in FOLDERS:
    r = requests.get(url, auth=("", PAT), params={
        "path": folder, "$format": "zip", "download": "true",
        "versionDescriptor.version": BRANCH,
        "api-version": "7.1"})
    r.raise_for_status()
    tmp = "/tmp/devops_tmdl"
    shutil.rmtree(tmp, ignore_errors=True)
    zipfile.ZipFile(io.BytesIO(r.content)).extractall(tmp)
    for root, dirs, _ in os.walk(tmp):
        for d in list(dirs):
            if d.endswith(".SemanticModel"):
                dst = os.path.join(TMDL, d)
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(os.path.join(root, d), dst)
                n += 1
    print(f"{folder}: done")
print("semantic models landed:", n)

# %%
# SETUP C — the dictionary: fold the zc batches into the value
# csv, then convert all csvs to the four json files. RUN ONCE
# per fresh extraction upload — a rerun doubles the zc rows.
import csv
import glob
import sys

folder = "/lakehouse/default/Files/02_dictionary/"


def rd(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


value = rd(folder + "dict_extract_value.csv")
added = 0
for p in sorted(glob.glob(folder + "dict_extract_value_zc*.csv")):
    rows = rd(p)
    if rows and rows[0] == value[0]:
        rows = rows[1:]
    assert all(len(r) == 3 for r in rows), f"bad rows in {p}"
    value += rows
    added += len(rows)
with open(folder + "dict_extract_value.csv", "w",
          newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(value)
print("zc rows folded in:", added)
sys.path.append(folder)
import csv_to_json

csv_to_json.convert(folder, folder)

# %%
# SETUP D — sql input hygiene, part 1: ENCODING. Generate
# Scripts' default "Unicode" is UTF-16 and the engine refuses
# it; ANSI brings cp1252 bytes. Safe to re-run — clean files
# are skipped.
import codecs
import os

folder = "/lakehouse/default/Files/01_sql_input/"
fixed = 0
for n in sorted(os.listdir(folder)):
    if not n.endswith(".sql"):
        continue
    with open(folder + n, "rb") as f:
        raw = f.read()
    if raw.startswith(codecs.BOM_UTF16_LE) \
            or raw.startswith(codecs.BOM_UTF16_BE):
        text = raw.decode("utf-16")
    elif raw.startswith(codecs.BOM_UTF8):
        text = raw.decode("utf-8-sig")
    else:
        try:
            raw.decode("utf-8")
            continue
        except UnicodeDecodeError:
            text = raw.decode("cp1252")
    with open(folder + n, "w", encoding="utf-8") as f:
        f.write(text)
    fixed += 1
print("converted:", fixed, "files")

# %%
# SETUP E — sql input hygiene, part 2: NAMES. The file name
# minus .sql is the identity everywhere downstream; clean it
# BEFORE a file's first paid run. Only touches fresh Generate
# Scripts output (Schema.Object.ObjectType.sql) — safe to
# re-run, clean files untouched, dots inside object names kept.
import os

folder = "/lakehouse/default/Files/01_sql_input/"
TAILS = (".StoredProcedure.sql", ".View.sql")
renamed = 0
for n in sorted(os.listdir(folder)):
    tail = next((t for t in TAILS if n.endswith(t)), None)
    if tail is None:
        continue
    core = n[: -len(tail)]
    new = (core.split(".", 1)[1] if "." in core else core) \
        + ".sql"
    assert not os.path.exists(folder + new), \
        f"would collide: {n} -> {new}"
    os.rename(folder + n, folder + new)
    renamed += 1
print("renamed", renamed, "file(s)")

# %%
# RUN 1 — the key, from the vault (the only form on a customer
# tenant). A missing or failed key stops everything downstream:
# the preflight refuses, nothing is delivered (ruled 2026-10-08).
import os

from notebookutils import credentials

os.environ["OPENAI_API_KEY"] = credentials.getSecret(
    "https://<vault-name>.vault.azure.net/",
    "ai01-openai-key")
print("key loaded:", bool(os.environ["OPENAI_API_KEY"]))

# %%
# RUN 2 — the preflight. Must end "/ 0 fail"; every FAIL line
# names its own fix. A FAIL stops the session: fix, re-run this
# cell, only then proceed.
import sqldesc_cli

sqldesc_cli.preflight(
    "/lakehouse/default/Files/03_tmdl",
    "/lakehouse/default/Files/01_sql_input",
    "/lakehouse/default/Files/04_run",
    dict_dir="/lakehouse/default/Files/02_dictionary")

# %%
# RUN 3 — the sweep (free; before the FIRST paid run on a new
# corpus, and again after adding files). K = 0: go on. K > 0:
# send 04_run/11_construct_census_output.json home; a new wheel
# rules the constructs in, then continue.
import sqldesc_cli

census = sqldesc_cli.sweep(
    "/lakehouse/default/Files/01_sql_input",
    "/lakehouse/default/Files/04_run",
    dict_dir="/lakehouse/default/Files/02_dictionary")

# %%
# RUN 4 — BUILD (free, whole corpus): parse every sql file,
# technical descriptions, report links, the 13 stamp. Run when
# the input folders change; the describe cell refuses if you
# forget ("the build is stale: run the build cell first").
import sqldesc_cli

sqldesc_cli.build(
    "/lakehouse/default/Files/03_tmdl",
    "/lakehouse/default/Files/01_sql_input",
    "/lakehouse/default/Files/04_run",
    dict_dir="/lakehouse/default/Files/02_dictionary")

# %%
# RUN 5 — DESCRIBE (paid, the batch): the next 10 new files go
# to the LLM; cards + terms + the ledger + the delivery. Quiet
# minutes = paid calls working. Re-run until "0 remain".
import sqldesc_cli

delivery = sqldesc_cli.describe(
    "/lakehouse/default/Files/03_tmdl",
    "/lakehouse/default/Files/01_sql_input",
    "/lakehouse/default/Files/04_run",
    dict_dir="/lakehouse/default/Files/02_dictionary",
    max_new=10)  # the batch cap; omit to take everything new

# %%
# RUN 6 — the eye: the human twin of the delivery. Entries are
# PAID FILES ONLY; a report lists files_described and
# files_waiting — Collibra waits until waiting is empty.
print(open("/lakehouse/default/Files/04_run/"
           "12_ai_delivery_output.txt").read()[:4000])

# %%
# ANSWER — the data owner's hand only (D15): rule on a number
# the delivery says it is AWAITING. "show" = the number may
# appear; "omit" = the card must speak without it. To GIVE IT
# A MEANING instead: add the inline comment in the SQL itself
# and re-run BUILD + DESCRIBE — the SQL is the one meaning
# store. After show/omit, re-run DESCRIBE: exactly that card
# re-proposes, nothing else pays.
import business_descriptions as bd

bd.answer("/lakehouse/default/Files/04_run/"
          "07_business_descriptions",
          "<node_id>", "<number>", "show")

# %%
# BLESS — the data owner's hand only (edit the placeholders,
# then run; blessings land in
# 04_run/07_business_descriptions/
# 07_business_descriptions_blessings_output.json and survive
# every rerun).
import business_terms as bt

bt.bless("/lakehouse/default/Files/04_run",
         "/lakehouse/default/Files/04_run/"
         "07_business_descriptions",
         "<node_id>", "<report name>",
         "RULED <date> (<the blesser>): <the ruling>")
