"""Paint bone weights on the rigged mesh in the Tripo pose (numpy, no Blender): the rig run with --debug writes rig_debug.npz.

    python3 wlook.py OUT/rig_debug.npz forearm.R,hand.R OUT/w.png [x0,x1,y0,y1,z0,z1]

Front and side views; red = the summed weight of the listed bones, blue = none.
"""
import numpy as np, sys
from PIL import Image, ImageDraw
d=np.load(sys.argv[1]); P=d['P']; body=d['body']; W=d['W4']; gn=list(d['gn']); lt=d['lt']
bones=sys.argv[2].split(','); out=sys.argv[3]
crop=[float(x) for x in sys.argv[4].split(',')] if len(sys.argv)>4 else None
w=np.zeros(len(P)); w[body]=W[:,[gn.index(b) for b in bones]].sum(1)
cols=np.stack([w, 0.3*np.ones_like(w), 1-w],1)
# rasterize triangles with painter's algorithm (centroid sort), per view
def view(ax_u, ax_v, ax_d, sgn_u, sgn_d, px=600):
    C=P[lt].mean(1); m=np.ones(len(lt),bool)
    if crop: m=(C[:,0]>crop[0])&(C[:,0]<crop[1])&(C[:,2]>crop[4])&(C[:,2]<crop[5])&(C[:,1]>crop[2])&(C[:,1]<crop[3])
    T=lt[m]; Cm=C[m]
    U=P[:,ax_u]*sgn_u; V=P[:,ax_v]
    lo=np.array([U[T].min(),V[T].min()]); hi=np.array([U[T].max(),V[T].max()]); sp=(hi-lo).max()*1.05
    im=Image.new('RGB',(px,px),(200,200,200)); dr=ImageDraw.Draw(im)
    n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); n/=np.linalg.norm(n,axis=1)[:,None]+1e-12
    for i in np.argsort(Cm[:,ax_d]*sgn_d):
        t=T[i]; pts=[((U[k]-lo[0])/sp*px, px-(V[k]-lo[1])/sp*px) for k in t]
        sh=0.5+0.5*abs(n[i,ax_d]); c=cols[t].mean(0)*sh
        dr.polygon(pts, fill=tuple((np.clip(c,0,1)*255).astype(int)))
    return im
a=view(0,2,1,1,-1); b=view(1,2,0,-1,-1)
M=Image.new('RGB',(1200,600)); M.paste(a,(0,0)); M.paste(b,(600,0)); M.save(out)
