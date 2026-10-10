"""Generates all game data for eras 3-10 (Iron Age .. The Data Center) from tools/era_spec.py.

Writes/updates: data/towers.json, data/heroes.json, data/enemies.json, data/maps.json,
data/map_<id>.json, data/waves_<id>.json and the era XP multipliers in data/legacy.json.
Stone and Bronze Age content is hand-authored and left untouched (except that every
existing hero ability gets a generic "type").

Design rules:
- Each era tower is built from the Bronze Age tower of the same lineage (proven balance),
  scaled by the era's power and given its signature twist plus two branch "styles".
- Gold costs stay the same across eras; robot HP (map hp_mult) and tower damage both scale
  with era power, so later eras are about new mechanics, not bigger numbers alone.
- Descriptions of upgrades are generated from their actual stat changes, so they never lie.

Run: python3 tools/gen_eras.py   (from the repo root). Use --hp key=value to override a map's hp_mult."""
import copy
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import era_spec as S  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
D = os.path.join(ROOT, "data")


def load(name):
    return json.load(open(os.path.join(D, name)))


def save(name, obj):
    with open(os.path.join(D, name), "w") as f:
        json.dump(obj, f, indent=1)


towers = load("towers.json")
heroes = load("heroes.json")
enemies = load("enemies.json")
maps_index = load("maps.json")
legacy = load("legacy.json")

ERA_BY_ID = {e["id"]: e for e in S.ERAS}
TEMPLATE = {"Ranged": "bronze_archer", "Brute": "spear_guard", "Siege": "torsion_catapult", "Control": "sun_priest"}
SWING = {"Ranged": [-0.9, 0.5], "Brute": [-0.5, 1.2], "Siege": [-0.15, 2.0], "Control": [-0.5, 0.35]}

# ------------------------------------------------------------------ branch styles
# Three tiers of mods per style. "damage" values are Bronze-scale and get multiplied by era power.
STYLES = {
    # Ranged
    "fire":      [{"dtype": "fire", "damage": 3, "splash": 0.7}, {"damage": 6, "shots": 1}, {"damage": 16, "splash": 0.5, "shots": 1}],
    "rapid":     [{"shots": 2, "cooldown_mult": 0.85}, {"damage": 3, "shots": 1, "cooldown_mult": 0.85}, {"shots": 3, "cooldown_mult": 0.55, "damage": 3}],
    "heavy":     [{"damage": 6, "armor_pierce": 3}, {"damage": 12, "crit_chance": 0.2, "crit_mult": 3.0, "range": 1.0}, {"damage": 34, "armor_pierce": 6, "boss_mult": 1.5}],
    "crit":      [{"crit_chance": 0.2, "crit_mult": 3.0, "range": 0.8}, {"damage": 6, "cooldown_mult": 0.8}, {"damage": 14, "crit_chance": 0.15, "crit_mult": 5.0, "range": 1.0}],
    "pin":       [{"damage": 6, "stun": 0.25}, {"damage": 10, "armor_pierce": 3, "range": 0.8}, {"damage": 30, "stun": 0.25, "boss_mult": 1.5}],
    "chain":     [{"chain": 1, "damage": 3}, {"chain": 1, "chain_range": 0.6, "damage": 6}, {"chain": 3, "damage": 16}],
    "pulse":     [{"cooldown_mult": 0.7}, {"damage": 4, "cooldown_mult": 0.8}, {"damage": 10, "cooldown_mult": 0.6}],
    # Brute
    "crowd":     [{"max_targets": 4, "stun": 0.35, "range": 0.4}, {"damage": 10, "knockback": 0.4}, {"damage": 28, "max_targets": 40, "stun": 0.05}],
    "boss":      [{"cooldown_mult": 0.55}, {"damage": 16, "armor_pierce": 4}, {"damage": 24, "boss_mult": 3.0}],
    "inferno":   [{"max_targets": 4, "burn": 3, "burn_time": 2.0, "dtype": "fire"}, {"damage": 10, "range": 0.4, "burn": 3}, {"damage": 26, "max_targets": 40, "burn": 6}],
    "slam":      [{"max_targets": 3, "stun": 0.4}, {"damage": 10, "stun": 0.15, "range": 0.4}, {"damage": 26, "max_targets": 40, "stun": 0.25}],
    "steam":     [{"max_targets": 4, "knockback": 0.3, "range": 0.3}, {"damage": 10, "dtype": "fire", "burn": 2}, {"damage": 26, "max_targets": 40, "knockback": 0.3}],
    # Siege
    "firepot":   [{"dtype": "fire", "damage": 6, "burn": 2, "burn_time": 2.0}, {"damage": 12, "splash": 0.6, "burn": 2}, {"damage": 50, "splash": 1.0, "stun": 0.3}],
    "shatter":   [{"shred": 2, "stun": 0.25}, {"damage": 14, "shred": 2}, {"damage": 30, "cooldown_mult": 0.6, "shred": 3}],
    "barrage":   [{"cooldown_mult": 0.6}, {"damage": 10, "cooldown_mult": 0.8, "shred": 1}, {"damage": 24, "cooldown_mult": 0.55}],
    "blast":     [{"damage": 8, "splash": 0.6}, {"damage": 16, "splash": 0.5}, {"damage": 56, "splash": 1.0, "stun": 0.2}],
    "sam":       [{"cooldown_mult": 0.7, "anti_air": 1}, {"damage": 12, "air_mult": 2.0}, {"damage": 28, "cooldown_mult": 0.6, "air_mult": 3.0}],
    # Control
    "hold":      [{"stun": 0.3, "slow": 0.15}, {"expose": 0.2, "range": 0.6}, {"stun": 0.3, "expose": 0.25, "range": 1.0}],
    "storm":     [{"damage": 6}, {"damage": 12, "cooldown_mult": 0.7}, {"damage": 34, "range": 0.8}],
    "corrode":   [{"slow": 0.15, "shred": 1}, {"expose": 0.2, "shred": 1, "range": 0.5}, {"slow": 0.15, "expose": 0.3, "shred": 2}],
    "freeze":    [{"slow": 0.2, "slow_time": 0.6}, {"slow": 0.1, "stun": 0.2, "range": 0.6}, {"slow": 0.1, "expose": 0.35, "stun": 0.2}],
    "shockwave": [{"stun": 0.3, "range": 0.4}, {"damage": 10, "stun": 0.2}, {"damage": 30, "stun": 0.4, "range": 0.8}],
}

