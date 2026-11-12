#!/bin/bash
# Pass 2 leftovers (towers): before_after.mp4 (shipped left, new right: CLIPS twice at az 315 then 200) and check_glb.txt
#   bash p2h_finish_tower.sh ID "Combat,Attack" [SHIPPED.glb]
set -e
id=$1; CL=$2; H=$(cd "$(dirname "$0")" && pwd); REPO=$(cd $H/../../../.. && pwd)
D=/home/claude/work/pass2/$id; F=/home/claude/work/pass2/_frames/$id; SHIP=${3:-$REPO/assets/towers/$id.glb}
cd $H; export RX=360 RY=440 ZOOM=${ZOOM:-1.0}
rm -rf $F; mkdir -p $F
python3 frames.py $SHIP $F/old "$CL" 315,200 35 > /dev/null 2>&1
python3 frames.py $D/$id.glb $F/new "$CL" 315,200 35 > /dev/null 2>&1
python3 video.py $F/old $F/new $D/before_after.mp4 "az315:$CL,$CL;az200:$CL,$CL" > $D/vid.log 2>&1
rm -rf $F
cd $H/../herotripo_prep && python3 check_glb.py -- $D/$id.glb $SHIP 2>&1 | grep -v INFO > $D/check_glb.txt || true
echo "$id: $(tail -1 $D/vid.log); $(tail -1 $D/check_glb.txt)"
