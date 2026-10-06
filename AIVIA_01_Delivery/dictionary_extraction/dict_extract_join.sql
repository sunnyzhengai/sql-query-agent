-- dict_extract_join.sql — THE FULL-DICTIONARY extraction
-- (ruled 2026-10-06: unscoped), SHAPE-MATCHED to the engine's
-- join keys. destin_in_scope is 'Y' by definition here: the
-- full dictionary makes everything in scope (the home build
-- computed it against the corpus table set).
-- Run by the customer's hand; save as dict_extract_join.csv.
SELECT
    CONCAT(CAST(TFA.TABLE_ID AS VARCHAR(40)), '-',
           CAST(TFA.FOREIGN_KEY_NUM AS VARCHAR(20)))
                                      AS join_id,
    TFA.ORDINAL_POSITION              AS ordinal,
    CAST(TFA.TABLE_ID AS VARCHAR(80)) AS source_table_id,
    TFA.SOURCE_TABLE_NAME             AS source_table_name,
    CAST(TFA.SOURCE_COLUMN_ID AS VARCHAR(80))
                                      AS source_column_id,
    TFA.SOURCE_COLUMN_NAME            AS source_column_name,
    CAST(TFA.DEST_TABLE_ID AS VARCHAR(80))
                                      AS destin_table_id,
    TFA.DEST_TABLE_NAME               AS destin_table_name,
    CAST(TFA.DEST_COLUMN_ID AS VARCHAR(80))
                                      AS destin_column_id,
    TFA.DEST_COLUMN_NAME              AS destin_column_name,
    TFA.CONDITIONAL_C                 AS conditional_c,
    TFA.MAY_BE_STALE_C                AS may_be_stale_c,
    TFA.IS_CURRENT_DATA_MODEL_YN      AS is_current_data_model_yn,
    TFA.IS_SUPPLEMENTAL_YN            AS is_supplemental_yn,
    'Y'                               AS destin_in_scope
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_TBL_FK_ALL TFA
        ON TBL.TABLE_ID = TFA.TABLE_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
ORDER BY TFA.TABLE_ID, TFA.FOREIGN_KEY_NUM,
         TFA.ORDINAL_POSITION;
