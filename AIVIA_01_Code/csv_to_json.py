"""csv_to_json.py — the DUMB converter (ruled 2026-10-06: the
delivery extraction SQL is shape-matched, so this script
carries ZERO logic — csv rows in, the engine's json files out,
names mapped, nothing renamed, nothing computed).

SOURCE lives in the engine codebase (the gate's carve-out);
a COPY rides in the delivery bucket's tools/ at pack time,
like the wheel — the bucket's hygiene lock keeps both clean.

Usage (anywhere Python 3.11 runs — laptop or a notebook cell):

    python csv_to_json.py <csv_dir> <out_dir>

or from a notebook:

    import csv_to_json
    csv_to_json.convert("<csv_dir>", "<out_dir>")

Reads dict_extract_*.csv, writes the four files the engine's
--dict folder expects.
"""

import csv
import json
import sys
from pathlib import Path

# csv name -> the engine's expected json name
NAME_MAP = {
    "dict_extract_table.csv":
        "02_emr_data_dictionary_extraction_table.json",
    "dict_extract_column.csv":
        "02_emr_data_dictionary_extraction_column.json",
    "dict_extract_join.csv":
        "02_emr_data_dictionary_extraction_join.json",
    "dict_extract_value.csv":
        "02_emr_data_dictionary_extraction_value.json",
}


def convert(csv_dir, out_dir):
    """Faithful rows, no logic. Returns the written paths."""
    csv_dir, out_dir = Path(csv_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for csv_name, json_name in NAME_MAP.items():
        src = csv_dir / csv_name
        if not src.exists():
            print(f"skipped (no file): {csv_name}")
            continue
        with open(src, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        target = out_dir / json_name
        target.write_text(json.dumps(rows, indent=1))
        written.append(target)
        print(f"{csv_name} -> {json_name}: {len(rows)} rows")
    return written


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python csv_to_json.py <csv_dir> <out_dir>")
        raise SystemExit(2)
    convert(sys.argv[1], sys.argv[2])
