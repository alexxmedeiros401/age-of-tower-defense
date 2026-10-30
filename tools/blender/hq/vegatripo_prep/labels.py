import numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
T=np.load('topo.npz'); F=T['F']; fa=T['fa']; fb=T['fb']; C=T['C']; Pw=T['Pw']; A=T['A']
nf=len(F)
lab=np.zeros(nf,np.int8)
lab[np.load('lab_gun.npy')]=1
lab[np.load('lab_sw.npy')]=2
lab[np.load('lab_cable.npy')]=3
# keep only the largest component per label (smaller pieces -> body for props; discard tiny islands of body)
def comps(mask):
    idx=np.where(mask)[0]; m=mask[fa]&mask[fb]
    ii=np.full(nf,-1); ii[idx]=np.arange(len(idx))
    G=sp.coo_matrix((np.ones(m.sum()),(ii[fa[m]],ii[fb[m]])),shape=(len(idx),len(idx)))
    n,l=connected_components(G,directed=False); return idx,l,n
for L in (1,2):
    idx,l,n=comps(lab==L); cnt=np.bincount(l); big=np.argmax(cnt)
    print('label',L,'components',n,'sizes',sorted(cnt)[-5:])
    lab[idx[l!=big]]=0
idx,l,n=comps(lab==0); cnt=np.bincount(l); big=np.argmax(cnt)
print('body components',n,'sizes',sorted(cnt)[-6:])
lab[idx[l!=big]]=3
np.save('labels.npy',lab)
print('counts',np.bincount(lab))
# boundary loops of the body
m=(lab[fa]==0)!=(lab[fb]==0)
print('body boundary edges',m.sum())
