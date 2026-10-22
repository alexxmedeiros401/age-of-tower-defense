"""HQ map kits: sculpt every prop of a Stone Age theme, bake them all into one texture atlas, export one GLB with one mesh
per prop (named as game.gd DECOR_V2 expects: Pine_A, Rock_C, Mammoth, Cave, ...), each at the origin, ground at y = 0.

    python3 decor_build.py -- --theme meadow|snow|volcano|...|olive|coast|acropolis|classical_city|farmland|darkwood|castle|medieval_city
                              --out DIR [--stage sculpt|game|export|all] [--fine]
                              [--tex 2048] [--ao 24] [--only Pine_A,Rock_A] [--shots DIR]

Props are sculpted side by side (so their ambient occlusion doesn't mix), baked per part, then split and moved back to
the origin. Grass tufts and flower clumps are direct geometry coloured from a swatch strip on the right of the atlas.
Glowing parts (the volcano's lava) stay emissive (their own material slot, not baked).
"""
import sys, os, time, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

import sdf, mats, prep
import lowpoly as lp
import bake as bk
import decor_props as DP
import decor_mats as DM

THEME = arg("--theme", "meadow")
OUT = arg("--out", "out_kit_" + THEME)
STAGE = arg("--stage", "all")
TEX = int(arg("--tex", "2048"))
AO_SPP = int(arg("--ao", "24"))
ONLY = arg("--only").split(",") if arg("--only") else None
DP.FINE[0] = "--fine" in ARGS
os.makedirs(OUT, exist_ok=True)
HI = os.path.join(OUT, "kit_hi.blend")
GAME = os.path.join(OUT, "kit_game.blend")
GLB = arg("--glb", {"meadow": "stone_decor", "snow": "stone_decor_snow", "volcano": "stone_decor_volcano",
                   "portal": "time_portal", "delta": "bronze_decor_delta", "desert": "bronze_decor_desert",
                   "canyon": "bronze_decor_canyon", "city": "bronze_city", "highland": "iron_decor_highland",
                   "forge": "iron_decor_forge", "bog": "iron_decor_bog", "iron_city": "iron_city",
                   "olive": "classical_decor_olive", "coast": "classical_decor_coast", "acropolis": "classical_decor_acropolis",
                   "classical_city": "classical_city", "farmland": "medieval_decor_farmland",
                   "darkwood": "medieval_decor_darkwood", "castle": "medieval_decor_castle", "medieval_city": "medieval_city"}[THEME])
BRONZE = THEME in ("delta", "desert", "canyon", "city")
IRON = THEME in ("highland", "forge", "bog", "iron_city")
CLASSICAL = THEME in ("olive", "coast", "acropolis", "classical_city")
MEDIEVAL = THEME in ("farmland", "darkwood", "castle", "medieval_city")
G0, G1, S0 = 0.05, 0.6, 0.7          # swatch strip: grass gradient rows, then flat colours (as in build_game.base_stage)
SWATCHES = [(0.97, 0.96, 0.92), (1.0, 0.86, 0.3), (0.72, 0.56, 0.96), (0.96, 0.52, 0.76), (0.3, 0.5, 0.18)]
GRASS = {"meadow": ((0.17, 0.34, 0.09), (0.6, 0.78, 0.3)), "snow": ((0.3, 0.27, 0.16), (0.62, 0.56, 0.36)),
         "volcano": ((0.16, 0.13, 0.1), (0.5, 0.42, 0.3)), "delta": ((0.19, 0.4, 0.1), (0.56, 0.75, 0.27)),
         "desert": ((0.46, 0.38, 0.19), (0.86, 0.75, 0.46)), "canyon": ((0.38, 0.29, 0.15), (0.76, 0.62, 0.37)),
         "highland": ((0.2, 0.3, 0.1), (0.56, 0.62, 0.28)), "forge": ((0.2, 0.16, 0.11), (0.5, 0.42, 0.27)),
         "bog": ((0.24, 0.3, 0.11), (0.66, 0.6, 0.3)), "olive": ((0.36, 0.34, 0.14), (0.8, 0.7, 0.36)),
         "coast": ((0.3, 0.34, 0.16), (0.72, 0.7, 0.42)), "acropolis": ((0.34, 0.34, 0.16), (0.74, 0.68, 0.36)),
         "farmland": ((0.16, 0.34, 0.08), (0.52, 0.72, 0.26)), "darkwood": ((0.1, 0.2, 0.07), (0.34, 0.46, 0.18)),
         "castle": ((0.2, 0.32, 0.1), (0.56, 0.66, 0.3))
         }.get(THEME, ((0.17, 0.34, 0.09), (0.6, 0.78, 0.3)))


def log(*a):
    print("[kit]", *a, flush=True)


