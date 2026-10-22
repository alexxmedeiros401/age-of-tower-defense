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

