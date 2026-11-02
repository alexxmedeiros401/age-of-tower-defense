#!/bin/bash
# Start runner bakes: push an art-jobs branch with the heroes' inputs (see README.md, step 6).
#   bash push_bake.sh TAG RUN ID [ID ...]      e.g.  bash push_bake.sh herotripo b1 ugo mara
# For each ID: the compressed Tripo GLB (heroglb/src/ID.glb, decoded on the runner; the plain heroglb/plain/ID.glb
# when there is no compressed one) and the work folder's labels.npz,
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
for ID in "$@"; do
  D=tools/blender/hq/herotripo_in/$ID
  mkdir -p $D
  if [ -f "$SRC/$ID.glb" ]; then cp "$SRC/$ID.glb" $D/tripo_src.glb      # compressed (decoded on the runner)
  else cp "${HEROGLB_PLAIN:-/home/claude/work/heroglb/plain}/$ID.glb" $D/tripo.glb; fi   # or the plain one (~65 MB)
  for f in labels.npz patches.pkl fit.json; do cp "$WORK/$ID/prep/$f" $D/; done
done
python3 - "$TAG" "$RUN" "$@" <<'PY'
import json, sys
tag, run, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
jobs = []
for i in ids:
    n = "%s_%s_%s" % (tag, i, run)
    cmd = "\n".join([
        "O=$GITHUB_WORKSPACE/out/%s; mkdir -p $O" % n,
        "pip install -q xatlas==0.0.11",
        "[ -f herotripo_in/%s/tripo.glb ] || (cd herotripo_prep && npm install --silent --no-audit --no-fund && node decode.mjs ../herotripo_in/%s/tripo_src.glb ../herotripo_in/%s/tripo.glb)" % (i, i, i),
        "python3 herotripo_bake.py -- --hero %s --in herotripo_in/%s --out $O > $O/bake.log 2>&1 || (tail -80 $O/bake.log; exit 1)" % (i, i),
        "grep '^.ht.' $O/bake.log | tail -40; rm -f $O/tex_*; ls -la $O"])
    jobs.append(dict(name=n, cmd=cmd, out="out/" + n))
json.dump(jobs, open("art_jobs.json", "w"), indent=1)
print(json.dumps(jobs, indent=1))
PY
git add -f art_jobs.json tools/blender/hq/herotripo_in
git commit -qm "Art jobs: $TAG $RUN ($*)"
git push -q -f origin "$BR"
echo "pushed $BR"
cd "$REPO"
git worktree remove --force "$JW"
