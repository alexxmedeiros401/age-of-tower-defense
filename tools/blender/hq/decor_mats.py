"""Materials for the HQ Stone Age map kits (Cycles, baked into the kit's texture atlas).
Upward-facing surfaces take the theme's cover: moss and grass (meadow), snow (snow), ash (volcano)."""
import bpy
from mats import new, lin, stone, bone, wood, ground


def _up(g, lo=0.45, hi=0.8):
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], g.geo("Normal"))
    return g.smooth(sep.outputs["Z"], lo, hi)


def _cover(g, c, rough, theme, p, amount=1.0, lo=0.5, hi=0.8, cap=False):
    """Snow / ash on top-facing surfaces, broken up by noise. cap=True: a whole cap on top with a wavy edge (boulders,
    the cave) rather than scattered patches (branches)."""
    if theme not in ("snow", "volcano"):
        return c, rough
    if cap:
        sep = g.node("ShaderNodeSeparateXYZ")
        g.put(sep.inputs[0], g.geo("Normal"))
        wav = g.math("MULTIPLY", g.math("SUBTRACT", g.noise(p, 2.2, 3.0, 0.6), 0.5), 0.7)
        m = g.math("MULTIPLY", g.smooth(g.math("ADD", sep.outputs["Z"], wav), lo, hi), amount)
    else:
        up = _up(g, lo, hi)
        brk = g.smooth(g.noise(p, 3.0, 4.0, 0.6), 0.35, 0.55)
        m = g.math("MULTIPLY", g.math("MULTIPLY", up, brk), amount)
    if theme == "snow":
        sc = g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.86, 0.91, 0.99)), g.rgb((1.0, 1.0, 1.0)))
        return g.mix(m, c, sc), g.mixf(m, rough, 0.55)
    ash = g.mix(g.noise(p, 15.0, 2.0), g.rgb((0.3, 0.27, 0.25)), g.rgb((0.44, 0.4, 0.36)))
    return g.mix(g.math("MULTIPLY", m, 0.7), c, ash), rough


def needles(name="DK_Needles", theme="meadow"):
    """Pine foliage: deep green clumps, bright tips catching the light, dark inside; snow / ash on top."""
    g = new(name)
    p = g.obj()
    strands = g.noise(g.scale_vec(p, (30.0, 30.0, 60.0)), 1.0, 3.0, 0.6)
    base = g.mix(g.remap(g.noise(p, 2.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.1, 0.32, 0.12)), g.rgb((0.16, 0.42, 0.14)))
    tips = g.smooth(g.geo("Pointiness"), 0.51, 0.58)
    c = g.mix(g.math("MULTIPLY", tips, 0.8), base, g.rgb((0.42, 0.66, 0.2)))
    up = _up(g, 0.2, 0.9)
    c = g.mix(g.math("MULTIPLY", up, 0.35), c, g.rgb((0.3, 0.56, 0.18)))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.35
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.8), c, g.rgb((0.03, 0.12, 0.06)))
    c = g.mix(g.math("MULTIPLY", g.remap(strands, 0.3, 0.7, 0.0, 1.0), 0.25), c, g.rgb((0.06, 0.2, 0.08)))
    rough = 0.8
    if theme == "snow":
        c, rough = _cover(g, c, rough, theme, p, 1.0, 0.35, 0.65)
    return g.finish(c, rough, g.bump(strands, 0.5, 0.01))


def bark(name="DK_Bark", theme="meadow", charred=False):
    g = new(name)
    p = g.obj()
    grooves = g.wave(g.scale_vec(p, (1.0, 1.0, 0.25)), 9.0, 6.0, 3.0, "BANDS", "X")
    if charred:
        c = g.mix(g.remap(grooves, 0.3, 0.8, 0.0, 1.0), g.rgb((0.06, 0.05, 0.05)), g.rgb((0.2, 0.17, 0.15)))
        crack = g.smooth(grooves, 0.08, 0.02)
        c = g.mix(g.math("MULTIPLY", crack, g.smooth(g.noise(p, 4.0, 2.0), 0.5, 0.65)), c, g.rgb((1.0, 0.38, 0.06)))
    else:
        c = g.mix(g.remap(grooves, 0.3, 0.8, 0.0, 1.0), g.rgb((0.22, 0.13, 0.07)), g.rgb((0.44, 0.29, 0.17)))
        c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 6.0, 3.0), 0.55, 0.7), 0.4), c, g.rgb((0.5, 0.45, 0.36)))   # lichen
    rough = 0.85
    c, rough = _cover(g, c, rough, theme, p, 0.9)
    return g.finish(c, rough, g.bump(grooves, 0.6, 0.012))


