"""require_engine: the version-skew killer (ADR 0042)."""

import pytest

from src.engine_floor import require_engine


def test_older_engine_dies_loudly():
    with pytest.raises(SystemExit) as e:
        require_engine("1.17.2", "1.18", "200_parse")
    assert "200_parse" in str(e.value)
    assert "1.17.2" in str(e.value)


def test_equal_and_newer_pass():
    require_engine("1.18.0", "1.18", "200_parse")
    require_engine("1.18", "1.18", "200_parse")
    require_engine("2.0.0", "1.18", "200_parse")


def test_minor_compare_is_numeric_not_lexical():
    # 1.9 < 1.18 numerically (lexically "9" > "18" would pass wrongly)
    with pytest.raises(SystemExit):
        require_engine("1.9.0", "1.18", "nb")


def test_dev_suffixes_tolerated():
    require_engine("1.18.0.dev1", "1.18", "nb")