def materials():
    th = THEME
    dark = mats.new("DK_Dark")
    dark.finish(dark.rgb((0.03, 0.025, 0.022)), 0.95)
    return {
        "needles": DM.needles("DK_Needles", th), "bark": DM.bark("DK_Bark", th), "charred": DM.bark("DK_Charred", th, charred=True),
        "leaves": DM.leaves("DK_Leaves"), "leaves_berry": DM.leaves("DK_LeavesBerry", berries=(0.85, 0.12, 0.15)),
        "rock": DM.rock("DK_Rock", th), "wood_end": DM.wood_end("DK_WoodEnd", th, charred=(th == "volcano")),
        "bone": DM.old_bone("DK_Bone", th), "hide": DM.hide("DK_Hide", th), "snow": DM.snowpack("DK_Snow"),
        "ice": DM.ice("DK_Ice"), "obsidian": DM.obsidian("DK_Obsidian"), "ochre": DM.ochre("DK_Ochre"),
        "turf": DM.turf("DK_Turf", th), "dark": dark.mat,
        "glow_lava": DM.glow("DK_GlowLava", (1.0, 0.45, 0.08), 2.2),
        "glow_cyan": DM.glow("DK_GlowCyan", (0.25, 0.85, 1.0), 2.2), "glow_magenta": DM.glow("DK_GlowMagenta", (1.0, 0.2, 0.85), 2.2),
        "portal_metal": __import__("robot_mats").gunmetal(name="DK_PortalMetal", base=(0.2, 0.22, 0.28), edge=(0.6, 0.66, 0.78),
                                                           labels=[(2, (0.1, 0.1, 0.12), 0.6)], seams=[2], scale=2.0),
        "portal_armor": __import__("robot_mats").armor(name="DK_PortalArmor", labels=[(1, (1.0, 0.47, 0.08), 0.35),
                                                       (2, (0.2, 0.2, 0.22), 0.6), (3, (0.08, 0.08, 0.09), 0.4)], seams=[2], scale=2.0),
    } if not (BRONZE or IRON or CLASSICAL or MEDIEVAL) else (bronze_materials(dark.mat) if BRONZE else
                                                             (iron_materials(dark.mat) if IRON else
                                                              (classical_materials(dark.mat) if CLASSICAL else medieval_materials(dark.mat))))


def bronze_materials(dark):
    """The Bronze Age kits' materials (v0.9.28): rocks, turf and dead wood by theme, plus everything the delta, desert,
    canyon and city props are made of."""
    th = THEME
    rock_m = {"delta": lambda: DM.rock("DK_Rock", "delta"),
              "desert": lambda: DM.sandstone("DK_Rock", base=(0.8, 0.64, 0.44), dark=(0.62, 0.48, 0.32), bedding=0.22),
              "canyon": lambda: DM.redrock("DK_Rock"), "city": lambda: DM.rock("DK_Rock", "delta")}[th]()
    return {
        "rock": rock_m, "turf": DM.bronze_turf("DK_Turf", th if th != "city" else "delta"), "dark": dark,
        "leaves": DM.leaves("DK_Leaves"), "leaves_berry": DM.leaves("DK_LeavesBerry", berries=(0.92, 0.36, 0.58)),
        "charred": DM.driftwood("DK_DeadWood"), "wood_end": DM.timber_log("DK_WoodEnd"),
        "palm_bark": DM.palm_bark("DK_PalmBark"), "frond": DM.frond("DK_Frond"), "frond_rib": DM.frond_rib("DK_FrondRib"),
        "dates": DM.dates("DK_Dates"), "papyrus": DM.papyrus("DK_Papyrus"), "papyrus_head": DM.papyrus_head("DK_PapyrusHead"),
        "reed_leaf": DM.papyrus("DK_ReedLeaf", base=(0.3, 0.44, 0.15), hi=(0.54, 0.6, 0.26)), "cattail": DM.cattail("DK_Cattail"),
        "mud": DM.mud("DK_Mud"), "sand": DM.sand("DK_Sand"), "sandstone": DM.sandstone("DK_Sandstone"),
        "ashlar": DM.ashlar("DK_Ashlar"), "malachite": DM.malachite("DK_Malachite"), "mud_plaster": DM.mud_plaster("DK_MudPlaster"),
        "rail": DM.rail("DK_Rail"), "acacia_bark": DM.bark("DK_AcaciaBark", "desert"),
        "acacia_leaves": DM.leaves("DK_AcaciaLeaves", base=(0.2, 0.3, 0.1), hi=(0.46, 0.54, 0.2)),
        "scrub": DM.leaves("DK_Scrub", base=(0.3, 0.34, 0.18), hi=(0.56, 0.56, 0.34)),
        "mudbrick": mats.mudbrick("DK_Mudbrick"), "siege": mats.siege("DK_Timber"), "reed": mats.reed("DK_Reed"),
        "terracotta": mats.terracotta("DK_Terracotta"), "linen": mats.linen("DK_Linen", base=(0.8, 0.7, 0.52)), "hide": DM.hide("DK_Hide", "desert"),
        "charcoal": mats.charcoal("DK_Charcoal"), "granite": mats.granite("DK_Granite"), "gold": mats.gold("DK_Gold"),
        "copper": mats.bronze("DK_Copper", base=(0.7, 0.33, 0.16), hi=(0.98, 0.66, 0.44), dark=(0.3, 0.12, 0.06), patina=(0.24, 0.6, 0.48)),
        "bronze": mats.bronze("DK_Bronze"), "wool": mats.wool("DK_Wool"),
        "glow_turq": DM.glow("DK_GlowTurq", (0.3, 1.0, 0.78), 2.2), "glow_fire": DM.glow("DK_GlowFire", (1.0, 0.55, 0.15), 2.2),
        # v0.9.29: the desert's cacti
        "saguaro": DM.cactus("DK_Saguaro"),
        "barrel_cactus": DM.cactus("DK_BarrelCactus", base=(0.22, 0.38, 0.17), hi=(0.78, 0.58, 0.26), groove=(0.06, 0.13, 0.05),
                                   spine=(0.86, 0.36, 0.16), dots=30.0, dot_r=0.3),
        "opuntia": DM.opuntia("DK_Opuntia"), "agave": DM.agave("DK_Agave"),
        "agave_spine": DM.flat("DK_AgaveSpine", (0.22, 0.13, 0.08), 0.5),
        "flower_cream": DM.flat("DK_FlowerCream", (0.95, 0.92, 0.8), 0.6, hi=(1.0, 0.98, 0.92)),
        "flower_gold": DM.flat("DK_FlowerGold", (0.96, 0.76, 0.2), 0.6),
        "flower_yellow": DM.flat("DK_FlowerYellow", (0.98, 0.84, 0.26), 0.6, hi=(1.0, 0.95, 0.6)),
        "flower_orange": DM.flat("DK_FlowerOrange", (0.98, 0.56, 0.16), 0.6, hi=(1.0, 0.8, 0.4)),
        "cactus_fruit": DM.flat("DK_CactusFruit", (0.64, 0.08, 0.3), 0.4, hi=(0.86, 0.3, 0.46)),
    }
