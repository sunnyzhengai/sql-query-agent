# sync_files.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/04_fabric_move.md (M02's transport; the
#           local-stays-truth refresh story, decision 6)
# Contract: AIVIA_01_Design/04_fabric_move_data_contract.md (the Files
#           paths are the TRANSPORT the notebook reads — Delta-only
#           ruling stands; Files are the load's input, never the archive)
# Tests:    AIVIA_01_Test/test_04_fabric_move_data_contract.py (grows a
#           sync section, RED first)
#
# PURPOSE. Upload the local asset files (the truth) to the lakehouse
# Files paths — including the two big sheets (254MB column.json, 1.1GB
# value sidecar) that make portal uploads tedious. One command, Sunny's
# hand, same sign-in pattern as sync_wheel.
#
# THE FILE LIST (a module constant, pinned by test — exactly what the
# M02 notebook reads, nothing more):
#   from AIVIA_01_Data/02_emr_data_dictionary/ ->
#        Files/Data/02_emr_data_dictionary/:
#     02_emr_data_dictionary_extraction_table.json
#     02_emr_data_dictionary_extraction_column.json        (~254 MB)
#     02_emr_data_dictionary_extraction_join.json
#     02_emr_data_dictionary_extraction_value.json
#     02_emr_data_dictionary_extraction_value_embeddings.json (~1.1 GB)
#     02_no_dictionary_match.json
#   from AIVIA_01_Data/03_chat_bot/ -> Files/Data/03_chat_bot/:
#     03_chat_technical_terms.md
#     03_chat_abstract_names.json
#
# THE COMMAND (ids are parameters, never in code; lakehouse id is in
# the portal URL when AIVIA_01_LH is open):
#   /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_files.py \
#       --workspace <workspace-id> --lakehouse <lakehouse-id> \
#       [--tenant <tenant-id>] [--force]
#
# HOW IT UPLOADS (OneLake speaks the ADLS Gen2 protocol; standard
# library only, the sync_wheel pattern):
#   - sign-in: the same PKCE browser flow as sync_wheel — ONE shared
#     function; sync_wheel.sign_in gains a scope parameter (default
#     the Fabric API scope; this script passes the Azure Storage scope
#     "https://storage.azure.com/.default", which OneLake requires).
#     Token in memory for this run only.
#   - per file, against
#     https://onelake.dfs.fabric.microsoft.com/<workspace-id>/
#         <lakehouse-id>/<Files path>:
#       1. PUT  ?resource=file            (create/replace the file)
#       2. PATCH ?action=append&position=<offset>  in 32 MB CHUNKS —
#          the 1.1 GB sidecar streams from disk chunk by chunk, never
#          whole in memory; progress printed per chunk.
#       3. PATCH ?action=flush&position=<total length>
#     Fail loudly on any non-success, OneLake's answer verbatim.
#   - THE ECONOMY RULE: before uploading, HEAD the remote file; if it
#     exists AND its Content-Length equals the local size, SKIP it
#     (printed as skipped). --force uploads everything regardless.
#     Size-equality is the cheap honest check; a content change that
#     keeps the byte count identical is possible in principle — the
#     notebook's golden-count gate and Sunny's census eye are the
#     backstop, and --force is the hammer.
#   - census printed at the end: uploaded (with sizes and seconds),
#     skipped, total bytes moved.
#
# CLAUDE'S TESTS (sync section of test_04, red first; live upload is
# Sunny's hand, not pytest-able):
#   - SYNC_FILES: the constant lists exactly the contract files
#     (eight 02/03; +24 at the 2026-10-04 manifest extension,
#     census scope)
#     with their local dirs and Files destinations.
#   - every listed local file exists on this machine (the truth is
#     present before anyone ships it).
#   - the command refuses to run without --workspace/--lakehouse,
#     naming what is missing.
#   - chunking math: a fake 70 MB length yields offsets 0/32/64 MB
#     with the right sizes; a 0-byte file yields one empty flush.
#   - the skip rule: with an injected remote-size reader, equal size
#     -> skipped, different size -> uploaded, --force -> uploaded.
#   - sync_wheel.sign_in still defaults to the Fabric scope (the
#     refactor cannot change wheel-sync behavior).

