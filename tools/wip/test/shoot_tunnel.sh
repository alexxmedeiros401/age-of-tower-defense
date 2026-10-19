#!/bin/bash
# shoot_tunnel.sh OUTDIR MAP [extra args] -> frames of robots walking into the map's first tunnel
out=$(realpath -m "$1"); m=$2; shift 2
mkdir -p $out
cd /home/claude/age-of-tower-defense
export XDG_DATA_HOME=/tmp/claude-0/xdg_tunnel_$m_$$
U="$XDG_DATA_HOME/godot/app_userdata/Age of Tower Defense"
mkdir -p "$U"
rm -f "$U"/tunnel_*.png
timeout 300 xvfb-run -a -s "-screen 0 1280x720x24" godot --path . --rendering-driver opengl3 --resolution 1280x720 -- --demo --map=$m --shoot-tunnel "$@" > $out/log.txt 2>&1
grep -E "SCRIPT ERROR|Parse Error|TUNNEL" $out/log.txt | head -5
rm -f $out/tunnel_*.png
mv "$U"/tunnel_*.png $out/ 2>/dev/null
rm -rf "$XDG_DATA_HOME"
ls $out | grep -c png
