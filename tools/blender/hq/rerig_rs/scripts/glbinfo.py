"""Pure-python summary of a unit GLB (no Blender): nodes, skin, meshes, clips, images. usage: glbinfo.py FILE [FILE2]"""
import sys, json, struct, hashlib
def load(p):
    b = open(p, 'rb').read()
    assert b[:4] == b'glTF'
    n = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
    return js, b[bin0:], len(b)
def info(p):
    js, bn, size = load(p)
    acc = js['accessors']; bv = js['bufferViews']
    out = dict(size=size, nodes=len(js['nodes']), node_names=[n.get('name') for n in js['nodes'] if 'mesh' in n or n.get('name') in ('Yaw', 'CavemanRig', 'RockSlingerHQ')],
               joints=len(js['skins'][0]['joints']) if js.get('skins') else 0, materials=[m['name'] for m in js['materials']], meshes={})
    for m in js['meshes']:
        tris = sum(acc[pr['indices']]['count'] // 3 for pr in m['primitives']); verts = sum(acc[pr['attributes']['POSITION']]['count'] for pr in m['primitives'])
        out['meshes'][m['name']] = dict(tris=tris, verts=verts, attrs=sorted(m['primitives'][0]['attributes']))
    out['clips'] = {}
    for a in js.get('animations', []):
        tmax = max(acc[s['input']]['max'][0] for s in a['samplers'])
        paths = {}
        for c in a['channels']: paths[c['target']['path']] = paths.get(c['target']['path'], 0) + 1
        out['clips'][a['name']] = dict(length=round(tmax, 4), channels=paths, keys=max(acc[s['input']]['count'] for s in a['samplers']))
    out['images'] = {}
    for im in js.get('images', []):
        v = bv[im['bufferView']]; d = bn[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]
        out['images'][im.get('name')] = (im.get('mimeType'), len(d), hashlib.md5(d).hexdigest()[:10])
    out['extensions'] = js.get('extensionsUsed', [])
    return out
for p in sys.argv[1:]:
    i = info(p); print(p)
    for k, v in i.items(): print('   %-10s %s' % (k, v))
