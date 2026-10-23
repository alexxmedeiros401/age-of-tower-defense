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


def needles(name="DK_Needles", theme="meadow", dark=False):
    """Pine foliage: deep green clumps, bright tips catching the light, dark inside; snow / ash on top. dark: the
    Darkwood's spruces, a deeper blue-green."""
    g = new(name)
    p = g.obj()
    strands = g.noise(g.scale_vec(p, (30.0, 30.0, 60.0)), 1.0, 3.0, 0.6)
    b0, b1, tip_c, up_c = (((0.1, 0.32, 0.12), (0.16, 0.42, 0.14), (0.42, 0.66, 0.2), (0.3, 0.56, 0.18)) if not dark else
                           ((0.05, 0.18, 0.1), (0.08, 0.25, 0.12), (0.24, 0.42, 0.16), (0.16, 0.34, 0.14)))
    base = g.mix(g.remap(g.noise(p, 2.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(b0), g.rgb(b1))
    tips = g.smooth(g.geo("Pointiness"), 0.51, 0.58)
    c = g.mix(g.math("MULTIPLY", tips, 0.8), base, g.rgb(tip_c))
    up = _up(g, 0.2, 0.9)
    c = g.mix(g.math("MULTIPLY", up, 0.35), c, g.rgb(up_c))
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


def rock(name="DK_Rock", theme="meadow", scale=1.0, dark=False, moss=True):
    """Boulders: speckled grey stone with crisp edges; moss on top (meadow), snow caps, or basalt with glowing seams.
    dark (meadow): the Darkwood's boulders, darker stone under deeper moss; moss=False: bare (a catapult's shot)."""
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
    k = 0.62 if dark else 1.0
    c = g.mix(g.remap(macro, 0.35, 0.65, 0.0, 1.0), g.rgb((0.46 * k, 0.47 * k, 0.5 * k)), g.rgb((0.64 * k, 0.63 * k, 0.6 * k)))
    speck = g.noise(p, 70.0 / scale, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.6, 0.66), 0.45), c, g.rgb((0.32, 0.33, 0.36)))
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.34, 0.28), 0.35), c, g.rgb((0.78, 0.77, 0.74)))
    edge = g.smooth(g.geo("Pointiness"), 0.51, 0.57)
    c = g.mix(g.math("MULTIPLY", edge, 0.55), c, g.rgb((0.82, 0.81, 0.78)))
    crev = g.smooth(g.geo("Pointiness"), 0.48, 0.43)
    c = g.mix(g.math("MULTIPLY", crev, 0.6), c, g.rgb((0.22, 0.22, 0.24)))
    rough = 0.78
    if theme == "meadow" and not moss:
        pass
    elif theme == "meadow":
        up = _up(g, 0.4, 0.8)
        patch = g.smooth(g.noise(p, 3.2 / scale, 4.0, 0.6), 0.46, 0.56)
        mossc = g.mix(g.noise(p, 25.0, 3.0), g.rgb((0.27, 0.44, 0.13) if not dark else (0.12, 0.24, 0.07)),
                      g.rgb((0.46, 0.6, 0.2) if not dark else (0.22, 0.36, 0.1)))
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


def turf_roof(name="DK_TurfRoof"):
    """A sod roof in the deep wood (Darkwood's hut): dark, damp grass and moss in hummocks, bare black earth where the
    sod has slumped, paler moss on the crowns; earth on the cut edges. (Meadow grass read as a lime-green slab there.)"""
    g = new(name)
    p = g.obj()
    up = _up(g, 0.35, 0.7)
    gr = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.07, 0.13, 0.04)), g.rgb((0.15, 0.24, 0.07)))
    moss = g.smooth(g.noise(p, 7.0, 3.0), 0.55, 0.66)
    gr = g.mix(g.math("MULTIPLY", moss, 0.6), gr, g.rgb((0.26, 0.32, 0.1)))
    blades = g.noise(g.scale_vec(p, (55.0, 55.0, 55.0)), 1.0, 2.0)
    gr = g.mix(g.math("MULTIPLY", blades, 0.4), gr, g.rgb((0.05, 0.09, 0.03)))
    bare = g.smooth(g.noise(p, 2.2, 3.0, 0.5), 0.6, 0.7)
    earth = g.mix(g.noise(p, 9.0, 2.0), g.rgb((0.08, 0.06, 0.04)), g.rgb((0.17, 0.12, 0.08)))
    gr = g.mix(g.math("MULTIPLY", bare, 0.8), gr, earth)
    c = g.mix(up, earth, gr)
    return g.finish(c, 0.92, g.bump(g.math("ADD", g.math("MULTIPLY", blades, 0.6), moss), 0.5, 0.008))


def glow(name, col, strength=2.5):
    g = new(name)
    return g.finish(g.rgb(col), 0.3, emit=g.rgb(col), emit_strength=strength)


# ------------------------------------------------------------------------------------------------ Bronze Age (v0.9.28)
def _z(g):
    s = g.node("ShaderNodeSeparateXYZ")
    g.put(s.inputs[0], g.obj())
    return s.outputs["Z"]


def palm_bark(name="DK_PalmBark"):
    """Date palm trunk: grey-tan boots of old leaf bases (the sculpt's criss-cross scales), dark fibre in the gaps
    between them, sun-bleached rims."""
    g = new(name)
    p = g.obj()
    fib = g.noise(g.scale_vec(p, (45.0, 45.0, 7.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.4, 0.31, 0.21)), g.rgb((0.56, 0.45, 0.32)))
    c = g.mix(g.math("MULTIPLY", g.remap(fib, 0.3, 0.7, 0.0, 1.0), 0.4), c, g.rgb((0.28, 0.2, 0.13)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.49, 0.43), 0.85), c, g.rgb((0.14, 0.09, 0.06)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.55), c, g.rgb((0.74, 0.66, 0.52)))
    return g.finish(c, 0.88, g.bump(fib, 0.45, 0.004))


def frond(name="DK_Frond", base=(0.16, 0.38, 0.11), hi=(0.4, 0.62, 0.2), dry=(0.66, 0.54, 0.26)):
    """Palm leaflets: deep green, brighter where they face the sky and along the edges, dark between the leaflets,
    the odd dry yellow-brown patch."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 2.5, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.3) for x in base)))
    c = g.mix(g.math("MULTIPLY", _up(g, 0.15, 0.9), 0.5), c, g.rgb(hi))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.58), 0.45), c, g.rgb(tuple(min(1, x * 1.25) for x in hi)))
    streak = g.noise(g.scale_vec(p, (30.0, 30.0, 30.0)), 1.0, 2.0)
    c = g.mix(g.math("MULTIPLY", g.remap(streak, 0.3, 0.7, 0.0, 1.0), 0.22), c, g.rgb(tuple(x * 0.7 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 1.4, 2.0), 0.66, 0.74), 0.85), c, g.rgb(dry))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.2
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.75), c, g.rgb((0.03, 0.1, 0.04)))
    return g.finish(c, 0.62, g.bump(streak, 0.25, 0.003))


def frond_rib(name="DK_FrondRib"):
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 8.0, 2.0), g.rgb((0.6, 0.6, 0.26)), g.rgb((0.44, 0.48, 0.18)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb((0.78, 0.76, 0.42)))
    return g.finish(c, 0.6)


def dates(name="DK_Dates"):
    """Ripe dates: amber to deep red-brown, glossy, dark between the fruit."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.86, 0.46, 0.1)), g.rgb((0.56, 0.18, 0.05)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.49, 0.43), 0.7), c, g.rgb((0.22, 0.07, 0.03)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb((1.0, 0.68, 0.3)))
    return g.finish(c, 0.35)


def papyrus(name="DK_Papyrus", base=(0.26, 0.48, 0.14), hi=(0.48, 0.66, 0.22)):
    """Papyrus and reed stems: green with fine lengthwise fibres, brown and wet at the foot."""
    g = new(name)
    p = g.obj()
    fib = g.noise(g.scale_vec(p, (70.0, 70.0, 4.0)), 1.0, 2.0)
    c = g.mix(g.remap(fib, 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(hi))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb(tuple(min(1, x * 1.3) for x in hi)))
    foot = g.math("SUBTRACT", 1.0, g.smooth(_z(g), 0.04, 0.3))
    c = g.mix(g.math("MULTIPLY", foot, 0.85), c, g.rgb((0.3, 0.24, 0.12)))
    return g.finish(c, 0.6, g.bump(fib, 0.3, 0.003))


def papyrus_head(name="DK_PapyrusHead", base=(0.5, 0.66, 0.22), tip=(0.76, 0.82, 0.38)):
    """The papyrus umbels: a burst of yellow-green threads, paler at the ends."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 40.0, 2.0), g.rgb(base), g.rgb(tip))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.6), c, g.rgb((0.86, 0.88, 0.5)))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.08
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.6), c, g.rgb((0.16, 0.26, 0.06)))
    return g.finish(c, 0.7)


def cattail(name="DK_Cattail"):
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 60.0, 2.0), g.rgb((0.36, 0.2, 0.1)), g.rgb((0.5, 0.3, 0.15)))
    return g.finish(c, 0.9, g.bump(g.noise(p, 120.0, 2.0), 0.3, 0.002))


def mud(name="DK_Mud"):
    """Wet river silt: dark glossy brown, drying paler on the tops."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 6.0, 3.0), g.rgb((0.22, 0.16, 0.1)), g.rgb((0.34, 0.25, 0.16)))
    up = _up(g, 0.5, 0.9)
    dry = g.smooth(g.noise(p, 3.0, 3.0), 0.5, 0.62)
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", up, dry), 0.8), c, g.rgb((0.5, 0.4, 0.27)))
    return g.finish(c, g.mixf(dry, 0.4, 0.85), g.bump(g.noise(p, 20.0, 3.0), 0.3, 0.004))


