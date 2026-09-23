#!/bin/bash
T=/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp
for N in $(seq ${START:-1} 12); do echo "=== scene $N $(date +%H:%M:%S) ==="; out=$(bash $T/a23/up22.sh $N 2>&1); echo "$out" | tail -4; echo "$out" | grep -q "PUBLISHED" || { echo "UPLOAD_FAIL_AT $N"; exit 1; }; sleep 3; done
echo UPLOAD_LOOP_END
