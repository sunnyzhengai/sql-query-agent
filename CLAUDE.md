# AIVIA — sql-query-agent
Owner: Sunny Zheng (she)
Development Principle: Each development phase is independently designed, developed and tested. No mockups or shortcuts. All development is dynamic and can be shipped to enterprise customers without breaking down.
Development Discipline: Sunny defines the phase, data contract, test cases. Claude reviews and understands these documents. Claude gives advice to Sunny, and discuss the plan until both agree. Claude develops and tests until all pass.
Development Process: Design, plan and develop locally. Then move code and data to Fabric. 

## THE CHANGE PROCESS — mandatory, before ANY code change
All work is done in the sunnyzheng/sql-query-agent/AIVIA_01_* folders.
Sunny is the only author for AIVIA_01_Design/, AIVIA_01_Data/ folders.
Claude can edit or author in AIVIA_01_Code/, AIVIA_01_Test/ folders.
Claude needs permission from Sunny to create, update any files and folders.

## Standing laws (bind every change)
In chat session, Sunny gives instruction on which phase to build.
Before building a phase, Sunny and Claude plan together to document and agree on:
- AIVIA_01_Design/##_<phase name>.md: documents all design decisions. Claude reviews and asks questions to fully understand what to build.
- AIVIA_01_Design/##_<phase name>_data_contract.md: documents input, output, definitions and authorship.
- AIVIA_01_Test/test_##_<data_contract>.py: documents all Claude created tests.
- AIVIA_01_Test/test_##_<data_contract>_sunny.md: documents Sunny's hand written test cases. Claude updates with the manual test command Sunny needs to use to run these tests after build.
Claude writes one code file at a time.
Claude writes pseudo code as comments in AIVIA_01_Code/ folder code file first.
Sunny reviews the pseudo code and approves or asks questions until both agree.
Claude writes the actual code right after the commented pseudo code.
Tests red before code, verbatim pytest results, Sunny validates by running the same command and eyeballing the artifacts.
Claude tests the two test suites (Sunny's and Claude's) and code until all test results are green.
Chat rulings land in the phase docs the same day.
All LLM calls use paid API calls, no fake calls.

## Where truth lives


## Working with Sunny


## Operational facts
- The one Python: /opt/homebrew/bin/python3.11 runs all tests and scripts — never Apple's Python, never a venv.
- The test command: /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v
- Installed packages, pinned: openai 3.19.2, pytest 9.1.1, ruff 0.16.3, pythonnet 3.1.0, deltalake 1.6.3 (ruled 2026-09-30 at M04 — local Delta reads from OneLake; never ships in the wheel, Fabric notebooks keep Spark).
- ScriptDom (ADR 0001, the only T-SQL parser): DLL at libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll (18.0.78.1, tracked in git); .NET 8 runtime at ~/.dotnet (the loader asserts DOTNET_ROOT only if that folder exists); the one parse door is AIVIA_01_Code/scriptdom_loader.py — no other file instantiates the parser (test-locked).
- The OPENAI_API_KEY and AZURE_OPENAI_KEY live in .env at repo root (local development); production Azure key: Key Vault aivia01-kv / aivia01-azure-openai-key.

