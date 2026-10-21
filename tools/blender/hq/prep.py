"""Paint-time attributes on the high-poly: skin warmth (nose, cheeks, ears, knuckles, knees...) and the
eye colours (sclera, iris, pupil, painted highlight) as vertex attributes; then materials."""
import math
import numpy as np
import bpy
import character as cm
from sdf import v3, norm, axis_angle
from mats import lin


def paint_skin(ob):
    me = ob.data
    V = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3) + np.array(ob.location, np.float32)
    w = np.zeros(len(V), np.float32)
    for c, r, k in cm.warm_points():
        d = np.linalg.norm(V - c.astype(np.float32), axis=1)
        w += k * np.exp(-(d / r) ** 2)
    a = me.attributes.get("warm") or me.attributes.new("warm", "FLOAT", "POINT")
    a.data.foreach_set("value", np.clip(w, 0, 1))


def paint_eyes(ob, iris=None):
    """Sclera, iris (brown unless the character gives `iris` = (outer ring, inner ring) colours), pupil, highlight."""
    me = ob.data
    V = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3).astype(np.float64)
    io, ii = iris if iris is not None else ((0.28, 0.16, 0.06), (0.62, 0.42, 0.16))
    sclera, iris_o, iris_i, pupil, hi = lin((0.95, 0.93, 0.88)), lin(io), lin(ii), lin((0.03, 0.02, 0.02)), lin((1, 1, 1))
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


def region_masks(ob):
    """Split the integer 'region' labels into one float mask per label (r0, r1, ...). Interpolating the integer
    itself across a face would pass through the labels in between (fringes); masks blend cleanly."""
    me = ob.data
    a = me.attributes.get("region")
    if a is None:
        return []
    lab = np.zeros(len(me.vertices), np.int32)
    a.data.foreach_get("value", lab)
    out = []
    for L in np.unique(lab):
        m = (lab == L).astype(np.float32)
        pa = me.attributes.get("p%d" % int(L))
        if pa is not None:                       # painted label: smooth ramp from the sculpt's paint distance
            m = np.zeros(len(me.vertices), np.float32)
            pa.data.foreach_get("value", m)
        nm = "r%d" % int(L)
        att = me.attributes.get(nm) or me.attributes.new(nm, "FLOAT", "POINT")
        att.data.foreach_set("value", m)
        out.append(nm)
    return out
