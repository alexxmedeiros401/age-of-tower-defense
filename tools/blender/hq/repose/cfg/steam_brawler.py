# Steam Brawler: the punches rolled the upper arms up to ~50 deg about their own axis (Attack ~f4-14, the left
# sleeve smears/stretches at the shoulder) and kept ~15 deg of roll in the guard. The punch paths, fist orientations
# and timing are right, so the hands keep their shipped paths and orientations (no offset) and the arms are rebuilt
# for them with the least upper-arm roll; the steam rams (separate prop bones) are re-keyed every frame to keep
# their shipped placement relative to each fist (follow.py + armsolve).
from mathutils import Vector as V
import follow as FW
FW.attach('ram.L', 'L'); FW.attach('ram.R', 'R')
PRE = FW.pre(('R', 'L')); POST = FW.attach_post
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
CLIPS = {c: {'R': FW.track(c, 'R'), 'L': FW.track(c, 'L')} for c in ('Combat', 'Attack', 'Idle')}