TOWER_STYLES = {
    "javelin_thrower": ("pin", "rapid"), "axe_warrior": ("crowd", "boss"), "ballista": ("firepot", "barrage"), "druid": ("hold", "storm"),
    "cretan_archer": ("fire", "crit"), "legionary": ("slam", "boss"), "onager": ("firepot", "shatter"), "oracle": ("hold", "storm"),
    "crossbowman": ("heavy", "rapid"), "knight": ("crowd", "boss"), "trebuchet": ("firepot", "blast"), "alchemist": ("corrode", "storm"),
    "musketeer": ("crit", "rapid"), "halberdier": ("crowd", "slam"), "cannon": ("blast", "barrage"), "war_drummer": ("shockwave", "storm"),
    "rifleman": ("heavy", "rapid"), "steam_brawler": ("steam", "boss"), "field_gun": ("blast", "barrage"), "tesla_coil": ("shockwave", "storm"),
    "sniper": ("heavy", "crit"), "flamethrower": ("inferno", "boss"), "missile_launcher": ("blast", "sam"), "emp_tower": ("hold", "storm"),
    "laser_turret": ("chain", "pulse"), "mech_brawler": ("slam", "boss"), "plasma_mortar": ("blast", "barrage"), "cryo_field": ("freeze", "shockwave"),
    "arc_cannon": ("chain", "rapid"), "titan_mech": ("crowd", "boss"), "nova_artillery": ("blast", "shatter"), "firewall": ("hold", "storm"),
}

DAMAGE_KEYS = ("damage", "burn", "armor_pierce", "shred")   # armor scales with era power too


def fmt_num(v):
    v = round(v, 1)
    return str(int(v)) if abs(v - int(v)) < 1e-6 else str(v)


