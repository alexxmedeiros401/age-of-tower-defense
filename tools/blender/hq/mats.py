"""Procedural, hand-painted-style materials for the HQ high-poly (Cycles). Everything here is baked
into the game textures (albedo, normal, roughness), so bump detail ends up in the normal map."""
import bpy


def lin(c):
    """sRGB (0-1) -> linear, for colour sockets."""
    out = []
    for x in c[:3]:
        out.append(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92)
    return (out[0], out[1], out[2], 1.0)


def _sock(node, ident, out=False):
    for s in (node.outputs if out else node.inputs):
        if s.identifier == ident or s.name == ident:
            return s
    raise KeyError(ident)


class NB:
    def __init__(self, mat):
        mat.use_nodes = True
        self.mat = mat
        self.nt = mat.node_tree
        self.nodes = self.nt.nodes
        self.links = self.nt.links
        self.bsdf = self.nodes.get("Principled BSDF")
        self.out = self.nodes.get("Material Output")

    def node(self, t, **props):
        nd = self.nodes.new(t)
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def put(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.links.new(v, sock)
        elif isinstance(v, (tuple, list)):
            if len(sock.default_value) == 4 and len(v) == 3:
                v = tuple(v) + (1.0,)
            sock.default_value = v
        else:
            sock.default_value = v

    # ---------------------------------------------------------------- basics
    def rgb(self, srgb):
        n = self.node("ShaderNodeRGB")
        n.outputs[0].default_value = lin(srgb)
        return n.outputs[0]

    def value(self, v):
        n = self.node("ShaderNodeValue")
        n.outputs[0].default_value = v
        return n.outputs[0]

    def math(self, op, a, b=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.put(n.inputs[0], a)
        if b is not None:
            self.put(n.inputs[1], b)
        return n.outputs[0]

    def mix(self, fac, a, b, blend="MIX", clamp=True):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend, clamp_factor=clamp)
        self.put(_sock(n, "Factor_Float"), fac)
        self.put(_sock(n, "A_Color"), a)
        self.put(_sock(n, "B_Color"), b)
        return _sock(n, "Result_Color", out=True)

    def mixf(self, fac, a, b):
        n = self.node("ShaderNodeMix", data_type="FLOAT", clamp_factor=True)
        self.put(_sock(n, "Factor_Float"), fac)
        self.put(_sock(n, "A_Float"), a)
        self.put(_sock(n, "B_Float"), b)
        return _sock(n, "Result_Float", out=True)

    def smooth(self, x, lo, hi):
        n = self.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
        self.put(n.inputs["Value"], x)
        n.inputs["From Min"].default_value = lo
        n.inputs["From Max"].default_value = hi
        return n.outputs["Result"]

    def remap(self, x, a0, a1, b0, b1):
        n = self.node("ShaderNodeMapRange", interpolation_type="LINEAR", clamp=True)
        self.put(n.inputs["Value"], x)
        n.inputs["From Min"].default_value = a0
        n.inputs["From Max"].default_value = a1
        n.inputs["To Min"].default_value = b0
        n.inputs["To Max"].default_value = b1
        return n.outputs["Result"]

    def obj(self):
        return self.node("ShaderNodeTexCoord").outputs["Object"]

    def geo(self, out):
        return self.node("ShaderNodeNewGeometry").outputs[out]

    def attr(self, name, out="Fac"):
        n = self.node("ShaderNodeAttribute", attribute_name=name)
        return n.outputs[out]

    def scale_vec(self, vec, s):
        n = self.node("ShaderNodeVectorMath", operation="MULTIPLY")
        self.put(n.inputs[0], vec)
        n.inputs[1].default_value = s if isinstance(s, (tuple, list)) else (s, s, s)
        return n.outputs[0]

    def add_vec(self, a, b):
        n = self.node("ShaderNodeVectorMath", operation="ADD")
        self.put(n.inputs[0], a)
        self.put(n.inputs[1], b)
        return n.outputs[0]

    def noise(self, vec, scale=5.0, detail=3.0, rough=0.55, distort=0.0, out="Fac"):
        n = self.node("ShaderNodeTexNoise")
        if vec is not None:
            self.put(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = distort
        return n.outputs[out]

    def voronoi(self, vec, scale=5.0, rand=1.0, feature="F1", out="Distance"):
        n = self.node("ShaderNodeTexVoronoi", feature=feature)
        if vec is not None:
            self.put(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = scale
        n.inputs["Randomness"].default_value = rand
        return n.outputs[out]

    def wave(self, vec, scale=5.0, distort=2.0, detail=2.0, bands="BANDS", direction="Z", profile="SIN"):
        n = self.node("ShaderNodeTexWave", wave_type=bands, wave_profile=profile)
        if bands == "BANDS":
            n.bands_direction = direction
        else:
            n.rings_direction = direction
        if vec is not None:
            self.put(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = scale
        n.inputs["Distortion"].default_value = distort
        n.inputs["Detail"].default_value = detail
        return n.outputs["Fac"]

    def reg(self, k):
        """Smooth 0..1 mask of sculpt label k (float attribute r<k>, see prep.region_masks)."""
        return self.smooth(self.attr("r%d" % k), 0.35, 0.65)

    def eq(self, x, k):
        """1 where x == k (integers stored as float)."""
        d = self.math("ABSOLUTE", self.math("SUBTRACT", x, float(k)))
        return self.math("LESS_THAN", d, 0.5)

    def bump(self, height, strength=0.5, distance=0.01, normal=None):
        n = self.node("ShaderNodeBump")
        self.put(n.inputs["Height"], height)
        n.inputs["Strength"].default_value = strength
        n.inputs["Distance"].default_value = distance
        if normal is not None:
            self.put(n.inputs["Normal"], normal)
        return n.outputs["Normal"]

    def finish(self, color, rough=0.6, normal=None, metal=0.0, emit=None, emit_strength=0.0):
        b = self.bsdf
        self.put(b.inputs["Base Color"], color)
        self.put(b.inputs["Roughness"], rough)
        self.put(b.inputs["Metallic"], metal)
        if normal is not None:
            self.put(b.inputs["Normal"], normal)
        if emit is not None:
            self.put(b.inputs["Emission Color"], emit)
            b.inputs["Emission Strength"].default_value = emit_strength
        return self.mat


def new(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    return NB(m)


# ======================================================================================= recipes
def skin(name="HQ_Skin", base=(0.84, 0.6, 0.45), ruddy=(0.86, 0.47, 0.37), lips=(0.76, 0.42, 0.38), nails=(0.94, 0.82, 0.74),
         brow=((0.15, 0.09, 0.06), (0.3, 0.19, 0.12)), paint=(0.62, 0.13, 0.07), extra=()):
    """Skin: warm spots (attribute 'warm'), mottling, freckles; painted labels 1 nails, 2 lips, 3 mouth, 4 brows,
    5 war paint. `extra`: more labels as (label, colour, roughness), e.g. tar on a shaman's hands."""
    g = new(name)
    warm = g.attr("warm")
    p = g.obj()
    b = base
    c = g.mix(g.math("MULTIPLY", warm, 0.85), g.rgb(b), g.rgb(ruddy))
    mott = g.noise(p, 22.0, 4.0, 0.6)
    c = g.mix(g.remap(mott, 0.35, 0.65, 0.0, 0.12), c, g.rgb((b[0] * 0.833, b[1] * 0.75, b[2] * 0.756)))
    freck = g.smooth(g.noise(p, 140.0, 2.0, 0.5), 0.62, 0.7)
    c = g.mix(g.math("MULTIPLY", freck, 0.1), c, g.rgb((b[0] * 0.786, b[1] * 0.7, b[2] * 0.667)))
    # painted regions
    c = g.mix(g.math("MULTIPLY", g.reg(2), 0.6), c, g.rgb(lips))           # lips
    c = g.mix(g.reg(3), c, g.rgb((0.22, 0.05, 0.05)))                      # mouth
    c = g.mix(g.reg(1), c, g.rgb(nails))                                   # nails
    strands = g.noise(g.scale_vec(p, (40.0, 40.0, 140.0)), 1.0, 2.0, 0.5)
    brw = g.mix(g.remap(strands, 0.3, 0.7, 0.0, 1.0), g.rgb(brow[0]), g.rgb(brow[1]))
    c = g.mix(g.reg(4), c, brw)
    pm = g.math("MULTIPLY", g.reg(5), g.remap(g.noise(p, 45.0, 3.0, 0.6), 0.3, 0.7, 0.72, 0.97))
    c = g.mix(pm, c, g.rgb(paint))                                         # war paint
    rough = g.mixf(g.reg(2), g.mixf(g.reg(5), 0.55, 0.8), 0.4)
    for lab, col, rgh in extra:
        c = g.mix(g.reg(lab), c, g.rgb(col))
        rough = g.mixf(g.reg(lab), rough, rgh)
    h = g.math("ADD", g.math("MULTIPLY", g.noise(p, 180.0, 1.0, 0.5), 0.4), g.math("MULTIPLY", strands, g.reg(4)))
    return g.finish(c, rough, g.bump(h, 0.12, 0.002))


def eyes():
    g = new("HQ_Eyes")
    col = g.node("ShaderNodeVertexColor", layer_name="eyecol").outputs["Color"]
    return g.finish(col, 0.12)


def teeth():
    g = new("HQ_Teeth")
    p = g.obj()
    c = g.mix(g.noise(p, 60.0, 2.0), g.rgb((0.96, 0.93, 0.8)), g.rgb((0.85, 0.78, 0.6)))
    return g.finish(c, 0.3)


def hair(name="HQ_Hair", base=(0.25, 0.155, 0.095), hi=(0.52, 0.34, 0.2), low=None, streak=None, tint=None):
    """Hair: darker where it faces down, light on the ridges of the locks, fine strands. low/streak/tint default to the
    brown tones the first characters were baked with; light hair (white, grey) passes its own."""
    g = new(name)
    p = g.obj()
    point = g.geo("Pointiness")
    strands = g.noise(g.scale_vec(p, (70.0, 70.0, 16.0)), 1.0, 3.0, 0.55)
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    top = g.smooth(nz.outputs["Z"], -0.1, 0.9)
    c = g.mix(g.math("MULTIPLY", top, 0.55), g.rgb(low or (0.14, 0.085, 0.055)), g.rgb(base))
    ridge = g.smooth(point, 0.5, 0.56)
    c = g.mix(g.math("MULTIPLY", ridge, 0.7), c, g.rgb(hi))
    c = g.mix(g.remap(strands, 0.3, 0.7, 0.0, 0.4), c, g.rgb(streak or (0.12, 0.07, 0.045)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 4.0, 2.0), 0.45, 0.7), 0.3), c, g.rgb(tint or (0.36, 0.22, 0.13)))
    nrm = g.bump(strands, 0.35, 0.004)
    return g.finish(c, 0.6, nrm)


def pelt():
    g = new("HQ_Pelt")
    p = g.obj()
    warp = g.add_vec(p, g.scale_vec(g.noise(p, 5.0, 2.0, 0.5, out="Color"), 0.12))
    cell = g.voronoi(warp, 8.0, 1.0)
    size = g.remap(g.noise(p, 2.0, 1.0), 0.3, 0.7, 0.13, 0.27)
    spot = g.math("SUBTRACT", 1.0, g.smooth(g.math("SUBTRACT", cell, size), -0.02, 0.02))
    hole = g.math("SUBTRACT", 1.0, g.smooth(g.math("SUBTRACT", cell, g.math("MULTIPLY", size, 0.45)), -0.015, 0.015))
    broken = g.smooth(g.noise(p, 14.0, 2.0), 0.45, 0.55)
    ring_only = g.math("MULTIPLY", hole, g.math("GREATER_THAN", size, 0.21))
    dark = g.math("MULTIPLY", g.math("SUBTRACT", spot, ring_only, clamp=True), g.mixf(broken, 1.0, 0.75))
    base = g.mix(g.noise(p, 3.0, 2.0), g.rgb((0.84, 0.55, 0.24)), g.rgb((0.93, 0.69, 0.36)))
    strands = g.noise(g.scale_vec(p, (48.0, 48.0, 9.0)), 1.0, 3.0, 0.55)
    c = g.mix(g.remap(strands, 0.3, 0.7, 0.0, 0.35), base, g.rgb((0.62, 0.36, 0.14)))
    c = g.mix(g.math("MULTIPLY", ring_only, 0.5), c, g.rgb((0.66, 0.38, 0.15)))
    c = g.mix(g.math("MULTIPLY", dark, 0.9), c, g.rgb((0.25, 0.14, 0.07)))
    tips = g.smooth(g.geo("Pointiness"), 0.52, 0.6)
    c = g.mix(g.math("MULTIPLY", tips, 0.4), c, g.rgb((0.98, 0.84, 0.6)))
    nrm = g.bump(strands, 0.45, 0.006)
    return g.finish(c, 0.82, nrm)


def leather(name="HQ_Leather", base=(0.42, 0.25, 0.13)):
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 9.0, 3.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.25) for x in base)))
    worn = g.smooth(g.geo("Pointiness"), 0.51, 0.58)
    c = g.mix(g.math("MULTIPLY", worn, 0.6), c, g.rgb((0.66, 0.45, 0.27)))
    scr = g.smooth(g.noise(g.scale_vec(p, (120.0, 120.0, 30.0)), 1.0, 2.0), 0.62, 0.68)
    c = g.mix(g.math("MULTIPLY", scr, 0.35), c, g.rgb((0.2, 0.11, 0.06)))
    nrm = g.bump(g.math("ADD", g.noise(p, 90.0, 3.0), scr), 0.25, 0.003)
    return g.finish(c, 0.58, nrm)


