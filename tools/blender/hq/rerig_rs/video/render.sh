#!/bin/bash
# Before/after renders of the full attack, played the way the game plays it (rig/rs_fight.py), then compose.py.
#   bash video/render.sh [old|new|both]      old = src/rock_slinger_before.glb, new = out/rock_slinger.glb
# About 0.7 s a frame on 2 cores; the BEFORE half does not change when the new unit does.
cd "$(dirname "$0")/.."
R="python3 -I rig/rs_fight.py --"
C="--first 1.0 --shots 4 --tail 1.2 --cd 0.85 --rock --rx 720 --ry 600 --aa 8 --noshadow --size 4.3"
which=${1:-both}
for u in old new; do
  [ "$which" = both ] || [ "$which" = $u ] || continue
  if [ $u = old ]; then G=src/rock_slinger_before.glb; else G=out/rock_slinger.glb; fi
  rm -rf video/A_$u video/B_$u video/C_$u video/D_$u
  $R $G video/A_$u $C --az 325 --elev 20 --ctr 0,0.06,1.72 2>&1 | grep rendered                                 # the full attack, game speed
  $R $G video/B_$u $C --az 325 --elev 20 --ctr 0,0.06,1.72 --slow 4 --t0 0.9 --t1 1.95 2>&1 | grep rendered     # first two shots, x4 slower
  $R $G video/C_$u $C --az 175 --elev 20 --ctr 0,0.06,1.72 --slow 4 --t0 0.9 --t1 1.95 2>&1 | grep rendered     # the same from behind
  $R $G video/D_$u $C --az 290 --elev 54 --ctr 0,0.06,1.45 --t0 0.4 --t1 4.0 2>&1 | grep rendered               # at the game camera's pitch
done
echo ALL DONE
