#!/bin/bash
# Rock Slinger re-rig: the whole build. bash build.sh [prep|weights|rig|export|check|install|all]   (see README.md)
# all = prep -> weights -> rig -> export -> check. install copies the result over assets/towers/rock_slinger.glb.
set -e
cd "$(dirname "$0")"
W=${RS_WORK:-out}; IN=${RS_IN:-src}; SHIP=${RS_SHIPPED:-src/rock_slinger_before.glb}
step=${1:-all}
mkdir -p $W
q() { grep -v "^$\|EGL Error\|INFO\|Read blend\|Saved as" || true; }
if [ "$step" = all ] || [ "$step" = prep ]; then
  python3 -I rig/rs_prep.py -- $IN/low.blend $W/mesh.npz 2>&1 | q
  # the base's vertices, for the clearance check
  [ -f $W/shipped.npz ] || python3 -I scripts/dump_glb.py -- $SHIP $W/shipped.npz 2>&1 | q
fi
if [ "$step" = all ] || [ "$step" = prep ] || [ "$step" = weights ]; then python3 -I rig/rs_make_weights.py -- $W/mesh.npz $IN/hero_albedo.png $W/weights.npz 2>&1 | q; fi
if [ "$step" = all ] || [ "$step" = prep ] || [ "$step" = weights ] || [ "$step" = rig ]; then python3 -I rig/rs_build.py -- $SHIP $W/mesh.npz $W/weights.npz $W/rs_rig.blend 2>&1 | q; fi
if [ "$step" = all ] || [ "$step" = export ]; then python3 -I rig/rs_export.py -- $W/rs_rig.blend $SHIP $W/rock_slinger.glb $W/rock_slinger_hq.blend 2>&1 | q; fi
if [ "$step" = all ] || [ "$step" = check ]; then python3 rig/rs_check.py $W/mesh.npz $W/weights.npz $W/shipped.npz; fi
if [ "$step" = install ]; then cp $W/rock_slinger.glb ../../../../assets/towers/rock_slinger.glb; echo "installed assets/towers/rock_slinger.glb"; fi