def sand(name="DK_Sand", base=(0.84, 0.68, 0.45), hi=(0.94, 0.8, 0.56), shade=(0.72, 0.56, 0.36)):
    """Wind-blown sand: the desert ground's colours, wind ripples, pale crests, a cooler shade on the lee slopes."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 1.5, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(hi))
    rip = g.wave(g.scale_vec(p, (1.0, 0.35, 1.0)), 9.0, 4.0, 2.0, "BANDS", "X")
    c = g.mix(g.math("MULTIPLY", g.smooth(rip, 0.6, 0.9), 0.3), c, g.rgb(shade))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.55), 0.45), c, g.rgb((0.98, 0.9, 0.7)))
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, _up(g, 0.3, 0.95)), 0.35), c, g.rgb(shade))
    return g.finish(c, 0.93, g.bump(g.math("ADD", rip, g.noise(p, 60.0, 2.0)), 0.25, 0.003))


def sandstone(name="DK_Sandstone", base=(0.82, 0.69, 0.5), dark=(0.6, 0.47, 0.32), bedding=0.0, scale=1.0):
    """Dressed or wind-worn sandstone: warm sand colour, darker in joints and hollows, pale chipped edges, fine pits;
    `bedding` > 0 adds the horizontal layers of a natural rock. Label 5 = red ochre paint, 7 = blue paint (both worn off
    the edges), 6 = gold."""
    g = new(name)
    p = g.obj()
    macro = g.noise(p, 2.6 / scale, 3.0, 0.55)
    c = g.mix(g.remap(macro, 0.35, 0.65, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.08) for x in base)))
    if bedding:
        bed = g.wave(p, 0.9 / scale, 4.0, 3.0, "BANDS", "Z")              # (a band every ~0.35 units)
        c = g.mix(g.math("MULTIPLY", g.smooth(bed, 0.55, 0.85), bedding), c, g.rgb(dark))
        c = g.mix(g.math("MULTIPLY", g.smooth(bed, 0.2, 0.05), bedding * 0.6), c, g.rgb(tuple(min(1, x * 1.12) for x in base)))
    pits = g.smooth(g.noise(p, 80.0 / scale, 2.0, 0.6), 0.62, 0.68)
    c = g.mix(g.math("MULTIPLY", pits, 0.35), c, g.rgb(dark))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.7), c, g.rgb(tuple(x * 0.62 for x in dark)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.55), c, g.rgb((0.96, 0.9, 0.76)))
    stain = g.smooth(g.noise(p, 1.4, 2.0), 0.56, 0.7)
    c = g.mix(g.math("MULTIPLY", stain, 0.22), c, g.rgb(dark))
    worn = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.smooth(pt, 0.515, 0.6), 0.85))
    brush = g.remap(g.noise(p, 40.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    red = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb((0.72, 0.22, 0.1)), g.rgb((0.56, 0.15, 0.07)))
    blue = g.mix(g.math("MULTIPLY", brush, 0.3), g.rgb((0.16, 0.36, 0.66)), g.rgb((0.1, 0.24, 0.5)))
    fade = g.remap(g.noise(p, 5.0, 2.0), 0.3, 0.7, 0.55, 1.0)
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", g.reg(5), worn), fade), c, red)
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", g.reg(7), worn), fade), c, blue)
    c = g.mix(g.reg(6), c, g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.86, 0.62, 0.2)), g.rgb((1.0, 0.9, 0.55))))
    h = g.math("ADD", g.math("MULTIPLY", pits, -0.5), g.noise(p, 16.0 / scale, 4.0, 0.6))
    return g.finish(c, g.mixf(g.reg(6), 0.86, 0.3), g.bump(h, 0.32, 0.005))


def ashlar(name="DK_Ashlar", base=(0.84, 0.74, 0.56), joint=(0.46, 0.38, 0.27), course=0.3, block=0.62, grime7=None):
    """Dressed limestone blocks laid in courses (joints sunk a little in the normal map): the step pyramid, plinths and
    platforms. Labels as sandstone: 5 red, 7 blue, 6 gold. `grime7` (a colour): label 7 is weathering instead (rain
    streaks and grime low down, the Classical Age's walls)."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    z = sep.outputs["Z"]
    row = g.math("FLOOR", g.math("DIVIDE", z, course))
    fz = g.math("SUBTRACT", g.math("DIVIDE", z, course), row)
    run = g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), g.math("MULTIPLY", g.math("MODULO", row, 2.0), block * 0.5))
    fx = g.math("FRACT", g.math("DIVIDE", run, block))
    jz = g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz))
    jx = g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx))
    jt = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.smooth(jz, 0.02, 0.06)), g.math("SUBTRACT", 1.0, g.smooth(jx, 0.01, 0.03)))
    up = _up(g, 0.7, 0.9)
    joint_m = g.math("MULTIPLY", jt, g.math("SUBTRACT", 1.0, up))      # (no joints drawn across the treads)
    blk = g.voronoi(g.scale_vec(p, (1.0 / block, 1.0 / block, 1.0 / course)), 1.0, 1.0, "F1", "Color")
    c = g.mix(g.remap(g.noise(p, 2.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(x * 0.9 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(blk, 0.4, 0.9), 0.18), c, g.rgb(tuple(x * 0.82 for x in base)))
    c = g.mix(joint_m, c, g.rgb(joint))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.6), c, g.rgb(joint))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.5), c, g.rgb((0.96, 0.92, 0.82)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 1.2, 2.0), 0.58, 0.72), 0.25), c, g.rgb((0.62, 0.52, 0.38)))
    red = g.mix(g.math("MULTIPLY", g.remap(g.noise(p, 30.0, 2.0), 0.3, 0.7, 0.0, 1.0), 0.3), g.rgb((0.72, 0.2, 0.1)), g.rgb((0.55, 0.14, 0.07)))
    c = g.mix(g.reg(5), c, red)
    if grime7 is None:
        c = g.mix(g.reg(7), c, g.rgb((0.14, 0.32, 0.64)))
    else:
        streak = g.remap(g.noise(g.scale_vec(p, (9.0, 9.0, 1.2)), 1.0, 2.0), 0.3, 0.7, 0.35, 0.85)
        c = g.mix(g.math("MULTIPLY", g.reg(7), streak), c, g.rgb(grime7))
    c = g.mix(g.reg(6), c, g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.86, 0.62, 0.2)), g.rgb((1.0, 0.9, 0.55))))
    h = g.math("ADD", g.math("MULTIPLY", joint_m, -0.8), g.math("MULTIPLY", g.noise(p, 22.0, 3.0), 0.3))
    return g.finish(c, g.mixf(g.reg(6), 0.86, 0.3), g.bump(h, 0.3, 0.006))


def redrock(name="DK_RedRock", scale=1.0, flecks=True):
    """Canyon rock: red sandstone in strata (pale cream and dark red bands), dark desert-varnish streaks running down,
    pale worn edges, dark cracks, the odd fleck of copper-green malachite."""
    g = new(name)
    p = g.obj()
    strata = g.wave(p, 0.85 / scale, 2.5, 2.0, "BANDS", "Z")            # (a band every ~0.37 units)
    thin = g.wave(p, 2.6 / scale, 3.0, 2.0, "BANDS", "Z")
    c = g.mix(g.remap(g.noise(p, 2.0 / scale, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.56, 0.27, 0.14)), g.rgb((0.7, 0.37, 0.2)))
    c = g.mix(g.math("MULTIPLY", g.smooth(strata, 0.62, 0.9), 0.42), c, g.rgb((0.84, 0.6, 0.4)))
    c = g.mix(g.math("MULTIPLY", g.smooth(strata, 0.2, 0.04), 0.35), c, g.rgb((0.42, 0.17, 0.1)))
    c = g.mix(g.math("MULTIPLY", g.smooth(thin, 0.8, 0.95), 0.15), c, g.rgb((0.78, 0.5, 0.32)))
    varn = g.smooth(g.noise(g.scale_vec(p, (14.0 / scale, 14.0 / scale, 1.2 / scale)), 1.0, 3.0, 0.6), 0.6, 0.7)
    c = g.mix(g.math("MULTIPLY", varn, 0.45), c, g.rgb((0.24, 0.12, 0.08)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.7), c, g.rgb((0.2, 0.08, 0.05)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.5), c, g.rgb((0.92, 0.7, 0.52)))
    if flecks:
        fl = g.smooth(g.noise(p, 30.0 / scale, 2.0, 0.5), 0.75, 0.79)
        c = g.mix(g.math("MULTIPLY", fl, 0.85), c, g.rgb((0.18, 0.62, 0.44)))
    h = g.math("ADD", g.math("MULTIPLY", strata, 0.35), g.noise(p, 12.0 / scale, 4.0, 0.6))
    return g.finish(c, 0.86, g.bump(h, 0.35, 0.006))


def malachite(name="DK_Malachite"):
    """Malachite and copper ore: banded greens (dark and light rings), bright on the bulges, near black in the cracks."""
    g = new(name)
    p = g.obj()
    bands = g.wave(p, 9.0, 6.0, 2.0, "RINGS", "Z")
    c = g.mix(g.remap(g.noise(p, 6.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.05, 0.36, 0.22)), g.rgb((0.12, 0.52, 0.34)))
    c = g.mix(g.math("MULTIPLY", g.smooth(bands, 0.55, 0.85), 0.35), c, g.rgb((0.26, 0.72, 0.5)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.56), 0.6), c, g.rgb((0.55, 0.94, 0.74)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.8), c, g.rgb((0.02, 0.1, 0.07)))
    return g.finish(c, 0.32, g.bump(bands, 0.2, 0.002))


def mud_plaster(name="DK_MudPlaster", base=(0.72, 0.56, 0.38)):
    """Hand-smoothed mud plaster: warm tan with smear marks and hairline cracks, darker where rain splashes the foot of
    the wall, pale on worn edges; label 7 = whitewash, 5 = a painted red band."""
    g = new(name)
    p = g.obj()
    smear = g.noise(g.scale_vec(p, (8.0, 8.0, 3.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(smear, 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.1) for x in base)))
    crack = g.smooth(g.voronoi(p, 7.0, 1.0, "DISTANCE_TO_EDGE"), 0.012, 0.0)
    c = g.mix(g.math("MULTIPLY", crack, 0.45), c, g.rgb(tuple(x * 0.6 for x in base)))
    foot = g.math("SUBTRACT", 1.0, g.smooth(_z(g), 0.05, 0.3))
    c = g.mix(g.math("MULTIPLY", foot, 0.4), c, g.rgb(tuple(x * 0.7 for x in base)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.45), c, g.rgb(tuple(min(1, x * 1.22) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), c, g.rgb(tuple(x * 0.55 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.reg(7), 0.92), c, g.mix(g.math("MULTIPLY", smear, 0.3), g.rgb((0.93, 0.9, 0.82)), g.rgb((0.8, 0.76, 0.66))))
    c = g.mix(g.reg(5), c, g.rgb((0.7, 0.2, 0.1)))
    h = g.math("ADD", g.math("MULTIPLY", smear, 0.5), g.math("MULTIPLY", crack, -0.6))
    return g.finish(c, 0.9, g.bump(h, 0.3, 0.004))


def rail(name="DK_Rail"):
    """Mine rails: dark iron-grey, rust in patches, polished bright where the wheels run."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 10.0, 2.0), g.rgb((0.2, 0.2, 0.22)), g.rgb((0.3, 0.29, 0.28)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 6.0, 3.0), 0.55, 0.68), 0.6), c, g.rgb((0.44, 0.24, 0.13)))
    c = g.mix(g.math("MULTIPLY", _up(g, 0.7, 0.95), 0.8), c, g.rgb((0.72, 0.72, 0.74)))
    return g.finish(c, 0.45)


def bronze_turf(name, theme):
    """The ground a Bronze Age landmark sits in: grass (delta), sand (desert), red dirt with pebbles (canyon)."""
    if theme == "delta":
        return ground(name)
    if theme == "desert":
        return sand(name)
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 3.0, 3.0), g.rgb((0.56, 0.3, 0.17)), g.rgb((0.7, 0.4, 0.23)))
    peb = g.smooth(g.voronoi(p, 22.0), 0.12, 0.08)
    c = g.mix(g.math("MULTIPLY", peb, 0.5), c, g.rgb((0.42, 0.24, 0.14)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 30.0, 2.0, 0.5), 0.74, 0.78), 0.8), c, g.rgb((0.18, 0.6, 0.42)))
    return g.finish(c, 0.88, g.bump(peb, 0.3, 0.006))


def timber_log(name="DK_TimberLog"):
    """Trimmed logs lying along X: bark streaked along their length, pale wood with rings on the cut ends (+-X)."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], g.geo("Normal"))
    cut = g.smooth(g.math("ABSOLUTE", sep.outputs["X"]), 0.75, 0.9)
    streak = g.noise(g.scale_vec(p, (2.0, 45.0, 45.0)), 1.0, 3.0, 0.6)
    bark = g.mix(g.remap(streak, 0.3, 0.7, 0.0, 1.0), g.rgb((0.42, 0.28, 0.16)), g.rgb((0.26, 0.16, 0.09)))
    bark = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), bark, g.rgb((0.58, 0.42, 0.26)))
    rings = g.wave(p, 6.0, 1.5, 2.0, "RINGS", "X")
    wood = g.mix(rings, g.rgb((0.78, 0.6, 0.38)), g.rgb((0.6, 0.42, 0.24)))
    c = g.mix(cut, bark, wood)
    return g.finish(c, 0.8, g.bump(g.mixf(cut, streak, rings), 0.4, 0.004))


def driftwood(name="DK_DriftWood"):
    """Sun-bleached dead wood: silver-grey and tan, split along the grain, dark in the cracks."""
    g = new(name)
    p = g.obj()
    grain = g.noise(g.scale_vec(p, (40.0, 40.0, 3.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb((0.66, 0.6, 0.52)), g.rgb((0.5, 0.44, 0.37)))
    c = g.mix(g.math("MULTIPLY", g.smooth(grain, 0.66, 0.72), 0.7), c, g.rgb((0.24, 0.2, 0.16)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb((0.8, 0.76, 0.68)))
    return g.finish(c, 0.85, g.bump(grain, 0.5, 0.004))


# ------------------------------------------------------------------------------------------------ cacti (v0.9.29)
def cactus(name="DK_Saguaro", base=(0.25, 0.42, 0.19), hi=(0.46, 0.6, 0.3), groove=(0.07, 0.15, 0.06),
           spine=(0.9, 0.85, 0.68), dots=16.0, dot_r=0.2, foot=(0.46, 0.4, 0.3), rough=0.48):
    """Cactus skin: waxy green with faint lengthwise streaks, paler along the crests of the ribs and deep down the
    grooves, a corky dusty foot, and spine clusters (areoles) dotted along the crests."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 2.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1, x * 1.18) for x in base)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.505, 0.55), 0.7), c, g.rgb(hi))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.495, 0.45), 0.85), c, g.rgb(groove))
    streak = g.noise(g.scale_vec(p, (30.0, 30.0, 2.5)), 1.0, 2.0)
    c = g.mix(g.math("MULTIPLY", g.remap(streak, 0.35, 0.65, 0.0, 1.0), 0.18), c, g.rgb(tuple(x * 0.78 for x in base)))
    ft = g.math("SUBTRACT", 1.0, g.smooth(_z(g), 0.03, 0.2))
    c = g.mix(g.math("MULTIPLY", ft, 0.75), c, g.rgb(foot))
    dot = g.math("MULTIPLY", g.smooth(g.voronoi(p, dots, 0.75), dot_r, dot_r * 0.45), g.smooth(pt, 0.495, 0.53))
    c = g.mix(dot, c, g.rgb(spine))
    return g.finish(c, rough, g.bump(g.math("ADD", g.math("MULTIPLY", streak, 0.6), dot), 0.3, 0.003))


def opuntia(name="DK_Opuntia"):
    """Prickly pear pads: yellow-green, paler and a little rosy round the rims, areoles in a scatter of brown dots
    with pale spine tufts."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.36, 0.52, 0.2)), g.rgb((0.5, 0.63, 0.26)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.55), c, g.rgb((0.66, 0.62, 0.34)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.535, 0.6), 0.35), c, g.rgb((0.62, 0.36, 0.34)))
    vd = g.voronoi(p, 26.0, 0.65)
    c = g.mix(g.smooth(vd, 0.22, 0.12), c, g.rgb((0.5, 0.38, 0.2)))
    c = g.mix(g.smooth(vd, 0.1, 0.04), c, g.rgb((0.92, 0.88, 0.72)))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.12
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.6), c, g.rgb((0.1, 0.18, 0.06)))
    return g.finish(c, 0.55, g.bump(g.smooth(vd, 0.22, 0.08), 0.35, 0.003))


def agave(name="DK_Agave"):
    """Agave leaves: blue-green under a pale waxy bloom, a thin creamy margin, darker toward the heart."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.34, 0.5, 0.45)), g.rgb((0.46, 0.6, 0.55)))
    c = g.mix(g.math("MULTIPLY", _up(g, 0.2, 0.9), 0.4), c, g.rgb((0.62, 0.72, 0.66)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.52, 0.58), 0.6), c, g.rgb((0.8, 0.78, 0.56)))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.15
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.7), c, g.rgb((0.08, 0.16, 0.12)))
    streak = g.noise(g.scale_vec(p, (25.0, 25.0, 25.0)), 1.0, 2.0)
    return g.finish(c, 0.5, g.bump(streak, 0.15, 0.002))


def flat(name, col, rough=0.6, var=0.12, hi=None):
    """A plain colour with a little mottling (flowers, fruit, spines), lighter on the edges when `hi` is given."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 30.0, 2.0), g.rgb(col), g.rgb(tuple(min(1.0, x * (1.0 + var)) for x in col)))
    if hi is not None:
        c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.6), c, g.rgb(hi))
    return g.finish(c, rough)


