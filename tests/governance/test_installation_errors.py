"""The error KB must align with the ops_installation_errors contract."""

from src.governance.installation_errors import ERROR_SEEDS
from src.schemas import INSTALLATION_ERRORS


def test_every_seed_matches_the_contract_shape():
    contract_columns = {c[0] for c in INSTALLATION_ERRORS["columns"]}
    for seed in ERROR_SEEDS:
        assert set(seed) == contract_columns, f"misaligned seed: {seed['error_signature']}"


def test_signatures_are_unique_and_fields_populated():
    signatures = [s["error_signature"] for s in ERROR_SEEDS]
    assert len(signatures) == len(set(signatures))
    for seed in ERROR_SEEDS:
        assert all(v.strip() for v in seed.values()), f"empty field in: {seed['error_signature']}"
