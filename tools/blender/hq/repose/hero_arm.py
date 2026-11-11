# Re-author the arm motion of chosen clips on a shipped hero / tower GLB (everything else keeps its keys).
# usage: python3 hero_arm.py IN.glb OUT.glb CFG.py [REPORT.json]
#
# CFG.CLIPS = {clip: {'R': keys, 'L': keys, 'hand_R': hand, 'hand_L': hand, 'psi_max': 30}}
#   keys : [(frame, wrist, pole), ...] (Catmull-Rom between keys) or a function f -> (wrist, pole).
#          wrist = where the hand bone's head goes, pole = where the elbow points; both chest-relative, written in the
#          armature's REST coordinates (the chest's motion in the clip carries them), so they are read off the rest pose.
#   hand : 'keep'   the clip's own wrist rotation (relative to the forearm), the default
#          'straight' no wrist rotation
#          [(frame, dir, up), ...] aim: the held thing's axis CFG.AXIS_<side> (armature rest space) points along dir,
#          its CFG.UP_<side> toward up (None: least rotation); chest-relative like the keys; slerped between keys.
#          Or a function f -> (dir, up).
# Solved analytically per frame: elbow on the shoulder-wrist circle toward the pole; the upper arm swung from its
# carried rest frame and rolled (psi) only as far as needed to put the elbow's hinge in the bend plane, within
# +-psi_max (big rolls twist the skin); the forearm swung, its twist (if the rig has no forearm_twist bone) taking
# the hand's turn about the forearm up to CFG.TW_MAX (default 70), the wrist the rest. *_half bones get their share of
# the turn, forearm_twist bones their share of the hand's twist (the herotripo cfg values), as in the rig pass.
# Parentless prop bones (posed in armature space each frame) that the re-authored hand held keep their grip.
# CFG.SLING = True: the 'sling' bone (child of hand.R) hangs and trails the hand (Rock Slinger / Ugo).
import bpy, sys, math, json, os, importlib.util
from mathutils import Vector, Matrix, Quaternion

IN, OUT, CFGPY = sys.argv[1:4]
REPORT = sys.argv[4] if len(sys.argv) > 4 else OUT + '.numbers.json'
sp = importlib.util.spec_from_file_location('cfg', CFGPY); C = importlib.util.module_from_spec(sp); sp.loader.exec_module(C)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
P = arm.pose.bones; B = arm.data.bones
AW = arm.matrix_world.copy(); AWi = AW.inverted()
chest_rest = B['chest'].matrix_local.copy()
HERO = getattr(C, 'HERO', None)
hcfg = {}
if HERO:
    pth = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'herotripo_cfg', HERO + '.json')
    if os.path.exists(pth): hcfg = json.load(open(pth))
TW_SHARE = float(hcfg.get('twist_share', 0.5))
HALF_SHARE = {jh['bone']: float(jh.get('share', 0.5)) for jh in hcfg.get('joint_helpers', [])}
TW_MAX = getattr(C, 'TW_MAX', 70)
WRIST_SOFT = getattr(C, 'WRIST_SOFT', 55)
PROPS = [b.name for b in B if b.parent is None and b.name != 'root']
print('twist share', TW_SHARE, 'half shares', HALF_SHARE, 'props', PROPS)

def r3(m): return m.to_3x3().normalized()

def cr_interp(keys, f, idx):
    fs = [k[0] for k in keys]
    if f <= fs[0]: return keys[0][idx].copy()
    if f >= fs[-1]: return keys[-1][idx].copy()
    i = max(j for j in range(len(fs)) if fs[j] <= f)
    t = (f - fs[i]) / (fs[i + 1] - fs[i])
    p0 = keys[max(i - 1, 0)][idx]; p1 = keys[i][idx]; p2 = keys[i + 1][idx]; p3 = keys[min(i + 2, len(keys) - 1)][idx]
    if getattr(C, 'LOOP_CR', False) and False: pass
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)