# ------------------------------------------------------------------------------------------------ Iron Age
def scots_bark(name="DK_ScotsBark"):
    """Scots pine bark: grey-brown, deeply fissured plates low on the trunk, turning to thin orange flakes from about
    head height up (the kit's pines are 2.4-3.6 tall)."""
    g = new(name)
    p = g.obj()
    z = _z(g)
    plates = g.voronoi(g.scale_vec(p, (1.0, 1.0, 0.4)), 16.0, 1.0, "DISTANCE_TO_EDGE", "Distance")
    crack = g.smooth(plates, 0.06, 0.0)
    low = g.mix(g.remap(g.noise(p, 8.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.28, 0.22, 0.18)), g.rgb((0.44, 0.36, 0.3)))
    flake = g.noise(g.scale_vec(p, (24.0, 24.0, 5.0)), 1.0, 3.0)
    up = g.mix(g.remap(flake, 0.3, 0.7, 0.0, 1.0), g.rgb((0.7, 0.36, 0.16)), g.rgb((0.88, 0.54, 0.28)))
    t = g.smooth(z, 0.9, 1.7)
    c = g.mix(t, low, up)
    c = g.mix(g.math("MULTIPLY", crack, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", t, 0.65))), c, g.rgb((0.09, 0.06, 0.05)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.35), c, g.rgb((0.9, 0.7, 0.5)))
    h = g.math("ADD", g.math("SUBTRACT", 1.0, crack), g.math("MULTIPLY", flake, 0.4))
    return g.finish(c, 0.85, g.bump(h, 0.45, 0.006))


def birch_bark(name="DK_BirchBark"):
    """Birch: chalk-white bark ringed with thin dark lenticels, black scars round the branch stubs, rough and dark at
    the foot."""
    g = new(name)
    p = g.obj()
    z = _z(g)
    c = g.mix(g.noise(p, 6.0, 2.0), g.rgb((0.84, 0.82, 0.76)), g.rgb((0.96, 0.95, 0.9)))
    dash = g.smooth(g.noise(g.scale_vec(p, (12.0, 12.0, 150.0)), 1.0, 2.0, 0.5), 0.63, 0.7)
    c = g.mix(g.math("MULTIPLY", dash, 0.85), c, g.rgb((0.16, 0.14, 0.13)))
    blot = g.smooth(g.noise(g.scale_vec(p, (5.0, 5.0, 10.0)), 1.0, 3.0, 0.6), 0.67, 0.72)
    c = g.mix(blot, c, g.rgb((0.1, 0.09, 0.09)))
    foot = g.smooth(z, 0.5, 0.08)
    c = g.mix(g.math("MULTIPLY", foot, g.smooth(g.noise(p, 12.0, 3.0), 0.3, 0.55)), c, g.rgb((0.2, 0.17, 0.14)))
    return g.finish(c, 0.7, g.bump(g.math("ADD", dash, blot), 0.3, 0.003))


def heather(name="DK_Heather"):
    """Heather: wiry dark shoots, the tops a haze of tiny purple-pink flowers, dark in the hollows."""
    g = new(name)
    p = g.obj()
    base = g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.12, 0.17, 0.08)), g.rgb((0.26, 0.22, 0.12)))
    up = _up(g, 0.2, 0.85)
    tip = g.smooth(g.geo("Pointiness"), 0.485, 0.535)                  # the tufts' crowns, not the hollows
    fl = g.smooth(g.noise(p, 55.0, 2.0, 0.6), 0.4, 0.6)
    pink = g.mix(g.noise(p, 7.0, 2.0), g.rgb((0.48, 0.2, 0.42)), g.rgb((0.7, 0.38, 0.6)))
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", up, tip), g.mixf(fl, 0.5, 1.0)), base, pink)
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.15
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.8), c, g.rgb((0.05, 0.06, 0.04)))
    return g.finish(c, 0.85, g.bump(g.noise(p, 70.0, 2.0), 0.5, 0.006))


def drystone(name="DK_DryStone", base=(0.52, 0.5, 0.47), moss=True):
    """Dry-stone walling: flat slabs laid in rough courses without mortar, every stone its own shade of grey, dark
    gaps between them, pale lichen, moss on the tops (moss=True)."""
    g = new(name)
    p = g.obj()
    sp = g.scale_vec(p, (3.0, 3.0, 7.5))
    shade = g.voronoi(sp, 1.0, 0.85, "F1", "Color")
    gap = g.smooth(g.voronoi(sp, 1.0, 0.85, "DISTANCE_TO_EDGE", "Distance"), 0.07, 0.025)
    c = g.mix(shade, g.rgb(tuple(x * 0.72 for x in base)), g.rgb(tuple(min(1.0, x * 1.2) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), 0.3), c, g.rgb((0.42, 0.38, 0.32)))
    speck = g.noise(p, 60.0, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.62, 0.68), 0.35), c, g.rgb((0.26, 0.26, 0.27)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.45), c, g.rgb((0.8, 0.79, 0.76)))
    lich = g.math("MULTIPLY", g.smooth(g.noise(p, 10.0, 3.0), 0.64, 0.7), 0.75)
    c = g.mix(lich, c, g.rgb((0.78, 0.76, 0.52)))
    if moss:
        mz = g.math("MULTIPLY", _up(g, 0.45, 0.85), g.smooth(g.noise(p, 3.5, 3.0), 0.44, 0.56))
        c = g.mix(mz, c, g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.26, 0.4, 0.12)), g.rgb((0.44, 0.56, 0.2))))
    c = g.mix(gap, c, g.rgb((0.07, 0.065, 0.06)))
    h = g.math("ADD", g.math("SUBTRACT", 1.0, gap), g.math("MULTIPLY", speck, 0.3))
    return g.finish(c, 0.85, g.bump(h, 0.55, 0.012))


def thatch(name="DK_Thatch", base=(0.6, 0.48, 0.28), old=(0.42, 0.37, 0.28)):
    """Thatch: straw laid in courses down the roof, the stalk ends showing as fine streaks along the slope and a dark
    line under every course, weathered grey-brown in patches, green with moss low on the roof; label 5 = the bound
    ridge and the hazel spars (darker, twisted)."""
    g = new(name)
    p = g.obj()
    z = _z(g)
    streak = g.noise(g.scale_vec(p, (80.0, 80.0, 5.0)), 1.0, 2.0, 0.6)
    c = g.mix(g.remap(streak, 0.3, 0.7, 0.0, 1.0), g.rgb(tuple(x * 0.78 for x in base)), g.rgb(tuple(min(1.0, x * 1.18) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 2.5, 3.0), 0.42, 0.68), 0.75), c, g.rgb(old))
    course = g.wave(p, 2.3, 1.2, 1.0, "BANDS", "Z", "SAW")
    line = g.smooth(course, 0.82, 0.97)
    c = g.mix(g.math("MULTIPLY", line, 0.6), c, g.rgb((0.16, 0.12, 0.08)))
    mz = g.math("MULTIPLY", g.smooth(z, 1.0, 0.55), g.smooth(g.noise(p, 4.0, 3.0), 0.45, 0.6))
    c = g.mix(g.math("MULTIPLY", mz, 0.8), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.28, 0.34, 0.14)), g.rgb((0.42, 0.46, 0.2))))
    tw = g.wave(p, 60.0, 1.0, 0.0, "BANDS", "DIAGONAL")
    c = g.mix(g.reg(5), c, g.mix(g.math("MULTIPLY", tw, 0.5), g.rgb((0.36, 0.26, 0.14)), g.rgb((0.22, 0.15, 0.08))))
    h = g.math("ADD", g.math("MULTIPLY", streak, 0.6), g.math("MULTIPLY", course, 0.8))
    return g.finish(c, 0.92, g.bump(h, 0.5, 0.012))


def slag(name="DK_Slag"):
    """Iron slag: black and glassy, ropey with flow lines, an oily blue-purple sheen on the tops, rust where it has
    weathered, bubble pits."""
    g = new(name)
    p = g.obj()
    flow = g.noise(g.scale_vec(p, (8.0, 8.0, 22.0)), 1.0, 4.0, 0.6, 1.5)
    c = g.mix(g.remap(flow, 0.3, 0.7, 0.0, 1.0), g.rgb((0.05, 0.05, 0.06)), g.rgb((0.16, 0.15, 0.16)))
    sheen = g.math("MULTIPLY", _up(g, 0.4, 0.95), g.smooth(g.noise(p, 5.0, 3.0), 0.5, 0.7))
    c = g.mix(g.math("MULTIPLY", sheen, 0.35), c, g.mix(g.noise(p, 9.0, 2.0), g.rgb((0.18, 0.2, 0.26)), g.rgb((0.24, 0.2, 0.27))))
    rust = g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.49, 0.44), g.smooth(g.noise(p, 7.0, 3.0), 0.5, 0.62))
    c = g.mix(g.math("MULTIPLY", rust, 0.85), c, g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.42, 0.18, 0.07)), g.rgb((0.62, 0.32, 0.12))))
    pits = g.smooth(g.voronoi(p, 30.0, 1.0, "F1", "Distance"), 0.16, 0.05)
    c = g.mix(g.math("MULTIPLY", pits, 0.8), c, g.rgb((0.02, 0.02, 0.02)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb((0.42, 0.42, 0.46)))
    return g.finish(c, g.mixf(rust, 0.22, 0.85), g.bump(g.math("SUBTRACT", flow, g.math("MULTIPLY", pits, 0.6)), 0.4, 0.006))


def iron_ore(name="DK_IronOre"):
    """Bog-iron ore: knobbly nodules, rust-red to ochre-yellow, black-brown in the cracks, earthy."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 9.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.32, 0.12, 0.06)), g.rgb((0.52, 0.23, 0.09)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 4.0, 3.0), 0.58, 0.72), 0.7), c, g.rgb((0.62, 0.45, 0.17)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.49, 0.43), 0.8), c, g.rgb((0.14, 0.07, 0.04)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.4), c, g.rgb((0.86, 0.6, 0.36)))
    return g.finish(c, 0.9, g.bump(g.noise(p, 40.0, 3.0), 0.45, 0.005))


def ironstone(name="DK_Ironstone"):
    """Rock of the forge: dark grey-brown stone streaked and stained with rust running down from the ore seams,
    sooty on the tops."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 2.2, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.18, 0.16, 0.15)), g.rgb((0.34, 0.3, 0.27)))
    speck = g.noise(p, 60.0, 2.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(speck, 0.6, 0.66), 0.4), c, g.rgb((0.1, 0.09, 0.09)))
    run = g.noise(g.scale_vec(p, (14.0, 14.0, 2.0)), 1.0, 3.0, 0.6)
    rust = g.math("MULTIPLY", g.smooth(run, 0.56, 0.68), g.math("SUBTRACT", 1.0, _up(g, 0.55, 0.9)))
    c = g.mix(g.math("MULTIPLY", rust, 0.75), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.44, 0.19, 0.08)), g.rgb((0.62, 0.3, 0.12))))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.5), c, g.rgb((0.5, 0.46, 0.42)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.48, 0.43), 0.6), c, g.rgb((0.06, 0.05, 0.05)))
    soot = g.math("MULTIPLY", _up(g, 0.6, 0.9), g.smooth(g.noise(p, 3.0, 3.0), 0.48, 0.6))
    c = g.mix(g.math("MULTIPLY", soot, 0.6), c, g.rgb((0.08, 0.075, 0.07)))
    h = g.math("ADD", g.math("MULTIPLY", speck, 0.5), g.noise(p, 14.0, 4.0, 0.6))
    return g.finish(c, 0.8, g.bump(h, 0.35, 0.006))


