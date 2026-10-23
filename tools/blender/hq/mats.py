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
    for e in extra:                                                        # (label, colour, roughness[, strength])
        lab, col, rgh = e[:3]
        m = g.reg(lab) if len(e) < 4 else g.math("MULTIPLY", g.reg(lab), e[3])
        c = g.mix(m, c, g.rgb(col))
        rough = g.mixf(m, rough, rgh)
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


def hair(name="HQ_Hair", base=(0.25, 0.155, 0.095), hi=(0.52, 0.34, 0.2), low=None, streak=None, tint=None, fleck=None,
         fleck_amt=0.5):
    """Hair: darker where it faces down, light on the ridges of the locks, fine strands. low/streak/tint default to the
    brown tones the first characters were baked with; light hair (white, grey) passes its own. `fleck`: a colour for
    scattered strands through it (grey flecks in a black beard), `fleck_amt` how much of it."""
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
    if fleck is not None:
        fl = g.smooth(g.noise(g.scale_vec(p, (55.0, 55.0, 12.0)), 1.0, 2.0, 0.5), 0.6, 0.66)
        fl = g.math("MULTIPLY", fl, g.smooth(g.noise(p, 6.0, 2.0), 0.35, 0.6))
        c = g.mix(g.math("MULTIPLY", fl, fleck_amt), c, g.rgb(fleck))
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


def leather_dyed(name="HQ_DyedLeather", base=(0.42, 0.25, 0.13), dyed=(0.6, 0.12, 0.08), worn_c=(0.66, 0.45, 0.27)):
    """Leather (label 0) with red-dyed pieces (5) and bronze studs (6), worn pale on the edges (`worn_c`: black leather
    wears grey, not tan)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 9.0, 3.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.25) for x in base)))
    red = g.mix(g.noise(p, 9.0, 3.0), g.rgb(dyed), g.rgb(tuple(x * 0.72 for x in dyed)))
    c = g.mix(g.reg(5), c, red)
    pt = g.geo("Pointiness")
    worn = g.smooth(pt, 0.51, 0.58)
    c = g.mix(g.math("MULTIPLY", worn, 0.5), c, g.rgb(worn_c))
    scr = g.smooth(g.noise(g.scale_vec(p, (120.0, 120.0, 30.0)), 1.0, 2.0), 0.62, 0.68)
    c = g.mix(g.math("MULTIPLY", scr, 0.35), c, g.rgb((0.2, 0.11, 0.06)))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.74, 0.48, 0.2)), g.rgb((1.0, 0.84, 0.54)))
    c = g.mix(g.reg(6), c, br)
    nrm = g.bump(g.math("ADD", g.noise(p, 90.0, 3.0), scr), 0.25, 0.003)
    return g.finish(c, g.mixf(g.reg(6), 0.58, 0.3), nrm)


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


# ======================================================================================= Bronze Age (v0.9.21)
def bronze(name="HQ_Bronze", base=(0.7, 0.44, 0.19), hi=(0.98, 0.8, 0.5), dark=(0.3, 0.17, 0.08), patina=(0.3, 0.56, 0.48),
           gilt=None):
    """Polished bronze, hand-painted: warm golden brown, bright on edges and ridges and on faces turned to the sky, dark in
    the recesses, a little green patina in the deepest crevices, fine hammer marks. (Baked: there is no metal channel.)
    `gilt`: a sculpt label painted gold (trim on a helmet)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1.0, x * 1.15) for x in base)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.75), c, g.rgb(hi))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), c, g.rgb(dark))
    pat = g.math("MULTIPLY", g.smooth(pt, 0.46, 0.41), g.smooth(g.noise(p, 12.0, 3.0), 0.5, 0.64))
    c = g.mix(g.math("MULTIPLY", pat, 0.7), c, g.rgb(patina))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    c = g.mix(g.math("MULTIPLY", g.smooth(nz.outputs["Z"], 0.3, 0.95), 0.28), c, g.rgb(hi))
    if gilt is not None:
        gc = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.75), g.rgb((0.88, 0.66, 0.2)), g.rgb((1.0, 0.93, 0.64)))
        gc = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.55), gc, g.rgb((0.44, 0.28, 0.06)))
        c = g.mix(g.reg(gilt), c, gc)
    ham = g.voronoi(p, 90.0, 1.0, "F1", "Distance")
    h = g.math("ADD", g.math("MULTIPLY", ham, 0.3), g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.2))
    return g.finish(c, g.mixf(pat, 0.3, 0.7), g.bump(h, 0.12, 0.002))


def gold(name="HQ_Gold"):
    return bronze(name, base=(0.86, 0.64, 0.2), hi=(1.0, 0.92, 0.62), dark=(0.42, 0.26, 0.06), patina=(0.62, 0.48, 0.16))


def linen(name="HQ_Linen", base=(0.93, 0.9, 0.82), border=(0.74, 0.13, 0.08), stripe=(0.16, 0.3, 0.64)):
    """Bleached linen: off-white with a fine weave, grey-ochre in the folds; label 5 = a woven red border, 6 = a blue stripe."""
    g = new(name)
    p = g.obj()
    weave = g.math("ADD", g.wave(p, 420.0, 0.0, 0.0, "BANDS", "X"), g.wave(p, 420.0, 0.0, 0.0, "BANDS", "Z"))
    c = g.mix(g.remap(g.noise(p, 8.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb((0.85, 0.81, 0.71)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.49, 0.43), 0.55), c, g.rgb((0.6, 0.56, 0.48)))
    bc = g.mix(g.math("MULTIPLY", g.smooth(g.wave(p, 160.0, 0.0, 0.0, "BANDS", "Z"), 0.4, 0.6), 0.35), g.rgb(border), g.rgb((0.95, 0.75, 0.3)))
    c = g.mix(g.reg(5), c, bc)
    c = g.mix(g.reg(6), c, g.rgb(stripe))
    return g.finish(c, 0.86, g.bump(weave, 0.12, 0.0012))


def bow(name="HQ_Bow"):
    """Composite bow: dark red-brown lacquered limbs with a cream horn belly (label 7), red cord wrapped round the grip
    (5), bronze tip caps (6)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(g.scale_vec(p, (25.0, 25.0, 25.0)), 1.0, 2.0), g.rgb((0.32, 0.12, 0.07)), g.rgb((0.48, 0.2, 0.11)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.5), c, g.rgb((0.66, 0.36, 0.2)))
    horn = g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.9, 0.84, 0.68)), g.rgb((0.74, 0.64, 0.46)))
    c = g.mix(g.reg(7), c, horn)
    tw = g.wave(p, 320.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(5), c, g.mix(g.math("MULTIPLY", tw, 0.6), g.rgb((0.78, 0.15, 0.09)), g.rgb((0.46, 0.07, 0.05))))
    c = g.mix(g.reg(6), c, g.rgb((0.9, 0.64, 0.32)))
    rough = g.mixf(g.reg(6), g.mixf(g.reg(5), 0.32, 0.8), 0.28)
    return g.finish(c, rough, g.bump(g.math("MULTIPLY", tw, g.reg(5)), 0.3, 0.002))


def yew_bow(name="HQ_Longbow", sap=(0.88, 0.76, 0.54), heart=(0.66, 0.32, 0.12), grip=(0.24, 0.14, 0.08), horn=(0.86, 0.8, 0.66)):
    """A yew self bow: the orange-brown heartwood of the belly (label 0) with a fine grain along the limbs and a few
    darker pin knots; the pale sapwood of the back (7); a leather grip (5); horn nocks (6)."""
    g = new(name)
    p = g.obj()
    grain = g.noise(g.scale_vec(p, (12.0, 12.0, 160.0)), 1.0, 3.0, 0.5)
    c = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb(heart), g.rgb(tuple(x * 0.78 for x in heart)))
    knots = g.smooth(g.noise(p, 26.0, 2.0), 0.7, 0.76)
    c = g.mix(g.math("MULTIPLY", knots, 0.6), c, g.rgb(tuple(x * 0.5 for x in heart)))
    sw = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb(sap), g.rgb(tuple(x * 0.9 for x in sap)))
    c = g.mix(g.reg(7), c, sw)
    tw = g.wave(p, 300.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(5), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb(grip), g.rgb(tuple(x * 0.7 for x in grip))))
    c = g.mix(g.reg(6), c, g.mix(g.noise(p, 40.0, 2.0), g.rgb(horn), g.rgb(tuple(x * 0.85 for x in horn))))
    rough = g.mixf(g.reg(5), g.mixf(g.reg(6), 0.42, 0.3), 0.75)
    return g.finish(c, rough, g.bump(g.math("ADD", g.math("MULTIPLY", grain, 0.3), g.math("MULTIPLY", tw, g.reg(5))), 0.25, 0.0015))


def arrows(name="HQ_Arrows", shaft=((0.76, 0.6, 0.34), (0.6, 0.44, 0.24)), head=(0.9, 0.62, 0.3), head_rough=0.3,
           fletch=((0.86, 0.14, 0.08), (0.97, 0.95, 0.9)), crest=None, crest2=None, head_hi=None):
    """Reed shafts (label 0 / 7), leaf-shaped bronze heads (6), red and white fletching (8); optionally painted cresting
    bands on the shafts (5 `crest`, 9 `crest2`). Medieval: ash shafts, steel bodkins, grey goose feathers."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(g.scale_vec(p, (70.0, 70.0, 12.0)), 1.0, 2.0), g.rgb(shaft[0]), g.rgb(shaft[1]))
    hc = g.rgb(head) if head_hi is None else g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.5, 0.56), 0.7), g.rgb(head), g.rgb(head_hi))
    c = g.mix(g.reg(6), c, hc)
    split = g.smooth(g.noise(p, 22.0, 1.0), 0.47, 0.53)
    c = g.mix(g.reg(8), c, g.mix(split, g.rgb(fletch[0]), g.rgb(fletch[1])))
    if crest is not None:
        c = g.mix(g.reg(5), c, g.rgb(crest))
    if crest2 is not None:
        c = g.mix(g.reg(9), c, g.rgb(crest2))
    return g.finish(c, g.mixf(g.reg(6), 0.62, head_rough))


def quiver(name="HQ_Quiver", base=(0.56, 0.16, 0.09), band=(0.9, 0.62, 0.2), rim=(0.88, 0.6, 0.3), shaft=(0.74, 0.58, 0.33),
           fletch=((0.86, 0.14, 0.08), (0.97, 0.95, 0.9)), crest2=(0.72, 0.12, 0.08), worn=(0.78, 0.45, 0.3), scratch=(0.22, 0.06, 0.04)):
    """Dyed leather quiver: `band`s (label 5), a metal rim (6), the arrows' shafts (7) and fletching (8), a second
    cresting colour on the shafts (9)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 9.0, 3.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.3) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.58), 0.55), c, g.rgb(worn))
    scr = g.smooth(g.noise(g.scale_vec(p, (120.0, 120.0, 30.0)), 1.0, 2.0), 0.62, 0.68)
    c = g.mix(g.math("MULTIPLY", scr, 0.35), c, g.rgb(scratch))
    c = g.mix(g.reg(5), c, g.rgb(band))
    c = g.mix(g.reg(6), c, g.rgb(rim))
    c = g.mix(g.reg(7), c, g.rgb(shaft))
    split = g.smooth(g.noise(p, 22.0, 1.0), 0.47, 0.53)
    c = g.mix(g.reg(8), c, g.mix(split, g.rgb(fletch[0]), g.rgb(fletch[1])))
    c = g.mix(g.reg(9), c, g.rgb(crest2))
    return g.finish(c, g.mixf(g.reg(6), 0.6, 0.3), g.bump(g.math("ADD", g.noise(p, 90.0, 3.0), scr), 0.2, 0.003))


def mudbrick(name="HQ_Mudbrick", base=(0.72, 0.56, 0.38), mortar=(0.56, 0.42, 0.28), glaze=(0.16, 0.36, 0.7), course=0.085, brick=0.2):
    """Sun-dried mud brick: courses of bricks (staggered joints sunk a little in the normal map), straw flecks, weathered
    edges; label 5 = a band of blue glazed bricks, 6 = yellow-white glaze (rosettes, trim), 7 = whitewash plaster."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    z = sep.outputs["Z"]
    row = g.math("FLOOR", g.math("DIVIDE", z, course))
    fz = g.math("SUBTRACT", g.math("DIVIDE", z, course), row)
    run = g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), g.math("MULTIPLY", g.math("MODULO", row, 2.0), brick * 0.5))
    fx = g.math("FRACT", g.math("DIVIDE", run, brick))
    jz = g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz))
    jx = g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx))
    joint = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.smooth(jz, 0.04, 0.12)), g.math("SUBTRACT", 1.0, g.smooth(jx, 0.02, 0.06)))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    # (no courses drawn across flat tops: a roof or a tread is plastered, and the courses' x+y runs drew diagonal stripes)
    joint = g.math("MULTIPLY", joint, g.math("SUBTRACT", 1.0, g.smooth(nz.outputs["Z"], 0.7, 0.9)))
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.12) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 45.0, 2.0), 0.6, 0.68), 0.35), c, g.rgb((0.86, 0.74, 0.46)))   # straw
    c = g.mix(joint, c, g.rgb(mortar))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.45), c, g.rgb((0.84, 0.72, 0.54)))
    gl = g.mix(g.noise(p, 20.0, 2.0), g.rgb(glaze), g.rgb(tuple(min(1, x * 1.35) for x in glaze)))
    c = g.mix(g.math("MULTIPLY", g.reg(5), g.math("SUBTRACT", 1.0, g.math("MULTIPLY", joint, 0.7))), c, gl)
    c = g.mix(g.reg(6), c, g.rgb((0.96, 0.86, 0.5)))
    c = g.mix(g.math("MULTIPLY", g.reg(7), 0.9), c, g.rgb((0.9, 0.86, 0.76)))
    rough = g.mixf(g.math("MAXIMUM", g.reg(5), g.reg(6)), 0.88, 0.25)
    h = g.math("ADD", g.math("MULTIPLY", joint, -0.6), g.math("MULTIPLY", g.noise(p, 30.0, 3.0), 0.35))
    return g.finish(c, rough, g.bump(h, 0.35, 0.006))


