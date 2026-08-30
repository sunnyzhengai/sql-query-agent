#!/bin/zsh
# Nightly COLD battery (RW-25 standing acceptance): no warm-up —
# the overnight-idled store is the test. One summary line per run
# appended to internal/docs/NIGHTLY_BATTERY.md; pushed so the
# relay surfaces regressions to both sessions.
set -u
cd /Users/sunnyzheng/sql-query-agent || exit 1
git pull --rebase -q origin dev 2>/dev/null
LOG=/tmp/nightly_wb.log
WEBAPP_EAGER=1 python3.11 -m uvicorn src.webapp.main:app --port 8011 >"$LOG" 2>&1 &
WB=$!
for i in {1..30}; do curl -s -o /dev/null http://127.0.0.1:8011/ && break; sleep 2; done
OUT=internal/docs/NIGHTLY_TRANSCRIPT.md
python3.11 devtools/walk_runner_0062.py http://127.0.0.1:8011 "$OUT" >/dev/null 2>&1
kill $WB 2>/dev/null
Q=$(grep -c "^## " "$OUT" 2>/dev/null || echo 0)
ERR=$(grep -c "BATTERY ERROR\|conclusion kind: None\|error" "$OUT" 2>/dev/null || echo 0)
DIF=$(grep -c "verdict: DIFFERS" "$OUT" 2>/dev/null || echo 0)
STAMP=$(date "+%Y-%m-%d %H:%M")
if [ "$Q" -ge 22 ] && [ "$ERR" -eq 0 ] && [ "$DIF" -ge 3 ]; then V="PASS"; else V="FAIL"; fi
echo "- $STAMP cold run: $V — questions:$Q errors:$ERR differs:$DIF (no warm-up; idle store is the test)" >> internal/docs/NIGHTLY_BATTERY.md
git add internal/docs/NIGHTLY_BATTERY.md internal/docs/NIGHTLY_TRANSCRIPT.md
git commit -q -m "Nightly cold battery: $V (q:$Q err:$ERR)" && git push -q origin dev 2>/dev/null