def iron_materials(dark):
    """The Iron Age kits' materials: moorland, forge and bog stone, turf and wood, and everything the highland,
    forge, bog and hill-fort props are made of."""
    th = THEME
    rock_m = {"forge": lambda: DM.ironstone("DK_Rock")}.get(th, lambda: DM.rock("DK_Rock", "meadow"))()
    turf_m = {"forge": lambda: DM.turf("DK_Turf", "volcano"), "bog": lambda: DM.sphagnum("DK_Turf")}.get(th, lambda: mats.ground("DK_Turf"))()
    return {
        "rock": rock_m, "turf": turf_m, "dark": dark,
        "needles": DM.needles("DK_Needles", "meadow"), "scots_bark": DM.scots_bark("DK_ScotsBark"),
        "birch_bark": DM.birch_bark("DK_BirchBark"),
        "birch_leaves": DM.leaves("DK_BirchLeaves", base=(0.28, 0.42, 0.12), hi=(0.6, 0.7, 0.25)),
        "heather": DM.heather("DK_Heather"),
        "gorse": DM.leaves("DK_Gorse", base=(0.12, 0.24, 0.08), hi=(0.28, 0.4, 0.12), berries=(1.0, 0.8, 0.12)),
        "bracken": DM.frond("DK_Bracken", base=(0.26, 0.4, 0.11), hi=(0.5, 0.6, 0.2), dry=(0.66, 0.38, 0.14)),
        "wood_end": DM.wood_end("DK_WoodEnd", "volcano" if th == "forge" else "meadow", charred=(th == "forge")),
        "charred": DM.bark("DK_Charred", "volcano", charred=True),
        "reed_leaf": DM.papyrus("DK_ReedLeaf", base=(0.3, 0.44, 0.15), hi=(0.54, 0.6, 0.26)), "cattail": DM.cattail("DK_Cattail"),
        "mud": DM.mud("DK_Mud"), "rushes": DM.papyrus("DK_Rushes", base=(0.15, 0.29, 0.09), hi=(0.32, 0.46, 0.15)),
        "drystone": DM.drystone("DK_DryStone"), "thatch": DM.thatch("DK_Thatch"),
        "daub": DM.mud_plaster("DK_Daub", base=(0.74, 0.64, 0.48)),
        "timber": mats.siege("DK_Timber", wood=(0.54, 0.38, 0.24), wood2=(0.38, 0.26, 0.16), blue=(0.16, 0.3, 0.64), metal="iron"),
        "logs": DM.timber_log("DK_Logs"), "bark_wood": mats.bark_wood("DK_BarkWood"),
        "slag": DM.slag("DK_Slag"), "iron_ore": DM.iron_ore("DK_IronOre"),
        "earth": DM.turf("DK_Earth", "volcano") if th == "forge" else DM.mud_plaster("DK_Earth", base=(0.44, 0.34, 0.24)),
        "charcoal": mats.charcoal("DK_Charcoal"), "furnace_clay": DM.furnace_clay("DK_FurnaceClay"),
        "leather": mats.leather("DK_Leather", base=(0.4, 0.25, 0.13)), "basket": mats.basket(), "iron": mats.iron("DK_Iron"),
        "dark_water": DM.flat("DK_DarkWater", (0.05, 0.055, 0.04), 0.1, var=0.25),
        "willow_bark": mats.bark_wood("DK_WillowBark", bark=(0.4, 0.37, 0.31)),
        "willow_leaves": DM.leaves("DK_WillowLeaves", base=(0.3, 0.38, 0.2), hi=(0.6, 0.66, 0.44)),
        "alder_bark": mats.bark_wood("DK_AlderBark", bark=(0.25, 0.23, 0.21)),
        "alder_leaves": DM.leaves("DK_AlderLeaves", base=(0.1, 0.24, 0.08), hi=(0.28, 0.46, 0.14)),
        "deadwood": DM.driftwood("DK_DeadWood"),
        "bog_grass": DM.papyrus("DK_BogGrass", base=(0.46, 0.42, 0.2), hi=(0.68, 0.62, 0.32)),
        "cotton": DM.flat("DK_Cotton", (0.95, 0.95, 0.92), 0.85, hi=(1.0, 1.0, 1.0)),
        "sphagnum": DM.sphagnum("DK_Sphagnum"), "bog_oak": DM.bog_oak("DK_BogOak"), "peat": DM.peat("DK_Peat"),
        "idol_wood": mats.siege("DK_IdolWood", wood=(0.44, 0.33, 0.23), wood2=(0.3, 0.21, 0.14), metal="iron"),
        "quartz": DM.flat("DK_Quartz", (0.94, 0.94, 0.9), 0.3, hi=(1.0, 1.0, 1.0)),
        "pottery": mats.terracotta("DK_Pottery", base=(0.46, 0.32, 0.22)),
        "banner": mats.wool("DK_Banner", base=(0.16, 0.3, 0.64), border=(0.94, 0.92, 0.86), stripe=(0.1, 0.12, 0.2)),
        "glow_fire": DM.glow("DK_GlowFire", (1.0, 0.55, 0.15), 2.2),
    }


