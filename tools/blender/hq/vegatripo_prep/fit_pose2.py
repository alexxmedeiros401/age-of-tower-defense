import numpy as np, sys
from scipy.spatial import cKDTree
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
import rigmath as rm
S0=2.057; DZ=-0.031
o=np.load('old_vega.npz'); V=o['V']; W=o['W']; gn=[str(x) for x in o['gn']]; part=o['part']; T=o['T']; TP=o['TP']
rig=rm.Rig([str(x) for x in o['bn']], o['bm'])
bodyv=np.unique(T[~np.isin(part[TP],[14,15,16,17])])
rng=np.random.default_rng(0)
sub=rng.choice(bodyv, 5000, replace=False)
Vs=V[sub]; Ws=W[sub]
# tripo body points
t=np.load('topo.npz'); C=t['C']; N=t['N']; lab=np.load('labels.npy')
bm=(lab==0); idx=np.where(bm)[0]; idx=idx[rng.choice(len(idx),400000,replace=False)]
Pt=C[idx]*S0; Pt[:,2]+=DZ; Nt=N[idx]
tree=cKDTree(Pt)
BONES=['root','spine','chest','neck','head','clavicle.R','upperarm.R','forearm.R','hand.R','clavicle.L','upperarm.L','forearm.L','hand.L','thigh.R','shin.R','foot.R','thigh.L','shin.L','foot.L']
TWOK=np.array([b in ('root','spine','chest','neck','head') for b in BONES])
def unpack(x):
    x=x.copy(); xx=x[:-3].reshape(-1,3); xx[~TWOK,1]=0; xx[0]=0; x[:-3]=xx.ravel()
    rot={b:Rot.from_rotvec(x[3*i:3*i+3]).as_matrix() for i,b in enumerate(BONES)}
    tr=x[-3:]
    return rot,tr
def pose_verts(x, Vq=Vs, Wq=Ws):
    rot,tr=unpack(x); S=rig.skin_mats(rot)
    return rm.lbs(Vq,Wq,gn,S)+tr
REG=float(sys.argv[1]) if len(sys.argv)>1 else 0.05
TW=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
def resid(x):
    P=pose_verts(x)
    d,i=tree.query(P)
    r=((P-Pt[i])*Nt[i]).sum(1)    # point-to-plane
    reg=x[:-3].reshape(-1,3)*np.array([REG,TW,REG])
    return np.concatenate([r, reg.ravel()])
x0=np.zeros(3*len(BONES)+3); x0[-2]=-0.07
r0=resid(x0)[:len(Vs)]; print('initial rms %.4f med %.4f'%(np.sqrt((r0**2).mean()),np.median(np.abs(r0))))
res=least_squares(resid,x0,loss='soft_l1',f_scale=0.01,max_nfev=60,verbose=0,diff_step=1e-4)
x=res.x; r1=resid(x)[:len(Vs)]; print('final rms %.4f med %.4f'%(np.sqrt((r1**2).mean()),np.median(np.abs(r1))))
rot,tr=unpack(x)
print('translation',tr.round(4))
for i,b in enumerate(BONES): print(' %-11s %5.1f deg'%(b,np.degrees(np.linalg.norm(x[3*i:3*i+3]))), np.round(x[3*i:3*i+3],3))
xx=x[:-3].reshape(-1,3); xx[~TWOK,1]=0; xx[0]=0; x[:-3]=xx.ravel(); np.save('pose_fit2.npy',x)
