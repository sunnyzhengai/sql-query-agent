# 04_fabric_move — production runbook

Sunny's manual runbook for the phase 04 move. Every file name and
command exact. Written by Claude 2026-09-30; grows as steps land.

> **Status:** Steps A–C ran clean 2026-09-30 (Sunny) — golden counts to
> the digit. Step E PASSED 2026-09-30 — all four gate probes matched
> the ground truth. Step F PASSED 2026-10-01 — census matched local to
> the digit, all twelve shapes green Fabric-backed. Next: M05.

---

## Prerequisites — check once

- [x] The Fabric workspace exists and opens in the portal.
- [x] Environment item **AIVIA_01_ENV** exists, with `openai 3.19.2` in
  its public libraries (set once, phase 01).
- [x] Lakehouse **AIVIA_01_LH** exists.
- [x] The ids (from portal URLs when each item is open):

  | item | id |
  |---|---|
  | workspace | `23112b57-368a-46ed-941b-c10e3baad392` |
  | environment | `1b87c0e2-f56c-4253-9933-fb7a60db181d` |
  | lakehouse | `891d75cb-c87e-4096-9383-9cd7df9d6ef3` |
  | notebook (nb_m02_load_dictionary) | `3fbc2a7d-fb79-4893-8b50-a837614146fb` |

- [ ] Local suite green first:

  ```
  /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v
  ```

- [ ] All commands run from the repo root: `cd /Users/sunnyzheng/sql-query-agent`

---

## Step A — ship the wheel + the M02 notebook definition

One command: builds the wheel, browser sign-in, removes stale wheels,
uploads, pushes the notebook cell, then **asks** before publishing
(publish = capacity, several minutes).

**Paste as ONE line** (a multi-line paste drops the backslashes and zsh
splits it into broken commands — met live 2026-09-30):

```
/opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_wheel.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --environment 1b87c0e2-f56c-4253-9933-fb7a60db181d --notebook 3fbc2a7d-fb79-4893-8b50-a837614146fb --notebook-source AIVIA_01_Code/notebook_m02_load_dictionary_tables.py
```

- At `Publish environment now? [y/N]` — answer `y` when ready to spend
  the capacity; `N` leaves it staged.
- Success: publish state `success`, and **aivia01 0.3.0** in the
  printed libraries next to openai 3.19.2.

---

## Step B — upload the asset files (the transport)

```
/opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_files.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --lakehouse 891d75cb-c87e-4096-9383-9cd7df9d6ef3
```

The eight files it ships (local → `Files/Data/...`, same names):

| file | size |
|---|---|
| 02_emr_data_dictionary_extraction_table.json | small |
| 02_emr_data_dictionary_extraction_column.json | ~254 MB |
| 02_emr_data_dictionary_extraction_join.json | small |
| 02_emr_data_dictionary_extraction_value.json | small |
| 02_emr_data_dictionary_extraction_value_embeddings.json | ~1.1 GB |
| 02_no_dictionary_match.json | tiny |
| 03_chat_technical_terms.md | tiny |
| 03_chat_abstract_names.json | ~720 KB |

Unchanged files (same size remotely) are skipped; `--force` re-uploads
everything. The big two take a few minutes; progress prints per 32 MB
chunk.

---

## Step C — run the M02 notebook (capacity: your go)

1. Open the notebook in the portal.
2. Attach environment **AIVIA_01_ENV** and lakehouse **AIVIA_01_LH**
   (default).
3. The one cell is already there from Step A. **Run**.
4. **The acceptance** — printed counts must equal the golden numbers to
   the digit, and the census line must end `joinsByFk 210,
   joinsByRule 181`:

   | table | count | table | count |
   |---|---|---|---|
   | dict_tables | 38 | dict_columns | 1618 |
   | dict_joins | 5262 | dict_values | 14476 |
   | dict_value_embeddings | 14476 | dict_no_match | 1 |
   | chat_abstract_names | 1656 | chat_technical_terms | 9 |
   | graph_join_edges | 391 | graph_table_nodes | 38 |
   | graph_column_nodes | 1618 | | |

   Any other number = **STOP**; the loader fails loudly on drift, so a
   wrong count means something upstream moved — bring the verbatim
   output to the chat session.