def wood_end(name="DK_WoodEnd", theme="meadow", charred=False):
    """Stumps and logs: growth rings on the cut faces (by the cut's normal), bark round the sides."""
    g = new(name)
    p = g.obj()
    rings = g.wave(p, 18.0, 2.0, 2.0, "RINGS", "Z" if True else "X")
    rings_x = g.wave(p, 18.0, 2.0, 2.0, "RINGS", "X")
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], g.geo("Normal"))
    top = g.smooth(sep.outputs["Z"], 0.75, 0.9)
    side_cut = g.smooth(g.math("ABSOLUTE", sep.outputs["X"]), 0.8, 0.92)
    wood_c = g.mix(g.math("MAXIMUM", g.math("MULTIPLY", rings, top), g.math("MULTIPLY", rings_x, side_cut)),
                   g.rgb((0.72, 0.52, 0.3)), g.rgb((0.52, 0.34, 0.18)))
    grooves = g.wave(g.scale_vec(p, (1.0, 1.0, 0.25)), 9.0, 6.0, 3.0, "BANDS", "X")
    bark_c = g.mix(g.remap(grooves, 0.3, 0.8, 0.0, 1.0), g.rgb((0.22, 0.13, 0.07)), g.rgb((0.42, 0.28, 0.16)))
    cut = g.math("MAXIMUM", top, side_cut)
    if charred:
        wood_c = g.mix(rings, g.rgb((0.1, 0.07, 0.06)), g.rgb((0.6, 0.2, 0.05)))
        bark_c = g.mix(g.remap(grooves, 0.3, 0.8, 0.0, 1.0), g.rgb((0.05, 0.04, 0.04)), g.rgb((0.16, 0.13, 0.12)))
    c = g.mix(cut, bark_c, wood_c)
    if theme == "meadow":
        moss = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, cut), g.smooth(g.noise(p, 3.0, 3.0), 0.55, 0.62))
        c = g.mix(g.math("MULTIPLY", moss, 0.8), c, g.rgb((0.32, 0.5, 0.16)))
    rough = 0.82
    c, rough = _cover(g, c, rough, theme, p, 0.9, 0.55, 0.85)
    return g.finish(c, rough, g.bump(g.math("ADD", grooves, g.math("MULTIPLY", rings, 0.3)), 0.5, 0.008))


def leaves(name="DK_Leaves", base=(0.18, 0.42, 0.13), hi=(0.46, 0.7, 0.22), berries=None):
    """Bush clumps: leaf-shaped cells, bright tops and tips, dark hollows; berries as a painted label (1)."""
    g = new(name)
    p = g.obj()
    cells = g.voronoi(p, 26.0)
    leaf = g.smooth(cells, 0.35, 0.05)
    c = g.mix(g.remap(g.noise(p, 3.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(x * 1.25 for x in base)))
    c = g.mix(g.math("MULTIPLY", leaf, 0.45), c, g.rgb(hi))
    up = _up(g, 0.3, 0.9)
    c = g.mix(g.math("MULTIPLY", up, 0.35), c, g.rgb(hi))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.25
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.8), c, g.rgb((0.04, 0.12, 0.05)))
    if berries is not None:
        c = g.mix(g.reg(1), c, g.rgb(berries))
    return g.finish(c, 0.7, g.bump(leaf, 0.6, 0.01))


