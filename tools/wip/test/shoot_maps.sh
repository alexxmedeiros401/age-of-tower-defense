#!/bin/bash
# usage: shoot_maps.sh OUTROOT map1 map2 ...   (showcase battle shot per map)
out=$1; shift
cd /home/claude/age-of-tower-defense
U="/root/.local/share/godot/app_userdata/Age of Tower Defense"
for m in "$@"; do
  rm -f "$U"/showcase_*.png
  timeout 120 xvfb-run -a -s "-screen 0 1920x1080x24" godot --path . --rendering-driver opengl3 --resolution 1920x1080 -- --demo --shoot-showcase --map=$m --boss > /tmp/shoot_$m.log 2>&1
  mkdir -p $out/$m; cp "$U"/showcase_${m}_*.png $out/$m/ 2>/dev/null
  echo "$m errors=$(grep -c 'SCRIPT ERROR' /tmp/shoot_$m.log) stale=$(grep -c stale /tmp/shoot_$m.log)"
done
