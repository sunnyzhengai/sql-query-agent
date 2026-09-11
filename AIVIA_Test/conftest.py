"""AIVIA_Test — the M-ladder gate tests (Sunny's folder ruling
2026-09-10): the per-batch answer-key suites live here, beside
AIVIA_Design (the criteria) and AIVIA_Product (the estates),
starting with M1's. Same CLR teardown guard as tests/conftest.py
(the parser hosts the CLR in-process; finalization can segfault
after a green run — exit with the real status instead)."""

_exitstatus = 0


def pytest_sessionfinish(session, exitstatus):
    global _exitstatus
    _exitstatus = int(exitstatus)


def pytest_unconfigure(config):
    import sys
    if "clr" in sys.modules:
        import os
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(_exitstatus)