5. Your eye: AIVIA_01_LH → Tables shows the eleven; spot-check
   `dict_tables` (camelCase columns, PATIENT's description reads right).

---

## Step D — verify from the SQL endpoint (optional)

```sql
SELECT COUNT(*) FROM dict_tables;                           -- 38
SELECT COUNT(*) FROM dict_columns;                          -- 1618
SELECT kind, COUNT(*) FROM graph_join_edges GROUP BY kind;  -- joins_by_fk 210 / joins_by_rule 181
SELECT TOP 5 tableName, code, meaning FROM dict_values
 WHERE tableName = 'ZC_DISCH_DISP';                         -- verbatim meanings
```

---

## Step E — M03: the graph model + the validation gate

Capacity: your go. Results land in `04_fabric_move.md` same-day.

### E1 — re-use AIVIA_01_GRAPH (ruled 2026-09-30)

The item is a container for a declaration and its name is
phase-neutral — one graph model for the workspace. Open it and
**delete the phase-01 declaration** (the `SQL_FILE` node; its record
lives in git and the docs). The stale "couldn't load your data" banner
belongs to the old f01 mapping and dies with it.

### E2 — declare the model

**The law: only the three `graph_*` tables, NEVER `dict_*`** — their
3,072-number embedding columns break the graph mapping (met live at
F12/F13).

| element | label | from table | keys |
|---|---|---|---|
| node | `Table` | graph_table_nodes | key `tableId` |
| node | `Column` | graph_column_nodes | key `columnId` |
| edge | `hasColumn` | graph_column_nodes | source `tableId` → Table, target `columnId` → Column |
| edge | `joins` | graph_join_edges | source `sourceTableId` → Table, target `destinTableId` → Table |

`joins` properties: kind, edgeKey, rule, columnPairs, conditionalC,
mayBeStaleC, isCurrentDataModelYn, isSupplementalYn.

(`graph_column_nodes` serves as node table **and** edge table — its
`tableId` column is the ownership edge.)

Save, then build/refresh the model — the capacity spend.

### E3 — the validation gate

Run in the graph query experience; compare to the expected answers
(computed from the local engine, the ground truth). Record what you
actually ran and got, verbatim.

**Fabric GQL laws, met live 2026-09-30:** every returned expression
must carry an `AS` alias; grouped aggregation is refused in both
implicit and explicit forms — filtered counts are the form.

**Probe 1 — node census**

```
MATCH (t:Table) RETURN count(t) AS tableCount
MATCH (c:Column) RETURN count(c) AS columnCount
```

| query | expected |
|---|---|
| tableCount | **38** |
| columnCount | **1618** |

**Probe 2 — edge census by kind** (the L08 provenance law intact)

```
MATCH ()-[e:joins]->() WHERE e.kind = 'joins_by_fk' RETURN count(e) AS n
MATCH ()-[e:joins]->() WHERE e.kind = 'joins_by_rule' RETURN count(e) AS n
MATCH ()-[e:hasColumn]->() RETURN count(e) AS n
```

| query | expected |
|---|---|
| joins_by_fk | **210** |
| joins_by_rule | **181** |
| hasColumn | **1618** |

**Probe 3 — one component of 38** (reachability census from PATIENT)

```
MATCH (a:Table {tableName: 'PATIENT'})-[:joins]-{0,2}(t:Table)
RETURN count(DISTINCT t) AS reachable
```

Expected: **38** — every table reachable from PATIENT within TWO
undirected hops = one component, and the estate's true radius (the
local BFS histogram: 1 + 20 at one hop + 17 at two). DATE_DIMENSION
connects only through `joins_by_rule`, so this probe also proves the
rule edges landed.
(Met live 2026-09-30: a {0,20} bound ran for minutes — GQL pattern
matching ENUMERATES paths, and twenty hops through hub tables
explodes; bound quantified patterns by the graph's real radius.)

**Probe 4 — ZC_STATE's 9 edges, FK owners correct**

```
MATCH (src:Table)-[e:joins]->(dst:Table {tableName: 'ZC_STATE'})
RETURN src.tableName AS owner, e.kind AS kind
```

Expected: exactly **9 rows**, all `joins_by_fk`, all with ZC_STATE as
the **destination** (the owners point at the category — the stored
direction, never flipped):

| owner | rows |
|---|---|
| CLARITY_DEP | 1 |
| CLARITY_EPM | 2 |
| COVERAGE_MEMBER_LIST | 2 |
| PATIENT | 2 |
| PATIENT_4 | 1 |
| PAT_RELATIONSHIP_LIST | 1 |

And the reverse direction must be empty:

```
MATCH (src:Table {tableName: 'ZC_STATE'})-[e:joins]->(dst:Table)
RETURN count(e) AS n
```

Expected: **0**.

### E4 — the verdict

All four probes matching = the gate **passes**; paste the verbatim
results into the chat session and the pass lands in `04_fabric_move.md`
dated. Any mismatch = **STOP**, bring the verbatim output — the local
engine is the ground truth and the model's *declaration* (not the
data) is the first suspect.