def cord():
    g = new("HQ_Cord")
    p = g.obj()
    tw = g.wave(g.scale_vec(p, 1.0), 260.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.math("MULTIPLY", tw, 0.45), g.rgb((0.66, 0.5, 0.31)), g.rgb((0.4, 0.28, 0.16)))
    return g.finish(c, 0.75, g.bump(tw, 0.4, 0.002))


def bone(name="HQ_Bone", banded=False):
    g = new(name)
    p = g.obj()
    base = g.mix(g.noise(p, 7.0, 3.0), g.rgb((0.93, 0.88, 0.74)), g.rgb((0.84, 0.76, 0.6)))
    c = base
    h = g.noise(p, 60.0, 2.0)
    if banded:
        z = g.node("ShaderNodeSeparateXYZ")
        g.put(z.inputs[0], p)
        bands = g.wave(g.scale_vec(p, (0.0, 0.0, 1.0)), 9.0, 1.5, 2.0, "BANDS", "Z")
        c = g.mix(g.math("MULTIPLY", g.smooth(bands, 0.55, 0.85), 0.35), c, g.rgb((0.66, 0.56, 0.42)))
        dirt = g.math("SUBTRACT", 1.0, g.smooth(z.outputs["Z"], 0.25, 0.75))
        c = g.mix(g.math("MULTIPLY", dirt, 0.7), c, g.rgb((0.42, 0.32, 0.22)))
        h = g.math("ADD", h, g.math("MULTIPLY", bands, 0.6))
    crack = g.smooth(g.geo("Pointiness"), 0.42, 0.48)
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, crack), 0.35), c, g.rgb((0.55, 0.45, 0.32)))
    return g.finish(c, 0.45, g.bump(h, 0.25, 0.004))