def furnace_clay(name="DK_FurnaceClay"):
    """A bloomery's clay: fired orange-red to buff, crazed with cracks, black with soot toward the top and round the
    mouth (label 5), glazed grey-green where the heat ran (label 6)."""
    g = new(name)
    p = g.obj()
    z = _z(g)
    c = g.mix(g.remap(g.noise(p, 4.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.66, 0.38, 0.22)), g.rgb((0.8, 0.58, 0.38)))
    crack = g.smooth(g.voronoi(p, 9.0, 1.0, "DISTANCE_TO_EDGE"), 0.02, 0.0)
    c = g.mix(g.math("MULTIPLY", crack, 0.7), c, g.rgb((0.3, 0.16, 0.08)))
    hot = g.math("MAXIMUM", g.smooth(z, 0.9, 1.4), g.reg(5))
    c = g.mix(g.math("MULTIPLY", hot, g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.6, 1.0)), c, g.rgb((0.08, 0.07, 0.07)))
    c = g.mix(g.math("MULTIPLY", g.reg(6), 0.9), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.26, 0.3, 0.24)), g.rgb((0.4, 0.42, 0.34))))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.4), c, g.rgb((0.9, 0.72, 0.52)))
    return g.finish(c, 0.88, g.bump(g.math("ADD", g.noise(p, 25.0, 3.0), g.math("MULTIPLY", crack, -1.0)), 0.35, 0.004))


def sphagnum(name="DK_Sphagnum"):
    """Sphagnum hummocks: cushions of moss in patches of red, ochre and green, the tiny heads giving a fine knobbly
    texture, wet and dark in the hollows."""
    g = new(name)
    p = g.obj()
    patch = g.noise(p, 3.6, 3.0, 0.6)
    red = g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.44, 0.16, 0.1)), g.rgb((0.6, 0.27, 0.15)))
    green = g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.34, 0.46, 0.14)), g.rgb((0.52, 0.6, 0.22)))
    ochre = g.rgb((0.66, 0.5, 0.2))
    c = g.mix(g.smooth(patch, 0.36, 0.46), red, green)
    c = g.mix(g.math("MULTIPLY", g.smooth(patch, 0.62, 0.7), 0.85), c, ochre)
    heads = g.voronoi(p, 90.0, 1.0, "F1", "Distance")
    c = g.mix(g.math("MULTIPLY", g.smooth(heads, 0.25, 0.6), 0.35), c, g.rgb((0.12, 0.1, 0.05)))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.15
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.8), c, g.rgb((0.06, 0.06, 0.03)))
    return g.finish(c, 0.7, g.bump(g.math("SUBTRACT", 1.0, heads), 0.5, 0.004))


def peat(name="DK_Peat"):
    """Cut peat: dark brown and fibrous, the spade-cut faces smoother and a little lighter, drying grey-brown on the
    tops, rootlets showing."""
    g = new(name)
    p = g.obj()
    fib = g.noise(g.scale_vec(p, (50.0, 50.0, 12.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(fib, 0.3, 0.7, 0.0, 1.0), g.rgb((0.13, 0.08, 0.05)), g.rgb((0.26, 0.17, 0.1)))
    c = g.mix(g.math("MULTIPLY", _up(g, 0.6, 0.95), 0.6), c, g.rgb((0.36, 0.3, 0.24)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.45), c, g.rgb((0.44, 0.32, 0.22)))
    root = g.smooth(g.noise(g.scale_vec(p, (120.0, 120.0, 8.0)), 1.0, 2.0), 0.66, 0.7)
    c = g.mix(g.math("MULTIPLY", root, 0.6), c, g.rgb((0.6, 0.48, 0.32)))
    return g.finish(c, 0.92, g.bump(fib, 0.45, 0.005))


def bog_oak(name="DK_BogOak"):
    """Bog oak: ancient wood stained jet black by the peat, split deep along the grain, grey-brown on the dried tops."""
    g = new(name)
    p = g.obj()
    grain = g.noise(g.scale_vec(p, (3.0, 40.0, 40.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(grain, 0.3, 0.7, 0.0, 1.0), g.rgb((0.05, 0.045, 0.04)), g.rgb((0.14, 0.12, 0.1)))
    split = g.smooth(grain, 0.3, 0.24)
    c = g.mix(split, c, g.rgb((0.01, 0.01, 0.01)))
    c = g.mix(g.math("MULTIPLY", _up(g, 0.55, 0.95), 0.55), c, g.rgb((0.32, 0.28, 0.24)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.4), c, g.rgb((0.4, 0.36, 0.3)))
    return g.finish(c, 0.7, g.bump(g.math("SUBTRACT", grain, split), 0.6, 0.006))


# ------------------------------------------------------------------------------------------------ Classical Age
def limestone_rock(name="DK_Limestone", base=(0.8, 0.78, 0.71), hi=(0.9, 0.88, 0.82), grime=(0.48, 0.46, 0.4)):
    """Pale Mediterranean limestone: cream-grey, pitted, sharp pale edges, dark grey-brown in the cracks, crusts of grey
    and orange lichen on the faces turned to the sky; label 7 = rain-streaked grime low down."""
    g = new(name)
    p = g.obj()
    macro = g.noise(p, 2.4, 3.0, 0.55)
    c = g.mix(g.remap(macro, 0.35, 0.65, 0.0, 1.0), g.rgb(base), g.rgb(hi))
    pits = g.smooth(g.noise(p, 75.0, 2.0, 0.6), 0.62, 0.68)
    c = g.mix(g.math("MULTIPLY", pits, 0.45), c, g.rgb(tuple(x * 0.62 for x in base)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.65), c, g.rgb((0.36, 0.34, 0.3)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.6), c, g.rgb((0.97, 0.96, 0.92)))
    up = _up(g, 0.45, 0.85)
    lich = g.math("MULTIPLY", up, g.smooth(g.noise(p, 7.0, 3.0, 0.6), 0.6, 0.66))
    c = g.mix(g.math("MULTIPLY", lich, 0.7), c, g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.62, 0.62, 0.56)), g.rgb((0.7, 0.68, 0.6))))
    orange = g.math("MULTIPLY", up, g.smooth(g.noise(p, 11.0, 3.0, 0.6), 0.68, 0.72))
    c = g.mix(g.math("MULTIPLY", orange, 0.6), c, g.rgb((0.86, 0.6, 0.26)))
    streak = g.remap(g.noise(g.scale_vec(p, (9.0, 9.0, 1.2)), 1.0, 2.0), 0.3, 0.7, 0.35, 0.85)
    c = g.mix(g.math("MULTIPLY", g.reg(7), streak), c, g.rgb(grime))
    h = g.math("ADD", g.math("MULTIPLY", pits, -0.6), g.noise(p, 16.0, 4.0, 0.6))
    return g.finish(c, 0.82, g.bump(h, 0.35, 0.006))


def dry_turf(name="DK_Turf", top=((0.6, 0.52, 0.26), (0.74, 0.64, 0.34)), earth=((0.52, 0.32, 0.2), (0.62, 0.42, 0.27))):
    """The ground a Classical Age landmark sits in: dry golden grass on top, red-brown earth on the sides and bare
    patches, pebbles."""
    g = new(name)
    p = g.obj()
    up = _up(g, 0.5, 0.85)
    grass = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(top[0]), g.rgb(top[1]))
    blades = g.smooth(g.noise(g.scale_vec(p, (60.0, 60.0, 8.0)), 1.0, 2.0), 0.55, 0.65)
    grass = g.mix(g.math("MULTIPLY", blades, 0.4), grass, g.rgb(tuple(min(1.0, x * 1.2) for x in top[1])))
    soil = g.mix(g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(earth[0]), g.rgb(earth[1]))
    peb = g.smooth(g.voronoi(p, 22.0), 0.12, 0.08)
    soil = g.mix(g.math("MULTIPLY", peb, 0.5), soil, g.rgb((0.74, 0.7, 0.62)))
    bare = g.smooth(g.noise(p, 2.0, 3.0, 0.6), 0.6, 0.68)
    m = g.math("MULTIPLY", up, g.math("SUBTRACT", 1.0, bare))
    c = g.mix(m, soil, grass)
    return g.finish(c, 0.9, g.bump(g.math("ADD", peb, g.math("MULTIPLY", blades, 0.5)), 0.3, 0.006))



# ------------------------------------------------------------------------------------------------ Gunpowder Age
def jungle_bark(name="DK_JungleBark"):
    """Rainforest bark: smooth and pale grey-brown, blotched with white and grey-green lichen, streaked darker where the
    rain runs down, mossy round the foot and the buttresses."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(g.scale_vec(p, (3.0, 3.0, 0.8)), 2.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.42, 0.37, 0.3)), g.rgb((0.56, 0.5, 0.42)))
    streak = g.noise(g.scale_vec(p, (14.0, 14.0, 1.5)), 1.0, 3.0, 0.6)
    c = g.mix(g.math("MULTIPLY", g.smooth(streak, 0.55, 0.7), 0.5), c, g.rgb((0.28, 0.24, 0.19)))
    lich = g.smooth(g.noise(p, 4.5, 3.0, 0.6), 0.6, 0.66)
    c = g.mix(g.math("MULTIPLY", lich, 0.8), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.78, 0.8, 0.72)), g.rgb((0.6, 0.66, 0.52))))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), c, g.rgb((0.16, 0.13, 0.1)))
    foot = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(_z(g), 0.15, 0.8)), g.smooth(g.noise(p, 3.0, 3.0), 0.42, 0.58))
    c = g.mix(g.math("MULTIPLY", foot, 0.9), c, g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.18, 0.34, 0.1)), g.rgb((0.32, 0.48, 0.14))))
    return g.finish(c, 0.8, g.bump(g.math("ADD", streak, g.math("MULTIPLY", lich, 0.4)), 0.25, 0.004))


def mossy_rock(name="DK_JungleRock"):
    """A boulder of the rainforest: dark wet grey-brown stone almost hidden under thick moss, bright where the light
    falls and dark in the hollows, pale lichen spots on the bare faces."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 2.4, 3.0, 0.55), 0.35, 0.65, 0.0, 1.0), g.rgb((0.3, 0.29, 0.26)), g.rgb((0.42, 0.4, 0.36)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.45), c, g.rgb((0.58, 0.56, 0.5)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), c, g.rgb((0.12, 0.12, 0.1)))
    lich = g.math("MULTIPLY", g.smooth(g.noise(p, 9.0, 3.0), 0.64, 0.7), 0.7)
    c = g.mix(lich, c, g.rgb((0.72, 0.74, 0.6)))
    up = _up(g, 0.05, 0.6)
    patch = g.smooth(g.noise(p, 2.6, 4.0, 0.6), 0.36, 0.5)
    moss = g.mix(g.noise(p, 18.0, 3.0), g.rgb((0.14, 0.32, 0.08)), g.rgb((0.3, 0.5, 0.12)))
    moss = g.mix(g.math("MULTIPLY", _up(g, 0.6, 0.95), 0.45), moss, g.rgb((0.44, 0.62, 0.16)))
    c = g.mix(g.math("MULTIPLY", up, patch), c, moss)
    h = g.math("ADD", g.math("MULTIPLY", g.math("MULTIPLY", up, patch), g.noise(p, 40.0, 2.0)), g.noise(p, 14.0, 4.0, 0.6))
    return g.finish(c, 0.82, g.bump(h, 0.4, 0.006))


