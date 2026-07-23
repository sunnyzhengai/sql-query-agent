# libs/

Place external DLL files here for use in Fabric notebooks.

## Required for ScriptDom parsing:

1. Download from NuGet: https://www.nuget.org/packages/Microsoft.SqlServer.TransactSql.ScriptDom
2. Rename `.nupkg` to `.zip`, extract
3. Copy `lib/netstandard2.0/Microsoft.SqlServer.TransactSql.ScriptDom.dll` here

The `.dll` file is gitignored (binary, not source code).
