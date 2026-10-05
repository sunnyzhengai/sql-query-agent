"""Brief_Packaging locks (STAMPED 2026-10-04): the deterministic
work wheel aivia01-sqldesc. RED until build_sqldesc_wheel.py
exposes the builder. The wheel is built INTO tmp here — no
network (pip wheel --no-build-isolation), no keys, no estate
data; the locks read the built artifact's own bytes.
"""

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "AIVIA_01_Code"))

CANARY = ("CCMC EMERGENCY", "CCMC IR IMAGING", "CCMC CATH LAB",
          "CCMC MAIN OR", "CCMC SPA OR", "CCMC PHP PSYCHIATRY",
          "CCMC CARDIOVASCULAR OR", "DSC OR")
SECRET_SHAPES = ("OPENAI", "AZURE_OPENAI", "api_key",
                 "import openai", "import requests",
                 "import httpx")


def _wheel(tmp_path):
    import build_sqldesc_wheel as bw
    return Path(bw.build(out_dir=tmp_path))


def test_wheel_manifest_equality(tmp_path):
    """Lock 1: the wheel's contents == the stamped allowlist
    exactly — one extra or missing file is a refused build."""
    import build_sqldesc_wheel as bw
    whl = _wheel(tmp_path)
    names = set(zipfile.ZipFile(whl).namelist())
    payload = {n for n in names if ".dist-info/" not in n}
    assert payload == set(bw.ALLOWLIST)


def test_wheel_carries_no_secret_shapes(tmp_path):
    """Lock 2: no key-shaped strings, no network clients, in any
    packaged python module."""
    whl = _wheel(tmp_path)
    z = zipfile.ZipFile(whl)
    for n in z.namelist():
        if not n.endswith(".py"):
            continue
        text = z.read(n).decode("utf-8", errors="replace")
        for shape in SECRET_SHAPES:
            assert shape not in text, (n, shape)


def test_wheel_carries_no_estate_data(tmp_path):
    """Lock 3: the census canary — customer strings must not
    exist anywhere in the wheel, any member, any encoding."""
    whl = _wheel(tmp_path)
    z = zipfile.ZipFile(whl)
    for n in z.namelist():
        blob = z.read(n)
        for canary in CANARY:
            assert canary.encode() not in blob, (n, canary)