def describe(mods):
    """Plain-English upgrade text generated from the actual stat changes."""
    parts = []
    m = mods
    if m.get("dtype") == "fire":
        parts.append("fire damage")
    if m.get("dtype") == "energy":
        parts.append("energy damage")
    if "damage" in m:
        parts.append("+%s damage" % fmt_num(m["damage"]))
    if "shots" in m:
        parts.append("+%d shot%s" % (m["shots"], "" if m["shots"] == 1 else "s"))
    if "cooldown_mult" in m:
        c = m["cooldown_mult"]
        parts.append("attacks %d%% faster" % round((1 / c - 1) * 100) if c < 1 else "slower but stronger")
    if "max_targets" in m:
        parts.append("hits everything in reach" if m["max_targets"] >= 40 else "hits %d more" % m["max_targets"])
    if "chain" in m:
        parts.append("jumps to %d more robot%s" % (m["chain"], "" if m["chain"] == 1 else "s"))
    if "splash" in m:
        parts.append("bigger blast")
    if "burn" in m:
        parts.append("sets robots on fire")
    if "stun" in m:
        parts.append("stuns")
    if "slow" in m:
        parts.append("slows more")
    if "expose" in m:
        parts.append("marked robots take +%d%% damage" % round(m["expose"] * 100))
    if "armor_pierce" in m:
        parts.append("pierces %d more armor" % m["armor_pierce"])
    if "shred" in m:
        parts.append("strips armor")
    if "crit_chance" in m:
        parts.append("%d%% crit chance for %sx" % (round(m["crit_chance"] * 100), fmt_num(m.get("crit_mult", 2))))
    if "knockback" in m:
        parts.append("knocks robots back")
    if "boss_mult" in m:
        parts.append("%sx damage to bosses" % fmt_num(m["boss_mult"]))
    if "anti_air" in m:
        parts.append("hits flying robots")
    if "air_mult" in m:
        parts.append("%sx damage to flyers" % fmt_num(m["air_mult"]))
    if "range" in m:
        parts.append("+%s range" % fmt_num(m["range"]))
    if "chain_range" in m:
        parts.append("longer jumps")
    if "slow_time" in m and "slow" not in m:
        parts.append("slows longer")
    txt = ", ".join(parts[:3]) if parts else "Stronger"
    return txt[0].upper() + txt[1:]


def sc(v, power):
    x = v * power
    return int(round(x)) if abs(x) >= 10 else round(x, 1)


def scale_mods(mods, power):
    out = {}
    for k, v in mods.items():
        if k in DAMAGE_KEYS and isinstance(v, (int, float)):
            out[k] = sc(v, power)
        else:
            out[k] = v
    return out


DTYPE = {"tesla_coil": "energy", "emp_tower": "energy", "cryo_field": "energy", "firewall": "energy",
         "druid": "blunt", "war_drummer": "blunt", "alchemist": "fire"}


def make_tower(spec, era):
    lin = spec["lineage"]
    t = copy.deepcopy(towers[TEMPLATE[lin]])
    p = era["power"]
    base = t["base"]
    for k in DAMAGE_KEYS:
        if k in base:
            base[k] = sc(base[k], p)
    if spec["id"] in DTYPE:
        base["dtype"] = DTYPE[spec["id"]]
    for k, v in spec.get("twist", {}).items():
        if k == "cooldown_mult":
            base["cooldown"] = round(base["cooldown"] * v, 3)
        elif isinstance(v, str):
            base[k] = v
        elif k in DAMAGE_KEYS:
            base[k] = sc(base.get(k, 0) + v * p, 1.0)
        else:
            base[k] = round(base.get(k, 0) + v, 3)
            if base[k] <= 0 and k in ("shots", "max_targets"):
                base[k] = 1
    if base.get("shots", 1) <= 1:
        base.pop("shots", None)
    if base.get("splash", 0) < 0:
        base["splash"] = 0
    if "slow" in base and base["slow"] <= 0:
        base.pop("slow", None)
    if spec.get("proj"):
        base["proj"] = spec["proj"]
    if base["kind"] == "projectile" and spec.get("proj") in ("bullet", "laser", "arc"):
        base["proj_speed"] = 34
    t.update({"name": spec["name"], "era": era["name"], "desc": spec["desc"], "model_scale": 0.56, "swing": SWING[lin]})
    # shared tiers keep their Bronze mods (scaled) but take the era's names
    for i, nm in enumerate(spec["tiers"]):
        tier = t["tiers"][i]
        tier["name"] = nm
        tier["mods"] = scale_mods(tier["mods"], p)
        tier["desc"] = describe(tier["mods"])
    sa, sb = TOWER_STYLES[spec["id"]]
    for key, style in (("A", sa), ("B", sb)):
        bname, tnames, bdesc = spec[key]
        br = t["branches"][key]
        br["name"] = bname
        br["desc"] = bdesc
        for i in range(3):
            mods = scale_mods(STYLES[style][i], p)
            br["tiers"][i]["name"] = tnames[i]
            br["tiers"][i]["mods"] = mods
            br["tiers"][i]["desc"] = describe(mods)
    if spec.get("twist", {}).get("detect"):
        base["detect"] = 1
    return t


