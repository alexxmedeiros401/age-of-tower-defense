import numpy as np
from scipy.spatial.transform import Rotation as Rot
PARENT={'root':None,'spine':'root','chest':'spine','neck':'chest','head':'neck',
 'clavicle.R':'chest','upperarm.R':'clavicle.R','forearm.R':'upperarm.R','hand.R':'forearm.R',
 'clavicle.L':'chest','upperarm.L':'clavicle.L','forearm.L':'upperarm.L','hand.L':'forearm.L',
 'thigh.R':'root','shin.R':'thigh.R','foot.R':'shin.R','thigh.L':'root','shin.L':'thigh.L','foot.L':'shin.L',
 'pistol':None,'switch':None,'button':'switch'}
class Rig:
    def __init__(self, names, mats):
        self.names=list(names); self.rest={n:np.array(m) for n,m in zip(names,mats)}
        self.order=[]
        def add(n):
            if n in self.order: return
            p=PARENT[n]
            if p: add(p)
            self.order.append(n)
        for n in self.names: add(n)
    def skin_mats(self, rot, trans=None):
        """rot: {bone: 3x3 local rotation (bone space)}; trans: {bone: local translation in bone space}. returns {bone: 4x4 skin}"""
        posed={}
        for n in self.order:
            R=np.eye(4)
            if n in rot: R[:3,:3]=rot[n]
            if trans and n in trans: R[:3,3]=trans[n]
            p=PARENT[n]
            if p is None: posed[n]=self.rest[n]@R
            else: posed[n]=posed[p]@np.linalg.inv(self.rest[p])@self.rest[n]@R
        self.posed=posed
        return {n:posed[n]@np.linalg.inv(self.rest[n]) for n in self.order}
def lbs(V, W, gn, S):
    """V (n,3), W (n,g) weights with columns named gn, S dict of 4x4 -> posed verts"""
    out=np.zeros_like(V); Vh=np.c_[V,np.ones(len(V))]
    for j,n in enumerate(gn):
        w=W[:,j]; m=w>0
        if not m.any(): continue
        out[m]+=w[m,None]*(Vh[m]@S[n].T)[:,:3]
    return out
def blend_mats(W, gn, S):
    M=np.zeros((W.shape[0],4,4))
    for j,n in enumerate(gn):
        w=W[:,j]
        if not (w>0).any(): continue
        M+=w[:,None,None]*S[n][None]
    return M
def inv_lbs(Vp, W, gn, S):
    M=blend_mats(W,gn,S)
    Mi=np.linalg.inv(M)
    return np.einsum('nij,nj->ni',Mi,np.c_[Vp,np.ones(len(Vp))])[:,:3]
