#!/bin/bash
# Rebuild one unit's work folder from what lives on GitHub (after a fresh container), so it can be re-rigged:
#   bash restore.sh ID [REF]      REF: an art-jobs branch (default: the newest one holding herotripo_in/ID)
# Writes:
#   /home/claude/work/heroglb/old/ID.glb      the model shipped BEFORE the Tripo rebuild (the rig's "old"; common.py)
#   /home/claude/work/heroglb/src/ID.glb      the compressed Tripo model, and plain/ID.glb (decoded)
#   /home/claude/work/herotripo/ID/prep/      labels.npz, patches.pkl, fit.json (from the branch), then old.py + load.py
#   /home/claude/work/herotripo/ID/bake_RUN/  the runner bake of that branch (low.blend + maps)
# When the unit's last branch was overwritten (no branch holds it), pass SRC=path/to/tripo.glb in the environment:
# cut.py, patches.py and fit.py are then re-run from the config, and BAKE=TAG_ID_RUN names the release zip to fetch.
set -e
ID=$1; REF=$2
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
G=/home/claude/work/heroglb; W=/home/claude/work/herotripo/$ID; P=$W/prep
mkdir -p $G/old $G/src $G/plain $P
cd "$REPO"
# 1. the pre-Tripo shipped model: the parent of the first commit that put a Tripo model in its asset path
for d in towers heroes robots; do [ -f assets/$d/$ID.glb ] && A=assets/$d/$ID.glb; done
[ -n "$A" ] || { echo "no shipped assets/*/$ID.glb"; exit 1; }
FIRST=$(git log --reverse --format='%H %s' -- "$A" | grep -i -m1 'tripo' | cut -d' ' -f1)
[ -n "$FIRST" ] || { echo "no Tripo commit for $A"; exit 1; }
git show "$FIRST^:$A" > $G/old/$ID.glb
echo "old: $A at ${FIRST:0:7}^ ($(stat -c%s $G/old/$ID.glb) bytes)"
# 2. the branch's inputs
if [ -z "$REF" ] && [ -z "$SRC" ]; then
  REF=$(for r in $(git for-each-ref --sort=committerdate --format='%(refname:short)' refs/remotes/aj); do
          git cat-file -e "$r:tools/blender/hq/herotripo_in/$ID/fit.json" 2>/dev/null && echo $r; done | tail -1)
fi
if [ -n "$REF" ]; then
  B=tools/blender/hq/herotripo_in/$ID
  for f in labels.npz patches.pkl fit.json; do git show "$REF:$B/$f" > $P/$f; done
  if git cat-file -e "$REF:$B/tripo_src.glb" 2>/dev/null; then git show "$REF:$B/tripo_src.glb" > $G/src/$ID.glb
  else git show "$REF:$B/tripo.glb" > $G/plain/$ID.glb; fi
  T=${REF#*/}; TAG=${T%-*}; RUN=${T##*-}; BAKE=${BAKE:-${TAG}_${ID}_${RUN}}
  echo "inputs: $REF"
else
  cp "$SRC" $G/src/$ID.glb
fi
# 3. decode, then the numpy prep steps that the branch does not carry
cd "$HERE"
[ -d node_modules ] || npm install --silent --no-audit --no-fund
[ -f $G/plain/$ID.glb ] || node decode.mjs $G/src/$ID.glb $G/plain/$ID.glb
python3 old.py -- --hero $ID > $W/old.log 2>&1 || { tail -20 $W/old.log; exit 1; }
python3 load.py -- --hero $ID > $W/load.log 2>&1 || { tail -20 $W/load.log; exit 1; }
if [ -z "$REF" ]; then
  python3 cut.py -- --hero $ID > $W/cut.log 2>&1 && python3 patches.py -- --hero $ID > $W/patches.log 2>&1 \
    && python3 fit.py -- --hero $ID > $W/fit.log 2>&1 || { echo "prep failed: see $W/*.log"; exit 1; }
fi
# 4. the bake
if [ -n "$BAKE" ]; then bash fetch.sh "$BAKE" "$W/bake_${BAKE##*_}" | tail -1; fi
echo "restored $ID"
