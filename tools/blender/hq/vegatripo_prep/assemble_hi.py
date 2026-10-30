import numpy as np, pickle
def build(lab, F, Pw, patches, which, L):
    """faces of label L + patch faces -> (V, F, is_patch, pcol, prm) with vertex indices into a compact array"""
    Fm=F[lab==L]
    used=np.unique(Fm); remap=np.full(Pw.shape[0],-1); remap[used]=np.arange(len(used))
    V=[Pw[used]]; Fs=[remap[Fm]]; isp=[np.zeros(len(Fm),bool)]
    nv=len(used); pcol=[np.zeros((nv,3))]; prm=[np.zeros((nv,3))]
    for (Lr,Pin,tris,col,rmv) in patches[which]:
        n=len(Lr); idx=np.r_[remap[Lr], nv+np.arange(len(Pin))]
        assert (remap[Lr]>=0).all()
        V.append(Pin); Fs.append(idx[tris]); isp.append(np.ones(len(tris),bool))
        pc=np.zeros((len(Pin),3)); pc[:]=col[n:]; pcol.append(pc); pr=np.zeros((len(Pin),3)); pr[:]=rmv[n:]; prm.append(pr)
        # boundary verts get their colours too (for patch faces' interpolation)
        pcol[0][remap[Lr]]=col[:n]; prm[0][remap[Lr]]=rmv[:n]
        nv+=len(Pin)
    return np.concatenate(V), np.concatenate(Fs), np.concatenate(isp), np.concatenate(pcol), np.concatenate(prm), used
def check(Fc):
    nv=Fc.max()+1
    he=np.concatenate([Fc[:,[0,1]],Fc[:,[1,2]],Fc[:,[2,0]]])
    key=he[:,0]*nv+he[:,1]
    u,c=np.unique(key,return_counts=True)
    rk=he[:,1]*nv+he[:,0]
    has_rev=np.isin(rk,u)
    print('  faces',len(Fc),'dup directed half-edges',(c>1).sum(),'half-edges without twin',(~has_rev).sum())
if __name__=='__main__':
    T=np.load('topo.npz'); F=T['F']; Pw=T['Pw']; lab=np.load('labels.npy'); pt=pickle.load(open('patches.pkl','rb'))
    for L,w in ((0,'body'),(1,'gun'),(2,'sw')):
        V,Fc,isp,pc,pr,used=build(lab,F,Pw,pt,w,L); print(w); check(Fc)