def ruin_stone(name="DK_RuinStone"):
    """The temple's limestone: pale grey blocks in courses, black and green streaks run down from every ledge, thick
    moss on whatever faces the sky, dark in the joints and carvings; label 5 = the last traces of red stucco."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    z = sep.outputs["Z"]
    course, block = 0.16, 0.3
    row = g.math("FLOOR", g.math("DIVIDE", z, course))
    fz = g.math("SUBTRACT", g.math("DIVIDE", z, course), row)
    run = g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), g.math("MULTIPLY", g.math("MODULO", row, 2.0), block * 0.5))
    fx = g.math("FRACT", g.math("DIVIDE", run, block))
    jz = g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz))
    jx = g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx))
    jt = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.smooth(jz, 0.03, 0.09)), g.math("SUBTRACT", 1.0, g.smooth(jx, 0.015, 0.05)))
    up = _up(g, 0.55, 0.85)
    joint = g.math("MULTIPLY", jt, g.math("SUBTRACT", 1.0, up))
    blk = g.voronoi(g.scale_vec(p, (1.0 / block, 1.0 / block, 1.0 / course)), 1.0, 1.0, "F1", "Color")
    c = g.mix(g.remap(g.noise(p, 2.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.66, 0.65, 0.6)), g.rgb((0.76, 0.74, 0.68)))
    c = g.mix(g.math("MULTIPLY", g.smooth(blk, 0.4, 0.9), 0.22), c, g.rgb((0.56, 0.55, 0.5)))
    streak = g.smooth(g.noise(g.scale_vec(p, (11.0, 11.0, 1.1)), 1.0, 3.0, 0.6), 0.5, 0.66)
    c = g.mix(g.math("MULTIPLY", streak, 0.55), c, g.mix(g.noise(p, 6.0, 2.0), g.rgb((0.2, 0.2, 0.18)), g.rgb((0.26, 0.32, 0.2))))
    c = g.mix(joint, c, g.rgb((0.2, 0.2, 0.17)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.42), 0.6), c, g.rgb((0.14, 0.14, 0.12)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.45), c, g.rgb((0.86, 0.85, 0.8)))
    worn = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.smooth(pt, 0.515, 0.6), 0.85))
    red = g.mix(g.math("MULTIPLY", g.remap(g.noise(p, 30.0, 2.0), 0.3, 0.7, 0.0, 1.0), 0.35), g.rgb((0.66, 0.18, 0.1)), g.rgb((0.5, 0.13, 0.08)))
    fade = g.smooth(g.noise(p, 3.5, 3.0), 0.42, 0.56)
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", g.reg(5), worn), fade), c, red)
    patch = g.smooth(g.noise(p, 2.2, 4.0, 0.6), 0.38, 0.52)
    moss = g.mix(g.noise(p, 22.0, 3.0), g.rgb((0.16, 0.32, 0.08)), g.rgb((0.34, 0.52, 0.14)))
    m = g.math("MULTIPLY", up, patch)
    c = g.mix(m, c, moss)
    low = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(z, 0.05, 0.6)), g.smooth(g.noise(p, 4.0, 3.0), 0.45, 0.6))
    c = g.mix(g.math("MULTIPLY", low, 0.7), c, moss)
    h = g.math("ADD", g.math("MULTIPLY", joint, -0.7), g.math("MULTIPLY", g.noise(p, 20.0, 3.0), 0.35))
    h = g.math("ADD", h, g.math("MULTIPLY", m, g.math("MULTIPLY", g.noise(p, 45.0, 2.0), 0.6)))
    return g.finish(c, 0.88, g.bump(h, 0.32, 0.006))


def coco_bark(name="DK_CocoBark"):
    """A coconut palm's trunk: grey with a warm tan cast, ringed by the scars of old fronds (dark in the grooves), fine
    fibres running up it, paler and swollen at the foot."""
    g = new(name)
    p = g.obj()
    fib = g.noise(g.scale_vec(p, (50.0, 50.0, 5.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.46, 0.42, 0.36)), g.rgb((0.6, 0.55, 0.47)))
    c = g.mix(g.math("MULTIPLY", g.remap(fib, 0.3, 0.7, 0.0, 1.0), 0.35), c, g.rgb((0.36, 0.31, 0.25)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.495, 0.46), 0.85), c, g.rgb((0.2, 0.16, 0.12)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.505, 0.54), 0.5), c, g.rgb((0.72, 0.68, 0.6)))
    foot = g.math("SUBTRACT", 1.0, g.smooth(_z(g), 0.05, 0.4))
    c = g.mix(g.math("MULTIPLY", foot, 0.5), c, g.rgb((0.58, 0.5, 0.38)))
    return g.finish(c, 0.85, g.bump(fib, 0.35, 0.003))


def broadleaf(name, base=(0.06, 0.26, 0.08), hi=(0.22, 0.48, 0.14), edge=None, rough=0.42, heart=None):
    """A big glossy leaf (aroids, heliconias, bromeliads): a smooth deep green, brighter where it faces the sky, a sheen
    of fine streaks, dark in the hollows; `edge` a colour for the rims (dry, torn: bananas); label 5 = `heart`."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 2.5, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(min(1.0, x * 1.25) for x in base)))
    c = g.mix(g.math("MULTIPLY", _up(g, 0.1, 0.9), 0.55), c, g.rgb(hi))
    streak = g.noise(g.scale_vec(p, (40.0, 40.0, 40.0)), 1.0, 2.0)
    c = g.mix(g.math("MULTIPLY", g.remap(streak, 0.35, 0.65, 0.0, 1.0), 0.18), c, g.rgb(tuple(x * 0.75 for x in base)))
    pt = g.geo("Pointiness")
    if edge is not None:
        c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.52, 0.58), g.smooth(g.noise(p, 5.0, 2.0), 0.4, 0.55)), c, g.rgb(edge))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.15
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.75), c, g.rgb((0.02, 0.08, 0.03)))
    if heart is not None:
        c = g.mix(g.reg(5), c, g.mix(g.noise(p, 12.0, 2.0), g.rgb(heart), g.rgb(tuple(min(1.0, x * 1.25) for x in heart))))
    return g.finish(c, rough, g.bump(streak, 0.15, 0.002))


def banana_stem(name="DK_BananaStem"):
    """Banana pseudostems: smooth green sheaths with fine streaks, blotched dark purple-brown, paler toward the top."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(g.scale_vec(p, (30.0, 30.0, 3.0)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.32, 0.46, 0.16)), g.rgb((0.46, 0.58, 0.24)))
    blot = g.smooth(g.noise(p, 9.0, 3.0, 0.6), 0.6, 0.66)
    c = g.mix(g.math("MULTIPLY", blot, 0.85), c, g.rgb((0.26, 0.14, 0.12)))
    c = g.mix(g.math("MULTIPLY", g.smooth(_z(g), 0.6, 1.3), 0.35), c, g.rgb((0.6, 0.7, 0.32)))
    return g.finish(c, 0.5)


def fungus(name="DK_Fungus"):
    """Bracket fungi: tiers of shelves banded orange, rust and cream, a pale rim."""
    g = new(name)
    p = g.obj()
    bands = g.wave(p, 40.0, 2.0, 1.0, "RINGS", "Z")
    c = g.mix(g.smooth(bands, 0.3, 0.7), g.rgb((0.86, 0.48, 0.14)), g.rgb((0.62, 0.3, 0.12)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.56), 0.85), c, g.rgb((0.96, 0.88, 0.66)))
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, _up(g, -0.2, 0.3)), 0.6), c, g.rgb((0.9, 0.82, 0.62)))
    return g.finish(c, 0.65, g.bump(bands, 0.15, 0.002))


def jungle_floor(name="DK_JungleFloor"):
    """The ground a jungle landmark sits in: dark damp earth under fallen leaves (brown, ochre, rust) with moss creeping
    over it; earth on the sides."""
    g = new(name)
    p = g.obj()
    earth = g.mix(g.noise(p, 6.0, 3.0), g.rgb((0.16, 0.11, 0.07)), g.rgb((0.26, 0.18, 0.11)))
    lv = g.voronoi(p, 30.0, 1.0, "F1", "Color")
    litter = g.mix(g.smooth(lv, 0.3, 0.7), g.rgb((0.42, 0.27, 0.14)), g.rgb((0.58, 0.42, 0.2)))
    litter = g.mix(g.math("MULTIPLY", g.smooth(lv, 0.75, 0.9), 0.8), litter, g.rgb((0.52, 0.2, 0.1)))
    edge = g.smooth(g.voronoi(p, 30.0, 1.0, "DISTANCE_TO_EDGE"), 0.06, 0.0)
    litter = g.mix(g.math("MULTIPLY", edge, 0.7), litter, g.rgb((0.12, 0.08, 0.05)))
    up = _up(g, 0.5, 0.85)
    top = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 2.5, 3.0), 0.48, 0.6), 0.9), litter,
                g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.16, 0.3, 0.08)), g.rgb((0.28, 0.44, 0.12))))
    c = g.mix(up, earth, top)
    return g.finish(c, 0.9, g.bump(g.math("ADD", edge, g.noise(p, 30.0, 2.0)), 0.3, 0.004))


def earthwork(name="DK_Earthwork"):
    """Fresh-dug siege earth: brown clods and layers on the slopes, the tops trampled grass gone patchy and yellow, a
    few stones."""
    g = new(name)
    p = g.obj()
    dirt = g.mix(g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.36, 0.26, 0.16)), g.rgb((0.5, 0.38, 0.24)))
    strata = g.wave(p, 6.0, 3.0, 2.0, "BANDS", "Z")
    dirt = g.mix(g.math("MULTIPLY", g.smooth(strata, 0.6, 0.85), 0.35), dirt, g.rgb((0.28, 0.19, 0.11)))
    clod = g.smooth(g.voronoi(p, 18.0), 0.1, 0.05)
    dirt = g.mix(g.math("MULTIPLY", clod, 0.4), dirt, g.rgb((0.58, 0.46, 0.3)))
    peb = g.smooth(g.voronoi(p, 30.0), 0.08, 0.04)
    dirt = g.mix(g.math("MULTIPLY", peb, 0.6), dirt, g.rgb((0.62, 0.6, 0.55)))
    up = _up(g, 0.55, 0.85)
    grass = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.32, 0.42, 0.14)), g.rgb((0.56, 0.56, 0.24)))
    bare = g.smooth(g.noise(p, 2.4, 3.0, 0.6), 0.5, 0.62)
    m = g.math("MULTIPLY", up, g.math("SUBTRACT", 1.0, bare))
    c = g.mix(m, dirt, grass)
    return g.finish(c, 0.92, g.bump(g.math("ADD", clod, g.math("MULTIPLY", strata, 0.4)), 0.35, 0.006))


def net(name="DK_Net"):
    """A fishing net drying: brown cords knotted in a square mesh over dark gaps (the net hangs in the XZ plane)."""
    g = new(name)
    p = g.obj()
    wx = g.wave(p, 26.0, 0.6, 1.0, "BANDS", "X")
    wz = g.wave(p, 26.0, 0.6, 1.0, "BANDS", "Z")
    cords = g.math("MAXIMUM", g.smooth(wx, 0.75, 0.92), g.smooth(wz, 0.75, 0.92))
    c = g.mix(g.noise(p, 6.0, 2.0), g.rgb((0.14, 0.11, 0.08)), g.rgb((0.2, 0.16, 0.11)))
    cord_c = g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.58, 0.47, 0.3)), g.rgb((0.72, 0.6, 0.4)))
    c = g.mix(cords, c, cord_c)
    return g.finish(c, 0.9, g.bump(cords, 0.5, 0.004))


def whitewash(name="DK_Whitewash", base=(0.92, 0.9, 0.84), stone=(0.6, 0.56, 0.5), course=(0.74, 0.7, 0.62)):
    """Whitewashed render over rubble stone (a mill, a lookout, a tavern's ground floor): off-white, grimy low down;
    label 7 = where it has flaked away (the rubble shows: stones of different greys, dark gaps), 5 = stone courses."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 4.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(base), g.rgb(tuple(x * 0.9 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(_z(g), 0.05, 0.45)), 0.45), c, g.rgb(tuple(x * 0.62 for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.48, 0.43), 0.5), c, g.rgb((0.42, 0.4, 0.36)))
    sp = g.scale_vec(p, (5.0, 5.0, 9.0))
    shade = g.voronoi(sp, 1.0, 0.85, "F1", "Color")
    gap = g.smooth(g.voronoi(sp, 1.0, 0.85, "DISTANCE_TO_EDGE", "Distance"), 0.08, 0.03)
    rub = g.mix(shade, g.rgb(tuple(x * 0.75 for x in stone)), g.rgb(tuple(min(1.0, x * 1.2) for x in stone)))
    rub = g.mix(gap, rub, g.rgb((0.18, 0.16, 0.14)))
    c = g.mix(g.reg(7), c, rub)
    c = g.mix(g.reg(5), c, g.rgb(course))
    h = g.math("MULTIPLY", g.reg(7), g.math("SUBTRACT", 1.0, gap))
    return g.finish(c, 0.88, g.bump(g.math("ADD", h, g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.3)), 0.4, 0.006))


