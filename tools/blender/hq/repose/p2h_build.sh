#!/bin/bash
# Pass 2 heroes: re-rigged GLB -> re-posed arms (cfg/ID_arms.py) -> held props re-gripped (cfg/ID_propfix.txt, if any)
#   bash p2h_build.sh ID RIG.glb OUTDIR
set -e
ID=$1; RIG=$2; D=$3; H=$(cd "$(dirname "$0")" && pwd); mkdir -p $D
cd $H
if [ -f cfg/${ID}_arms.py ]; then
  python3 hero_arm.py $RIG $D/_arms.glb cfg/${ID}_arms.py $D/author_numbers.json > $D/author.log 2>&1 || { tail -20 $D/author.log; exit 1; }
else cp $RIG $D/_arms.glb; fi
if [ -f cfg/${ID}_propfix.txt ]; then
  python3 propgrip.py $D/_arms.glb $D/$ID.glb "$(tr -d '\n' < cfg/${ID}_propfix.txt)" > $D/propfix.log 2>&1 || { tail -20 $D/propfix.log; exit 1; }
  rm $D/_arms.glb
else mv $D/_arms.glb $D/$ID.glb; fi
python3 propgrip.py $D/$ID.glb 2>&1 | grep -E "jumps" > $D/propgrip.txt || true
echo "built $D/$ID.glb"
