# libs/

The ScriptDom DLL ships HERE — tracked in the repo (MIT-licensed,
github.com/microsoft/SqlScriptDOM) and included in every ship zip.
Nothing to download.

- `Microsoft.SqlServer.TransactSql.ScriptDom.dll` — file version
  18.0.78.1, 6.9 MB, sha256
  `400a457ae1f34f54063538aa1e6c4ce80893d2dd709690cf42789bfb05ce54d3`.
  The ONLY parser (the native-parser law, ADR 0001); the parse
  validation and the recorded fixtures came from this exact binary.

Where it runs:

- Laptop: the loader (`aisql/graph/kg2_mapper/scriptdom_loader.py`)
  finds it in this folder automatically.
- Fabric: this same file, uploaded once to the lakehouse Files.

Replacing the DLL is a ruled change (its own brief): the new binary
from NuGet `Microsoft.SqlServer.TransactSql.ScriptDom`
(`lib/netstandard2.0/`), with the version + hash lines above and
the recorded fixtures re-verified in the same act.
