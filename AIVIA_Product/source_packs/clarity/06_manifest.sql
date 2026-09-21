-- clarity-pack-1.2 · Script 6 -> the manifest.json values
--
-- Copy the results into manifest.json EXACTLY as returned.
-- db_name and server are OPTIONAL (MR1a, 2026-09-19): omit both
-- for the minimal form; naming the db here AND in
-- registration.json arms the wrong-database refusal (INTAKE-8) —
-- case-sensitive when armed.
-- Minimal form:
-- {
--  "source": "clarity",
--  "operator": "<your name>",
--  "as_of": "<as_of below>",
--  "source_pack_version": "clarity-pack-1.2",
--  "default_schema": "dbo"
-- }
SELECT
    DB_NAME()                                   AS [db_name],
    @@SERVERNAME                                AS [server],
    CONVERT(varchar(33), SYSUTCDATETIME(), 127) AS [as_of];
