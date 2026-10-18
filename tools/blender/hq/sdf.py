"""Signed-distance-field sculpting for the HQ models.

Shapes are distance fields combined with smooth unions/subtractions (soft, sculpted joins), evaluated on a
voxel grid in chunks and turned into a mesh with marching cubes. Every primitive has a bounding box, so each
one is only evaluated where it can change the surface. Units are Blender metres, Z up.
"""
import math
import numpy as np

F = np.float32


# ----------------------------------------------------------------------------------------- vector helpers
def v3(x):
    return np.asarray(x, dtype=np.float64).reshape(3)


def norm(x):
    x = v3(x)
    return x / max(1e-12, np.linalg.norm(x))


def rot_from_axes(x_axis=None, y_axis=None, z_axis=None):
    """Orthonormal rotation (columns = local axes in world space) from one or two given axes."""
    if z_axis is not None:
        z = norm(z_axis)
        ref = v3(y_axis) if y_axis is not None else (v3((0, 1, 0)) if abs(z[1]) < 0.9 else v3((1, 0, 0)))
        x = norm(np.cross(ref, z))
        y = np.cross(z, x)
    elif y_axis is not None:
        y = norm(y_axis)
        ref = v3(x_axis) if x_axis is not None else (v3((0, 0, 1)) if abs(y[2]) < 0.9 else v3((1, 0, 0)))
        z = norm(np.cross(ref, y))
        x = np.cross(y, z)
    else:
        x = norm(x_axis)
        ref = v3((0, 0, 1)) if abs(x[2]) < 0.9 else v3((0, 1, 0))
        y = norm(np.cross(ref, x))
        z = np.cross(x, y)
    return np.stack([x, y, z], axis=1)


def euler(rx=0.0, ry=0.0, rz=0.0):
    """XYZ euler (radians) -> rotation matrix, Blender convention."""
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def axis_angle(axis, ang):
    a = norm(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


# ----------------------------------------------------------------------------------------- noise
class Noise:
    """Vectorised 3D gradient (Perlin) noise + fBm."""

    def __init__(self, seed=0):
        rs = np.random.RandomState(seed)
        p = rs.permutation(256)
        self.perm = np.concatenate([p, p]).astype(np.int32)
        g = rs.normal(size=(256, 3))
        self.grad = (g / np.linalg.norm(g, axis=1, keepdims=True)).astype(F)

    def __call__(self, P):
        P = np.asarray(P, dtype=F)
        pi = np.floor(P).astype(np.int32)
        pf = (P - pi).astype(F)
        pi &= 255
        u = pf * pf * pf * (pf * (pf * 6 - 15) + 10)
        perm, grad = self.perm, self.grad
        out = 0.0
        res = None
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    h = perm[perm[perm[pi[:, 0] + dx] + pi[:, 1] + dy] + pi[:, 2] + dz]
                    g = grad[h]
                    d = pf - np.array([dx, dy, dz], dtype=F)
                    dot = (g * d).sum(1)
                    w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) * (u[:, 2] if dz else 1 - u[:, 2])
                    res = dot * w if res is None else res + dot * w
        return res

    def fbm(self, P, octaves=4, lac=2.03, gain=0.5):
        P = np.asarray(P, dtype=F)
        amp, tot, s = 1.0, None, 1.0
        for o in range(octaves):
            n = self(P * s + o * 17.31) * amp
            tot = n if tot is None else tot + n
            amp *= gain
            s *= lac
        return tot


NOISE = Noise(7)


# ----------------------------------------------------------------------------------------- primitives
class Prim:
    """A primitive: world point -> distance. `R` columns are local axes, `c` the local origin.
    `lo`/`hi` bound the shape in world space (used to skip points that cannot be affected)."""
    pad = 0.0

    def __init__(self, c=(0, 0, 0), R=None, disp=None, disp_amp=0.0):
        self.c = v3(c)
        self.R = np.eye(3) if R is None else np.asarray(R, dtype=np.float64)
        self.disp = disp
        self.disp_amp = disp_amp

    def local(self, P):
        return ((P - self.c.astype(F)) @ self.R.astype(F)).astype(F)

    def bounds_from_local(self, lo, hi):
        lo, hi = v3(lo), v3(hi)
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        w = corners @ self.R.T + self.c
        a = self.disp_amp
        self.lo, self.hi = w.min(0) - a, w.max(0) + a

    def __call__(self, P):
        d = self.sdf(P)
        if self.disp is not None:
            d = d + self.disp(P)
        return d


