# Brief_Notebook_Import_Law — every tenant notebook is importable, never copy-paste

**Status: BUILT** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED)
Approved by Sunny 2026-10-10, her word in chat: "approved".
Built the same sitting: the .py (ruff clean, noqa per the
notebook_work_wheel precedent), the generated .ipynb (7 cells),
the .md slimmed to runbook prose. Files changed == declared.

Sunny's rule, her words (2026-10-10): *"can you make all
notebooks in the future downloadable from github so i can
import instead of copy and paste"*.

ONE sentence of scope: every tenant-facing notebook in
AIVIA_01_Delivery ships as a versioned `.py` source (the one
truth, `# %%` cells) plus a generated `.ipynb` twin for
Fabric's Import notebook — downloadable from GitHub; the
copy-paste cell template retires as a form.

The standing law this sets: a NEW tenant notebook is born as
the `.py` + `.ipynb` pair; a paste-template never ships again.
The `.ipynb` is always GENERATED from the `.py` by
sync_notebook's own cell splitter (one generator, no hand-made
twins). The work wheel already lives this way
(notebook_work_wheel.py + .ipynb, the 2026-10-09 import
fallback); this brief brings the one straggler under the law.

First application — the Collibra publish template:
- AIVIA_01_Delivery/collibra_publish_notebook.md today holds
  six cells as fenced code blocks for hand-copying.
- The build: the SAME cells, verbatim in behavior, land in
  collibra_publish_notebook.py (cells split by `# %%`, the
  laws as comments); the `.ipynb` twin is generated from it;
  the `.md` slims to the runbook text: what it does, the laws,
  how to import, the CONFIG checklist — no duplicated code to
  drift.
- NO behavior change: same CONFIG fields, same skips
  (files_waiting, awaiting_human — delivered-with-findings
  ships, her 2026-10-10 publish ruling), same dry-run/sandbox/
  census mechanics. Class: mechanical repackaging.
- Out of scope: running it (still blocked on tenant intake
  section 4), the home-estate publisher (Brief_Collibra, a
  separate arc), any wheel change.

Tests: none new — the notebook is a template with blanks; the
shipped check remains the preflight (the no-pytest-at-work
law). The sync tool's splitter is already suite-covered.

Sunny's approval: PENDING — she rules, then the status flips
to APPROVED and the three files land.

## Files declared

    AIVIA_Design/briefs/Brief_Notebook_Import_Law.md
    AIVIA_01_Delivery/collibra_publish_notebook.py
    AIVIA_01_Delivery/collibra_publish_notebook.ipynb
    AIVIA_01_Delivery/collibra_publish_notebook.md
