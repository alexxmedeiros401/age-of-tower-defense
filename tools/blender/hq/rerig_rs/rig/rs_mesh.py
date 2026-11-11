"""The Rock Slinger's low mesh (the bake's low.blend, dumped to low.npz) as numpy arrays, in armature space."""
import os, numpy as np
import rs_skel

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get('RS_WORK', os.path.join(HERE, '..', 'out'))


class Mesh:
    def __init__(self, path=None):
        d = np.load(path or os.path.join(WORK, 'mesh.npz'))
        self.V = d['V'] + rs_skel.SHIFT
        self.F = d['F']
        self.part = d['part']                 # per face: 0 body, 1 sling, 2 stone
        self.uv = d['uv']                     # (faces, 3, 2)
        n = len(self.V)
        vp = np.full(n, -1)
        for p in (0, 1, 2):
            vp[np.unique(self.F[self.part == p])] = p
        self.vpart = vp
        self._edges = None

    @property
    def edges(self):
        if self._edges is None:
            F = self.F
            E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
            self._edges = np.unique(np.sort(E, axis=1), axis=0)
        return self._edges

    def vertex_normals(self):
        V, F = self.V, self.F
        fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
        N = np.zeros_like(V)
        for k in range(3):
            np.add.at(N, F[:, k], fn)
        return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    def vertex_colors(self, albedo_path):
        from PIL import Image
        im = np.asarray(Image.open(albedo_path).convert('RGB'), dtype=np.float64) / 255.0
        H, W = im.shape[:2]
        uv = self.uv.reshape(-1, 2)
        x = np.clip(uv[:, 0] * W - 0.5, 0, W - 1); y = np.clip((1 - uv[:, 1]) * H - 0.5, 0, H - 1)
        c = im[np.round(y).astype(int), np.round(x).astype(int)]
        C = np.zeros((len(self.V), 3)); cnt = np.zeros(len(self.V))
        np.add.at(C, self.F.reshape(-1), c); np.add.at(cnt, self.F.reshape(-1), 1)
        return C / np.maximum(cnt, 1)[:, None]

    def laplacian(self, verts=None):
        """Cotangent Laplacian (positive semi-definite, L = D - W) and lumped vertex areas."""
        from scipy.sparse import coo_matrix, diags
        V, F = self.V, self.F
        n = len(V)
        I, Jx, Wt = [], [], []
        area = np.zeros(n)
        for a, b, c in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            u = V[F[:, a]] - V[F[:, c]]; v = V[F[:, b]] - V[F[:, c]]
            cr = np.linalg.norm(np.cross(u, v), axis=1)
            cot = (u * v).sum(1) / np.maximum(cr, 1e-12)
            cot = np.clip(cot, 0.02, 20.0) * 0.5
            I += [F[:, a], F[:, b]]; Jx += [F[:, b], F[:, a]]; Wt += [cot, cot]
            np.add.at(area, F[:, c], cr / 6.0)
        Wm = coo_matrix((np.concatenate(Wt), (np.concatenate(I), np.concatenate(Jx))), shape=(n, n)).tocsr()
        L = diags(np.asarray(Wm.sum(1)).ravel()) - Wm
        return L.tocsr(), np.maximum(area, 1e-10)