def terracotta(name="HQ_Terracotta", base=(0.72, 0.36, 0.2), paint=(0.15, 0.1, 0.08)):
    """Fired clay: orange-red with darker firing clouds, pale on worn rims; label 5 = black painted bands."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 4.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb((0.58, 0.28, 0.16)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.5), c, g.rgb((0.86, 0.6, 0.42)))
    c = g.mix(g.reg(5), c, g.rgb(paint))
    return g.finish(c, 0.7, g.bump(g.noise(p, 60.0, 2.0), 0.1, 0.002))


def reed(name="HQ_Reed", base=(0.66, 0.6, 0.36)):
    """Dried reed bundles and mats: pale straw with fine lengthwise fibres and darker bindings (label 5)."""
    g = new(name)
    p = g.obj()
    fib = g.wave(p, 220.0, 2.0, 1.0, "BANDS", "X")
    c = g.mix(g.math("MULTIPLY", fib, 0.5), g.rgb(base), g.rgb((0.48, 0.42, 0.24)))
    c = g.mix(g.reg(5), c, g.rgb((0.36, 0.22, 0.12)))
    return g.finish(c, 0.8, g.bump(fib, 0.25, 0.002))


def coals(name="HQ_Coals"):
    """Burning charcoal: black lumps split by glowing orange cracks, ash-grey on the edges (the glow is painted in)."""
    g = new(name)
    p = g.obj()
    cr = g.voronoi(p, 45.0, 1.0, "DISTANCE_TO_EDGE", "Distance")
    hot = g.math("MULTIPLY", g.smooth(cr, 0.06, 0.0), g.smooth(g.noise(p, 9.0, 2.0), 0.4, 0.6))
    c = g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.07, 0.06, 0.06)), g.rgb((0.16, 0.14, 0.13)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.58), 0.6), c, g.rgb((0.5, 0.48, 0.46)))
    c = g.mix(hot, c, g.mix(g.noise(p, 20.0, 1.0), g.rgb((1.0, 0.36, 0.06)), g.rgb((1.0, 0.72, 0.2))))
    return g.finish(c, 0.9, g.bump(g.math("MULTIPLY", cr, 2.0), 0.3, 0.003))


def wool(name="HQ_Wool", base=(0.66, 0.12, 0.08), border=(0.92, 0.86, 0.72), stripe=(0.12, 0.11, 0.14)):
    """Dyed wool: a coarse weave, darker in the folds, lighter fuzz on the ridges; label 5 = a woven border with a
    zigzag, 6 = a dark stripe."""
    g = new(name)
    p = g.obj()
    weave = g.math("ADD", g.wave(p, 260.0, 0.0, 0.0, "BANDS", "X"), g.wave(p, 260.0, 0.0, 0.0, "BANDS", "Z"))
    dark = tuple(x * 0.72 for x in base)
    c = g.mix(g.remap(g.noise(p, 7.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(dark))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.49, 0.43), 0.6), c, g.rgb(tuple(x * 0.55 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.35), c, g.rgb(tuple(min(1, x * 1.3 + 0.05) for x in base)))
    zz = g.smooth(g.wave(p, 90.0, 0.0, 0.0, "BANDS", "DIAGONAL", "TRI"), 0.45, 0.55)
    bc = g.mix(g.math("MULTIPLY", zz, 0.5), g.rgb(border), g.rgb(tuple(x * 0.8 for x in border)))
    c = g.mix(g.reg(5), c, bc)
    c = g.mix(g.reg(6), c, g.rgb(stripe))
    return g.finish(c, 0.92, g.bump(weave, 0.18, 0.0015))


def spear_shaft(name="HQ_Spear"):
    """Ash spear shaft (pale wood, fine grain along it), red cord binding (label 5), bronze head and butt (6)."""
    g = new(name)
    p = g.obj()
    grain = g.noise(g.scale_vec(p, (70.0, 70.0, 6.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb((0.62, 0.45, 0.28)), g.rgb((0.46, 0.32, 0.19)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb((0.74, 0.58, 0.4)))
    tw = g.wave(p, 300.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(5), c, g.mix(g.math("MULTIPLY", tw, 0.6), g.rgb((0.8, 0.16, 0.09)), g.rgb((0.5, 0.08, 0.05))))
    pt = g.geo("Pointiness")
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.76, 0.5, 0.22)), g.rgb((1.0, 0.84, 0.54)))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), br, g.rgb((0.34, 0.2, 0.09)))
    c = g.mix(g.reg(6), c, br)
    rough = g.mixf(g.reg(6), g.mixf(g.reg(5), 0.7, 0.85), 0.28)
    return g.finish(c, rough, g.bump(g.math("ADD", grain, g.math("MULTIPLY", tw, g.reg(5))), 0.2, 0.002))


def shield_hide(name="HQ_Shield"):
    """A hide shield: cream ox-hide stretched on a frame (mottled, a little translucent-looking at the edges), red
    paint (label 5) with brush grain, bronze rim, boss and studs (6), a dark wooden grip (7)."""
    g = new(name)
    p = g.obj()
    hide = g.mix(g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.9, 0.82, 0.64)), g.rgb((0.78, 0.66, 0.46)))
    spots = g.smooth(g.noise(p, 3.2, 2.0), 0.6, 0.66)
    c = g.mix(g.math("MULTIPLY", spots, 0.45), hide, g.rgb((0.55, 0.38, 0.24)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.49, 0.44), 0.4), c, g.rgb((0.5, 0.4, 0.28)))
    brush = g.noise(g.scale_vec(p, (120.0, 30.0, 120.0)), 1.0, 2.0)
    paint = g.mix(g.math("MULTIPLY", g.remap(brush, 0.3, 0.7, 0.0, 1.0), 0.35), g.rgb((0.74, 0.12, 0.07)), g.rgb((0.56, 0.07, 0.04)))
    c = g.mix(g.reg(5), c, paint)
    pt = g.geo("Pointiness")
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.78, 0.52, 0.22)), g.rgb((1.0, 0.85, 0.55)))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.55), br, g.rgb((0.34, 0.2, 0.09)))
    c = g.mix(g.reg(6), c, br)
    c = g.mix(g.reg(7), c, g.rgb((0.34, 0.21, 0.12)))
    rough = g.mixf(g.reg(6), g.mixf(g.reg(5), 0.78, 0.55), 0.26)
    return g.finish(c, rough, g.bump(g.math("ADD", g.noise(p, 70.0, 2.0), g.math("MULTIPLY", brush, g.reg(5))), 0.12, 0.002))


def limestone(name="HQ_Limestone"):
    """Dressed limestone: warm sand colour, darker weathering in joints and hollows, pale chipped edges, fine pits."""
    g = new(name)
    p = g.obj()
    macro = g.noise(p, 3.0, 3.0, 0.55)
    c = g.mix(g.remap(macro, 0.35, 0.65, 0.0, 1.0), g.rgb((0.8, 0.71, 0.55)), g.rgb((0.88, 0.8, 0.65)))
    pits = g.smooth(g.noise(p, 80.0, 2.0, 0.6), 0.62, 0.68)
    c = g.mix(g.math("MULTIPLY", pits, 0.4), c, g.rgb((0.56, 0.48, 0.36)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.7), c, g.rgb((0.46, 0.39, 0.29)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.6), c, g.rgb((0.95, 0.9, 0.78)))
    stain = g.smooth(g.noise(p, 1.5, 2.0), 0.55, 0.7)
    c = g.mix(g.math("MULTIPLY", stain, 0.25), c, g.rgb((0.6, 0.55, 0.42)))
    # label 5: red ochre paint, worn off the edges; 6: worn smooth and pale (wheel tracks)
    worn = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.smooth(pt, 0.52, 0.6), 0.8))
    red = g.mix(g.math("MULTIPLY", g.remap(g.noise(p, 40.0, 2.0), 0.3, 0.7, 0.0, 1.0), 0.3), g.rgb((0.7, 0.2, 0.1)), g.rgb((0.55, 0.14, 0.07)))
    c = g.mix(g.math("MULTIPLY", g.reg(5), worn), c, red)
    c = g.mix(g.math("MULTIPLY", g.reg(6), 0.55), c, g.rgb((0.94, 0.88, 0.74)))
    h = g.math("ADD", g.math("MULTIPLY", pits, -0.5), g.noise(p, 18.0, 4.0, 0.6))
    h = g.math("MULTIPLY", h, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.reg(6), 0.6)))
    return g.finish(c, g.mixf(g.reg(6), 0.85, 0.55), g.bump(h, 0.3, 0.005))


def marble(name="HQ_Marble", base=(0.93, 0.91, 0.87), warm=(0.9, 0.84, 0.74), vein=(0.58, 0.6, 0.65), vein_scale=1.0):
    """White marble (Classical Age): grey veins wandering through it, warm cream in patches, grey-brown grime in the
    joints and crevices, bright on worn edges, fine pits; label 5 = worn red paint, 6 = polished smooth and bright
    (worn by feet), 7 = weathered dark (lichen, rain streaks). vein_scale > 1: finer, closer veins (small statues)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 2.0, 3.0), 0.35, 0.65, 0.0, 1.0), g.rgb(base), g.rgb(warm))
    pv = p if vein_scale == 1.0 else g.scale_vec(p, (vein_scale, vein_scale, vein_scale))
    v1 = g.smooth(g.wave(pv, 2.2, 14.0, 4.0, "BANDS", "DIAGONAL"), 0.9, 0.985)
    v2 = g.smooth(g.wave(g.scale_vec(pv, (1.0, 1.7, 0.6)), 3.4, 18.0, 3.0, "BANDS", "X"), 0.93, 0.99)
    c = g.mix(g.math("MULTIPLY", v1, 0.5), c, g.rgb(vein))
    c = g.mix(g.math("MULTIPLY", v2, 0.3), c, g.rgb(vein))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.6), c, g.rgb((0.56, 0.52, 0.46)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.5), c, g.rgb((1.0, 0.99, 0.96)))
    pits = g.smooth(g.noise(p, 70.0, 2.0, 0.6), 0.64, 0.7)
    c = g.mix(g.math("MULTIPLY", pits, 0.3), c, g.rgb((0.66, 0.63, 0.58)))
    worn = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.smooth(pt, 0.52, 0.6), 0.8))
    red = g.mix(g.math("MULTIPLY", g.remap(g.noise(p, 40.0, 2.0), 0.3, 0.7, 0.0, 1.0), 0.3), g.rgb((0.72, 0.18, 0.1)), g.rgb((0.56, 0.13, 0.07)))
    c = g.mix(g.math("MULTIPLY", g.reg(5), worn), c, red)
    c = g.mix(g.math("MULTIPLY", g.reg(6), 0.45), c, g.rgb((0.98, 0.97, 0.93)))
    lich = g.mix(g.noise(p, 9.0, 3.0), g.rgb((0.44, 0.46, 0.38)), g.rgb((0.62, 0.62, 0.54)))
    c = g.mix(g.math("MULTIPLY", g.reg(7), g.smooth(g.noise(p, 6.0, 3.0), 0.4, 0.6)), c, lich)
    h = g.math("ADD", g.math("MULTIPLY", pits, -0.4), g.math("MULTIPLY", g.noise(p, 14.0, 3.0, 0.5), 0.6))
    return g.finish(c, g.mixf(g.reg(6), 0.5, 0.28), g.bump(h, 0.16, 0.004))


