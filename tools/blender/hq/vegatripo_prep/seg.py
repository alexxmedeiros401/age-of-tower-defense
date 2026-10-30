import numpy as np, scipy.sparse as sp, os
from scipy.sparse.csgraph import maximum_flow, breadth_first_order
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__))
T=None
def load():
    global T
    if T is None:
        T=dict(np.load(os.path.join(D,'topo.npz')))
        z=np.load(os.path.join(D,'tripo_np.npz')); UV=z['UV']; I=z['I']
        tex=np.asarray(Image.open(os.path.join(D,'tex_base.jpg')))
        uvc=UV[I].mean(1)
        T['col']=tex[np.clip((uvc[:,1]*4095).astype(int),0,4095), np.clip((uvc[:,0]*4095).astype(int),0,4095)].astype(np.float32)/255
    return T
def box(C,x,y,z):
    return (C[:,0]>x[0])&(C[:,0]<x[1])&(C[:,1]>y[0])&(C[:,1]<y[1])&(C[:,2]>z[0])&(C[:,2]<z[1])
def orange(col):
    r,g,b=col[:,0],col[:,1],col[:,2]
    return (r>0.55)&(r-b>0.3)&(g<r*0.85)
def caps(T, sub_a, sub_b, concave_k=8.0):
    N,C=T['N'],T['C']
    na,nb=N[sub_a],N[sub_b]
    cosang=np.clip((na*nb).sum(1),-1,1)
    d=C[sub_b]-C[sub_a]
    concave=((d*na).sum(1)>1e-9)
    w=np.where(concave, concave_k*(1-cosang), 0.1*(1-cosang))
    return w
def mincut(region, src, sink, concave_k=8.0, scale=1e6):
    """region/src/sink: boolean face masks. returns boolean mask (region faces on the source side)"""
    T=load(); fa,fb,L=T['fa'],T['fb'],T['L']
    idx=np.full(len(region),-1); rf=np.where(region)[0]; idx[rf]=np.arange(len(rf))
    m=region[fa]&region[fb]
    a,b=idx[fa[m]],idx[fb[m]]
    w=caps(T,fa[m],fb[m],concave_k)
    avg=w.mean()
    c=L[m]*np.exp(-w/avg*1.0)
    ci=np.maximum((c*scale).astype(np.int64),1)
    n=len(rf); S=n; K=n+1
    big=np.int64(2**30)
    s_f=np.where(src[rf])[0]; k_f=np.where(sink[rf]&~src[rf])[0]
    rows=np.concatenate([a,b,np.full(len(s_f),S),k_f]); cols=np.concatenate([b,a,s_f,np.full(len(k_f),K)])
    data=np.concatenate([ci,ci,np.full(len(s_f),big),np.full(len(k_f),big)]).astype(np.int32 if ci.max()<2**31 else np.int64)
    G=sp.csr_matrix((data.astype(np.int32),(rows,cols)),shape=(n+2,n+2))
    G.sum_duplicates()
    res=maximum_flow(G,S,K)
    print('flow',res.flow_value/scale, 'src',len(s_f),'sink',len(k_f),'region',n)
    Fl=res.flow
    R=(G-Fl).tocsr(); R.data=np.where(R.data>0,1,0); R.eliminate_zeros()
    reach=breadth_first_order(R,S,directed=True,return_predecessors=False)
    out=np.zeros(len(region),bool)
    reach=reach[reach<n]
    out[rf[reach]]=True
    return out
