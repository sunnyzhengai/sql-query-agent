"""The served page's JS must parse AS SERVED (live find 2026-08-13:
double-escaping put a literal newline inside a JS string literal —
the script died at parse time and the form fell through to a native
GET). node --check runs against the RUNTIME string, not the source."""

import shutil
import subprocess

import pytest

from src.webapp.app import WORKBENCH_PAGE


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_workbench_script_parses_as_served(tmp_path):
    js = WORKBENCH_PAGE.split("<script>")[1].split("</script>")[0]
    f = tmp_path / "page.js"
    f.write_text(js)
    proc = subprocess.run(["node", "--check", str(f)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[:500]


def test_no_raw_newlines_inside_js_string_literals():
    """Belt and braces without node: a quote-opened JS string must not
    contain a raw newline before closing (the exact bug class)."""
    js = WORKBENCH_PAGE.split("<script>")[1].split("</script>")[0]
    for lineno, line in enumerate(js.splitlines(), 1):
        for q in ("'", '"'):
            if line.count(q) % 2 == 1 and "`" not in line:
                raise AssertionError(
                    f"line {lineno}: unbalanced {q} quote — a string "
                    f"literal spans a newline: {line.strip()[:80]}")
