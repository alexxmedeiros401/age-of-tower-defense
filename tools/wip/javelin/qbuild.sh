#!/bin/bash
# quick (coarse) sculpt + a small bake of the Javelin Thrower (no base), for pose previews
cd /home/claude/age-of-tower-defense/tools/blender/hq
python3 sculpt_char.py --character javelin --out /home/claude/work/iron/javelin/q/jav_q.blend --shots /home/claude/work/iron/javelin/q/views > /home/claude/work/iron/javelin/q/sculpt.log 2>&1
python3 build_game.py -- --character javelin --char /home/claude/work/iron/javelin/q/jav_q.blend --base none --out /home/claude/work/iron/javelin/qb --tex 512 --ao 6 --stage char > /home/claude/work/iron/javelin/qb/build.log 2>&1
grep "\[game\]\|Traceback\|Error" /home/claude/work/iron/javelin/qb/build.log | tail -5
echo QBUILD_DONE
