#!/bin/bash
# pose strips of the quick build: every other frame of each clip, small and fast
B=${1:-/home/claude/work/iron/javelin/qb/char_game.blend}
O=${2:-/home/claude/work/iron/javelin/poses}
cd /home/claude/age-of-tower-defense/tools/blender/hq
mkdir -p $O
python3 render_asset.py -- --blend $B --out $O --mode frames --action Attack --range 0,24 --step 2 --spp 6 --res 360 --tz 1.0 --dist 7.0 > $O/attack.log 2>&1
python3 render_asset.py -- --blend $B --out $O --mode frames --action Combat --range 0,40 --step 10 --spp 6 --res 360 --tz 1.0 --dist 7.0 > $O/combat.log 2>&1
python3 render_asset.py -- --blend $B --out $O --mode frames --action Idle --range 0,120 --step 15 --spp 6 --res 360 --tz 1.0 --dist 7.0 > $O/idle.log 2>&1
echo POSES_DONE
