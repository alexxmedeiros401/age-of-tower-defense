"""Armature, skin weights and procedural keyframed animation for the HQ Rock Slinger.

Posing is done with a small forward-kinematics solver (world-space aims + analytic two-bone IK), so poses
are written as 'where should this limb point' instead of raw local rotations."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion, kdtree
import character as cm

V = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))


def prop_specs():
    """Bones for what the character holds (not skinned to the body). Default: the sling and its stone."""
    if hasattr(cm.module(), "prop_bones"):
        return cm.prop_bones()
    fist, attach, pouch = cm.sling_points()
    return [("sling", attach, pouch, "hand.R"),
            ("stone", pouch + np.array((0, 0, 0.03)), pouch + np.array((0, 0, -0.09)), "sling")]


def non_body_bones():
    """Bones the sculpt's skin weights must never use: props, plus extra bones (cape, machine parts...)."""
    names = {s[0] for s in prop_specs()}
    extra = getattr(cm.module(), "extra_bones", None)
    if extra is not None:
        names |= {s[0] for s in extra()}
    return names


def bone_specs():
    hp = cm.hp
    wrR, fR, nR, tR = cm.hand_frame("R")
    wrL, fL, nL, tL = cm.hand_frame("L")
    tb = {"spine": ((0, 0.03, 0.93), (0, 0.045, 1.13)), "chest": ((0, 0.045, 1.13), (0, 0.06, 1.38)),
          "neck": ((0, 0.06, 1.38), hp((0, 0.02, 1.56))), "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))), "clavicle_z": 1.37}
    if hasattr(cm.module(), "torso_bones"):
        tb.update(cm.torso_bones())
    cz = tb["clavicle_z"]
    specs = [
        ("root", cm.J["root"], cm.J["root"] + np.array((0, 0, 0.13)), None),
        ("spine", tb["spine"][0], tb["spine"][1], "root"),
        ("chest", tb["chest"][0], tb["chest"][1], "spine"),
        ("neck", tb["neck"][0], tb["neck"][1], "chest"),
        ("head", tb["head"][0], tb["head"][1], "neck"),
        ("clavicle.R", (-0.07, 0.06, cz), cm.J["shoulder_R"], "chest"),
        ("upperarm.R", cm.J["shoulder_R"], cm.J["elbow_R"], "clavicle.R"),
        ("forearm.R", cm.J["elbow_R"], cm.J["wrist_R"], "upperarm.R"),
        ("hand.R", wrR, wrR + fR * 0.17, "forearm.R"),
        ("clavicle.L", (0.07, 0.06, cz), cm.J["shoulder_L"], "chest"),
        ("upperarm.L", cm.J["shoulder_L"], cm.J["elbow_L"], "clavicle.L"),
        ("forearm.L", cm.J["elbow_L"], cm.J["wrist_L"], "upperarm.L"),
        ("hand.L", wrL, wrL + fL * 0.17, "forearm.L"),
        ("thigh.R", cm.J["hip_R"], cm.J["knee_R"], "root"),
        ("shin.R", cm.J["knee_R"], cm.J["ankle_R"], "thigh.R"),
        ("foot.R", cm.J["ankle_R"], cm.J["toe_R"], "shin.R"),
        ("thigh.L", cm.J["hip_L"], cm.J["knee_L"], "root"),
        ("shin.L", cm.J["knee_L"], cm.J["ankle_L"], "thigh.L"),
        ("foot.L", cm.J["ankle_L"], cm.J["toe_L"], "shin.L"),
    ] + prop_specs()
    extra = getattr(cm.module(), "extra_bones", None)
    if extra is not None:
        specs += extra()
    return specs


def build_armature(name="CavemanRig"):
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    for nm, h, t, par in bone_specs():
        eb = arm.edit_bones.new(nm)
        eb.head = V(h)
        eb.tail = V(t)
        if par:
            eb.parent = arm.edit_bones[par]
            eb.use_connect = False
        # roll: keep bone Z toward the character's front (-Y) or up, consistently
        d = (eb.tail - eb.head).normalized()
        ref = Vector((0, -1, 0)) if abs(d.y) < 0.9 else Vector((0, 0, 1))
        eb.align_roll(ref)
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in arm.bones:
        b.use_deform = True
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return ob


# ======================================================================================= weights
def _weights_of(ob):
    vg_names = {g.index: g.name for g in ob.vertex_groups}
    out = []
    for v in ob.data.vertices:
        out.append({vg_names[g.group]: g.weight for g in v.groups if g.weight > 1e-4})
    return out


def auto_weights(arm_ob, skin_ob, exclude=("sling", "stone")):
    for b in arm_ob.data.bones:
        b.use_deform = b.name not in exclude
    bpy.ops.object.select_all(action="DESELECT")
    skin_ob.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for b in arm_ob.data.bones:
        b.use_deform = True
    # any vertex the heat solve missed: weight from the nearest bone segment
    names = [b.name for b in arm_ob.data.bones if b.name not in exclude]
    segs = [(V(arm_ob.data.bones[n].head_local), V(arm_ob.data.bones[n].tail_local)) for n in names]
    W = _weights_of(skin_ob)
    fixed = 0
    for i, w in enumerate(W):
        if sum(w.values()) > 0.05:
            continue
        p = skin_ob.data.vertices[i].co
        best, bd = None, 1e9
        for n, (a, b) in zip(names, segs):
            ab = b - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
            d = (a + ab * t - p).length
            if d < bd:
                best, bd = n, d
        g = skin_ob.vertex_groups.get(best) or skin_ob.vertex_groups.new(name=best)
        g.add([i], 1.0, "REPLACE")
        fixed += 1
    return fixed


def transfer_weights(src_ob, dst_ob, k=4, smooth_power=2.0, allowed=None, caps=None):
    """Copy skin weights to clothing/accessories: inverse-distance blend of the k nearest skin vertices,
    restricted to `allowed` bones (renormalised) and with optional per-bone caps."""
    W = _weights_of(src_ob)
    kd = kdtree.KDTree(len(src_ob.data.vertices))
    for i, v in enumerate(src_ob.data.vertices):
        kd.insert(src_ob.matrix_world @ v.co, i)
    kd.balance()
    groups = {}
    for v in dst_ob.data.vertices:
        p = dst_ob.matrix_world @ v.co
        acc = {}
        tot = 0.0
        for (co, idx, dist) in kd.find_n(p, k):
            w = 1.0 / max(dist, 1e-4) ** smooth_power
            tot += w
            for n, x in W[idx].items():
                if allowed is not None and n not in allowed:
                    continue
                acc[n] = acc.get(n, 0.0) + x * w
        s = sum(acc.values())
        if s <= 1e-9:
            acc = {"chest" if allowed is None or "chest" in allowed else sorted(allowed)[0]: 1.0}
            s = 1.0
        acc = {n: x / s for n, x in acc.items()}
        if caps:
            for n, cap in caps.items():
                if acc.get(n, 0.0) > cap:
                    extra = acc[n] - cap
                    acc[n] = cap
                    others = [m for m in acc if m != n]
                    tgt = others[0] if others else "root"
                    if not others:
                        acc["root"] = extra
                    else:
                        tot_o = sum(acc[m] for m in others) or 1.0
                        for m in others:
                            acc[m] += extra * acc[m] / tot_o
        for n, x in acc.items():
            if x < 0.01:
                continue
            g = groups.get(n) or dst_ob.vertex_groups.get(n) or dst_ob.vertex_groups.new(name=n)
            groups[n] = g
            g.add([v.index], x, "REPLACE")


def set_weights(ob, idx, wdict):
    for g in ob.vertex_groups:
        g.remove([idx])
    for n, x in wdict.items():
        if x <= 1e-4:
            continue
        g = ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n)
        g.add([idx], x, "REPLACE")


