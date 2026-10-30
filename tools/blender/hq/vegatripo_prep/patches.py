import numpy as np, scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from scipy.spatial import Delaunay
from matplotlib.path import Path
from PIL import Image
from loops import loops_of
T=np.load('topo.npz'); F=T['F']; Pw=T['Pw']
z=np.load('tripo_np.npz'); UV=z['UV']; I=z['I']; inv=z['inv']
lab=np.load('labels.npy')
tb=np.asarray(Image.open('tex_base.jpg')).astype(np.float32)/255
trm=np.asarray(Image.open('tex_rm.jpg')).astype(np.float32)/255
# a uv for every welded vertex, taken from a corner of a face of the piece being patched
def vuv_for(Lb):
    m=lab==Lb
    vuv=np.zeros((Pw.shape[0],2),np.float32); vuv[inv[I[m].ravel()]]=UV[I[m].ravel()]
    return vuv
def samp(tex,uv,r=3):
    x=np.clip((uv[:,0]*4095).astype(int),r,4095-r); y=np.clip((uv[:,1]*4095).astype(int),r,4095-r)
    acc=0
    for dx in range(-r,r+1,r):
        for dy in range(-r,r+1,r): acc=acc+tex[y+dy,x+dx]
    return acc/9
def patch(loop, faces_mask, Lb):
    vuv=vuv_for(Lb)
    L=np.array(loop); P=Pw[L]; n=len(L)
    if n==3:
        tris=np.array([[0,1,2]]); Pin=np.zeros((0,3))
        allP=P; nb=3
    else:
        c=P.mean(0); U,S,Vt=np.linalg.svd(P-c); ax=Vt[:2]
        Q=(P-c)@ax.T
        poly=Path(Q)
        el=np.median(np.linalg.norm(np.roll(Q,-1,0)-Q,axis=1))
        h=el*1.6
        lo,hi=Q.min(0),Q.max(0)
        gx,gy=np.meshgrid(np.arange(lo[0]+h/2,hi[0],h),np.arange(lo[1]+h/2,hi[1],h*0.866))
        gx=gx+(np.arange(gx.shape[0])[:,None]%2)*h/2
        G=np.c_[gx.ravel(),gy.ravel()]
        G=G[poly.contains_points(G)]
        # keep interior points away from the boundary
        if len(G):
            from scipy.spatial import cKDTree
            d,_=cKDTree(Q).query(G); G=G[d>h*0.6]
        Q2=np.r_[Q,G]
        tri=Delaunay(Q2).simplices
        cen=Q2[tri].mean(1)
        tri=tri[poly.contains_points(cen)]
        # drop triangles made only of boundary vertices that span across a concavity (centroid inside is the test already)
        nb=n; m=len(G)
        # harmonic 3d positions for interior pts
        allP=np.zeros((n+m,3)); allP[:n]=P
        if m:
            e=np.r_[tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]
            A=sp.coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n+m,n+m)); A=((A+A.T)>0).astype(float).tocsr()
            deg=np.asarray(A.sum(1)).ravel()
            Lp=sp.diags(deg)-A
            Lii=Lp[n:,n:]; Lib=Lp[n:,:n]
            for k in range(3):
                allP[n:,k]=spsolve(Lii.tocsc(),-Lib@P[:,k])
        tris=tri
    # colours: harmonic too (same system); boundary colours from texture
    cb=samp(tb,vuv[L]); rb=samp(trm,vuv[L])
    if Lb==0:
        # the body's patches: plain coat (the darker half's median colour), no smear of the props' colours
        lum=cb.mean(1); dk=lum<=np.median(lum)
        cb=np.tile(np.median(cb[dk],0),(n,1)); rb=np.tile(np.median(rb[dk],0),(n,1))
    m=len(allP)-n
    col=np.zeros((len(allP),3)); rmv=np.zeros((len(allP),3)); col[:n]=cb; rmv[:n]=rb
    if m:
        for k in range(3):
            col[n:,k]=spsolve(Lii.tocsc(),-Lib@cb[:,k]); rmv[n:,k]=spsolve(Lii.tocsc(),-Lib@rb[:,k])
    # orientation: boundary half-edge L[0]->L[1] belongs to the mesh; the patch must contain L[1]->L[0]
    # orientation: the mesh's half-edges along the loop vs the patch's
    Fm=F[faces_mask]; nvv=Pw.shape[0]
    hs=set((np.concatenate([Fm[:,[0,1]],Fm[:,[1,2]],Fm[:,[2,0]]])@np.array([nvv,1])).tolist())
    fwd=sum((int(L[i])*nvv+int(L[(i+1)%n])) in hs for i in range(n))
    gl=np.r_[L, -np.ones(len(allP)-n,int)]
    pe=set()
    for t in tris:
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
            if a<n and b<n: pe.add((a,b))
    same=sum(((i,(i+1)%n) in pe) for i in range(n)); rev=sum((((i+1)%n,i) in pe) for i in range(n))
    # mesh has L[i]->L[i+1] (fwd>0): patch must hold the reverse
    if (fwd>=n/2 and same>rev) or (fwd<n/2 and rev>same):
        tris=tris[:,::-1]
    return L, allP[n:], tris, col, rmv
out={}
for Lb,nm in ((0,'body'),(1,'gun'),(2,'sw')):
    lps=loops_of(lab==Lb)
    res=[]
    for lp in lps:
        if len(lp)<10: continue
        Lr,Pin,tris,col,rmv=patch(lp, lab==Lb, Lb)
        res.append((Lr,Pin,tris,col,rmv))
        print(nm,len(lp),'interior',len(Pin),'tris',len(tris),'col',(col.mean(0)*255).round())
    out[nm]=res
import pickle; pickle.dump(out,open('patches.pkl','wb'))