def slerp_dir(a, b, t):
    a = a.normalized(); b = b.normalized()
    return (Quaternion().slerp(a.rotation_difference(b), t) @ a).normalized()

def aim_interp(keys, f):
    fs = [k[0] for k in keys]
    if f <= fs[0]: return keys[0][1].normalized(), keys[0][2]
    if f >= fs[-1]: return keys[-1][1].normalized(), keys[-1][2]
    i = max(j for j in range(len(fs)) if fs[j] <= f)
    t = (f - fs[i]) / (fs[i + 1] - fs[i]); t = t * t * (3 - 2 * t)
    up = None
    if keys[i][2] is not None and keys[i + 1][2] is not None: up = slerp_dir(keys[i][2], keys[i + 1][2], t)
    return slerp_dir(keys[i][1], keys[i + 1][1], t), up

def get_keys(spec, f):
    if callable(spec): return spec(f)
    return cr_interp(spec, f, 1), cr_interp(spec, f, 2)

def get_aim(spec, f):
    if callable(spec): return spec(f)
    return aim_interp(spec, f)

def chest_xf():
    return AW @ P['chest'].matrix @ chest_rest.inverted()       # rest armature coords -> world, carried by the chest

def frame_map(a0, a1, b0, b1):
    """rotation taking a0 -> a1 exactly and b0 toward b1"""
    q = a0.rotation_difference(a1)
    b0r = q @ b0
    pa = (b0r - a1 * b0r.dot(a1)); pb = (b1 - a1 * b1.dot(a1))
    if pa.length < 1e-6 or pb.length < 1e-6: return q
    ang = pa.normalized().angle(pb.normalized())
    if a1.dot(pa.cross(pb)) < 0: ang = -ang
    return Quaternion(a1, ang) @ q

def wrapd(a): return (a + 180) % 360 - 180

TW_RATE = getattr(C, 'TW_RATE', 10)

def smooth_tw(TWW, frames, loop):
    out = {}
    for s, w in TWW.items():
        v = [w[f] for f in frames]
        for i in range(1, len(v)):           # unwrap
            while v[i] - v[i - 1] > 180: v[i] -= 360
            while v[i] - v[i - 1] < -180: v[i] += 360
        n = len(v); k = [math.exp(-0.5 * (j / 2.0) ** 2) for j in range(-6, 7)]
        sm = []
        for i in range(n):
            acc = ws = 0
            for j, kk in zip(range(-6, 7), k):
                ii = (i + j) % (n - 1) if loop else min(max(i + j, 0), n - 1)
                acc += kk * v[ii]; ws += kk
            sm.append(acc / ws)
        if not loop: sm[0], sm[-1] = v[0], v[-1]     # the ends meet other clips: keep their own solution
        for i in range(1, n): sm[i] = max(sm[i - 1] - TW_RATE, min(sm[i - 1] + TW_RATE, sm[i]))
        for i in range(n - 2, -1, -1): sm[i] = max(sm[i + 1] - TW_RATE, min(sm[i + 1] + TW_RATE, sm[i]))
        out[s] = {f: sm[i] for i, f in enumerate(frames)}
    return out

PSI_RATE = math.radians(getattr(C, 'PSI_RATE', 6))     # max upper-arm roll change per frame

def smooth_psi(WANT, frames, psi_max, loop, PIN):
    out = {}
    for s, w in WANT.items():
        pin = PIN.get(s, {})
        v = [pin[f] if f in pin else max(-psi_max, min(psi_max, w[f])) for f in frames]
        n = len(v)
        # gaussian smoothing (sigma 2 frames)
        k = [math.exp(-0.5 * (j / 2.0) ** 2) for j in range(-6, 7)]
        sm = []
        for i in range(n):
            acc = 0; ws = 0
            for j, kk in zip(range(-6, 7), k):
                ii = (i + j) % (n - 1) if loop else min(max(i + j, 0), n - 1)
                acc += kk * v[ii]; ws += kk
            sm.append(acc / ws)
        sm = [pin[f] if f in pin else x for f, x in zip(frames, sm)]
        # rate limit, forward then backward (no step bigger than PSI_RATE)
        for i in range(1, n): sm[i] = max(sm[i - 1] - PSI_RATE, min(sm[i - 1] + PSI_RATE, sm[i]))
        for i in range(n - 2, -1, -1): sm[i] = max(sm[i + 1] - PSI_RATE, min(sm[i + 1] + PSI_RATE, sm[i]))
        out[s] = {f: sm[i] for i, f in enumerate(frames)}
    return out

