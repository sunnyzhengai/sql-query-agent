"""Shared pytest wiring.

coreclr teardown guard: with the CLR hosted in-process, CPython
finalization can segfault AFTER a fully green run (observed on the CI
3.9 leg, 1.32.0: '801 passed' then exit 139 at shutdown). When clr is
loaded, exit with the REAL pytest status after the summary prints,
skipping interpreter finalization — the crash was cosmetic; masking
the true result was not.
"""

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