def stone(name="HQ_Stone", moss=False, scale=1.0, paint=False):
    g = new(name)
    p = g.obj()
    macro = g.noise(p, 2.2 / scale, 3.0, 0.55)
    c = g.mix(g.remap(macro, 0.35, 0.65, 0.0, 1.0), g.rgb((0.5, 0.52, 0.56)), g.rgb((0.66, 0.64, 0.6)))
    speck = g.noise(p, 70.0 / scale, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.6, 0.66), 0.45), c, g.rgb((0.36, 0.37, 0.4)))
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.34, 0.28), 0.35), c, g.rgb((0.78, 0.77, 0.74)))
    edge = g.smooth(g.geo("Pointiness"), 0.51, 0.57)
    c = g.mix(g.math("MULTIPLY", edge, 0.55), c, g.rgb((0.8, 0.79, 0.76)))
    if moss:
        nz = g.node("ShaderNodeSeparateXYZ")
        g.put(nz.inputs[0], g.geo("Normal"))
        up = g.smooth(nz.outputs["Z"], 0.45, 0.8)
        patch = g.smooth(g.noise(p, 3.5, 4.0, 0.6), 0.48, 0.58)
        m = g.math("MULTIPLY", up, patch)
        mossc = g.mix(g.noise(p, 25.0, 3.0), g.rgb((0.3, 0.46, 0.15)), g.rgb((0.47, 0.6, 0.2)))
        c = g.mix(m, c, mossc)
    if paint:
        pm = g.math("MULTIPLY", g.reg(5), g.remap(g.noise(p, 30.0, 3.0, 0.6), 0.3, 0.7, 0.6, 0.92))
        c = g.mix(pm, c, g.rgb((0.66, 0.16, 0.08)))
    h = g.math("ADD", g.math("MULTIPLY", speck, 0.5), g.noise(p, 14.0 / scale, 4.0, 0.6))
    return g.finish(c, 0.78, g.bump(h, 0.35, 0.006))


