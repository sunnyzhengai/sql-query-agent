"""L0 tests for the answer_evals INFRA-SKIP contract (2026-08-22 outage
find, closed 2026-08-23): transport-dead questions skip loudly; >20% of
attempted questions skipped aborts the run as infrastructure-invalid.

Proves: contract:suite-integrity
"""

from devtools.answer_evals import (
    INFRA_ABORT_FRACTION,
    INFRA_ABORT_MIN_ATTEMPTS,
    infra_abort,
)


def test_no_abort_below_min_attempts():
    # 3 of 3 skipped is 100%, but the floor keeps an early blip alive
    assert infra_abort(skipped=3, graded=0) is False


def test_no_abort_at_exactly_the_fraction():
    # 2 of 10 = exactly 20% — the contract is STRICTLY more than
    assert infra_abort(skipped=2, graded=8) is False


def test_abort_above_the_fraction():
    assert infra_abort(skipped=3, graded=9) is True


def test_abort_on_the_outage_shape():
    # the field corpse: ~6-minute outage mid-suite — many consecutive
    # skips against a graded prefix must abort, not grind on
    assert infra_abort(skipped=10, graded=37) is True


def test_clean_run_never_aborts():
    assert infra_abort(skipped=0, graded=60) is False


def test_constants_are_the_documented_contract():
    assert INFRA_ABORT_FRACTION == 0.20
    assert INFRA_ABORT_MIN_ATTEMPTS == 10