def straw_target(name="HQ_StrawTarget"):
    """A coiled straw archery target: pale straw coils with fine fibres, darker between the coils; painted rings
    (label 5 red, 6 black, 7 white) and a rope binding (8)."""
    g = new(name)
    p = g.obj()
    fib = g.noise(g.scale_vec(p, (160.0, 160.0, 160.0)), 1.0, 2.0)
    c = g.mix(g.remap(fib, 0.3, 0.7, 0.0, 1.0), g.rgb((0.84, 0.72, 0.44)), g.rgb((0.68, 0.55, 0.3)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), c, g.rgb((0.42, 0.32, 0.16)))
    c = g.mix(g.math("MULTIPLY", g.reg(5), 0.9), c, g.rgb((0.76, 0.15, 0.08)))
    c = g.mix(g.math("MULTIPLY", g.reg(6), 0.9), c, g.rgb((0.1, 0.08, 0.07)))
    c = g.mix(g.math("MULTIPLY", g.reg(7), 0.9), c, g.rgb((0.94, 0.91, 0.83)))
    c = g.mix(g.reg(8), c, g.rgb((0.5, 0.36, 0.2)))
    return g.finish(c, 0.85, g.bump(fib, 0.25, 0.002))


def plaster(name="HQ_Plaster", base=(0.94, 0.91, 0.84), paint=(0.72, 0.14, 0.08)):
    """Lime plaster: off-white, faint brush marks and grime in the hollows; label 5 = a red painted band."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb((0.84, 0.8, 0.7)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.49, 0.43), 0.5), c, g.rgb((0.6, 0.55, 0.46)))
    brush = g.noise(g.scale_vec(p, (60.0, 60.0, 12.0)), 1.0, 2.0)
    c = g.mix(g.reg(5), c, g.mix(g.math("MULTIPLY", g.remap(brush, 0.3, 0.7, 0.0, 1.0), 0.3), g.rgb(paint), g.rgb(tuple(x * 0.8 for x in paint))))
    return g.finish(c, 0.8, g.bump(g.math("ADD", brush, g.noise(p, 50.0, 2.0)), 0.12, 0.002))


def siege(name="HQ_Siege", wood=(0.6, 0.36, 0.2), wood2=(0.44, 0.25, 0.13), red=(0.72, 0.15, 0.08), blue=(0.14, 0.3, 0.62),
          metal="bronze"):
    """A war engine's timber and fittings: adzed cedar with the grain along Y (label 0), X (10) or Z (11), darker in the
    joints, pale on worn edges; red ochre (5) and blue (7) paint with brush grain, chipped back to the wood on the edges;
    bronze fittings (6; metal="iron": forged iron, see _iron_col); rope and twisted sinew (8); leather (9)."""
    g = new(name)
    p = g.obj()
    gy = g.noise(g.scale_vec(p, (60.0, 3.0, 60.0)), 1.0, 4.0, 0.62)
    gx = g.noise(g.scale_vec(p, (3.0, 60.0, 60.0)), 1.0, 4.0, 0.62)
    gz = g.noise(g.scale_vec(p, (60.0, 60.0, 3.0)), 1.0, 4.0, 0.62)
    gr = g.mixf(g.reg(11), g.mixf(g.reg(10), gy, gx), gz)
    c = g.mix(g.remap(gr, 0.32, 0.68, 0.0, 1.0), g.rgb(wood), g.rgb(wood2))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 2.5, 2.0), 0.45, 0.7), 0.3), c, g.rgb(tuple(x * 0.75 for x in wood2)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.55), c, g.rgb((0.22, 0.13, 0.07)))            # grime in the joints
    worn = g.smooth(pt, 0.51, 0.57)
    c = g.mix(g.math("MULTIPLY", worn, 0.5), c, g.rgb((0.78, 0.6, 0.4)))
    brush = g.remap(g.noise(g.scale_vec(p, (80.0, 80.0, 80.0)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    chip = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.smooth(pt, 0.53, 0.6), g.smooth(g.noise(p, 30.0, 2.0), 0.45, 0.55)))
    red_c = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb(red), g.rgb(tuple(x * 0.78 for x in red)))
    blue_c = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb(blue), g.rgb(tuple(x * 0.75 for x in blue)))
    c = g.mix(g.math("MULTIPLY", g.reg(5), chip), c, red_c)
    c = g.mix(g.math("MULTIPLY", g.reg(7), chip), c, blue_c)
    if metal == "iron":
        br, _rs = _iron_col(g, p)
    else:
        br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.72, 0.46, 0.2)), g.rgb((1.0, 0.82, 0.52)))
        br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), br, g.rgb((0.3, 0.17, 0.08)))
        pat = g.math("MULTIPLY", g.smooth(pt, 0.46, 0.41), g.smooth(g.noise(p, 12.0, 3.0), 0.5, 0.64))
        br = g.mix(g.math("MULTIPLY", pat, 0.7), br, g.rgb((0.3, 0.56, 0.48)))
    c = g.mix(g.reg(6), c, br)
    tw = g.wave(p, 240.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(8), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb((0.78, 0.66, 0.46)), g.rgb((0.5, 0.38, 0.24))))
    hide = g.mix(g.noise(p, 9.0, 3.0), g.rgb((0.4, 0.23, 0.12)), g.rgb((0.52, 0.32, 0.17)))
    hide = g.mix(g.math("MULTIPLY", worn, 0.6), hide, g.rgb((0.66, 0.45, 0.27)))
    c = g.mix(g.reg(9), c, hide)
    rough = g.mixf(g.reg(6), g.mixf(g.math("MAXIMUM", g.reg(5), g.reg(7)), 0.78, 0.62), 0.28 if metal != "iron" else 0.42)
    h = g.math("ADD", g.math("MULTIPLY", gr, 0.8), g.math("MULTIPLY", tw, g.math("MULTIPLY", g.reg(8), 1.5)))
    h = g.math("ADD", h, g.math("MULTIPLY", g.noise(p, 90.0, 2.0), g.reg(6)))
    return g.finish(c, rough, g.bump(h, 0.32, 0.003))


def collar(name="HQ_Collar"):
    """A broad bead collar: rows of gold beads (label 0) with bands of lapis blue (5), carnelian red (6) and turquoise
    (7), each bead catching the light on its crown."""
    g = new(name)
    p = g.obj()
    bead = g.voronoi(p, 260.0, 0.6, "F1", "Distance")
    crown = g.smooth(bead, 0.32, 0.05)                                  # bright at each bead's middle
    gold_c = g.mix(g.math("MULTIPLY", crown, 0.8), g.rgb((0.62, 0.42, 0.12)), g.rgb((1.0, 0.86, 0.46)))
    lapis = g.mix(g.math("MULTIPLY", crown, 0.6), g.rgb((0.08, 0.16, 0.48)), g.rgb((0.3, 0.45, 0.9)))
    carn = g.mix(g.math("MULTIPLY", crown, 0.6), g.rgb((0.5, 0.1, 0.05)), g.rgb((0.9, 0.36, 0.2)))
    turq = g.mix(g.math("MULTIPLY", crown, 0.6), g.rgb((0.06, 0.4, 0.38)), g.rgb((0.36, 0.82, 0.74)))
    c = gold_c
    c = g.mix(g.reg(5), c, lapis)
    c = g.mix(g.reg(6), c, carn)
    c = g.mix(g.reg(7), c, turq)
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.48, 0.42), 0.5), c, g.rgb((0.12, 0.08, 0.04)))
    rough = g.mixf(g.math("MAXIMUM", g.math("MAXIMUM", g.reg(5), g.reg(6)), g.reg(7)), 0.28, 0.35)
    return g.finish(c, rough, g.bump(g.math("SUBTRACT", 1.0, bead), 0.35, 0.002))


def granite(name="HQ_Granite", base=(0.62, 0.38, 0.33), feld=(0.8, 0.5, 0.42), quartz=(0.6, 0.57, 0.55), mica=(0.08, 0.07, 0.07)):
    """Polished red granite: pink feldspar crystals, grey glassy quartz and black mica flecks in a warm ground; darker and
    dull in carved hollows, pale on worn edges."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 2.5, 3.0, 0.55), 0.35, 0.65, 0.0, 1.0), g.rgb(base), g.rgb(tuple(x * 0.84 for x in base)))
    cell = g.voronoi(p, 55.0, 1.0, "F1", "Color")                 # each crystal its own random shade
    c = g.mix(g.smooth(cell, 0.5, 0.62), c, g.rgb(feld))
    c = g.mix(g.smooth(cell, 0.24, 0.16), c, g.rgb(quartz))
    fleck = g.noise(p, 140.0, 2.0, 0.6)
    mica_m = g.smooth(fleck, 0.63, 0.69)
    c = g.mix(mica_m, c, g.rgb(mica))
    pt = g.geo("Pointiness")
    hollow = g.smooth(pt, 0.47, 0.42)
    c = g.mix(g.math("MULTIPLY", hollow, 0.6), c, g.rgb((0.2, 0.11, 0.09)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.52, 0.58), 0.4), c, g.rgb((0.86, 0.68, 0.62)))
    h = g.math("ADD", g.math("MULTIPLY", mica_m, -0.4), g.noise(p, 20.0, 3.0, 0.5))
    return g.finish(c, g.mixf(hollow, 0.36, 0.75), g.bump(h, 0.1, 0.002))


def flagstone(name="HQ_Flagstone", base=(0.42, 0.39, 0.36), alt=(0.53, 0.47, 0.39), stain=None):
    """Worn flagstones: a warm dark grey (label 7 = a lighter, browner stone for some of the flags), pale on worn edges,
    dark grit in the joints and hollows, fine pits; label 5 = soot (black, dull), 6 = hammer scale and charcoal grit;
    `stain`: a colour for label 8, spilled brews soaked into the stone (glossy at their hearts)."""
    g = new(name)
    p = g.obj()
    macro = g.remap(g.noise(p, 3.0, 3.0, 0.55), 0.35, 0.65, 0.0, 1.0)
    c = g.mix(macro, g.rgb(base), g.rgb(tuple(min(1.0, x * 1.16) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.reg(7), 0.9), c, g.mix(macro, g.rgb(alt), g.rgb(tuple(x * 0.88 for x in alt))))
    speck = g.noise(p, 90.0, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.62, 0.68), 0.4), c, g.rgb((0.22, 0.2, 0.19)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.75), c, g.rgb((0.13, 0.11, 0.1)))      # grit in the joints
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.55), c, g.rgb((0.7, 0.66, 0.6)))       # worn pale edges
    soot = g.math("MULTIPLY", g.reg(5), g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.55, 1.0))
    c = g.mix(soot, c, g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.06, 0.055, 0.05)), g.rgb((0.13, 0.11, 0.1))))
    grit = g.math("MULTIPLY", g.reg(6), g.smooth(g.noise(p, 150.0, 1.0), 0.6, 0.66))
    c = g.mix(grit, c, g.rgb((0.07, 0.065, 0.06)))
    h = g.math("ADD", g.math("MULTIPLY", speck, 0.4), g.noise(p, 14.0, 4.0, 0.6))
    rough = g.mixf(soot, 0.8, 0.95)
    if stain is not None:
        st = g.math("MULTIPLY", g.reg(8), g.remap(g.noise(p, 9.0, 3.0), 0.3, 0.7, 0.5, 1.0))
        c = g.mix(st, c, g.mix(g.noise(p, 30.0, 2.0), g.rgb(stain), g.rgb(tuple(min(1.0, x * 1.3) for x in stain))))
        rough = g.mixf(st, rough, 0.3)
    return g.finish(c, rough, g.bump(h, 0.3, 0.005))


