import json, struct, numpy as np, sys
def read(path):
    b = open(path,'rb').read()
    magic, ver, L = struct.unpack('<III', b[:12])
    off = 12; chunks=[]
    while off < L:
        cl, ct = struct.unpack('<II', b[off:off+8]); chunks.append((ct, b[off+8:off+8+cl])); off += 8+cl
    js = json.loads(chunks[0][1]); bin_ = chunks[1][1] if len(chunks)>1 else b''
    return js, bin_
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def acc(js, bin_, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    o = bv.get('byteOffset',0)+a.get('byteOffset',0); n=a['count']*NC[a['type']]
    arr = np.frombuffer(bin_, CT[a['componentType']], n, o)
    return arr.reshape(a['count'], NC[a['type']]) if NC[a['type']]>1 else arr
if __name__=='__main__':
    js, bin_ = read(sys.argv[1])
    print(json.dumps({k:v for k,v in js.items() if k not in ('accessors','bufferViews')}, indent=1)[:3000])
    for i,a in enumerate(js['accessors']): print(i, a['type'], a['count'], a.get('min'), a.get('max'))
