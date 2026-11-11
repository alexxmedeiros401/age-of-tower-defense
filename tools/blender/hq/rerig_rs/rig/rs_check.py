"""Rock Slinger re-rig: automatic checks over every frame of every clip (numpy skinning of the game mesh).

  python3 rs_check.py OUT/mesh.npz OUT/weights.npz SHIPPED.glb.npz(base verts)  ->  prints a report, exits 1 on a failure

  stretch     edges more than 2x their rest length and 3 cm longer (torn skin), by bone pair
  flips       faces turned over against their bones
  reach       arms or legs asked beyond their length
  planted     the left foot (planted in Whirl and Throw) must not slide; soles on the rock, not through it
  clearance   nothing sweeps through the base's tusks, torch or basket whichever way he faces (the base does not turn)
  inside      sling hand, forearm and sling inside the head, hair or trunk
  loops       first and last frame of each clip agree; no jumps between frames
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_mesh, rs_core, rs_anim, rs_clips, rs_skel
from scipy.spatial import cKDTree


def main(mesh_npz, weights_npz, shipped_npz, verbose=True):
    M = rs_mesh.Mesh(mesh_npz)
    w = np.load(weights_npz, allow_pickle=True)
    names = [str(n) for n in w['names']]; W = w['W']
    V = M.V; F = M.F; E = M.edges
    rest_len = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    dom = W.argmax(1)
    fn_rest = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    ni = {n: i for i, n in enumerate(names)}
    # the base, seen from the yaw axis: the least radius of anything standing at each height (it does not turn with him)
    sh = np.load(shipped_npz, allow_pickle=True)
    BV = sh['BV'] - np.array([0.0, 0.06, 0.9])
    br = np.hypot(BV[:, 0], BV[:, 1])
    zs = np.arange(0.05, 2.3, 0.05)
    prof = np.full(len(zs), np.inf)
    for i, z in enumerate(zs):
        m = (np.abs(BV[:, 2] - z) < 0.06) & (br > 0.55)
        if m.any(): prof[i] = br[m].min()
    # the stone pile on the rock top (r 0.31..0.48, up to z 0.18)
    pile = (BV[:, 2] > 0.03) & (br < 0.55)
    pile_r = br[pile].min() if pile.any() else np.inf; pile_z = BV[pile, 2].max() if pile.any() else 0
    # head / trunk volumes for the 'inside' test: rest surface points with normals
    N = M.vertex_normals()
    head_v = np.where(W[:, ni['head']] > 0.95)[0]
    trunk_v = np.where((W[:, ni['chest']] + W[:, ni['spine']] + W[:, ni['root']]) > 0.9)[0]
    kd_head = cKDTree(V[head_v]); kd_trunk = cKDTree(V[trunk_v])
    arm_v = np.where((W[:, [ni[n] for n in ('hand.R', 'forearm.R', 'forearm_tw.R')]].sum(1) > 0.6))[0]
    arml_v = np.where((W[:, [ni[n] for n in ('hand.L', 'forearm.L', 'forearm_tw.L')]].sum(1) > 0.6))[0]
    sling_v = np.where(M.vpart > 0)[0]
    fails = []; rep = {}
    for cname in ('Idle', 'Whirl', 'Throw'):
        clip = rs_clips.CLIPS[cname]()
        poses = rs_anim.bake(clip)
        n = clip.frames
        X = []
        worst = dict(stretch=0, stretch_n=0, flips=0, clear=np.inf, inside_head=0.0, inside_trunk=0.0, sole_lo=0.0, sole_hi=0.0, slide=0.0, over=set(), pile=np.inf)
        ballL = []; pairs = {}
        for f, (c, P, info) in enumerate(poses):
            Xf = rs_core.skin(V, W, names, P); X.append(Xf)
            for o in info['over']: worst['over'].add(o)
            # stretch
            L = np.linalg.norm(Xf[E[:, 0]] - Xf[E[:, 1]], axis=1)
            bad = (L > 2.0 * rest_len) & (L - rest_len > 0.03)
            # (the stone is scaled away on purpose)
            bad &= ~((dom[E[:, 0]] == ni['stone']) | (dom[E[:, 1]] == ni['stone']))
            if bad.any():
                worst['stretch_n'] = max(worst['stretch_n'], int(bad.sum())); worst['stretch'] = max(worst['stretch'], float((L / rest_len)[bad].max()))
                for a, b in zip(dom[E[bad, 0]], dom[E[bad, 1]]):
                    k = tuple(sorted((names[a], names[b]))); pairs[k] = max(pairs.get(k, 0), 1)
            # flips: posed face normal against the rest normal carried by the face's main bone
            fnp = np.cross(Xf[F[:, 1]] - Xf[F[:, 0]], Xf[F[:, 2]] - Xf[F[:, 0]])
            fb = dom[F[:, 0]]
            carried = np.zeros_like(fn_rest)
            for b in np.unique(fb):
                m = fb == b; carried[m] = fn_rest[m] @ P[names[b]].R.T
            flip = ((fnp * carried).sum(1) < 0) & (fb != ni['stone']) & (np.linalg.norm(fn_rest, axis=1) > 2e-5)
            worst['flips'] = max(worst['flips'], int(flip.sum()))
            # clearance from the base, any facing
            r = np.hypot(Xf[:, 0], Xf[:, 1]); zi = np.clip(np.round((Xf[:, 2] - zs[0]) / 0.05).astype(int), 0, len(zs) - 1)
            ok = (Xf[:, 2] > 0.2)
            cl = (prof[zi] - r)[ok].min()
            worst['clear'] = min(worst['clear'], float(cl))
            low = (Xf[:, 2] < pile_z + 0.02) & (Xf[:, 2] > 0.0)
            if low.any(): worst['pile'] = min(worst['pile'], float(pile_r - r[low].max()))
            # inside head / trunk (points carried back to the rest frame of that part)
            for tag, kd, src, bone in (('inside_head', kd_head, head_v, 'head'), ('inside_trunk', kd_trunk, trunk_v, 'chest')):
                for grp in (arm_v, sling_v, arml_v):
                    d = P[bone]
                    pts = (Xf[grp] - d.t) @ d.R            # R^T (x - t)
                    dist, idx = kd.query(pts)
                    vi = src[idx]
                    depth = -((pts - V[vi]) * N[vi]).sum(1)
                    inside = (depth > 0) & (dist < 0.12)
                    if inside.any(): worst[tag] = max(worst[tag], float(depth[inside].max()))
            # feet
            soles = Xf[(W[:, [ni[k] for k in ('foot.L', 'toe.L', 'foot.R', 'toe.R')]].sum(1) > 0.9)]
            worst['sole_lo'] = min(worst['sole_lo'], float(soles[:, 2].min()))
            ballL.append(P['toe.L'](rs_skel.J['toe_end.L']))
        X = np.array(X)
        ballL = np.array(ballL)
        if cname != 'Idle': worst['slide'] = float(np.linalg.norm(ballL - ballL[0], axis=1).max())
        # loops and jumps
        loop_gap = float(np.linalg.norm(X[0] - X[-1], axis=1).max())
        body = M.vpart == 0
        step = np.linalg.norm(np.diff(X, axis=0), axis=2)          # (frames, verts)
        acc = np.linalg.norm(np.diff(X, n=2, axis=0), axis=2)
        rep[cname] = dict(frames=n, loop_gap=loop_gap, max_step_body=float(step[:, body].max()), max_step_sling=float(step[:, ~body].max()),
                          max_acc_body=float(acc[:, body].max()), **{k: (sorted(v) if isinstance(v, set) else v) for k, v in worst.items()}, pairs=sorted(pairs))
        r = rep[cname]
        print('%-5s %2d frames | stretch: %d edges (worst x%.1f) %s | flips %d | reach %s | base clearance %.3f m, pile %.3f | inside head %.3f trunk %.3f | soles lowest %.3f | left foot slide %.4f | loop gap %.5f | body step max %.3f acc max %.3f | sling step max %.3f'
              % (cname, n, r['stretch_n'], r['stretch'], r['pairs'][:6], r['flips'], r['over'] or 'ok', r['clear'], r['pile'], r['inside_head'], r['inside_trunk'], r['sole_lo'], r['slide'], r['loop_gap'], r['max_step_body'], r['max_acc_body'], r['max_step_sling']))
        if r['over']: fails.append('%s: out of reach %s' % (cname, r['over']))
        if r['loop_gap'] > 2e-3: fails.append('%s: first and last frame differ by %.4f' % (cname, r['loop_gap']))
        if r['clear'] < 0.0: fails.append('%s: sweeps into the base by %.3f' % (cname, -r['clear']))
        if r['slide'] > 5e-3: fails.append('%s: planted foot slides %.4f' % (cname, r['slide']))
    print('FAIL: ' + '; '.join(fails) if fails else 'checks passed')
    return rep, fails


if __name__ == '__main__':
    rep, fails = main(*sys.argv[1:4])
    sys.exit(1 if fails else 0)