def charcoal(name="HQ_Charcoal"):
    """Charcoal: dull black lumps, split along the grain, grey-silver on the broken edges."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.05, 0.048, 0.046)), g.rgb((0.11, 0.1, 0.1)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.58), 0.6), c, g.rgb((0.36, 0.36, 0.37)))
    cr = g.wave(p, 140.0, 2.0, 1.0, "BANDS", "Z")
    return g.finish(c, 0.7, g.bump(cr, 0.25, 0.002))


# ======================================================================================= Iron Age (v0.9.29)
def _iron_col(g, p, base=(0.32, 0.32, 0.34), hi=(0.74, 0.76, 0.8), dark=(0.1, 0.1, 0.11), rust=(0.5, 0.24, 0.1)):
    """Forged iron, hand-painted: blue-grey, bright on its edges and ridges and on faces turned to the sky, dark in the
    recesses, rust in the deepest crevices. Returns (colour, rust mask)."""
    c = g.mix(g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1.0, x * 1.25) for x in base)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.8), c, g.rgb(hi))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), c, g.rgb(dark))
    rs = g.math("MULTIPLY", g.smooth(pt, 0.47, 0.42), g.smooth(g.noise(p, 14.0, 3.0), 0.48, 0.62))
    c = g.mix(g.math("MULTIPLY", rs, 0.75), c, g.rgb(rust))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    c = g.mix(g.math("MULTIPLY", g.smooth(nz.outputs["Z"], 0.3, 0.95), 0.25), c, g.rgb(hi))
    return c, rs


def iron(name="HQ_Iron", col=None, wood=None, cord=None):
    """Forged iron (see _iron_col), fine hammer marks. `col`: _iron_col's colours (base, hi, dark, rust) for a darker
    iron (cast-iron grenades are black); `wood`: a colour for label 5 (a fuse's wooden plug), `cord`: label 8 (tarred
    fuse cord)."""
    g = new(name)
    p = g.obj()
    c, rs = _iron_col(g, p, **(col or {}))
    rough = g.mixf(rs, 0.35, 0.8)
    if wood is not None:
        w = g.mix(g.noise(g.scale_vec(p, (60.0, 60.0, 8.0)), 1.0, 3.0), g.rgb(wood), g.rgb(tuple(x * 0.7 for x in wood)))
        c = g.mix(g.reg(5), c, w)
        rough = g.mixf(g.reg(5), rough, 0.75)
    if cord is not None:
        tw = g.wave(p, 300.0, 1.0, 0.0, "BANDS", "DIAGONAL")
        c = g.mix(g.reg(8), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb(cord), g.rgb(tuple(x * 0.6 for x in cord))))
        rough = g.mixf(g.reg(8), rough, 0.8)
    h = g.math("ADD", g.math("MULTIPLY", g.voronoi(p, 80.0, 1.0, "F1", "Distance"), 0.3), g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.2))
    return g.finish(c, rough, g.bump(h, 0.14, 0.002))


def mail(name="HQ_Mail", base=(0.36, 0.37, 0.4)):
    """Iron mail: rows of small interlocked rings (a near-regular cell grid, a ring round each cell's middle), forged-iron
    colours (_iron_col), dark in the gaps between the rings; label 5 = a band of bronze rings at the edges."""
    g = new(name)
    p = g.obj()
    c, rs = _iron_col(g, p, base=base)
    q = g.scale_vec(p, (1.0, 1.0, 1.3))
    cell = g.voronoi(q, 80.0, 0.12, "F1", "Distance")
    ring = g.math("MULTIPLY", g.smooth(cell, 0.18, 0.28), g.math("SUBTRACT", 1.0, g.smooth(cell, 0.4, 0.5)))
    gap = g.math("SUBTRACT", 1.0, ring)
    c = g.mix(g.math("MULTIPLY", gap, 0.6), c, g.rgb(tuple(x * 0.35 for x in base)))
    br = g.mix(g.math("MULTIPLY", ring, 0.6), g.rgb((0.55, 0.34, 0.14)), g.rgb((0.95, 0.72, 0.4)))
    c = g.mix(g.reg(5), c, br)
    return g.finish(c, g.mixf(rs, 0.38, 0.8), g.bump(ring, 0.35, 0.002))


def roman_steel(name="HQ_RomanSteel", base=(0.42, 0.43, 0.46)):
    """Polished iron armour (Classical Age): bright blue-grey plates (_iron_col, kept polished: little rust), label 6 =
    brass fittings (hinges, buckles, rivets, edging), 5 = red-dyed leather."""
    g = new(name)
    p = g.obj()
    c, rs = _iron_col(g, p, base=base, hi=(0.86, 0.88, 0.92), dark=(0.12, 0.12, 0.14), rust=(0.42, 0.24, 0.12))
    pt = g.geo("Pointiness")
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.78, 0.58, 0.22)), g.rgb((1.0, 0.88, 0.52)))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), br, g.rgb((0.36, 0.22, 0.08)))
    c = g.mix(g.reg(6), c, br)
    red = g.mix(g.noise(p, 9.0, 3.0), g.rgb((0.6, 0.1, 0.07)), g.rgb((0.46, 0.07, 0.05)))
    c = g.mix(g.reg(5), c, red)
    h = g.math("ADD", g.math("MULTIPLY", g.voronoi(p, 70.0, 1.0, "F1", "Distance"), 0.2), g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.15))
    rough = g.mixf(g.reg(5), g.mixf(g.reg(6), g.mixf(rs, 0.26, 0.7), 0.3), 0.8)
    return g.finish(c, rough, g.bump(h, 0.12, 0.002))


def scutum(name="HQ_Scutum", red=(0.66, 0.1, 0.06), gold=(0.95, 0.74, 0.28)):
    """A legionary's shield: red-painted hide over plywood (brush marks, worn dark at the bottom, chipped at the edges),
    label 5 = gold paint (wings, bolts, borders), 6 = brass edging, 7 = iron (the boss and its plate), 8 = the bare wood
    of the back."""
    g = new(name)
    p = g.obj()
    brush = g.remap(g.noise(g.scale_vec(p, (60.0, 60.0, 15.0)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    c = g.mix(g.math("MULTIPLY", brush, 0.35), g.rgb(red), g.rgb(tuple(x * 0.78 for x in red)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), c, g.rgb((0.3, 0.05, 0.03)))
    chip = g.math("MULTIPLY", g.smooth(pt, 0.53, 0.6), g.smooth(g.noise(p, 30.0, 2.0), 0.45, 0.55))
    c = g.mix(g.math("MULTIPLY", chip, 0.6), c, g.rgb((0.62, 0.45, 0.3)))
    gc = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb(gold), g.rgb(tuple(x * 0.82 for x in gold)))
    c = g.mix(g.reg(5), c, gc)
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.76, 0.56, 0.22)), g.rgb((1.0, 0.88, 0.52)))
    c = g.mix(g.reg(6), c, br)
    ir, rs = _iron_col(g, p, base=(0.4, 0.41, 0.44), hi=(0.85, 0.87, 0.9))
    c = g.mix(g.reg(7), c, ir)
    wood = g.mix(g.noise(g.scale_vec(p, (40.0, 40.0, 3.0)), 1.0, 3.0), g.rgb((0.5, 0.34, 0.2)), g.rgb((0.36, 0.23, 0.13)))
    c = g.mix(g.reg(8), c, wood)
    rough = g.mixf(g.math("MAXIMUM", g.reg(6), g.reg(7)), g.mixf(g.reg(5), 0.62, 0.42), 0.3)
    return g.finish(c, rough, g.bump(g.math("ADD", brush, g.noise(p, 90.0, 2.0)), 0.12, 0.002))


def gladius(name="HQ_Gladius"):
    """A short sword: a polished steel blade (label 0) with a darker fuller, a bone grip with finger ridges (5), brass
    guard and pommel fittings (6)."""
    g = new(name)
    p = g.obj()
    c, rs = _iron_col(g, p, base=(0.55, 0.57, 0.6), hi=(0.95, 0.96, 0.98), dark=(0.2, 0.2, 0.22), rust=(0.4, 0.25, 0.14))
    bone_c = g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.9, 0.84, 0.7)), g.rgb((0.74, 0.66, 0.5)))
    c = g.mix(g.reg(5), c, bone_c)
    pt = g.geo("Pointiness")
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.78, 0.58, 0.22)), g.rgb((1.0, 0.88, 0.52)))
    c = g.mix(g.reg(6), c, br)
    rough = g.mixf(g.reg(5), g.mixf(g.reg(6), 0.2, 0.3), 0.6)
    return g.finish(c, rough, g.bump(g.noise(p, 60.0, 2.0), 0.08, 0.001))


def plaid(name="HQ_Plaid", base=(0.2, 0.36, 0.18), stripe=(0.62, 0.13, 0.08), line=(0.88, 0.74, 0.3),
          border=(0.62, 0.13, 0.08), period=0.11):
    """Checked wool (Iron Age): broad bands of `stripe` crossing on `base` (where two cross the colour is full, a band
    alone shows half, as woven), darker bands between them, thin `line`s; a coarse weave, darker in the folds, lighter
    fuzz on the ridges; label 5 = a woven border. The checks run up and round (bands along x, y and z)."""
    g = new(name)
    p = g.obj()
    s = 0.314 / period
    # a band along an axis is a stack of planes across it: where the cloth faces along that axis (a back, a chest) the
    # planes cut it in contour rings, not stripes; so each axis' bands fade out where the cloth faces along it
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], g.geo("Normal"))
    wts = [g.math("SUBTRACT", 1.0, g.smooth(g.math("ABSOLUTE", sep.outputs[a]), 0.5, 0.82)) for a in ("X", "Y", "Z")]

    def bands(offset, lo, hi):
        q = g.add_vec(p, offset)
        bx = g.math("MULTIPLY", g.smooth(g.wave(q, s, 0.0, 0.0, "BANDS", "X"), lo, hi), wts[0])
        by = g.math("MULTIPLY", g.smooth(g.wave(q, s, 0.0, 0.0, "BANDS", "Y"), lo, hi), wts[1])
        bz = g.math("MULTIPLY", g.smooth(g.wave(q, s, 0.0, 0.0, "BANDS", "Z"), lo, hi), wts[2])
        v = g.math("MAXIMUM", bx, by)
        return g.math("ADD", g.math("MULTIPLY", v, 0.5), g.math("MULTIPLY", bz, 0.5))

    c = g.mix(g.remap(g.noise(p, 7.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(x * 0.82 for x in base)))
    c = g.mix(bands((period * 0.25, period * 0.25, period * 0.25), 0.82, 0.9), c, g.rgb(tuple(x * 0.55 for x in base)))
    c = g.mix(bands((0.0, 0.0, 0.0), 0.74, 0.82), c, g.rgb(stripe))
    c = g.mix(bands((period * 0.5, period * 0.5, period * 0.5), 0.965, 0.985), c, g.rgb(line))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.49, 0.43), 0.55), c, g.rgb(tuple(x * 0.5 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.3), c, g.rgb(tuple(min(1, x * 1.3 + 0.05) for x in base)))
    zz = g.smooth(g.wave(p, 90.0, 0.0, 0.0, "BANDS", "DIAGONAL", "TRI"), 0.45, 0.55)
    bc = g.mix(g.math("MULTIPLY", zz, 0.5), g.rgb(border), g.rgb((0.9, 0.82, 0.55)))
    c = g.mix(g.reg(5), c, bc)
    weave = g.math("ADD", g.wave(p, 260.0, 0.0, 0.0, "BANDS", "X"), g.wave(p, 260.0, 0.0, 0.0, "BANDS", "Z"))
    return g.finish(c, 0.92, g.bump(weave, 0.18, 0.0015))


def leafy(name="HQ_Leafy", leaf=(0.2, 0.36, 0.1), vein=(0.4, 0.54, 0.18), berry=(0.93, 0.94, 0.86), mist=(0.56, 0.62, 0.24),
          twig=(0.36, 0.26, 0.16)):
    """Leaves (a druid's wreath): oak green, mottled, lighter along the ridges and edges (label 0); waxy white mistletoe
    berries (5); mistletoe's narrow yellow-green leaves (6); twigs (7)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 30.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb(leaf), g.rgb(tuple(x * 1.25 for x in leaf)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.52, 0.6), 0.6), c, g.rgb(vein))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.48, 0.42), 0.5), c, g.rgb(tuple(x * 0.55 for x in leaf)))
    c = g.mix(g.reg(6), c, g.rgb(mist))
    c = g.mix(g.reg(7), c, g.rgb(twig))
    c = g.mix(g.reg(5), c, g.rgb(berry))
    rough = g.mixf(g.reg(5), 0.62, 0.25)
    return g.finish(c, rough, g.bump(g.noise(p, 90.0, 2.0), 0.15, 0.001))


def bark_wood(name="HQ_BarkWood", bark=(0.34, 0.24, 0.15), wood=(0.76, 0.6, 0.4)):
    """Logs, stakes and a stump: bark in cracked plates, dark in the cracks, lighter on the worn ridges (label 0); pale
    cut or split wood with fine grain and darker rings (label 5); grey-brown withies (7); iron (6)."""
    g = new(name)
    p = g.obj()
    plates = g.voronoi(g.scale_vec(p, (1.0, 1.0, 0.45)), 26.0, 1.0, "F1", "Distance")
    cracks = g.smooth(g.voronoi(g.scale_vec(p, (1.0, 1.0, 0.45)), 26.0, 1.0, "DISTANCE_TO_EDGE", "Distance"), 0.0, 0.06)
    c = g.mix(g.remap(g.noise(p, 9.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(bark), g.rgb(tuple(x * 1.25 for x in bark)))
    c = g.mix(g.math("SUBTRACT", 1.0, cracks), c, g.rgb(tuple(x * 0.4 for x in bark)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.4), c, g.rgb(tuple(min(1, x * 1.6) for x in bark)))
    rings = g.wave(p, 60.0, 3.0, 2.0, "RINGS", "SPHERICAL")
    cut = g.mix(g.math("MULTIPLY", rings, 0.35), g.rgb(wood), g.rgb(tuple(x * 0.72 for x in wood)))
    cut = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 30.0, 2.0), 0.55, 0.7), 0.3), cut, g.rgb(tuple(x * 0.6 for x in wood)))
    c = g.mix(g.reg(5), c, cut)
    withy = g.mix(g.noise(g.scale_vec(p, (60.0, 60.0, 60.0)), 1.0, 2.0), g.rgb((0.42, 0.36, 0.28)), g.rgb((0.56, 0.48, 0.36)))
    c = g.mix(g.reg(7), c, withy)
    ic, rs = _iron_col(g, p)
    c = g.mix(g.reg(6), c, ic)
    h = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", 1.0, cracks), g.math("SUBTRACT", 1.0, g.reg(5))), g.math("MULTIPLY", plates, 0.2))
    return g.finish(c, g.mixf(g.reg(6), 0.85, g.mixf(rs, 0.35, 0.8)), g.bump(h, 0.35, 0.004))


