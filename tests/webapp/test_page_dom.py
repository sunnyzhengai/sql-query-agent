"""RW-19 — the page-JS gate's RUNTIME leg (TESTPLAN_0062 D).

The headless battery is API-only and structurally blind to page JS:
the no-match card crashed on a null addEventListener while every
static gate stayed green. This test executes the REAL page script in
node against a purpose-built minimal DOM (tests/webapp/dom_harness.js
— our markup is our own; no jsdom dependency) and renders EVERY card
variant; a throw, a null wire, or a missing expected listener fails.

Proves: law:walk-finds
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_every_card_variant_renders_and_wires(tmp_path):
    node = shutil.which("node")
    assert node, ("node is required for the DOM smoke leg (RW-19) — "
                  "present on ubuntu-latest CI and dev machines")
    from src.webapp.app import WORKBENCH_PAGE
    m = re.search(r"<script>\n(.*)\n</script>", WORKBENCH_PAGE,
                  re.DOTALL)
    assert m, "page script block not found"
    script = tmp_path / "page_script.js"
    script.write_text(m.group(1))
    out = subprocess.run(
        [node, str(REPO / "tests" / "webapp" / "dom_harness.js"),
         str(script)],
        capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr[:800]
    verdict = json.loads(out.stdout.strip().splitlines()[-1])
    assert verdict["ok"], "\n".join(verdict["failures"])