def fix_skin_weights(skin_ob):
    """Face rigid with the head (eyes, teeth and hair are rigid with it too); a soft neck band;
    deltoids follow the upper arms more so raised arms keep their shoulders."""
    hp = cm.hp
    z0, z1 = hp((0, 0, 1.455))[2], hp((0, 0, 1.52))[2]
    W = _weights_of(skin_ob)
    for v, w in zip(skin_ob.data.vertices, W):
        p = v.co
        if abs(p.x) < 0.27 and p.y < 0.24 and p.z > z0:
            t = max(0.0, min(1.0, (p.z - z0) / (z1 - z0)))
            t = t * t * (3 - 2 * t)
            nw = {n: x * (1 - t) for n, x in w.items()}
            nw["head"] = nw.get("head", 0.0) + t
            s = sum(nw.values())
            set_weights(skin_ob, v.index, {n: x / s for n, x in nw.items()})
            continue
        for side, sx in (("R", -1), ("L", 1)):
            c = Vector(cm.J["shoulder_" + side]) + Vector((sx * 0.03, 0.0, 0.02))
            d = (p - c).length
            if d < 0.17 and p.x * sx > abs(c.x) - 0.02 and p.z > c.z - 0.06:
                k = (1 - d / 0.17) ** 1.5 * 0.5
                nw = {n: x * (1 - k) for n, x in w.items()}
                nw["upperarm." + side] = nw.get("upperarm." + side, 0.0) + k
                s = sum(nw.values())
                set_weights(skin_ob, v.index, {n: x / s for n, x in nw.items()})


def rigid_weights(ob, bone):
    g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    g.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")


