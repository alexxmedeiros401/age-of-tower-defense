"""Play a unit GLB the way the game does and render it (review / before-after tool).

  python3 rs_fight.py -- UNIT.glb OUTDIR [--cd 0.85] [--shots 4] [--first 1.2] [--tail 1.6] [--fps 30] [--slow 1]
                         [--az 315] [--elev 25] [--size 3.4] [--ctr x,y,z] [--rx 540 --ry 640] [--nobase] [--rock] [--t0 a --t1 b]

It follows game.gd: every shot restarts the attack clip (Throw / Attack) with a 0.05 s cross-fade, sped up to fit the
cooldown (clamp(length / cooldown, 1, 3)); when the attack ends the combat loop (Whirl / Combat) fades in over 0.25 s
and holds for max(2.2, 1.25 cd + 0.3) s after the last shot; then Idle fades in over 0.25 s. Cross-fades follow Godot's
AnimationMixer (the outgoing clip keeps playing while it fades; rotations blend as rest * slerp(1, a, wa) * slerp(1, b, wb)).
--rock draws the game's own projectile: it appears at the unit's middle, 1.3 world units up, the moment the sim fires.
--slow N plays everything N times slower (more rendered frames), for a slow-motion pass.
"""
import sys, os, math, argparse, json
import bpy, mathutils
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('out')
ap.add_argument('--cd', type=float, default=0.85); ap.add_argument('--shots', type=int, default=4)
ap.add_argument('--first', type=float, default=1.2); ap.add_argument('--tail', type=float, default=1.6)
ap.add_argument('--fps', type=float, default=30.0); ap.add_argument('--slow', type=float, default=1.0)
ap.add_argument('--az', type=float, default=315.0); ap.add_argument('--elev', type=float, default=25.0)
ap.add_argument('--size', type=float, default=3.4); ap.add_argument('--ctr', default='0,0.06,1.9')
ap.add_argument('--rx', type=int, default=540); ap.add_argument('--ry', type=int, default=640)
ap.add_argument('--nobase', action='store_true'); ap.add_argument('--rock', action='store_true')
ap.add_argument('--t0', type=float, default=None); ap.add_argument('--t1', type=float, default=None)
ap.add_argument('--model_scale', type=float, default=0.64); ap.add_argument('--dry', action='store_true')
ap.add_argument('--idle0', type=float, default=1.9)
ap.add_argument('--aa', default='8'); ap.add_argument('--noshadow', action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
if arm.animation_data: arm.animation_data.action = None
if arm.animation_data:
    for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
FPS_CLIP = 24.0
names = [pb.name for pb in arm.pose.bones]


def load_action(act):
    """-> length (s), sampler(t) -> {bone: (loc(3), quat(4 wxyz), scale(3))}"""
    try:
        fcs = [fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    except Exception:
        fcs = list(act.fcurves)
    ch = {}
    for fc in fcs:
        if 'pose.bones' not in fc.data_path: continue
        bone = fc.data_path.split('"')[1]; kind = fc.data_path.rsplit('.', 1)[1]
        ch.setdefault(bone, {}).setdefault(kind, {})[fc.array_index] = fc
    f0, f1 = act.frame_range
    n = int(round(f1 - f0))
    # sample every clip frame once (the GLB holds one key per frame), then interpolate like the engine does
    S = {}
    for bone in names:
        c = ch.get(bone, {})
        L = np.zeros((n + 1, 3)); Q = np.zeros((n + 1, 4)); Q[:, 0] = 1; Sc = np.ones((n + 1, 3))
        for k in range(n + 1):
            fr = f0 + k
            for i in range(3):
                if 'location' in c and i in c['location']: L[k, i] = c['location'][i].evaluate(fr)
                if 'scale' in c and i in c['scale']: Sc[k, i] = c['scale'][i].evaluate(fr)
            for i in range(4):
                if 'rotation_quaternion' in c and i in c['rotation_quaternion']: Q[k, i] = c['rotation_quaternion'][i].evaluate(fr)
        Q /= np.linalg.norm(Q, axis=1, keepdims=True)
        for k in range(1, n + 1):
            if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
        S[bone] = (L, Q, Sc)
    return n / FPS_CLIP, S


ACT = {act.name: load_action(act) for act in bpy.data.actions}
print('clips', {k: round(v[0], 3) for k, v in ACT.items()})
COMBAT = 'Combat' if 'Combat' in ACT else 'Whirl'
ATTACK = 'Attack' if 'Attack' in ACT else 'Throw'
LOOPS = ('Idle', 'Whirl', 'Combat')


def sample(name, t):
    length, S = ACT[name]
    n = int(round(length * FPS_CLIP))
    if name in LOOPS: t = t % length
    t = min(max(t, 0.0), length)
    x = t * FPS_CLIP; k = min(int(math.floor(x)), n - 1); s = x - k
    out = {}
    for bone, (L, Q, Sc) in S.items():
        q = Q[k] * (1 - s) + Q[k + 1] * s
        out[bone] = (L[k] * (1 - s) + L[k + 1] * s, q / np.linalg.norm(q), Sc[k] * (1 - s) + Sc[k + 1] * s)
    return out


def qslerp_id(q, w):
    """slerp(identity, q, w), q = (w, x, y, z)."""
    if q[0] < 0: q = -q
    ang = 2 * math.acos(min(1.0, q[0]))
    if ang < 1e-8: return np.array([1.0, 0, 0, 0])
    ax = q[1:] / math.sin(ang / 2)
    h = ang * w / 2
    return np.concatenate([[math.cos(h)], ax * math.sin(h)])


def qmul(p, q):
    return np.array([p[0] * q[0] - p[1:] @ q[1:], *(p[0] * q[1:] + q[0] * p[1:] + np.cross(p[1:], q[1:]))])


class Player:
    """Godot's AnimationPlayer, as game.gd drives it."""

    def __init__(self):
        self.cur = None; self.pos = 0.0; self.playing = False
        self.blends = []          # [name, pos, blend_left, blend_time]
        self.speed = 1.0

    def play(self, name, blend, seek=None):
        if self.cur is not None and blend > 0:
            self.blends.append([self.cur, self.pos, 1.0, blend])
        self.cur = name; self.playing = True
        self.pos = 0.0 if seek is None else seek

    def advance(self, dt):
        d = dt * self.speed
        if self.playing:
            self.pos += d
            if self.cur not in LOOPS and self.pos >= ACT[self.cur][0]:
                self.pos = ACT[self.cur][0]; self.playing = False
                self.blends = []                                    # (end reached: Godot drops the running blends)
        keep = []
        for b in self.blends:
            b[2] = max(0.0, b[2] - abs(d) / b[3])
            b[1] += d
            if b[2] > 0: keep.append(b)
        self.blends = keep

    def pose(self):
        wsum = sum(b[2] for b in self.blends)
        parts = [(self.cur, self.pos, max(0.0, 1.0 - wsum))] + [(b[0], b[1], b[2]) for b in self.blends]
        acc = {bn: (np.zeros(3), np.array([1.0, 0, 0, 0]), np.zeros(3)) for bn in names}
        for nme, pos, w in parts:
            if w <= 0: continue
            smp = sample(nme, pos)
            for bn in names:
                L, Q, S = smp[bn]; aL, aQ, aS = acc[bn]
                acc[bn] = (aL + L * w, qmul(aQ, qslerp_id(Q, w)), aS + (S - 1.0) * w)
        return {bn: (v[0], v[1] / np.linalg.norm(v[1]), v[2] + 1.0) for bn, v in acc.items()}


# ---- the fight
fires = [a.first + i * a.cd for i in range(a.shots)]
hold = max(2.2, a.cd * 1.25 + 0.3)
rate = min(max(ACT[ATTACK][0] / max(a.cd, 0.1), 1.0), 3.0)
end = fires[-1] + hold + a.tail if a.shots else a.first + a.tail
T0 = 0.0 if a.t0 is None else a.t0; T1 = end if a.t1 is None else a.t1
TICK = 1.0 / 60.0
pl = Player(); pl.play('Idle', 0.0, seek=a.idle0)
last_fire = -100.0

# ---- render setup (workbench, as the other review tools)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
sh.show_shadows = not a.noshadow; sh.shadow_intensity = 0.35
sc.display.render_aa = a.aa
sc.render.resolution_x = a.rx; sc.render.resolution_y = a.ry
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.47, 0.56, 0.42)
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 300; cam.data.ortho_scale = a.size
ctr = mathutils.Vector([float(x) for x in a.ctr.split(',')])
az = math.radians(a.az); el = math.radians(a.elev)
cam.location = ctr + mathutils.Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * 40.0
cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
try:
    sc.display.light_direction = (0.35, 0.45, 0.82)
except Exception:
    pass
if a.nobase:
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.find_armature() is None: o.hide_render = True
rock = None
if a.rock:
    me = bpy.data.meshes.new('rock')
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.11 / a.model_scale); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    m = bpy.data.materials.new('rock'); m.diffuse_color = (0.6, 0.58, 0.55, 1); me.materials.append(m)
    rock = bpy.data.objects.new('GameRock', me); sc.collection.objects.link(rock)
    rock.scale = (1.0, 0.9, 0.85)