def ground(name="HQ_Ground", dirt_label=None, tar_label=None):
    """Grass on top, layered dirt on the sides. `dirt_label`: a painted region of bare, trampled earth on top (an arena);
    `tar_label`: black, glossy tar stains."""
    g = new(name)
    p = g.obj()
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    pz = g.node("ShaderNodeSeparateXYZ")
    g.put(pz.inputs[0], p)
    top = g.math("MULTIPLY", g.smooth(nz.outputs["Z"], 0.45, 0.75), g.smooth(pz.outputs["Z"], 0.05, 0.14))
    if dirt_label is not None:
        bare = g.math("MULTIPLY", g.reg(dirt_label), g.smooth(nz.outputs["Z"], 0.3, 0.6))
        top = g.math("MULTIPLY", top, g.math("SUBTRACT", 1.0, bare))
    gr = g.mix(g.remap(g.noise(p, 2.5, 3.0), 0.35, 0.65, 0.0, 1.0), g.rgb((0.27, 0.48, 0.15)), g.rgb((0.46, 0.64, 0.22)))
    gr = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 9.0, 2.0), 0.55, 0.62), 0.5), gr, g.rgb((0.62, 0.72, 0.3)))
    blades = g.noise(g.scale_vec(p, (60.0, 60.0, 60.0)), 1.0, 2.0)
    gr = g.mix(g.math("MULTIPLY", blades, 0.35), gr, g.rgb((0.2, 0.36, 0.1)))
    dirt = g.mix(g.noise(p, 6.0, 3.0), g.rgb((0.36, 0.24, 0.15)), g.rgb((0.48, 0.33, 0.2)))
    strata = g.wave(p, 5.0, 3.0, 2.0, "BANDS", "Z")
    dirt = g.mix(g.math("MULTIPLY", g.smooth(strata, 0.6, 0.8), 0.3), dirt, g.rgb((0.26, 0.17, 0.1)))
    peb = g.smooth(g.voronoi(p, 26.0), 0.12, 0.08)
    dirt = g.mix(g.math("MULTIPLY", peb, 0.5), dirt, g.rgb((0.6, 0.55, 0.5)))
    rough = 0.9
    if dirt_label is not None:
        # trampled earth: lighter, dusty, with scuffs (no strata on a flat top)
        tr = g.mix(g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.5, 0.36, 0.23)), g.rgb((0.64, 0.49, 0.33)))
        scuff = g.smooth(g.noise(g.scale_vec(p, (14.0, 14.0, 2.0)), 1.0, 3.0, 0.6), 0.55, 0.68)
        tr = g.mix(g.math("MULTIPLY", scuff, 0.45), tr, g.rgb((0.4, 0.28, 0.17)))
        tr = g.mix(g.math("MULTIPLY", peb, 0.55), tr, g.rgb((0.66, 0.62, 0.56)))
        dirt = g.mix(bare, dirt, tr)
    c = g.mix(top, dirt, gr)
    if tar_label is not None:
        tar = g.reg(tar_label)
        c = g.mix(tar, c, g.mix(g.noise(p, 12.0, 2.0), g.rgb((0.05, 0.045, 0.05)), g.rgb((0.11, 0.09, 0.08))))
        rough = g.mixf(tar, 0.9, 0.18)
    h = g.math("ADD", g.math("MULTIPLY", blades, top), g.math("MULTIPLY", peb, g.math("SUBTRACT", 1.0, top)))
    return g.finish(c, rough, g.bump(h, 0.4, 0.006))


def basket():
    g = new("HQ_Basket")
    p = g.obj()
    c = g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.76, 0.58, 0.32)), g.rgb((0.62, 0.45, 0.23)))
    edge = g.smooth(g.geo("Pointiness"), 0.5, 0.56)
    c = g.mix(g.math("MULTIPLY", edge, 0.5), c, g.rgb((0.88, 0.74, 0.48)))
    return g.finish(c, 0.7, g.bump(g.noise(g.scale_vec(p, (200.0, 200.0, 40.0)), 1.0, 1.0), 0.2, 0.002))


def wood():
    g = new("HQ_Wood")
    p = g.obj()
    grain = g.wave(g.scale_vec(p, (1.0, 1.0, 0.08)), 30.0, 6.0, 3.0, "RINGS", "Z")
    c = g.mix(grain, g.rgb((0.46, 0.3, 0.17)), g.rgb((0.3, 0.19, 0.1)))
    return g.finish(c, 0.7, g.bump(grain, 0.3, 0.004))


def flame():
    g = new("HQ_Flame")
    pz = g.node("ShaderNodeSeparateXYZ")
    g.put(pz.inputs[0], g.obj())
    t = g.smooth(pz.outputs["Z"], 1.33, 1.62)
    c = g.mix(t, g.rgb((1.0, 0.45, 0.06)), g.rgb((1.0, 0.86, 0.36)))
    return g.finish(c, 0.5, emit=c, emit_strength=6.0)


