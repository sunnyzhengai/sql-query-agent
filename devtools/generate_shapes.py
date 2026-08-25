"""Regenerate the shape corpus (ADR 0055) into data/shapes/generated/.

Deterministic (spec:E2): same palette in, byte-identical corpus out —
the committed files are the corpus of record and CI asserts that a
regeneration produces zero diff (the TRACE_MAP pattern).

Usage: python3.11 devtools/generate_shapes.py [--palette PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.shapes.generator import generate, load_palette  # noqa: E402

OUT = PROJECT_ROOT / "data" / "shapes" / "generated"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--palette", default=str(
        PROJECT_ROOT / "data" / "shapes" / "palette_diabetes.json"))
    args = ap.parse_args()
    palette = load_palette(args.palette)
    files, manifest = generate(palette)
    for relpath, sql in sorted(files.items()):
        path = OUT / "sql" / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(sql.encode())
    (OUT / "shape_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    n_cells = len(manifest["cells"])
    n_inst = sum(1 for c in manifest["cells"]
                 if c["status"] == "instantiated")
    print(f"wrote {len(files)} SQL files + shape_manifest.json "
          f"({n_cells} cells: {n_inst} instantiated, "
          f"{n_cells - n_inst} excluded-with-reason)")


if __name__ == "__main__":
    main()
