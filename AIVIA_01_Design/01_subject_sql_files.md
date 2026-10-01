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
    F05: Upload the data sheet into Fabric lakehouse file, /Files/Data/01_subject_sql_files/01_subject_sql_files_data_sheet.json.
    F06: Create the Environment item in it AIVIA_01_ENV 
    F07: Add openai==3.19.2 to its public libraries.
    F08: Get workspace-id: 23112b57-368a-46ed-941b-c10e3baad392  
    F09: Get environment-id: 1b87c0e2-f56c-4253-9933-fb7a60db181d
    F10: Run (by my hand only): /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_wheel.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --environment 1b87c0e2-f56c-4253-9933-fb7a60db181d
    
    F11: Create a Notebook. Attach AIVIA_01_ENV as its environment and AIVIA_01_LH as its default lakehouse, paste the one cell from the top of load_lh_table.py (the from load_lh_table import to_table_rows … saveAsTable block), and run it. Load the data sheet json (01_subject_sql_files_data_sheet.json) from Files into lakehouse table f01_subject_sql_files_lh_table.".     
    F12: Create a Fabric graph model, AIVIA_01_GRAPH.
    F13: Load the lakehouse table f01_subject_sql_files_graph (embedding-free graph export written by the F11 notebook) into the graph model. Each report as a node (SQL_FILE), names as properties. Embeddings do NOT enter the graph — ruled 2026-09-27: the graph cannot hold the 3072-number array; embeddings stay in f01_subject_sql_files_lh_table.
    
    F14: Create the test suites using GQL to validate the loading of the table is correct. Run the tests.
    F15: Create a graph visual design document to standardize the graph visual page. (In the past we always encountered the same issues with visuals).
    F16: Create visual page for this graph model.
    F17: Create a chat interface for this graph model, using LLM to understand user's questions and compare embeddings with the embeddings in f01_subject_sql_files_lh_table; the graph serves structure.
    F18: Return matched nodes. Return all nodes ranked, with similarity scores.
    F19: Packages arrive in Fabric via a Fabric Environment item with pinned versions matching local (openai==3.19.2) — not per-notebook %pip install.
    F20: All paths and the key location are parameters/contract facts, never written inside code — the notebook passes lakehouse paths to the same functions we tested locally.
    F21: notebook definitions sync from AIVIA_01_Code via the sync script; running stays by my hand

    Your commands, once you grab the notebook's item id from its URL (open the notebook; the id follows /synapsenotebooks/):

# wheel + notebook together (the F21 one-command path):
/opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_wheel.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --environment 1b87c0e2-f56c-4253-9933-fb7a60db181d --notebook <notebook-item-id>

# notebook only (no wheel build, no publish question):

SUPERSESSION (2026-09-30, ruled at the 04 M03 gate): the two phase-01
lakehouse tables — f01_subject_sql_files_lh_table and
f01_subject_sql_files_graph — are DELETED from AIVIA_01_LH, and the
AIVIA_01_GRAPH item's SQL_FILE declaration is retired; the item now
carries the phase-04 dictionary graph model (Table/Column nodes,
hasColumn/joins edges). The phase-02+ dictionary estate supersedes the
file-level graph. Nothing is lost: the local data sheet json stays the
truth, and one run of the F11 notebook recreates both tables if ever
wanted. This design doc and git remain the record of F11-F21 as built
and accepted.

/opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_notebook.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --notebook <notebook-item-id> --source AIVIA_01_Code/notebook_f11_load_lh_table.py

