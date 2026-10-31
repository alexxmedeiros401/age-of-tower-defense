"""Step 5 (numpy/scipy): the pose of the OLD rig that puts the old hero's body onto the Tripo body -> fit.json.

    python3 fit.py -- --hero ugo [--reg 0.05] [--nfev 80]

Least squares (point to plane, soft-L1) between the old body mesh, skinned with its own weights and posed, and the
Tripo body (label 0). Unknowns: a rotation per body bone (the spine chain, neck and head turn freely; limbs and soft
bones like cape.* bend but do not twist; the root and the feet stay at rest), a global translation and a relative scale
of the Tripo model (the load step's height-based scale is only a start: hoods, hair and feathers make heights a poor
measure). The scale and translation go into the Tripo -> game transform ('xf'), so the fitted pose needs no offset.
Also writes landmarks of the fitted pose (bone heads/tails) that the bake uses (where the head and the face are).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
import common as C

FREE3 = ("spine", "chest", "neck", "head")
FIXED = ("root", "foot.R", "foot.L")


class Rig:
    def __init__(self, bn, bm, bp):
        self.bn = [str(b) for b in bn]
        self.rest = {n: np.array(m) for n, m in zip(self.bn, bm)}
        self.parent = {n: (self.bn[p] if p >= 0 else None) for n, p in zip(self.bn, bp)}
        self.order = []
        def add(n):
            if n in self.order:
                return
            if self.parent[n]:
                add(self.parent[n])
            self.order.append(n)
        for n in self.bn:
            add(n)

    def posed(self, rot):
        P = {}
        for n in self.order:
            R = np.eye(4)
            if n in rot:
                R[:3, :3] = rot[n]
            p = self.parent[n]
            P[n] = self.rest[n] @ R if p is None else P[p] @ np.linalg.inv(self.rest[p]) @ self.rest[n] @ R
        return P

    def skin(self, rot):
        P = self.posed(rot)
        return {n: P[n] @ np.linalg.inv(self.rest[n]) for n in self.order}, P


def lbs(V, W, gn, S):
    out = np.zeros_like(V)
    Vh = np.c_[V, np.ones(len(V))]
    for j, n in enumerate(gn):
        w = W[:, j]
        m = w > 0
        if m.any() and n in S:
            out[m] += w[m, None] * (Vh[m] @ S[n].T)[:, :3]
    return out


def main():
    hid = C.arg("--hero")
    cfg = C.load_cfg(hid)
    Wd = C.work_dir(hid)
    xf0 = json.load(open(os.path.join(Wd, "xf.json")))
    o = np.load(os.path.join(Wd, "old.npz"))
    V, Wt, gn, T, Tp = o["V"], o["W"], [str(x) for x in o["gn"]], o["T"], o["Tprop"]
    rig = Rig(o["bn"], o["bm"], o["bp"])
    info = json.load(open(os.path.join(Wd, "old.json")))
    props = set(info["prop_bones"])
    used = set(np.array(gn)[(Wt[np.unique(T[Tp == -1])] > 0.05).any(0)])
    BONES = [b for b in rig.order if b in used and b not in props and b not in FIXED]
    print("[fit] bones", BONES)
    rng = np.random.default_rng(0)
    bodyv = np.unique(T[Tp == -1])
    sub = rng.choice(bodyv, min(6000, len(bodyv)), replace=False)
    Vs, Ws = V[sub], Wt[sub]
    t = np.load(os.path.join(Wd, "topo.npz"))
    lab = np.load(os.path.join(Wd, "labels.npz"))["lab"]
    idx = np.nonzero(lab == 0)[0]
    idx = idx[rng.choice(len(idx), min(400000, len(idx)), replace=False)]
    Pt = C.to_game(t["C"][idx], xf0)
    Nt = t["N"][idx] @ C.rotz(xf0["yaw"]).T
    tree = cKDTree(Pt)
    # the reverse term: Tripo body points pull the nearest posed old point (without it an old limb can settle on any
    # Tripo surface: Mara's old left hand lay on her belt's hanging ends, 20 cm from the Tripo hand)
    REV = float(C.arg("--rev", cfg.get("fit_reverse", 1.0)))
    Prv = Pt[rng.choice(len(Pt), 8000, replace=False)]
    sub2 = rng.choice(bodyv, min(14000, len(bodyv)), replace=False)
    V2, W2 = V[sub2], Wt[sub2]
    nb = len(BONES)
    free3 = np.array([b in FREE3 for b in BONES])
    REG = float(C.arg("--reg", cfg["fit_reg"]))
    fix_scale = cfg["scale"] != "auto"

    def unpack(x):
        xx = x[:3 * nb].reshape(-1, 3).copy()
        xx[~free3, 1] = 0.0                      # (no twist about the bone's own axis for limbs)
        rot = {b: Rot.from_rotvec(xx[i]).as_matrix() for i, b in enumerate(BONES)}
        tr = x[3 * nb:3 * nb + 3]
        k = 1.0 if fix_scale else np.exp(x[-1])
        return rot, tr, k, xx

    def resid(x):
        rot, tr, k, xx = unpack(x)
        S, _ = rig.skin(rot)
        P = lbs(Vs, Ws, gn, S)
        Y = (P - tr) / k                        # the posed old body in the load step's game frame
        d, i = tree.query(Y)
        r = ((Y - Pt[i]) * Nt[i]).sum(1)
        out = [r, (xx * REG).ravel(), [x[-1] * 0.02]]
        if REV > 0:
            Y2 = (lbs(V2, W2, gn, S) - tr) / k
            d2, _ = cKDTree(Y2).query(Prv)
            out.insert(1, d2 * REV * np.sqrt(len(Vs) / len(Prv)))
        return np.concatenate(out)

    x0 = np.zeros(3 * nb + 4)
    if cfg.get("fit_recentre"):
        # start the translation from the body's hips (props cut away): the load step centres on the whole model's
        # hips, which a big prop at hip height (Brenna's shield) pulls aside, and the fit then settles too small
        def hips(X):
            z0, h = X[:, 2].min(), X[:, 2].max() - X[:, 2].min()
            sl = X[(X[:, 2] > z0 + 0.42 * h) & (X[:, 2] < z0 + 0.5 * h)]
            return np.r_[np.median(sl[:, :2], 0), z0]
        x0[3 * nb:3 * nb + 3] = hips(V[bodyv]) - hips(Pt)
        print("[fit] translation started at", x0[3 * nb:3 * nb + 3].round(4))
    r0 = resid(x0)[:len(Vs)]
    print("[fit] reverse term weight %.2f" % REV)
    print("[fit] initial rms %.4f median %.4f" % (np.sqrt((r0 ** 2).mean()), np.median(np.abs(r0))))
    res = least_squares(resid, x0, loss="soft_l1", f_scale=0.01, max_nfev=int(C.arg("--nfev", "80")), diff_step=1e-4)
    x = res.x
    r1 = resid(x)[:len(Vs)]
    rot, tr, k, xx = unpack(x)
    print("[fit] final rms %.4f median %.4f; translation %s, scale x%.4f" % (np.sqrt((r1 ** 2).mean()), np.median(np.abs(r1)), tr.round(4), k))
    for i, b in enumerate(BONES):
        print("   %-12s %5.1f deg" % (b, np.degrees(np.linalg.norm(xx[i]))), xx[i].round(3))
    xf = dict(yaw=xf0["yaw"], s=xf0["s"] * k, t=(np.array(xf0["t"]) * k + tr).tolist())
    _, Pz = rig.skin(rot)
    marks = {}
    for n in rig.order:
        M = Pz[n]
        L = np.linalg.norm(np.array(info["bones"][n]["tail"]) - np.array(info["bones"][n]["head"]))
        marks[n] = dict(head=M[:3, 3].tolist(), tail=(M[:3, 3] + M[:3, 1] * L).tolist())
    json.dump(dict(rotvec={b: xx[i].tolist() for i, b in enumerate(BONES)}, translation=[0.0, 0.0, 0.0], xf=xf,
                   posed=marks, rms=float(np.sqrt((r1 ** 2).mean()))), open(os.path.join(Wd, "fit.json"), "w"), indent=1)
    print("[fit] xf", xf)


if __name__ == "__main__":
    main()
