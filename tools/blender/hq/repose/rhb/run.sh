# run.sh ID  : author + triage of the new GLB (summary)
id=$1; D=/home/claude/work/repose/$id; mkdir -p $D
cd /home/claude/wt/rhB/tools/blender/hq/repose
python3 hero_arm.py /home/claude/wt/rhB/assets/heroes/$id.glb $D/$id.glb cfg/${id}_arms.py $D/author_numbers.json > $D/author.log 2>&1 || { tail -20 $D/author.log; exit 1; }
grep -E "Error|Traceback" $D/author.log
python3 triage.py $D/$id.glb $D/triage_new.json all 1 > $D/triage_new.log 2>&1
python3 /home/claude/work/repose/rhB_tools/summ.py $D/triage_new.json /home/claude/work/repose/rhB_triage/$id.json
