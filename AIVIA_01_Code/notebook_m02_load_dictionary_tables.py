# notebook_m02_load_dictionary_tables — the M02 notebook source (F21
# pattern: this file IS the notebook definition; sync_wheel --notebook
# pushes it; the notebook stays a THIN CALLER, logic lives in the wheel).
# Approved with the load_dictionary_tables pseudo code, 2026-09-30.

from load_dictionary_tables import build_table_rows

tables, census = build_table_rows(
    "/lakehouse/default/Files/Data/02_emr_data_dictionary",
    "/lakehouse/default/Files/Data/03_chat_bot",
)
for name, rows in tables.items():
    spark.createDataFrame(rows).write.mode("overwrite").saveAsTable(name)  # noqa: F821
    print(name, spark.table(name).count())  # noqa: F821
print(census)