# rest data
REL = {}
for s in 'RL':
    U, F, H, Cl = B['upperarm.' + s], B['forearm.' + s], B['hand.' + s], B['clavicle.' + s]
    REL[s] = dict(
        Lu=(F.head_local - U.head_local).length, Lf=(H.head_local - F.head_local).length,
        rel_u=r3(Cl.matrix_local).inverted() @ r3(U.matrix_local),
        rel_f=r3(U.matrix_local).inverted() @ r3(F.matrix_local),
        rel_h=r3(F.matrix_local).inverted() @ r3(H.matrix_local),
        dU=(r3(U.matrix_local).inverted() @ (F.head_local - U.head_local)).normalized(),
        dF=(r3(F.matrix_local).inverted() @ (H.head_local - F.head_local)).normalized(),
        axis_f_in_h=(r3(H.matrix_local).inverted() @ (H.head_local - F.head_local)).normalized(),
        twist=('forearm_twist.' + s) in B,
    )

numbers = {}
for clip, spec in C.CLIPS.items():
    act = bpy.data.actions[clip]
    arm.animation_data_create(); arm.animation_data.action = act
    f0, f1 = [int(round(x)) for x in act.frame_range]
    frames = list(range(f0, f1 + 1))
    sides = [s for s in 'RL' if s in spec]
    psi_max = math.radians(spec.get('psi_max', getattr(C, 'PSI_MAX', 30)))
    # the original: hand local rotations, hand and prop world matrices
    orig = {}
    for f in frames:
        sc.frame_set(f)
        orig[f] = {'hand_local': {s: P['hand.' + s].rotation_quaternion.copy() for s in 'RL'},
                   'hand_w': {s: (AW @ P['hand.' + s].matrix).copy() for s in 'RL'},
                   'props': {p: (AW @ P[p].matrix).copy() for p in PROPS},
                   'local': {b.name: b.rotation_quaternion.copy() for b in P},
                   'upper': {s_: r3(AW @ P['upperarm.' + s_].matrix) for s_ in 'RL'},
                   'elbow': {s_: (AW @ P['forearm.' + s_].matrix).translation.copy() for s_ in 'RL'},
                   'shoulder': {s_: (AW @ P['upperarm.' + s_].matrix).translation.copy() for s_ in 'RL'},
                   'world': {b: (AW @ P[b].matrix).copy() for b in spec.get('keep_world', [])},
                   'tails': {b: (AW @ P[b].tail).copy() for b in spec.get('follow_tail', {})}}
    WANT = {s: {} for s in sides}; PSI = None; PIN = {}; TWS = None; TWW = {}
    HW = {}
    for s in sides:
        sg = spec.get('hand_smooth_' + s, spec.get('hand_smooth', 0))
        if not sg: continue
        qs = [orig[f]['hand_w'][s].to_quaternion() for f in frames]
        for i in range(1, len(qs)):
            if qs[i].dot(qs[i - 1]) < 0: qs[i].negate()
        rad = int(3 * sg) + 1; n_ = len(qs); out_ = {}
        for i, f in enumerate(frames):
            acc = Vector((0, 0, 0, 0)); ws = 0
            for j in range(-rad, rad + 1):
                ii = (i + j) % (n_ - 1) if spec.get('loop') else min(max(i + j, 0), n_ - 1)
                if not spec.get('loop') and i in (0, n_ - 1): ii = i
                k = math.exp(-0.5 * (j / sg) ** 2); q = qs[ii]
                if q.dot(qs[i]) < 0: q = -q
                acc += Vector(q[:]) * k; ws += k
            out_[f] = Quaternion(acc / ws).normalized().to_matrix()
        HW[s] = out_
    for pass_ in (0, 1):
        rows = []
        prev = {s: dict(psi=0.0, tw=None, q={}) for s in sides}
        newhand = {}
        for f in frames:
            sc.frame_set(f)
            X = chest_xf()
            row = {'f': f}
            for s in sides:
                R = REL[s]
                wr, pole = get_keys(spec[s], f)
                Hw = X @ wr; Pw = X @ pole
                Sw = (AW @ P['upperarm.' + s].matrix).translation
                d_vec = Hw - Sw; d = d_vec.length
                lo_, hi_ = abs(R['Lu'] - R['Lf']) + 1e-3, (R['Lu'] + R['Lf']) * 0.995
                reach = 0.0
                if d > hi_: reach = d - hi_; d = hi_
                if d < lo_: reach = lo_ - d; d = lo_
                n = d_vec.normalized()
                a = (R['Lu'] ** 2 - R['Lf'] ** 2 + d * d) / (2 * d); rr = math.sqrt(max(R['Lu'] ** 2 - a * a, 0))
                pv = (Pw - Sw); pv = pv - n * pv.dot(n)
                if pv.length < 1e-6: pv = n.orthogonal()
                E = Sw + n * a + pv.normalized() * rr
                Hreal = Sw + n * d
                u = (E - Sw).normalized(); fd = (Hreal - E).normalized()
                # upper arm: carried rest frame, swung, rolled
                AWr = r3(AW)
                Rc = AWr @ r3(P['clavicle.' + s].matrix)
                Ru0 = Rc @ R['rel_u']
                Rsw = (Ru0 @ R['dU']).rotation_difference(u).to_matrix() @ Ru0
                nb = u.cross(fd)
                if nb.length > math.sin(math.radians(12)):
                    nb.normalize()
                    x0 = Rsw.col[0]
                    ang = math.atan2(u.dot(x0.cross(nb)), x0.dot(nb))
                    # the hinge may also face the other way only if it is a reversed bone roll (rare): keep the nearer
                    want = ang
                else:
                    want = prev[s]['psi'] * 0.8
                # continuity: stay near the last roll
                while want - prev[s]['psi'] > math.pi: want -= 2 * math.pi
                while want - prev[s]['psi'] < -math.pi: want += 2 * math.pi
                WANT[s][f] = want
                bi_, bo_ = spec.get('blend_' + s, spec.get('blend', (0, 0)))
                if (bi_ and f - f0 < bi_) or (bo_ and f1 - f < bo_):
                    uo = (orig[f]['elbow'][s] - orig[f]['shoulder'][s]).normalized()
                    Rso = (Ru0 @ R['dU']).rotation_difference(uo).to_matrix() @ Ru0
                    xo = Rso.col[0]; xu = orig[f]['upper'][s].col[0]
                    PIN.setdefault(s, {})[f] = math.atan2(uo.dot(xo.cross(xu)), xo.dot(xu))
                psi = PSI[s][f] if PSI else max(-psi_max, min(psi_max, want))
                Ru = Matrix.Rotation(psi, 3, u) @ Rsw
                # forearm swung (no twist yet)
                Rf0 = Ru @ R['rel_f']
                Rfs = (Rf0 @ R['dF']).rotation_difference(fd).to_matrix() @ Rf0
                # hand
                hs = spec.get('hand_' + s, 'keep')
                if hs == 'keep':
                    Rh_target = Rfs @ R['rel_h'] @ orig[f]['hand_local'][s].to_matrix()
                elif hs == 'world':
                    # the hand (and what it holds) keeps its shipped orientation: only where it is changes
                    # (optionally smoothed over time: 'hand_smooth' sigma in frames, for shipped clips that flip the fist)
                    Rh_target = HW[s][f] if s in HW else r3(orig[f]['hand_w'][s])
                    af = spec.get('aim_fix_' + s)
                    if af:      # swing the held thing's axis onto a bone's point (an arrow onto the bow grip), weight w(f)
                        w_ = af['w'](f) if callable(af.get('w')) else af.get('w', 1.0)
                        if w_ == 'auto':    # only while the shipped clip had it on target (the grip within 6 cm of its line)
                            oh = orig[f]['hand_w'][s]; ax0 = (oh.to_3x3().normalized() @ (r3(B['hand.' + s].matrix_local).inverted() @ Vector(af['axis']))).normalized()
                            gp = orig[f]['hand_w'][af['at'].split('.')[-1]] if af['at'].startswith('hand.') else None
                            gp = (gp @ Vector(af.get('offset', (0, 0, 0)))) if gp is not None else tgt0
                            rel_ = gp - oh.translation; dl_ = (rel_ - ax0 * rel_.dot(ax0)).length if rel_.dot(ax0) > 0 else 9
                            w_ = max(0.0, min(1.0, (0.12 - dl_) / 0.06))
                        if w_ > 0:
                            tgt = (AW @ P[af['at']].matrix) @ Vector(af.get('offset', (0, 0, 0)))
                            axw = (Rh_target @ (r3(B['hand.' + s].matrix_local).inverted() @ Vector(af['axis']))).normalized()
                            want_ = (tgt - Hreal).normalized()
                            Rh_target = Quaternion().slerp(axw.rotation_difference(want_), w_).to_matrix() @ Rh_target
                    wr_ = spec.get('world_rot_' + s, spec.get('world_rot'))
                    if wr_:     # an extra turn of the held thing about a chest-relative axis (deg), e.g. a hammer head swung out
                        ax_, deg_ = wr_(f) if callable(wr_) else wr_
                        Rh_target = Matrix.Rotation(math.radians(deg_), 3, (r3(X) @ Vector(ax_)).normalized()) @ Rh_target
                elif hs == 'straight':
                    # straight wrist; the hand (and what it holds) turned about the forearm by the keyed twist (deg)
                    tk = spec.get('twist_' + s)
                    tdeg = 0.0
                    if tk: tdeg = tk(f) if callable(tk) else float(cr_interp([(k[0], Vector((k[1], 0, 0)), Vector()) for k in tk], f, 1).x)
                    Rh_target = Matrix.Rotation(math.radians(tdeg), 3, fd) @ Rfs @ R['rel_h']
                else:
                    dirc, upc = get_aim(hs, f)
                    dw = (r3(X) @ dirc).normalized()
                    Rh0 = Rfs @ R['rel_h']
                    ax_l = (r3(B['hand.' + s].matrix_local).inverted() @ getattr(C, 'AXIS_' + s)).normalized()
                    if upc is not None:
                        up_l = (r3(B['hand.' + s].matrix_local).inverted() @ getattr(C, 'UP_' + s)).normalized()
                        q = frame_map(Rh0 @ ax_l, dw, Rh0 @ up_l, (r3(X) @ upc).normalized())
                    else:
                        # least rotation, but let the forearm twist take what lowers the wrist
                        # the held thing's roll about its own axis is free: pick the hand turn (twist about the forearm
                        # + least swing) that keeps the wrist and the twist small and close to the last frame's
                        best = None
                        Rh0i = Rh0.inverted()
                        for k in range(-150, 151, 3):
                            qt = Quaternion(fd, math.radians(k))
                            qq = (qt @ (Rh0 @ ax_l)).rotation_difference(dw) @ qt
                            lq = (Rh0i @ qq.to_matrix() @ Rh0).to_quaternion()
                            sw_, tw_ = lq.to_swing_twist('Y')
                            tw_d = wrapd(math.degrees(tw_)); sw_d = math.degrees(Quaternion(sw_).angle)
                            sw_d = min(sw_d, 360 - sw_d)
                            if TWS:          # pass 2: follow the smoothed twist
                                c = min(sw_d, 90) + 4.0 * abs(wrapd(tw_d - TWS[s][f]))
                            else:
                                wmx_ = spec.get('wrist_max', getattr(C, 'WRIST_MAX', 60))
                                twx_ = 999 if R['twist'] else TW_MAX
                                c = (sw_d + 0.4 * abs(tw_d) + 6 * max(0, sw_d - wmx_) + 6 * max(0, abs(tw_d) - twx_)
                                     + (0.3 * abs(wrapd(tw_d - prev[s]['tw'])) if prev[s]['tw'] is not None else 0))
                            if best is None or c < best[0]: best = (c, qq, tw_d)
                        q = best[1]
                        TWW.setdefault(s, {})[f] = best[2]
                        if TWS:
                            # pass 2: the twist is the smoothed one; the wrist swings (axis across the forearm, up to
                            # the wrist limit) to aim as near the key as it can
                            wmx = spec.get('wrist_max', getattr(C, 'WRIST_MAX', 60))
                            qtw = Quaternion((0, 1, 0), math.radians(TWS[s][f]))
                            dl = (Rh0i @ dw).normalized()
                            bestb = None
                            for ia in range(0, 360, 6):
                                axs = Vector((math.cos(math.radians(ia)), 0, math.sin(math.radians(ia))))
                                for th in range(0, int(wmx) + 1, 3):
                                    lq = Quaternion(axs, math.radians(th)) @ qtw
                                    e = (lq @ ax_l).angle(dl)
                                    if bestb is None or e < bestb[0] - 1e-9 or (abs(e - bestb[0]) < 1e-9 and th < bestb[2]): bestb = (e, lq, th)
                            q = (Rh0 @ bestb[1].to_matrix() @ Rh0i).to_quaternion()
                    Rh_target = q.to_matrix() @ Rh0
                # split the hand's turn (relative to the swung forearm) into twist about the forearm axis + swing
                loc = (Rfs @ R['rel_h']).inverted() @ Rh_target
                ql = loc.to_quaternion()
                sw, tw = ql.to_swing_twist('Y') if abs(R['axis_f_in_h'].y) > 0.95 else (ql, 0.0)
                # never aim with the wrist alone: the wrist's bend stops at WRIST_MAX (the weapon then points a little
                # off its key instead of the hand folding over)
                sw = Quaternion(sw)
                if sw.w < 0: sw.negate()
                sa = math.degrees(sw.angle)
                wmax = spec.get('wrist_max_' + s, spec.get('wrist_max', 180 if hs in ('world', 'keep') else getattr(C, 'WRIST_MAX', 60)))
                if sa > wmax:
                    sw = Quaternion().slerp(sw, wmax / sa)
                    Rh_target = (Rfs @ R['rel_h']) @ (sw @ Quaternion((0, 1, 0), tw)).to_matrix()
                tw = wrapd(math.degrees(tw))
                if prev[s]['tw'] is not None:
                    while tw - prev[s]['tw'] > 180: tw -= 360
                    while tw - prev[s]['tw'] < -180: tw += 360
                if R['twist']:
                    ftw = 0.0
                else:
                    twm = spec.get('tw_max_' + s, spec.get('tw_max', 0 if hs in ('world', 'keep') else TW_MAX))
                    ftw = max(-twm, min(twm, tw))
                Rf = Matrix.Rotation(math.radians(ftw), 3, fd) @ Rfs
                # write: matrices in armature space
                def setm(bn, Rw, pos=None):
                    pb = P[bn]
                    cur = AW @ pb.matrix
                    m = (Rw).to_4x4(); m.translation = cur.translation if pos is None else pos
                    pb.matrix = AWi @ m
                    bpy.context.view_layer.update()
                setm('upperarm.' + s, Ru)
                setm('forearm.' + s, Rf)
                setm('hand.' + s, Rh_target)
                for b in ('upperarm.' + s, 'forearm.' + s, 'hand.' + s):
                    qq = P[b].rotation_quaternion.copy()
                    pq = prev[s]['q'].get(b)
                    if pq is not None and qq.dot(pq) < 0: qq.negate(); P[b].rotation_quaternion = qq
                    prev[s]['q'][b] = qq.copy()
                    P[b].keyframe_insert('rotation_quaternion', frame=f)
                for b, src in (('upperarm_half.' + s, 'upperarm.' + s), ('forearm_half.' + s, 'forearm.' + s)):
                    if b in P:
                        P[b].rotation_quaternion = Quaternion().slerp(P[src].rotation_quaternion, HALF_SHARE.get(src, 0.5))
                        P[b].keyframe_insert('rotation_quaternion', frame=f)
                hq = P['hand.' + s].rotation_quaternion
                hsw, htw = hq.to_swing_twist('Y')
                if R['twist']:
                    h_ = math.radians(wrapd(math.degrees(htw))) * TW_SHARE / 2
                    P['forearm_twist.' + s].rotation_quaternion = (math.cos(h_), 0.0, math.sin(h_), 0.0)
                    P['forearm_twist.' + s].keyframe_insert('rotation_quaternion', frame=f)
                bpy.context.view_layer.update()
                prev[s]['psi'] = psi; prev[s]['tw'] = tw
                fq = P['forearm.' + s].rotation_quaternion
                row[s] = dict(psi=round(math.degrees(psi), 1), psi_want=round(math.degrees(want), 1),
                              fortw=round(wrapd(math.degrees(fq.to_swing_twist('Y')[1])), 1),
                              handtw=round(wrapd(math.degrees(htw)), 1),
                              elbow=round(math.degrees(fq.to_swing_twist('Y')[0].angle), 1),
                              wrist=round(math.degrees(Quaternion(hsw).angle) if R['twist'] else math.degrees(hq.angle), 1),
                              reach=round(reach, 3))
                newhand.setdefault(f, {})[s] = (AW @ P['hand.' + s].matrix).copy()
                if not isinstance(hs, str):
                    axw = (r3(AW @ P['hand.' + s].matrix) @ (r3(B['hand.' + s].matrix_local).inverted() @ getattr(C, 'AXIS_' + s))).normalized()
                    row[s]['aim_err'] = round(math.degrees(axw.angle(dw)), 1)
            # ease in from / out to the original pose at the clip's ends (it meets clips that keep their old arms)
            for s in sides:
                if pass_ and f in (f0, f1):     # seam check: how far the new end pose is from the shipped one
                    seam = max(math.degrees(P[b + s].rotation_quaternion.rotation_difference(orig[f]['local'][b + s]).angle) for b in ('upperarm.', 'forearm.', 'hand.'))
                    row.setdefault('seam', {})[s] = round(min(seam, 360 - seam), 1)
                bi, bo = spec.get('blend_' + s, spec.get('blend', (0, 0)))
                wb = 1.0
                if bi and f - f0 < bi: wb = (f - f0) / bi
                if bo and f1 - f < bo: wb = min(wb, (f1 - f) / bo)
                wb = wb * wb * (3 - 2 * wb)
                if wb < 1.0:
                    for b in [x for x in ('upperarm.', 'forearm.', 'hand.', 'upperarm_half.', 'forearm_half.', 'forearm_twist.') if x + s in P]:
                        pb = P[b + s]; qn = pb.rotation_quaternion.copy(); qo = orig[f]['local'][b + s]
                        if qn.dot(qo) < 0: qo = -qo
                        pb.rotation_quaternion = qo.slerp(qn, wb)
                        pb.keyframe_insert('rotation_quaternion', frame=f)
                    bpy.context.view_layer.update()
                    newhand[f][s] = (AW @ P['hand.' + s].matrix).copy()
                row['blend'] = round(wb, 2)
            for b, s_ in spec.get('follow_tail', {}).items():
                # a bone whose tail met the (old) hand (a bowstring at the nock) is turned and stretched to meet it again
                if s_ not in sides: continue
                ot = orig[f]['tails'][b]
                if (ot - orig[f]['hand_w'][s_].translation).length > spec.get('tail_reach', 0.15): continue
                tgt = newhand[f][s_] @ (orig[f]['hand_w'][s_].inverted() @ ot)
                m = AW @ P[b].matrix; head = m.translation.copy(); cur = AW @ P[b].tail
                q = (cur - head).normalized().rotation_difference((tgt - head).normalized())
                P[b].matrix = AWi @ (Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ m)
                bpy.context.view_layer.update()
                k_ = (tgt - head).length / max((AW @ P[b].tail - head).length, 1e-6)
                sc_ = P[b].scale.copy(); sc_.y *= k_; P[b].scale = sc_
                bpy.context.view_layer.update()
                P[b].keyframe_insert('rotation_quaternion', frame=f); P[b].keyframe_insert('scale', frame=f)
            for b in spec.get('keep_world', []):
                m = AW @ P[b].matrix; wo = orig[f]['world'][b]
                nm = Matrix.Translation(m.translation) @ wo.to_quaternion().to_matrix().to_4x4() @ Matrix.Diagonal(m.to_scale()).to_4x4()
                P[b].matrix = AWi @ nm; bpy.context.view_layer.update()
                P[b].keyframe_insert('rotation_quaternion', frame=f)
            rows.append(row)
            if pass_: print(clip, f, {s: row[s] for s in sides}, 'SEAM %s' % row['seam'] if 'seam' in row else '', flush=True)
        if pass_ == 0:
            PSI = smooth_psi(WANT, frames, psi_max, spec.get("loop", False), PIN)
            if TWW: TWS = smooth_tw(TWW, frames, spec.get("loop", False))
    # props held by a re-authored hand keep their grip
    hold = getattr(C, 'HOLD', 0.3)
    for p in PROPS:
        for f in frames:
            po = orig[f]['props'][p]
            best = None
            for s in sides:
                dd = (po.translation - orig[f]['hand_w'][s].translation).length
                if best is None or dd < best[0]: best = (dd, s)
            if best is None or best[0] > hold + 0.1: continue
            w = max(0.0, min(1.0, (hold + 0.1 - best[0]) / 0.1))
            s = best[1]
            nm = newhand[f][s] @ orig[f]['hand_w'][s].inverted() @ po
            if w < 1:
                loc = po.translation.lerp(nm.translation, w)
                qq = po.to_quaternion().slerp(nm.to_quaternion(), w)
                nm = Matrix.Translation(loc) @ qq.to_matrix().to_4x4() @ Matrix.Diagonal(po.to_scale()).to_4x4()
            sc.frame_set(f)
            P[p].matrix = AWi @ nm
            bpy.context.view_layer.update()
            for path in ('location', 'rotation_quaternion', 'scale'):
                P[p].keyframe_insert(path, frame=f)
    if getattr(C, 'SLING', False) and 'R' in sides:
        hp = [newhand[f]['R'].translation for f in frames]
        nfr = len(frames)
        for k, f in enumerate(frames):
            sc.frame_set(f)
            v = hp[min(k + 1, nfr - 1)] - hp[max(k - 1, 0)]
            dvec = (Vector((0, 0, -1)) - v * 6.0).normalized()
            sl = P['sling']; m = AW @ sl.matrix
            q = m.to_3x3().col[1].normalized().rotation_difference(dvec)
            head = m.translation.copy()
            sl.matrix = AWi @ (Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ m)
            bpy.context.view_layer.update()
            sl.keyframe_insert('rotation_quaternion', frame=f)
    numbers[clip] = rows

json.dump(numbers, open(REPORT, 'w'))
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                          export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                          export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
print('wrote', OUT)