def classical_materials(dark):
    """The Classical Age kits' materials: pale limestone and marble, dry golden turf, olive, cypress, umbrella pine and
    maquis, whitewash and terracotta, cut stone, bronze, and everything the olive hills, the coast, the acropolis and
    the walled city are made of."""
    th = THEME
    turf_top = {"olive": ((0.6, 0.52, 0.26), (0.74, 0.64, 0.34)), "coast": ((0.62, 0.58, 0.36), (0.78, 0.72, 0.48)),
                "acropolis": ((0.56, 0.52, 0.3), (0.7, 0.64, 0.38))}.get(th, ((0.6, 0.52, 0.26), (0.74, 0.64, 0.34)))
    return {
        "dark": dark, "turf": DM.dry_turf("DK_Turf", turf_top),
        "limestone": DM.limestone_rock("DK_Limestone"), "rock": DM.limestone_rock("DK_Rock"),
        "marble": mats.marble("DK_Marble"),
        "marble_fine": mats.marble("DK_MarbleFine", vein_scale=2.6),     # (the statues: finer veins at their size)
        "ashlar": DM.ashlar("DK_Ashlar", base=(0.86, 0.8, 0.68), joint=(0.5, 0.45, 0.36), course=0.3, block=0.6,
                            grime7=(0.52, 0.48, 0.4)),
        "flags": mats.flagstone("DK_Flags", base=(0.7, 0.66, 0.58), alt=(0.78, 0.72, 0.6)),
        "olive_bark": mats.bark_wood("DK_OliveBark", bark=(0.4, 0.38, 0.33), wood=(0.74, 0.62, 0.44)),
        "olive_leaves": DM.leaves("DK_OliveLeaves", base=(0.33, 0.39, 0.27), hi=(0.72, 0.78, 0.64)),     # (silvery grey-green)
        "olive_fruit": DM.flat("DK_OliveFruit", (0.12, 0.13, 0.06), 0.35, hi=(0.3, 0.3, 0.14)),
        "cypress": DM.leaves("DK_Cypress", base=(0.05, 0.14, 0.06), hi=(0.2, 0.34, 0.14)),
        "pine_bark": DM.scots_bark("DK_PineBark"), "needles": DM.needles("DK_Needles", "meadow"),
        "pine_crown": DM.leaves("DK_PineCrown", base=(0.09, 0.19, 0.07), hi=(0.3, 0.42, 0.16)),      # (the umbrella pines' dark crowns)
        "maquis": DM.leaves("DK_Maquis", base=(0.13, 0.22, 0.08), hi=(0.36, 0.44, 0.2)),
        "herb": DM.leaves("DK_Herb", base=(0.3, 0.35, 0.24), hi=(0.6, 0.64, 0.46)),
        "flower_purple": DM.flat("DK_FlowerPurple", (0.6, 0.42, 0.86), 0.6, hi=(0.8, 0.66, 0.98)),
        "flower_pink": DM.flat("DK_FlowerPink", (0.94, 0.5, 0.72), 0.6, hi=(1.0, 0.76, 0.86)),
        "pottery": mats.terracotta("DK_Pottery"), "tiles": mats.terracotta("DK_Tiles", base=(0.74, 0.34, 0.18)),
        "plaster": mats.plaster("DK_Plaster"),
        "timber": mats.siege("DK_Timber", wood=(0.52, 0.37, 0.24), wood2=(0.38, 0.26, 0.16), red=(0.66, 0.14, 0.08),
                             blue=(0.14, 0.32, 0.6), metal="bronze"),
        "boat": mats.siege("DK_Boat", wood=(0.3, 0.22, 0.15), wood2=(0.22, 0.15, 0.1), red=(0.92, 0.9, 0.82),
                           blue=(0.12, 0.3, 0.6), metal="bronze"),
        "basket": mats.basket(), "bronze": mats.bronze("DK_Bronze"),
        "sailcloth": mats.linen("DK_Sailcloth", base=(0.86, 0.8, 0.66)),
        "rope": DM.flat("DK_Rope", (0.62, 0.52, 0.36), 0.8, hi=(0.76, 0.66, 0.48)),
        "banner": mats.wool("DK_Banner", base=(0.64, 0.08, 0.06), border=(0.98, 0.78, 0.26), stripe=(0.42, 0.3, 0.16)),
        "glow_fire": DM.glow("DK_GlowFire", (1.0, 0.55, 0.15), 2.2),
    }


