# Fabric Environment Setup

## Why Fabric Environment (not %pip install)

`%pip install` inside notebooks triggers kernel restarts that permanently break
pythonnet's .NET CLR initialization. Fabric Environments pre-install packages
at the workspace level before any notebook starts, eliminating this issue.

## Setup Steps

### 1. Create Environment

1. Open your Fabric workspace
2. Click **+ New** → **Environment**
3. Name it: `sql-logic-env`

### 2. Add Python Dependencies

In the Environment settings → **Public libraries**:
1. Click **Add from requirements.txt**
2. Upload `requirements.txt` from this folder
3. Or manually add each package with its pinned version

### 3. Upload Custom Library (optional)

In the Environment settings → **Custom libraries**:
1. Upload `sql_query_agent-1.1.0-py3-none-any.whl` from `dist/`
2. This makes `from src.* import ...` available without `sys.path.insert`

### 4. Publish

Click **Publish** — Fabric builds the environment. Takes 2-5 minutes.

### 5. Attach to Notebooks

For each notebook:
1. Open the notebook
2. In the toolbar, click **Environment** dropdown
3. Select `sql-logic-env`
4. The notebook now uses the pre-installed packages

## Verification

After attaching, run this in any notebook cell:

```python
import pydantic, yaml, sqlglot, sqlparse
from pythonnet import load
try:
    load("coreclr")
except Exception:
    pass
import clr
print("All packages loaded successfully")
print(f"pydantic={pydantic.__version__}, sqlglot={sqlglot.__version__}")
```

## Updating Packages

When a new version is released:
1. Update `requirements.txt` with new versions
2. Build new `.whl`: `python -m build --wheel`
3. Upload both to the Environment
4. Click **Publish** to rebuild
5. All attached notebooks automatically use the new versions