class Sphere(Prim):
    def __init__(self, c, r, **kw):
        super().__init__(c, **kw)
        self.r = r
        self.bounds_from_local((-r,) * 3, (r,) * 3)

    def sdf(self, P):
        q = P - self.c.astype(F)
        return np.sqrt((q * q).sum(1)) - F(self.r)


class Ellipsoid(Prim):
    def __init__(self, c, radii, R=None, **kw):
        super().__init__(c, R, **kw)
        self.rad = v3(radii)
        self.bounds_from_local(-self.rad, self.rad)

    def sdf(self, P):
        q = self.local(P)
        r = self.rad.astype(F)
        k0 = np.sqrt(((q / r) ** 2).sum(1))
        k1 = np.sqrt(((q / (r * r)) ** 2).sum(1))
        return k0 * (k0 - 1.0) / np.maximum(k1, F(1e-9))


class RoundCone(Prim):
    """Capsule from a (radius ra) to b (radius rb); exact distance (Inigo Quilez)."""

    def __init__(self, a, b, ra, rb=None, **kw):
        super().__init__((0, 0, 0), **kw)
        self.a, self.b = v3(a), v3(b)
        self.ra = ra
        self.rb = ra if rb is None else rb
        r = max(self.ra, self.rb)
        self.lo = np.minimum(self.a, self.b) - r - self.disp_amp
        self.hi = np.maximum(self.a, self.b) + r + self.disp_amp

    def sdf(self, P):
        a, b = self.a.astype(F), self.b.astype(F)
        ba = b - a
        l2 = F(ba @ ba)
        r1, r2 = F(self.ra), F(self.rb)
        if l2 < 1e-12:
            q = P - a
            return np.sqrt((q * q).sum(1)) - r1
        rr = r1 - r2
        a2 = l2 - rr * rr
        il2 = F(1.0) / l2
        pa = P - a
        y = pa @ ba
        z = y - l2
        xv = pa * l2 - np.outer(y, ba)
        x2 = (xv * xv).sum(1)
        y2 = y * y * l2
        z2 = z * z * l2
        k = np.sign(rr) * rr * rr * x2
        d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
        d1 = np.sqrt(x2 + z2) * il2 - r2
        d2 = np.sqrt(x2 + y2) * il2 - r1
        return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3)).astype(F)


class RoundBox(Prim):
    def __init__(self, c, half, r=0.0, R=None, **kw):
        super().__init__(c, R, **kw)
        self.half = v3(half)
        self.r = r
        self.bounds_from_local(-self.half, self.half)

    def sdf(self, P):
        q = np.abs(self.local(P)) - (self.half - self.r).astype(F)
        outside = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        inside = np.minimum(q.max(1), 0)
        return outside + inside - F(self.r)


class Torus(Prim):
    """Ring in the local XY plane (local Z = axis)."""

    def __init__(self, c, R_major, r_minor, R=None, **kw):
        super().__init__(c, R, **kw)
        self.Rm, self.rm = R_major, r_minor
        e = R_major + r_minor
        self.bounds_from_local((-e, -e, -r_minor), (e, e, r_minor))

    def sdf(self, P):
        q = self.local(P)
        xy = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - F(self.Rm)
        return np.sqrt(xy * xy + q[:, 2] ** 2) - F(self.rm)


class Cylinder(Prim):
    """Capped cylinder along local Z, with rounded edges (radius `rr`)."""

    def __init__(self, c, r, h, rr=0.0, R=None, **kw):
        super().__init__(c, R, **kw)
        self.r, self.h, self.rr = r, h, rr
        self.bounds_from_local((-r, -r, -h / 2), (r, r, h / 2))

    def sdf(self, P):
        q = self.local(P)
        dx = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - F(self.r - self.rr)
        dz = np.abs(q[:, 2]) - F(self.h / 2 - self.rr)
        return np.minimum(np.maximum(dx, dz), 0) + np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dz, 0) ** 2) - F(self.rr)


class Plane(Prim):
    """Half-space: negative on the side opposite to the normal."""

    def __init__(self, c, n, **kw):
        super().__init__(c, **kw)
        self.n = norm(n)
        self.lo = np.full(3, -1e9)
        self.hi = np.full(3, 1e9)

    def sdf(self, P):
        return (P - self.c.astype(F)) @ self.n.astype(F)


class Func(Prim):
    """Any callable P->d with explicit bounds."""

    def __init__(self, fn, lo, hi, **kw):
        super().__init__((0, 0, 0), **kw)
        self.fn = fn
        self.lo, self.hi = v3(lo) - self.disp_amp, v3(hi) + self.disp_amp

    def sdf(self, P):
        return self.fn(P).astype(F)


