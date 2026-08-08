CREATE EXTERNAL MODEL [aivia_embeddings]
    AUTHORIZATION [founder@aiviaapp.com]
WITH (
LOCATION = N'https://aivia.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-06-01',
API_FORMAT = N'Azure OpenAI',
MODEL_TYPE = EMBEDDINGS,
MODEL = N'text-embedding-3-small',
CREDENTIAL = [https://aivia.openai.azure.com]
);


GO

