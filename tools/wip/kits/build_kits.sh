#!/bin/bash
# the fine builds of the Bronze Age kits, one at a time (a kit bake peaks near 2.6 GB)
cd /home/claude/age-of-tower-defense/tools/blender/hq
for th in "$@"; do
  D=/home/claude/work/bronze/kits/$th
  mkdir -p $D
  echo "== $th start $(date +%T)"
  python3 decor_build.py -- --theme $th --out $D --fine --tex 2048 --ao 24 --shots $D/shots --each > $D/build.log 2>&1 || echo "== $th FAILED"
  grep "\[kit\] game done\|\[kit\] exported\|Traceback" $D/build.log | tail -3
  echo "== $th done $(date +%T)"
done
echo KITS_DONE
