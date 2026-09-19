# SOP_Environment_Preflight — prove the environment BEFORE any build

**Purpose: no trial and error. Anyone new runs the battery below,
records what each step said, and the verdict table names the route.
Every step is a cheap check or a per-user action; nothing here
installs AIVIA itself. All of it runs on the target machine or
tenant — nothing environment-specific (names, URLs, messages with
internal paths) is ever written back into this repo's tracked
files. Findings return as rows: step id · good/blocked · the exact
message, scrubbed of anything internal.**

## The verdict table (fill after running Parts A and B)

| Windows (Part A) | Fabric (Part B) | route |
|---|---|---|
| green | any | THE LAPTOP — the built route: the full dry run, the console, today. Prerequisites table + steps: `work_dryrun/README_Runbook.md` |
| blocked | green | FABRIC IS FEASIBLE — but the current engine is NOT yet packaged to run there (see the runbook's prerequisites table). The green Part B findings become the inputs of the Fabric-resident packaging brief; the dry run waits for that build |
| blocked | blocked | neither runs today — the findings rows come back and a third route gets designed on facts, not guesses |

Both green = still the laptop; it is the built, tested route.

## Part A — Windows laptop (P-steps)

Open PowerShell: Start menu → type "PowerShell" → Enter.

P1. `python --version`
    Good = `Python 3.11.x` (3.10–3.12 fine; avoid 3.13 —
    untested with the parser). "not recognized", or the
    Microsoft Store opens = not installed → P3.
P2. Only if P1 failed: `py -0`
    (lists every installed python). Good = 3.10 or newer
    listed → use `py -3.11` in place of `python` below.
P3. Install python WITHOUT admin — in order, stop at the first
    that works. A real privilege block is LOUD (an admin
    credential prompt, or an explicit error); a silent
    multi-minute hang is usually the proxy or endpoint
    management, not privilege — note it and try the next route.
    a. `winget install Python.Python.3.11 --scope user`
       Good = finishes with no admin credential prompt.
    b. python.org → Downloads → the 3.11 installer → run →
       "Install Now" (the per-user default). Good = completes
       without asking for admin credentials. This route gives
       the fastest definitive yes/no on privilege.
    c. The company Software Center / app portal → search
       "Python" — the sanctioned route if a and b are blocked.
    Then CLOSE and REOPEN PowerShell, re-run P1.
P4. `python -m pip install pythonnet`
    Good = `Successfully installed pythonnet-3...`.
    Timeout / connection error = the proxy blocks pypi.org →
    ask IT for the proxy address, retry:
    `python -m pip install pythonnet --proxy http://<address>`.
P5. `dotnet --list-runtimes`
    Good = a `Microsoft.NETCore.App 8.` line (6.x/7.x usually
    also work; corporate Windows often has one already).
P6. Only if P5 printed nothing — .NET into your OWN user
    folder, no admin:
    `Invoke-WebRequest https://dot.net/v1/dotnet-install.ps1 -OutFile dotnet-install.ps1`
    `powershell -ExecutionPolicy Bypass -File .\dotnet-install.ps1 -Runtime dotnet -Channel 8.0`
    then, in every session that runs the engine:
    `$env:DOTNET_ROOT = "$HOME\.dotnet"`
    Re-run P5. (Policy refusing to run the script is itself a
    P6 finding.)
P7. Part A verdict: P1 (or P2/P3) + P4 + P5 (or P6) all good =
    green. Any hard block = record the step id + exact message.

Mac instead: `python3 --version` · `brew install python@3.11` or
the python.org per-user installer · then P4/P5 the same, with
`python3.11` in place of `python`.

## Part B — Fabric workspace (F-steps)

Browser → app.fabric.microsoft.com, your org sign-in.

F1. The workspace list (left rail → Workspaces).
    Good = at least one workspace besides "My workspace".
F2. Try to create your OWN workspace: Workspaces → "+ New
    workspace" → any scratch name.
    Good = it creates (a dedicated workspace beats borrowing a
    shared one). Blocked = fine, continue with an existing
    workspace you can see.
F3. In the candidate workspace: Manage access → find your name.
    Good = Admin, Member, or Contributor.
    Viewer = that workspace can never work; pick another or
    request a role upgrade.
F4. Workspace settings → License info (or the workspace's
    capacity marker). Good = Fabric capacity or Trial (an
    F-SKU / P-SKU / trial diamond). "Pro" alone = notebooks
    will not run there.
F5. "+ New item" → Notebook. Good = a notebook opens.
F6. In a cell: `print("preflight")` → run.
    Good = the session starts and it prints. (A first start
    can take a few minutes — slow is not blocked.)
F7. New cell: `%pip install pythonnet` → run, then
    `import pythonnet` in the next cell.
    Good = both succeed = the workspace reaches PyPI and
    allows installs. `%pip` is session-only — nothing to
    clean up, which is why preflight uses it and NOT an
    Environment item (that is the permanent library form,
    configured later at real setup, not tested here).
    ONLY if `%pip` is refused by policy: fact-check the
    fallback — "+ New item" → Environment → Public libraries
    → add `pythonnet` → publish → attach to the notebook →
    re-test the import (publishing takes minutes; this is
    the one preflight step that leaves an item behind).
F8. New cell: `from pythonnet import load; load("coreclr")`
    Good = no error = the .NET runtime the parser needs exists
    in this Fabric runtime.
F9. "+ New item" → Lakehouse → open it → Files → Upload → any
    tiny text file. Good = both create and upload work (this
    is where the parser DLL and engine files would live).
F10. New cell:
     `import urllib.request, urllib.error`
     `try: urllib.request.urlopen("https://api.openai.com/v1/models", timeout=15)`
     `except urllib.error.HTTPError as e: print("reachable:", e.code)`
     `except Exception as e: print("blocked:", type(e).__name__)`
     Good = `reachable: 401` (the service answers; 401 is
     expected without a key). `blocked:` = outbound is closed —
     asking questions and Scribe drafts cannot run from here.
F11. Part B verdict: F3 + F4 + F5/F6 + F7 + F8 + F9 all good =
     green (F2 and F10 shape HOW, not whether). Any block =
     record the step id + exact message.

## Findings

One row per step that surprised you (blocked, slow, odd message —
scrubbed of internal names):

| step | good / blocked | what it said |
|---|---|---|