import argparse
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from sync_wheel import sign_in

CODE_DIR = Path(__file__).resolve().parent
DATA_DIR = CODE_DIR.parent / "AIVIA_01_Data"

ONELAKE = "https://onelake.dfs.fabric.microsoft.com"
STORAGE_SCOPE = "https://storage.azure.com/.default"
CHUNK = 32 * 1024 * 1024

# The eight contract files the M02 notebook reads — pinned by test.
SYNC_FILES = [
    ("02_emr_data_dictionary",
     "02_emr_data_dictionary_extraction_table.json"),
    ("02_emr_data_dictionary",
     "02_emr_data_dictionary_extraction_column.json"),
    ("02_emr_data_dictionary",
     "02_emr_data_dictionary_extraction_join.json"),
    ("02_emr_data_dictionary",
     "02_emr_data_dictionary_extraction_value.json"),
    ("02_emr_data_dictionary",
     "02_emr_data_dictionary_extraction_value_embeddings.json"),
    ("02_emr_data_dictionary", "02_no_dictionary_match.json"),
    ("03_chat_bot", "03_chat_technical_terms.md"),
    ("03_chat_bot", "03_chat_abstract_names.json"),
    # THE SYNC MANIFEST EXTENSION (2026-10-04, her "go, build
    # step 0" — 04 contract amended first, lock red second,
    # this constant third): the 05/06/07 estate, census scope.
    ("05_semantic_graph",
     "05_contains_edges.json"),
    ("05_semantic_graph",
     "05_discovered_joins.json"),
    ("05_semantic_graph",
     "05_exclusion_ledger.json"),
    ("05_semantic_graph",
     "05_expression_sheet.json"),
    ("05_semantic_graph",
     "05_file_sheet.json"),
    ("05_semantic_graph",
     "05_kind_library.json"),
    ("05_semantic_graph",
     "05_parameter_sheet.json"),
    ("05_semantic_graph",
     "05_predicate_sheet.json"),
    ("05_semantic_graph",
     "05_resolves_edges.json"),
    ("05_semantic_graph",
     "05_scope_sheet.json"),
    ("05_semantic_graph",
     "05_statement_sheet.json"),
    ("05_semantic_graph",
     "05_structure_sheet.json"),
    ("06_technical_descriptions",
     "06_description_sheet.json"),
    ("06_technical_descriptions",
     "06_voicing_ledger.json"),
    ("06_technical_descriptions",
     "COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS.txt"),
    ("06_technical_descriptions",
     "COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS.svg"),
    ("07_business_descriptions",
     "07_business_sheet.json"),
    ("07_business_descriptions",
     "07_blessing_registry.json"),
    ("07_business_descriptions",
     "07_fact_voices.json"),
    ("07_business_descriptions",
     "07_code_sightings.json"),
    ("07_business_descriptions",
     "07_walk_trace.json"),
    ("07_business_descriptions",
     "07_naming_gaps.json"),
    ("07_business_descriptions",
     "COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS.txt"),
    ("07_business_descriptions",
     "COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS.facts.txt"),
]


def chunk_spans(total, chunk=None):
    chunk = chunk or CHUNK  # resolved at call time, so tests can shrink it
    return [(offset, min(chunk, total - offset))
            for offset in range(0, total, chunk)]


def should_upload(local_size, remote_size, force):
    if force:
        return True
    return remote_size != local_size


def _onelake(token, method, path, body=b"", extra_headers=None):
    req = urllib.request.Request(
        f"{ONELAKE}/{path}", data=body, method=method,
        headers={"Authorization": f"Bearer {token}",
                 "x-ms-version": "2021-10-04",
                 **(extra_headers or {})})
    # 300s hard timeout: a 32MB chunk on a slow uplink fits; a hung
    # connection fails fast into the retry (the Errno-60 class, fixed
    # across sync_wheel AND here in one pass — enumerate-all-cases).
    with urllib.request.urlopen(req, timeout=300) as resp:
        return dict(resp.headers)