def cane(name="DK_Cane"):
    """Walls of split cane: pale straw-gold strips side by side, darker between them, darker bindings (label 5)."""
    g = new(name)
    p = g.obj()
    strips = g.noise(g.scale_vec(p, (60.0, 60.0, 3.0)), 1.0, 2.0, 0.5)
    c = g.mix(g.remap(strips, 0.3, 0.7, 0.0, 1.0), g.rgb((0.62, 0.52, 0.3)), g.rgb((0.8, 0.7, 0.44)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.49, 0.45), 0.7), c, g.rgb((0.3, 0.24, 0.13)))
    c = g.mix(g.reg(5), c, g.rgb((0.36, 0.26, 0.15)))
    return g.finish(c, 0.8, g.bump(strips, 0.3, 0.003))


def brushwood(name="DK_Brushwood"):
    """Fascines: brushwood laid along the bundle (twigs grey-brown and russet, dark gaps), bound with green withies
    (label 5)."""
    g = new(name)
    p = g.obj()
    tw = g.noise(g.scale_vec(p, (2.0, 50.0, 50.0)), 1.0, 3.0, 0.6)
    c = g.mix(g.remap(tw, 0.3, 0.7, 0.0, 1.0), g.rgb((0.3, 0.22, 0.14)), g.rgb((0.52, 0.42, 0.28)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 2.0), 0.55, 0.7), 0.5), c, g.rgb((0.5, 0.28, 0.16)))
    c = g.mix(g.math("MULTIPLY", g.smooth(tw, 0.3, 0.2), 0.7), c, g.rgb((0.12, 0.09, 0.06)))
    c = g.mix(g.reg(5), c, g.rgb((0.4, 0.42, 0.2)))
    return g.finish(c, 0.88, g.bump(tw, 0.5, 0.004))


def rusty_iron(name="DK_RustyIron", dark=False):
    """Iron left out by the sea or blackened shot: forged iron (mats._iron_col) eaten by rust in patches; dark=True:
    cast-iron shot, nearly black."""
    from mats import _iron_col
    g = new(name)
    p = g.obj()
    if dark:
        c, rs = _iron_col(g, p, base=(0.13, 0.13, 0.14), hi=(0.42, 0.43, 0.46), dark=(0.04, 0.04, 0.045), rust=(0.34, 0.16, 0.08))
        rough = 0.5
    else:
        c, rs = _iron_col(g, p, base=(0.26, 0.22, 0.2), hi=(0.6, 0.56, 0.52), rust=(0.56, 0.26, 0.1))
        patch = g.smooth(g.noise(p, 5.0, 3.0), 0.48, 0.6)
        c = g.mix(g.math("MULTIPLY", patch, 0.85), c, g.mix(g.noise(p, 30.0, 2.0), g.rgb((0.52, 0.24, 0.1)), g.rgb((0.68, 0.36, 0.14))))
        rough = 0.75
    h = g.math("ADD", g.math("MULTIPLY", g.voronoi(p, 60.0, 1.0, "F1", "Distance"), 0.3), g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.3))
    return g.finish(c, rough, g.bump(h, 0.18, 0.002))


def two_tone(name, col, col5, rough=0.4, col6=None, hi=None):
    """A plain colour (mottled a little, brighter on the edges) with a second on label 5 (and a third on label 6):
    gems, grapes, flowers' bracts."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 30.0, 2.0), g.rgb(col), g.rgb(tuple(min(1.0, x * 1.15) for x in col)))
    c = g.mix(g.reg(5), c, g.mix(g.noise(p, 30.0, 2.0), g.rgb(col5), g.rgb(tuple(min(1.0, x * 1.15) for x in col5))))
    if col6 is not None:
        c = g.mix(g.reg(6), c, g.rgb(col6))
    if hi is not None:
        c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.6), c, g.rgb(hi))
    return g.finish(c, rough)


def round_leaves(name="DK_SeaGrape"):
    """Sea-grape leaves: big round leathery leaves, glossy green, their veins and some whole leaves flushed red."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.22, 0.42, 0.14)), g.rgb((0.36, 0.56, 0.2)))
    c = g.mix(g.math("MULTIPLY", _up(g, 0.2, 0.9), 0.4), c, g.rgb((0.5, 0.66, 0.26)))
    red = g.smooth(g.noise(p, 4.0, 2.0), 0.62, 0.7)
    c = g.mix(g.math("MULTIPLY", red, 0.75), c, g.rgb((0.62, 0.24, 0.14)))
    vein = g.smooth(g.voronoi(p, 40.0, 1.0, "DISTANCE_TO_EDGE"), 0.035, 0.0)
    c = g.mix(g.math("MULTIPLY", vein, 0.45), c, g.rgb((0.66, 0.32, 0.2)))
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8)
    ao.inputs["Distance"].default_value = 0.15
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.75), c, g.rgb((0.03, 0.08, 0.03)))
    return g.finish(c, 0.45, g.bump(vein, 0.2, 0.002))


def brazier(name="DK_Brazier"):
    """A brazier: blackened iron (sooty toward the bowl) on a pedestal of pale stone (label 7)."""
    from mats import _iron_col
    g = new(name)
    p = g.obj()
    c, rs = _iron_col(g, p, base=(0.18, 0.18, 0.19), hi=(0.5, 0.5, 0.52))
    c = g.mix(g.math("MULTIPLY", g.smooth(_z(g), 0.75, 1.05), 0.7), c, g.rgb((0.06, 0.05, 0.05)))
    st = g.mix(g.remap(g.noise(p, 4.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.78, 0.73, 0.62)), g.rgb((0.88, 0.83, 0.72)))
    st = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.48, 0.43), 0.5), st, g.rgb((0.42, 0.38, 0.32)))
    c = g.mix(g.reg(7), c, st)
    return g.finish(c, g.mixf(g.reg(7), 0.45, 0.85))


# ------------------------------------------------------------------------------------------------ Industrial Age
def _cell_rand(g, a, b):
    """A random 0..1 value per (a, b) cell (the integer parts of two node outputs): every brick or slate its own shade."""
    cmb = g.node("ShaderNodeCombineXYZ")
    g.put(cmb.inputs["X"], a)
    g.put(cmb.inputs["Y"], b)
    wn = g.node("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    g.put(wn.inputs["Vector"], cmb.outputs[0])
    return wn.outputs["Value"]


def _paint_col(g, p, col, edge=0.5):
    """A painted surface: the paint mottled a little, lighter on worn edges, dark grime in the recesses."""
    c = g.mix(g.remap(g.noise(p, 4.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(col), g.rgb(tuple(min(1.0, x * 1.18) for x in col)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), edge), c, g.rgb(tuple(min(1.0, x * 1.5 + 0.1) for x in col)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), c, g.rgb(tuple(x * 0.45 for x in col)))
    return c


def _brass(g):
    pt = g.geo("Pointiness")
    br = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.76, 0.54, 0.2)), g.rgb((1.0, 0.88, 0.55)))
    return g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.6), br, g.rgb((0.32, 0.2, 0.08)))


def brick(name="DK_Brick", base=(0.56, 0.24, 0.15), mortar=(0.64, 0.58, 0.5), course=0.07, length=0.19, soot=0.3):
    """Victorian red brick in stretcher bond: every brick its own shade of red (a few over-burnt purple), pale lime mortar
    sunk in the joints (none drawn across flat tops), soot-darkened in streaks (`soot`), pale on worn arrises.
    Labels: 5 = soot (black: chimney tops, furnace mouths), 6 = cream stone dressings (sills, lintels, copings, string
    courses), 7 = grime streaking down, 8 = blue-black engineering brick (plinths, bands), 9 = painted (dark green)."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    z = sep.outputs["Z"]
    row = g.math("FLOOR", g.math("DIVIDE", z, course))
    fz = g.math("SUBTRACT", g.math("DIVIDE", z, course), row)
    run = g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), g.math("MULTIPLY", g.math("MODULO", row, 2.0), length * 0.5))
    col = g.math("FLOOR", g.math("DIVIDE", run, length))
    fx = g.math("SUBTRACT", g.math("DIVIDE", run, length), col)
    jz = g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz))
    jx = g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx))
    joint = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.smooth(jz, 0.05, 0.13)), g.math("SUBTRACT", 1.0, g.smooth(jx, 0.018, 0.05)))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    joint = g.math("MULTIPLY", joint, g.math("SUBTRACT", 1.0, g.smooth(nz.outputs["Z"], 0.7, 0.9)))
    rnd = _cell_rand(g, row, col)
    c = g.mix(rnd, g.rgb(tuple(x * 0.78 for x in base)), g.rgb(tuple(min(1.0, x * 1.18) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(rnd, 0.86, 0.9), 0.85), c, g.rgb((0.3, 0.15, 0.15)))            # over-burnt
    c = g.mix(g.math("MULTIPLY", g.remap(g.noise(p, 30.0, 2.0), 0.3, 0.7, 0.0, 1.0), 0.25), c, g.rgb(tuple(x * 0.7 for x in base)))
    eng = g.mix(rnd, g.rgb((0.12, 0.11, 0.14)), g.rgb((0.22, 0.2, 0.24)))
    c = g.mix(g.reg(8), c, eng)
    c = g.mix(joint, c, g.mix(g.reg(8), g.rgb(mortar), g.rgb(tuple(x * 0.55 for x in mortar))))
    st = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.76, 0.7, 0.58)), g.rgb((0.86, 0.8, 0.68)))
    c = g.mix(g.reg(6), c, st)
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.4), c, g.rgb((0.82, 0.62, 0.48)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), c, g.rgb((0.14, 0.1, 0.08)))
    streak = g.remap(g.noise(g.scale_vec(p, (9.0, 9.0, 1.1)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    c = g.mix(g.math("MULTIPLY", g.smooth(streak, 0.45, 0.75), soot), c, g.rgb((0.16, 0.12, 0.1)))
    c = g.mix(g.math("MULTIPLY", g.reg(7), g.mixf(streak, 0.35, 0.85)), c, g.rgb((0.13, 0.1, 0.085)))
    c = g.mix(g.math("MULTIPLY", g.reg(9), 0.95), c, _paint_col(g, p, (0.1, 0.22, 0.15)))
    c = g.mix(g.math("MULTIPLY", g.reg(5), g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.7, 1.0)), c,
              g.mix(g.noise(p, 25.0, 2.0), g.rgb((0.05, 0.045, 0.04)), g.rgb((0.12, 0.1, 0.09))))
    h = g.math("ADD", g.math("MULTIPLY", joint, -0.8), g.math("MULTIPLY", g.noise(p, 40.0, 2.0), 0.25))
    return g.finish(c, g.mixf(g.reg(9), 0.86, 0.45), g.bump(h, 0.35, 0.006))


def slate(name="DK_Slate", base=(0.25, 0.27, 0.31), course=0.075, width=0.13):
    """Welsh slate: courses of grey-blue slates (each its own shade), dark gaps under every course and between slates,
    soot and pale lichen; label 5 = the ridge tiles (dark red-brown terracotta), 6 = lead flashing (pale grey)."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    row = g.math("FLOOR", g.math("DIVIDE", sep.outputs["Z"], course))
    fz = g.math("SUBTRACT", g.math("DIVIDE", sep.outputs["Z"], course), row)
    run = g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), g.math("MULTIPLY", g.math("MODULO", row, 2.0), width * 0.5))
    col = g.math("FLOOR", g.math("DIVIDE", run, width))
    fx = g.math("SUBTRACT", g.math("DIVIDE", run, width), col)
    gap = g.math("MAXIMUM", g.smooth(fz, 0.12, 0.0), g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx)), 0.01, 0.04)))
    rnd = _cell_rand(g, row, col)
    c = g.mix(rnd, g.rgb(tuple(x * 0.8 for x in base)), g.rgb(tuple(min(1.0, x * 1.22) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(rnd, 0.8, 0.86), 0.6), c, g.rgb((0.3, 0.27, 0.32)))
    c = g.mix(g.math("MULTIPLY", gap, 0.85), c, g.rgb((0.06, 0.065, 0.075)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 6.0, 3.0), 0.62, 0.7), 0.6), c, g.rgb((0.6, 0.62, 0.52)))     # lichen
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(g.scale_vec(p, (6.0, 6.0, 1.5)), 1.0, 2.0), 0.52, 0.72), 0.45), c, g.rgb((0.1, 0.1, 0.11)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.45), c, g.rgb((0.56, 0.58, 0.62)))
    c = g.mix(g.reg(5), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.36, 0.17, 0.11)), g.rgb((0.46, 0.24, 0.15))))
    c = g.mix(g.reg(6), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb((0.5, 0.52, 0.55)), g.rgb((0.62, 0.64, 0.66))))
    h = g.math("ADD", g.math("MULTIPLY", gap, -0.8), g.math("MULTIPLY", fz, 0.4))
    return g.finish(c, 0.62, g.bump(h, 0.4, 0.006))


