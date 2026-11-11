# vid.sh ID COMBAT ATTACK  -> before_after.mp4 (ZOOM 1.25)
id=$1; C=$2; A=$3; D=/home/claude/work/repose/$id; F=/home/claude/work/repose/rhB_frames/$id
cd /home/claude/wt/rhB/tools/blender/hq/repose
export RX=360 RY=440 ZOOM=1.25
[ -d $F/old ] || python3 frames.py /home/claude/wt/rhB/assets/heroes/$id.glb $F/old "$C,$A,Ability,Cheer" 315,200 35 > /dev/null 2>&1
rm -rf $F/new; python3 frames.py $D/$id.glb $F/new "$C,$A,Ability,Cheer" 315,200 35 > /dev/null 2>&1
python3 video.py $F/old $F/new $D/before_after.mp4 "az315:$C,$A,$C,$A;az200:$C,$A,$C,$A;az315:Ability,Cheer;az200:Ability,Cheer"