# ------------------------------------------------------------------ heroes
HERO_BASE = {
    "projectile": {"kind": "projectile", "range": 5.2, "cooldown": 0.8, "damage": 4, "dtype": "pierce", "proj_speed": 20, "splash": 0},
    "melee": {"kind": "melee", "range": 2.2, "cooldown": 0.7, "damage": 8, "dtype": "pierce", "max_targets": 2, "armor_pierce": 3},
    "pulse": {"kind": "pulse", "range": 3.2, "cooldown": 1.1, "damage": 3, "dtype": "blunt", "slow": 0.25, "slow_time": 1.2},
    "lob": {"kind": "lob", "range": 6.5, "cooldown": 1.4, "damage": 7, "dtype": "blunt", "splash": 1.2, "flight": 0.8},
}
HERO_PER_LEVEL = {
    "projectile": {"damage": 0.9, "range": 0.06, "cooldown": -0.012},
    "melee": {"damage": 1.8, "range": 0.04},
    "pulse": {"damage": 0.6, "range": 0.06},
    "lob": {"damage": 1.4, "range": 0.05},
}
AURA = {
    "damage": {"damage": 0.1, "damage_per_level": 0.015},
    "speed": {"speed": 0.08, "speed_per_level": 0.01},
    "range": {"range": 0.06, "range_per_level": 0.008},
}
HERO_PROJ = {"brenna": "javelin", "kael": "javelin", "wren": "arrow", "isla": "bullet", "ada": "bolt", "maya": "bullet",
             "nova": "laser", "vega": "plasma", "marco": "cannonball", "zero": "shell"}


def ability(atype, aid, name, desc, p):
    a = {"id": aid, "type": atype, "name": name, "desc": desc, "unlock": 3}
    if atype == "rain":
        a.update({"cooldown": 55, "targets": 10, "damage": round(32 * p), "damage_per_level": round(10 * p)})
    elif atype == "quake":
        a.update({"cooldown": 60, "stun": 1.5, "stun_per_level": 0.1, "damage": round(16 * p), "damage_per_level": round(6 * p)})
    elif atype == "flare":
        a.update({"cooldown": 45, "radius": 5.5, "damage": round(120 * p), "damage_per_level": round(40 * p), "expose": 0.25, "expose_time": 6.0})
    elif atype == "fury":
        a.update({"cooldown": 60, "speed": 0.5, "duration": 7.0})
    elif atype == "strike":
        a.update({"cooldown": 50, "targets": 3, "damage": round(260 * p), "damage_per_level": round(80 * p), "splash": 1.6})
    elif atype == "freeze":
        a.update({"cooldown": 60, "slow": 0.7, "duration": 5.0, "duration_per_level": 0.25})
    elif atype == "emp":
        a.update({"cooldown": 50, "radius": 6.0, "stun": 2.5, "stun_per_level": 0.15, "damage": round(60 * p), "damage_per_level": round(20 * p)})
    return a


def make_hero(spec, era):
    p = era["power"]
    kind = spec["kind"]
    base = copy.deepcopy(HERO_BASE[kind])
    for k in DAMAGE_KEYS:
        if k in base:
            base[k] = round(base[k] * p, 1)
    if spec["id"] in HERO_PROJ:
        base["proj"] = HERO_PROJ[spec["id"]]
    per = copy.deepcopy(HERO_PER_LEVEL[kind])
    per["damage"] = round(per["damage"] * p, 2)
    lin, stat = spec["aura"]
    aura = {"radius": 4.0, "lineage": lin}
    aura.update(AURA[stat])
    aid, aname, atype, adesc = spec["ability"]
    return {
        "legacy_unlock": spec["unlock"], "name": spec["name"], "title": spec["title"], "era": era["name"],
        "color": spec["color"], "blurb": spec["blurb"], "base": base, "per_level": per, "aura": aura,
        "ability": ability(atype, aid, aname, adesc, p), "swing": [-0.9, 1.2] if kind == "melee" else [-1.0, 0.8],
        "model_scale": 0.55,
    }