def grass_blades():
    g = new("HQ_GrassBlades")
    uv = g.node("ShaderNodeUVMap")
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], uv.outputs["UV"])
    t = g.smooth(sep.outputs["Y"], 0.0, 1.0)
    c = g.mix(t, g.rgb((0.18, 0.36, 0.1)), g.rgb((0.58, 0.76, 0.3)))
    return g.finish(c, 0.7)


def flower(kind):
    cols = {0: (0.97, 0.96, 0.92), 1: (1.0, 0.86, 0.3), 2: (0.7, 0.55, 0.95), "c": (1.0, 0.7, 0.15), "s": (0.3, 0.5, 0.18)}
    g = new("HQ_Flower_%s" % kind)
    return g.finish(g.rgb(cols[kind]), 0.6)


def saber(name="HQ_Saber"):
    """Sabertooth hide (hood + cape): tawny fur with broken dark stripes (across the cat's head, horizontal down the
    cape), a darker dorsal line, cream muzzle, dark nose and paw pads, pink inner ears, amber stones for eyes and
    tanned suede on the inside."""
    g = new(name)
    region = g.attr("region")
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    X, Y, Z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    base = g.mix(g.remap(g.noise(p, 3.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.82, 0.47, 0.16)), g.rgb((0.93, 0.62, 0.26)))
    strands = g.noise(g.scale_vec(p, (60.0, 60.0, 15.0)), 1.0, 3.0, 0.55)
    c = g.mix(g.remap(strands, 0.3, 0.7, 0.0, 0.32), base, g.rgb((0.58, 0.3, 0.1)))
    warp = g.add_vec(p, g.scale_vec(g.noise(p, 3.5, 2.0, 0.5, out="Color"), 0.06))
    head_b = g.wave(warp, 5.0, 3.0, 2.0, "BANDS", "X")
    body_b = g.wave(warp, 3.2, 4.0, 2.0, "BANDS", "Z")
    on_head = g.smooth(Z, 1.66, 1.76)
    bands = g.mixf(on_head, body_b, head_b)
    stripe = g.smooth(bands, 0.8, 0.9)
    breakup = g.smooth(g.noise(p, 5.0, 2.0), 0.36, 0.52)
    ax = g.math("ABSOLUTE", X)
    edge_fade = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.smooth(ax, 0.24, 0.4), g.math("SUBTRACT", 1.0, on_head)))
    stripe = g.math("MULTIPLY", g.math("MULTIPLY", stripe, breakup), edge_fade)
    c = g.mix(g.math("MULTIPLY", stripe, 0.88), c, g.rgb((0.27, 0.13, 0.05)))
    dorsal = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(ax, 0.03, 0.12)), g.smooth(Y, 0.05, 0.2))
    c = g.mix(g.math("MULTIPLY", dorsal, 0.45), c, g.rgb((0.42, 0.22, 0.08)))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    under = g.smooth(nz.outputs["Z"], -0.2, -0.75)
    c = g.mix(g.math("MULTIPLY", under, 0.5), c, g.rgb((0.95, 0.82, 0.6)))
    tips = g.smooth(g.geo("Pointiness"), 0.52, 0.6)
    c = g.mix(g.math("MULTIPLY", tips, 0.35), c, g.rgb((1.0, 0.86, 0.62)))
    c = g.mix(g.reg(6), c, g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.97, 0.91, 0.78)), g.rgb((0.9, 0.8, 0.64))))   # muzzle
    c = g.mix(g.reg(7), c, g.rgb((0.22, 0.12, 0.1)))                                                       # nose pad
    amber = g.mix(g.smooth(Z, 2.015, 2.037), g.rgb((0.95, 0.5, 0.05)), g.rgb((1.0, 0.82, 0.3)))
    c = g.mix(g.reg(8), c, amber)                                                                          # amber eyes
    c = g.mix(g.reg(9), c, g.rgb((0.86, 0.6, 0.52)))                                                       # inner ears
    suede = g.mix(g.noise(p, 12.0, 3.0), g.rgb((0.62, 0.42, 0.26)), g.rgb((0.74, 0.54, 0.35)))
    c = g.mix(g.reg(10), c, suede)                                                                         # tanned inside
    c = g.mix(g.reg(11), c, g.rgb((0.3, 0.19, 0.16)))                                                      # paw pads
    rough = g.mixf(g.reg(8), g.mixf(g.reg(7), 0.82, 0.45), 0.12)
    furry = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("ADD", g.reg(8), g.reg(10))), strands)
    nrm = g.bump(g.math("ADD", furry, g.math("MULTIPLY", stripe, 0.15)), 0.4, 0.005)
    return g.finish(c, rough, nrm)


def fur(name="HQ_BrownFur", base=(0.34, 0.2, 0.11), tip=(0.6, 0.42, 0.26)):
    """Plain shaggy fur (bear): dark roots, lighter tips, fine strands."""
    g = new(name)
    p = g.obj()
    strands = g.noise(g.scale_vec(p, (60.0, 60.0, 14.0)), 1.0, 3.0, 0.55)
    c = g.mix(g.remap(g.noise(p, 4.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1.0, x * 1.25) for x in base)))
    c = g.mix(g.remap(strands, 0.3, 0.7, 0.0, 0.45), c, g.rgb(tuple(x * 0.55 for x in base)))
    tips = g.smooth(g.geo("Pointiness"), 0.51, 0.6)
    c = g.mix(g.math("MULTIPLY", tips, 0.55), c, g.rgb(tip))
    return g.finish(c, 0.85, g.bump(strands, 0.45, 0.006))