class Chain(Prim):
    """Smooth union of round cones through a polyline of (point, radius) — limbs, hair clumps, cords."""

    def __init__(self, pts, radii, k=0.0, **kw):
        super().__init__((0, 0, 0), **kw)
        self.segs = [RoundCone(pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)]
        self.k = k
        self.lo = np.min([s.lo for s in self.segs], 0) - self.disp_amp - k
        self.hi = np.max([s.hi for s in self.segs], 0) + self.disp_amp + k

    def sdf(self, P):
        d = None
        for s in self.segs:
            b = s.sdf(P)
            d = b if d is None else smin(d, b, self.k)
        return d


# ----------------------------------------------------------------------------------------- smooth ops
def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


# ----------------------------------------------------------------------------------------- field
class Field:
    """Ordered list of operations. Labels mark which primitive owns the surface (for painting/masks)."""

    def __init__(self, name="field"):
        self.name = name
        self.ops = []

    def add(self, prim, k=0.0, label=0):
        self.ops.append(("add", prim, k, label))
        return prim

    def sub(self, prim, k=0.0):
        self.ops.append(("sub", prim, k, 0))
        return prim

    def inter(self, prim, k=0.0):
        self.ops.append(("inter", prim, k, 0))
        return prim

    def paint(self, prim, label):
        """Label-only op: points inside `prim` (d<0) get `label` (no shape change)."""
        self.ops.append(("paint", prim, 0.0, label))
        return prim

    def bounds(self):
        los = [p.lo for kind, p, k, l in self.ops if kind == "add"]
        his = [p.hi for kind, p, k, l in self.ops if kind == "add"]
        return np.min(los, 0), np.max(his, 0)

    def eval(self, P, labels=False, margin=0.0):
        """Distance at P. Primitives are skipped for points outside their bounds (+ smoothing radius + `margin`),
        so values farther than that from every shape read as 1.0; shells of a field pass their offset as `margin`."""
        P = np.asarray(P, dtype=F)
        n = len(P)
        d = np.full(n, F(1.0))
        lab = np.zeros(n, np.int16)
        plo, phi = P.min(0), P.max(0)
        for kind, prim, k, label in self.ops:
            m = k + 1e-4 + margin
            if kind != "inter":
                if np.any(prim.hi + m < plo) or np.any(prim.lo - m > phi):
                    continue
                sel = np.all((P >= (prim.lo - m).astype(F)) & (P <= (prim.hi + m).astype(F)), axis=1)
                idx = np.nonzero(sel)[0]
                if len(idx) == 0:
                    continue
                Q = P[idx]
                b = prim(Q)
                a = d[idx]
                if kind == "add":
                    d[idx] = smin(a, b, k)
                    if labels:
                        lab[idx] = np.where(b < a, label, lab[idx])
                elif kind == "sub":
                    d[idx] = smax(a, -b, k)
                elif kind == "paint":
                    if labels:
                        lab[idx] = np.where(b < 0, label, lab[idx])
            else:
                b = prim(P)
                d = smax(d, b, k)
        return (d, lab) if labels else d

    def paint_dist(self, P, band=0.004):
        """Signed distance to every painted label's region, {label: d}, following the same op order as eval():
        a paint op makes the region grow by its shape (smooth edge); a later add op that takes over a point flips it
        hard in or out (those edges are geometric creases anyway). Stored per vertex as a clamped ramp, painted edges
        can be drawn crisply between vertices."""
        P = np.asarray(P, dtype=F)
        n = len(P)
        painted = sorted({label for kind, prim, k, label in self.ops if kind == "paint"})
        out = {L: np.full(n, F(1.0)) for L in painted}
        d = np.full(n, F(1.0))
        plo, phi = P.min(0), P.max(0)
        for kind, prim, k, label in self.ops:
            m = k + 1e-4
            if kind == "inter":
                d = smax(d, prim(P), k)
                continue
            if np.any(prim.hi + m < plo) or np.any(prim.lo - m > phi):
                continue
            sel = np.all((P >= (prim.lo - m).astype(F)) & (P <= (prim.hi + m).astype(F)), axis=1)
            idx = np.nonzero(sel)[0]
            if len(idx) == 0:
                continue
            b = prim(P[idx])
            a = d[idx]
            if kind == "add":
                win = idx[b < a]
                for L in painted:
                    if L == label:
                        out[L][win] = np.minimum(out[L][win], F(-band))
                    else:
                        out[L][win] = np.maximum(out[L][win], F(band))
                d[idx] = smin(a, b, k)
            elif kind == "sub":
                d[idx] = smax(a, -b, k)
            elif kind == "paint" and label in out:
                out[label][idx] = np.minimum(out[label][idx], b)
        return out

    # --------------------------------------------------------------------- meshing
    def mesh(self, voxel, lo=None, hi=None, chunk=24, verbose=True):
        import time
        from skimage import measure
        t0 = time.time()
        blo, bhi = self.bounds()
        lo = blo - 2 * voxel if lo is None else v3(lo)
        hi = bhi + 2 * voxel if hi is None else v3(hi)
        dims = np.ceil((hi - lo) / voxel).astype(int) + 1
        xs = (lo[0] + np.arange(dims[0]) * voxel).astype(F)
        ys = (lo[1] + np.arange(dims[1]) * voxel).astype(F)
        zs = (lo[2] + np.arange(dims[2]) * voxel).astype(F)
        vol = np.empty(dims, F)
        for z0 in range(0, dims[2], chunk):
            z1 = min(dims[2], z0 + chunk)
            X, Y, Z = np.meshgrid(xs, ys, zs[z0:z1], indexing="ij")
            P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
            vol[:, :, z0:z1] = self.eval(P).reshape(dims[0], dims[1], z1 - z0)
        vol[0, :, :] = vol[-1, :, :] = 1
        vol[:, 0, :] = vol[:, -1, :] = 1
        vol[:, :, 0] = vol[:, :, -1] = 1
        if vol.min() >= 0:
            raise ValueError("field %s is empty" % self.name)
        verts, faces, normals, _ = measure.marching_cubes(vol, 0.0, spacing=(voxel,) * 3, gradient_direction="ascent")
        verts = verts + lo
        faces = faces[:, [0, 2, 1]]          # outward-facing winding
        if verbose:
            print("  mesh %-12s grid %s  %d verts  %d tris  %.1fs" % (self.name, tuple(dims), len(verts), len(faces), time.time() - t0))
        return verts.astype(np.float64), faces.astype(np.int64)

    def project(self, verts, iters=2, h=None):
        """Pull vertices onto the exact zero surface (removes marching-cubes faceting on sharp-ish parts)."""
        V = np.asarray(verts, dtype=np.float64).copy()
        h = h or 1e-3
        for _ in range(iters):
            P = V.astype(F)
            d = self.eval(P).astype(np.float64)
            g = np.zeros_like(V)
            for i in range(3):
                e = np.zeros(3, F)
                e[i] = h
                g[:, i] = (self.eval(P + e) - self.eval(P - e)) / (2 * h)
            gl2 = np.maximum((g * g).sum(1), 1e-8)
            step = (d / gl2)[:, None] * g
            sl = np.linalg.norm(step, axis=1)
            lim = np.minimum(1.0, (2 * h) / np.maximum(sl, 1e-12))[:, None]
            V -= step * lim
        return V


