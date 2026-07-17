"""Fabric Notebook: Scan .sql files to find views/procs that reference target tables.

Upload your .sql files to your Lakehouse Files folder, then run this notebook
to discover which ones belong to the surgery domain (or any domain you define).

In Fabric: create a new Notebook, copy each cell, attach to your Lakehouse, run all.
"""

# %% Cell 1: Configuration — edit these values
import os
import re

# Where your .sql files are stored in the Lakehouse
SQL_FILES_FOLDER = "/lakehouse/default/Files/sql_files"

# Tables that define the surgery domain (case-insensitive matching)
TARGET_TABLES = ["OR_LOG", "OR_CASE"]

# %% Cell 2: Scan all .sql files for target table references

def find_sql_files(folder):
    """Recursively find all .sql files in a folder."""
    sql_files = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".sql"):
                sql_files.append(os.path.join(root, f))
    return sorted(sql_files)


def search_file_for_tables(file_path, target_tables):
    """Check if a .sql file references any of the target tables.

    Uses word-boundary matching to avoid false positives
    (e.g. 'OR_LOG' won't match 'FLOOR_LOGGING').
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    content_upper = content.upper()
    matches = []
    for table in target_tables:
        # Word boundary match: table name not surrounded by other word chars
        pattern = r'\b' + re.escape(table.upper()) + r'\b'
        if re.search(pattern, content_upper):
            matches.append(table)

    return matches, content


# Scan
sql_files = find_sql_files(SQL_FILES_FOLDER)
print(f"Found {len(sql_files)} .sql files in {SQL_FILES_FOLDER}\n")

results = []
for filepath in sql_files:
    matches, content = search_file_for_tables(filepath, TARGET_TABLES)
    if matches:
        filename = os.path.basename(filepath)
        results.append({
            "file": filename,
            "path": filepath,
            "tables_matched": matches,
            "content": content,
        })

print(f"=== {len(results)} files reference surgery tables ===\n")
for r in results:
    tables = ", ".join(r["tables_matched"])
    print(f"  {r['file']}  [{tables}]")

# %% Cell 3: Review matched files — show first few lines of each

for r in results:
    print(f"\n{'='*60}")
    print(f"FILE: {r['file']}")
    print(f"TABLES: {', '.join(r['tables_matched'])}")
    print(f"{'='*60}")
    # Show first 20 lines
    lines = r["content"].split("\n")[:20]
    for line in lines:
        print(f"  {line}")
    if len(r["content"].split("\n")) > 20:
        print(f"  ... ({len(r['content'].split(chr(10)))} total lines)")

# %% Cell 4: Load matched files into sql_sources Delta table
# STOP AND REVIEW Cell 3 output before running this cell.
# Remove any files from `results` that you don't want to include.

from pyspark.sql.types import StringType, StructField, StructType

def extract_object_name(filename):
    """Derive a clean object name from the filename."""
    name = filename.replace(".sql", "").replace(".SQL", "")
    return name


def strip_create_prefix(sql_text):
    """Strip CREATE VIEW/PROC prefix to get the SELECT body."""
    upper = sql_text.upper().strip()
    # Find the AS keyword that precedes the SELECT/WITH
    # Handle: CREATE VIEW x AS, CREATE OR ALTER VIEW x AS, CREATE PROCEDURE x AS
    as_pattern = re.compile(
        r'\bAS\s*\n',  # AS followed by newline
        re.IGNORECASE
    )
    match = as_pattern.search(sql_text)
    if match:
        after = sql_text[match.end():].strip()
        after_upper = after.upper()
        if after_upper.startswith("SELECT") or after_upper.startswith("WITH") or after_upper.startswith("BEGIN"):
            return after
    # Fallback: try simpler AS pattern
    as_idx = upper.find(" AS ")
    if as_idx != -1:
        after = sql_text[as_idx + 4:].strip()
        after_upper = after.upper()
        if after_upper.startswith("SELECT") or after_upper.startswith("WITH"):
            return after
    return sql_text


sql_sources_rows = []
for r in results:
    obj_name = extract_object_name(r["file"])
    select_body = strip_create_prefix(r["content"])
    sql_sources_rows.append((
        f"surgery.{obj_name}",  # metric_id
        obj_name,                # name
        select_body,             # sql (SELECT body)
        None,                    # steward (fill in later)
        None,                    # developer (fill in later)
    ))

print(f"Preparing {len(sql_sources_rows)} sql_sources records:\n")
for row in sql_sources_rows:
    print(f"  metric_id: {row[0]}")

# %% Cell 5: Write to Delta table

sql_sources_schema = StructType([
    StructField("metric_id", StringType(), False),
    StructField("name", StringType(), False),
    StructField("sql", StringType(), False),
    StructField("steward", StringType(), True),
    StructField("developer", StringType(), True),
])

new_df = spark.createDataFrame(sql_sources_rows, schema=sql_sources_schema)  # noqa: F821

# Merge into existing sql_sources (upsert by metric_id)
new_df.createOrReplaceTempView("new_surgery_sources")

try:
    spark.sql("""  # noqa: F821
        MERGE INTO sql_sources AS target
        USING new_surgery_sources AS source
        ON target.metric_id = source.metric_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)
    print(f"Merged {len(sql_sources_rows)} records into sql_sources")
except Exception:
    new_df.write.format("delta").mode("append").saveAsTable("sql_sources")
    print(f"Created/appended {len(sql_sources_rows)} records to sql_sources")

# %% Cell 6: Verify
print("\nCurrent sql_sources:")
spark.table("sql_sources").select("metric_id", "name").show(truncate=False)  # noqa: F821