def medieval_materials(dark):
    """The Medieval Age kits' materials: green meadow turf and grey stone, oak, spruce and hawthorn, thatch, limewashed
    daub and dark oak beams, boards and dry-stone, hay and wattle, grey castle ashlar under slate, the besiegers' striped
    canvas, hides and iron, blue and gold banners."""
    return {
        "dark": dark, "turf": DM.turf("DK_Turf", "meadow"), "rock": DM.rock("DK_Rock", "meadow"),
        "wood_end": DM.wood_end("DK_WoodEnd", "meadow"), "charred": DM.bark("DK_Charred", "volcano", charred=True),
        "oak_bark": mats.bark_wood("DK_OakBark", bark=(0.3, 0.27, 0.22), wood=(0.72, 0.58, 0.4)),
        "oak_leaves": DM.leaves("DK_OakLeaves", base=(0.16, 0.34, 0.1), hi=(0.44, 0.62, 0.2)),
        "dark_leaves": DM.leaves("DK_DarkLeaves", base=(0.08, 0.2, 0.07), hi=(0.24, 0.38, 0.13)),
        "hedge": DM.leaves("DK_Hedge", base=(0.12, 0.3, 0.09), hi=(0.36, 0.56, 0.18)),
        "blossom": DM.flat("DK_Blossom", (0.97, 0.95, 0.9), 0.6, hi=(1.0, 0.86, 0.9)),
        "needles": DM.needles("DK_Needles", "meadow"), "spruce_bark": DM.bark("DK_SpruceBark", "meadow"),
        "deadwood": DM.driftwood("DK_DeadWood"),
        "fern": DM.frond("DK_Fern", base=(0.14, 0.32, 0.08), hi=(0.36, 0.56, 0.16), dry=(0.56, 0.4, 0.16)),
        "toadstool": mats.terracotta("DK_Toadstool", base=(0.78, 0.1, 0.06), paint=(0.97, 0.95, 0.9)),
        "mushroom": DM.flat("DK_Mushroom", (0.92, 0.88, 0.78), 0.7, hi=(1.0, 0.97, 0.9)),
        "thatch": DM.thatch("DK_Thatch"), "daub": DM.mud_plaster("DK_Daub", base=(0.88, 0.82, 0.68)),
        "timber": mats.siege("DK_Timber", wood=(0.4, 0.28, 0.18), wood2=(0.28, 0.19, 0.12), red=(0.62, 0.12, 0.08),
                             blue=(0.14, 0.28, 0.58), metal="iron"),
        "boards": mats.siege("DK_Boards", wood=(0.5, 0.36, 0.24), wood2=(0.36, 0.25, 0.16), red=(0.12, 0.08, 0.05), metal="iron"),
        "sails": mats.siege("DK_Sails", wood=(0.46, 0.32, 0.2), wood2=(0.34, 0.23, 0.14), red=(0.88, 0.84, 0.74), metal="iron"),
        "ram": mats.siege("DK_Ram", wood=(0.44, 0.31, 0.2), wood2=(0.3, 0.2, 0.13), metal="iron"),
        "drystone": DM.drystone("DK_DryStone"),
        "hay": DM.thatch("DK_Hay", base=(0.8, 0.66, 0.34), old=(0.66, 0.56, 0.32)), "wattle": mats.basket(),
        "sacking": mats.linen("DK_Sacking", base=(0.62, 0.5, 0.34), border=(0.42, 0.32, 0.2), stripe=(0.3, 0.24, 0.16)),
        "logs": DM.timber_log("DK_Logs"), "turf_roof": DM.turf("DK_TurfRoof", "meadow"),
        "chapel_stone": DM.ashlar("DK_ChapelStone", base=(0.6, 0.58, 0.53), joint=(0.32, 0.3, 0.27), course=0.22, block=0.4,
                                  grime7=(0.34, 0.36, 0.28)),
        "ivy": DM.leaves("DK_Ivy", base=(0.07, 0.2, 0.06), hi=(0.22, 0.4, 0.12)),
        "flags": mats.flagstone("DK_Flags"),
        "canvas": mats.linen("DK_Canvas", base=(0.9, 0.86, 0.74), border=(0.66, 0.1, 0.07), stripe=(0.14, 0.28, 0.6)),
        "hide": DM.hide("DK_Hide", "meadow"),
        "arrows": mats.arrows("DK_Arrows", head=(0.5, 0.52, 0.56), head_hi=(0.8, 0.82, 0.86),
                              fletch=((0.62, 0.6, 0.56), (0.9, 0.88, 0.84))),
        "spear": mats.javelin_shaft("DK_Spear"), "iron": mats.iron("DK_Iron"),
        "banner": mats.wool("DK_Banner", base=(0.14, 0.26, 0.62), border=(0.96, 0.78, 0.26), stripe=(0.08, 0.1, 0.2)),
        "ashlar": DM.ashlar("DK_Ashlar", base=(0.66, 0.64, 0.6), joint=(0.36, 0.35, 0.32), course=0.3, block=0.55,
                            grime7=(0.38, 0.38, 0.34)),
        "slate": DM.ashlar("DK_Slate", base=(0.3, 0.33, 0.38), joint=(0.13, 0.14, 0.17), course=0.1, block=0.17),
        "dark_water": DM.flat("DK_DarkWater", (0.05, 0.07, 0.06), 0.1, var=0.25),
        "glow_fire": DM.glow("DK_GlowFire", (1.0, 0.55, 0.15), 2.2),
    }