# ----------------------------------------------------------------------------------------- blender bridge
def to_blender(name, verts, faces, collection=None, smooth=True):
    import bpy
    me = bpy.data.meshes.new(name)
    nv, nf = len(verts), len(faces)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.asarray(verts, dtype=np.float32).ravel())
    me.loops.add(nf * 3)
    me.loops.foreach_set("vertex_index", np.asarray(faces, dtype=np.int32).ravel())
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 3, 3, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(nf, 3, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(nf, dtype=bool))
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def clean_islands(verts, faces, min_tris=60):
    """Drop tiny disconnected pieces (marching cubes specks)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    nv = len(verts)
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv))
    ncomp, lab = connected_components(A, directed=False)
    flab = lab[faces[:, 0]]
    counts = np.bincount(flab, minlength=ncomp)
    keepf = counts[flab] >= min_tris
    faces = faces[keepf]
    used = np.unique(faces)
    remap = -np.ones(nv, np.int64)
    remap[used] = np.arange(len(used))
    return verts[used], remap[faces]


def fix_winding(ob):
    """Flip a closed mesh whose faces point inward (negative signed volume)."""
    import bpy
    me = ob.data
    n = len(me.vertices)
    V = np.zeros(n * 3, np.float64)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    tri = [p.vertices[:3] for p in me.polygons if len(p.vertices) == 3]
    if not tri:
        return False
    T = np.array(tri)
    vol = np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6.0
    if vol < 0:
        me.flip_normals()
        me.update()
        return True
    return False
