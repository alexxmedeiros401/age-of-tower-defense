# Generic arm re-author (both arms, any of the CavemanRig towers): the wrist path, the weapon direction (optional) and
# an elbow hint (optional) are keyed chest-relative; per frame the arm is solved analytically:
#   - the elbow is placed on its circle (two-bone IK) where the upper arm needs the least roll (psi) about its own axis
#     relative to the least-swing frame (big rolls twist the skin), kept outward of the body and continuous;
#   - the forearm bends on the elbow hinge (local X), its twist is chosen (continuous, small) so the hand needs the
#     smallest wrist to point the weapon; a straight wrist when no weapon direction is keyed;
#   - halves (upperarm_half/forearm_half) get half of their bone, forearm_twist.* gets `twist_share` of the hand twist.
# usage: python3 armsolve.py IN.glb OUT.glb CFG.py [report.json]
# CFG:
#   CLIPS = {clip: {'R': keys | callable, 'L': ...}}  (a side left out keeps its shipped motion)
#     keys: [(frame, wrist(Vector, rest armature space = chest-relative), opts dict)], opts: dir (weapon axis direction,
#     chest-relative), up (weapon second axis, needs AXIS2), pole (where the elbow should point, a direction), tw (forearm
#     twist preference, deg). A callable f -> (wrist, opts).
#   AXIS = {'R': Vector}  weapon axis in rest armature space (needed for dir); AXIS2 = {'R': Vector} (for up)
#   OUT = {'R': Vector, 'L': Vector} preferred elbow direction (default out/back/down)
#   POST(ctx, clip, f) optional hook after a frame is keyed (bow strings etc.)
import bpy, sys, math, json, importlib.util
from mathutils import Vector, Matrix, Quaternion

IN, OUT, CFGPY = sys.argv[1:4]
REPORT = sys.argv[4] if len(sys.argv) > 4 else None
sp = importlib.util.spec_from_file_location('cfg', CFGPY); C = importlib.util.module_from_spec(sp); sp.loader.exec_module(C)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
P = arm.pose.bones; B = arm.data.bones
assert arm.matrix_world == Matrix.Identity(4) or True
RB = {b.name: b.matrix_local.copy() for b in B}
chest_rest = RB['chest']
OUTD = getattr(C, 'OUT', {})
TWS = getattr(C, 'TWIST_SHARE', 0.5)
OUTMIN = getattr(C, 'OUTMIN', 0.0)
WFIT = getattr(C, 'WFIT', 1.0)
TWMAX = getattr(C, "TWMAX", 60.0)
CONT = getattr(C, "CONT", 0.0)
TWC = getattr(C, "TWC", 0.0)
TWK = getattr(C, "TWK", 1.5)
for b in P:
    b.rotation_mode = 'QUATERNION'

def rot3(m): return m.to_3x3().normalized()

def interp(keys, f):
    fs = [k[0] for k in keys]
    if f <= fs[0]: i, t = 0, 0.0
    elif f >= fs[-1]: i, t = len(keys) - 2, 1.0
    else:
        i = max(j for j in range(len(fs)) if fs[j] <= f); t = (f - fs[i]) / (fs[i + 1] - fs[i])
    if len(keys) == 1: return keys[0][1].copy(), dict(keys[0][2])
    p0 = keys[max(i - 1, 0)][1]; p1 = keys[i][1]; p2 = keys[i + 1][1]; p3 = keys[min(i + 2, len(keys) - 1)][1]
    t2, t3 = t * t, t * t * t
    pos = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
    o1, o2 = keys[i][2], keys[i + 1][2]; ts = t * t * (3 - 2 * t)
    opts = {}
    for k in ('dir', 'up', 'pole'):
        a, b = o1.get(k), o2.get(k)
        if a is None and b is None: continue
        if a is None: a = b
        if b is None: b = a
        a = a.normalized(); b = b.normalized()
        if k == 'pole': opts[k] = (a.lerp(b, ts)).normalized()
        else: opts[k] = (Quaternion().slerp(a.rotation_difference(b), ts) @ a).normalized()
    for k in ('tw',):
        a, b = o1.get(k), o2.get(k)
        if a is not None or b is not None:
            a = a if a is not None else b; b = b if b is not None else a; opts[k] = a + (b - a) * ts
    return pos, opts

def basis_from(child, parent_pose, desired):
    # pose matrix = parent_pose @ (Rp^-1 @ Rc) @ basis
    rel = RB[B[child].parent.name].inverted() @ RB[child]
    return (parent_pose @ rel).inverted() @ desired

def frame_m(X, Y, Z, t):
    m = Matrix((X, Y, Z)).transposed().to_4x4(); m.translation = t; return m

