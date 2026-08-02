"""Pipeline step functions — the pure core of each notebook.

Each step is a pure function: contract-shaped rows in, contract-shaped rows
out. No Spark, no storage, no Fabric — fully executable locally and in CI.
Notebooks are thin shells: read Delta -> call step -> write Delta -> run the
postcondition gate (gates.postcondition_gate).

Flow contracts live at two levels (see ADR discussion 2026-08-02):
- Logic relations (input<->output laws of the transformation) are asserted
  INSIDE each step — they hold wherever the step runs.
- State relations (what actually landed in Delta) are checked by the
  notebook-boundary gate, driven by the table contracts in src/schemas.py.
"""