def _ash(g, p):
    grain = g.noise(g.scale_vec(p, (70.0, 70.0, 6.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb((0.66, 0.5, 0.32)), g.rgb((0.5, 0.36, 0.22)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb((0.78, 0.63, 0.44)))
    return c, grain


def javelin_shaft(name="HQ_Javelin"):
    """An ash javelin (pale wood, fine grain along it), a leather binding below the head (label 5), a forged iron head and
    butt cap (6)."""
    g = new(name)
    p = g.obj()
    c, grain = _ash(g, p)
    tw = g.wave(p, 300.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(5), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb((0.42, 0.25, 0.13)), g.rgb((0.26, 0.15, 0.08))))
    ic, rs = _iron_col(g, p)
    c = g.mix(g.reg(6), c, ic)
    rough = g.mixf(g.reg(6), g.mixf(g.reg(5), 0.7, 0.8), g.mixf(rs, 0.32, 0.8))
    return g.finish(c, rough, g.bump(g.math("ADD", grain, g.math("MULTIPLY", tw, g.reg(5))), 0.2, 0.002))


def javelin_case(name="HQ_JavCase", base=(0.4, 0.24, 0.12)):
    """A leather javelin case: rawhide bands and bindings (label 5), the javelins' iron heads (6) and ash shafts (7)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 9.0, 3.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.3) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.58), 0.55), c, g.rgb(tuple(min(1, x * 1.6) for x in base)))
    scr = g.smooth(g.noise(g.scale_vec(p, (120.0, 120.0, 30.0)), 1.0, 2.0), 0.62, 0.68)
    c = g.mix(g.math("MULTIPLY", scr, 0.35), c, g.rgb(tuple(x * 0.45 for x in base)))
    c = g.mix(g.reg(5), c, g.rgb((0.82, 0.72, 0.52)))
    ic, rs = _iron_col(g, p)
    c = g.mix(g.reg(6), c, ic)
    ash, grain = _ash(g, p)
    c = g.mix(g.reg(7), c, ash)
    return g.finish(c, g.mixf(g.reg(6), 0.62, g.mixf(rs, 0.32, 0.8)), g.bump(g.math("ADD", g.noise(p, 90.0, 3.0), scr), 0.2, 0.003))


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


def vials(name="HQ_Vials", glass=(0.8, 0.9, 0.88)):
    """Glassware with coloured brews: pale green-white glossy glass (label 0, brighter on its rims and edges), brews of
    green (5), amber (6), violet (7) and red (8), cork stoppers (9), wax seals (10)."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 30.0, 2.0), g.rgb(tuple(x * 0.86 for x in glass)), g.rgb(glass))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.6), c, g.rgb((0.97, 1.0, 0.99)))
    for lab, col, hi in ((5, (0.24, 0.82, 0.18), (0.62, 1.0, 0.45)), (6, (0.92, 0.52, 0.08), (1.0, 0.8, 0.35)),
                         (7, (0.48, 0.2, 0.74), (0.74, 0.5, 0.95)), (8, (0.74, 0.1, 0.08), (0.98, 0.4, 0.3))):
        cc = g.mix(g.remap(g.noise(p, 25.0, 2.0), 0.35, 0.65, 0.0, 1.0), g.rgb(col), g.rgb(hi))
        c = g.mix(g.reg(lab), c, cc)
    cork = g.mix(g.noise(p, 90.0, 2.0), g.rgb((0.52, 0.36, 0.2)), g.rgb((0.72, 0.55, 0.34)))
    c = g.mix(g.reg(9), c, cork)
    c = g.mix(g.reg(10), c, g.rgb((0.62, 0.08, 0.06)))
    rough = g.mixf(g.math("MAXIMUM", g.reg(9), g.reg(10)), 0.06, 0.75)
    return g.finish(c, rough)


# ======================================================================================= Gunpowder Age
def drum(name="HQ_Drum", shell=(0.55, 0.08, 0.08), device=(0.88, 0.66, 0.22), hoop=(0.07, 0.065, 0.065),
         hoop_gold=(0.9, 0.7, 0.26), rope=(0.94, 0.92, 0.86), buff=(0.42, 0.25, 0.13), head=(0.93, 0.87, 0.73)):
    """A military side drum: the shell's paint (label 0) with brush grain, darker in the hollows, chipped back to the wood
    on its worn edges; the painted device (5, gold); the hoops' black paint (6) and their gold paint (7); white rope (8),
    twisted; leather buffs (9); calfskin heads (10), mottled, pale; brass (11); the head's patch worn grey where the
    sticks strike (13)."""
    g = new(name)
    p = g.obj()
    pt = g.geo("Pointiness")
    brush = g.remap(g.noise(g.scale_vec(p, (70.0, 70.0, 70.0)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    chip = g.math("MULTIPLY", g.smooth(pt, 0.53, 0.6), g.smooth(g.noise(p, 30.0, 2.0), 0.45, 0.55))
    c = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb(shell), g.rgb(tuple(x * 0.78 for x in shell)))
    dv = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb(device), g.rgb(tuple(x * 0.82 for x in device)))
    c = g.mix(g.reg(5), c, dv)
    hp_ = g.mix(g.math("MULTIPLY", brush, 0.4), g.rgb(hoop), g.rgb(tuple(min(1.0, x * 1.8) for x in hoop)))
    c = g.mix(g.reg(6), c, hp_)
    hg = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb(hoop_gold), g.rgb(tuple(x * 0.8 for x in hoop_gold)))
    c = g.mix(g.reg(7), c, hg)
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.45), c, g.rgb((0.12, 0.05, 0.04)))           # grime in the hollows
    c = g.mix(g.math("MULTIPLY", chip, 0.55), c, g.rgb((0.6, 0.44, 0.28)))                                  # chipped to the wood
    tw = g.wave(p, 260.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(8), c, g.mix(g.math("MULTIPLY", tw, 0.45), g.rgb(rope), g.rgb(tuple(x * 0.78 for x in rope))))
    lth = g.mix(g.noise(p, 9.0, 3.0), g.rgb(buff), g.rgb(tuple(min(1.0, x * 1.3) for x in buff)))
    lth = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.58), 0.5), lth, g.rgb((0.66, 0.45, 0.27)))
    c = g.mix(g.reg(9), c, lth)
    skin_ = g.mix(g.remap(g.noise(p, 7.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(head), g.rgb((0.84, 0.76, 0.6)))
    skin_ = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 2.0), 0.58, 0.68), 0.35), skin_, g.rgb((0.74, 0.62, 0.46)))
    c = g.mix(g.reg(10), c, skin_)
    c = g.mix(g.math("MULTIPLY", g.reg(13), 0.6), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.62, 0.56, 0.46)), g.rgb((0.72, 0.66, 0.54))))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.76, 0.54, 0.2)), g.rgb((1.0, 0.86, 0.52)))
    c = g.mix(g.reg(11), c, br)
    gloss = g.mixf(g.math("MAXIMUM", g.reg(8), g.reg(10)), 0.42, 0.8)
    rough = g.mixf(g.reg(11), g.mixf(g.reg(9), gloss, 0.6), 0.28)
    h = g.math("ADD", g.math("MULTIPLY", tw, g.math("MULTIPLY", g.reg(8), 1.5)), g.math("MULTIPLY", g.noise(p, 60.0, 2.0), 0.3))
    return g.finish(c, rough, g.bump(h, 0.25, 0.002))


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


# ======================================================================================= Gunpowder Age (the Musketeer)
def matchlock(name="HQ_Matchlock", wood=(0.42, 0.22, 0.11), wood2=(0.27, 0.13, 0.065), ash=(0.68, 0.53, 0.34)):
    """Arms and kit of the Gunpowder Age: oiled walnut (label 0, its grain along Y; 10 along X; 11 along Z), darker in
    the hollows, pale on worn edges; pale ash (14); brass (5); forged iron (6, _iron_col); polished steel (7); twisted
    hemp match cord (8); brown leather (9); a charred black match end (12); black paint or leather, worn through to a
    sheen on the edges (13)."""
    g = new(name)
    p = g.obj()
    gy = g.noise(g.scale_vec(p, (60.0, 3.0, 60.0)), 1.0, 4.0, 0.62)
    gx = g.noise(g.scale_vec(p, (3.0, 60.0, 60.0)), 1.0, 4.0, 0.62)
    gz = g.noise(g.scale_vec(p, (60.0, 60.0, 3.0)), 1.0, 4.0, 0.62)
    gr = g.mixf(g.reg(11), g.mixf(g.reg(10), gy, gx), gz)
    c = g.mix(g.remap(gr, 0.3, 0.7, 0.0, 1.0), g.rgb(wood), g.rgb(wood2))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(g.scale_vec(p, (14.0, 1.5, 14.0)), 1.0, 3.0), 0.55, 0.7), 0.4), c,
              g.rgb(tuple(x * 0.6 for x in wood2)))                                          # walnut figure
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.5), c, g.rgb((0.12, 0.06, 0.03)))
    worn = g.smooth(pt, 0.51, 0.57)
    c = g.mix(g.math("MULTIPLY", worn, 0.45), c, g.rgb(tuple(min(1.0, x * 1.55) for x in wood)))
    ashc = g.mix(g.remap(gr, 0.3, 0.7, 0.0, 1.0), g.rgb(ash), g.rgb(tuple(x * 0.8 for x in ash)))
    ashc = g.mix(g.math("MULTIPLY", worn, 0.4), ashc, g.rgb(tuple(min(1.0, x * 1.15) for x in ash)))
    c = g.mix(g.reg(14), c, ashc)
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.76, 0.54, 0.2)), g.rgb((1.0, 0.88, 0.56)))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), br, g.rgb((0.36, 0.22, 0.08)))
    c = g.mix(g.reg(5), c, br)
    ic, rs = _iron_col(g, p)
    c = g.mix(g.reg(6), c, ic)
    sc, _ = _iron_col(g, p, base=(0.5, 0.52, 0.56), hi=(0.92, 0.94, 0.97), dark=(0.15, 0.15, 0.17), rust=(0.42, 0.26, 0.14))
    c = g.mix(g.reg(7), c, sc)
    tw = g.wave(p, 240.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(8), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb((0.56, 0.45, 0.32)), g.rgb((0.32, 0.25, 0.17))))
    hide = g.mix(g.noise(p, 9.0, 3.0), g.rgb((0.34, 0.2, 0.1)), g.rgb((0.45, 0.28, 0.14)))
    hide = g.mix(g.math("MULTIPLY", worn, 0.5), hide, g.rgb((0.62, 0.43, 0.26)))
    c = g.mix(g.reg(9), c, hide)
    blk = g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.055, 0.05, 0.05)), g.rgb((0.11, 0.1, 0.095)))
    blk = g.mix(g.math("MULTIPLY", worn, 0.6), blk, g.rgb((0.32, 0.29, 0.26)))
    c = g.mix(g.reg(13), c, blk)
    c = g.mix(g.reg(12), c, g.mix(g.noise(p, 60.0, 2.0), g.rgb((0.04, 0.035, 0.03)), g.rgb((0.2, 0.17, 0.15))))
    rough = g.mixf(g.reg(5), g.mixf(g.reg(14), 0.5, 0.62), 0.3)
    rough = g.mixf(g.reg(6), rough, g.mixf(rs, 0.4, 0.8))
    rough = g.mixf(g.reg(7), rough, 0.26)
    rough = g.mixf(g.math("MAXIMUM", g.reg(8), g.reg(12)), rough, 0.9)
    rough = g.mixf(g.reg(9), rough, 0.62)
    rough = g.mixf(g.reg(13), rough, 0.42)
    h = g.math("ADD", g.math("MULTIPLY", gr, 0.6), g.math("MULTIPLY", tw, g.math("MULTIPLY", g.reg(8), 1.5)))
    h = g.math("ADD", h, g.math("MULTIPLY", g.noise(p, 90.0, 2.0), g.math("MAXIMUM", g.reg(6), g.reg(9))))
    return g.finish(c, rough, g.bump(h, 0.28, 0.003))


