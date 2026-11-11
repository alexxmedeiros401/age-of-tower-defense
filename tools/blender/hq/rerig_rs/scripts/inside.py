"""Which part of the sling arm / sling is inside the head or trunk volume, per Throw frame (same test as rs_check)."""
import sys, numpy as np
sys.path.insert(0, 'rig')
import rs_mesh, rs_core, rs_anim, rs_clips
from scipy.spatial import cKDTree
M = rs_mesh.Mesh('out/mesh.npz'); w = np.load('out/weights.npz', allow_pickle=True)
names = [str(n) for n in w['names']]; W = w['W']; V = M.V; ni = {n: i for i, n in enumerate(names)}
N = M.vertex_normals()
head_v = np.where(W[:, ni['head']] > 0.95)[0]
trunk_v = np.where((W[:, ni['chest']] + W[:, ni['spine']] + W[:, ni['root']]) > 0.9)[0]
kd = {'head': (cKDTree(V[head_v]), head_v, 'head'), 'trunk': (cKDTree(V[trunk_v]), trunk_v, 'chest')}
dom = W.argmax(1)
groups = {'hand.R': np.where(W[:, ni['hand.R']] > 0.6)[0], 'forearm.R': np.where(W[:, [ni['forearm.R'], ni['forearm_tw.R']]].sum(1) > 0.6)[0],
          'sling': np.where(M.vpart == 1)[0], 'stone': np.where(M.vpart == 2)[0],
          'hand.L': np.where(W[:, ni['hand.L']] > 0.6)[0], 'forearm.L': np.where(W[:, [ni['forearm.L'], ni['forearm_tw.L']]].sum(1) > 0.6)[0]}
clip = sys.argv[1] if len(sys.argv) > 1 else 'Throw'
poses = rs_anim.bake(rs_clips.CLIPS[clip]())
for f, (c, P, info) in enumerate(poses[:-1]):
    X = rs_core.skin(V, W, names, P); out = []
    for tag, (tree, src, bone) in kd.items():
        d = P[bone]
        for g, idx in groups.items():
            if g == 'stone' and c.get('stone', 1) < 0.5: continue
            pts = (X[idx] - d.t) @ d.R
            dist, k = tree.query(pts); vi = src[k]
            depth = -((pts - V[vi]) * N[vi]).sum(1)
            inside = (depth > 0.01) & (dist < 0.12)
            if inside.any(): out.append('%s in %s %.3f (%d verts)' % (g, tag, depth[inside].max(), inside.sum()))
    if out: print('f%02d  %s' % (f, ' | '.join(out)))
