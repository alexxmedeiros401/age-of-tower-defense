#!/bin/bash
# resume a kit build from its sculpt (kit_hi.blend): the game stage (low poly, UVs, bakes), then the export
cd /home/claude/age-of-tower-defense/tools/blender/hq
for th in "$@"; do
  D=/home/claude/work/bronze/kits/$th
  echo "== $th game start $(date +%T)"
  python3 decor_build.py -- --theme $th --out $D --fine --tex 2048 --ao 24 --stage game > $D/build_game.log 2>&1 || echo "== $th game FAILED"
  python3 decor_build.py -- --theme $th --out $D --fine --tex 2048 --ao 24 --stage export > $D/build_export.log 2>&1 || echo "== $th export FAILED"
  grep "\[kit\] game done\|\[kit\] exported\|Traceback" $D/build_game.log $D/build_export.log | tail -3
  echo "== $th done $(date +%T)"
done
echo RESUME_DONE
