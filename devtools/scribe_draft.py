"""Brief_Work_Dryrun (Sunny's "approved, both proposals stand",
2026-09-18): the Scribe draft driver — his paid run as ONE
command, for the work dry run and any estate here.

SHIM since Brief_Fabric_Resident (the turn-key ruling, 2026-09-19:
"all that can be packaged into .wheel, must be packaged"): the
driver core lives in aivia.fabric_run.scribe — ONE home; this
script keeps the CLI seat and the cheap refusals (no estate arg or
no key = exit 2 before any boot, spend, or network — the
AIVIA_RECORD posture). Landing approved text in descriptions.json
stays a human act everywhere.
"""
import sys


def _env_key() -> str:
    from aivia.console import _env_key as key
    return key()


def main(argv) -> None:
    if not argv:
        print("usage: python3.11 devtools/scribe_draft.py "
              "<estate>  (an estate folder name under "
              "AIVIA_Product/estates/, or a path to an estate "
              "folder)", file=sys.stderr)
        raise SystemExit(2)
    key = _env_key()
    if not key:
        print("no OPENAI_API_KEY (repo .env or environment) — "
              "the Scribe is a paid seat and never runs without "
              "the key at hand", file=sys.stderr)
        raise SystemExit(2)
    from aivia import fabric_run
    fabric_run.scribe(argv[0], key=key)


if __name__ == "__main__":
    main(sys.argv[1:])
