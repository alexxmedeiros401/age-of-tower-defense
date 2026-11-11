#!/bin/bash
# Cloud side: send a unit's rig + review job to the PC runner (Documents\AgeOfTD; see README.md).
#   bash tools/pc/push_pc.sh TAG RUN ID [ID ...]
# For each ID it puts on a new branch pc-jobs/TAG-RUN (made from the current commit, sparse: tools/ only):
#   pcin/ID/prep/{old.json,old.npz,fit.json,xf.json}   from /home/claude/work/herotripo/ID/prep
#   pcin/ID/bake/                                         the newest bake_* folder there (low.blend, low.json, maps)
#   pcin/old/ID.glb                                       /home/claude/work/heroglb/old/ID.glb (the pre-Tripo model)
# The config and scripts come from the branch's tools/. On the PC, `sh tools/pc/pcrig.sh pc-jobs/TAG-RUN ID ...`
# (run through the linked Linux shell) fetches the branch and queues the jobs. Commit your config changes first.
# Set BAKE=<folder> to pick a bake folder other than the newest.
set -e
TAG=$1; RUN=$2; shift 2
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
W=${HEROTRIPO_WORK:-/home/claude/work/herotripo}
BR=pc-jobs/$TAG-$RUN
JW=/tmp/claude-0/wt_pc_${TAG}_${RUN}
cd "$REPO"
BASE=$(git rev-parse HEAD)
git worktree remove --force "$JW" 2>/dev/null || true
git branch -D "$BR" 2>/dev/null || true
git worktree add -q --no-checkout -b "$BR" "$JW" "$BASE"
cd "$JW"
git sparse-checkout set --cone tools
git checkout -q "$BR"
for ID in "$@"; do
  P=pcin/$ID; mkdir -p $P/prep $P/bake pcin/old
  for f in old.json old.npz fit.json xf.json; do cp "$W/$ID/prep/$f" $P/prep/; done
  B=${BAKE:-$(ls -dt "$W/$ID"/bake_* | head -1)}
  for f in low.blend low.json hero_albedo.png hero_normal.png hero_orm.png; do [ -f "$B/$f" ] && cp "$B/$f" $P/bake/; done
  cp /home/claude/work/heroglb/old/$ID.glb pcin/old/$ID.glb
  echo "$ID: bake $(basename $B)"
done
git add --sparse -f pcin
git commit -qm "PC job: $TAG $RUN ($*)"
git push -q -f origin "$BR"
echo "pushed $BR"
cd "$REPO"
git worktree remove --force "$JW"
