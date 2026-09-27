Sunny's Test Cases

Testing Method:
- Sunny to open a command window and use command:
  /opt/homebrew/bin/python3.11 AIVIA_01_Code/local_chat.py AIVIA_01_Data/01_subject_sql_files/01_subject_sql_files_data_sheet.json
- To type the inputs below, Sunny starts the local web chat with command:
  "/opt/homebrew/bin/python3.11 AIVIA_01_Code/local_chat.py AIVIA_01_Data/01_subject_sql_files/01_subject_sql_files_data_sheet.json"
  then opens http://localhost:8701 in a browser. Ctrl+C in the command window stops it.
  Each question costs one paid embedding call.
- Sunny to type each of the following inputs and see the outputs.

Test Case 1:
- Input: What reports are for census?
- Expected Output: all 8 file names should be returned.

- Input: Which reports for for CCMC?
- Expected Output: all 8 file names should be returned. 2 report names with "CCMC" in the name may or may not be ranked higher than other 6 files names.
  Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_Detail_PBI
  Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_Summary_PBI


- Input: Which reports are for inpatient census?
- Expected Output: all 8 file names should be returned. The following 3 files may or may not be ranked the highest.
  COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS
  Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_SSRS
  Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Totals_SSRS


- Input: Which reports are for hospitalist census?
- Expected Output: all 8 file names should be returned.
  Reporting_USP_Hospitalist_Daily_Census_Report_92a_PBI should be ranked higher than other files.