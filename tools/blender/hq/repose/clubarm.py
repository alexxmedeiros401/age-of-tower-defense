# Right arm of a club/weapon holder: the hand path and the weapon direction are keyed; the arm is solved so the
# forearm stays square to the weapon (a straight wrist), the elbow roll is carried over frame to frame (no flips),
# and pronation goes into the forearm (shared by its half bone).
# usage: python3 clubarm.py IN.glb OUT.glb CFG.py
import bpy, sys, math, importlib.util
from mathutils import Vector, Matrix, Quaternion
IN, OUT, CFGPY = sys.argv[1:4]
sp = importlib.util.spec_from_file_location('cfg', CFGPY); C = importlib.util.module_from_spec(sp); sp.loader.exec_module(C)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
P = arm.pose.bones; B = arm.data.bones
S0 = B['upperarm.R'].head_local.copy()
Lu = B['upperarm.R'].length; Lf = B['forearm.R'].length
chest_rest = B['chest'].matrix_local.copy()
# weapon axis in hand-local space
club_local = (B['hand.R'].matrix_local.to_3x3().inverted() @ C.CLUB_AXIS).normalized()
OUT_DIR = Vector((-1, 0.3, -0.6)).normalized()   # where the elbow likes to point (out, back, down)

def interp_pos(keys, f):
    fs = [k[0] for k in keys]
    if f <= fs[0]: return keys[0][1].copy()
    if f >= fs[-1]: return keys[-1][1].copy()
    i = max(j for j in range(len(fs)) if fs[j] <= f)
    t = (f - fs[i]) / (fs[i + 1] - fs[i])
    p0 = keys[max(i - 1, 0)][1]; p1 = keys[i][1]; p2 = keys[i + 1][1]; p3 = keys[min(i + 2, len(keys) - 1)][1]
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)

def interp_dir(keys, f):
    fs = [k[0] for k in keys]
    if f <= fs[0]: return keys[0][2].normalized()
    if f >= fs[-1]: return keys[-1][2].normalized()
    i = max(j for j in range(len(fs)) if fs[j] <= f)
    t = (f - fs[i]) / (fs[i + 1] - fs[i]); t = t * t * (3 - 2 * t)
    a = keys[i][2].normalized(); b = keys[i + 1][2].normalized()
    return (Quaternion().slerp(a.rotation_difference(b), t) @ a).normalized()

def solve(h, d, prev_f):
    # forearm direction f square to d, elbow on the upper-arm sphere
    a = d.orthogonal().normalized(); b = d.cross(a).normalized()
    best = None
    for k in range(360):
        th = math.radians(k)
        fdir = (a * math.cos(th) + b * math.sin(th))
        e = h - fdir * Lf
        r = abs((e - S0).length - Lu)
        out = (e - S0).normalized().dot(OUT_DIR)
        cont = (fdir - prev_f).length if prev_f is not None else 0
        score = r * 10 - 0.05 * out + 0.15 * cont
        if best is None or score < best[0]: best = (score, fdir, e, r)
    _, fdir, e, r = best
    e = S0 + (e - S0).normalized() * Lu
    return fdir, e, r

def chest_xf():
    return P['chest'].matrix @ chest_rest.inverted()

def swing_matrix(prev_m, ydir, pos):
    # rotate prev_m so its Y axis points along ydir with the least twist (parallel transport)
    y0 = prev_m.to_3x3().col[1].normalized()
    q = y0.rotation_difference(ydir)
    r = q.to_matrix() @ prev_m.to_3x3()
    m = r.to_4x4(); m.translation = pos
    return m

