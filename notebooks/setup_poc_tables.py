"""Fabric Notebook: Create POC sample Delta tables.

Run this ONCE in your POC workspace to create the dict_tables, dict_columns,
and sql_sources Delta tables in your Lakehouse. After this, the orchestrator
notebook can run.

In Fabric: create a new Notebook, copy each cell, attach to your Lakehouse, run all.
"""

# %% Cell 1: Create dict_tables
from pyspark.sql.types import StringType, StructField, StructType

dict_tables_data = [
    ("encounter", "Patient encounter/visit records"),
    ("patient", "Patient demographics"),
    ("department", "Hospital departments and units"),
]

dict_tables_schema = StructType([
    StructField("TABLE_NAME", StringType(), False),
    StructField("DESCRIPTION", StringType(), True),
])

dict_tables_df = spark.createDataFrame(dict_tables_data, schema=dict_tables_schema)
dict_tables_df.write.format("delta").mode("overwrite").saveAsTable("dict_tables")

print("Created dict_tables:")
dict_tables_df.show(truncate=False)

# %% Cell 2: Create dict_columns
dict_columns_data = [
    ("encounter", "encounter_id", "Unique encounter identifier"),
    ("encounter", "patient_id", "FK to patient table"),
    ("encounter", "admit_dt", "Admission date/time"),
    ("encounter", "discharge_dt", "Discharge date/time"),
    ("encounter", "department_id", "FK to department table"),
    ("patient", "patient_id", "Unique patient identifier"),
    ("patient", "birth_date", "Patient date of birth"),
    ("department", "department_id", "Unique department identifier"),
    ("department", "department_name", "Department display name"),
]

dict_columns_schema = StructType([
    StructField("TABLE_NAME", StringType(), False),
    StructField("COLUMN_NAME", StringType(), False),
    StructField("DESCRIPTION", StringType(), True),
])

dict_columns_df = spark.createDataFrame(dict_columns_data, schema=dict_columns_schema)
dict_columns_df.write.format("delta").mode("overwrite").saveAsTable("dict_columns")

print("Created dict_columns:")
dict_columns_df.show(truncate=False)

# %% Cell 3: Create sql_sources
sql_sources_data = [
    (
        "ER_LOS",
        "ER Length of Stay",
        """WITH er_visits AS (
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
FROM los_calc""",
        "Dr. Smith",
        "jane.doe",
    ),
]

sql_sources_schema = StructType([
    StructField("metric_id", StringType(), False),
    StructField("name", StringType(), False),
    StructField("sql", StringType(), False),
    StructField("steward", StringType(), True),
    StructField("developer", StringType(), True),
])

sql_sources_df = spark.createDataFrame(sql_sources_data, schema=sql_sources_schema)
sql_sources_df.write.format("delta").mode("overwrite").saveAsTable("sql_sources")

print("Created sql_sources:")
sql_sources_df.show(truncate=False)

# %% Cell 4: Verify
print("=== All POC tables created ===")
print("Tables in lakehouse:")
spark.sql("SHOW TABLES").show()
