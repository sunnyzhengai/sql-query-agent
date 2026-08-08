-- L3 retrieval probe (ADR 0030 amendment) — paste into a NEW Fabric SQL
-- database item's query editor, section by section. Decides whether the
-- semantic catalog architecture is viable. ~10 min of T-SQL, then the
-- Data Agent part (bottom of file).
--
-- Replace <AIVIA-KEY-1> with the aivia resource's Key 1 before running
-- section 1. NEVER commit this file with a real key in it.

-- ===== 1. Credential + external model (one-time setup) ================
-- Credential name MUST match protocol+FQDN of the endpoint URL.
CREATE MASTER KEY;

CREATE DATABASE SCOPED CREDENTIAL [https://aivia.openai.azure.com]
WITH IDENTITY = 'HTTPEndpointHeaders',
     SECRET = '{"api-key":"<AIVIA-KEY-1>"}';

CREATE EXTERNAL MODEL aivia_embeddings
WITH (
    LOCATION = 'https://aivia.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-06-01',
    API_FORMAT = 'Azure OpenAI',
    MODEL_TYPE = EMBEDDINGS,
    MODEL = 'text-embedding-3-small',
    CREDENTIAL = [https://aivia.openai.azure.com]
);

-- Smoke the model binding BEFORE anything else (should return a vector):
SELECT AI_GENERATE_EMBEDDINGS('hello' USE MODEL aivia_embeddings) AS v;

-- ===== 2. Seed catalog (5 rows, sepsis-corpus-flavored) ===============
CREATE TABLE semantic_catalog (
    node_id       varchar(200) PRIMARY KEY,
    name          varchar(200),
    business_name varchar(200),
    description   varchar(2000),
    emb           VECTOR(1536)
);

INSERT INTO semantic_catalog (node_id, name, business_name, description) VALUES
('canonical:reporting.USP_ED_Sepsis', 'reporting.USP_ED_Sepsis',
 'ED Sepsis Screening',
 'Measures pediatric patients under 21 days old presenting to the emergency department with valid sepsis screening scores and recorded blood pressure measurements.'),
('canonical:reports.USP_Severe_Sepsis', 'reports.USP_Severe_Sepsis',
 'Severe Sepsis Episodes',
 'Reports management timelines of unique severe sepsis episodes, including arrival times and care event metrics.'),
('transform:reporting.USP_ED_Sepsis:ED_Readmit', 'Base_Pop_ED_Readmit',
 NULL,
 'Patient encounters readmitted to the emergency department within 24 hours of a prior visit.'),
('transform:reporting.USP_ED_Sepsis:BPA', 'BPA',
 NULL,
 'Timeline of clinical alerts and actions taken for each patient encounter, detailing alert statuses and overridden comments.'),
('canonical:reporting.USP_IP_SepsisDates', 'reporting.USP_IP_SepsisDates',
 'Sepsis Reporting Calendar',
 'A filtered list of fiscal dates relevant to sepsis cases within a specified date range.');

-- Embed in-database (documented Example C pattern):
UPDATE semantic_catalog
SET emb = AI_GENERATE_EMBEDDINGS(
    CONCAT(name, ' | ', COALESCE(business_name, ''), ' | ', description)
    USE MODEL aivia_embeddings)
WHERE emb IS NULL;

-- ===== 3. Verify the search shape works when YOU run it ===============
-- (If this fails, stop — the problem is setup, not the agent.)
WITH q AS (SELECT AI_GENERATE_EMBEDDINGS('patients who came back to the ER'
             USE MODEL aivia_embeddings) AS v)
SELECT TOP 3 c.node_id, c.name, c.business_name,
       VECTOR_DISTANCE('cosine', c.emb, q.v) AS distance
FROM semantic_catalog c CROSS JOIN q
ORDER BY distance;
-- Expect Base_Pop_ED_Readmit closest. Note the distance values — they
-- calibrate the threshold.

-- ===== 4. Data Agent part (portal, not SQL) ===========================
-- a. New Data Agent (throwaway, e.g. "L3 Probe Agent"); ONLY source:
--    this SQL database; select semantic_catalog + (if offered) the
--    aivia_embeddings function in schema selection.
-- b. Instructions (paste):
--      To find catalog entries matching a user's topic, embed the CORE
--      CONCEPT of their question (a short noun phrase, not the full
--      sentence) with AI_GENERATE_EMBEDDINGS USE MODEL aivia_embeddings
--      and rank by VECTOR_DISTANCE('cosine', ...) ascending. Report how
--      many rows scored below 0.55 before listing the top matches.
--      1 - distance is closeness: relative similarity, never a
--      probability. If nothing scores below 0.55, say the catalog has
--      nothing sufficiently related.
-- c. ONE example pair:
--    Q: "what do we have about cancelled appointments?"
--    SQL:
--      WITH q AS (SELECT AI_GENERATE_EMBEDDINGS('cancelled appointments'
--                   USE MODEL aivia_embeddings) AS v)
--      SELECT TOP 10 c.node_id, c.name, c.business_name, c.description,
--             VECTOR_DISTANCE('cosine', c.emb, q.v) AS distance
--      FROM semantic_catalog c CROSS JOIN q
--      ORDER BY distance;
-- d. THE PROBE: ask a PARAPHRASE the examples never mention, e.g.
--      "anything about newborns screened for sepsis in the ER?"
--    then open the answer's RUN STEPS and check:
--      [ ] generated SQL contains AI_GENERATE_EMBEDDINGS  -> steered OK
--      [ ] the query EXECUTED and returned rows           -> ENGINE PASS
--      [ ] top match is reporting.USP_ED_Sepsis           -> quality OK
--    Ask a second paraphrase ("patients bouncing back to the ED same
--    day?") — expect the readmit step.
-- e. VERDICT -> record in ADR 0030:
--      PASS: semantic catalog is the architecture (L3 confirmed)
--      FAIL at execution (function not found / endpoint error): agent
--        queries run on the read-only analytics mirror -> Eventhouse
--        fork gets evaluated next
--      FAIL at generation (never writes the shape): steering problem,
--        not engine — iterate instructions/examples before concluding
-- f. Delete the throwaway agent; keep the SQL DB for the real build if
--    PASS, delete it too if FAIL.
