import numpy as np, sys
sys.path.insert(0,'.'); import seg
T=seg.load(); C=T['C']
g=np.load('lab_gunall.npy')
y0=float(sys.argv[1])
src=g&(C[:,1]<y0)
sink=g&(C[:,1]>0.16)
gun=seg.mincut(g, src, sink)
print('gun', gun.sum(), 'cable', (g&~gun).sum())
np.save('lab_gun.npy', gun); np.save('lab_cable.npy', g&~gun)
Cg=C[gun]; print('gun y range', Cg[:,1].min(), Cg[:,1].max())
