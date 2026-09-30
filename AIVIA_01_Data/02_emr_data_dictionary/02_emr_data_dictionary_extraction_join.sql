-- 02_emr_data_dictionary_extraction_join.sql (contract Output File 3, move 2; generated from the discovery facts).
-- Run in the EMR by Sunny's hand. Save the FULL result as
-- 02_emr_data_dictionary_extraction_join.csv in AIVIA_01_Data/02_emr_data_dictionary/.
-- The TBL_DESCRIPTOR_OVR filter is Sunny's de-dup ruling
-- (2 rows per table without it). Table list: the 39 used tables
-- from the derived census, casing folded.
SELECT TFA.TABLE_ID, TFA.FOREIGN_KEY_NUM, TFA.ORDINAL_POSITION,
       TFA.SOURCE_TABLE_NAME, TFA.SOURCE_COLUMN_ID,
       TFA.SOURCE_COLUMN_NAME, TFA.DEST_TABLE_ID, TFA.DEST_TABLE_NAME,
       TFA.DEST_COLUMN_ID, TFA.DEST_COLUMN_NAME, TFA.CONDITIONAL_C,
       TFA.MAY_BE_STALE_C, TFA.IS_CURRENT_DATA_MODEL_YN,
       TFA.IS_SUPPLEMENTAL_YN
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_TBL_FK_ALL TFA
        ON TBL.TABLE_ID = TFA.TABLE_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
    'CLARITY_ADT',
    'CLARITY_BED',
    'CLARITY_DEP',
    'CLARITY_EPM',
    'CLARITY_LOC',
    'CLARITY_ROM',
    'CLARITY_SA',
    'COVERAGE_MEMBER_LIST',
    'CR_STAT_EXECUTION',
    'DATE_DIMENSION',
    'F_IP_HSP_PAT_DAYS',
    'F_SCHED_APPT',
    'PATIENT',
    'PATIENT_4',
    'PATIENT_MYC',
    'PATIENT_RACE',
    'PAT_CVG_FILE_ORDER',
    'PAT_ENC',
    'PAT_ENC_HSP',
    'PAT_RELATIONSHIP_LIST',
    'PAT_RELATIONSHIP_LIST_HX',
    'PAT_REL_LANGUAGES',
    'V_COVERAGE_PAYOR_PLAN',
    'V_PAT_ADT_LOCATION_HX',
    'V_REPORT_RUN_FACT',
    'ZC_COUNTRY',
    'ZC_COUNTY',
    'ZC_DISCH_DISP',
    'ZC_EMERG_PAT_REL',
    'ZC_ETHNIC_GROUP',
    'ZC_GENDER_IDENTITY',
    'ZC_LANGUAGE',
    'ZC_MYCHART_STATUS',
    'ZC_PATIENT_RACE',
    'ZC_PAT_CLASS',
    'ZC_PAT_SERVICE',
    'ZC_SEX',
    'ZC_SEX_ASGN_AT_BIRTH',
    'ZC_STATE'
  )
ORDER BY TFA.TABLE_ID, TFA.FOREIGN_KEY_NUM, TFA.ORDINAL_POSITION;