GLOW_KEYS = {"glow_lava": ((1.0, 0.45, 0.08), 1.6, 0.6), "glow_cyan": ((0.25, 0.85, 1.0), 1.3, 0.5),
             "glow_magenta": ((1.0, 0.2, 0.85), 1.3, 0.5), "glow_turq": ((0.3, 1.0, 0.78), 1.2, 0.5),
             "glow_fire": ((1.0, 0.55, 0.15), 1.4, 0.6)}      # (above ~1.5 glows wash out to pastel in game)


def kit():
    k = DP.KITS(THEME)
    return {n: v for n, v in k.items() if not ONLY or n in ONLY}


# ------------------------------------------------------------------------------------------------ sculpt
def sculpt_stage():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    T = time.time()
    x = 0.0
    for name, (fn, budget) in kit().items():
        parts = fn()
        meshes = []
        for part, f, vxs, mkey in parts:
            V, Fc = f.mesh(vxs)
            V, Fc = sdf.clean_islands(V, Fc, min_tris=30)
            meshes.append((part, V, Fc, mkey, f))
        lo = min(V[:, 0].min() for _, V, _, _, _ in meshes)
        hi = max(V[:, 0].max() for _, V, _, _, _ in meshes)
        off = x - lo
        x += (hi - lo) + 2.0
        tot = sum(len(Fc) for _, _, Fc, _, _ in meshes)
        for part, V, Fc, mkey, f in meshes:
            ob = sdf.to_blender("%s__%s" % (name, part), V + np.array([off, 0.0, 0.0]), Fc)
            ob["prop"] = name
            ob["part"] = part
            ob["mat"] = mkey
            ob["off"] = off
            ob["budget"] = max(40, int(budget * len(Fc) / max(tot, 1)))
            if any(op[0] == "paint" or op[3] for op in f.ops):          # (painted, or parts added under a label)
                d, lab = f.eval(V.astype(np.float32), labels=True)
                a = ob.data.attributes.new("region", "INT", "POINT")
                a.data.foreach_set("value", lab.astype(np.int32))
                for L, dd in f.paint_dist(V.astype(np.float32)).items():
                    pa = ob.data.attributes.new("p%d" % L, "FLOAT", "POINT")
                    pa.data.foreach_set("value", np.clip(0.5 - dd / 0.006, -2.0, 3.0).astype(np.float32))
        log("sculpted", name, tot, "tris %.0fs" % (time.time() - T))
    bpy.ops.wm.save_as_mainfile(filepath=HI)
    if arg("--shots"):
        shots(arg("--shots"))


