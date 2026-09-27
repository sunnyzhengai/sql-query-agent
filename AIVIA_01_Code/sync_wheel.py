# sync_wheel.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:  AIVIA_01_Design/01_subject_sql_files.md — "Packages arrive in
#          Fabric via a Fabric Environment item" — this script is the local
#          automation of that arrival: build the wheel, upload it to the
#          Environment item, publish. Ruled 2026-09-26: automation runs by
#          Sunny's hand (one command), never on a timer or a git push.
#
# WHAT MUST EXIST FIRST (one-time, Sunny's hand, in the Fabric portal):
#   - the workspace for AIVIA_01
#   - an Environment item in it (the design doc's pinned openai==3.19.2
#     goes in its public libraries, set once in the portal)
#   The script never creates these — creating Fabric items is capacity
#   and stays with Sunny.
#
# THE WHEEL (new, rides this step):
#   AIVIA_01_Code/pyproject.toml — package name aivia01, version 0.1.0,
#   floor python 3.11. It packages the two modules built so far:
#   build_data_sheet and local_chat (the notebook imports build_data_sheet
#   and local_chat's rank/answer functions; the web layer just comes along).
#   Version bumps by hand in pyproject.toml when code changes — Fabric
#   replaces a staged library by file name, so the file name stays
#   aivia01-<version>-py3-none-any.whl.
#
# THE COMMAND (all ids are PARAMETERS — never written inside the code):
#   /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_wheel.py \
#       --workspace <workspace-id> --environment <environment-id> \
#       [--tenant <tenant-id>]
#   Workspace and environment ids come from the Fabric portal URL when the
#   Environment item is open (the script prints where to look if missing).
#   --tenant defaults to "organizations" (the sign-in step then asks which
#   tenant); passing your tenant id skips that question.
#
# PSEUDO CODE
#
# Step 1 — build the wheel.
#     Run: python -m build --wheel AIVIA_01_Code/  (the `build` package,
#     already on the one Python). Take the newest .whl from
#     AIVIA_01_Code/dist/. Print its name and size.
#
# Step 2 — sign in (normal browser sign-in, standard library only).
#     RULED 2026-09-27: the original device-code flow is BLOCKED by the
#     tenant's security defaults (error 530035, first real run) — device
#     codes are a phishing vector and Entra refuses them. Security
#     defaults stay ON; the script adapts, not the tenant.
#     The flow now: the script opens the browser to the Microsoft
#     sign-in page; Sunny signs in the normal way (same as the Fabric
#     portal); Microsoft sends the browser back to a one-time localhost
#     address where the script is listening, and the script trades that
#     answer for a Fabric API token. Standard library only, token held
#     in memory for this run only, nothing stored on disk.
#     (A service principal / GitHub Actions variant can come later; this
#     step is the by-Sunny's-hand version.)
#
# Step 3 — upload the wheel to the Environment's STAGING libraries.
#     POST the .whl bytes to the Fabric REST endpoint:
#       workspaces/<id>/environments/<id>/staging/libraries
#     Staging = uploaded but not live. Uploading the same file name again
#     replaces it. Fail loudly on any non-success answer, printing
#     Fabric's error text verbatim.
#     THE VERSION-COLLISION MECHANISM (ruled 2026-09-27, found at the
#     0.1.0 -> 0.2.0 bump before it could bite): a version bump changes
#     the wheel FILE NAME, so Fabric would keep old and new side by side
#     and the import winner would be luck. Before uploading, the script
#     deletes every OTHER aivia01-*.whl it knows from local dist/ out of
#     the environment's staging (absent ones are fine and skipped) —
#     every sync leaves exactly ONE aivia01 in the environment.
#
# Step 4 — confirm, then publish.
#     Publish rebuilds the environment pool: several minutes, consumes
#     capacity. The script STOPS and asks:
#       "Publish environment now? [y/N]"
#     Only "y" proceeds (the capacity law, enforced in code). "N" leaves
#     the wheel staged — publishable later from the portal.
#
# Step 5 — poll until publish finishes.
#     GET the environment every 30 seconds, print the publish state
#     (running / success / failed). On failed: print Fabric's error
#     verbatim and exit non-zero. On success: print the installed
#     libraries list so Sunny sees aivia01 sitting next to openai 3.19.2.
#
# TESTS (test_01_sync_wheel.py, red first) — what is mechanically pinned:
#   - Step 1 is fully testable: building produces exactly one
#     aivia01-*.whl, and the wheel really contains build_data_sheet and
#     local_chat (unzip and look — a wheel is a zip).
#   - the command refuses to run without --workspace/--environment,
#     naming what is missing.
#   - Steps 2-5 touch the live Fabric service and Sunny's sign-in; they
#     are NOT pytest-able without her hand. Their acceptance test is the
#     first real run: Sunny runs the command, signs in, sees aivia01 in
#     the environment's libraries in the portal. That run is this step's
#     "Sunny validates by eyeballing the artifacts".

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent

FABRIC_API = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
LOGIN_BASE = "https://login.microsoftonline.com"
# Microsoft's well-known PUBLIC client id for the Azure CLI — the standard
# app id for command-line sign-in; it is not a secret and belongs to no tenant.
SIGN_IN_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"

POLL_SECONDS = 30


# --------------------------------------------------------------------------
# Step 1 — build the wheel
# --------------------------------------------------------------------------


def build_wheel(code_dir=CODE_DIR):
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", str(code_dir)],
        check=True,
    )
    wheels = sorted(
        (code_dir / "dist").glob("aivia01-*.whl"), key=lambda p: p.stat().st_mtime
    )
    if not wheels:
        raise FileNotFoundError(f"build finished but no aivia01 wheel in {code_dir}/dist")
    return wheels[-1]


# --------------------------------------------------------------------------
# Step 2 — normal browser sign-in (standard library only)
# --------------------------------------------------------------------------


def _post_form(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data)) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        raise SystemExit(f"sign-in failed: {body.get('error_description', body)}")


class _SignInHandler(BaseHTTPRequestHandler):
    """Catches the single browser redirect that carries the sign-in answer."""

    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        self.server.signin_answer = {k: v[0] for k, v in query.items()}
        page = (
            "<html><body style='font-family:sans-serif'>"
            "<h2>Signed in — you can close this tab and return to the "
            "command window.</h2></body></html>"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def log_message(self, *args):  # keep the terminal clean
        pass


def sign_in(tenant):
    # Proof-of-possession pair (PKCE): a secret made fresh for this run;
    # only the process that STARTED the sign-in can finish it.
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    state = uuid.uuid4().hex

    listener = HTTPServer(("127.0.0.1", 0), _SignInHandler)  # free port
    redirect_uri = f"http://localhost:{listener.server_address[1]}"

    auth_url = f"{LOGIN_BASE}/{tenant}/oauth2/v2.0/authorize?" + urllib.parse.urlencode(
        {
            "client_id": SIGN_IN_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": FABRIC_SCOPE,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
    )
    print("\nopening the browser for Microsoft sign-in…")
    print(f"(if no browser opens, paste this address yourself:\n{auth_url})\n")
    webbrowser.open(auth_url)

    listener.handle_request()  # waits for the one redirect back
    answer = getattr(listener, "signin_answer", {})
    listener.server_close()

    if answer.get("error"):
        raise SystemExit(
            f"sign-in failed: {answer.get('error_description', answer['error'])}"
        )
    if answer.get("state") != state or "code" not in answer:
        raise SystemExit("sign-in failed: the browser's answer did not match this run")

    token = _post_form(
        f"{LOGIN_BASE}/{tenant}/oauth2/v2.0/token",
        {
            "grant_type": "authorization_code",
            "client_id": SIGN_IN_CLIENT_ID,
            "code": answer["code"],
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
    )
    print("signed in")
    return token["access_token"]


# --------------------------------------------------------------------------
# Steps 3-5 — Fabric REST calls (fail loudly, Fabric's words verbatim)
# --------------------------------------------------------------------------


def _fabric(token, method, path, body=None, content_type=None):
    req = urllib.request.Request(
        f"{FABRIC_API}/{path}", data=body, method=method,
        headers={"Authorization": f"Bearer {token}"},
    )
    if content_type:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"Fabric said no to {method} {path} "
            f"(HTTP {e.code}):\n{e.read().decode(errors='replace')}"
        )


def upload_staging_library(token, workspace, environment, wheel_path):
    boundary = uuid.uuid4().hex
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{wheel_path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    _fabric(
        token, "POST",
        f"workspaces/{workspace}/environments/{environment}/staging/libraries",
        body=head + wheel_path.read_bytes() + tail,
        content_type=f"multipart/form-data; boundary={boundary}",
    )


def stale_wheel_names(current_wheel):
    """Every OTHER aivia01 wheel in dist/ — the file names a version bump
    left behind, which must not linger in the environment."""
    return sorted(
        p.name
        for p in current_wheel.parent.glob("aivia01-*.whl")
        if p.name != current_wheel.name
    )


def delete_staged_library(token, workspace, environment, file_name):
    """Best effort: True if deleted, False if Fabric said no (usually
    'not there', which is exactly the state we want)."""
    try:
        _fabric(
            token, "DELETE",
            f"workspaces/{workspace}/environments/{environment}/staging/libraries"
            f"?libraryToDelete={urllib.parse.quote(file_name)}",
        )
        return True
    except SystemExit:
        return False


def publish(token, workspace, environment):
    _fabric(
        token, "POST",
        f"workspaces/{workspace}/environments/{environment}/staging/publish",
    )


def publish_state(token, workspace, environment):
    env = _fabric(token, "GET", f"workspaces/{workspace}/environments/{environment}")
    details = (env.get("properties") or {}).get("publishDetails") or {}
    return details.get("state", "unknown"), env


def list_libraries(token, workspace, environment):
    return _fabric(
        token, "GET", f"workspaces/{workspace}/environments/{environment}/libraries"
    )


# --------------------------------------------------------------------------
# The command
# --------------------------------------------------------------------------


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the aivia01 wheel, upload it to the Fabric "
        "Environment item, and (after asking) publish. Ids are in the "
        "portal URL when the Environment item is open: "
        ".../groups/<workspace-id>/environments/<environment-id>",
    )
    parser.add_argument("--workspace", required=True, help="Fabric workspace id")
    parser.add_argument("--environment", required=True, help="Environment item id")
    parser.add_argument(
        "--tenant", default="organizations",
        help="Entra tenant id (default: asked during sign-in)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    wheel = build_wheel()
    print(f"\nwheel built: {wheel.name} ({wheel.stat().st_size:,} bytes)")

    token = sign_in(args.tenant)

    for stale in stale_wheel_names(wheel):
        if delete_staged_library(token, args.workspace, args.environment, stale):
            print(f"removed stale wheel from staging: {stale}")

    upload_staging_library(token, args.workspace, args.environment, wheel)
    print(f"staged: {wheel.name} is uploaded (not live until publish)")

    reply = input("Publish environment now? Takes minutes, consumes capacity. [y/N] ")
    if reply.strip().lower() != "y":
        print("left staged — publish later from the portal or rerun this script")
        return 0

    publish(token, args.workspace, args.environment)
    print("publish started")
    while True:
        state, env = publish_state(token, args.workspace, args.environment)
        print(f"  publish state: {state}")
        if state.lower() == "success":
            print("\ninstalled libraries now:")
            print(json.dumps(list_libraries(token, args.workspace, args.environment),
                             indent=2))
            return 0
        if state.lower() in ("failed", "cancelled"):
            print("publish did not succeed — Fabric's answer, verbatim:")
            print(json.dumps(env, indent=2))
            return 1
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