def plume(name="HQ_Plume", col=(0.55, 0.08, 0.08), col2=(0.95, 0.93, 0.87)):
    """Ostrich plumes: soft, fluffy barbs, label 0 in `col`, label 5 in `col2`; darker in the hollows between the
    fronds, lighter on their crests, fine barb lines."""
    g = new(name)
    p = g.obj()
    barbs = g.wave(p, 150.0, 4.0, 2.0, "BANDS", "DIAGONAL")
    fluff = g.noise(p, 110.0, 2.0, 0.6)
    c0 = g.mix(g.remap(g.noise(p, 10.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb(col), g.rgb(tuple(min(1.0, x * 1.3) for x in col)))
    c1 = g.mix(g.remap(g.noise(p, 10.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb(col2), g.rgb(tuple(x * 0.86 for x in col2)))
    c = g.mix(g.reg(5), c0, c1)
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.49, 0.43), 0.55), c, g.rgb((0.45, 0.42, 0.42)), blend="MULTIPLY")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.3), c, g.rgb((0.3, 0.27, 0.25)), blend="ADD")
    c = g.mix(g.math("MULTIPLY", g.smooth(barbs, 0.6, 0.9), 0.28), c, g.rgb((0.6, 0.58, 0.56)), blend="MULTIPLY")
    return g.finish(c, 0.88, g.bump(g.math("ADD", g.math("MULTIPLY", barbs, 0.6), fluff), 0.32, 0.002))


# ======================================================================================= Gunpowder Age: Isla (v0.9.5x)
def armory(name="HQ_Armory", wood=(0.42, 0.23, 0.11), wood2=(0.26, 0.13, 0.06), grip=(0.08, 0.065, 0.06), copper=None):
    """Arms of the Gunpowder Age: walnut stocks with a fine grain and a darker figure, pale where handled, dark in the
    joints (label 0); black leather or cord (5); polished brass (6); bright steel (7); dark forged iron (8); gun bronze (9).
    `copper` = (colour, highlight): label 9 is polished copper instead of gun bronze (no green patina; Industrial Age)."""
    g = new(name)
    p = g.obj()
    grain = g.noise(g.scale_vec(p, (90.0, 90.0, 90.0)), 1.0, 3.0, 0.6)
    fig = g.wave(p, 18.0, 6.0, 3.0, "BANDS", "DIAGONAL")
    c = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb(wood), g.rgb(wood2))
    c = g.mix(g.math("MULTIPLY", g.smooth(fig, 0.55, 0.8), 0.35), c, g.rgb(tuple(x * 0.7 for x in wood2)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.45), c, g.rgb(tuple(min(1.0, x * 1.5) for x in wood)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), c, g.rgb((0.1, 0.05, 0.03)))
    lea = g.mix(g.noise(p, 40.0, 2.0), g.rgb(grip), g.rgb(tuple(min(1.0, x * 1.8) for x in grip)))
    c = g.mix(g.reg(5), c, lea)
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.8, 0.6, 0.24)), g.rgb((1.0, 0.9, 0.56)))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), br, g.rgb((0.38, 0.24, 0.08)))
    c = g.mix(g.reg(6), c, br)
    st, _r1 = _iron_col(g, p, base=(0.56, 0.58, 0.62), hi=(0.95, 0.96, 0.98), dark=(0.2, 0.2, 0.23), rust=(0.42, 0.3, 0.2))
    c = g.mix(g.reg(7), c, st)
    ir, rs = _iron_col(g, p, base=(0.2, 0.2, 0.22), hi=(0.56, 0.57, 0.6), dark=(0.06, 0.06, 0.07), rust=(0.42, 0.2, 0.09))
    c = g.mix(g.reg(8), c, ir)
    bz0, bz1 = copper if copper is not None else ((0.66, 0.42, 0.18), (0.96, 0.76, 0.44))
    bz = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.75), g.rgb(bz0), g.rgb(bz1))
    bz = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), bz, g.rgb((0.28, 0.16, 0.07) if copper is None else (0.3, 0.11, 0.05)))
    if copper is None:
        pat = g.math("MULTIPLY", g.smooth(pt, 0.47, 0.42), g.smooth(g.noise(p, 12.0, 3.0), 0.5, 0.64))
        bz = g.mix(g.math("MULTIPLY", pat, 0.6), bz, g.rgb((0.3, 0.52, 0.44)))
    c = g.mix(g.reg(9), c, bz)
    metal = g.math("MAXIMUM", g.math("MAXIMUM", g.reg(6), g.reg(7)), g.math("MAXIMUM", g.reg(8), g.reg(9)))
    rough = g.mixf(metal, g.mixf(g.reg(5), 0.55, 0.7), g.mixf(g.reg(8), 0.25, g.mixf(rs, 0.4, 0.8)))
    h = g.math("ADD", g.math("MULTIPLY", grain, g.math("SUBTRACT", 1.0, metal)), g.math("MULTIPLY", g.noise(p, 70.0, 2.0), 0.2))
    return g.finish(c, rough, g.bump(h, 0.12, 0.0015))


def timber(name="HQ_Timber", wood=(0.58, 0.52, 0.44), wood2=(0.4, 0.35, 0.29), worn=(0.8, 0.77, 0.7), stain=(0.36, 0.2, 0.1)):
    """Sea-weathered timber: silver-grey planks and posts, the grain along Y (label 0), X (10) or Z (11), dark in the
    cracks and joints, pale and smooth on worn edges; 5 = tarred and wet (dark, green weed at a post's foot); 6 = forged
    iron (bolts, bands, a bollard); 7 = brass; 8 = hemp rope; 9 = stained, oiled wood (a sea chest)."""
    g = new(name)
    p = g.obj()
    gy = g.noise(g.scale_vec(p, (70.0, 3.0, 70.0)), 1.0, 4.0, 0.62)
    gx = g.noise(g.scale_vec(p, (3.0, 70.0, 70.0)), 1.0, 4.0, 0.62)
    gz = g.noise(g.scale_vec(p, (70.0, 70.0, 3.0)), 1.0, 4.0, 0.62)
    gr = g.mixf(g.reg(11), g.mixf(g.reg(10), gy, gx), gz)
    c = g.mix(g.remap(gr, 0.3, 0.7, 0.0, 1.0), g.rgb(wood), g.rgb(wood2))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 2.2, 2.0), 0.45, 0.7), 0.35), c, g.rgb(tuple(x * 0.72 for x in wood2)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.65), c, g.rgb((0.14, 0.12, 0.1)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.55), c, g.rgb(worn))
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    tar = g.mix(g.noise(p, 9.0, 3.0), g.rgb((0.12, 0.1, 0.08)), g.rgb((0.2, 0.17, 0.12)))
    weed = g.math("MULTIPLY", g.smooth(sep.outputs["Z"], 0.24, 0.14), g.smooth(g.noise(p, 14.0, 3.0), 0.4, 0.6))
    tar = g.mix(g.math("MULTIPLY", weed, 0.8), tar, g.rgb((0.2, 0.32, 0.14)))
    c = g.mix(g.reg(5), c, tar)
    ic, rs = _iron_col(g, p, base=(0.22, 0.22, 0.24), hi=(0.56, 0.57, 0.6), dark=(0.06, 0.06, 0.07), rust=(0.5, 0.24, 0.1))
    c = g.mix(g.reg(6), c, ic)
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.8, 0.6, 0.24)), g.rgb((1.0, 0.9, 0.56)))
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), br, g.rgb((0.38, 0.24, 0.08)))
    c = g.mix(g.reg(7), c, br)
    tw = g.wave(p, 240.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(8), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb((0.8, 0.68, 0.48)), g.rgb((0.52, 0.4, 0.25))))
    st = g.mix(g.remap(gr, 0.3, 0.7, 0.0, 1.0), g.rgb(stain), g.rgb(tuple(x * 0.62 for x in stain)))
    st = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.45), st, g.rgb(tuple(min(1.0, x * 1.6) for x in stain)))
    c = g.mix(g.reg(9), c, st)
    rough = g.mixf(g.reg(6), g.mixf(g.math("MAXIMUM", g.reg(5), g.reg(9)), 0.88, 0.45), g.mixf(rs, 0.4, 0.8))
    rough = g.mixf(g.reg(7), rough, 0.3)
    h = g.math("ADD", g.math("MULTIPLY", gr, 0.9), g.math("MULTIPLY", tw, g.math("MULTIPLY", g.reg(8), 1.5)))
    return g.finish(c, rough, g.bump(h, 0.35, 0.003))


def beach_sand(name="HQ_BeachSand", base=(0.86, 0.75, 0.55), hi=(0.95, 0.88, 0.7), side=(0.62, 0.5, 0.34)):
    """A sandy shore: pale warm sand on top, fine dark and bright grains, soft wind ripples, flecks of broken shell; damp,
    darker sand in layers down its sides; label 5 = wet sand (darker, glossy) where the tide reached."""
    g = new(name)
    p = g.obj()
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    top = g.smooth(nz.outputs["Z"], 0.4, 0.75)
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.35, 0.65, 0.0, 1.0), g.rgb(base), g.rgb(hi))
    rip = g.wave(g.scale_vec(p, (1.0, 0.55, 1.0)), 7.0, 4.0, 2.0, "BANDS", "X")
    c = g.mix(g.math("MULTIPLY", g.smooth(rip, 0.55, 0.85), 0.22), c, g.rgb(tuple(x * 0.84 for x in base)))
    grains = g.noise(p, 170.0, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(grains, 0.63, 0.7), 0.4), c, g.rgb((0.52, 0.42, 0.3)))
    c = g.mix(g.math("MULTIPLY", g.smooth(grains, 0.33, 0.27), 0.35), c, g.rgb((1.0, 0.98, 0.92)))
    flk = g.smooth(g.voronoi(p, 34.0), 0.07, 0.03)
    c = g.mix(g.math("MULTIPLY", flk, 0.45), c, g.rgb((0.98, 0.9, 0.86)))
    sd = g.mix(g.noise(p, 6.0, 3.0), g.rgb(side), g.rgb(tuple(x * 0.82 for x in side)))
    strata = g.wave(p, 6.0, 3.0, 2.0, "BANDS", "Z")
    sd = g.mix(g.math("MULTIPLY", g.smooth(strata, 0.6, 0.8), 0.3), sd, g.rgb(tuple(x * 0.7 for x in side)))
    c = g.mix(top, sd, c)
    wet = g.mix(g.noise(p, 8.0, 2.0), g.rgb((0.56, 0.46, 0.32)), g.rgb((0.64, 0.53, 0.38)))
    c = g.mix(g.reg(5), c, wet)
    rough = g.mixf(g.reg(5), 0.95, 0.45)
    h = g.math("ADD", g.math("MULTIPLY", g.math("MULTIPLY", rip, top), 0.6), g.math("MULTIPLY", grains, 0.5))
    return g.finish(c, rough, g.bump(h, 0.3, 0.004))


