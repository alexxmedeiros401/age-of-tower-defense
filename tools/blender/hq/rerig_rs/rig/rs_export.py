"""Step 4 (Blender): bake the clips onto the rigged scene and export the unit.

  python3 rs_export.py -- OUT/rs_rig.blend SHIPPED.glb OUT/rock_slinger.glb [OUT/rock_slinger_hq.blend]

The export call is the Tripo pipeline's (herotripo_rig.py). The textures in the new file are then swapped for the
shipped file's own bytes (same images, no second JPEG pass), so Godot re-extracts identical .jpg files.
"""
import sys, os, json, struct
import bpy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_anim, rs_apply, rs_clips

ORDER = ['Idle', 'Throw', 'Whirl']


def bake_actions(arm):
    K = rs_apply.Keyer(arm)
    report = {}
    for name in ORDER:
        clip = rs_clips.CLIPS[name]()
        poses = rs_anim.bake(clip)
        act = rs_apply.new_action(arm, name)
        K.prev = {}
        for f, (c, P, info) in enumerate(poses):
            K.key(P, f)
        # the stone pops in and out (no shrinking over a frame inside Blender; the exporter samples every frame)
        try:
            fcs = [fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
        except Exception:
            fcs = list(getattr(act, 'fcurves', []))
        for fc in fcs:
            if fc.data_path.endswith('["stone"].scale'):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
            else:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        rs_apply.finish_action(arm, act, 0, clip.frames, name != 'Throw')
        over = sorted({o for c, P, info in poses for o in info['over']})
        report[name] = dict(frames=clip.frames, over=over)
        print('clip %s: %d frames, over-reach: %s' % (name, clip.frames, over or 'none'))
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    return report


def read_glb(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'glTF'
    jl = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20 + jl].decode('utf8'))
    o = 20 + jl
    bl = struct.unpack('<I', b[o:o + 4])[0]
    return js, b[o + 8:o + 8 + bl]


def write_glb(path, js, bin_):
    jb = json.dumps(js, separators=(',', ':')).encode('utf8')
    jb += b' ' * ((4 - len(jb) % 4) % 4)
    bin_ += b'\x00' * ((4 - len(bin_) % 4) % 4)
    with open(path, 'wb') as f:
        f.write(b'glTF' + struct.pack('<II', 2, 12 + 8 + len(jb) + 8 + len(bin_)))
        f.write(struct.pack('<I', len(jb)) + b'JSON' + jb)
        f.write(struct.pack('<I', len(bin_)) + b'BIN\x00' + bin_)


def keep_shipped_images(new_path, shipped_path):
    """Replace each embedded image of the new GLB by the shipped GLB's image of the same name (bytes untouched)."""
    js, bn = read_glb(new_path); ss, sb = read_glb(shipped_path)
    old = {}
    for im in ss.get('images', []):
        bv = ss['bufferViews'][im['bufferView']]
        old[im['name']] = (sb[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']], im.get('mimeType'))
    img_bv = {im['bufferView']: im for im in js.get('images', [])}
    out = bytearray(); swapped = []
    for i, bv in enumerate(js['bufferViews']):
        data = bn[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
        if i in img_bv and img_bv[i]['name'] in old:
            data, mime = old[img_bv[i]['name']]
            if mime: img_bv[i]['mimeType'] = mime
            swapped.append(img_bv[i]['name'])
        while len(out) % 4: out.append(0)
        bv['byteOffset'] = len(out); bv['byteLength'] = len(data)
        out += data
    js['buffers'][0]['byteLength'] = len(out) + ((4 - len(out) % 4) % 4)
    write_glb(new_path, js, bytes(out))
    missing = [im['name'] for im in js.get('images', []) if im['name'] not in old]
    return swapped, missing


def fix_zero_tangents(path, mesh_name='Caveman'):
    """The exporter leaves a zero tangent where a vertex's UV triangles are degenerate; give those a real one (any unit
    vector across the normal), in place."""
    import numpy as np
    js, bn = read_glb(path); bn = bytearray(bn); fixed = 0
    def view(ai, comps):
        a = js['accessors'][ai]; bv = js['bufferViews'][a['bufferView']]
        assert a['componentType'] == 5126 and not bv.get('byteStride'), 'packed float accessors expected'
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        return off, np.frombuffer(bytes(bn[off:off + a['count'] * comps * 4]), '<f4').reshape(-1, comps).copy()
    for m in js['meshes']:
        if m.get('name') != mesh_name: continue
        for pr in m['primitives']:
            if 'TANGENT' not in pr['attributes']: continue
            off, T = view(pr['attributes']['TANGENT'], 4); _, N = view(pr['attributes']['NORMAL'], 3)
            bad = np.where(np.linalg.norm(T[:, :3], axis=1) < 0.5)[0]
            for i in bad:
                n = N[i]; a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
                t = a - n * (a @ n); t /= np.linalg.norm(t)
                T[i] = (t[0], t[1], t[2], 1.0)
            if len(bad):
                bn[off:off + T.size * 4] = T.astype('<f4').tobytes(); fixed += len(bad)
    if fixed: write_glb(path, js, bytes(bn))
    return fixed


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index("--") + 1:]
    blend, shipped, out = argv[:3]
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
    sc = bpy.context.scene
    sc.render.fps = 24
    arm = bpy.data.objects['CavemanRig']
    rep = bake_actions(arm)
    for ob in sc.objects: ob.select_set(False)
    if len(argv) > 3:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(argv[3]))
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                              export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                              export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
    swapped, missing = keep_shipped_images(os.path.abspath(out), os.path.abspath(shipped))
    print('images kept from the shipped file:', swapped, '| re-encoded:', missing)
    print('zero tangents repaired on the character:', fix_zero_tangents(os.path.abspath(out)))
    print('wrote', out, os.path.getsize(out), 'bytes')