for clip, keys in C.CLIPS.items():
    act = bpy.data.actions[clip]; arm.animation_data.action = act
    f0, f1 = [int(x) for x in act.frame_range]
    frames = list(range(f0, f1 + 1))
    sc.frame_set(f0)
    prev_u = None; prev_f = None; prev_fm = None; prev_roll = None
    rows = []
    prev_psi = 0.0; prev_th = None; prev_tw = 0.0
    Bu, Bf, Bc = B['upperarm.R'].matrix_local.to_3x3(), B['forearm.R'].matrix_local.to_3x3(), B['clavicle.R'].matrix_local.to_3x3()
    rel_u = Bc.inverted() @ Bu; rel_f = Bu.inverted() @ Bf
    club_f = Bf.inverted() @ C.CLUB_AXIS
    Yv = Vector((0, 1, 0))
    for f in frames:
        sc.frame_set(f)
        X = chest_xf()
        h = X @ interp_pos(keys, f)
        d = (X.to_3x3() @ interp_dir(keys, f)).normalized()
        S = P['upperarm.R'].matrix.translation.copy()
        Zu = P['clavicle.R'].matrix.to_3x3() @ rel_u
        a_ = d.orthogonal().normalized(); b_ = d.cross(a_).normalized()
        outw = (X.to_3x3() @ OUT_DIR).normalized()
        best = None
        for kt in range(72 * 7):
            th = math.radians((kt // 7) * 5); tilt = math.radians(((kt % 7) - 3) * 12)
            F = ((a_ * math.cos(th) + b_ * math.sin(th)) * math.cos(tilt) + d * math.sin(tilt)).normalized()
            e = h - F * Lf
            e = S + (e - S).normalized() * Lu
            hh = e + F * Lf
            U = (e - S).normalized()
            reach = (hh - h).length
            sw = Zu.col[1].normalized().rotation_difference(U).to_matrix() @ Zu
            for kq in range(-3 * 9, 4 * 9):
                kp = kq // 9 if kq >= 0 else -((-kq + 8) // 9); kt2 = (kq % 9) - 4
                psi = math.radians(kp * 10)
                Mu = Matrix.Rotation(psi, 3, U) @ sw
                base = Mu @ rel_f
                Q = Yv.rotation_difference((base.inverted() @ F).normalized()).to_matrix()
                Mf = Matrix.Rotation(math.radians(kt2 * 15), 3, F) @ base @ Q
                cw = (Mf @ club_f).normalized()
                err = math.degrees(cw.angle(d))
                dpsi = abs(math.degrees(psi - prev_psi))
                score = reach * 40 + err * 0.02 + 0.01 * max(0.0, err - 35) ** 1.5 + dpsi * 0.03 + abs(kp * 10) * 0.05 + abs(kt2 * 15) * 0.008 + abs(kt2 * 15 - prev_tw) * 0.08 - 2 * U.dot(outw)
                if prev_th is not None: score += 0.5 * (F - prev_th).length
                if best is None or score < best[0]: best = (score, Mu, Mf, e, reach, err, psi, F, kt2 * 15)
        _, Mu, Mf, e, resid, err, psi, F, twv = best
        prev_psi = psi; prev_th = F; prev_tw = twv
        m = Mu.to_4x4(); m.translation = S; P['upperarm.R'].matrix = m; bpy.context.view_layer.update()
        m = Mf.to_4x4(); m.translation = P['forearm.R'].matrix.translation.copy(); P['forearm.R'].matrix = m
        P['hand.R'].rotation_quaternion = Quaternion(); bpy.context.view_layer.update()
        cw = (P['hand.R'].matrix.to_3x3() @ club_local).normalized()
        hm = P['hand.R'].matrix; q = cw.rotation_difference(d); hp = hm.translation.copy()
        P['hand.R'].matrix = Matrix.Translation(hp) @ q.to_matrix().to_4x4() @ Matrix.Translation(-hp) @ hm
        bpy.context.view_layer.update()
        cw = (P['hand.R'].matrix.to_3x3() @ club_local).normalized()
        for b in ('upperarm.R', 'forearm.R', 'hand.R'):
            P[b].keyframe_insert('rotation_quaternion', frame=f)
        P['upperarm_half.R'].rotation_quaternion = Quaternion().slerp(P['upperarm.R'].rotation_quaternion, 0.5)
        P['forearm_half.R'].rotation_quaternion = Quaternion().slerp(P['forearm.R'].rotation_quaternion, 0.5)
        P['upperarm_half.R'].keyframe_insert('rotation_quaternion', frame=f)
        P['forearm_half.R'].keyframe_insert('rotation_quaternion', frame=f)
        tw = math.degrees(P['forearm.R'].rotation_quaternion.to_swing_twist('Y')[1])
        print(clip, f, 'psi %.0f' % math.degrees(psi), 'reach resid %.3f' % resid, 'weapon err %.1f' % math.degrees(cw.angle(d)), 'forearm twist %.0f' % tw, 'wrist %.0f' % math.degrees(P['hand.R'].rotation_quaternion.angle),
              'elbow %.0f' % math.degrees(P['forearm.R'].rotation_quaternion.to_swing_twist('Y')[0].angle), flush=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                          export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                          export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
print('wrote', OUT)
