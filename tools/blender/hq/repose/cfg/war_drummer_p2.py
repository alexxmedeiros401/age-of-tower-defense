# War Drummer (remake5 body, pass 2). The Tripo sticks are long (0.33 m): with the shipped motion they stood up in front
# of his beard and face: in the Combat ready pose (sticks vertical in front of the chest, tips at the chin) and in the
# Attack salute (f12-30: both fists at the chin, the sticks crossed in a V in front of the face, tips at hat height).
# Re-authored: the Attack salute is carried out to the sides (fists 14 cm further out, 8 cm back, 5 cm lower), the sticks
# tilted outward so their tips stand beside the hat brim, not in front of the face; the Combat ready pose tips the
# sticks forward (about 45 deg) so their tips sit in front of the chest. Hand paths, timing and the drum beats (the
# Attack's f1-4 and f7-11 strokes) are the shipped ones.
from mathutils import Vector as V, Quaternion as Q
import follow as FW
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
_S = {}
_p0 = FW.pre(('R', 'L'))
def PRE(ctx, clip):
    _p0(ctx, clip)
    P, B, sc = ctx['P'], ctx['B'], ctx['sc']
    cr = B['chest'].matrix_local
    for f in range(ctx['f0'], ctx['f1'] + 1):
        sc.frame_set(f)
        R3 = (P['chest'].matrix @ cr.inverted()).inverted().to_3x3()
        for s in ('R', 'L'):
            _S[(clip, s, f)] = (R3 @ P['stick.' + s].matrix.to_3x3().col[1]).normalized()
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def _turn(clip, side, f, target, w):
    d = _S[(clip, side, f)]
    q = d.rotation_difference(target.normalized())
    return Q().slerp(q, w)
def mk(clip, side, w_of, off_of, target_of):
    def k(f):
        p, y, z = FW.orig(clip, side, f)
        w = w_of(f)
        q = _turn(clip, side, f, target_of(f), w)
        return p + off_of(f) * w, {'dir': q @ y, 'up': q @ z}
    return k
sg = {'R': -1.0, 'L': 1.0}
# Attack: the salute (f12-30), eased in over f11-14 and out over f27-31
def w_att(f): return _ss(10.5, 13.5, f) * (1 - _ss(27, 31, f))
def off_att(s): return lambda f: V((0.14 * sg[s], 0.08, -0.05))
def tgt_att(s): return lambda f: V((0.45 * sg[s], 0.05, 0.89))
# Combat: the whole clip (a loop): sticks tipped forward
def w_cmb(f): return 1.0
def tgt_cmb(s): return lambda f: V((0.12 * sg[s], -0.72, 0.68))
CLIPS = {
    'Attack': {s: mk('Attack', s, w_att, off_att(s), tgt_att(s)) for s in ('R', 'L')},
    'Combat': {s: mk('Combat', s, w_cmb, lambda f: V(), tgt_cmb(s)) for s in ('R', 'L')},
}
WINDOW = {'Attack': {'R': (10, 32, 1), 'L': (10, 32, 1)}}