def _onelake_retry(token, method, path, body=b"", extra_headers=None,
                   what="", attempts=3):
    """Transient NETWORK errors retry; OneLake's own HTTP answers
    (HTTPError) stay loud — a position-mismatch after a half-landed
    chunk must surface, not loop."""
    for attempt in range(1, attempts + 1):
        try:
            return _onelake(token, method, path, body, extra_headers)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"    network blip on {what} ({e}) — "
                  f"retry {attempt}/{attempts}")
            if attempt == attempts:
                raise SystemExit(
                    f"the network kept failing on {what}; rerun the "
                    "command — this file restarts from its first chunk")
            time.sleep(5)


def _loud(e, what):
    raise SystemExit(
        f"OneLake said no to {what} (HTTP {e.code}):\n"
        f"{e.read().decode(errors='replace')}")


def remote_size(token, workspace, lakehouse, dest):
    path = urllib.parse.quote(f"{workspace}/{lakehouse}/{dest}")
    try:
        headers = _onelake(token, "HEAD", path)
        return int(headers.get("Content-Length", 0))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        _loud(e, f"HEAD {dest}")


def upload_file(token, workspace, lakehouse, dest, local_path):
    path = urllib.parse.quote(f"{workspace}/{lakehouse}/{dest}")
    total = local_path.stat().st_size
    try:
        _onelake_retry(token, "PUT", f"{path}?resource=file",
                       what=f"create {dest}")
        with open(local_path, "rb") as f:
            for offset, size in chunk_spans(total):
                _onelake_retry(
                    token, "PATCH",
                    f"{path}?action=append&position={offset}",
                    body=f.read(size),
                    extra_headers={
                        "Content-Type": "application/octet-stream"},
                    what=f"chunk at {offset:,} of {dest}")
                print(f"    …{offset + size:,} / {total:,} bytes")
        _onelake_retry(token, "PATCH",
                       f"{path}?action=flush&position={total}",
                       what=f"flush {dest}")
    except urllib.error.HTTPError as e:
        _loud(e, f"upload {dest}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Upload the local asset files (the truth) to the "
        "lakehouse Files paths the M02 notebook reads. Ids are in the "
        "portal URL when AIVIA_01_LH is open: "
        ".../groups/<workspace-id>/lakehouses/<lakehouse-id>")
    parser.add_argument("--workspace", required=True,
                        help="Fabric workspace id")
    parser.add_argument("--lakehouse", required=True,
                        help="Lakehouse item id")
    parser.add_argument("--tenant", default="organizations",
                        help="Entra tenant id (default: asked at sign-in)")
    parser.add_argument("--force", action="store_true",
                        help="upload everything, skip nothing")
    args = parser.parse_args(argv)

    token = sign_in(args.tenant, scope=STORAGE_SCOPE)

    uploaded = skipped = moved = 0
    for subdir, name in SYNC_FILES:
        local = DATA_DIR / subdir / name
        if not local.exists():
            raise SystemExit(f"missing local truth: {local}")
        dest = f"Files/Data/{subdir}/{name}"
        size = local.stat().st_size
        remote = remote_size(token, args.workspace, args.lakehouse, dest)
        if not should_upload(size, remote, args.force):
            print(f"skipped (same {size:,} bytes remotely): {name}")
            skipped += 1
            continue
        print(f"uploading {name} ({size:,} bytes)…")
        started = time.monotonic()
        upload_file(token, args.workspace, args.lakehouse, dest, local)
        print(f"  done in {time.monotonic() - started:.0f}s")
        uploaded += 1
        moved += size
    print(f"\nsync census: {uploaded} uploaded ({moved:,} bytes), "
          f"{skipped} skipped — {len(SYNC_FILES)} files total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
