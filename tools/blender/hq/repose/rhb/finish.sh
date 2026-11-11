# finish.sh ID COMBAT ATTACK CLIPSPEC : video + check_glb + notes
id=$1; D=/home/claude/work/repose/$id
/home/claude/work/repose/rhB_tools/vid.sh $id $2 $3 > $D/vid.log 2>&1
cd /home/claude/wt/rhB/tools/blender/hq/herotripo_prep && python3 check_glb.py -- $D/$id.glb /home/claude/wt/rhB/assets/heroes/$id.glb 2>&1 | grep -v INFO > $D/check_glb.txt
python3 /home/claude/work/repose/rhB_tools/gen_notes.py $id "$4" /home/claude/work/repose/rhB_notes/$id.md
rm -f $D/$id.glb.numbers.json
echo "$id done: $(grep -c DIFF $D/check_glb.txt) diff lines; $(tail -1 $D/vid.log)"
