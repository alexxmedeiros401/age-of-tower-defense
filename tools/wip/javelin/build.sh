#!/bin/bash
# the fine build of the Javelin Thrower (char and base sculpts one after the other: memory)
cd /home/claude/age-of-tower-defense/tools/blender/hq
H=/home/claude/work/iron/javelin/hi
python3 sculpt_char.py --character javelin --fine --out $H/jav_hi.blend --shots $H/shots_fine > $H/sculpt_char.log 2>&1
python3 sculpt_base.py --module javelin_base --fine --out $H/jav_base_hi.blend --shots $H/base_shots_fine > $H/sculpt_base.log 2>&1
python3 build_game.py -- --character javelin --char $H/jav_hi.blend --base $H/jav_base_hi.blend --out /home/claude/work/iron/javelin/final --tex 2048 --ao 40 > /home/claude/work/iron/javelin/final/build.log 2>&1
grep "\[game\]\|Traceback" /home/claude/work/iron/javelin/final/build.log | tail -6
echo BUILD_DONE
