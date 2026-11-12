#!/bin/bash
# Pass 2 heroes: deliverables for one built unit in OUTDIR (= /home/claude/work/pass2/ID): before_after.mp4 (shipped left,
# new right: COMBAT, ATTACK twice at az 315 then 200, Ability + Cheer at 315 and 200), check_glb.txt, triage_new.json
# + clearance summary vs the shipped triage, stretch.json/log.
#   bash p2h_finish.sh ID COMBAT ATTACK [SHIPPED_TRIAGE.json]
set -e
id=$1; C=$2; A=$3; OT=${4:-/home/claude/work/repose/$id/triage_new.json}
H=$(cd "$(dirname "$0")" && pwd); REPO=$(cd $H/../../../.. && pwd)
D=/home/claude/work/pass2/$id; F=/home/claude/work/pass2/_frames/$id
SHIP=$REPO/assets/heroes/$id.glb
cd $H
export RX=360 RY=440 ZOOM=1.25
rm -rf $F; mkdir -p $F
python3 frames.py $SHIP $F/old "$C,$A,Ability,Cheer" 315,200 35 > /dev/null 2>&1
python3 frames.py $D/$id.glb $F/new "$C,$A,Ability,Cheer" 315,200 35 > /dev/null 2>&1
python3 video.py $F/old $F/new $D/before_after.mp4 "az315:$C,$A,$C,$A;az200:$C,$A,$C,$A;az315:Ability,Cheer;az200:Ability,Cheer" > $D/vid.log 2>&1
rm -rf $F
cd $H/../herotripo_prep && python3 check_glb.py -- $D/$id.glb $SHIP 2>&1 | grep -v INFO > $D/check_glb.txt || true
cd $H; python3 triage_heroes.py $D/$id.glb $D/triage_new.json all 1 > $D/triage_new.log 2>&1
python3 rhb/summ.py $D/triage_new.json $OT > $D/clearance.txt
cd $H/../herotripo_prep && python3 stretch_check.py -- --hero $id --model $D/$id.glb --json $D/stretch.json > $D/stretch.log 2>&1 || true
S0=/home/claude/work/pass2/_audit/$id.stretch.json; [ -f $S0 ] || python3 stretch_check.py -- --hero $id --model $SHIP --json $S0 > /dev/null 2>&1 || true
cd $H; python3 p2h_stretchsum.py $S0 $D/stretch.json > $D/stretch_table.md
echo "$id: video $(du -h $D/before_after.mp4 | cut -f1); check_glb: $(grep -cE 'DIFF|MISSING|EXTRA' $D/check_glb.txt) diff lines"
