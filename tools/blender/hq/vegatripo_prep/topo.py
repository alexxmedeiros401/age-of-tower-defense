import numpy as np, scipy.sparse as sp, os
D=os.path.dirname(os.path.abspath(__file__))
def build():
    z=np.load(os.path.join(D,'tripo_np.npz')); P=z['PB'].astype(np.float64); I=z['I'].astype(np.int64); inv=z['inv'].astype(np.int64)
    n=inv.max()+1; Pw=np.zeros((n,3)); Pw[inv]=P
    F=inv[I]
    nf=len(F)
    e=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); fe=np.tile(np.arange(nf),3)
    e.sort(1); key=e[:,0]*n+e[:,1]
    order=np.argsort(key,kind='stable'); ks=key[order]
    # pairs of faces sharing an edge
    same=np.where(ks[1:]==ks[:-1])[0]
    fa=fe[order[same]]; fb=fe[order[same+1]]
    ev=e[order[same]]
    cnt=np.bincount(np.searchsorted(np.unique(ks),ks), minlength=0)
    print('edges',len(np.unique(ks)),'shared pairs',len(fa),'nonmanifold edges(>2)',(cnt>2).sum(),'boundary(1)',(cnt==1).sum())
    v0,v1,v2=Pw[F[:,0]],Pw[F[:,1]],Pw[F[:,2]]
    N=np.cross(v1-v0,v2-v0); A=np.linalg.norm(N,axis=1); N/=np.maximum(A,1e-20)[:,None]
    C=(v0+v1+v2)/3
    L=np.linalg.norm(Pw[ev[:,0]]-Pw[ev[:,1]],axis=1)
    np.savez(os.path.join(D,'topo.npz'),Pw=Pw,F=F,fa=fa,fb=fb,L=L,N=N,C=C,A=A/2)
if __name__=='__main__': build()
