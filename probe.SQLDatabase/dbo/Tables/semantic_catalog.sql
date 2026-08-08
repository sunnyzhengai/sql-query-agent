CREATE TABLE [dbo].[semantic_catalog] (
    [node_id]       VARCHAR (200)  NOT NULL,
    [name]          VARCHAR (200)  NULL,
    [business_name] VARCHAR (200)  NULL,
    [description]   VARCHAR (2000) NULL,
    [emb]           VECTOR(1536)   NULL,
    PRIMARY KEY CLUSTERED ([node_id] ASC)
);


GO

