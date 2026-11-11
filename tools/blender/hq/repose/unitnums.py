# Numbers for notes.md: per re-authored clip/arm, the ranges of upper-arm roll (psi), forearm twist, wrist (deviation
# from the neutral grip), elbow, and their largest frame-to-frame changes (from armsolve's report), plus the
# head/torso clearance of the shipped and the new GLB (from triage json).
# usage: python3 unitnums.py SOLVE.json TRI_OLD.json TRI_NEW.json [per-frame clip ...]
import json, sys
sol = json.load(open(sys.argv[1])); to = json.load(open(sys.argv[2]))['clips']; tn = json.load(open(sys.argv[3]))['clips']
per = sys.argv[4:]
print('| clip | arm | roll psi | forearm twist | wrist | elbow | max frame delta psi/twist/wrist/elbow |')
print('|---|---|---|---|---|---|---|')
for c, sides in sol.items():
    for s, rows in sides.items():
        rows = [r for r in rows if r.get('w', 1) > 0]
        mm = lambda q: '%.0f..%.0f' % (min(r[q] for r in rows), max(r[q] for r in rows))
        md = '/'.join('%.0f' % max(abs(r['d' + q]) for r in rows) for q in ('psi', 'tw', 'wrist', 'elbow'))
        print('| %s | %s | %s | %s | %s | %s | %s |' % (c, s, mm('psi'), mm('tw'), mm('wrist'), mm('elbow'), md))
print()
print('Clearance (deepest arm/hand/weapon vertex inside head / torso, cm; detection counts sleeves and props resting on the body too):')
print()
print('| clip | arm | shipped head | shipped torso | new head | new torso |')
print('|---|---|---|---|---|---|')
for c in tn:
    for s in ('R', 'L'):
        mo = lambda k, t: max(r[s][k] for r in t[c])
        print('| %s | %s | %.1f | %.1f | %.1f | %.1f |' % (c, s, mo('head', to), mo('torso', to), mo('head', tn), mo('torso', tn)))
for c in per:
    if c not in sol: continue
    print('\nPer frame, %s (f: psi/twist/wrist/elbow):' % c)
    for s, rows in sol[c].items():
        print('- %s: ' % s + ' '.join('%d:%.0f/%.0f/%.0f/%.0f' % (r['f'], r['psi'], r['tw'], r['wrist'], r['elbow']) for r in rows if r.get('w', 1) > 0))