# ------------------------------------------------------------------ robots
def make_robot(r, boss=False):
    out = {"name": r["name"], "hp": r["hp"], "speed": r["speed"], "armor": r["armor"], "bounty": r["bounty"],
           "leak": r["leak"], "size": r["size"], "model_scale": 1.0 if boss else 0.9}
    for k in ("flying", "cloak", "on_death", "summon", "emp", "regen", "enrage", "shield", "shield_delay", "heal"):
        if k in r:
            out[k] = r[k]
    out["bar_h"] = 3.8 if boss else round(0.95 + 0.95 * r["size"], 2)
    if boss:
        out["boss"] = True
    if r.get("flying"):
        out["flying_look"] = True
    return out


# ------------------------------------------------------------------ maps
ERA_BASE = {"iron": "hillfort", "classical": "temple", "medieval": "castle", "gunpowder": "fort",
            "industrial": "factory", "modern": "bunker", "digital": "lab", "datacenter": "camp"}
ERA_BOSS = {b["era"]: b["id"] for b in S.BOSSES}
# era roster substitutions used to remix the proven Bronze wave tables
ROSTER = {
    "iron":       {"heavy": "ironclad", "special": "carrier", "fast": "scout", "shield": "shield_bot"},
    "classical":  {"heavy": "ironclad", "special": "hydra_head", "fast": "hover_drone", "shield": "shield_bot"},
    "medieval":   {"heavy": "ironclad", "special": "cloaker", "fast": "hover_drone", "shield": "shield_bot"},
    "gunpowder":  {"heavy": "ironclad", "special": "bomber", "fast": "cloaker", "shield": "shield_bot"},
    "industrial": {"heavy": "steam_tank", "special": "bomber", "fast": "hover_drone", "shield": "shield_bot"},
    "modern":     {"heavy": "steam_tank", "special": "stealth_jet", "fast": "cloaker", "shield": "shield_bot"},
    "digital":    {"heavy": "steam_tank", "special": "nano_swarm", "fast": "stealth_jet", "shield": "shield_bot"},
    "datacenter": {"heavy": "sentinel", "special": "nano_swarm", "fast": "stealth_jet", "shield": "shield_bot"},
}
THEME_BLOCKERS = {
    "highland": ["stones", "lake", "trees"], "forge": ["slag", "lava", "slag"], "bog": ["lake", "trees", "lake"],
    "olive": ["ruins", "trees", "rocks"], "coast": ["rocks", "ruins", "rocks"], "acropolis": ["ruins", "statue", "ruins"],
    "farmland": ["trees", "building", "trees"], "castle": ["rocks", "tents", "rocks"], "darkwood": ["trees", "ruins", "trees"],
    "harbor": ["crates", "rocks", "crates"], "fortress": ["crater", "crates", "crater"], "jungle": ["trees", "ruins", "trees"],
    "railyard": ["coal", "crates", "coal"], "factory": ["building", "machine", "building"], "smog": ["building", "lake", "building"],
    "suburb": ["building", "lake", "trees"], "military": ["crater", "machine", "crates"], "metro": ["building", "trees", "building"],
    "neon": ["pylon", "pit", "pylon"], "satellite": ["dish", "panels", "dish"], "lab": ["machine", "tank", "machine"],
    "server": ["rack", "machine", "rack"], "cooling": ["ice", "machine", "ice"], "core": ["pillar", "wreck", "pillar"],
}

