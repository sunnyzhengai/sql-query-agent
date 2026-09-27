01-subject-sql-files-design

Description:
Step 1: Prepare a set of sql files being used as the subject matter for this project AIVIA_01.
Local:
    L01: Create a data contract: "01_subject_sql_files_data_contract.md".
    L02: Create a folder: AIVIA_01_Data/01_subject_sql_files/. Save all imported sql files in this Location.
    L03: Create a data sheet 01_subject_sql_files_data_sheet.json.
    L04: Create a local web chat to test the embeddings before the Fabric move:
      reads the data sheet json, embeds the user's question with the same model,
      ranks all files by cosine similarity, returns all file names with scores.
      Sunny's hand test cases in test_01_subject_sql_files_data_contract_sunny.md
      run against this chat.
Fabric
    F01: Create a Fabric workspace AIVIA_01
    F02: Create a Fabric lakehouse, AIVIA_01_LH.
    F03: Create a subfolder lakehouse /Files/Data/01_subject_sql_files/
    F04: Upload the 8 sql files into this folder.
    F05: Upload the data sheet into Fabric lakehouse table, /Files/Data/01_subject_sql_files/01_subject_sql_files_data_sheet.json.
    F06: Create the Environment item in it AIVIA_01_ENV 
    F07: Add openai==3.19.2 to its public libraries.
    F08: Get workspace-id: 23112b57-368a-46ed-941b-c10e3baad392  
    F09: Get environment-id: 1b87c0e2-f56c-4253-9933-fb7a60db181d
    F10: Run (by my hand only): /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_wheel.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --environment 1b87c0e2-f56c-4253-9933-fb7a60db181d
      
    - Create a Fabric graph model, AIVIA_01_graph.
    - Load the lakehouse table into the graph model. Each report as a node, populate names and embeddings in the nodes as properties.
    - Create visual page for this graph model.
    - Create a chat interface for this graph model, using LLM to understand user's questions and compare embeddings with the graph model's embeddings.
    - Return matched nodes. Return all nodes ranked, with similarity scores.
    - Packages arrive in Fabric via a Fabric Environment item with pinned versions matching local (openai==3.19.2) — not per-notebook %pip install.
    - All paths and the key location are parameters/contract facts, never written inside code — the notebook passes lakehouse paths to the same functions we tested locally.