def shots(D):
    """Material preview of the high-poly kit: one wide shot of every prop in its row."""
    os.makedirs(D, exist_ok=True)
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    cache = materials()
    for o in objs:
        sdf.fix_winding(o)
        prep.region_masks(o)
        m = cache.get(o.get("mat"))
        if m is not None:
            o.data.materials.clear()
            o.data.materials.append(m)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    __import__("cycles_dev").use(sc)
    sc.cycles.samples = 16
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    wd = bpy.data.worlds.new("W")
    sc.world = wd
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.58, 0.68, 1)
    wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(48), 0, math.radians(-30))
    sc.collection.objects.link(sun)
    lo = np.min([np.array(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box], 0)
    hi = np.max([np.array(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box], 0)
    W = hi[0] - lo[0]
    sc.render.resolution_x = 2400
    sc.render.resolution_y = min(1000, max(400, int(2400 * 6.0 / max(W, 1))))     # (a big frame costs GBs to render)
    cd = bpy.data.cameras.new("C")
    cd.type = "ORTHO"
    cd.ortho_scale = W * 1.04
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = Vector(((lo[0] + hi[0]) / 2, -30.0, 18.0))
    cam.rotation_euler = (Vector(((lo[0] + hi[0]) / 2, 0, 1.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(D, "kit_%s.png" % THEME)
    bpy.ops.render.render(write_still=True)
    if "--each" in ARGS:                       # plus a close-up of every prop from the game camera's angle
        from PIL import Image
        sc.render.resolution_x, sc.render.resolution_y = 640, 520
        sc.cycles.samples = 24
        props = {}
        for o in objs:
            props.setdefault(o.get("prop", o.name), []).append(o)
        tiles = []
        for name, obs in props.items():
            for o in objs:
                o.hide_render = o not in obs
            plo = np.min([np.array(o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box], 0)
            phi = np.max([np.array(o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box], 0)
            ctr = Vector(((plo + phi) / 2).tolist())
            r = float(np.linalg.norm(phi - plo)) / 2
            d = Vector((0.35, -0.75, 0.62)).normalized()
            cam.location = ctr + d * (r * 6)
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            cd.ortho_scale = r * 2.1
            fp = os.path.join(D, "each_%s.png" % name)
            sc.render.filepath = fp
            bpy.ops.render.render(write_still=True)
            tiles.append((name, fp))
        for o in objs:
            o.hide_render = False
        cols = 4
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (640 * cols, 520 * rows), (120, 130, 145))
        for i, (name, fp) in enumerate(tiles):
            sheet.paste(Image.open(fp).convert("RGB"), ((i % cols) * 640, (i // cols) * 520))
        sheet.save(os.path.join(D, "each_%s.png" % THEME))
    log("shots ->", D)


# ------------------------------------------------------------------------------------------------ direct geometry
def tuft_geometry(rng, blades=9, r=0.12, h=0.19):
    V, F, UV = [], [], []
    for i in range(blades):
        a = 2 * math.pi * i / blades + rng.uniform(-0.3, 0.3)
        rr = r * rng.uniform(0.2, 0.8)
        hh = h * rng.uniform(0.6, 1.0)
        lean = rng.uniform(0.3, 0.7)
        bx, by = rr * 0.3 * math.cos(a), rr * 0.3 * math.sin(a)
        w = 0.018
        px, py = -math.sin(a) * w, math.cos(a) * w
        tip = (bx + math.cos(a) * hh * lean, by + math.sin(a) * hh * lean, hh)
        mid = (bx + math.cos(a) * hh * lean * 0.4 - px * 0.6, by + math.sin(a) * hh * lean * 0.4 - py * 0.6, hh * 0.55)
        mid2 = (bx + math.cos(a) * hh * lean * 0.4 + px * 0.6, by + math.sin(a) * hh * lean * 0.4 + py * 0.6, hh * 0.55)
        k = len(V)
        V += [(bx - px, by - py, -0.02), (bx + px, by + py, -0.02), mid2, mid, tip]
        UV += [0.0, 0.0, 0.55, 0.55, 1.0]
        F += [(k, k + 1, k + 2, k + 3), (k + 3, k + 2, k + 4)]
    return V, F, [(0.975, G0 + G1 * t) for t in UV]


def flowers_geometry(rng, n=6):
    V, F, UV = [], [], []
    for i in range(n):
        cx, cy = rng.uniform(-0.2, 0.2), rng.uniform(-0.17, 0.17)
        h = rng.uniform(0.1, 0.18)
        col = int(rng.integers(0, 4))
        # stem
        k = len(V)
        V += [(cx - 0.008, cy, 0.0), (cx + 0.008, cy, 0.0), (cx, cy, h)]
        F += [(k, k + 1, k + 2)]
        UV += [(0.975, S0 + 0.055 * 4 + 0.022)] * 3
        # petals: a flat star
        k = len(V)
        V.append((cx, cy, h + 0.004))
        UV.append((0.975, S0 + 0.055 * 1 + 0.022))        # yellow centre
        for j in range(10):
            a = 2 * math.pi * j / 10
            rr = 0.045 if j % 2 == 0 else 0.02
            V.append((cx + rr * math.cos(a), cy + rr * math.sin(a), h))
            UV.append((0.975, S0 + 0.055 * (0 if col == 1 else col) + 0.022) if col != 1 else (0.975, S0 + 0.055 * 3 + 0.022))
        for j in range(10):
            F.append((k, k + 1 + j, k + 1 + (j + 1) % 10))
    return V, F, UV


def mesh_from(name, V, F, UV, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = UV[me.loops[li].vertex_index]
        poly.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------------------------------------ game
def game_stage():
    T = time.time()
    bpy.ops.wm.open_mainfile(filepath=HI)
    hi = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in hi:
        sdf.fix_winding(o)
        prep.region_masks(o)
    cache = materials()
    for o in hi:
        m = cache.get(o["mat"])
        o.data.materials.clear()
        o.data.materials.append(m)
    bake_hi = [o for o in hi if o["mat"] not in GLOW_KEYS]
    glow_hi = [o for o in hi if o["mat"] in GLOW_KEYS]
    pid = {o.name: i for i, o in enumerate(bake_hi)}
    props = sorted({o["prop"] for o in hi})
    prop_id = {p: i for i, p in enumerate(props)}
    low = []
    for o in bake_hi:
        lo_ob = lp.decimated_copy(o, int(o["budget"]), o.name + "_low")
        lp.tag_part(lo_ob, pid[o.name])
        a = lo_ob.data.attributes.new("prop", "INT", "FACE")
        a.data.foreach_set("value", np.full(len(lo_ob.data.polygons), prop_id[o["prop"]], np.int32))
        low.append(lo_ob)
    log("lowpoly", sum(len(o.data.polygons) for o in low), "tris %.0fs" % (time.time() - T))
    kitob = lp.join(low, "Kit")
    kitob.data.validate(clean_customdata=False)
    lp.unwrap(kitob, margin=0.003)
    uv = kitob.data.uv_layers.active.data
    co = np.zeros(len(uv) * 2, np.float32)
    uv.foreach_get("uv", co)
    co *= 0.94                                   # keep a free column on the right for the swatches
    uv.foreach_set("uv", co)
    log("uv %.0fs" % (time.time() - T))
    groups = [([pid[o.name]], [o]) for o in bake_hi]
    maps = bk.bake_groups(kitob, groups, TEX, ["DIFFUSE", "NORMAL", "ROUGHNESS", "AO"], ao_samples=AO_SPP, ao_dist=0.35,
                          extrusion=0.02, maxdist=0.06)
    log("bakes %.0fs" % (time.time() - T))
    from mats import lin
    def paint(a):
        h, w, _ = a.shape
        x0 = int(w * 0.955)
        c0, c1 = np.array(lin(GRASS[0])[:3]), np.array(lin(GRASS[1])[:3])
        for y in range(int(h * G0), int(h * (G0 + G1))):
            t = (y - h * G0) / (h * G1)
            a[y, x0:w - 4] = c0 * (1 - t) + c1 * t
        for i, c in enumerate(SWATCHES):
            y0 = int(h * (S0 + 0.055 * i))
            a[y0:y0 + int(h * 0.045), x0:w - 4] = np.array(lin(c)[:3])
        return a
    pa, pn, po = bk.save_maps(maps, OUT, GLB, ao_strength=0.75, extra_paint=paint, sat=1.08, val=1.02)
    nrm = np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(pn)).copy()
    nrm[:, int(nrm.shape[1] * 0.95):] = (128, 128, 255)
    __import__("PIL.Image", fromlist=["Image"]).fromarray(nrm).save(pn)
    kmat = bk.game_material("KitMat", pa, pn, po)
    kitob.data.materials.clear()
    kitob.data.materials.append(kmat)
    # split per prop, back to the origin
    bm_all = kitob
    objs = {}
    for p in props:
        bm = bmesh.new()
        bm.from_mesh(bm_all.data)
        lay = bm.faces.layers.int.get("prop")
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != prop_id[p]], context="FACES")
        if len(bm.faces) == 0:
            bm.free()
            continue
        me = bpy.data.meshes.new(p)
        bm.to_mesh(me)
        bm.free()
        off = next(o["off"] for o in hi if o["prop"] == p)
        me.transform(Matrix.Translation((-off, 0, 0)))
        ob = bpy.data.objects.new(p, me)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.clear()
        me.materials.append(kmat)
        objs[p] = ob
    # glowing parts join their prop as a second, emissive surface
    for o in glow_hi:
        p = o["prop"]
        g = lp.decimated_copy(o, int(o["budget"]), o.name + "_glow")
        g.data.transform(Matrix.Translation((-o["off"], 0, 0)))
        col, strength, base = GLOW_KEYS[o["mat"]]
        gm = bpy.data.materials.get("Glow_" + o["mat"]) or bpy.data.materials.new("Glow_" + o["mat"])
        gm.use_nodes = True
        b = gm.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = mats.lin(tuple(c * base for c in col))
        b.inputs["Emission Color"].default_value = mats.lin(col)
        b.inputs["Emission Strength"].default_value = strength
        g.data.materials.clear()
        g.data.materials.append(gm)
        if p in objs:
            bpy.ops.object.select_all(action="DESELECT")
            objs[p].select_set(True)
            g.select_set(True)
            bpy.context.view_layer.objects.active = objs[p]
            bpy.ops.object.join()
        else:
            g.name = p
            objs[p] = g
    rng = np.random.default_rng(3)
    if THEME in ("meadow", "volcano", "delta", "desert", "canyon", "highland", "forge", "bog", "olive", "coast", "acropolis",
                 "farmland", "darkwood", "castle"):
        V, F, UV = [], [], []
        for k in range(3):                          # a clump of three tufts
            v, f, u = tuft_geometry(rng)
            ox, oy = rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08)
            base = len(V)
            V += [(x + ox, y + oy, z) for x, y, z in v]
            F += [tuple(base + i for i in q) for q in f]
            UV += u
        objs["Tuft"] = mesh_from("Tuft", V, F, UV, kmat)
    if THEME in ("meadow", "delta", "highland", "olive", "coast", "farmland", "castle"):
        V, F, UV = flowers_geometry(rng)
        objs["Flowers"] = mesh_from("Flowers", V, F, UV, kmat)
    bpy.data.objects.remove(bm_all)
    for o in hi:
        bpy.data.objects.remove(o)
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and o.name not in objs:
            bpy.data.objects.remove(o)
    for me in [me for me in bpy.data.meshes if me.users == 0]:
        bpy.data.meshes.remove(me)
    for ob in objs.values():
        ob.data.validate(clean_customdata=False)
    bpy.ops.wm.save_as_mainfile(filepath=GAME)
    log("game done %.0fs" % (time.time() - T), {k: len(v.data.polygons) for k, v in objs.items()})


def export_stage():
    bpy.ops.wm.open_mainfile(filepath=GAME)
    path = os.path.join(OUT, GLB + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_animations=False, export_tangents=True,
                              export_apply=False, export_yup=True, export_image_format="JPEG", export_jpeg_quality=92,
                              export_materials="EXPORT")
    log("exported", path, os.path.getsize(path))


if STAGE in ("sculpt", "all"):
    sculpt_stage()
if STAGE in ("game", "all"):
    game_stage()
if STAGE in ("export", "all"):
    export_stage()
if STAGE == "shots":
    bpy.ops.wm.open_mainfile(filepath=HI)
    shots(arg("--shots", os.path.join(OUT, "shots")))