L = [-15.6]
PATHS = {
    "highland_ford": [[[-15.6, -5], [-10, -5], [-10, 4.5], [-4, 4.5], [-4, -5], [2.5, -5], [2.5, 4.5], [9, 4.5], [9, -1.5], [15.4, -1.5]]],
    "ember_forge": [[[-15.6, 6], [-7, 6], [-7, -6], [0, -6], [0, 2], [6, 2], [6, -4], [11, -4], [11, 5], [15.4, 5]]],
    "olive_hills": [[[-15.6, 0], [-11, 0], [-11, -6], [-5, -6], [-5, 6], [1, 6], [1, -2], [7, -2], [7, 6], [12, 6], [12, -3], [15.4, -3]]],
    "marble_coast": [[[-15.6, -6], [-6, -6], [-6, 0], [-12, 0], [-12, 6], [-1, 6], [-1, -4], [5, -4], [5, 3], [15.4, 3]]],
    "hedgerow_fields": [[[-15.6, 3], [-9, 3], [-9, -6], [-2, -6], [-2, 5], [5, 5], [5, -5], [11, -5], [11, 1], [15.4, 1]]],
    "castle_siege": [[[-15.6, -2], [-6, -2], [-6, -7], [6, -7], [6, -2], [0, -2], [0, 6], [10, 6], [10, 0], [15.4, 0]]],
    "smugglers_harbor": [[[-15.6, 5], [-9, 5], [-9, -3], [-3, -3], [-3, 5], [3, 5], [3, -6], [10, -6], [10, 2], [15.4, 2]]],
    "star_fort": [[[-15.6, -6], [-10, -6], [-10, 6], [-5, 6], [-5, -2], [0, -2], [0, 6], [5, 6], [5, -6], [10, -6], [10, 3], [15.4, 3]]],
    "railyard": [[[-15.6, -1], [-8, -1], [-8, 6], [-2, 6], [-2, -6], [4, -6], [4, 2], [10, 2], [10, -4], [15.4, -4]]],
    "foundry_row": [[[-15.6, 7], [-11, 7], [-11, -4], [-6, -4], [-6, 3], [-1, 3], [-1, -6], [5, -6], [5, 4], [11, 4], [11, -1], [15.4, -1]]],
    "suburbia": [[[-15.6, 4], [-6, 4], [-6, -5], [3, -5], [3, 6], [9, 6], [9, -2], [15.4, -2]]],
    "airbase": [[[-15.6, -7], [-3, -7], [-3, -1], [-11, -1], [-11, 6], [4, 6], [4, -3], [9, -3], [9, 3], [15.4, 3]]],
    "neon_grid": [[[-15.6, 0], [-10, 0], [-10, -6], [-4, -6], [-4, 6], [2, 6], [2, -6], [8, -6], [8, 6], [12, 6], [12, 0], [15.4, 0]]],
    "dish_array": [[[-15.6, 6], [-8, 6], [-8, -2], [-13, -2], [-13, -7], [0, -7], [0, 2], [6, 2], [6, -4], [12, -4], [12, 5], [15.4, 5]]],
    "server_hall": [[[-15.6, -4], [-11, -4], [-11, 5], [-5, 5], [-5, -4], [1, -4], [1, 5], [7, 5], [7, -4], [13, -4], [13, 1], [15.4, 1]]],
    "coolant_vaults": [[[-15.6, 2], [-8, 2], [-8, -6], [1, -6], [1, 6], [8, 6], [8, -3], [15.4, -3]]],
}


def twin(a, b, tail):
    return [a + tail, b + tail]


PATHS.update({
    "mirefen_bog": twin([[-15.6, -6], [-6, -6], [-6, 0]], [[-15.6, 6], [-10, 6], [-10, 2], [-3, 2], [-3, 0]],
                        [[0, 0], [0, 6], [7, 6], [7, -5], [15.4, -5]]),
    "acropolis": twin([[-15.6, -5], [-9, -5], [-9, 0]], [[-15.6, 6], [-4, 6], [-4, 0]],
                      [[2, 0], [2, -6], [9, -6], [9, 4], [15.4, 4]]),
    "darkwood": twin([[-15.6, -7], [-10, -7], [-10, -3]], [[-15.6, 3], [-12, 3], [-12, 7], [-4, 7], [-4, -3]],
                     [[1, -3], [7, -3], [7, 5], [12, 5], [12, -1], [15.4, -1]]),
    "jungle_outpost": twin([[-15.6, -3], [-9, -3], [-9, 2]], [[-15.6, 7], [-3, 7], [-3, 2]],
                           [[3, 2], [3, -6], [10, -6], [10, 3], [15.4, 3]]),
    "smog_city": twin([[-15.6, -6], [-5, -6], [-5, 0]], [[-15.6, 5], [-10, 5], [-10, 0]],
                      [[-1, 0], [6, 0], [6, 6], [12, 6], [12, -4], [15.4, -4]]),
    "downtown": twin([[-15.6, -7], [-6, -7], [-6, -1]], [[-15.6, 4], [-9, 4], [-9, 7], [0, 7], [0, -1]],
                     [[4, -1], [10, -1], [10, 6], [15.4, 6]]),
    "cleanroom": twin([[-15.6, -4], [-8, -4], [-8, -1]], [[-15.6, 5], [-5, 5], [-5, -1]],
                      [[0, -1], [0, -7], [7, -7], [7, 5], [15.4, 5]]),
    "the_core": twin([[-15.6, -7], [-7, -7], [-7, 0]], [[-15.6, 7], [-7, 7], [-7, 0]],
                     [[2, 0], [8, 0], [8, -6], [13, -6], [13, 3], [15.4, 3]]),
})


