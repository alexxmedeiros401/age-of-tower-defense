# Bow helpers for armsolve configs (PRE/POST hooks): after the arms are re-authored, the bow string (string_top/bot,
# children of the bow hand) is re-aimed so its tail sits on the arrow's nock wherever the shipped clip had it drawn,
# and the arrow (child of the draw hand) is re-aimed at its rest on the bow wherever the shipped clip had it nocked.
# Use in a cfg:  import bowstring as BS; PRE = BS.pre('L', 'R'); POST = BS.post
import math
from mathutils import Vector, Matrix
_O = {}
def pre(bow_side, draw_side, strings=('string_top', 'string_bot'), arrow='arrow', attach=0.05, nock_deg=20):
    def _pre(ctx, clip):
        P, sc = ctx['P'], ctx['sc']
        hb = 'hand.' + bow_side
        d = {'bow': hb, 'strings': [s for s in strings if s in P], 'arrow': arrow if arrow in P else None, 'fr': {}}
        for f in range(ctx['f0'], ctx['f1'] + 1):
            sc.frame_set(f)
            r = {}
            Mb = P[hb].matrix.copy()
            if d['arrow']:
                a = P[d['arrow']]; nock = a.head.copy(); adir = (a.tail - a.head).normalized()
                vis = a.scale.y > 0.5
                # where the arrow line passes the bow hand (in the bow hand's frame): the arrow rest
                g = P[hb].head; t = (g - nock).dot(adir); rest = nock + adir * t
                ang = math.degrees(adir.angle((rest - nock))) if t > 0 else 180
                r['nocked'] = vis and t > 0.05 and (g - rest).length < 0.25
                r['rest_local'] = Mb.inverted() @ rest
            else:
                nock = None
            for s in d['strings']:
                tail = P[s].tail.copy()
                r[s] = nock is not None and (tail - nock).length < attach and P[s].scale.y > 1.001
            d['fr'][f] = r
        # one arrow rest (bow-hand frame) for the clip: the mean over the nocked frames
        rl = [r['rest_local'] for r in d['fr'].values() if r.get('nocked')]
        d['rest'] = sum(rl, Vector()) / len(rl) if rl else None
        _O[clip] = d
    return _pre

def _aim(pb, target, keep_len=True, rest_len=None):
    M = pb.matrix.copy(); h = M.translation.copy()
    loc, rot, scl = M.decompose()
    y = (rot.to_matrix() @ Vector((0, 1, 0))).normalized()
    want = (target - h)
    q = y.rotation_difference(want.normalized())
    R = (q @ rot).to_matrix().to_4x4()
    sy = 1.0 if keep_len else want.length / rest_len
    pb.matrix = Matrix.Translation(h) @ R @ Matrix.Diagonal((scl.x, sy, scl.z, 1.0))

def post(ctx, clip, f):
    import bpy
    d = _O.get(clip)
    if not d: return
    P, B = ctx['P'], ctx['B']; r = d['fr'][f]
    if d['arrow'] and r.get('nocked') and d['rest'] is not None:
        a = P[d['arrow']]
        target = P[d['bow']].matrix @ d['rest']
        _aim(a, target)
        bpy.context.view_layer.update()
        a.keyframe_insert('rotation_quaternion', frame=f)
    if d['arrow']:
        nock = P[d['arrow']].head.copy()
        for s in d['strings']:
            if r.get(s):
                _aim(P[s], nock, keep_len=False, rest_len=B[s].length)
                bpy.context.view_layer.update()
                P[s].keyframe_insert('rotation_quaternion', frame=f); P[s].keyframe_insert('scale', frame=f)
