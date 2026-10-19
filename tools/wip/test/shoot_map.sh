#!/bin/bash
# shoot_map.sh OUTDIR MAP [extra args] -> the showcase shots of one map (battle with a boss, close, hub, ...)
out=$(realpath -m "$1"); m=$2; shift 2
mkdir -p $out
cd /home/claude/age-of-tower-defense
export XDG_DATA_HOME=/tmp/claude-0/xdg_show_$$
U="$XDG_DATA_HOME/godot/app_userdata/Age of Tower Defense"
mkdir -p "$U"
timeout 180 xvfb-run -a -s "-screen 0 1920x1080x24" godot --path . --rendering-driver opengl3 --resolution 1920x1080 -- --demo --shoot-showcase --map=$m --boss "$@" > $out/log.txt 2>&1
cp "$U"/showcase_${m}_*.png $out/ 2>/dev/null
rm -rf "$XDG_DATA_HOME"
echo "$m errors=$(grep -c 'SCRIPT ERROR' $out/log.txt) shots=$(ls $out | grep -c png)"