The chat does **not** read this model — it stands validated for the
future query-writing phase.

---

## Troubleshooting (failures we have actually met)

| symptom | cause and fix |
|---|---|
| Sign-in error 530035 | Device-code flow blocked by tenant security; the scripts use browser sign-in — rerun and complete the sign-in page. |
| SystemError1009 on a table load | Transient Fabric fault on trial capacity (met at F12/F13) — rerun the cell. |
| openai `billing_not_active` | OpenAI credit balance empty (Settings → Billing → Add credits). Local builds only; nothing in Fabric calls OpenAI. |
| Count mismatch in Step C | Never hand-edit lakehouse tables — local sheets are the truth; fix locally, rerun Steps B then C. |
| GQL `expecting 'AS'` | Every returned expression needs an alias: `count(t) AS n`. |
| GQL "not part of GROUP BY" | Grouped aggregation unsupported — use filtered counts (Probe 2's form). |
| Multi-line paste breaks | Paste commands as one line; zsh drops the backslashes. |
| GQL quantified path runs forever | Pattern matching enumerates paths — bound `{0,n}` by the graph's real radius (2 from PATIENT), never a generous guess. |
| Azure `DeploymentNotFound` | The deployments landed on the WRONG resource — the Foundry portal defaults to its own project (founder-9856-resource). Deploy via: aivia resource → Go to Foundry portal → flip the New Foundry toggle OFF → pick aivia → Deployments. |
| text-embedding-3-small anywhere | FORBIDDEN near the pipeline (the parity law) — delete the deployment on sight. |

---

## Step F — M04 stage A: the chat reads FROM Fabric

The same chat, the Delta tables as its source — browser sign-in, the
eight chat tables read over OneLake, then the server runs exactly as
local. Each question still costs one gpt-5-mini call + at most one
embedding call (OpenAI — M05 moves these to Azure).

**Paste as ONE line:**

```
/opt/homebrew/bin/python3.11 AIVIA_01_Code/chat_bot.py --fabric --workspace=23112b57-368a-46ed-941b-c10e3baad392 --lakehouse=891d75cb-c87e-4096-9383-9cd7df9d6ef3
```

(Note: the `--fabric` form uses `--workspace=<id>` with an equals sign.)

**The acceptance:**

1. The startup census prints `assets: fabric` and matches the local
   census **to the digit**: tables 38, columns 1618, values 14476,
   abstract_rows 1656, keywords 9, and the map's 122 + 18 edge lines.
2. The twelve shapes rerun against http://localhost:8703 by your hand
   — identical behavior to the local runs.

Reading the big embedding tables over the network takes a minute or
two at startup; the per-table progress prints.

---

## Step G — M05: the Azure OpenAI estate (your portal acts)

The chat's brains move from OpenAI (.env key) to YOUR Azure OpenAI,
keys in Key Vault — the launch posture. One-time setup, then the build
follows pseudo-first.

### G1 — re-use the existing resource (found 2026-10-01)

The Azure OpenAI resource **`aivia`** already exists in
`rg-fabric-prod`, East US 2 — re-use it, do NOT create a second.
Its endpoint lives on its **Keys and Endpoint** blade
(`https://aivia.openai.azure.com/` or the cognitiveservices form —
copy what the blade shows, exactly).

### G2 — the two model deployments

Open `aivia` → **Go to Azure AI Foundry portal** → **Deployments**.
Check what is already deployed; create what is missing via
**Deploy model → Deploy base model**:

| model | why | suggested deployment name |
|---|---|---|
| `text-embedding-3-large` | THE PARITY LAW — exactly this model or every stored embedding regenerates | `embed-3-large` |
| `gpt-5-mini` (or the small chat model the catalog offers) | segmentation | `chat-mini` |

Deployment type Standard or Global Standard — either. **Note the
deployment names you actually choose — the code calls them by name.**

### G3 — the Key Vault and the secret (closes the standing TBDs)

**1. Create the vault**

1. Portal top search → **Key vaults** → **+ Create**.
2. Basics: subscription `Azure subscription 1`; resource group
   `rg-fabric-prod`; name **`aivia01-kv`**; region **East US 2**;
   pricing tier **Standard**.
3. Access configuration tab: leave **Azure role-based access control
   (recommended)**.
4. **Review + create** → **Create** (~30s).

**2. Grant yourself secret-writing rights** — with RBAC, creating the
vault does NOT grant data-plane rights; the Secrets page refuses until:

1. Vault → **Access control (IAM)** → **+ Add → Add role assignment**.
2. Role **Key Vault Secrets Officer** → Members: your own account →
   **Review + assign** (give it a minute).

**3. Fetch the key and endpoint**

`aivia` resource → **Keys and Endpoint** blade → copy **KEY 1** and
the **Endpoint** URL.

**4. Store the secret**

Vault → **Objects → Secrets** → **+ Generate/Import** → name
`aivia01-azure-openai-key` → value = KEY 1 → **Create**.

**THE KEY LAW: the key value lives ONLY in the vault and the local
.env — never in this runbook, never in git.** After storing, rotate:
`aivia` → Keys and Endpoint → **Regenerate Key 1**, then update the
vault secret — any copy that traveled through chat or terminal dies.

### G4 — the facts (filled 2026-10-01)

| fact | value |
|---|---|
| endpoint URL | `https://aivia.openai.azure.com/` |
| embedding deployment name | `text-embedding-3-large` (Foundry default — equals the model name) |
| chat deployment name | `gpt-5.4-mini` (ADOPTED 2026-10-01 — found already deployed on aivia, newer; chat has no parity law) |
| vault name | `aivia01-kv` |
| secret name | `aivia01-azure-openai-key` |
| the key | NOT RECORDED — vault + local .env only, per the key law |

The build then starts: the chat's Azure mode (parameter, never a
fork), the PARITY CHECK (one known text re-embedded on the Azure
deployment, compared number-for-number to the stored vector,
recorded), and the 02/03/04 contracts' secret-name TBDs close.

