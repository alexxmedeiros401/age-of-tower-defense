"""Where the Throw's whip comes nearest the base ring (least radius of the base at each height, any facing)."""
import sys, numpy as np
sys.path.insert(0, 'rig')
import rs_mesh, rs_core, rs_anim, rs_clips
M = rs_mesh.Mesh('out/mesh.npz'); w = np.load('out/weights.npz', allow_pickle=True)
names = [str(n) for n in w['names']]; W = w['W']; V = M.V
sh = np.load('out/shipped.npz', allow_pickle=True)
BV = sh['BV'] - np.array([0.0, 0.06, 0.9]); br = np.hypot(BV[:, 0], BV[:, 1])
zs = np.arange(0.05, 2.3, 0.05); prof = np.full(len(zs), np.inf)
for i, z in enumerate(zs):
    m = (np.abs(BV[:, 2] - z) < 0.06) & (br > 0.55)
    if m.any(): prof[i] = br[m].min()
if '-p' in sys.argv: print('ring profile', {round(float(z), 2): round(float(p), 3) for z, p in zip(zs, prof) if z > 1.0})
frames = [float(x) for x in sys.argv[1].split(',')] if len(sys.argv) > 1 and sys.argv[1][0] != '-' else [0, 0.5, 1, 1.5, 2, 2.5, 3, 4]
clip = rs_clips.CLIPS['Throw']()
poses = rs_anim.bake(clip)
part = {0: 'body', 1: 'sling', 2: 'stone'}
for f in range(0, 6):
    c, P, info = poses[f]
    X = rs_core.skin(V, W, names, P)
    r = np.hypot(X[:, 0], X[:, 1]); zi = np.clip(np.round((X[:, 2] - zs[0]) / 0.05).astype(int), 0, len(zs) - 1)
    cl = prof[zi] - r; cl[X[:, 2] < 0.2] = np.inf
    out = []
    for p in (0, 1, 2):
        m = M.vpart == p
        if p == 2 and c.get('stone', 1) < 0.5: out.append('stone gone'); continue
        i = np.where(m)[0][np.argmin(cl[m])]
        out.append('%s %.3f at r %.2f z %.2f az %.0f' % (part[p], cl[i], r[i], X[i, 2], np.degrees(np.arctan2(X[i, 0], -X[i, 1]))))
    print('f%d  grip %s pouch %s | %s' % (f, np.round(info['grip'], 2), np.round(info['pouch'], 2), ' | '.join(out)))
