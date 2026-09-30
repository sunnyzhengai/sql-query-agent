# 02_emr_data_dictionary_discovery_facts

Discovery record (contract Output File 3, first move). Source: Sunny's
hand — pasted SELECT results into chat, 2026-09-28. Replaces the
discovery csv; Sunny has no access to run INFORMATION_SCHEMA queries.

## The dictionary tables and their fields (as pasted)

### CLARITY_TBL — one row per table (2 rows per table without the de-dup filter)
TABLE_ID, TABLE_NAME, EXTRACT_FILENAME, RELEASED_VERSION_C,
LAST_MOD_VERSION_C, BS_TEMPLATE_ID, DEPENDENT_INI, IS_JOB_DIVIDED_YN,
IS_EXTRACTED_YN, LOAD_FREQUENCY, LOAD_TYPE, ROUTINE_NAME,
ORA_DATA_TBLSPACE, ORA_INDEX_TBLSPACE, ORA_OVRFL_TBLSPACE,
IS_PARTITIONED_YN, PARTITION_TYPE, PARTITION_RANGE, PARTITION_KEY,
IS_IX_ORGANIZED_YN, SUB_PARTITION_KEY, SUB_PARTITION_VAL,
TBL_DESCRIPTOR, TBL_DESCRIPTOR_OVR, TABLE_INTRODUCTION, CHRONICLES_MF,
CM_PHY_OWNER_ID, CM_LOG_OWNER_ID, IS_PRESERVED_YN, ORA_STG_TBLSPACE,
ORA_STG_OVRFLTBLSP, TABLE_NOTES, DATA_RETAINED_YN, DEPRECATED_YN,
EXTRACT_TEMPLATE_C

- ids are strings like C0000000000015E380B21EAC0FFB60986
- table description = TABLE_INTRODUCTION (ruled)
- THE DE-DUP FILTER (Sunny's ruling): TBL_DESCRIPTOR_OVR IS NOT NULL —
  without it every table returns 2 entries; this is the consistent
  unique-table filter. It rides on every extraction query.

### CLARITY_COL — one row per column
COLUMN_ID, COLUMN_NAME, TABLE_ID, COL_DESCRIPTOR, COL_DESCRIPTOR_OVR,
DATA_TYPE, CLARITY_PRECISION, CLARITY_SCALE, HOUR_FORMAT,
RELEASED_VERSION_C, LAST_MOD_VERSION_C, IS_EXTRACTED_YN, FORMAT_INI,
FORMAT_ITEM, DESCRIPTION, CM_PHY_OWNER_ID, CM_LOG_OWNER_ID,
IS_PRESERVED_YN, COLUMN_NOTES, DEPRECATED_YN, REAL_TM_ENABLED_YN,
RECORD_STATUS_C, TRANSLATED_YN, TRANS_EXTENSION_ID, REPL_CHAR_YN,
REPLACEMENT_COLUMNS, VALID_DIS_EPIC_YN, VALID_DIS_EPIC_RSN,
VALID_DIS_CUST_YN, VALID_DIS_CUST_RSN, LAST_MODIFIED_BY_EPIC_DTTM,
DISALLOW_TRUNCATED_VALUES_YN, COL_TIME_ZONE_TYPE_C, EHI_EXPORT_TYPE_C,
DEPR_FUTURE_VERSION_C, DISCONTINUED_ITEM_YN, ITEM_DATA_COMMENTS_C,
ITEM_DATA_RESERVED_CHARS_YN, CLOUD_DATA_TYPE, CLOUD_PRECISION,
CLOUD_SCALE, LEGACY_DERIVED_TABLE_COL_DESC

- column description = DESCRIPTION (ruled); data type = DATA_TYPE

### CLARITY_TBL_FK_ALL — THE join source (ruled; matches the join sheet exactly)
TABLE_ID, FOREIGN_KEY_NUM, ORDINAL_POSITION, SOURCE_TABLE_NAME,
SOURCE_COLUMN_NAME, DEST_TABLE_NAME, DEST_COLUMN_NAME, CONDITIONAL_C,
CONDITIONAL_REASON_C, MAY_BE_STALE_C, MAY_BE_STALE_REASON_C,
IS_SUPPLEMENTAL_YN, IS_INDIRECT_CATEGORY_YN,
IS_DEST_TBL_GROUP_MASTER_YN, SOURCE_COLUMN_ID, DEST_TABLE_ID,
DEST_COLUMN_ID, IS_CURRENT_DATA_MODEL_YN, CM_PHY_OWNER_ID,
CM_LOG_OWNER_ID

- FOREIGN_KEY_NUM = the contract's join_id; ORDINAL_POSITION = ordinal
  (composite joins reassemble — observed live: FK 3 = REFERRAL_ID +
  GROUP_LINE, ordinals 1 and 2, both to REFERRAL_CVG_BED)
- carries ids AND names for source and destination
- FILTER RULING: none yet — CONDITIONAL_C / MAY_BE_STALE_C /
  IS_CURRENT_DATA_MODEL_YN reliability unknown; they ride along as
  columns instead
- (CLARITY_TBL_FK exists too — single-column links only, no composite
  grouping; NOT the source)

### CLARITY_TBL_PK — primary keys
TABLE_ID, LINE, PK_COLUMN_ID, CM_PHY_OWNER_ID, CM_LOG_OWNER_ID,
COLUMN_DESCRIPTOR

- LINE = key_ordinal; PK_COLUMN_ID joins to CLARITY_COL.COLUMN_ID

### CLARITY_COL_INIITM — Chronicles INI/item mapping (ruled IN, this phase)
COLUMN_ID, LINE, COLUMN_INI, COLUMN_ITEM, CM_LOG_OWNER_ID,
CM_PHY_OWNER_ID

## Estate facts (Sunny, 2026-09-28)
- V_* and F_* names inside the EMR are TABLES — same database and
  schema as the base tables. They are NOT our organization's views.
  Our own views and stored procedures live in their own schemas (the
  ones the sql files show: Reporting, COOK_RPT).
- DEPRECATED_YN rides along on sheets, never filtered — a
  used-but-deprecated object is a finding.
- Category values (ZC_* code -> NAME rows) are ruled IN, extracted in
  a THIRD move after the join csv lands: FK_ALL's DEST_COLUMN_NAME
  names each ZC table's id column, so the values queries derive from
  data, never guessed.