def dais(name="HQ_Dais"):
    """Carved granite: light speckled stone, darker in the chisel marks, red ochre paint (label 5)."""
    g = new(name)
    p = g.obj()
    macro = g.noise(p, 2.6, 3.0, 0.55)
    c = g.mix(g.remap(macro, 0.35, 0.65, 0.0, 1.0), g.rgb((0.58, 0.56, 0.54)), g.rgb((0.72, 0.69, 0.64)))
    speck = g.noise(p, 90.0, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.6, 0.66), 0.5), c, g.rgb((0.36, 0.35, 0.36)))
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.34, 0.28), 0.4), c, g.rgb((0.86, 0.84, 0.8)))
    edge = g.smooth(g.geo("Pointiness"), 0.51, 0.57)
    c = g.mix(g.math("MULTIPLY", edge, 0.5), c, g.rgb((0.88, 0.86, 0.82)))
    groove = g.smooth(g.geo("Pointiness"), 0.47, 0.42)
    c = g.mix(g.math("MULTIPLY", groove, 0.55), c, g.rgb((0.3, 0.28, 0.27)))
    paint = g.math("MULTIPLY", g.reg(5), g.remap(g.noise(p, 30.0, 3.0, 0.6), 0.3, 0.7, 0.65, 0.95))
    c = g.mix(paint, c, g.rgb((0.66, 0.16, 0.08)))
    h = g.math("ADD", g.math("MULTIPLY", speck, 0.4), g.noise(p, 16.0, 4.0, 0.6))
    return g.finish(c, g.mixf(paint, 0.72, 0.85), g.bump(h, 0.3, 0.005))


def amber(name="HQ_Amber"):
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 40.0, 3.0), g.rgb((1.0, 0.62, 0.08)), g.rgb((1.0, 0.85, 0.35)))
    return g.finish(c, 0.15, emit=c, emit_strength=0.6)


def fang(name="HQ_Fang"):
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    c = g.mix(g.noise(p, 40.0, 2.0), g.rgb((0.97, 0.94, 0.86)), g.rgb((0.9, 0.84, 0.7)))
    root = g.smooth(sep.outputs["Z"], 1.84, 1.93)
    c = g.mix(g.math("MULTIPLY", root, 0.6), c, g.rgb((0.78, 0.66, 0.45)))
    h = g.noise(g.scale_vec(p, (30.0, 30.0, 120.0)), 1.0, 2.0)
    return g.finish(c, 0.32, g.bump(h, 0.15, 0.002))


def feather(name="HQ_Feather"):
    """White feathers with fine barbs, an ochre band and dark tips (position along the feather from its base)."""
    g = new(name)
    p = g.obj()
    d = g.node("ShaderNodeVectorMath", operation="DISTANCE")
    g.put(d.inputs[0], p)
    d.inputs[1].default_value = (0.205, 0.085, 2.005)
    t = g.math("DIVIDE", d.outputs["Value"], 0.27)
    c = g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.98, 0.97, 0.93)), g.rgb((0.9, 0.88, 0.82)))
    band = g.math("MULTIPLY", g.smooth(t, 0.52, 0.56), g.math("SUBTRACT", 1.0, g.smooth(t, 0.66, 0.7)))
    c = g.mix(band, c, g.rgb((0.85, 0.42, 0.12)))
    c = g.mix(g.smooth(t, 0.8, 0.86), c, g.rgb((0.18, 0.11, 0.08)))
    barbs = g.wave(g.scale_vec(p, 1.0), 120.0, 2.0, 1.0, "BANDS", "DIAGONAL")
    c = g.mix(g.math("MULTIPLY", g.smooth(barbs, 0.6, 0.9), 0.18), c, g.rgb((0.5, 0.45, 0.4)))
    return g.finish(c, 0.6, g.bump(barbs, 0.2, 0.0015))


def cloth(name="HQ_RedCloth", col=(0.78, 0.13, 0.08)):
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(g.scale_vec(p, (80.0, 80.0, 20.0)), 1.0, 2.0), g.rgb(col), g.rgb(tuple(x * 0.62 for x in col)))
    return g.finish(c, 0.85, g.bump(g.noise(g.scale_vec(p, (200.0, 200.0, 40.0)), 1.0, 1.0), 0.2, 0.002))