def limit_and_normalize(ob, limit=4):
    vg = {g.index: g for g in ob.vertex_groups}
    for v in ob.data.vertices:
        ws = sorted([(g.weight, g.group) for g in v.groups], reverse=True)
        keep = ws[:limit]
        tot = sum(w for w, _ in keep) or 1.0
        for w, gi in ws[limit:]:
            vg[gi].remove([v.index])
        for w, gi in keep:
            vg[gi].add([v.index], w / tot, "REPLACE")


# ======================================================================================= posing
class Poser:
    def __init__(self, arm_ob):
        self.ob = arm_ob
        self.bones = arm_ob.data.bones
        self.rest = {b.name: b.matrix_local.copy() for b in self.bones}
        self.order = []
        def visit(b):
            self.order.append(b.name)
            for c in b.children:
                visit(c)
        for b in self.bones:
            if b.parent is None:
                visit(b)

    def solve(self, aims, root_off=Vector((0, 0, 0)), root_rot=Quaternion(), scales=None, offsets=None):
        """aims: bone -> world direction Vector, or callable(P, base)->direction, or ('rot', Quaternion world).
        root_off/root_rot move the body ("root"); other parentless bones (machines) stay put unless `offsets` moves them.
        scales: bone -> uniform factor or (x, y, z) in bone space (y = along the bone: stretch a rope).
        Returns {bone: (loc, quat, scale)} local pose channels and the posed matrices P."""
        P, out = {}, {}
        for nm in self.order:
            b = self.bones[nm]
            if b.parent is not None:
                base = P[b.parent.name] @ (self.rest[b.parent.name].inverted() @ self.rest[nm])
            elif nm == "root":
                r = self.rest[nm]
                head = r.translation
                rot = root_rot.to_matrix().to_4x4()
                base = Matrix.Translation(head + root_off) @ rot @ Matrix.Translation(-head) @ r
            else:
                base = Matrix.Translation(Vector((offsets or {}).get(nm, (0, 0, 0)))) @ self.rest[nm]
            M = base
            a = aims.get(nm)
            if callable(a):
                a = a(P, base)                 # may return a direction, (direction, twist), ("rot", q) or ("frame", ...)
            if a is not None:
                if isinstance(a, tuple) and isinstance(a[0], str) and a[0] == "rot":
                    R = a[1].to_matrix() @ base.to_3x3()
                    M = Matrix.Translation(base.translation) @ R.to_4x4()
                elif isinstance(a, tuple) and isinstance(a[0], str) and a[0] == "frame":
                    # full world orientation: rest-pose direction r1 -> w1 exactly, r2 -> w2 (as near as possible)
                    _, r1, w1, r2, w2 = a
                    R = frame_map(r1, w1, r2, w2) @ self.rest[nm].to_3x3()
                    M = Matrix.Translation(base.translation) @ R.to_4x4()
                else:
                    d = a
                    twist = 0.0
                    if isinstance(d, tuple):
                        d, twist = d
                    d = Vector(d).normalized()
                    y0 = base.col[1].xyz.normalized()
                    q = y0.rotation_difference(d)
                    R = q.to_matrix() @ base.to_3x3()
                    if twist:
                        R = Quaternion(d, twist).to_matrix() @ R
                    M = Matrix.Translation(base.translation) @ R.to_4x4()
            P[nm] = M
            # pose = parent pose @ (parent rest^-1 @ rest) @ basis; a parentless bone's pose = rest @ basis, so its
            # channels must carry the root offset / rotation too (measured from the rest pose, not from `base`)
            basis = (base if b.parent is not None else self.rest[nm]).inverted() @ M
            loc, quat, _ = basis.decompose()
            sc = (scales or {}).get(nm, 1.0)
            out[nm] = (loc if b.parent is None else Vector((0, 0, 0)), quat, sc)
        return out, P

    def key(self, channels, frame):
        for nm, (loc, quat, sc) in channels.items():
            pb = self.ob.pose.bones[nm]
            pb.rotation_quaternion = quat
            pb.keyframe_insert("rotation_quaternion", frame=frame)
            if self.bones[nm].parent is None:
                pb.location = loc
                pb.keyframe_insert("location", frame=frame)
            pb.scale = tuple(sc) if isinstance(sc, (tuple, list, Vector)) else (sc, sc, sc)
            pb.keyframe_insert("scale", frame=frame)


def frame_map(r1, w1, r2, w2):
    """Rotation taking direction r1 to w1 and the plane (r1, r2) to the plane (w1, w2)."""
    def basis(a, b):
        a = Vector(a).normalized()
        b = Vector(b)
        b = (b - a * b.dot(a)).normalized()
        return Matrix((a, b, a.cross(b))).transposed()       # columns a, b, a x b
    return basis(w1, w2) @ basis(r1, r2).transposed()


def head_of(P, nm):
    return P[nm].translation.copy()


