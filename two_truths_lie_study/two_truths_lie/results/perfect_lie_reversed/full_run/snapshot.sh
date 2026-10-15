#!/bin/bash
# Every 20 minutes while the follow-up run is alive: gzip a copy of each records.jsonl, commit the
# snapshot and manifests, push. A container restart then loses at most ~20 minutes of calls; resume
# by gunzipping the snapshot back to records.jsonl (the runner never repeats a completed cell).
cd "$(dirname "$0")"
REPO=$(git rev-parse --show-toplevel)
while true; do
  for s in main comprehension; do
    if [ -f $s/records.jsonl ]; then cp $s/records.jsonl $s/.snap && gzip -c $s/.snap > $s/records.jsonl.gz && rm $s/.snap; fi
  done
  git -C "$REPO" add -f $(ls -d */records.jsonl.gz */manifest.json run.log 2>/dev/null | sed "s|^|$PWD/|") >/dev/null 2>&1
  git -C "$REPO" commit -q -m "Reversed follow-up: full-run snapshot $(date -u +%FT%TZ)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_013SE24WnjYMuptK8z4542YA" >/dev/null 2>&1 && \
    for i in 1 2 3 4; do git -C "$REPO" push -q origin claude/confident-babbage-fljgmx >/dev/null 2>&1 && break; sleep $((2**i)); done
  pgrep -f "[r]un_perfect_lie_reversed.py --go" >/dev/null || { [ -n "$ONCE_MORE" ] && exit 0; ONCE_MORE=1; }
  sleep 1200
done