# ======================================================================================= Industrial Age (the Tesla Coil)
def electric(name="HQ_Electric", copper=(0.75, 0.35, 0.18), brass=(0.8, 0.55, 0.22), iron=(0.17, 0.17, 0.19),
             wood=(0.5, 0.27, 0.11), porcelain=(0.93, 0.91, 0.86), rubber=(0.07, 0.07, 0.075), slate=(0.22, 0.24, 0.27),
             glass=(0.12, 0.36, 0.26), enamel=(0.95, 0.92, 0.82), paint=(0.62, 0.1, 0.07), leather=(0.4, 0.23, 0.11)):
    """Electrical apparatus of the Industrial Age, hand-painted: polished copper (label 0: bright on edges and ridges and on
    faces turned to the sky, dark in the recesses, a trace of verdigris in the deepest crevices); brass (5); soot-black
    riveted iron (6, _iron_col); varnished wood with the grain along Z (7); glazed porcelain (8, glossy); black rubber and
    ebonite (9, a soft sheen); slate (10, matte, fine speckle); copper winding (11: fine wire turns round Z); bottle-green
    glass (12); cream enamel dials (13); red paint (14); brown leather (4)."""
    g = new(name)
    p = g.obj()
    pt = g.geo("Pointiness")
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    up = g.smooth(nz.outputs["Z"], 0.3, 0.95)
    ridge, hollow = g.smooth(pt, 0.51, 0.56), g.smooth(pt, 0.48, 0.43)
    def metal(base, hi, dark):
        c = g.mix(g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1.0, x * 1.15) for x in base)))
        c = g.mix(g.math("MULTIPLY", ridge, 0.75), c, g.rgb(hi))
        c = g.mix(g.math("MULTIPLY", hollow, 0.6), c, g.rgb(dark))
        return g.mix(g.math("MULTIPLY", up, 0.28), c, g.rgb(hi))
    cu = metal(copper, (1.0, 0.74, 0.52), (0.3, 0.12, 0.06))
    verd = g.math("MULTIPLY", g.smooth(pt, 0.46, 0.41), g.smooth(g.noise(p, 12.0, 3.0), 0.52, 0.66))
    c = g.mix(g.math("MULTIPLY", verd, 0.6), cu, g.rgb((0.3, 0.55, 0.45)))
    c = g.mix(g.reg(5), c, metal(brass, (1.0, 0.88, 0.56), (0.34, 0.2, 0.06)))
    ir, rs = _iron_col(g, p, base=iron, hi=(0.5, 0.52, 0.56), dark=(0.04, 0.04, 0.045), rust=(0.42, 0.2, 0.09))
    c = g.mix(g.reg(6), c, ir)
    gz = g.noise(g.scale_vec(p, (60.0, 60.0, 3.0)), 1.0, 4.0, 0.62)
    wd = g.mix(g.remap(gz, 0.3, 0.7, 0.0, 1.0), g.rgb(wood), g.rgb(tuple(x * 0.66 for x in wood)))
    wd = g.mix(g.math("MULTIPLY", ridge, 0.4), wd, g.rgb(tuple(min(1.0, x * 1.5) for x in wood)))
    c = g.mix(g.reg(7), c, wd)
    pc = g.mix(g.math("MULTIPLY", hollow, 0.5), g.rgb(porcelain), g.rgb(tuple(x * 0.72 for x in porcelain)))
    pc = g.mix(g.math("MULTIPLY", ridge, 0.6), pc, g.rgb((1.0, 1.0, 0.98)))
    c = g.mix(g.reg(8), c, pc)
    rb = g.mix(g.math("MULTIPLY", ridge, 0.5), g.rgb(rubber), g.rgb(tuple(min(1.0, x * 2.6 + 0.06) for x in rubber)))
    c = g.mix(g.reg(9), c, rb)
    sl = g.mix(g.remap(g.noise(p, 9.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(slate), g.rgb(tuple(x * 0.8 for x in slate)))
    sl = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 160.0, 2.0), 0.64, 0.7), 0.4), sl, g.rgb(tuple(min(1.0, x * 1.5) for x in slate)))
    sl = g.mix(g.math("MULTIPLY", ridge, 0.45), sl, g.rgb(tuple(min(1.0, x * 1.7) for x in slate)))
    c = g.mix(g.reg(10), c, sl)
    turns = g.wave(p, 520.0, 0.0, 0.0, "BANDS", "Z")
    wcol = g.mix(g.math("MULTIPLY", g.smooth(turns, 0.25, 0.75), 0.55), g.rgb(tuple(x * 0.62 for x in copper)), cu)
    c = g.mix(g.reg(11), c, wcol)
    c = g.mix(g.reg(12), c, g.mix(g.math("MULTIPLY", ridge, 0.6), g.rgb(glass), g.rgb((0.55, 0.85, 0.7))))
    c = g.mix(g.reg(13), c, g.mix(g.math("MULTIPLY", hollow, 0.4), g.rgb(enamel), g.rgb(tuple(x * 0.8 for x in enamel))))
    c = g.mix(g.reg(14), c, g.mix(g.math("MULTIPLY", ridge, 0.4), g.rgb(paint), g.rgb(tuple(min(1.0, x * 1.4) for x in paint))))
    lt = g.mix(g.noise(p, 9.0, 3.0), g.rgb(leather), g.rgb(tuple(min(1.0, x * 1.25) for x in leather)))
    c = g.mix(g.reg(4), c, g.mix(g.math("MULTIPLY", ridge, 0.5), lt, g.rgb((0.62, 0.42, 0.25))))
    rough = g.mixf(g.reg(5), g.mixf(verd, 0.26, 0.7), 0.3)
    rough = g.mixf(g.reg(6), rough, g.mixf(rs, 0.5, 0.85))
    rough = g.mixf(g.reg(7), rough, 0.42)
    rough = g.mixf(g.reg(8), rough, 0.16)
    rough = g.mixf(g.reg(9), rough, 0.5)
    rough = g.mixf(g.reg(10), rough, 0.85)
    rough = g.mixf(g.reg(12), rough, 0.1)
    rough = g.mixf(g.math("MAXIMUM", g.reg(13), g.reg(14)), rough, 0.4)
    rough = g.mixf(g.reg(4), rough, 0.62)
    h = g.math("ADD", g.math("MULTIPLY", g.voronoi(p, 80.0, 1.0, "F1", "Distance"), g.math("MULTIPLY", g.reg(6), 0.3)),
               g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.15))
    h = g.math("ADD", h, g.math("MULTIPLY", turns, g.math("MULTIPLY", g.reg(11), 0.6)))
    h = g.math("ADD", h, g.math("MULTIPLY", gz, g.math("MULTIPLY", g.reg(7), 0.5)))
    return g.finish(c, rough, g.bump(h, 0.22, 0.002))


# ======================================================================================= Industrial Age: the Steam Brawler
def steamworks(name="HQ_Steamworks", iron=(0.13, 0.13, 0.14), brass=(0.8, 0.55, 0.22), copper=(0.75, 0.35, 0.18),
               leather=(0.36, 0.21, 0.11), enamel=(0.93, 0.89, 0.76), paint=(0.7, 0.1, 0.06), glass=(0.16, 0.36, 0.26)):
    """Steam-age engineering, hand-painted: soot-black riveted iron (label 0, _iron_col: bright on its edges and ridges,
    rust in the deepest crevices); polished brass (5); copper (6, a little verdigris in the crevices); bright steel (7: rams,
    piston rods); black rubber (8, dull, fine ribs); brown leather (9); cream enamel (10: a gauge's dial); red paint (11: its
    needle, a valve wheel); black leather (12: boots, worn grey on the edges); green glass (13: goggle lenses, glossy)."""
    g = new(name)
    p = g.obj()
    pt = g.geo("Pointiness")
    hi_ = g.smooth(pt, 0.5, 0.56)
    lo_ = g.smooth(pt, 0.48, 0.43)
    c, rs = _iron_col(g, p, base=iron, hi=tuple(min(1.0, x * 3.6) for x in iron), dark=tuple(x * 0.35 for x in iron),
                      rust=(0.36, 0.17, 0.07))
    br = g.mix(g.math("MULTIPLY", hi_, 0.8), g.rgb(brass), g.rgb(tuple(min(1.0, x * 1.3 + 0.12) for x in brass)))
    br = g.mix(g.math("MULTIPLY", lo_, 0.6), br, g.rgb(tuple(x * 0.45 for x in brass)))
    c = g.mix(g.reg(5), c, br)
    cu = g.mix(g.remap(g.noise(p, 8.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(copper), g.rgb(tuple(x * 0.82 for x in copper)))
    cu = g.mix(g.math("MULTIPLY", hi_, 0.75), cu, g.rgb(tuple(min(1.0, x * 1.35 + 0.1) for x in copper)))
    cu = g.mix(g.math("MULTIPLY", lo_, 0.55), cu, g.rgb(tuple(x * 0.4 for x in copper)))
    vg = g.math("MULTIPLY", g.smooth(pt, 0.46, 0.41), g.smooth(g.noise(p, 12.0, 3.0), 0.5, 0.64))
    cu = g.mix(g.math("MULTIPLY", vg, 0.6), cu, g.rgb((0.3, 0.52, 0.42)))
    c = g.mix(g.reg(6), c, cu)
    st, _r = _iron_col(g, p, base=(0.58, 0.6, 0.64), hi=(0.96, 0.97, 0.99), dark=(0.22, 0.22, 0.25), rust=(0.42, 0.3, 0.2))
    c = g.mix(g.reg(7), c, st)
    rib = g.wave(p, 220.0, 0.5, 0.0, "BANDS", "DIAGONAL")
    rb = g.mix(g.math("MULTIPLY", rib, 0.4), g.rgb((0.045, 0.043, 0.045)), g.rgb((0.1, 0.095, 0.095)))
    rb = g.mix(g.math("MULTIPLY", hi_, 0.5), rb, g.rgb((0.22, 0.21, 0.2)))
    c = g.mix(g.reg(8), c, rb)
    lea = g.mix(g.noise(p, 9.0, 3.0), g.rgb(leather), g.rgb(tuple(min(1.0, x * 1.3) for x in leather)))
    lea = g.mix(g.math("MULTIPLY", hi_, 0.5), lea, g.rgb(tuple(min(1.0, x * 1.7) for x in leather)))
    c = g.mix(g.reg(9), c, lea)
    en = g.mix(g.noise(p, 30.0, 2.0), g.rgb(enamel), g.rgb(tuple(x * 0.9 for x in enamel)))
    c = g.mix(g.reg(10), c, en)
    c = g.mix(g.reg(11), c, g.rgb(paint))
    bl = g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.05, 0.046, 0.045)), g.rgb((0.1, 0.092, 0.088)))
    bl = g.mix(g.math("MULTIPLY", hi_, 0.6), bl, g.rgb((0.34, 0.32, 0.3)))
    c = g.mix(g.reg(12), c, bl)
    gl = g.mix(g.math("MULTIPLY", hi_, 0.7), g.rgb(glass), g.rgb(tuple(min(1.0, x * 2.4 + 0.2) for x in glass)))
    c = g.mix(g.reg(13), c, gl)
    rough = g.mixf(rs, 0.42, 0.8)
    rough = g.mixf(g.math("MAXIMUM", g.reg(5), g.reg(6)), rough, 0.3)
    rough = g.mixf(g.reg(7), rough, 0.22)
    rough = g.mixf(g.reg(8), rough, 0.85)
    rough = g.mixf(g.math("MAXIMUM", g.reg(9), g.reg(12)), rough, 0.6)
    rough = g.mixf(g.math("MAXIMUM", g.reg(10), g.reg(11)), rough, 0.35)
    rough = g.mixf(g.reg(13), rough, 0.08)
    ham = g.voronoi(p, 80.0, 1.0, "F1", "Distance")
    h = g.math("ADD", g.math("MULTIPLY", ham, 0.25), g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.2))
    h = g.math("ADD", h, g.math("MULTIPLY", rib, g.math("MULTIPLY", g.reg(8), 0.8)))
    return g.finish(c, rough, g.bump(h, 0.14, 0.002))


# ======================================================================================= Industrial Age (the Field Gun)
def _brass_col(g, pt, base=(0.8, 0.55, 0.22)):
    """Polished brass: bright on edges and ridges, dark in the recesses."""
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb(base), g.rgb((1.0, 0.9, 0.58)))
    return g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), br, g.rgb((0.36, 0.22, 0.07)))


