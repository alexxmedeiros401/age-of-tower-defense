#!/bin/bash
# Start runner bakes: push an art-jobs branch with the heroes' inputs (see README.md, step 6).
#   bash push_bake.sh TAG RUN ID [ID ...]      e.g.  bash push_bake.sh herotripo b1 ugo mara
# For each ID: the compressed Tripo GLB (heroglb/src/ID.glb, decoded on the runner) and the work folder's labels.npz,
# patches.pkl and fit.json go to tools/blender/hq/herotripo_in/ID/ on a new branch art-jobs/TAG-RUN made from the
# current commit of the worktree this script lives in (commit your script and config changes first). One job per hero;
# each result comes back as TAG_ID_RUN.zip on the draft release art-builds (fetch.sh).
set -e
TAG=$1; RUN=$2; shift 2
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
WORK=${HEROTRIPO_WORK:-/home/claude/work/herotripo}
SRC=${HEROGLB_SRC:-/home/claude/work/heroglb/src}
BR=art-jobs/$TAG-$RUN
JW=/tmp/claude-0/wt_${TAG}_jobs
cd "$REPO"
BASE=$(git rev-parse HEAD)
git worktree remove --force "$JW" 2>/dev/null || true
git branch -D "$BR" 2>/dev/null || true
git worktree add -q -b "$BR" "$JW" "$BASE"
cd "$JW"
JOBS="["
SEP=""
for ID in "$@"; do
  D=tools/blender/hq/herotripo_in/$ID
  mkdir -p $D
  cp "$SRC/$ID.glb" $D/tripo_src.glb
  for f in labels.npz patches.pkl fit.json; do cp "$WORK/$ID/prep/$f" $D/; done
  N=${TAG}_${ID}_${RUN}
  CMD="O=\$GITHUB_WORKSPACE/out/$N; mkdir -p \$O\npip install -q xatlas==0.0.11\n(cd herotripo_prep && npm install --silent --no-audit --no-fund && node decode.mjs ../herotripo_in/$ID/tripo_src.glb ../herotripo_in/$ID/tripo.glb)\npython3 herotripo_bake.py -- --hero $ID --in herotripo_in/$ID --out \$O > \$O/bake.log 2>&1 || (tail -80 \$O/bake.log; exit 1)\ngrep '^\\\\[ht\\\\]' \$O/bake.log | tail -40; rm -f \$O/tex_*; ls -la \$O"
  JOBS="$JOBS$SEP{\"name\": \"$N\", \"cmd\": \"$CMD\", \"out\": \"out/$N\"}"
  SEP=","
done
JOBS="$JOBS]"
printf '%b' "$JOBS" | python3 -c "import json,sys; d=json.loads(sys.stdin.read().replace('\n','\\\\n')); json.dump(d, open('art_jobs.json','w'), indent=1); print(json.dumps(d, indent=1))"
git add -f art_jobs.json tools/blender/hq/herotripo_in
git commit -qm "Art jobs: $TAG $RUN ($*)"
git push -q -f origin "$BR"
echo "pushed $BR"
cd "$REPO"
git worktree remove --force "$JW"
