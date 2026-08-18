-- Demo helper functions for aivia_demo_src (run AFTER seed_demo_tables.sql).
-- The corpus procs call dbo.fn_parse_date with reporting date tokens:
--   'T'  / 'T-1'  = today / today minus n days
--   'MB' / 'MB-1' = first day of the month, n months back
--   'ME' / 'ME-1' = last day of the month, n months back
--   'YB' / 'YE'   = year begin / year end, n years back
-- anything else parses as a literal date. Deterministic against GETDATE().
-- Run in the aivia_demo_src SQL query editor (same drill as the table seed).

CREATE OR ALTER FUNCTION dbo.fn_parse_date (@token VARCHAR(30))
RETURNS DATE
AS
BEGIN
    DECLARE @today DATE = CAST(GETDATE() AS DATE);
    DECLARE @t VARCHAR(30) = UPPER(LTRIM(RTRIM(ISNULL(@token, ''))));
    DECLARE @n INT = 0;
    DECLARE @dash INT = CHARINDEX('-', @t);

    IF @dash > 0 AND ISNUMERIC(SUBSTRING(@t, @dash + 1, 10)) = 1
    BEGIN
        SET @n = CAST(SUBSTRING(@t, @dash + 1, 10) AS INT);
        SET @t = LEFT(@t, @dash - 1);
    END

    RETURN CASE @t
        WHEN 'T'  THEN DATEADD(DAY, -@n, @today)
        WHEN 'MB' THEN DATEFROMPARTS(YEAR(DATEADD(MONTH, -@n, @today)),
                                     MONTH(DATEADD(MONTH, -@n, @today)), 1)
        WHEN 'ME' THEN EOMONTH(DATEADD(MONTH, -@n, @today))
        WHEN 'YB' THEN DATEFROMPARTS(YEAR(@today) - @n, 1, 1)
        WHEN 'YE' THEN DATEFROMPARTS(YEAR(@today) - @n, 12, 31)
        ELSE COALESCE(TRY_CONVERT(DATE, @token), @today)
    END;
END;
