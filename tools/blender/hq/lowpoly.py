"""High-poly -> game mesh: decimation targets, low-poly eyes, part bookkeeping, UV atlas."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
import caveman as cm

CHAR_TARGETS = {"Skin": 6800, "Hair": 3000, "Beard": 1600, "Pelt": 2300, "Leather": 1100, "Teeth": 360, "Cord": 380,
                "Bone": 420, "Sling": 700, "SlingStone": 140, "BagStones": 200}
BASE_TARGETS = {"Ground": 1500, "Rocks": 3800, "Tusks": 1300, "BaseLeather": 420, "Basket": 900, "AmmoStones": 620,
                "Wood": 300, "Pebbles": 420, "Flame": 160}


def decimated_copy(src, target_tris, name=None):
    tris = sum(len(p.vertices) - 2 for p in src.data.polygons)
    ratio = min(1.0, target_tris / max(1, tris))
    tmp = src.copy()
    tmp.data = src.data.copy()
    bpy.context.scene.collection.objects.link(tmp)
    m = tmp.modifiers.new("Dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = ratio
    m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    ev = tmp.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = tmp.data
    bpy.data.objects.remove(tmp)
    bpy.data.meshes.remove(old)
    ob = bpy.data.objects.new(name or (src.name + "_low"), me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = src.location
    for p in me.polygons:
        p.use_smooth = True
    return ob


def eyes_low(name="Eyes_low"):
    bm = bmesh.new()
    for sx in (-1, 1):
        c = cm.eye_c(sx)
        r = bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=12, radius=cm.EYE_R)
        for v in r["verts"]:
            v.co += Vector(c)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tag_part(ob, part_id):
    a = ob.data.attributes.get("part") or ob.data.attributes.new("part", "INT", "FACE")
    a.data.foreach_set("value", np.full(len(ob.data.polygons), part_id, np.int32))


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob


def unwrap(ob, boost=None, margin=0.004, angle=76.0, smooth_iters=80):
    """Islands are chosen on a heavily smoothed copy (coherent normals -> big islands), then the UVs are
    relaxed on the real shape (angle-based unwrap with those seams), equalised, boosted where more
    pixels matter (`boost(face_center, part)->scale`), and packed with concave shapes."""
    me = ob.data
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    bm = bmesh.new()
    bm.from_mesh(me)
    for _ in range(smooth_iters):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(me)
    bm.free()
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, scale_to_bounds=False)
    bpy.ops.uv.seams_from_islands()
    bpy.ops.object.mode_set(mode="OBJECT")
    me.vertices.foreach_set("co", co)
    me.update()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=margin)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    if boost is not None:
        _boost_islands(ob, boost)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def _boost_islands(ob, boost):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uvl = bm.loops.layers.uv.active
    part = bm.faces.layers.int.get("part")
    bm.faces.ensure_lookup_table()
    parent = list(range(len(bm.faces)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in bm.edges:
        fs = e.link_faces
        if len(fs) != 2:
            continue
        f0, f1 = fs
        same = True
        for v in e.verts:
            u0 = [l[uvl].uv for l in f0.loops if l.vert == v][0]
            u1 = [l[uvl].uv for l in f1.loops if l.vert == v][0]
            if (u0 - u1).length > 1e-6:
                same = False
                break
        if same:
            parent[find(f0.index)] = find(f1.index)
    islands = {}
    for f in bm.faces:
        islands.setdefault(find(f.index), []).append(f)
    for isl in islands.values():
        cen = sum((x.calc_center_median() for x in isl), Vector()) / len(isl)
        s = boost(cen, isl[0][part] if part is not None else 0)
        if abs(s - 1.0) > 1e-3:
            uvs = [l[uvl].uv.copy() for x in isl for l in x.loops]
            c = sum(uvs, Vector((0, 0))) / len(uvs)
            for x in isl:
                for l in x.loops:
                    l[uvl].uv = c + (l[uvl].uv - c) * s
    bm.to_mesh(ob.data)
    bm.free()
