import json,sys
new=json.load(open(sys.argv[1])); old=json.load(open(sys.argv[2])) if len(sys.argv)>2 else {}
def wr(x): return min(x,360-x)
for c in new:
    for tag,d in (('old',old.get(c)),('new',new[c])):
        if not d: continue
        s=d['summary']; parts=[]
        for side in 'RL':
            ph=s.get(f'pen_{side}_head',[0,[]]); pt=s.get(f'pen_{side}_torso',[0,[]]); nh=s.get(f'near_{side}_head',[9,[]])
            rows=d['rows']; wmax=max(wr(r[side+'_wrist']) for r in rows)
            parts.append(f"{side}: H{ph[0]*100:.0f}{ph[1][:6]} T{pt[0]*100:.0f}{pt[1][:6]} near{nh[0]*100:.0f}{nh[1][:6]} psi{s[side+'_psi'][0]:.0f}/{s[side+'_psi'][1]:.0f} d{s[side+'_psi'][2]:.0f} tw{s[side+'_fortw'][0]:.0f}/{s[side+'_fortw'][1]:.0f} d{s[side+'_fortw'][2]:.0f} wr{wmax:.0f} d{s[side+'_wrist'][2]:.0f} el d{s[side+'_elbow'][2]:.0f}")
        print(f"{c:8s} {tag} "+' | '.join(parts))
