"""Hard-surface materials for the HQ robots (Cycles, baked into albedo / normal / roughness like mats.py).

Painted armour plates wear through to bare metal on their edges (the Bevel node finds the edges), collect grime in
their creases (the Ambient Occlusion node), and carry fine scratches; painted regions (sculpt labels) take accent
colours such as hazard stripes. Frames are dark gunmetal with bright worn edges. Glowing parts are not baked: they ship
as emissive meshes (see robot_build.GLOW).
"""
import bpy
from mats import new, lin


def _edges(g, radius=0.006, lo=0.06, hi=0.22):
    """0 on flat areas, 1 on sharp convex/concave edges (bevel-normal vs true-normal difference)."""
    bev = g.node("ShaderNodeBevel")
    bev.samples = 8
    bev.inputs["Radius"].default_value = radius
    dot = g.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    g.put(dot.inputs[0], bev.outputs["Normal"])
    g.put(dot.inputs[1], g.geo("Normal"))
    d = g.math("SUBTRACT", 1.0, dot.outputs["Value"])
    return g.smooth(d, lo * 0.1, hi * 0.1)


def _cavity(g, dist=0.05):
    ao = g.node("ShaderNodeAmbientOcclusion", samples=8, only_local=True)
    ao.inputs["Distance"].default_value = dist
    return g.math("SUBTRACT", 1.0, ao.outputs["AO"])


def armor(name, base=(0.92, 0.92, 0.89), metal=(0.74, 0.76, 0.8), grime=(0.3, 0.27, 0.24), labels=(), wear=1.0,
          rough=0.32, scale=1.0, seams=()):
    """Painted armour. labels: [(label, colour, roughness)] painted regions (stripes, numbers, accent panels);
    seams: labels that are cut in as grooves (panel lines), dark and sunken in the normal map."""
    g = new(name)
    p = g.obj()
    var = g.noise(p, 6.0 / scale, 3.0, 0.55)
    c = g.mix(g.remap(var, 0.3, 0.7, 0.0, 0.08), g.rgb(base), g.rgb(tuple(x * 0.86 for x in base)))
    rgh = rough
    for lab, col, rg in labels:
        c = g.mix(g.reg(lab), c, g.rgb(col))
        rgh = g.mixf(g.reg(lab), rgh, rg)
    # worn edges: paint chipped back to bare metal, broken up by noise
    e = _edges(g, 0.008 * scale)
    chip = g.smooth(g.noise(p, 26.0 / scale, 4.0, 0.62), 0.42, 0.58)
    worn = g.math("MULTIPLY", g.math("MULTIPLY", e, g.math("ADD", 0.35, g.math("MULTIPLY", chip, 0.65))), wear)
    c = g.mix(worn, c, g.rgb(metal))
    rgh = g.mixf(worn, rgh, 0.22)
    # small paint chips away from the edges
    spots = g.math("MULTIPLY", g.smooth(g.noise(p, 55.0 / scale, 3.0, 0.6), 0.66, 0.7), 0.85 * wear)
    c = g.mix(spots, c, g.rgb(metal))
    # grime in the creases and streaking down
    cav = g.smooth(_cavity(g, 0.06 * scale), 0.15, 0.7)
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], g.geo("Normal"))
    down = g.smooth(sep.outputs["Z"], 0.2, -0.8)
    streak = g.math("MULTIPLY", g.smooth(g.noise(g.scale_vec(p, (14.0, 14.0, 2.5)), 1.0, 3.0, 0.5), 0.5, 0.75), 0.35)
    gm = g.math("MINIMUM", 1.0, g.math("ADD", g.math("MULTIPLY", cav, 0.85), g.math("MULTIPLY", g.math("ADD", down, streak), 0.25)))
    c = g.mix(g.math("MULTIPLY", gm, 0.75), c, g.rgb(grime))
    rgh = g.mixf(gm, rgh, 0.7)
    # fine scratches
    scr = g.smooth(g.wave(g.scale_vec(p, (1.0, 3.0, 1.0)), 38.0 / scale, 9.0, 3.0), 0.93, 0.99)
    scr = g.math("MULTIPLY", scr, g.smooth(g.noise(p, 9.0, 2.0), 0.55, 0.65))
    c = g.mix(g.math("MULTIPLY", scr, 0.5 * wear), c, g.rgb(metal))
    h = g.math("ADD", g.math("MULTIPLY", g.noise(p, 90.0 / scale, 2.0, 0.5), 0.25), g.math("MULTIPLY", scr, -0.4))
    for lab in seams:
        h = g.math("SUBTRACT", h, g.math("MULTIPLY", g.reg(lab), 1.6))
    return g.finish(c, rgh, g.bump(h, 0.12, 0.002))


def gunmetal(name, base=(0.25, 0.27, 0.31), edge=(0.62, 0.65, 0.7), labels=(), rough=0.42, scale=1.0, seams=()):
    """Frames, joints, pistons housings: dark blued steel, bright where edges wear, darker in creases."""
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 9.0 / scale, 3.0, 0.6), 0.3, 0.7, 0.0, 0.12), g.rgb(base), g.rgb(tuple(x * 0.75 for x in base)))
    rgh = rough
    for lab, col, rg in labels:
        c = g.mix(g.reg(lab), c, g.rgb(col))
        rgh = g.mixf(g.reg(lab), rgh, rg)
    e = _edges(g, 0.007 * scale)
    c = g.mix(g.math("MULTIPLY", e, 0.8), c, g.rgb(edge))
    rgh = g.mixf(e, rgh, 0.25)
    cav = g.smooth(_cavity(g, 0.05 * scale), 0.2, 0.75)
    c = g.mix(g.math("MULTIPLY", cav, 0.6), c, g.rgb((0.08, 0.08, 0.09)))
    h = g.noise(p, 70.0 / scale, 2.0, 0.55)
    for lab in seams:
        h = g.math("SUBTRACT", h, g.math("MULTIPLY", g.reg(lab), 1.6))
    return g.finish(c, rgh, g.bump(h, 0.1, 0.002))


def chrome(name, base=(0.82, 0.85, 0.9)):
    """Piston rods, rotor hubs: bright polished steel (baked as light grey with low roughness)."""
    g = new(name)
    p = g.obj()
    sep = g.node("ShaderNodeSeparateXYZ")
    g.put(sep.inputs[0], g.geo("Normal"))
    c = g.mix(g.smooth(sep.outputs["Z"], -0.4, 0.8), g.rgb(tuple(x * 0.62 for x in base)), g.rgb(base))
    return g.finish(c, 0.16, g.bump(g.noise(p, 120.0, 1.0), 0.04, 0.001))


def rubber(name, base=(0.1, 0.1, 0.11)):
    g = new(name)
    p = g.obj()
    c = g.mix(g.remap(g.noise(p, 30.0, 2.0), 0.3, 0.7, 0.0, 0.25), g.rgb(base), g.rgb((0.2, 0.19, 0.18)))
    return g.finish(c, 0.82, g.bump(g.noise(p, 160.0, 1.0), 0.15, 0.002))


def lens_socket(name, base=(0.06, 0.06, 0.07)):
    """The dark ring and glass round a glowing eye (the glow itself is a separate mesh)."""
    g = new(name)
    return g.finish(g.rgb(base), 0.12)


def glow(name, col, strength=2.0):
    """Preview stand-in for parts that ship as glow meshes (eyes, cores, thrusters)."""
    g = new(name)
    return g.finish(g.rgb(col), 0.2, emit=g.rgb(col), emit_strength=strength)