def ang(a, b, axis):
    # signed angle from a to b about axis
    a = (a - axis * a.dot(axis)).normalized(); b = (b - axis * b.dot(axis)).normalized()
    return math.atan2(axis.dot(a.cross(b)), a.dot(b))

def ang_wrap(a): return math.atan2(math.sin(a), math.cos(a))

def unit_q(q, prev):
    if prev is not None and q.dot(prev) < 0: q = -q
    return q

report = {}
for clip, sides in C.CLIPS.items():
    act = bpy.data.actions[clip]; arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    f0, f1 = [int(round(x)) for x in act.frame_range]
    rep = report.setdefault(clip, {})
    CTX = dict(P=P, B=B, RB=RB, arm=arm, sc=sc, f0=f0, f1=f1)
    if getattr(C, 'PRE', None): C.PRE(CTX, clip)      # (capture the shipped prop motion before the arms change)
    for side, keys in sides.items():
        if keys is None: continue
        ua, fa, ha = 'upperarm.' + side, 'forearm.' + side, 'hand.' + side
        Lu = B[ua].length; Lf = (RB[ha].translation - RB[fa].translation).length
        rel_u = RB['clavicle.' + side].inverted() @ RB[ua]
        rel_f = RB[ua].inverted() @ RB[fa]
        rel_h = RB[fa].inverted() @ RB[ha]
        axis = getattr(C, 'AXIS', {}).get(side); axis2 = getattr(C, 'AXIS2', {}).get(side)
        ax_l = (rot3(RB[ha]).inverted() @ axis).normalized() if axis is not None else None
        ax2_l = (rot3(RB[ha]).inverted() @ axis2).normalized() if axis2 is not None else None
        outd = OUTD.get(side, Vector((-1 if side == 'R' else 1, 0.4, -0.5))).normalized()
        tb = 'forearm_twist.' + side if ('forearm_twist.' + side) in P else None
        grip = Matrix.Identity(3)
        g = getattr(C, 'GRIP', {}).get(side)
        if g is not None:   # the neutral wrist: the shipped hand rotation in a frame where the weapon sits in the fist
            if isinstance(g, Quaternion): grip = g.to_matrix()
            else:
                act_ = arm.animation_data.action
                arm.animation_data.action = bpy.data.actions[g[0]]; sc.frame_set(g[1])
                grip = P[ha].rotation_quaternion.to_matrix().copy()
                arm.animation_data.action = act_
                try: arm.animation_data.action_slot = act_.slots[0]
                except Exception: pass
        prevq = {}; rows = []
        def solve(f, fixed=None):
            # one frame: optimise the elbow (on its circle) and the forearm twist, or use `fixed` (chest-relative
            # elbow direction, twist) from the smoothing pass
            prev_phi = None; prev_tw = 0.0
            if True:
                sc.frame_set(f)
                X = P['chest'].matrix @ chest_rest.inverted()
                wr, o = keys(f) if callable(keys) else interp(keys, f)
                H = X @ wr
                Mc = P['clavicle.' + side].matrix.copy()
                Mu_rc = Mc @ rel_u; S = Mu_rc.translation.copy()
                d = H - S; dl = d.length
                dl = min(max(dl, abs(Lu - Lf) + 1e-3), (Lu + Lf) * 0.995); n = d.normalized(); H = S + n * dl
                a = (Lu * Lu - Lf * Lf + dl * dl) / (2 * dl); r = math.sqrt(max(Lu * Lu - a * a, 1e-8)); Cc = S + n * a
                e1 = n.orthogonal().normalized(); e2 = n.cross(e1).normalized()
                Yr = rot3(Mu_rc).col[1].normalized()
                outw = (rot3(X) @ outd).normalized()
                pole = (rot3(X) @ o['pole']).normalized() if 'pole' in o else None
                dw = (rot3(X) @ o['dir']).normalized() if (ax_l is not None and 'dir' in o) else None
                upw = (rot3(X) @ o['up']).normalized() if (dw is not None and 'up' in o and ax2_l is not None) else None
                pref = o.get('tw', 0.0)
                def arm_at(phi):
                    ed = e1 * math.cos(phi) + e2 * math.sin(phi)
                    E = Cc + ed * r; U = (E - S).normalized(); F = (H - E).normalized()
                    q0 = Yr.rotation_difference(U); M0 = q0.to_matrix() @ rot3(Mu_rc)
                    Zp = F - U * F.dot(U)
                    bend = Zp.length
                    Z0 = M0.col[2].normalized()
                    Zu = Zp.normalized() if bend > 1e-4 else Z0
                    psi = ang(Z0, Zu, U)
                    if bend < 0.25:   # nearly straight arm: the hinge does not pin the roll; ease it to zero
                        psi *= bend / 0.25
                    Mu = (Quaternion(U, psi).to_matrix() @ M0)
                    Mf_r = Mu @ rot3(rel_f)
                    Mf0 = Mf_r.col[1].normalized().rotation_difference(F).to_matrix() @ Mf_r
                    return ed, E, U, F, psi, Mu, Mf0
                def hand_for(F, Mf0, tw):
                    Mf = Quaternion(F, math.radians(tw)).to_matrix() @ Mf0
                    Mh0 = Mf @ rot3(rel_h) @ grip
                    if dw is None: return Mf, Mh0, 0.0
                    cur = (Mh0 @ ax_l).normalized()
                    Mh = cur.rotation_difference(dw).to_matrix() @ Mh0
                    if upw is not None:
                        c2 = (Mh @ ax2_l); rr = ang(c2, upw, dw)
                        Mh = Quaternion(dw, rr).to_matrix() @ Mh
                    wq = (Mh0.inverted() @ Mh).to_quaternion()
                    return Mf, Mh, math.degrees(wq.angle)
                def tw_cost(t_, w): return w + 0.1 * abs(t_ - pref) + TWC * abs(t_ - prev_tw) + TWK * max(0.0, abs(t_) - TWMAX)
                def best_tw(F, Mf0, coarse=False):
                    if dw is None: return pref, 0.0
                    bt = None
                    for k in (range(-6, 7) if coarse else range(-18, 19)):
                        t_ = k * (15.0 if coarse else 5.0); w = hand_for(F, Mf0, t_)[2]; s_ = tw_cost(t_, w)
                        if bt is None or s_ < bt[0]: bt = (s_, t_, w)
                    if not coarse:
                        for k in range(-10, 11):
                            t_ = bt[1] + k * 0.5; w = hand_for(F, Mf0, t_)[2]; s_ = tw_cost(t_, w)
                            if s_ < bt[0]: bt = (s_, t_, w)
                    return bt[1], bt[2]
                def evalphi(phi):
                    ed, E, U, F, psi, Mu, Mf0 = arm_at(phi)
                    sc_ = (math.degrees(psi) / 25.0) ** 2 + 6.0 * max(0.0, OUTMIN - ed.dot(outw))
                    if pole is not None: sc_ += 6.0 * (1 - ed.dot(pole))
                    if prev_phi is not None: sc_ += CONT * (math.degrees(ed.angle(prev_phi)) / 5.0) ** 2
                    if dw is not None:
                        sc_ += WFIT * (best_tw(F, Mf0, True)[1] / 20.0) ** 2
                    return sc_
                best = None
                if fixed is not None:
                    v_ = rot3(X) @ fixed[0]; v_ = v_ - n * v_.dot(n)
                    best = (0.0, math.atan2(v_.dot(e2), v_.dot(e1)))
                for k in (range(72 if dw is None else 36) if fixed is None else ()):
                    ph = math.radians(k * (5 if dw is None else 10)); v = evalphi(ph)
                    if best is None or v < best[0]: best = (v, ph)
                for k in (range(-10, 11) if fixed is None else ()):
                    ph = best[1] + math.radians(k * (0.5 if dw is None else 1.0)); v = evalphi(ph)
                    if v < best[0]: best = (v, ph)
                phi = best[1]
                ed, E, U, F, psi, Mu, Mf0 = arm_at(phi)
                prev_phi = ed   # elbow direction (continuity in space, not in the circle parameter)
                Mu4 = Mu.to_4x4(); Mu4.translation = S
                tw = best_tw(F, Mf0)[0] if fixed is None else fixed[1]
                prev_tw = tw
                Mf, Mh, wdeg = hand_for(F, Mf0, tw)
                Mf4 = Mf.to_4x4(); Mf4.translation = E
                Mh4 = Mh.to_4x4(); Mh4.translation = Mf4 @ rel_h.translation
                adir = (rot3(X).inverted() @ (Mh @ ax_l)).normalized() if ax_l is not None else None
                return dict(adir=adir, ed_c=rot3(X).inverted() @ ed, tw=tw, Mc=Mc, Mu4=Mu4, Mf4=Mf4, Mh4=Mh4, psi=psi, wdeg=wdeg, U=U, F=F, H=H, S=S, n=n, dl=dl)
        frames = list(range(f0, f1 + 1))
        sol = [solve(f) for f in frames]
        # smooth the solved elbow direction and twist in time (the optimum can wander along a flat valley)
        loop = clip in getattr(C, 'LOOPS', ('Combat', 'Idle'))
        sig = getattr(C, 'SMOOTH', 1.5); K = [math.exp(-0.5 * (j / sig) ** 2) for j in range(-4, 5)]
        nF = len(frames); sm = []
        for k in range(nF):
            acc = Vector(); tacc = 0.0; ws = 0.0
            for j, wk in zip(range(-4, 5), K):
                kk = (k + j) % (nF - 1) if loop else min(max(k + j, 0), nF - 1)
                acc += sol[kk]['ed_c'] * wk; tacc += sol[kk]['tw'] * wk; ws += wk
            sm.append((acc.normalized(), tacc / ws))
        # optional window: re-author only frames fa..fb of this clip/side, easing from/to the shipped motion over `ramp`
        win = getattr(C, 'WINDOW', {}).get(clip, {}).get(side)
        bones_ = [ua, fa, ha] + [b for b in ('upperarm_half.' + side, 'forearm_half.' + side, tb) if b and b in P]
        orig = {}
        if win:
            for f in frames:
                sc.frame_set(f); orig[f] = {b: P[b].rotation_quaternion.copy() for b in bones_}
        def wgt(f):
            # WINDOW value: (fa, fb, ramp) or a list of them
            if not win: return 1.0
            best = 0.0
            for a_, b_, rp in (win if isinstance(win, list) else [win]):
                if a_ <= f <= b_: w = 1.0
                elif f < a_ - rp or f > b_ + rp: w = 0.0
                else:
                    t = (f - (a_ - rp)) / rp if f < a_ else ((b_ + rp) - f) / rp
                    w = t * t * (3 - 2 * t)
                best = max(best, w)
            return best
        prevq = {}; rows = []
        for f, fx in zip(frames, sm):
            g_ = solve(f, fx)
            adir = g_['adir']
            Mc, Mu4, Mf4, Mh4, psi, wdeg, U, F, H, S, n, dl, tw = [g_[k] for k in ('Mc', 'Mu4', 'Mf4', 'Mh4', 'psi', 'wdeg', 'U', 'F', 'H', 'S', 'n', 'dl', 'tw')]
            qu = basis_from(ua, Mc, Mu4).to_quaternion()
            qf = basis_from(fa, Mu4, Mf4).to_quaternion()
            qh = basis_from(ha, Mf4, Mh4).to_quaternion()
            vals = {ua: qu, fa: qf, ha: qh}
            if ('upperarm_half.' + side) in P: vals['upperarm_half.' + side] = Quaternion().slerp(qu, 0.5)
            if ('forearm_half.' + side) in P: vals['forearm_half.' + side] = Quaternion().slerp(qf, 0.5)
            if tb:
                fax = (rot3(RB[ha]).inverted() @ rot3(RB[fa]).col[1]).normalized()
                th = 2 * math.atan2(Vector((qh.x, qh.y, qh.z)).dot(fax), qh.w)
                th = math.atan2(math.sin(th), math.cos(th))
                vals[tb] = Quaternion((0, 1, 0), th * TWS)
            w_ = wgt(f)
            for bn, q in vals.items():
                if w_ < 1.0:
                    qo = orig[f][bn]; q = q.normalized()
                    if qo.dot(q) < 0: q = -q
                    q = qo.slerp(q, w_)
                q = unit_q(q.normalized(), prevq.get(bn)); prevq[bn] = q
                P[bn].rotation_quaternion = q
                P[bn].keyframe_insert('rotation_quaternion', frame=f)
            elbow = math.degrees(U.angle(F))
            rows.append(dict(f=f, adir=[round(x, 2) for x in adir] if adir is not None else None, w=round(w_, 2), psi=round(math.degrees(psi), 1), tw=round(tw, 1), wrist=round(wdeg, 1), elbow=round(elbow, 1),
                             reach=round((H - (S + n * dl)).length, 3)))
        for k in range(len(rows)):
            for q in ('psi', 'tw', 'wrist', 'elbow'):
                rows[k]['d' + q] = round(rows[k][q] - rows[k - 1][q], 1) if k else 0.0
        rep[side] = rows
        rows = [r for r in rows if r['w'] > 0]   # (outside a window the shipped motion is kept)
        def mm(q): return min(r[q] for r in rows), max(r[q] for r in rows)
        print('%s %s psi %.0f..%.0f tw %.0f..%.0f wrist %.0f..%.0f elbow %.0f..%.0f | max |d| psi %.0f tw %.0f wrist %.0f elbow %.0f' % (
            clip, side, *mm('psi'), *mm('tw'), *mm('wrist'), *mm('elbow'),
            *[max(abs(r['d' + q]) for r in rows) for q in ('psi', 'tw', 'wrist', 'elbow')]), flush=True)
    if getattr(C, 'POST', None):
        for f in range(f0, f1 + 1):
            sc.frame_set(f); C.POST(CTX, clip, f)

if REPORT: json.dump(report, open(REPORT, 'w'))
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                          export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                          export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
print('wrote', OUT)