---

## Step H — M05: run with Azure models (the production shape)

The full production shape — data from the lakehouse, brains from your
Azure, keys governed. **Paste as ONE line:**

```
/opt/homebrew/bin/python3.11 AIVIA_01_Code/chat_bot.py --fabric --azure --workspace=23112b57-368a-46ed-941b-c10e3baad392 --lakehouse=891d75cb-c87e-4096-9383-9cd7df9d6ef3
```

The census prints `assets: fabric` and `models: azure
(https://aivia.openai.azure.com/)`. (--azure also works with local
assets: the two flags are independent.)

The parity check, rerunnable any time (also a standing suite test):

```
/opt/homebrew/bin/python3.11 AIVIA_01_Code/azure_models.py --parity AIVIA_01_Data/02_emr_data_dictionary
```

Recorded 2026-10-01: cosine **0.999999** — PASS.

---

## What comes after (lands here as each step builds)

- **M06** — DONE 2026-10-01: scorecard complete in the 04 shapes md (ours 11/11 · Round A 0/2 structural · Round B 5/5/1).
- **Cleanup (ruled, after the E gate passes):** delete the two phase-01
  leftovers `f01_subject_sql_files_lh_table` and
  `f01_subject_sql_files_graph` — regenerable from local truth; a dated
  supersession line lands in the phase-01 design doc.