def uniform(name="HQ_Uniform", base=(0.18, 0.22, 0.42), facing=(0.62, 0.09, 0.07), brass=(0.8, 0.55, 0.22),
            buff=(0.74, 0.6, 0.38), black=(0.06, 0.055, 0.06)):
    """The Industrial Age corps' uniform cloth: navy wool (label 0) with a fine weave, darker in the folds and a lighter
    nap on the ridges; facings (5: a collar, piping, a trouser stripe), polished brass (6: buttons, badges), buff braid or
    a cap band (7), black patent leather (8: a cap's peak and chin strap, glossy)."""
    g = new(name)
    p = g.obj()
    weave = g.math("ADD", g.wave(p, 300.0, 0.0, 0.0, "BANDS", "X"), g.wave(p, 300.0, 0.0, 0.0, "BANDS", "Z"))
    pt = g.geo("Pointiness")
    def cloth(col):
        c = g.mix(g.remap(g.noise(p, 7.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(col), g.rgb(tuple(x * 0.8 for x in col)))
        c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.49, 0.43), 0.6), c, g.rgb(tuple(x * 0.5 for x in col)))
        return g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.45), c, g.rgb(tuple(min(1.0, x * 1.5 + 0.06) for x in col)))
    c = cloth(base)
    c = g.mix(g.reg(5), c, cloth(facing))
    c = g.mix(g.reg(7), c, cloth(buff))
    blk = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.7), g.rgb(black), g.rgb((0.36, 0.36, 0.4)))
    c = g.mix(g.reg(8), c, blk)
    c = g.mix(g.reg(6), c, _brass_col(g, pt, brass))
    rough = g.mixf(g.reg(6), g.mixf(g.reg(8), 0.9, 0.22), 0.28)
    h = g.math("MULTIPLY", weave, g.math("SUBTRACT", 1.0, g.math("MAXIMUM", g.reg(6), g.reg(8))))
    return g.finish(c, rough, g.bump(h, 0.16, 0.0014))


def fieldgun(name="HQ_FieldGun", olive=(0.33, 0.34, 0.2), grey=(0.3, 0.32, 0.34), brass=(0.8, 0.55, 0.22),
             wood=(0.55, 0.38, 0.22), copper=(0.75, 0.35, 0.18), red=(0.72, 0.1, 0.07), white=(0.9, 0.88, 0.82)):
    """A steel field gun of about 1900: olive-drab paint (label 0) and gunmetal-grey paint (5), both chipped back to the
    steel on the edges and grimy in the recesses, rivet heads catching the light; polished brass (6); bright machined
    steel (7: a breech face, worn tyres); black enamel and dark iron (8); oiled wood (9); cord (10); copper (11); red (12)
    and white (13) paint (a range marker's bands)."""
    g = new(name)
    p = g.obj()
    pt = g.geo("Pointiness")
    brush = g.remap(g.noise(g.scale_vec(p, (60.0, 60.0, 60.0)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    def paint(col):
        c = g.mix(g.math("MULTIPLY", brush, 0.25), g.rgb(col), g.rgb(tuple(x * 0.8 for x in col)))
        c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 2.0), 0.45, 0.7), 0.25), c, g.rgb(tuple(x * 0.72 for x in col)))
        return g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.4), c, g.rgb(tuple(min(1.0, x * 1.35 + 0.04) for x in col)))
    steel, rs = _iron_col(g, p, base=(0.42, 0.43, 0.46), hi=(0.82, 0.84, 0.88), dark=(0.14, 0.14, 0.16), rust=(0.45, 0.24, 0.12))
    chip = g.math("MULTIPLY", g.smooth(pt, 0.535, 0.6), g.smooth(g.noise(p, 26.0, 2.0), 0.45, 0.56))
    c = g.mix(chip, paint(olive), steel)
    c = g.mix(g.reg(5), c, g.mix(chip, paint(grey), steel))
    c = g.mix(g.reg(12), c, g.mix(chip, paint(red), steel))
    c = g.mix(g.reg(13), c, g.mix(chip, paint(white), steel))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.55), c, g.rgb((0.1, 0.09, 0.07)))            # grime in the recesses
    c = g.mix(g.reg(7), c, steel)
    blk, _r = _iron_col(g, p, base=(0.07, 0.07, 0.075), hi=(0.4, 0.41, 0.44), dark=(0.02, 0.02, 0.02), rust=(0.2, 0.12, 0.07))
    c = g.mix(g.reg(8), c, blk)
    wd = g.mix(g.noise(g.scale_vec(p, (60.0, 60.0, 6.0)), 1.0, 3.0), g.rgb(wood), g.rgb(tuple(x * 0.7 for x in wood)))
    c = g.mix(g.reg(9), c, wd)
    tw = g.wave(p, 260.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(10), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb((0.8, 0.7, 0.5)), g.rgb((0.52, 0.42, 0.28))))
    c = g.mix(g.reg(6), c, _brass_col(g, pt, brass))
    c = g.mix(g.reg(11), c, _brass_col(g, pt, copper))
    metal = g.math("MAXIMUM", g.math("MAXIMUM", g.reg(6), g.reg(11)), g.reg(7))
    rough = g.mixf(metal, g.mixf(chip, g.mixf(g.math("MAXIMUM", g.reg(9), g.reg(10)), 0.62, 0.8), 0.35), 0.26)
    rough = g.mixf(g.reg(8), rough, 0.35)
    h = g.math("ADD", g.math("MULTIPLY", brush, 0.3), g.math("MULTIPLY", g.noise(p, 90.0, 2.0), 0.25))
    h = g.math("ADD", h, g.math("MULTIPLY", tw, g.math("MULTIPLY", g.reg(10), 1.5)))
    return g.finish(c, rough, g.bump(h, 0.12, 0.002))


def sacking(name="HQ_Sacking", base=(0.62, 0.5, 0.33), dark=(0.42, 0.33, 0.2), stencil=(0.12, 0.1, 0.08)):
    """Sandbags: coarse jute sacking, a loose open weave, dusty and pale on the bulges, dark and damp in the creases and
    between the bags; label 5 = a stencilled mark (dark), 6 = twine (pale)."""
    g = new(name)
    p = g.obj()
    weave = g.math("ADD", g.wave(p, 170.0, 0.0, 0.0, "BANDS", "X"), g.wave(p, 170.0, 0.0, 0.0, "BANDS", "Z"))
    weave = g.math("ADD", weave, g.wave(p, 170.0, 0.0, 0.0, "BANDS", "Y"))
    c = g.mix(g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(x * 0.86 for x in base)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.49, 0.43), 0.75), c, g.rgb(dark))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.4), c, g.rgb(tuple(min(1.0, x * 1.25) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 2.0), 0.55, 0.7), 0.3), c, g.rgb((0.38, 0.3, 0.2)))   # earth stains
    c = g.mix(g.math("MULTIPLY", g.reg(5), 0.85), c, g.rgb(stencil))
    c = g.mix(g.reg(6), c, g.rgb((0.82, 0.74, 0.56)))
    return g.finish(c, 0.95, g.bump(weave, 0.3, 0.0016))


# ======================================================================================= Industrial Age: red brick (the Rifleman)
def red_brick(name="HQ_RedBrick", base=(0.6, 0.25, 0.16), alt=(0.48, 0.2, 0.13), mortar=(0.66, 0.62, 0.55),
              blue=(0.2, 0.22, 0.27), soot=(0.09, 0.08, 0.075), course=0.07, brick=0.2, radial=0.0):
    """Fired red brick in stretcher bond: each brick a little lighter or darker than its neighbours, pale mortar joints
    sunk in the normal map, worn pale edges; label 5 = blue engineering bricks (copings, glossier), 6 = soot and grime.
    `radial` > 0: the bricks run round a drum of that radius (the courses follow the angle about the z axis, not x + y)."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    z = sep.outputs["Z"]
    row = g.math("FLOOR", g.math("DIVIDE", z, course))
    fz = g.math("SUBTRACT", g.math("DIVIDE", z, course), row)
    if radial > 0:
        along = g.math("MULTIPLY", g.math("ARCTAN2", sep.outputs["Y"], sep.outputs["X"]), radial)
    else:
        along = g.math("ADD", sep.outputs["X"], sep.outputs["Y"])
    run = g.math("ADD", along, g.math("MULTIPLY", g.math("MODULO", g.math("ADD", row, 1000.0), 2.0), brick * 0.5))
    col = g.math("FLOOR", g.math("DIVIDE", run, brick))
    fx = g.math("SUBTRACT", g.math("DIVIDE", run, brick), col)
    jz = g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz))
    jx = g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx))
    joint = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.smooth(jz, 0.05, 0.13)), g.math("SUBTRACT", 1.0, g.smooth(jx, 0.018, 0.045)))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    joint = g.math("MULTIPLY", joint, g.math("SUBTRACT", 1.0, g.smooth(nz.outputs["Z"], 0.75, 0.92)))
    rnd = g.math("FRACT", g.math("MULTIPLY", g.math("SINE", g.math("ADD", g.math("MULTIPLY", col, 12.9898), g.math("MULTIPLY", row, 78.233))), 43758.5453))
    c = g.mix(rnd, g.rgb(base), g.rgb(alt))
    c = g.mix(g.math("MULTIPLY", g.smooth(rnd, 0.82, 0.9), 0.6), c, g.rgb((0.68, 0.36, 0.22)))
    c = g.mix(g.remap(g.noise(p, 9.0, 3.0), 0.3, 0.7, 0.0, 0.35), c, g.rgb(tuple(x * 0.72 for x in alt)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 60.0, 2.0), 0.6, 0.68), 0.35), c, g.rgb(tuple(x * 0.6 for x in alt)))
    bl = g.mix(g.math("MULTIPLY", rnd, 0.6), g.rgb(blue), g.rgb(tuple(min(1.0, x * 1.3) for x in blue)))
    c = g.mix(g.reg(5), c, bl)
    c = g.mix(joint, c, g.rgb(mortar))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.4), c, g.rgb((0.8, 0.6, 0.48)))
    st = g.math("MULTIPLY", g.reg(6), g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.4, 0.95))
    c = g.mix(st, c, g.rgb(soot))
    rough = g.mixf(g.reg(5), 0.86, 0.45)
    h = g.math("ADD", g.math("MULTIPLY", joint, -0.7), g.math("MULTIPLY", g.noise(p, 40.0, 3.0), 0.25))
    return g.finish(c, rough, g.bump(h, 0.4, 0.006))


# ======================================================================================= Modern Age: cast concrete (the EMP Tower)
def field_concrete(name="HQ_FieldConcrete", base=(0.6, 0.6, 0.58), dark=(0.42, 0.42, 0.41), paint=(0.95, 0.75, 0.12),
                   paint2=(0.07, 0.07, 0.07), stain=(0.3, 0.29, 0.27)):
    """Cast concrete, hand-painted: a cool grey with a fine aggregate speckle and pores, darker blotches and grime in the
    hollows, pale worn edges; label 5 = yellow road paint (worn), 6 = black paint (hazard stripes), 7 = oil stains."""
    g = new(name)
    p = g.obj()
    pt = g.geo("Pointiness")
    c = g.mix(g.remap(g.noise(p, 4.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(x * 0.88 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 1.6, 2.0), 0.55, 0.7), 0.35), c, g.rgb(dark))
    agg = g.noise(p, 140.0, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(agg, 0.62, 0.7), 0.45), c, g.rgb(tuple(min(1.0, x * 1.25) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(agg, 0.34, 0.27), 0.5), c, g.rgb(dark))
    pores = g.smooth(g.voronoi(p, 70.0), 0.06, 0.03)
    c = g.mix(g.math("MULTIPLY", pores, 0.5), c, g.rgb(tuple(x * 0.6 for x in dark)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.49, 0.43), 0.6), c, g.rgb(tuple(x * 0.7 for x in dark)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.52, 0.58), 0.45), c, g.rgb(tuple(min(1.0, x * 1.3) for x in base)))
    wear = g.smooth(g.noise(p, 18.0, 3.0), 0.62, 0.7)
    pc = g.mix(g.math("MULTIPLY", wear, 0.7), g.rgb(paint), c)
    c = g.mix(g.reg(5), c, pc)
    c = g.mix(g.reg(6), c, g.mix(g.math("MULTIPLY", wear, 0.6), g.rgb(paint2), c))
    oil = g.math("MULTIPLY", g.reg(7), g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.45, 0.9))
    c = g.mix(oil, c, g.rgb(stain))
    rough = g.mixf(g.math("MAXIMUM", g.reg(5), g.reg(6)), 0.88, 0.6)
    rough = g.mixf(g.reg(7), rough, 0.4)
    h = g.math("ADD", g.math("MULTIPLY", agg, 0.4), g.math("MULTIPLY", pores, -0.6))
    return g.finish(c, rough, g.bump(h, 0.25, 0.002))
