"""Generate sample data for demo/testing without real org data.

Creates:
- Sample data dictionary (tables + columns)
- Sample SQL sources with CTEs
- Sample canonical metric definitions
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"

SAMPLE_DICT_TABLES = [
    {"TABLE_NAME": "encounter", "DESCRIPTION": "Patient encounter/visit records"},
    {"TABLE_NAME": "patient", "DESCRIPTION": "Patient demographics"},
    {"TABLE_NAME": "department", "DESCRIPTION": "Hospital departments and units"},
]

SAMPLE_DICT_COLUMNS = [
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "encounter_id", "DESCRIPTION": "Unique encounter identifier"},
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "patient_id", "DESCRIPTION": "FK to patient table"},
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "admit_dt", "DESCRIPTION": "Admission date/time"},
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "discharge_dt", "DESCRIPTION": "Discharge date/time"},
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "department_id", "DESCRIPTION": "FK to department table"},
    {"TABLE_NAME": "patient", "COLUMN_NAME": "patient_id", "DESCRIPTION": "Unique patient identifier"},
    {"TABLE_NAME": "patient", "COLUMN_NAME": "birth_date", "DESCRIPTION": "Patient date of birth"},
    {"TABLE_NAME": "department", "COLUMN_NAME": "department_id", "DESCRIPTION": "Unique department identifier"},
    {"TABLE_NAME": "department", "COLUMN_NAME": "department_name", "DESCRIPTION": "Department display name"},
]

SAMPLE_SQL_SOURCES = [
    {
        "metric_id": "ER_LOS",
        "name": "ER Length of Stay",
        "sql": """
WITH er_visits AS (
    SELECT
        e.encounter_id,
        e.patient_id,
        e.admit_dt,
        e.discharge_dt,
        e.department_id
    FROM encounter e
    INNER JOIN department d ON e.department_id = d.department_id
    WHERE d.department_name = 'Emergency'
),
los_calc AS (
    SELECT
        encounter_id,
        patient_id,
        department_id,
        DATEDIFF(MINUTE, admit_dt, discharge_dt) / 60.0 AS los_hours
    FROM er_visits
)
SELECT
    AVG(los_hours) AS avg_er_los_hours
FROM los_calc
""",
        "steward": "Dr. Smith",
        "developer": "jane.doe",
    }
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, data in [
        ("dict_tables", SAMPLE_DICT_TABLES),
        ("dict_columns", SAMPLE_DICT_COLUMNS),
        ("sql_sources", SAMPLE_SQL_SOURCES),
    ]:
        path = OUTPUT_DIR / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote {path}")

    print(f"\nSample data written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