def wolf(name="HQ_Wolf", sash_c=(0.06, 0.03, 1.2), sash_n=(0.697, 0.0, -0.717)):
    """Grey wolf hide: grizzled grey fur with a darker saddle down the middle of the hide strip (its spine) fading to
    cream at the edges, a dark cap on the head, cream muzzle (label 11), black nose and lips (7), pink inner ears (8),
    dark eye holes (9) and tanned suede on the inside (10)."""
    g = new(name)
    p = g.obj()
    strands = g.noise(g.scale_vec(p, (60.0, 60.0, 15.0)), 1.0, 3.0, 0.55)
    base = g.mix(g.remap(g.noise(p, 3.5, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.56, 0.55, 0.53)), g.rgb((0.68, 0.64, 0.58)))
    c = g.mix(g.remap(strands, 0.3, 0.7, 0.0, 0.5), base, g.rgb((0.3, 0.29, 0.29)))
    # distance from the middle of the hide strip: dark saddle in the middle, light belly fur at the edges
    rel = g.node("ShaderNodeVectorMath", operation="SUBTRACT")
    g.put(rel.inputs[0], p)
    rel.inputs[1].default_value = sash_c
    dp = g.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    g.put(dp.inputs[0], rel.outputs[0])
    dp.inputs[1].default_value = sash_n
    d = g.math("ABSOLUTE", dp.outputs["Value"])
    wob = g.remap(g.noise(p, 6.0, 2.0), 0.3, 0.7, -0.025, 0.025)
    d = g.math("ADD", d, wob)
    saddle = g.math("SUBTRACT", 1.0, g.smooth(d, 0.03, 0.1))
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    on_head = g.math("MULTIPLY", g.smooth(sep.outputs["Z"], 1.52, 1.62), g.smooth(sep.outputs["X"], 0.3, 0.38))
    saddle = g.mixf(on_head, saddle, 0.0)
    c = g.mix(g.math("MULTIPLY", saddle, 0.75), c, g.mix(strands, g.rgb((0.2, 0.19, 0.19)), g.rgb((0.36, 0.33, 0.3))))
    belly = g.math("MULTIPLY", g.smooth(d, 0.1, 0.16), g.math("SUBTRACT", 1.0, on_head))
    c = g.mix(g.math("MULTIPLY", belly, 0.7), c, g.rgb((0.9, 0.86, 0.78)))
    # head: dark cap and brows, lighter cheeks below
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    cap = g.math("MULTIPLY", on_head, g.smooth(nz.outputs["Z"], 0.55, 0.9))
    c = g.mix(g.math("MULTIPLY", cap, 0.55), c, g.rgb((0.32, 0.3, 0.29)))
    under = g.math("MULTIPLY", on_head, g.smooth(nz.outputs["Z"], -0.1, -0.6))
    c = g.mix(g.math("MULTIPLY", under, 0.6), c, g.rgb((0.9, 0.86, 0.78)))
    tips = g.smooth(g.geo("Pointiness"), 0.52, 0.6)
    c = g.mix(g.math("MULTIPLY", tips, 0.4), c, g.rgb((0.95, 0.93, 0.88)))
    c = g.mix(g.reg(11), c, g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.93, 0.9, 0.84)), g.rgb((0.8, 0.76, 0.7))))   # muzzle
    c = g.mix(g.reg(7), c, g.rgb((0.07, 0.06, 0.06)))                                                     # nose, lips
    c = g.mix(g.reg(8), c, g.rgb((0.82, 0.58, 0.55)))                                                     # inner ears
    c = g.mix(g.reg(9), c, g.rgb((0.1, 0.07, 0.06)))                                                      # eye holes
    suede = g.mix(g.noise(p, 12.0, 3.0), g.rgb((0.6, 0.45, 0.32)), g.rgb((0.72, 0.56, 0.4)))
    c = g.mix(g.reg(10), c, suede)
    rough = g.mixf(g.reg(7), 0.85, 0.35)
    furry = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("ADD", g.reg(7), g.reg(10))), strands)
    return g.finish(c, rough, g.bump(furry, 0.42, 0.005))


def club_wood(name="HQ_ClubWood"):
    """Heavy club log: dark bark with grain running along the club, knots, paler worn ridges."""
    g = new(name)
    p = g.obj()
    grain = g.noise(g.scale_vec(p, (55.0, 4.0, 55.0)), 1.0, 4.0, 0.6)
    c = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb((0.3, 0.19, 0.11)), g.rgb((0.5, 0.34, 0.2)))
    cracks = g.smooth(g.noise(g.scale_vec(p, (90.0, 6.0, 90.0)), 1.0, 2.0, 0.5), 0.6, 0.7)
    c = g.mix(g.math("MULTIPLY", cracks, 0.6), c, g.rgb((0.16, 0.1, 0.06)))
    worn = g.smooth(g.geo("Pointiness"), 0.51, 0.57)
    c = g.mix(g.math("MULTIPLY", worn, 0.55), c, g.rgb((0.66, 0.5, 0.33)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 2.0), 0.5, 0.7), 0.25), c, g.rgb((0.36, 0.3, 0.2)))
    return g.finish(c, 0.72, g.bump(g.math("ADD", grain, g.math("MULTIPLY", cracks, 1.5)), 0.45, 0.006))


def flint(name="HQ_Flint"):
    """Knapped flint: dark blue-grey to brown-black, glassy, with pale chipped edges and conchoidal ripples."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 12.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.16, 0.16, 0.19)), g.rgb((0.32, 0.29, 0.27)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 30.0, 2.0), 0.55, 0.65), 0.5), c, g.rgb((0.42, 0.44, 0.5)))
    edge = g.smooth(g.geo("Pointiness"), 0.52, 0.6)
    c = g.mix(g.math("MULTIPLY", edge, 0.75), c, g.rgb((0.78, 0.76, 0.72)))
    ripple = g.wave(g.scale_vec(p, 1.0), 90.0, 3.0, 1.0, "RINGS", "SPHERICAL")
    return g.finish(c, 0.3, g.bump(ripple, 0.25, 0.002))


def horn(name="HQ_Horn", centre=(0.0, -0.2, 1.86), r0=0.24, r1=0.62):
    """Aurochs horn: creamy grey at the base darkening to black tips (distance from `centre`), with fine lengthwise
    streaks and growth ridges."""
    g = new(name)
    p = g.obj()
    d = g.node("ShaderNodeVectorMath", operation="DISTANCE")
    g.put(d.inputs[0], p)
    d.inputs[1].default_value = centre
    t = g.smooth(d.outputs["Value"], r0, r1)
    streak = g.noise(g.scale_vec(p, (25.0, 25.0, 25.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(streak, 0.3, 0.7, 0.0, 1.0), g.rgb((0.8, 0.75, 0.64)), g.rgb((0.66, 0.6, 0.5)))
    c = g.mix(g.math("MULTIPLY", t, 0.95), c, g.rgb((0.12, 0.1, 0.09)))
    ridge = g.wave(g.scale_vec(p, 1.0), 60.0, 2.0, 1.0, "RINGS", "SPHERICAL")
    return g.finish(c, g.mixf(t, 0.45, 0.3), g.bump(g.math("ADD", streak, g.math("MULTIPLY", ridge, 0.4)), 0.25, 0.003))


def robe(name="HQ_Robe", base=(0.36, 0.2, 0.47), hi=(0.48, 0.29, 0.6)):
    """Purple-dyed hide: mottled dye, darker in the folds, worn pale on the edges, ochre dots (label 5), tar stains (7)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(hi))
    blot = g.smooth(g.noise(p, 2.5, 2.0), 0.5, 0.7)
    c = g.mix(g.math("MULTIPLY", blot, 0.35), c, g.rgb(tuple(x * 0.7 for x in base)))
    fold = g.smooth(g.geo("Pointiness"), 0.48, 0.42)
    c = g.mix(g.math("MULTIPLY", fold, 0.5), c, g.rgb(tuple(x * 0.55 for x in base)))
    worn = g.smooth(g.geo("Pointiness"), 0.52, 0.6)
    c = g.mix(g.math("MULTIPLY", worn, 0.5), c, g.rgb((0.66, 0.52, 0.66)))
    och = g.math("MULTIPLY", g.reg(5), g.remap(g.noise(p, 40.0, 2.0), 0.3, 0.7, 0.75, 1.0))
    c = g.mix(och, c, g.rgb((0.88, 0.6, 0.2)))
    tar = g.reg(7)
    c = g.mix(tar, c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.05, 0.045, 0.05)), g.rgb((0.12, 0.1, 0.1))))
    rough = g.mixf(tar, 0.82, 0.15)
    h = g.math("ADD", g.noise(p, 50.0, 3.0), g.math("MULTIPLY", tar, 0.3))
    return g.finish(c, rough, g.bump(h, 0.25, 0.004))


