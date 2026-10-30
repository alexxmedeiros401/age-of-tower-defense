import numpy as np
T=np.load('topo.npz'); F=T['F']; Pw=T['Pw']
lab=np.load('labels.npy')
def loops_of(mask):
    """boundary loops of the face set mask (as vertex index lists, oriented)"""
    Fm=F[mask]
    he=np.concatenate([Fm[:,[0,1]],Fm[:,[1,2]],Fm[:,[2,0]]])
    n=Pw.shape[0]
    key=he[:,0]*n+he[:,1]; rkey=he[:,1]*n+he[:,0]
    s=set(key.tolist())
    bd=np.array([k not in s for k in rkey.tolist()])
    b=he[bd]
    nxt={}
    for a,c in b.tolist():
        nxt.setdefault(a,[]).append(c)
    loops=[]; used=set()
    for a,c in b.tolist():
        if (a,c) in used: continue
        loop=[a]; cur=c; used.add((a,c)); prev=a
        while cur!=a:
            loop.append(cur)
            cands=[x for x in nxt.get(cur,[]) if (cur,x) not in used]
            if not cands: break
            x=cands[0]; used.add((cur,x)); prev=cur; cur=x
        loops.append(loop)
    return loops
if __name__=='__main__':
    for L,nm in ((0,'body'),(1,'gun'),(2,'switch')):
        ls=loops_of(lab==L)
        for lp in ls:
            p=Pw[lp]; per=np.linalg.norm(np.roll(p,-1,0)-p,axis=1).sum()
            print(nm,len(lp),'perim %.3f'%per,'center',p.mean(0).round(3),'ext',(p.max(0)-p.min(0)).round(3))
