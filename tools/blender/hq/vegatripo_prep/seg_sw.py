import numpy as np, sys
sys.path.insert(0,'.'); import seg
T=seg.load(); C=T['C']; N=T['N']
region=seg.box(C,(0.03,0.32),(-0.05,0.34),(0.26,0.66))
cx,cy=0.14,0.145
d=np.stack([C[:,0]-cx,C[:,1]-cy],1); r=np.linalg.norm(d,axis=1); rad=d/np.maximum(r,1e-9)[:,None]
nr=(N[:,:2]*rad).sum(1)
src=region&(r<0.036)&(r>0.012)&(nr>0.6)&(C[:,2]>0.33)&(C[:,2]<0.585)
src|=region&(C[:,2]>0.319)&(C[:,2]<0.345)&(C[:,0]>0.14)&(C[:,0]<0.178)&(C[:,1]>0.16)&(C[:,1]<0.186)
print('seeds',src.sum())
inner=seg.box(C,(0.035,0.315),(-0.045,0.335),(0.265,0.655))
sink=(region&~inner)|(region&(r>0.065))|(region&(r>0.02)&(r<0.07)&(nr<-0.3)&(C[:,2]<0.48))
sink&=~src
sw=seg.mincut(region, src, sink)
print('switch faces', sw.sum())
np.save('lab_sw.npy', sw)
Cs=C[sw]; print('z range',Cs[:,2].min(),Cs[:,2].max(),'xy mean',Cs[:,:2].mean(0))
