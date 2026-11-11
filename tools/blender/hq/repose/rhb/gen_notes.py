# gen_notes.py ID "Clip:RL,Clip2:R" HUMAN.md -> /home/claude/work/repose/ID/notes.md
import json, sys
id_, spec, human = sys.argv[1:4]
D = f'/home/claude/work/repose/{id_}'
new = json.load(open(f'{D}/triage_new.json')); old = json.load(open(f'/home/claude/work/repose/rhB_triage/{id_}.json'))
def wrapd(a): return (a + 180) % 360 - 180
out = [open(human).read().rstrip(), '']
out.append('## Clearance (triage.py, cm: deepest arm/hand/weapon point inside the head or torso beyond its rest overlap; "near" = closest approach to the head)')
out.append('| clip | side | old head | new head | old torso | new torso | old near | new near |'); out.append('|---|---|---|---|---|---|---|---|')
for c in new:
    for s in 'RL':
        so, sn = old[c]['summary'], new[c]['summary']
        g = lambda d, k, dflt: d.get(k, [dflt])[0]
        out.append(f"| {c} | {s} | {g(so,f'pen_{s}_head',0)*100:.0f} | {g(sn,f'pen_{s}_head',0)*100:.0f} | {g(so,f'pen_{s}_torso',0)*100:.0f} | {g(sn,f'pen_{s}_torso',0)*100:.0f} | {g(so,f'near_{s}_head',9)*100:.0f} | {g(sn,f'near_{s}_head',9)*100:.0f} |")
out.append('')
out.append('## Joint numbers per frame for every re-authored arm (deg; d = change from the previous frame)')
out.append('psi = upper-arm roll, tw = forearm twist (the hand\'s twist for rigs with a forearm_twist bone, which carries its share), elbow = elbow bend, wrist = wrist swing.')
for item in spec.split(','):
    c, sides = item.split(':')
    rows = new[c]['rows']
    for s in sides:
        out.append(f'\n### {c} {s}  (max |d|: ' + ', '.join(f"{j} {max(abs(wrapd(b[s+'_'+j]-a[s+'_'+j])) for a,b in zip(rows,rows[1:])):.0f}" for j in ('psi','fortw','elbow','wrist')) + ')')
        out.append('| f | psi | d | tw | d | elbow | d | wrist | d | head pen | torso pen |'); out.append('|---|---|---|---|---|---|---|---|---|---|---|')
        prev = None
        for r in rows:
            vals = [r[s+'_psi'], r[s+'_fortw'], r[s+'_elbow'], r[s+'_wrist']]
            dl = ['' if prev is None else f'{abs(wrapd(v-p)):.0f}' for v, p in zip(vals, prev or vals)]
            out.append(f"| {r['f']} | {vals[0]:.0f} | {dl[0]} | {vals[1]:.0f} | {dl[1]} | {vals[2]:.0f} | {dl[2]} | {vals[3]:.0f} | {dl[3]} | {r.get(f'pen_{s}_head',0)*100:.0f} | {r.get(f'pen_{s}_torso',0)*100:.0f} |")
            prev = vals
open(f'{D}/notes.md', 'w').write('\n'.join(out) + '\n'); print('wrote', f'{D}/notes.md')