def rock(name="DK_Rock", theme="meadow", scale=1.0):
    """Boulders: speckled grey stone with crisp edges; moss on top (meadow), snow caps, or basalt with glowing seams."""
    if theme == "volcano":
        g = new(name)
        p = g.obj()
        macro = g.noise(p, 2.0 / scale, 3.0, 0.55)
        c = g.mix(g.remap(macro, 0.3, 0.7, 0.0, 1.0), g.rgb((0.08, 0.07, 0.07)), g.rgb((0.22, 0.19, 0.18)))
        edge = g.smooth(g.geo("Pointiness"), 0.51, 0.57)
        c = g.mix(g.math("MULTIPLY", edge, 0.5), c, g.rgb((0.36, 0.32, 0.3)))
        seam = g.smooth(g.voronoi(p, 3.0 / scale, feature="DISTANCE_TO_EDGE"), 0.035, 0.0)
        low = g.math("SUBTRACT", 1.0, _up(g, 0.2, 0.7))
        c = g.mix(g.math("MULTIPLY", seam, low), c, g.rgb((1.0, 0.36, 0.05)))
        c, rough = _cover(g, c, 0.7, theme, p, 0.8)
        return g.finish(c, rough, g.bump(g.noise(p, 12.0 / scale, 4.0, 0.6), 0.4, 0.008))
    g = new(name)
    p = g.obj()
    macro = g.noise(p, 2.2 / scale, 3.0, 0.55)
    c = g.mix(g.remap(macro, 0.35, 0.65, 0.0, 1.0), g.rgb((0.46, 0.47, 0.5)), g.rgb((0.64, 0.63, 0.6)))
    speck = g.noise(p, 70.0 / scale, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.6, 0.66), 0.45), c, g.rgb((0.32, 0.33, 0.36)))
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.34, 0.28), 0.35), c, g.rgb((0.78, 0.77, 0.74)))
    edge = g.smooth(g.geo("Pointiness"), 0.51, 0.57)
    c = g.mix(g.math("MULTIPLY", edge, 0.55), c, g.rgb((0.82, 0.81, 0.78)))
    crev = g.smooth(g.geo("Pointiness"), 0.48, 0.43)
    c = g.mix(g.math("MULTIPLY", crev, 0.6), c, g.rgb((0.22, 0.22, 0.24)))
    rough = 0.78
    if theme == "meadow":
        up = _up(g, 0.4, 0.8)
        patch = g.smooth(g.noise(p, 3.2 / scale, 4.0, 0.6), 0.46, 0.56)
        mossc = g.mix(g.noise(p, 25.0, 3.0), g.rgb((0.27, 0.44, 0.13)), g.rgb((0.46, 0.6, 0.2)))
        c = g.mix(g.math("MULTIPLY", up, patch), c, mossc)
        lich = g.math("MULTIPLY", g.smooth(g.noise(p, 9.0, 3.0), 0.62, 0.68), 0.6)
        c = g.mix(lich, c, g.rgb((0.72, 0.7, 0.42)))
    else:
        c, rough = _cover(g, c, rough, theme, p, 1.0, 0.58, 0.66, cap=True)
    h = g.math("ADD", g.math("MULTIPLY", speck, 0.5), g.noise(p, 14.0 / scale, 4.0, 0.6))
    return g.finish(c, rough, g.bump(h, 0.35, 0.006))


def old_bone(name="DK_Bone", theme="meadow"):
    """Weathered mammoth bone: ivory with brown stains in the cracks, moss / snow / soot by theme."""
    g = new(name)
    p = g.obj()
    base = g.mix(g.noise(p, 5.0, 3.0), g.rgb((0.9, 0.85, 0.72)), g.rgb((0.76, 0.68, 0.52)))
    crev = g.smooth(g.geo("Pointiness"), 0.49, 0.44)
    c = g.mix(g.math("MULTIPLY", crev, 0.7), base, g.rgb((0.42, 0.33, 0.22)))
    cracks = g.smooth(g.noise(g.scale_vec(p, (6.0, 6.0, 30.0)), 1.0, 3.0, 0.6), 0.62, 0.7)
    c = g.mix(g.math("MULTIPLY", cracks, 0.5), c, g.rgb((0.5, 0.42, 0.3)))
    rough = 0.6
    if theme == "meadow":
        moss = g.math("MULTIPLY", g.smooth(g.noise(p, 4.0, 3.0), 0.56, 0.64), 0.7)
        c = g.mix(moss, c, g.rgb((0.36, 0.52, 0.18)))
    elif theme == "volcano":
        soot = g.smooth(g.noise(p, 2.5, 3.0), 0.4, 0.65)
        c = g.mix(g.math("MULTIPLY", soot, 0.75), c, g.rgb((0.14, 0.11, 0.1)))
    else:
        c, rough = _cover(g, c, rough, theme, p, 1.0, 0.5, 0.8)
    return g.finish(c, rough, g.bump(g.math("ADD", cracks, g.noise(p, 50.0, 2.0)), 0.3, 0.004))


