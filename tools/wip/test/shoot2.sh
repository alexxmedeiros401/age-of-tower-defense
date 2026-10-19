#!/bin/bash
# shoot2.sh OUTDIR UNIT [extra game args]  -> attack frames at a fixed 30 fps, 1280x720, own user-data dir
out=$(realpath -m "$1"); unit=$2; shift 2
mkdir -p $out
cd /home/claude/age-of-tower-defense
export XDG_DATA_HOME=/tmp/claude-0/xdg_shoot
U="$XDG_DATA_HOME/godot/app_userdata/Age of Tower Defense"
mkdir -p "$U"
rm -f "$U"/atk_*.png
timeout 400 xvfb-run -a -s "-screen 0 1280x720x24" godot --path . --rendering-driver opengl3 --resolution 1280x720 --fixed-fps 30 -- --demo --map=${MAP:-mammoth_valley} --shoot-attacks --unit=$unit "$@" > $out/log.txt 2>&1
grep -E "SCRIPT ERROR|Parse Error|ATTACKS" $out/log.txt | head -5
rm -f $out/atk_*.png
mv "$U"/atk_*.png $out/ 2>/dev/null
ls $out | grep -c png