def painted_iron(name, paint=(0.1, 0.22, 0.15), col5=(0.62, 0.1, 0.07), col7=(0.06, 0.06, 0.065), rough=0.45):
    """Painted iron and steel (lamp posts, railings, engines, machines): the paint lighter on worn edges, chipped back
    to dark iron on the sharpest arrises, rust in the crevices; label 5 and 7 = two more paints (a red buffer beam, black
    bands), 6 = brass (domes, caps, gauges, rails)."""
    g = new(name)
    p = g.obj()
    c = _paint_col(g, p, paint)
    c = g.mix(g.reg(5), c, _paint_col(g, p, col5))
    c = g.mix(g.reg(7), c, _paint_col(g, p, col7))
    pt = g.geo("Pointiness")
    nb = g.math("SUBTRACT", 1.0, g.reg(6))
    chip = g.math("MULTIPLY", g.math("MULTIPLY", g.smooth(pt, 0.535, 0.6), g.smooth(g.noise(p, 30.0, 2.0), 0.45, 0.55)), nb)
    c = g.mix(g.math("MULTIPLY", chip, 0.8), c, g.rgb((0.3, 0.29, 0.29)))
    rs = g.math("MULTIPLY", g.math("MULTIPLY", g.smooth(pt, 0.47, 0.42), g.smooth(g.noise(p, 12.0, 3.0), 0.5, 0.62)), nb)
    c = g.mix(g.math("MULTIPLY", rs, 0.7), c, g.rgb((0.42, 0.2, 0.08)))
    c = g.mix(g.reg(6), c, _brass(g))
    h = g.math("ADD", g.math("MULTIPLY", g.noise(p, 60.0, 2.0), 0.2), g.math("MULTIPLY", chip, -0.6))
    return g.finish(c, g.mixf(g.reg(6), rough, 0.25), g.bump(h, 0.15, 0.002))


def coal(name="DK_Coal"):
    """Coal: black lumps with flat glassy facets catching the light, grey-blue sheen on top, dust in the hollows."""
    g = new(name)
    p = g.obj()
    cell = g.voronoi(p, 26.0, 1.0, "F1", "Color")
    c = g.mix(cell, g.rgb((0.03, 0.03, 0.035)), g.rgb((0.12, 0.115, 0.125)))
    edge = g.smooth(g.voronoi(p, 26.0, 1.0, "DISTANCE_TO_EDGE", "Distance"), 0.05, 0.0)
    c = g.mix(g.math("MULTIPLY", edge, 0.6), c, g.rgb((0.3, 0.31, 0.35)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.51, 0.57), 0.6), c, g.rgb((0.42, 0.43, 0.48)))
    up = _up(g, 0.5, 0.95)
    c = g.mix(g.math("MULTIPLY", up, 0.25), c, g.rgb((0.2, 0.21, 0.25)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.geo("Pointiness"), 0.48, 0.43), 0.6), c, g.rgb((0.015, 0.015, 0.015)))
    return g.finish(c, 0.55, g.bump(g.voronoi(p, 26.0, 1.0, "F1", "Distance"), 0.6, 0.006))


def cinders(name="DK_Cinders"):
    """The ground of a works yard: dark grey-brown ash and cinders, lumps of clinker, rust stains, a scruff of sooty
    grass on top."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 5.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.18, 0.16, 0.15)), g.rgb((0.3, 0.27, 0.24)))
    clk = g.smooth(g.voronoi(p, 24.0), 0.12, 0.06)
    c = g.mix(g.math("MULTIPLY", clk, 0.6), c, g.rgb((0.1, 0.1, 0.11)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 3.0), 0.6, 0.7), 0.6), c, g.rgb((0.42, 0.22, 0.1)))
    up = _up(g, 0.55, 0.85)
    grass = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb((0.22, 0.28, 0.12)), g.rgb((0.38, 0.42, 0.2)))
    m = g.math("MULTIPLY", up, g.smooth(g.noise(p, 2.2, 3.0, 0.6), 0.52, 0.64))
    c = g.mix(m, c, grass)
    return g.finish(c, 0.92, g.bump(g.math("ADD", clk, g.noise(p, 40.0, 2.0)), 0.35, 0.005))


def setts(name="DK_Setts"):
    """Granite setts: grey-brown cobbles in rows (dark grit between them), wet and darker in patches, worn shiny tops."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    w, l = 0.07, 0.11
    row = g.math("FLOOR", g.math("DIVIDE", sep.outputs["Y"], w))
    fy = g.math("SUBTRACT", g.math("DIVIDE", sep.outputs["Y"], w), row)
    run = g.math("ADD", sep.outputs["X"], g.math("MULTIPLY", g.math("MODULO", row, 2.0), l * 0.5))
    col = g.math("FLOOR", g.math("DIVIDE", run, l))
    fx = g.math("SUBTRACT", g.math("DIVIDE", run, l), col)
    gap = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fy, g.math("SUBTRACT", 1.0, fy)), 0.04, 0.12)),
                 g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx)), 0.03, 0.08)))
    rnd = _cell_rand(g, row, col)
    c = g.mix(rnd, g.rgb((0.32, 0.31, 0.3)), g.rgb((0.5, 0.47, 0.43)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 2.5, 3.0), 0.55, 0.68), 0.5), c, g.rgb((0.18, 0.18, 0.19)))
    c = g.mix(gap, c, g.rgb((0.09, 0.085, 0.08)))
    up = _up(g, 0.5, 0.85)
    c = g.mix(g.math("SUBTRACT", 1.0, up), g.rgb((0.26, 0.22, 0.18)), c)
    return g.finish(c, g.mixf(g.smooth(g.noise(p, 2.5, 3.0), 0.55, 0.68), 0.7, 0.35), g.bump(g.math("MULTIPLY", gap, -1.0), 0.4, 0.005))


def ballast(name="DK_Ballast"):
    """Track ballast: grey crushed stone chips, dark gaps, stained brown with rust and oil."""
    g = new(name)
    p = g.obj()
    cell = g.voronoi(p, 40.0, 1.0, "F1", "Color")
    c = g.mix(cell, g.rgb((0.36, 0.34, 0.32)), g.rgb((0.58, 0.56, 0.52)))
    c = g.mix(g.smooth(g.voronoi(p, 40.0, 1.0, "DISTANCE_TO_EDGE", "Distance"), 0.06, 0.0), c, g.rgb((0.1, 0.09, 0.08)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 3.0), 0.55, 0.7), 0.6), c, g.rgb((0.32, 0.2, 0.12)))
    return g.finish(c, 0.88, g.bump(g.voronoi(p, 40.0, 1.0, "F1", "Distance"), 0.5, 0.005))


def plane_bark(name="DK_PlaneBark"):
    """A London plane's bark: flaking in patches of olive-grey, cream and khaki, soot-blackened, darker at the foot."""
    g = new(name)
    p = g.obj()
    n1 = g.noise(g.scale_vec(p, (1.0, 1.0, 0.6)), 7.0, 2.0, 0.5)
    n2 = g.noise(g.scale_vec(p, (1.0, 1.0, 0.6)), 11.0, 2.0, 0.5)
    c = g.mix(g.smooth(n1, 0.47, 0.53), g.rgb((0.38, 0.38, 0.3)), g.rgb((0.7, 0.66, 0.5)))
    c = g.mix(g.smooth(n2, 0.56, 0.6), c, g.rgb((0.46, 0.38, 0.26)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(g.scale_vec(p, (8.0, 8.0, 1.2)), 1.0, 2.0), 0.45, 0.7), 0.45), c, g.rgb((0.12, 0.11, 0.1)))
    c = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.smooth(_z(g), 0.05, 0.5)), 0.5), c, g.rgb((0.14, 0.12, 0.1)))
    h = g.math("ADD", g.smooth(n1, 0.47, 0.53), g.math("MULTIPLY", g.smooth(n2, 0.56, 0.6), 0.5))
    return g.finish(c, 0.8, g.bump(h, 0.25, 0.003))


def glazing(name="DK_Glazing", glass=(0.1, 0.13, 0.16), bar=(0.84, 0.8, 0.7), pitch=0.16, rail=0.2):
    """Roof glazing (a sawtooth's north lights): dark glass catching the sky, with glazing bars painted in (every `pitch`
    along X, a rail every `rail` up it), dirty along the bars' feet."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    fx = g.math("FRACT", g.math("DIVIDE", sep.outputs["X"], pitch))
    fz = g.math("FRACT", g.math("DIVIDE", sep.outputs["Z"], rail))
    bx = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx)), 0.05, 0.09))
    bz = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz)), 0.05, 0.1))
    bars = g.math("MAXIMUM", bx, bz)
    c = g.mix(g.remap(g.noise(p, 3.0, 2.0), 0.3, 0.7, 0.0, 1.0), g.rgb(glass), g.rgb(tuple(min(1.0, x * 1.8 + 0.05) for x in glass)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 8.0, 2.0), 0.55, 0.7), 0.4), c, g.rgb((0.28, 0.27, 0.24)))
    c = g.mix(bars, c, g.rgb(bar))
    return g.finish(c, g.mixf(bars, 0.12, 0.6), g.bump(bars, 0.4, 0.004))


# ------------------------------------------------------------------------------------------------ Modern Age
def multi(name, base, cols=None, rough=0.45, var=0.08, edge=0.25):
    """Plain flat colours by label (plastic toys, a gnome, posters, flowers, towels): `base` on label 0 and cols
    {label: colour} over it, each mottled a little and lighter on its worn edges, darker in the crevices."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 20.0, 2.0), g.rgb(base), g.rgb(tuple(min(1.0, x * (1.0 + var)) for x in base)))
    for k, col in sorted((cols or {}).items()):
        c = g.mix(g.reg(k), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb(col), g.rgb(tuple(min(1.0, x * (1.0 + var)) for x in col))))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), edge), c, g.rgb((1.0, 1.0, 1.0)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.45), c, g.rgb((0.05, 0.05, 0.05)))
    return g.finish(c, rough)


