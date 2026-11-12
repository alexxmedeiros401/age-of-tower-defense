# python3 p2h_stretchsum.py SHIPPED_stretch.json NEW_stretch.json : per clip, stretched edges and worst growth (mm), shipped -> new
import json, sys
a = json.load(open(sys.argv[1]))['clips']; b = json.load(open(sys.argv[2]))['clips']
print('| clip | stretched edges shipped | new | worst stretch shipped (mm) | new |'); print('|---|---|---|---|---|')
for c in b:
    def st(d):
        ss = d.get(c, {}).get('stretched', []); return sum(s['edges'] for s in ss), round(max([s['grow_m'] for s in ss] or [0]) * 1000)
    (e0, w0), (e1, w1) = st(a), st(b)
    print(f'| {c} | {e0} | {e1} | {w0} | {w1} |')