def tar(name="HQ_Tar"):
    """Pitch-black tar: glossy, with brown-amber depths showing through where it is thin and a faint oily rainbow."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 4.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.04, 0.035, 0.035)), g.rgb((0.12, 0.08, 0.05)))
    swirl = g.wave(g.add_vec(p, g.scale_vec(g.noise(p, 3.0, 2.0, 0.5, out="Color"), 0.3)), 9.0, 6.0, 2.0, "BANDS", "X")
    c = g.mix(g.math("MULTIPLY", g.smooth(swirl, 0.75, 0.95), 0.25), c, g.rgb((0.22, 0.14, 0.24)))
    return g.finish(c, 0.08, g.bump(g.noise(p, 25.0, 2.0), 0.08, 0.002))


def glow_ball(name="HQ_GlowBall", col=(0.42, 1.0, 0.52), strength=3.0):
    """Preview stand-in for parts shipped as glowing meshes (spirit stones)."""
    g = new(name)
    return g.finish(g.rgb(col), 0.25, emit=g.rgb(col), emit_strength=strength)


def quartz(name="HQ_Quartz", col=(0.62, 0.36, 0.92), strength=1.2):
    """Purple quartz points: glassy violet, paler towards the tips, glowing softly (shipped as a glow mesh in game)."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    c = g.mix(g.remap(g.noise(p, 18.0, 2.0), 0.35, 0.65, 0.0, 1.0), g.rgb(col), g.rgb((0.84, 0.66, 1.0)))
    return g.finish(c, 0.12, emit=c, emit_strength=strength)


def outline_mat():
    """Inverted-hull outline for Cycles: black on back faces, invisible on front faces."""
    m = bpy.data.materials.get("HQ_Outline") or bpy.data.materials.new("HQ_Outline")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin((0.09, 0.06, 0.05))
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], mx.inputs[0])
    nt.links.new(em.outputs[0], mx.inputs[1])        # front faces of the flipped shell = the outline
    nt.links.new(tr.outputs[0], mx.inputs[2])        # back faces (nearest the camera) = invisible
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m.use_backface_culling = False
    return m


ASSIGN = {
    "Skin": skin, "Eyes": eyes, "Teeth": teeth, "Hair": lambda: hair("HQ_Hair"), "Beard": lambda: hair("HQ_Beard"),
    "Pelt": pelt, "Leather": leather, "Sling": lambda: leather("HQ_SlingLeather", (0.46, 0.28, 0.15)),
    "BaseLeather": lambda: leather("HQ_BaseLeather", (0.4, 0.24, 0.12)), "Cord": cord, "Bone": bone,
    "Tusks": lambda: bone("HQ_Tusk", banded=True), "BagStones": lambda: stone("HQ_HandStone", scale=0.3),
    "SlingStone": lambda: stone("HQ_HandStone", scale=0.3), "AmmoStones": lambda: stone("HQ_AmmoStone", scale=0.3),
    "Pebbles": lambda: stone("HQ_Pebble", scale=0.3), "Rocks": lambda: stone("HQ_Rock", moss=True),
    "Ground": ground, "Basket": basket, "Wood": wood, "Flame": flame, "Grass": grass_blades,
    "Hood": saber, "Cape": saber, "Fangs": fang, "Feather": feather, "Cloth": cloth, "Dais": dais, "Amber": amber,
    "Wolf": wolf, "Club": club_wood, "Flint": flint, "Rope": cord, "Quartz": quartz,
}


def assign_all(objs, overrides=None):
    """overrides: part -> (recipe name in this module, kwargs), e.g. a darker beard for one character."""
    cache = {}
    overrides = overrides or {}
    for o in objs:
        key = o.name.split(".")[0]
        if key not in ASSIGN and key not in overrides:
            continue
        if key not in cache:
            if key in overrides:
                fn, kw = overrides[key]
                cache[key] = globals()[fn](**kw)
            else:
                cache[key] = ASSIGN[key]()
        o.data.materials.clear()
        o.data.materials.append(cache[key])