def seg_dist(p, a, b):
    ax, az = a
    bx, bz = b
    px, pz = p
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (pz - az) * dz) / L2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def dist_to_paths(p, paths):
    return min(seg_dist(p, pts[i - 1], pts[i]) for pts in paths for i in range(1, len(pts)))


def path_len(pts):
    return sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts)))


def river_for(paths, seed):
    """A wavy vertical river that crosses the road exactly once (that crossing becomes a bridge)."""
    pts = paths[0]
    for x0 in [6.0, 5.5, 6.5, 7.0, -1.0, -2.0, 0.5, 4.0, -6.5, 12.5, 13.0]:
        n = 0
        for i in range(1, len(pts)):
            a, b = pts[i - 1][0], pts[i][0]
            if min(a, b) < x0 < max(a, b):
                n += 1
            if (a == x0 or b == x0):
                n += 9
        near_parallel = any(pts[i - 1][0] == pts[i][0] and abs(pts[i][0] - x0) < 2.8 for i in range(1, len(pts)))
        if n == 1 and not near_parallel:
            r = random.Random(seed)
            rv = []
            z = -13.0
            while z <= 13.01:
                rv.append([round(x0 + r.uniform(-0.7, 0.7), 2), round(z, 2)])
                z += 2.6
            return [{"pts": rv, "width": 2.2}]
    raise SystemExit("no single-crossing river for map")


def place_blockers(paths, rivers, kinds, seed, count=5):
    r = random.Random(seed)
    out = []
    tries = 0
    while len(out) < count and tries < 4000:
        tries += 1
        rad = round(r.uniform(1.15, 1.6), 2)
        x = round(r.uniform(-14 + rad, 14 - rad), 1)
        z = round(r.uniform(-7.6 + rad, 7.6 - rad), 1)
        if dist_to_paths((x, z), paths) < rad + 1.25:
            continue
        if rivers and dist_to_paths((x, z), [rv["pts"] for rv in rivers]) < rad + 1.6:
            continue
        if any(math.hypot(x - o[0], z - o[1]) < rad + o[2] + 1.4 for o in out):
            continue
        if x > 13.0 and abs(z - paths[0][-1][1]) < 4:   # keep the base area clear
            continue
        out.append([x, z, rad, kinds[len(out) % len(kinds)]])
    return out


DIFF = {"Normal": (0, 900), "Hard": (1, 1000), "Brutal": (2, 1250)}
HP_BASE = {"Normal": 1.3, "Hard": 1.45, "Brutal": 1.5}


def remix(table, roster, boss, era_id):
    """Swap the Bronze wave tables' robots for this era's roster, scaling counts by HP so pressure stays sane."""
    swap = {"brute": roster["heavy"], "carrier": roster["special"], "scout": roster["fast"], "shield_bot": roster["shield"]}
    out = []
    for wi, w in enumerate(table):
        groups = []
        for g in w:
            t, c, iv, dl = g[0], g[1], g[2], g[3]
            if t == "siege_crawler":
                groups.append({"type": boss, "count": c, "interval": iv, "delay": dl})
                continue
            nt = t
            # every other wave keeps the classic robot so the old roster still shows up
            if t in swap and (wi % 2 == 1 or t in ("carrier",) or wi >= 12):
                nt = swap[t]
            if nt != t:
                ratio = enemies[t]["hp"] / max(1.0, enemies_new[nt]["hp"]) if nt in enemies_new else 1.0
                if nt in ("hydra_head",):
                    ratio *= 0.6
                c = max(1, round(c * min(1.0, ratio * 1.25)))
                iv = round(iv / max(0.35, min(1.0, ratio * 1.25)), 2)
            groups.append({"type": nt, "count": c, "interval": iv, "delay": dl})
        out.append(groups)
    return out


def bronze_tables():
    sys.argv = [sys.argv[0], "/dev/null"]
    ns = {}
    src = open(os.path.join(os.path.dirname(__file__), "gen_waves.py")).read()
    src = src.split("def write(")[0]
    exec(src, ns)
    return {"Normal": ns["MAP4"], "Hard": ns["MAP5"], "Brutal": ns["MAP6"]}


# ------------------------------------------------------------------ build everything
hp_override = {}
for a in sys.argv[1:]:
    if "=" in a:
        k, v = a.split("=")
        hp_override[k] = float(v)

enemies_new = dict(enemies)
for r in S.ROBOTS:
    enemies_new[r["id"]] = make_robot(r)