def two_bone(root, target, la, lb, pole):
    """Analytic two-bone IK: returns the joint (elbow/knee) position."""
    root, target, pole = Vector(root), Vector(target), Vector(pole)
    d = target - root
    dist = min(d.length, (la + lb) * 0.999)
    u = d.normalized()
    cosa = (la * la + dist * dist - lb * lb) / (2 * la * dist)
    cosa = max(-1.0, min(1.0, cosa))
    sina = math.sqrt(1 - cosa * cosa)
    pv = (pole - u * pole.dot(u))
    pv = pv.normalized() if pv.length > 1e-6 else Vector((0, -1, 0))
    return root + u * (la * cosa) + pv * (la * sina)


def bone_len(arm_ob, nm):
    b = arm_ob.data.bones[nm]
    return (b.tail_local - b.head_local).length


def leg_aims(arm_ob, side, ankle_target, pole=Vector((0, -1, 0.15))):
    la, lb = bone_len(arm_ob, "thigh." + side), bone_len(arm_ob, "shin." + side)
    st = {}
    def thigh(P, base):
        hip = base.translation
        knee = two_bone(hip, ankle_target, la, lb, pole)
        st["knee"] = knee
        return knee - hip
    def shin(P, base):
        return Vector(ankle_target) - st["knee"]
    rest_foot = (arm_ob.data.bones["foot." + side].tail_local - arm_ob.data.bones["foot." + side].head_local).normalized()
    return {"thigh." + side: thigh, "shin." + side: shin, "foot." + side: rest_foot}


def arm_aims(arm_ob, side, wrist_target, pole, hand_dir=None, hand_twist=0.0):
    la, lb = bone_len(arm_ob, "upperarm." + side), bone_len(arm_ob, "forearm." + side)
    st = {}
    def upper(P, base):
        sh = base.translation
        el = two_bone(sh, wrist_target, la, lb, pole)
        st["el"] = el
        return el - sh
    def fore(P, base):
        return Vector(wrist_target) - st["el"]
    aims = {"upperarm." + side: upper, "forearm." + side: fore}
    if hand_dir is not None:
        aims["hand." + side] = (Vector(hand_dir), hand_twist) if hand_twist else Vector(hand_dir)
    return aims


def sdf_weights(skin_ob, field, arm_ob, sigma=0.032, exclude=("sling", "stone")):
    """Skin weights straight from the sculpt: every body shape belongs to the bone nearest to it, and a vertex
    takes its weights from the shapes it lies on (soft blend where shapes were smooth-unioned)."""
    import numpy as np
    from sdf import F
    skip = set(exclude) | non_body_bones()
    names = [b.name for b in arm_ob.data.bones if b.name not in skip and not b.name.startswith("cape")]
    segs = [(np.array(arm_ob.data.bones[n].head_local), np.array(arm_ob.data.bones[n].tail_local)) for n in names]
    penalty = {n: (0.02 if n.startswith("clavicle") else 0.0) for n in names}
    tz = getattr(cm.module(), "TORSO_Z", (0.7, 0.88, 1.06, 1.47))

    def seg_dist(p, a, b):
        ab = b - a
        t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
        return np.linalg.norm(a + ab * t - p)

    owners = []
    for kind, prim, k, label in field.ops:
        if kind != "add":
            continue
        c = (np.asarray(prim.lo) + np.asarray(prim.hi)) / 2
        best = min(names, key=lambda n: seg_dist(c, *segs[names.index(n)]) + penalty[n])
        # torso shapes on the centre line: by height
        if abs(c[0]) < 0.12 and tz[0] < c[2] < tz[3] and best not in ("neck", "head"):
            best = "root" if c[2] < tz[1] else ("spine" if c[2] < tz[2] else "chest")
        owners.append((prim, best))
    P = np.zeros((len(skin_ob.data.vertices), 3), np.float32)
    skin_ob.data.vertices.foreach_get("co", P.ravel())
    P = P + np.array(skin_ob.location, np.float32)
    D = {n: np.full(len(P), 1e3, np.float32) for n in names}
    for prim, n in owners:
        d = np.maximum(prim(P.astype(F)), 0.0)
        D[n] = np.minimum(D[n], d)
    W = np.stack([np.exp(-(D[n] / sigma) ** 2) for n in names], 1)
    W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
    for g in list(skin_ob.vertex_groups):
        skin_ob.vertex_groups.remove(g)
    groups = {n: skin_ob.vertex_groups.new(name=n) for n in names}
    for i in range(len(P)):
        row = W[i]
        top = np.argsort(-row)[:4]
        s = row[top].sum()
        for j in top:
            if row[j] / s > 0.01:
                groups[names[j]].add([i], float(row[j] / s), "REPLACE")
    m = skin_ob.modifiers.new("Armature", "ARMATURE")
    m.object = arm_ob
    skin_ob.parent = arm_ob
    return owners
