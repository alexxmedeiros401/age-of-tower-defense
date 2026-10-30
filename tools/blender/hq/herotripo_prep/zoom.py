"""Close-ups of chosen bones in chosen clip frames (Blender): one sheet.

    python3 zoom.py -- --hero ugo --new OUT/ugo_hq.blend --out DIR --shots "hand.R:0.6,Idle,0,40,5,0.35;hand.L:0.5,rest,0,0,10,0.5"

Each shot: bone[:along],action|rest,frame,azimuth,elevation,ortho size. Writes DIR/zoom.png.
"""
import sys, os, math
sys.argv = [sys.argv[0]] + ["--"] + sys.argv[sys.argv.index("--") + 1:]
HQ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HQ); sys.path.insert(0, HQ + "/herotripo_prep")
import common as C
a = sys.argv
NEW, OUT = C.arg("--new"), C.arg("--out")
sys.argv = [a[0], "--", "--hero", C.arg("--hero"), "--new", NEW, "--out", OUT, "--only", "none", "--res", C.arg("--res", "320"), "--samples", "12"]
exec(open(HQ + "/herotripo_review.py").read())
sc, arm = setup(NEW)
ps, labels = [], []
for spec in a[a.index("--shots") + 1].split(";"):
    bone, act, fr, az, el, o = spec.split(",")
    pose(arm, None if act == "rest" else act, int(fr))
    c = bone_world(arm, bone.split(":")[0], float(bone.split(":")[1]) if ":" in bone else 0.5)
    camera(sc, c, float(az), float(el), float(o))
    ps.append(shot(sc, os.path.join(OUT, "_z%d.png" % len(ps))))
    labels.append("%s %s %s" % (bone, act, fr))
sheet(ps, os.path.join(OUT, C.arg("--name", "zoom") + ".png"), 5, labels)
