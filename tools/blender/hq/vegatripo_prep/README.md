# Commander Vega from the Tripo model: preparation (run locally, numpy; paths are relative to a scratch folder)

1. `glbread.py` / `comps.py`-style load -> `tripo_np.npz`; `topo.py` welds the Tripo mesh (UV seams) and builds face adjacency.
2. `seg_gun.py`, `seg_cable.py`, `seg_sw.py` (with `seg.py`): min-cuts on the face graph (cheap across concave creases)
   between seeds on each prop and sinks on the coat: the holstered pistol, its cable (dropped) and the killswitch.
   `labels.py` keeps each prop's largest piece -> `labels.npz` (0 body, 1 pistol, 2 switch, 3 dropped).
3. `patches.py` (with `loops.py`): fills every hole the cuts left (harmonic membranes over the hole's projected
   triangulation); body holes get the coat's dark colour, the props' caps colours interpolated from their rims -> `patches.pkl`.
4. `fit_pose2.py` (with `rigmath.py`): the old rig's pose that puts the old Vega mesh onto the Tripo body (least squares,
   point-to-plane; no root rotation, no limb twist; the feet are reset to rest in `pose_fit.json`).
Then `../vegatripo_bake.py` on a runner (inputs: vega_tripo.glb, labels.npz, patches.pkl) and `../vegatripo_rig.py`.
