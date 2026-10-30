import numpy as np, sys
sys.path.insert(0,'.'); import seg
T=seg.load(); C=T['C']; col=T['col']
region=seg.box(C,(-0.31,0.0),(-0.37,0.36),(0.2,0.64))
src_barrel=seg.box(C,(-0.26,-0.06),(-0.37,-0.2),(0.4,0.64))
src_grip=seg.box(C,(-0.22,-0.12),(-0.14,-0.02),(0.29,0.37))&seg.orange(col)
src_cable=seg.box(C,(-0.32,-0.08),(0.19,0.36),(0.22,0.52))
print('seeds', src_barrel.sum(), src_grip.sum(), src_cable.sum())
# sink: faces on the region box's skin + coat faces toward his middle
inner=seg.box(C,(-0.30,-0.005),(-0.36,0.35),(0.21,0.63))
sink=(region&~inner)|(region&(C[:,0]>-0.095))
gun=seg.mincut(region, src_barrel|src_grip|src_cable, sink)
print('gun+cable faces', gun.sum())
np.save('lab_gunall.npy', gun)
