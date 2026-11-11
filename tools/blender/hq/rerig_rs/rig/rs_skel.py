"""Rock Slinger re-rig: the skeleton, fitted to the Tripo body in its sculpted pose (bind pose = sculpt pose).

Armature space = the bake's low-mesh space moved by SHIFT (soles on the rock top, where the shipped model stands).
He faces -Y; his right hand (the sling hand) is at -X.
"""
import numpy as np

SHIFT = np.array([0.0, 0.0, -0.049])

# joints measured on the low mesh (LOW space), see the notes in README.md
_J_LOW = {
    'pelvis':     (0.000, 0.045, 0.760),
    'spine':      (0.000, 0.040, 0.905),
    'chest':      (0.000, 0.045, 1.125),
    'neck':       (0.000, 0.055, 1.455),
    'head':       (0.000, 0.035, 1.575),
    'head_top':   (0.000, 0.035, 2.000),
    'clav.L':     (0.050, -0.100, 1.415),
    'shoulder.L': (0.490, 0.110, 1.390),
    'elbow.L':    (0.545, 0.090, 1.135),
    'wrist.L':    (0.722, 0.010, 0.872),
    'hand_end.L': (0.770, -0.040, 0.705),
    'clav.R':     (-0.050, -0.100, 1.415),
    'shoulder.R': (-0.490, 0.110, 1.390),
    'elbow.R':    (-0.538, 0.088, 1.130),
    'wrist.R':    (-0.700, 0.000, 0.868),
    'hand_end.R': (-0.728, -0.050, 0.750),      # the bottom of the fist, where the sling's cords leave it
    'hip.L':      (0.165, 0.050, 0.745),
    'knee.L':     (0.200, 0.040, 0.500),
    'ankle.L':    (0.220, 0.085, 0.170),
    'ball.L':     (0.245, -0.120, 0.075),
    'toe_end.L':  (0.250, -0.255, 0.065),
    'hip.R':      (-0.165, 0.050, 0.745),
    'knee.R':     (-0.197, 0.040, 0.500),
    'ankle.R':    (-0.214, 0.085, 0.170),
    'ball.R':     (-0.240, -0.120, 0.075),
    'toe_end.R':  (-0.246, -0.255, 0.065),
    'pouch':      (-0.688, -0.135, 0.400),      # the stone's middle
    'pouch_end':  (-0.676, -0.160, 0.300),
}
J = {k: np.array(v, float) + SHIFT for k, v in _J_LOW.items()}

SLING_SEGS = 4


def sling_nodes():
    a, b = J['hand_end.R'], J['pouch']
    return [a + (b - a) * i / SLING_SEGS for i in range(SLING_SEGS + 1)]


def bones():
    """[(name, parent, head, tail, kind)] parent first. kind: 'main' | 'helper' | 'sling' | 'prop' | 'jiggle'."""
    B = []
    def add(name, parent, head, tail, kind='main'):
        B.append((name, parent, np.array(head, float), np.array(tail, float), kind))
    add('root', None, J['pelvis'], J['spine'])
    add('spine', 'root', J['spine'], J['chest'])
    add('chest', 'spine', J['chest'], J['neck'])
    add('neck', 'chest', J['neck'], J['head'])
    add('head', 'neck', J['head'], J['head_top'])
    for s in 'LR':
        sh, el, wr, he = J['shoulder.' + s], J['elbow.' + s], J['wrist.' + s], J['hand_end.' + s]
        add('clavicle.' + s, 'chest', J['clav.' + s], sh)
        add('shoulder_half.' + s, 'clavicle.' + s, sh, sh + (el - sh) * 0.45, 'helper')   # half the arm's swing
        add('upperarm_sw.' + s, 'clavicle.' + s, sh, sh + (el - sh) * 0.5, 'helper')       # the swing, none of the twist
        add('upperarm_tw.' + s, 'upperarm_sw.' + s, sh + (el - sh) * 0.5, el, 'helper')    # the swing, half the twist
        add('upperarm.' + s, 'clavicle.' + s, sh, el)
        add('elbow_half.' + s, 'upperarm.' + s, el, el + (wr - el) * 0.4, 'helper')        # half the elbow's bend
        add('forearm.' + s, 'upperarm.' + s, el, wr)
        add('forearm_tw.' + s, 'forearm.' + s, el + (wr - el) * 0.55, wr, 'helper')        # half the hand's twist
        add('hand.' + s, 'forearm.' + s, wr, he)
    for s in 'LR':
        hp, kn, an, ba, te = (J[k + s] for k in ('hip.', 'knee.', 'ankle.', 'ball.', 'toe_end.'))
        add('thigh.' + s, 'root', hp, kn)
        add('knee_half.' + s, 'thigh.' + s, kn, kn + (an - kn) * 0.4, 'helper')
        add('shin.' + s, 'thigh.' + s, kn, an)
        add('foot.' + s, 'shin.' + s, an, ba)
        add('toe.' + s, 'foot.' + s, ba, te)
    n = sling_nodes()
    for i in range(SLING_SEGS):
        add('sling' if i == 0 else 'sling.%03d' % i, 'hand.R' if i == 0 else ('sling' if i == 1 else 'sling.%03d' % (i - 1)), n[i], n[i + 1], 'sling')
    add('stone', 'sling.%03d' % (SLING_SEGS - 1), J['pouch'], J['pouch_end'], 'prop')
    return B


def bone_names():
    return [b[0] for b in bones()]


if __name__ == '__main__':
    for b in bones():
        print('%-18s parent=%-16s head=%s len=%.3f %s' % (b[0], b[1], np.round(b[2], 3), np.linalg.norm(b[3] - b[2]), b[4]))
    print(len(bones()), 'bones')
