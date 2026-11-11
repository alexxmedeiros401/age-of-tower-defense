# Keep a clip's hand paths and hand orientations (so a two-handed prop stays in both hands) but move them by an
# offset, and let armsolve rebuild the arms (elbows, roll, twist) for the new hand places. For clips whose timing
# and grip are right but which sit in the wrong place (a stock against the face, hands inside a beard).
# In a cfg:  import follow as FW;  PRE = FW.pre(('R', 'L'))
#            AXIS = FW.AXIS; AXIS2 = FW.AXIS2          (the hand's own rest Y and Z: dir/up = the shipped hand frame)
#            CLIPS = {'Combat': {'L': FW.track('Combat', 'L', off), 'R': FW.track('Combat', 'R', off)}}
#            off: Vector or f -> Vector (chest-relative)
from mathutils import Vector, Matrix
_O = {}
AXIS = {}; AXIS2 = {}
def _axes(B):
    for s in ('R', 'L'):
        m = B['hand.' + s].matrix_local.to_3x3()
        AXIS[s] = m.col[1].normalized(); AXIS2[s] = m.col[2].normalized()
def pre(sides=('R', 'L')):
    def _pre(ctx, clip):
        P, B, sc = ctx['P'], ctx['B'], ctx['sc']
        _axes(B)
        cr = B['chest'].matrix_local
        d = {}
        for f in range(ctx['f0'], ctx['f1'] + 1):
            sc.frame_set(f)
            X = P['chest'].matrix @ cr.inverted(); Xi = X.inverted(); R3 = Xi.to_3x3()
            for s in sides:
                M = P['hand.' + s].matrix
                d[(s, f)] = (Xi @ M.translation, (R3 @ M.to_3x3().col[1]).normalized(), (R3 @ M.to_3x3().col[2]).normalized())
        _O[clip] = d
    return _pre
def track(clip, side, off=Vector(), extra=None):
    def k(f):
        p, y, z = _O[clip][(side, f)]
        o = off(f) if callable(off) else off
        opts = {'dir': y, 'up': z}
        if extra: opts.update(extra(f) if callable(extra) else extra)
        return p + o, opts
    return k
def orig(clip, side, f):
    return _O[clip][(side, f)]

# A prop on its own bone (not a child of the hand: halberd, linstock, musket) rides along with a hand: its shipped
# placement relative to the hand is kept frame by frame. In a cfg: PRE = FW.pre(...); POST = FW.attach_post
# with ATTACH = FW.attach('halberd', 'R') listed before (attach() registers the prop for the PRE capture).
_ATT = []
_AO = {}
def attach(prop, side):
    _ATT.append((prop, side))
def _pre_attach(ctx, clip):
    P, sc = ctx['P'], ctx['sc']
    d = {}
    for f in range(ctx['f0'], ctx['f1'] + 1):
        sc.frame_set(f)
        for prop, side in _ATT:
            d[(prop, f)] = P['hand.' + side].matrix.inverted() @ P[prop].matrix
    _AO[clip] = d
_pre_plain = pre
def pre(sides=('R', 'L')):
    p0 = _pre_plain(sides)
    def _pre(ctx, clip):
        p0(ctx, clip); _pre_attach(ctx, clip)
    return _pre
def attach_post(ctx, clip, f):
    import bpy
    P = ctx['P']
    for prop, side in _ATT:
        rel = _AO.get(clip, {}).get((prop, f))
        if rel is None: continue
        P[prop].matrix = P['hand.' + side].matrix @ rel
        bpy.context.view_layer.update()
        for ch in ('rotation_quaternion', 'location', 'scale'):
            P[prop].keyframe_insert(ch, frame=f)
