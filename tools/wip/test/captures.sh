#!/bin/bash
# the five units whose effects now start on their attack clips (_at_attack_frame)
C=/home/claude/work/bronze/clip/cap
cd /home/claude/work/attacks
bash shoot2.sh $C/club club_warrior --frames=24 --skip=2 | tail -2
bash shoot2.sh $C/tar tar_shaman --frames=24 --skip=2 | tail -2
bash shoot2.sh $C/mara hero --hero=mara --frames=24 --skip=2 | tail -2
MAP=river_delta bash shoot2.sh $C/spear spear_guard --frames=24 --skip=2 | tail -2
MAP=river_delta bash shoot2.sh $C/sun sun_priest --frames=24 --skip=2 | tail -2
grep -h -E "SCRIPT ERROR|ERROR: .*\.gd|Parse Error" $C/*/log.txt | head
echo CAPTURES_DONE
