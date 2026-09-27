01-subject-sql-files-design

Description:
Step 1: Prepare a set of sql files being used as the subject matter for this project AIVIA_01.
    - Create a data contract: "01_subject_sql_files_data_contract.md".
    - Create a folder: AIVIA_01_Data/01_subject_sql_files/. Save all imported sql files in this Location.
    - Create a data sheet 01_subject_sql_files_data_sheet.json.
    - Create a Fabric lakehouse, AIVIA_01_lh.
    - Load this data sheet into Fabric lakehouse table, 01_subject_sql_files_lh_table.
    - Call LLM to embed the file names and store the embeddings in the lakehouse table.
    - Create a Fabric graph model, AIVIA_01_graph.
    - Load the lakehouse table into the graph model. Each report as a node, populate names and embeddings in the nodes as properties.
    - Create visual page for this graph model.
    - Create a chat interface for this graph model, using LLM to understand user's questions and compare embeddings with the graph model's embeddings.
    - Return matched nodes. Return all nodes ranked, with similarity scores.
    - Packages arrive in Fabric via a Fabric Environment item with pinned versions matching local (openai==3.19.2) — not per-notebook %pip install.
    - All paths and the key location are parameters/contract facts, never written inside code — the notebook passes lakehouse paths to the same functions we tested locally.
