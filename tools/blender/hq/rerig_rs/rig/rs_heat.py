"""Which bones a vertex can see through the inside of the mesh (the anchoring test of bone heat, Baran & Popovic).

rs_labels gives each vertex to the nearest bone it sees; the smooth blends come from rs_weights' surface blur.
"""
import numpy as np


def seg_closest(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0.0, 1.0)
    C = a + t[:, None] * ab
    return C, t, np.linalg.norm(P - C, axis=1)


def visibility(V, N, F, segs, verts, eps=2e-3):
    """vis[i, j]: vertex verts[i] sees its closest point on segment j without the ray leaving the mesh."""
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    bvh = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(int(i) for i in f) for f in F])
    P = V[verts]
    dist = np.zeros((len(verts), len(segs))); vis = np.zeros((len(verts), len(segs)), bool)
    for j, (a, b) in enumerate(segs):
        C, t, d = seg_closest(P, a, b)
        dist[:, j] = d
        for i in range(len(verts)):
            dirv = C[i] - P[i]; L = d[i]
            if L < 1e-6:
                vis[i, j] = True; continue
            dirv = dirv / L
            # the ray must start by going into the body
            if dirv @ N[verts[i]] > 0.15:
                continue
            hit = bvh.ray_cast(Vector(P[i] + dirv * eps), Vector(dirv), L - eps)
            vis[i, j] = hit[0] is None
    return dist, vis