def vehicle(name, paint, col5=(0.62, 0.52, 0.36), col7=(0.05, 0.05, 0.055), col8=(0.7, 0.08, 0.06), col9=(0.92, 0.92, 0.88),
            rough=0.42, grime=0.35):
    """Modern painted metal (vehicles, aircraft, crates, street furniture): the paint mottled a little, lighter on
    worn edges, grime in the recesses and streaking down (grime); label 5, 8, 9 more paints (a band, a red light or
    flash, white markings), 6 bright metal (chrome, steel fittings), 7 black (trim, rubber, grilles)."""
    g = new(name)
    p = g.obj()
    c = _paint_col(g, p, paint, 0.35)
    for k, col in ((5, col5), (8, col8), (9, col9), (7, col7)):
        c = g.mix(g.reg(k), c, _paint_col(g, p, col, 0.25))
    pt = g.geo("Pointiness")
    ch = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.5, 0.56), 0.8), g.rgb((0.6, 0.62, 0.66)), g.rgb((0.95, 0.96, 1.0)))
    ch = g.mix(g.math("MULTIPLY", _up(g, 0.3, 0.95), 0.4), ch, g.rgb((0.85, 0.88, 0.92)))
    c = g.mix(g.reg(6), c, ch)
    streak = g.remap(g.noise(g.scale_vec(p, (10.0, 10.0, 1.2)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    nb = g.math("SUBTRACT", 1.0, g.reg(6))
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", g.smooth(streak, 0.55, 0.8), grime), nb), c, g.rgb(tuple(x * 0.6 for x in paint)))
    rgh = g.mixf(g.reg(6), g.mixf(g.reg(7), rough, 0.8), 0.2)
    return g.finish(c, rgh, g.bump(g.noise(p, 60.0, 2.0), 0.08, 0.002))


def concrete(name="DK_Concrete", base=(0.66, 0.65, 0.61), board=0.15):
    """Poured concrete: mottled warm grey, faint formwork lines (every `board` up), tie holes, stains running down,
    pale worn arrises, dark in the joints; label 5 yellow paint, 6 white paint, 7 dark grime and tyre marks, 8 hazard
    stripes (yellow and black on the diagonal), 9 white stencils."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(tuple(x * 0.88 for x in base)), g.rgb(tuple(min(1, x * 1.08) for x in base)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 25.0, 3.0), 0.55, 0.7), 0.35), c, g.rgb(tuple(x * 0.78 for x in base)))
    fz = g.math("FRACT", g.math("DIVIDE", sep.outputs["Z"], board))
    line = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz)), 0.0, 0.05))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    side = g.math("SUBTRACT", 1.0, g.smooth(g.math("ABSOLUTE", nz.outputs["Z"]), 0.6, 0.85))
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", line, side), 0.3), c, g.rgb(tuple(x * 0.7 for x in base)))
    streak = g.remap(g.noise(g.scale_vec(p, (8.0, 8.0, 1.0)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    c = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", g.smooth(streak, 0.55, 0.8), side), 0.4), c, g.rgb((0.36, 0.34, 0.3)))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.51, 0.57), 0.35), c, g.rgb((0.85, 0.84, 0.8)))
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), c, g.rgb((0.22, 0.21, 0.2)))
    c = g.mix(g.reg(5), c, _paint_col(g, p, (0.92, 0.72, 0.12), 0.2))
    c = g.mix(g.reg(6), c, _paint_col(g, p, (0.92, 0.92, 0.9), 0.2))
    c = g.mix(g.math("MULTIPLY", g.reg(7), 0.75), c, g.rgb((0.12, 0.115, 0.11)))
    diag = g.math("FRACT", g.math("DIVIDE", g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), sep.outputs["Z"]), 0.16))
    hz = g.mix(g.smooth(diag, 0.47, 0.53), g.rgb((0.95, 0.74, 0.1)), g.rgb((0.06, 0.06, 0.06)))
    c = g.mix(g.reg(8), c, hz)
    c = g.mix(g.reg(9), c, g.rgb((0.94, 0.94, 0.92)))
    h = g.math("ADD", g.math("MULTIPLY", line, -0.4), g.math("MULTIPLY", g.noise(p, 50.0, 2.0), 0.3))
    return g.finish(c, 0.86, g.bump(h, 0.25, 0.004))


def hesco(name="DK_Hesco", fabric=(0.66, 0.58, 0.42), wire=(0.42, 0.43, 0.44), pitch=0.075):
    """A HESCO cell's tan geotextile seen through its welded wire mesh (dark lines every `pitch` across and up), dusty
    low down; label 5 = the bare galvanised corner coils."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    c = g.mix(g.remap(g.noise(p, 6.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(fabric), g.rgb(tuple(x * 0.85 for x in fabric)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 3.0, 2.0), 0.55, 0.7), 0.4), c, g.rgb(tuple(x * 0.72 for x in fabric)))
    fa = g.math("FRACT", g.math("DIVIDE", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), pitch))
    fz = g.math("FRACT", g.math("DIVIDE", sep.outputs["Z"], pitch))
    ga = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fa, g.math("SUBTRACT", 1.0, fa)), 0.03, 0.08))
    gz = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fz, g.math("SUBTRACT", 1.0, fz)), 0.03, 0.08))
    grid = g.math("MAXIMUM", ga, gz)
    c = g.mix(g.math("MULTIPLY", grid, 0.85), c, g.rgb(wire))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.5), c, g.rgb((0.25, 0.2, 0.14)))
    low = g.math("SUBTRACT", 1.0, g.smooth(sep.outputs["Z"], 0.0, 0.18))
    c = g.mix(g.math("MULTIPLY", low, 0.5), c, g.rgb((0.5, 0.4, 0.28)))
    c = g.mix(g.reg(5), c, g.rgb((0.58, 0.6, 0.62)))
    return g.finish(c, 0.85, g.bump(grid, 0.35, 0.003))


def chainlink(name="DK_Chainlink"):
    """Chain-link mesh on a solid panel: bright galvanised wires in diamonds over a dim, see-through-dark ground."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    u = g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), sep.outputs["Z"])
    v = g.math("SUBTRACT", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), sep.outputs["Z"])
    fu = g.math("FRACT", g.math("DIVIDE", u, 0.06))
    fv = g.math("FRACT", g.math("DIVIDE", v, 0.06))
    wu = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fu, g.math("SUBTRACT", 1.0, fu)), 0.06, 0.14))
    wv = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fv, g.math("SUBTRACT", 1.0, fv)), 0.06, 0.14))
    w = g.math("MAXIMUM", wu, wv)
    c = g.mix(w, g.rgb((0.2, 0.21, 0.2)), g.rgb((0.72, 0.74, 0.76)))
    return g.finish(c, g.mixf(w, 0.9, 0.35), g.bump(w, 0.4, 0.003))


def camo(name="DK_Camo"):
    """Camouflage netting: woodland blotches (olive, brown, dark green, black, a little tan) over a knobbly garnish."""
    g = new(name)
    p = g.obj()
    n1 = g.noise(p, 2.4, 3.0, 0.6)
    n2 = g.noise(g.add_vec(p, g.rgb((3.1, 7.7, 1.3))), 2.8, 3.0, 0.6)
    c = g.mix(g.smooth(n1, 0.45, 0.5), g.rgb((0.33, 0.35, 0.2)), g.rgb((0.36, 0.27, 0.16)))
    c = g.mix(g.smooth(n2, 0.56, 0.6), c, g.rgb((0.14, 0.2, 0.1)))
    c = g.mix(g.smooth(n1, 0.66, 0.7), c, g.rgb((0.06, 0.06, 0.05)))
    c = g.mix(g.smooth(n2, 0.33, 0.29), c, g.rgb((0.6, 0.55, 0.38)))
    leaf = g.voronoi(p, 45.0, 1.0, "F1", "Distance")
    c = g.mix(g.math("MULTIPLY", g.smooth(leaf, 0.05, 0.0), 0.5), c, g.rgb((0.04, 0.04, 0.03)))
    return g.finish(c, 0.95, g.bump(leaf, 0.6, 0.008))


def curtain(name, glass=(0.18, 0.32, 0.38), mullion=(0.6, 0.64, 0.66), spandrel=(0.2, 0.24, 0.26), lit=(1.0, 0.84, 0.52), pitch=0.16,
            floor=0.3, z0=0.42):
    """A glass curtain wall: panes of tinted glass catching the sky (lighter up the tower) in a grid of aluminium
    mullions every `pitch` along x + y and an opaque spandrel band at every floor (`floor` apart from z0); label 5 =
    a lit office (warm), 6 = bright metal."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    fa = g.math("FRACT", g.math("DIVIDE", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), pitch))
    fz = g.math("FRACT", g.math("DIVIDE", g.math("SUBTRACT", sep.outputs["Z"], z0), floor))
    mul = g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fa, g.math("SUBTRACT", 1.0, fa)), 0.03, 0.06))
    spd = g.math("MAXIMUM", g.smooth(fz, 0.2, 0.17), g.smooth(fz, 0.9, 0.93))
    sky = g.smooth(sep.outputs["Z"], 0.0, 7.0)
    gc = g.mix(sky, g.rgb(glass), g.rgb(tuple(min(1.0, x * 1.7 + 0.08) for x in glass)))
    gc = g.mix(g.math("MULTIPLY", g.smooth(g.noise(g.scale_vec(p, (1.0, 1.0, 0.3)), 2.0, 2.0), 0.5, 0.7), 0.5), gc,
               g.rgb(tuple(min(1.0, x * 2.2 + 0.12) for x in glass)))
    c = g.mix(g.reg(5), gc, g.mix(g.noise(p, 9.0, 2.0), g.rgb(lit), g.rgb(tuple(x * 0.85 for x in lit))))
    c = g.mix(spd, c, g.rgb(spandrel))
    c = g.mix(mul, c, g.rgb(mullion))
    nz = g.node("ShaderNodeSeparateXYZ")
    g.put(nz.inputs[0], g.geo("Normal"))
    top = g.smooth(nz.outputs["Z"], 0.7, 0.9)
    c = g.mix(top, c, g.rgb((0.42, 0.43, 0.44)))
    c = g.mix(g.reg(6), c, g.rgb((0.8, 0.82, 0.84)))
    rough = g.mixf(g.math("MAXIMUM", g.math("MAXIMUM", mul, spd), top), 0.12, 0.6)
    return g.finish(c, rough, g.bump(g.math("MAXIMUM", mul, spd), 0.3, 0.003))


def siding(name, col, trim=(0.94, 0.93, 0.9), found=(0.5, 0.48, 0.45), shutter=(0.08, 0.1, 0.1), door=(0.62, 0.08, 0.07), lap=0.045):
    """Clapboard siding in `col`: lapped boards (a shadow line under each, every `lap` up), sun-faded in patches,
    grime at the foot; label 5 white trim paint, 6 the grey foundation, 7 the shutters' paint, 8 the front door's."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    fz = g.math("FRACT", g.math("DIVIDE", sep.outputs["Z"], lap))
    sh = g.smooth(fz, 0.16, 0.0)
    c = g.mix(g.remap(g.noise(p, 3.0, 3.0), 0.3, 0.7, 0.0, 1.0), g.rgb(col), g.rgb(tuple(min(1.0, x * 1.08) for x in col)))
    c = g.mix(g.math("MULTIPLY", sh, 0.55), c, g.rgb(tuple(x * 0.62 for x in col)))
    c = g.mix(g.reg(5), c, _paint_col(g, p, trim, 0.2))
    c = g.mix(g.reg(6), c, g.mix(g.noise(p, 20.0, 2.0), g.rgb(found), g.rgb(tuple(x * 0.85 for x in found))))
    c = g.mix(g.reg(7), c, _paint_col(g, p, shutter, 0.3))
    c = g.mix(g.reg(8), c, _paint_col(g, p, door, 0.3))
    pt = g.geo("Pointiness")
    c = g.mix(g.math("MULTIPLY", g.smooth(pt, 0.48, 0.43), 0.45), c, g.rgb((0.12, 0.12, 0.12)))
    low = g.math("SUBTRACT", 1.0, g.smooth(sep.outputs["Z"], 0.0, 0.25))
    c = g.mix(g.math("MULTIPLY", low, 0.3), c, g.rgb((0.35, 0.3, 0.24)))
    return g.finish(c, 0.7, g.bump(g.math("MULTIPLY", sh, -1.0), 0.35, 0.004))


def shingles(name, col=(0.26, 0.27, 0.29), course=0.05, tab=0.11, ridge=(0.12, 0.12, 0.13)):
    """Asphalt shingles: courses of tabs (each its own shade, granular), dark gaps under every course and between tabs;
    label 7 the darker ridge cap, 5 white fascia paint."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], p)
    row = g.math("FLOOR", g.math("DIVIDE", sep.outputs["Z"], course))
    fz = g.math("SUBTRACT", g.math("DIVIDE", sep.outputs["Z"], course), row)
    run = g.math("ADD", g.math("ADD", sep.outputs["X"], sep.outputs["Y"]), g.math("MULTIPLY", g.math("MODULO", g.math("ADD", row, 1000.0), 2.0), tab * 0.5))
    colm = g.math("FLOOR", g.math("DIVIDE", run, tab))
    fx = g.math("SUBTRACT", g.math("DIVIDE", run, tab), colm)
    gap = g.math("MAXIMUM", g.smooth(fz, 0.1, 0.0), g.math("SUBTRACT", 1.0, g.smooth(g.math("MINIMUM", fx, g.math("SUBTRACT", 1.0, fx)), 0.01, 0.04)))
    rnd = _cell_rand(g, row, colm)
    c = g.mix(rnd, g.rgb(tuple(x * 0.82 for x in col)), g.rgb(tuple(min(1.0, x * 1.2) for x in col)))
    c = g.mix(g.math("MULTIPLY", g.smooth(g.noise(p, 60.0, 2.0), 0.5, 0.7), 0.4), c, g.rgb(tuple(min(1.0, x * 1.4) for x in col)))
    c = g.mix(g.math("MULTIPLY", gap, 0.8), c, g.rgb(tuple(x * 0.35 for x in col)))
    c = g.mix(g.reg(7), c, g.rgb(ridge))
    c = g.mix(g.reg(5), c, g.rgb((0.94, 0.93, 0.9)))
    return g.finish(c, 0.88, g.bump(g.math("ADD", g.math("MULTIPLY", gap, -0.8), g.math("MULTIPLY", fz, 0.3)), 0.35, 0.004))


def radome(name="DK_Radome", base=(0.9, 0.9, 0.87)):
    """White fibreglass (a radome's panels, a dish): faint panel seams (voronoi edges), grime streaking down."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.noise(p, 4.0, 2.0), g.rgb(base), g.rgb(tuple(x * 0.94 for x in base)))
    seam = g.smooth(g.voronoi(p, 6.0, 0.6, "DISTANCE_TO_EDGE", "Distance"), 0.02, 0.0)
    c = g.mix(g.math("MULTIPLY", seam, 0.35), c, g.rgb(tuple(x * 0.7 for x in base)))
    streak = g.remap(g.noise(g.scale_vec(p, (8.0, 8.0, 1.0)), 1.0, 2.0), 0.3, 0.7, 0.0, 1.0)
    c = g.mix(g.math("MULTIPLY", g.smooth(streak, 0.6, 0.85), 0.25), c, g.rgb((0.5, 0.48, 0.42)))
    c = g.mix(g.reg(7), c, g.rgb((0.2, 0.21, 0.22)))
    return g.finish(c, 0.5, g.bump(seam, 0.2, 0.003))
