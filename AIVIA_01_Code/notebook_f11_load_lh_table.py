# ruff: noqa: F821 — `spark` exists in the Fabric notebook runtime, not here.
# THE F11 NOTEBOOK — source of truth (design doc F21: this file syncs to
# the Fabric notebook via sync_notebook.py; RUNNING stays Sunny's hand).
# Requires: AIVIA_01_ENV attached (brings the aivia01 wheel) and
# AIVIA_01_LH as the default lakehouse (both attached once, by hand).

from load_lh_table import to_table_rows

rows = to_table_rows(
    "/lakehouse/default/Files/Data/01_subject_sql_files/"
    "01_subject_sql_files_data_sheet.json"
)
df = spark.createDataFrame(rows)
df.write.mode("overwrite").saveAsTable("f01_subject_sql_files_lh_table")
df.drop("fileNameEmbedding").write.mode("overwrite").saveAsTable(
    "f01_subject_sql_files_graph"
)
