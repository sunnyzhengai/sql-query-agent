01-subject-sql-files-data-contract

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- 8 sql files

Where are these sql files from?
- Sunny downloaded from an authorized source

Who loaded these sql files, and how?
- Sunny Zheng, manually

Do we need to desensitize the sql files?
- No.

Where are these sql files located for local development?
- /Users/sunnyzheng/sql-query-agent/AIVIA_01_Data/01_subject_sql_files/

Where are these sql files located for production?
- Fabric lakehouse, AIVIA_01_LH/Files/Data/01_subject_sql_files/

What is the output of this data contract?
- A data sheet, 01_subject_sql_files_data_sheet.json

What columns are in the data sheet?
- file_name
- database_name: what database name is used in the file.
- schema_name: what schema name is used in the file.
- file_name_embedding
- Example: in pretty format for easy reading
{
  "file_name": "Reporting_USP_Hospitalist_Daily_Census_Report_92a_PBI",
  "database_name": "CookClarity" 
  "schema_name": "Reporting" 
  "file_name_embedding": [0.0123, -0.0456, ...]
}

Who fills out the data sheet?
- file_name: extracted from the file name by script authorized by Sunny Zheng
- database_name: filled by Sunny Zheng, fail loudly if not found.
- schema_name: filled by Sunny Zheng, fail loudly if not found.
- file_name_embedding: filled by script authorized by Sunny Zheng
- when the script rebuilds the sheet, it keeps existing database_name/schema_name values; a new file gets blanks; blanks fail loudly until Sunny fills them.

Who can read these sql files?
- Sunny Zheng
- Claude Code Agent
- Code script authorized by Sunny Zheng

Who can edit these sql files?
- Sunny Zheng

Who can edit the data sheet?
- Sunny Zheng to fill the names of the database and schema
- Script authorized by Sunny Zheng; 
- Claude asks before updating the data sheet

What model is used to embed the file names?
- Embedding model: OpenAI text-embedding-3-large, 
- 3072 numbers per embedding; 
- key in .env file.

Where does the key live in production? 
— Azure Key Vault, secret name TBD at the Fabric move.