for b in S.BOSSES:
    # Map hp_mult already scales with era power, so boss base HP only grows gently from the
    # Siege Crawler's 2600 (the spec's raw numbers would double-count the era scaling).
    bb = dict(b)
    idx = ERA_BY_ID[b["era"]]["index"]
    k = 2600 * 1.08 ** (idx - 1) / b["hp"]
    bb["hp"] = int(round(b["hp"] * k, -1))
    if "shield" in bb:
        bb["shield"] = int(round(b["shield"] * k, -1))
    enemies_new[b["id"]] = make_robot(bb, boss=True)

for era in S.ERAS:
    for spec in S.TOWERS[era["id"]]:
        towers[spec["id"]] = make_tower(spec, era)
    for spec in S.HEROES[era["id"]]:
        heroes["heroes"][spec["id"]] = make_hero(spec, era)

# old heroes get a generic ability type
OLD_TYPES = {"stone_rain": "rain", "earthquake": "quake", "solar_flare": "flare", "forge_fury": "fury"}
for hid, h in heroes["heroes"].items():
    if "type" not in h["ability"]:
        h["ability"]["type"] = OLD_TYPES[h["ability"]["id"]]

tables = bronze_tables()
prev_hp = {}
prev_boss = {}
for m in maps_index["maps"]:
    if os.path.exists(os.path.join(D, "map_%s.json" % m["id"])):
        old = load("map_%s.json" % m["id"])
        prev_hp[m["id"]] = old.get("hp_mult")
        if "boss_hp_mult" in old:
            prev_boss[m["id"]] = old["boss_hp_mult"]
maps_index["maps"] = [m for m in maps_index["maps"] if m["era"] in ("Stone Age", "Bronze Age")]
for mid, name, era_id, diff, theme, portals, blurb, extra in S.MAPS:
    era = ERA_BY_ID[era_id]
    paths = PATHS[mid]
    assert len(paths) == portals, mid
    seed = sum(ord(c) for c in mid)
    rivers = river_for(paths, seed) if extra.get("river") else []
    blockers = place_blockers(paths, rivers, THEME_BLOCKERS[theme], seed)
    hp = HP_BASE[diff] * era["power"] * (1.0 + 0.05 * (era["index"] - 1))
    if mid in hp_override:
        hp = hp_override[mid]
    elif prev_hp.get(mid):
        hp = prev_hp[mid]
    roster = ROSTER[era_id]
    m = {
        "id": mid, "name": name, "era": era["name"], "theme": theme, "base": ERA_BASE[era_id], "boss": ERA_BOSS[era_id],
        "waves_file": "waves_%s.json" % mid, "start_gold": DIFF[diff][1], "start_lives": 100, "path_width": 1.7,
        "hp_mult": round(hp, 3), "armor_mult": era["power"], "bounds": [-15.0, -8.5, 15.0, 8.5],
        "paths": paths, "blockers": blockers,
        "endless_pool": ["walker", roster["heavy"], roster["special"], roster["fast"], roster["shield"], "repair_drone"],
    }
    if rivers:
        m["rivers"] = rivers
    if mid in prev_boss:
        m["boss_hp_mult"] = prev_boss[mid]
    if extra.get("final"):
        m["final"] = True
    save("map_%s.json" % mid, m)
    waves = remix(tables[diff], roster, ERA_BOSS[era_id], era_id)
    if extra.get("final"):
        for g in waves[-1]:
            if g["type"] == ERA_BOSS[era_id]:
                g["count"] = 1
        m.setdefault("boss_hp_mult", 1.4)
        save("map_%s.json" % mid, m)
    save("waves_%s.json" % mid, {"waves": waves})
    maps_index["maps"].append({"id": mid, "name": name, "era": era["name"], "difficulty": diff, "blurb": blurb})
    lens = [round(path_len(p)) for p in paths]
    print("%-18s %-16s %-6s hp=%.2f len=%s blockers=%d%s" % (mid, era["name"], diff, hp, lens, len(blockers), " river" if rivers else ""))

for k, v in enemies_new.items():
    enemies[k] = v
# era XP multipliers for Legacy
for era in S.ERAS:
    legacy["xp"]["era"][era["name"]] = round(1.0 + 0.3 * era["index"], 2)

save("towers.json", towers)
save("heroes.json", heroes)
save("enemies.json", enemies)
save("maps.json", maps_index)
save("legacy.json", legacy)
print("towers", len(towers), "heroes", len(heroes["heroes"]), "enemies", len(enemies), "maps", len(maps_index["maps"]))
