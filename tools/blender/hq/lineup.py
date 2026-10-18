"""Group shot of finished HQ units (their *_hq.blend files), each posed on its own clip frame and scaled to its in-game
size, standing in a row.

    python3 lineup.py -- OUT.png RES_X RES_Y SPP  BLEND:ROOT:ACTION:FRAME:SCALE  [BLEND:ROOT:ACTION:FRAME:SCALE ...]
                      [--gap 2.0] [--az 0] [--el 16] [--dist 16] [--tz 0.9]
"""
import sys, os
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy
from mathutils import Vector
import look

ARGS = sys.argv[sys.argv.index("--") + 1:]
def opt(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
pos = [a for i, a in enumerate(ARGS) if not a.startswith("--") and (i == 0 or not ARGS[i - 1].startswith("--"))]
OUT, RX, RY, SPP = pos[0], int(pos[1]), int(pos[2]), int(pos[3])
UNITS = [u.split(":") for u in pos[4:]]
GAP = float(opt("--gap", "2.0"))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
BASE_FRAME = 200
n = len(UNITS)
for i, (path, root_name, act, fr, scale) in enumerate(UNITS):
    with bpy.data.libraries.load(path) as (src, dst):
        names = list(src.actions)
        dst.objects = list(src.objects)
        dst.actions = list(names)          # (a copy: Blender fills the assigned list with datablocks in place)
    acts = dict(zip(names, dst.actions))
    objs = [o for o in dst.objects if o is not None]
    for o in objs:
        sc.collection.objects.link(o)
    root = next(o for o in objs if o.name.startswith(root_name))
    root.location = Vector(((i - (n - 1) / 2) * GAP, 0.0, 0.0))
    root.scale = (float(scale),) * 3
    for o in objs:
        if o.type == "ARMATURE":
            ad = o.animation_data or o.animation_data_create()
            ad.action = None
            tr = ad.nla_tracks.new()
            st = tr.strips.new(act, BASE_FRAME - int(fr), acts[act])
            st.extrapolation = "HOLD"
sc.frame_set(BASE_FRAME)
look.setup(samples=SPP, res=(RX, RY), transparent=True)
look.camera((0.0, 0.0, float(opt("--tz", "0.9"))), float(opt("--dist", "16")), float(opt("--az", "0")), float(opt("--el", "16")),
            lens=float(opt("--lens", "50")))
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
look.backdrop(OUT, OUT.replace(".png", "_bg.png"))
print("LINEUP", OUT)