os.makedirs(a.out, exist_ok=True)
log = []
t = 0.0; nf = 0; next_frame_t = T0; fi = 0
dt_out = 1.0 / a.fps / a.slow          # game time per rendered frame
while t <= T1 + 1e-9:
    # game tick: events, then the clip logic of _hq_anim_tick
    while fi < len(fires) and fires[fi] <= t + 1e-9:
        last_fire = fires[fi]; fi += 1
        pl.play(ATTACK, 0.05, seek=0.0); pl.speed = rate
    cur = pl.cur
    pl.speed = rate if cur == ATTACK else 1.0
    if not (cur == ATTACK and pl.playing):
        want = COMBAT if (t - last_fire) < hold else 'Idle'
        if cur != want:
            pl.play(want, 0.25); pl.speed = 1.0
    if t + 1e-9 >= next_frame_t:
        pose = pl.pose()
        for bn in names:
            pb = arm.pose.bones[bn]; L, Q, S = pose[bn]
            pb.rotation_mode = 'QUATERNION'
            pb.location = L; pb.rotation_quaternion = Q; pb.scale = S
        if rock is not None:
            age = t - last_fire
            rock.hide_render = not (0.0 <= age < 0.6)
            if not rock.hide_render:
                # game.gd: spawned at the tower, 1.3 up; follows the sim's shot (proj_speed 16) at 1.1 up, eased 60% a frame
                k = 1.0 - 0.4 ** max(age * 60.0, 0.0)
                rock.location = (0.0, -16.0 * age / a.model_scale * 1.0, (1.3 + (1.1 - 1.3) * k) / a.model_scale)
        bpy.context.view_layer.update()
        state = pl.cur + ('' if not pl.blends else ' <- ' + '+'.join('%s %.0f%%' % (b[0], b[2] * 100) for b in pl.blends))
        log.append(dict(frame=nf, t=round(t, 4), clip=pl.cur, pos=round(pl.pos, 4), blends=[[b[0], round(b[2], 3)] for b in pl.blends], fire_age=round(t - last_fire, 4)))
        if not a.dry:
            sc.render.filepath = os.path.join(a.out, 'f_%05d.png' % nf)
            bpy.ops.render.render(write_still=True)
        nf += 1; next_frame_t += dt_out
    pl.advance(TICK / max(a.slow, 1.0) if a.slow > 1 else TICK)
    t += TICK / max(a.slow, 1.0) if a.slow > 1 else TICK
json.dump(dict(fires=fires, hold=hold, rate=rate, frames=log, fps=a.fps, slow=a.slow), open(os.path.join(a.out, 'log.json'), 'w'))
print('rendered %d frames; fires %s; attack rate %.3f; hold %.2f' % (nf, [round(x, 2) for x in fires], rate, hold))
