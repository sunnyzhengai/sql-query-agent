# Testing Strategy

## Test Tiers

### 1. Unit Tests (`tests/test_*.py`)
Deterministic parser and builder tests. SQL in -> structured output. No LLM, no Fabric.

```bash
pytest tests/test_sql_parser.py tests/test_graph_builder.py tests/test_graph_traversal.py
```

### 2. Golden File Tests (`tests/golden/`)
Hand-verified graph JSON for critical queries. Ensures the graph builder produces the exact expected structure for known SQL inputs.

```bash
pytest tests/golden/
```

### 3. Acceptance Tests (`tests/acceptance/`)
Question -> expected traversal path + expected filter YAML. Tests graph traversal correctness, not LLM output quality.

```bash
pytest tests/acceptance/
```

## Running All Tests

```bash
pytest                    # all tests
pytest --cov=src          # with coverage
pytest -x                 # stop on first failure
```