def hide(name="DK_Hide", theme="meadow"):
    """Stretched hides: tan leather patches with darker seams and stitches."""
    g = new(name)
    p = g.obj()
    cells = g.voronoi(p, 2.2, feature="DISTANCE_TO_EDGE")
    seam = g.smooth(cells, 0.04, 0.0)
    c = g.mix(g.noise(p, 4.0, 3.0), g.rgb((0.6, 0.42, 0.24)), g.rgb((0.76, 0.58, 0.36)))
    c = g.mix(g.math("MULTIPLY", seam, 0.7), c, g.rgb((0.3, 0.19, 0.1)))
    fur = g.noise(g.scale_vec(p, (40.0, 40.0, 40.0)), 1.0, 2.0)
    c = g.mix(g.math("MULTIPLY", fur, 0.3), c, g.rgb((0.44, 0.3, 0.17)))
    c, rough = _cover(g, c, 0.85, theme, p, 1.0, 0.55, 0.85)
    return g.finish(c, rough, g.bump(g.math("ADD", fur, g.math("MULTIPLY", seam, -1.0)), 0.4, 0.006))


def snowpack(name="DK_Snow"):
    """Snow drifts: white with cool blue hollows and a little sparkle."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 3.0, 3.0), g.rgb((0.86, 0.9, 0.98)), g.rgb((1.0, 1.0, 1.0)))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.4
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.7), c, g.rgb((0.58, 0.7, 0.9)))
    sp = g.smooth(g.noise(p, 90.0, 1.0), 0.7, 0.76)
    c = g.mix(g.math("MULTIPLY", sp, 0.6), c, g.rgb((1.0, 1.0, 1.0)))
    ripple = g.wave(g.scale_vec(p, (1.0, 0.4, 1.0)), 6.0, 4.0, 2.0, "BANDS", "X")
    return g.finish(c, 0.55, g.bump(g.math("ADD", ripple, g.noise(p, 20.0, 2.0)), 0.25, 0.01))


def ice(name="DK_Ice"):
    """Ice crystals: pale cyan, deeper blue inside, white frosted edges and inner fracture lines."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 3.0, 2.0), g.rgb((0.45, 0.72, 0.92)), g.rgb((0.7, 0.9, 1.0)))
    edge = g.smooth(g.geo("Pointiness"), 0.5, 0.56)
    c = g.mix(g.math("MULTIPLY", edge, 0.8), c, g.rgb((0.95, 0.99, 1.0)))
    frac = g.smooth(g.voronoi(p, 6.0, feature="DISTANCE_TO_EDGE"), 0.03, 0.0)
    c = g.mix(g.math("MULTIPLY", frac, 0.6), c, g.rgb((0.9, 0.97, 1.0)))
    return g.finish(c, 0.08, g.bump(frac, 0.2, 0.004))


def obsidian(name="DK_Obsidian"):
    """Volcanic glass: black with violet and blue sheen on the facets, sharp bright edges."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], g.geo("Normal"))
    sheen = g.smooth(g.math("ADD", sep.outputs["X"], sep.outputs["Z"]), 0.6, 1.2)
    c = g.mix(g.math("MULTIPLY", sheen, 0.7), g.rgb((0.04, 0.03, 0.06)), g.rgb((0.36, 0.22, 0.52)))
    edge = g.smooth(g.geo("Pointiness"), 0.5, 0.56)
    c = g.mix(g.math("MULTIPLY", edge, 0.7), c, g.rgb((0.62, 0.55, 0.78)))
    return g.finish(c, 0.1, g.bump(g.noise(p, 30.0, 2.0), 0.1, 0.002))


def ochre(name="DK_Ochre"):
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.62, 0.18, 0.08)), g.rgb((0.78, 0.3, 0.12)))
    return g.finish(c, 0.8)


def turf(name="DK_Turf", theme="meadow"):
    """The ground a landmark sits in: grass (meadow), snow (snow) or ash and cinders (volcano), dirt on the sides."""
    if theme == "meadow":
        return ground(name)
    if theme == "snow":
        return snowpack(name)
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 3.0, 3.0), g.rgb((0.12, 0.1, 0.1)), g.rgb((0.3, 0.26, 0.23)))
    peb = g.smooth(g.voronoi(p, 22.0), 0.12, 0.08)
    c = g.mix(g.math("MULTIPLY", peb, 0.5), c, g.rgb((0.4, 0.36, 0.32)))
    return g.finish(c, 0.85, g.bump(peb, 0.3, 0.006))


def glow(name, col, strength=2.5):
    g = new(name)
    return g.finish(g.rgb(col), 0.3, emit=g.rgb(col), emit_strength=strength)
