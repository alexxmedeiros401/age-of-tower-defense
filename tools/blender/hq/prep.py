"""Paint-time attributes on the high-poly: skin warmth (nose, cheeks, ears, knuckles, knees...) and the
eye colours (sclera, iris, pupil, painted highlight) as vertex attributes; then materials."""
import math
import numpy as np
import bpy
import caveman as cm
from sdf import v3, norm, axis_angle
from mats import lin


def warm_points():
    hp = cm.hp
    pts = [(hp((0, -0.248, 1.604)), 0.075, 0.95)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.105, -0.15, 1.6)), 0.065, 0.55), (hp((sx * 0.19, 0.03, 1.665)), 0.07, 0.75),
                (cm.J["elbow_" + ("R" if sx < 0 else "L")] + v3((0, 0.03, 0)), 0.08, 0.35),
                (cm.J["knee_" + ("R" if sx < 0 else "L")] + v3((0, -0.04, 0)), 0.09, 0.4),
                (cm.J["shoulder_" + ("R" if sx < 0 else "L")] + v3((0, 0, 0.11)), 0.13, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = cm.hand_frame(side)
        for o in (0.043, 0.0145, -0.0145, -0.043):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.035, 0.5))
        an = cm.J["ankle_" + side]
        sx = -1 if side == "R" else 1
        pts.append((an + v3((0, -0.17, -0.07)), 0.07, 0.5))
        pts.append((an + v3((0, 0.05, -0.07)), 0.06, 0.3))
    return pts


def paint_skin(ob):
    me = ob.data
    V = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3) + np.array(ob.location, np.float32)
    w = np.zeros(len(V), np.float32)
    for c, r, k in warm_points():
        d = np.linalg.norm(V - c.astype(np.float32), axis=1)
        w += k * np.exp(-(d / r) ** 2)
    a = me.attributes.get("warm") or me.attributes.new("warm", "FLOAT", "POINT")
    a.data.foreach_set("value", np.clip(w, 0, 1))


def paint_eyes(ob):
    me = ob.data
    V = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3).astype(np.float64)
    sclera, iris_o, iris_i, pupil, hi = lin((0.95, 0.93, 0.88)), lin((0.28, 0.16, 0.06)), lin((0.62, 0.42, 0.16)), lin((0.03, 0.02, 0.02)), lin((1, 1, 1))
    cols = np.zeros((len(V), 4), np.float32)
    for i, p in enumerate(V):
        sx = 1 if p[0] > 0 else -1
        c = cm.eye_c(sx)
        v = norm(p - c)
        g = norm((-sx * 0.1, -1.0, -0.12))
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(v @ g)))))
        hdir = axis_angle(norm(np.cross(g, (0.6, 0, 1.0))), math.radians(-13)) @ g
        hang = math.degrees(math.acos(max(-1.0, min(1.0, float(v @ hdir)))))
        if hang < 5.0:
            col = hi
        elif ang < 13.0:
            col = pupil
        elif ang < 31.0:
            t = (ang - 13.0) / 18.0
            col = tuple(iris_i[k] * (1 - t) + iris_o[k] * t for k in range(4))
        elif ang < 34.0:
            col = tuple(x * 0.45 for x in iris_o[:3]) + (1,)
        else:
            col = sclera
        cols[i] = col
    a = me.color_attributes.get("eyecol") or me.color_attributes.new("eyecol", "FLOAT_COLOR", "POINT")
    a.data.foreach_set("color", cols.ravel())
