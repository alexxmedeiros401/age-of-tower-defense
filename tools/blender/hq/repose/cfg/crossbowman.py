# Crossbowman: the crossbow was aimed from the cheek with the right forearm across the face and the hands up under
# the kettle-hat brim (head penetration ~12 cm in Combat and through the Attack reload). The grip, timing and
# reload are right, so both hands keep their shipped paths and orientations (the crossbow stays in both hands) but
# the whole aim/reload is carried 18 cm lower and 6 cm further forward (aimed from the chest, the forearm below the
# face and beard), and the arms are rebuilt for those hand places (follow.py + armsolve). The right (trigger) hand
# holds nothing rigid, so its shipped wrist (bent up to ~150 deg) is only a hint (aim 0.3).
from mathutils import Vector as V
import follow as FW
PRE = FW.pre(('R', 'L'))
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
OFF = V((-0.05, -0.09, -0.21))   # pass 2 (p2H): was (0, -0.06, -0.18); 5 cm out at his right, 3 cm forward, 3 cm lower
CLIPS = {c: {'L': FW.track(c, 'L', OFF), 'R': FW.track(c, 'R', OFF, {'aim': 0.3})} for c in ('Combat', 'Attack')}

# Pass 2 (p2H): at a few reload frames the trigger forearm still reached the kettle-hat brim / beard (Attack 4: 12 cm into
# the head volume) and the right hand pressed into the gambeson while the stock was tucked (Combat: 14 cm). The aim/reload
# is now carried 5 cm further out at his right, 3 cm more forward and 3 cm lower (Attack head 2 cm, Combat torso 1 cm).
