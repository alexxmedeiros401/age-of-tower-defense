"""Where faces flip and edges stretch over Whirl and Throw (prints a breakdown by bone, saves out/paint_flip.npy for paint.py).
Run from the folder root: python3 scripts/flipmap.py"""
import sys, numpy as np
sys.path.insert(0, 'rig')
import rs_mesh, rs_core, rs_anim, rs_clips
M = rs_mesh.Mesh('out/mesh.npz'); w = np.load('out/weights.npz', allow_pickle=True)
names = [str(n) for n in w['names']]; W = w['W']; ni = {n: i for i, n in enumerate(names)}
V, F, E = M.V, M.F, M.edges
dom = W.argmax(1); fn_rest = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
rest_len = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
col = np.zeros((len(V), 3)) + 0.6
tot_flip = np.zeros(len(F), int); tot_st = np.zeros(len(E), int)
for cname in ('Whirl', 'Throw'):
    poses = rs_anim.bake(rs_clips.CLIPS[cname]())
    for f, (c, P, info) in enumerate(poses[:-1]):
        X = rs_core.skin(V, W, names, P)
        fnp = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
        fb = dom[F[:, 0]]; carried = np.zeros_like(fn_rest)
        for b in np.unique(fb):
            m = fb == b; carried[m] = fn_rest[m] @ P[names[b]].R.T
        flip = ((fnp * carried).sum(1) < 0) & (fb != ni['stone']) & (np.linalg.norm(fn_rest, axis=1) > 2e-5)
        tot_flip += flip
        L = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)
        tot_st += (L > 2.0 * rest_len) & (L - rest_len > 0.03)
fv = np.unique(F[tot_flip > 0]); sv = np.unique(E[tot_st > 0])
col[sv] = (1.0, 0.85, 0.0); col[fv] = (1.0, 0.0, 0.0)
np.save('out/paint_flip.npy', col)
print('faces ever flipped', int((tot_flip > 0).sum()), 'edges ever stretched', int((tot_st > 0).sum()))
area = np.linalg.norm(fn_rest, axis=1) / 2
ff = np.where(tot_flip > 0)[0]
print('flipped faces: rest area median %.6f max %.6f; by bone:' % (np.median(area[ff]), area[ff].max()))
from collections import Counter
print(Counter(names[dom[F[i, 0]]] for i in ff).most_common(12))
c = V[F[ff]].mean(1); print('bbox', c.min(0).round(2), c.max(0).round(2))
# how far inside are the flips: are they tiny sliver faces?
el = np.array([[np.linalg.norm(V[F[i, a]] - V[F[i, b]]) for a, b in ((0, 1), (1, 2), (2, 0))] for i in ff])
print('flipped faces shortest edge median %.4f, longest median %.4f' % (np.median(el.min(1)), np.median(el.max(1))))
