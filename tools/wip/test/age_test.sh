#!/bin/bash
# age_test.sh OUT "unit ..." "map ..." CAPTURE_MAP KINDS
#   Attack captures: each unit up close attacking a column of robots (KINDS, comma list) on CAPTURE_MAP -> OUT/att_<unit>/
#   then a full auto-win match on each map -> OUT/aw_<map>.log; prints one line per capture and per match.
O=$(realpath -m "$1"); UNITS=$2; MAPS=$3; CMAP=$4; KINDS=$5
mkdir -p $O
cd /home/claude/age-of-tower-defense
L="flock /tmp/claude-0/heavy.lock"
for u in $UNITS; do
  X=/tmp/claude-0/xdg_att_$u; rm -rf "${X:?}"; mkdir -p "$X"
  UD="$X/godot/app_userdata/Age of Tower Defense"; mkdir -p "$UD"
  XDG_DATA_HOME=$X $L timeout 1800 xvfb-run -a -s "-screen 0 1920x1080x24" godot --path . --rendering-driver opengl3 \
    --resolution 1920x1080 --fixed-fps 30 -- --demo --map=$CMAP --shoot-attacks --unit=$u --focus --frames=40 --skip=1 \
    --kinds=$KINDS > $O/att_$u.log 2>&1
  mkdir -p $O/att_$u; mv "$UD"/atk_*.png $O/att_$u/ 2>/dev/null
  echo "ATT $u frames=$(ls $O/att_$u | grep -c png) errors=$(grep -c 'SCRIPT ERROR' $O/att_$u.log)"
  rm -rf "${X:?}"
done
for m in $MAPS; do
  X=/tmp/claude-0/xdg_aw_$m; rm -rf "${X:?}"; mkdir -p "$X"
  XDG_DATA_HOME=$X $L timeout 2400 godot --headless --path . -- --autowin --map=$m > $O/aw_$m.log 2>&1
  echo "$m $(grep -E 'AUTOWIN map=' $O/aw_$m.log | tail -1 | sed 's/newly.*//') errors=$(grep -c 'SCRIPT ERROR' $O/aw_$m.log)"
  rm -rf "${X:?}"
done
echo ALLDONE
